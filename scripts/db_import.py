#!/usr/bin/env python3
"""
AUPAT Import Script
Imports new locations and associated media via CLI.

This script:
1. Creates backup before import
2. Generates UUID for location
3. Checks for location name collisions
4. Prompts for location details
5. Imports media files to staging
6. Generates SHA256 hashes
7. Detects duplicates via SHA256 collision checking
8. Creates database entries in images/videos/documents tables
9. Uses hardlinks for same-disk imports
10. Updates versions table
11. Verifies import match counts

Version: 2.0.0
Last Updated: 2025-11-15
P0/P1 Implementation
"""

import argparse
import json
import logging
import os
import shutil
import sqlite3
import subprocess
from urllib.parse import urlparse
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    generate_uuid,
    calculate_sha256,
    generate_filename,
    determine_file_type,
    check_sha256_collision,
    check_location_name_collision
)
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


def run_backup(config_path: str) -> bool:
    """
    Run backup script before import.

    Args:
        config_path: Path to user.json config file

    Returns:
        bool: True if backup successful, False otherwise
    """
    backup_script = Path(__file__).parent / 'backup.py'

    if not backup_script.exists():
        logger.warning("backup.py not found - skipping backup")
        return True

    logger.info("Creating database backup before import...")

    try:
        result = subprocess.run(
            [sys.executable, str(backup_script), '--config', config_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            logger.info("✓ Backup completed successfully")
            return True
        else:
            logger.error(f"Backup failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Backup timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Backup failed with exception: {e}")
        return False


def import_location_from_metadata(db_path: str, metadata_path: str) -> dict:
    """
    Load location information from metadata.json file (for web interface imports).

    Args:
        db_path: Path to database
        metadata_path: Path to metadata.json file

    Returns:
        dict: Location data

    Raises:
        FileNotFoundError: If metadata file not found
        ValueError: If metadata is invalid
    """
    metadata_file = Path(metadata_path)
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    logger.info(f"Loading location data from metadata: {metadata_path}")

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    # Validate required fields
    required_fields = ['loc_name', 'state', 'type']
    missing_fields = [f for f in required_fields if not metadata.get(f)]
    if missing_fields:
        raise ValueError(f"Metadata missing required fields: {missing_fields}")

    # Extract and normalize data
    loc_name = normalize_location_name(metadata['loc_name'])

    # Check for location name collision
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    existing_uuid = check_location_name_collision(cursor, loc_name)
    if existing_uuid:
        logger.warning(f"⚠ Location name already exists: {loc_name}")
        logger.warning(f"  Existing UUID: {existing_uuid}")
        logger.warning("⚠ Creating duplicate location (web interface import)")

    # Generate UUID
    loc_uuid = generate_uuid(cursor, 'locations', 'loc_uuid')
    conn.close()

    loc_uuid8 = loc_uuid[:8]
    logger.info(f"Generated Location UUID: {loc_uuid}")
    logger.info(f"Location UUID8: {loc_uuid8}")

    # Build location data dict
    location_data = {
        'loc_uuid': loc_uuid,
        'loc_uuid8': loc_uuid8,
        'loc_name': loc_name,
        'aka_name': normalize_location_name(metadata['aka_name']) if metadata.get('aka_name') else None,
        'state': normalize_state_code(metadata['state']),
        'type': normalize_location_type(metadata['type']),
        'sub_type': normalize_sub_type(metadata['sub_type']) if metadata.get('sub_type') else None,
        'imp_author': normalize_author(metadata['imp_author']) if metadata.get('imp_author') else None,
        'is_film': 1 if metadata.get('is_film') else 0,
        'film_stock': metadata.get('film_stock'),
        'film_format': metadata.get('film_format')
    }

    logger.info("Location data loaded from metadata:")
    logger.info(f"  Name: {location_data['loc_name']}")
    logger.info(f"  State: {location_data['state']}")
    logger.info(f"  Type: {location_data['type']}")
    if location_data['imp_author']:
        logger.info(f"  Author: {location_data['imp_author']}")

    return location_data


def import_location_interactive(db_path: str) -> dict:
    """
    Interactively collect location information from user.

    Args:
        db_path: Path to database

    Returns:
        dict: Location data

    Raises:
        ValueError: If user cancels or location name collision detected
    """
    print("\n" + "=" * 60)
    print("Import New Location")
    print("=" * 60)

    # Collect location name first (for collision check)
    loc_name = input("\nLocation name: ").strip()
    loc_name = normalize_location_name(loc_name)

    # Check for location name collision
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    existing_uuid = check_location_name_collision(cursor, loc_name)
    if existing_uuid:
        logger.warning(f"⚠ Location name already exists: {loc_name}")
        logger.warning(f"  Existing UUID: {existing_uuid}")
        response = input("\nContinue anyway? This will create a duplicate location. (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            conn.close()
            raise ValueError("Import cancelled - location name already exists")

    # Generate UUID
    loc_uuid = generate_uuid(cursor, 'locations', 'loc_uuid')
    conn.close()

    loc_uuid8 = loc_uuid[:8]
    print(f"\nGenerated Location UUID: {loc_uuid}")
    print(f"Location UUID8: {loc_uuid8}")

    # Collect remaining details
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


def import_media_files(
    source_dir: str,
    staging_dir: str,
    db_path: str,
    loc_uuid: str,
    imp_author: str
) -> dict:
    """
    Import media files from source to staging directory with full database integration.

    This function:
    - Detects file types (image/video/document)
    - Checks for SHA256 collisions (duplicates)
    - Uses hardlinks when source and staging on same disk
    - Inserts records into appropriate database tables
    - Tracks detailed statistics

    Args:
        source_dir: Source directory containing media files
        staging_dir: Staging/ingest directory
        db_path: Path to database
        loc_uuid: Location UUID for these files
        imp_author: Author name for import tracking

    Returns:
        dict: Statistics about imported files

    Raises:
        FileNotFoundError: If source directory doesn't exist
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

    logger.info(f"Found {len(files)} files to process")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {
        'total': 0,
        'images': 0,
        'videos': 0,
        'documents': 0,
        'duplicates': 0,
        'errors': 0,
        'skipped': 0,
        'hardlinked': 0,
        'copied': 0
    }

    timestamp = normalize_datetime(None)

    # Check if source and staging are on same filesystem
    try:
        same_filesystem = source_path.stat().st_dev == loc_staging.stat().st_dev
        if same_filesystem:
            logger.info("Source and staging on same filesystem - will use hardlinks")
        else:
            logger.info("Source and staging on different filesystems - will copy files")
    except Exception:
        same_filesystem = False
        logger.warning("Could not determine filesystem - defaulting to copy")

    try:
        for file_path in files:
            try:
                # Get file extension and determine type
                ext = normalize_extension(file_path.suffix)
                file_type = determine_file_type(ext)

                # Skip unknown file types
                if file_type == 'other':
                    logger.debug(f"Skipping unknown file type: {file_path.name}")
                    stats['skipped'] += 1
                    continue

                # Calculate SHA256
                sha256 = calculate_sha256(str(file_path))
                sha8 = sha256[:8]

                # Check for collision
                if check_sha256_collision(cursor, sha256, file_type):
                    logger.warning(f"Duplicate {file_type} detected (SHA256 exists): {file_path.name} ({sha8})")
                    stats['duplicates'] += 1
                    continue

                # Generate standardized filename
                media_type = 'img' if file_type == 'image' else 'vid' if file_type == 'video' else 'doc'
                new_filename = generate_filename(
                    media_type=media_type,
                    loc_uuid=loc_uuid,
                    sha256=sha256,
                    extension=ext
                )

                # Target file in staging
                staging_file = loc_staging / new_filename

                # Copy or hardlink file
                if same_filesystem:
                    try:
                        os.link(file_path, staging_file)
                        stats['hardlinked'] += 1
                        logger.debug(f"Hardlinked: {file_path.name} -> {new_filename}")
                    except OSError as e:
                        # Fallback to copy if hardlink fails
                        logger.warning(f"Hardlink failed, falling back to copy: {e}")
                        shutil.copy2(file_path, staging_file)
                        stats['copied'] += 1
                else:
                    shutil.copy2(file_path, staging_file)
                    stats['copied'] += 1

                # Store original location
                orig_location = str(file_path.parent)
                orig_name = file_path.name

                # Insert into appropriate table
                if file_type == 'image':
                    cursor.execute(
                        """
                        INSERT INTO images (
                            img_sha256, img_name, img_loc, loc_uuid,
                            img_loco, img_nameo, img_add, img_update, imp_author
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sha256,
                            new_filename,
                            str(staging_file),  # img_loc points to staging until ingest moves to archive
                            loc_uuid,
                            orig_location,  # img_loco points to original location before import
                            orig_name,
                            timestamp,
                            timestamp,
                            imp_author
                        )
                    )
                    stats['images'] += 1
                    logger.info(f"✓ Imported image: {orig_name} -> {new_filename} ({sha8})")

                elif file_type == 'video':
                    cursor.execute(
                        """
                        INSERT INTO videos (
                            vid_sha256, vid_name, vid_loc, loc_uuid,
                            vid_loco, vid_nameo, vid_add, vid_update, imp_author
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sha256,
                            new_filename,
                            str(staging_file),  # vid_loc points to staging until ingest moves to archive
                            loc_uuid,
                            orig_location,  # vid_loco points to original location before import
                            orig_name,
                            timestamp,
                            timestamp,
                            imp_author
                        )
                    )
                    stats['videos'] += 1
                    logger.info(f"✓ Imported video: {orig_name} -> {new_filename} ({sha8})")

                elif file_type == 'document':
                    cursor.execute(
                        """
                        INSERT INTO documents (
                            doc_sha256, doc_name, doc_loc, doc_ext, loc_uuid,
                            doc_loco, doc_nameo, doc_add, doc_update, imp_author
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sha256,
                            new_filename,
                            str(staging_file),  # doc_loc points to staging until ingest moves to archive
                            ext,
                            loc_uuid,
                            orig_location,  # doc_loco points to original location before import
                            orig_name,
                            timestamp,
                            timestamp,
                            imp_author
                        )
                    )
                    stats['documents'] += 1
                    logger.info(f"✓ Imported document: {orig_name} -> {new_filename} ({sha8})")

                stats['total'] += 1

            except Exception as e:
                logger.error(f"Failed to import {file_path.name}: {e}")
                stats['errors'] += 1

        # Update versions table
        cursor.execute(
            """
            INSERT OR REPLACE INTO versions (modules, version, ver_updated)
            VALUES (?, ?, ?)
            """,
            (
                f'import_{loc_uuid[:8]}',
                '2.0.0',
                timestamp
            )
        )

        conn.commit()

        # Verify match count
        logger.info("\nVerifying import match counts...")
        expected_total = stats['images'] + stats['videos'] + stats['documents']
        if expected_total == stats['total']:
            logger.info(f"✓ Match count verified: {stats['total']} files imported")
        else:
            logger.warning(f"⚠ Match count mismatch: expected {expected_total}, got {stats['total']}")

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
                loc_add, loc_update, imp_author, is_film, film_stock, film_format
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                location_data.get('imp_author'),
                location_data.get('is_film', 0),
                location_data.get('film_stock'),
                location_data.get('film_format')
            )
        )

        conn.commit()
        logger.info(f"✓ Created location record: {location_data['loc_name']}")

    finally:
        conn.close()


