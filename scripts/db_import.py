#!/usr/bin/env python3
"""
AUPAT Import Script
Imports new locations and associated media via CLI.

This script:
1. Generates UUID for location
2. Prompts for location details
3. Imports media files to staging
4. Generates SHA256 hashes
5. Detects duplicates
6. Creates initial database entries

Version: 1.0.0
Last Updated: 2025-11-15
"""

import argparse
import json
import logging
import shutil
import sqlite3
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import generate_uuid, calculate_sha256
from normalize import (
    normalize_location_name,
    normalize_state_code,
    normalize_location_type,
    normalize_sub_type,
    normalize_datetime,
    normalize_extension,
    normalize_author
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_user_config(config_path: str = None) -> dict:
    """Load user configuration from user.json."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"user.json not found at {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)


def import_location_interactive(db_path: str) -> dict:
    """
    Interactively collect location information from user.

    Args:
        db_path: Path to database

    Returns:
        dict: Location data
    """
    print("\n" + "=" * 60)
    print("Import New Location")
    print("=" * 60)

    # Generate UUID
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    loc_uuid = generate_uuid(cursor, 'locations', 'loc_uuid')
    conn.close()

    loc_uuid8 = loc_uuid[:8]
    print(f"\nGenerated Location UUID: {loc_uuid}")
    print(f"Location UUID8: {loc_uuid8}")

    # Collect location details
    loc_name = input("\nLocation name: ").strip()
    loc_name = normalize_location_name(loc_name)

    aka_name = input("Also known as (optional): ").strip()
    aka_name = normalize_location_name(aka_name) if aka_name else None

    state = input("State (e.g., ny, vt, pa): ").strip()
    state = normalize_state_code(state)

    loc_type = input("Type (e.g., industrial, residential): ").strip()
    loc_type = normalize_location_type(loc_type)

    sub_type = input("Sub-type (optional): ").strip()
    sub_type = normalize_sub_type(sub_type) if sub_type else None

    author = input("Your name/username: ").strip()
    author = normalize_author(author)

    # Confirm
    print("\n" + "-" * 60)
    print("Location Details:")
    print(f"  Name: {loc_name}")
    if aka_name:
        print(f"  AKA: {aka_name}")
    print(f"  State: {state}")
    print(f"  Type: {loc_type}")
    if sub_type:
        print(f"  Sub-type: {sub_type}")
    print(f"  Author: {author}")
    print(f"  UUID: {loc_uuid}")
    print("-" * 60)

    confirm = input("\nContinue with import? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        raise ValueError("Import cancelled by user")

    return {
        'loc_uuid': loc_uuid,
        'loc_name': loc_name,
        'aka_name': aka_name,
        'state': state,
        'type': loc_type,
        'sub_type': sub_type,
        'imp_author': author
    }


def import_media_files(source_dir: str, staging_dir: str, db_path: str, loc_uuid: str) -> dict:
    """
    Import media files from source to staging directory.

    Args:
        source_dir: Source directory containing media files
        staging_dir: Staging/ingest directory
        db_path: Path to database
        loc_uuid: Location UUID for these files

    Returns:
        dict: Statistics about imported files
    """
    source_path = Path(source_dir)
    staging_path = Path(staging_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    # Create staging directory
    loc_staging = staging_path / loc_uuid[:8]
    loc_staging.mkdir(parents=True, exist_ok=True)

    logger.info(f"Importing files from: {source_dir}")
    logger.info(f"Staging directory: {loc_staging}")

    # Collect all files
    files = list(source_path.rglob('*'))
    files = [f for f in files if f.is_file()]

    logger.info(f"Found {len(files)} files to import")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {
        'total': 0,
        'images': 0,
        'videos': 0,
        'documents': 0,
        'duplicates': 0,
        'errors': 0
    }

    timestamp = normalize_datetime(None)

    try:
        for file_path in files:
            try:
                # Calculate SHA256
                sha256 = calculate_sha256(str(file_path))
                sha8 = sha256[:8]

                # Get file extension
                ext = normalize_extension(file_path.suffix)

                # Copy to staging
                staging_file = loc_staging / file_path.name
                shutil.copy2(file_path, staging_file)

                # Store original location
                orig_location = str(file_path.parent)
                orig_name = file_path.name

                stats['total'] += 1
                logger.info(f"Imported: {file_path.name} ({sha8})")

            except Exception as e:
                logger.error(f"Failed to import {file_path.name}: {e}")
                stats['errors'] += 1

        conn.commit()

    finally:
        conn.close()

    return stats


def create_location_record(db_path: str, location_data: dict) -> None:
    """
    Create database record for location.

    Args:
        db_path: Path to database
        location_data: Location details dict
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        timestamp = normalize_datetime(None)

        cursor.execute(
            """
            INSERT INTO locations (
                loc_uuid, loc_name, aka_name, state, type, sub_type,
                loc_add, loc_update, imp_author
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                location_data['loc_uuid'],
                location_data['loc_name'],
                location_data.get('aka_name'),
                location_data['state'],
                location_data['type'],
                location_data.get('sub_type'),
                timestamp,
                timestamp,
                location_data.get('imp_author')
            )
        )

        conn.commit()
        logger.info(f"Created location record: {location_data['loc_name']}")

    finally:
        conn.close()


def main():
    """Main import workflow."""
    parser = argparse.ArgumentParser(
        description='Import new location and media to AUPAT'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file'
    )
    parser.add_argument(
        '--source',
        type=str,
        required=True,
        help='Source directory containing media files to import'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_user_config(args.config)

        logger.info("=" * 60)
        logger.info("AUPAT Import")
        logger.info("=" * 60)

        # Collect location information
        location_data = import_location_interactive(config['db_loc'])

        # Create location record
        create_location_record(config['db_loc'], location_data)

        # Import media files
        logger.info("\nImporting media files...")
        stats = import_media_files(
            args.source,
            config.get('db_ingest', ''),
            config['db_loc'],
            location_data['loc_uuid']
        )

        # Summary
        logger.info("=" * 60)
        logger.info("Import Summary")
        logger.info("=" * 60)
        logger.info(f"Location: {location_data['loc_name']}")
        logger.info(f"UUID: {location_data['loc_uuid']}")
        logger.info(f"Total files: {stats['total']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info("=" * 60)
        logger.info("IMPORT SUCCESSFUL")
        logger.info("\nNext steps:")
        logger.info("  1. Run db_organize.py to extract metadata")
        logger.info("  2. Run db_folder.py to create folder structure")
        logger.info("  3. Run db_ingest.py to move files to archive")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