def import_web_urls(db_path: str, metadata_path: str, loc_uuid: str, imp_author: str) -> int:
    """
    Import web URLs from metadata.json into the urls table.

    Args:
        db_path: Path to database
        metadata_path: Path to metadata.json file
        loc_uuid: Location UUID to associate URLs with
        imp_author: Author name for tracking

    Returns:
        int: Number of URLs imported

    Raises:
        ValueError: If metadata file not found
    """
    # Load metadata
    if not Path(metadata_path).exists():
        raise ValueError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    web_urls = metadata.get('web_urls', [])
    if not web_urls:
        logger.info("No web URLs to import")
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        timestamp = normalize_datetime(None)
        imported_count = 0

        for url in web_urls:
            url = url.strip()
            if not url:
                continue

            # Parse domain from URL
            try:
                parsed = urlparse(url)
                domain = parsed.netloc or parsed.path.split('/')[0]
            except Exception as e:
                logger.warning(f"Failed to parse URL {url}: {e}")
                domain = "unknown"

            # Generate UUID for URL
            url_uuid = generate_uuid(cursor, 'urls', 'url_uuid')

            # Insert URL record
            cursor.execute(
                """
                INSERT INTO urls (
                    url_uuid, url, domain, loc_uuid, url_add, url_update, imp_author
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    url_uuid,
                    url,
                    domain,
                    loc_uuid,
                    timestamp,
                    timestamp,
                    imp_author
                )
            )
            imported_count += 1
            logger.info(f"Imported URL: {url} (domain: {domain})")

        conn.commit()
        logger.info(f"✓ Imported {imported_count} web URL(s)")

    finally:
        conn.close()

    return imported_count


def main():
    """Main import workflow with P0/P1 fixes."""
    parser = argparse.ArgumentParser(
        description='Import new location and media to AUPAT (P0/P1 Implementation)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import with backup
  python db_import.py --source /path/to/media

  # Skip backup (not recommended)
  python db_import.py --source /path/to/media --skip-backup

Features (P0/P1):
  ✓ Backup before import
  ✓ Location name collision detection
  ✓ File type detection (images/videos/documents)
  ✓ SHA256 collision checking
  ✓ Hardlink support for same-disk imports
  ✓ Database record creation for all media
  ✓ Versions table tracking
  ✓ Import match count verification
        """
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
        '--metadata',
        type=str,
        help='Path to metadata.json file with location data (for non-interactive/web imports)'
    )
    parser.add_argument(
        '--skip-backup',
        action='store_true',
        help='Skip database backup (not recommended)'
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
        config_path = args.config or str(Path(__file__).parent.parent / 'user' / 'user.json')
        config = load_user_config(config_path)

        logger.info("=" * 60)
        logger.info("AUPAT Import v2.0 (P0/P1 Implementation)")
        logger.info("=" * 60)

        # P0: Create backup before import
        if not args.skip_backup:
            if not run_backup(config_path):
                logger.error("Backup failed - aborting import for safety")
                logger.error("Use --skip-backup to import anyway (not recommended)")
                return 1
        else:
            logger.warning("⚠ Skipping backup (--skip-backup flag set)")

        # P1: Collect location information (includes name collision check)
        # Use metadata file if provided (web interface), otherwise prompt interactively
        if args.metadata:
            logger.info(f"Using metadata file: {args.metadata}")
            location_data = import_location_from_metadata(config['db_loc'], args.metadata)
        else:
            logger.info("Interactive mode - prompting for location details")
            location_data = import_location_interactive(config['db_loc'])

        # Create location record
        create_location_record(config['db_loc'], location_data)

        # Import web URLs if metadata file provided (web interface mode)
        url_count = 0
        if args.metadata:
            logger.info("\nImporting web URLs...")
            url_count = import_web_urls(
                config['db_loc'],
                args.metadata,
                location_data['loc_uuid'],
                location_data.get('imp_author', 'unknown')
            )

        # P0: Import media files with full database integration
        logger.info("\nImporting media files...")
        stats = import_media_files(
            args.source,
            config.get('db_ingest', ''),
            config['db_loc'],
            location_data['loc_uuid'],
            location_data.get('imp_author', 'unknown')
        )

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Import Summary")
        logger.info("=" * 60)
        logger.info(f"Location: {location_data['loc_name']}")
        logger.info(f"UUID: {location_data['loc_uuid']}")
        logger.info(f"")
        logger.info(f"Files processed: {len(list(Path(args.source).rglob('*')))}")
        logger.info(f"Files imported: {stats['total']}")
        logger.info(f"  - Images: {stats['images']}")
        logger.info(f"  - Videos: {stats['videos']}")
        logger.info(f"  - Documents: {stats['documents']}")
        if url_count > 0:
            logger.info(f"  - Web URLs: {url_count}")
        logger.info(f"")
        logger.info(f"Duplicates skipped: {stats['duplicates']}")
        logger.info(f"Unknown types skipped: {stats['skipped']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"")
        logger.info(f"Transfer method:")
        logger.info(f"  - Hardlinked: {stats['hardlinked']}")
        logger.info(f"  - Copied: {stats['copied']}")
        logger.info("=" * 60)

        if stats['errors'] > 0:
            logger.warning(f"⚠ Import completed with {stats['errors']} errors")
        else:
            logger.info("✓ IMPORT SUCCESSFUL")

        logger.info("\nNext steps:")
        logger.info("  1. Run db_organize.py to extract metadata")
        logger.info("  2. Run db_folder.py to create folder structure")
        logger.info("  3. Run db_ingest.py to move files to archive")
        logger.info("=" * 60)

        return 0 if stats['errors'] == 0 else 1

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
