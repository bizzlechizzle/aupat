#!/usr/bin/env python3
"""
AUPAT Import Script v0.1.2
Enhanced version with Immich integration, GPS extraction, and metadata enhancement.

This is a wrapper around db_import.py that adds:
- Automatic upload to Immich photo storage
- GPS coordinate extraction from EXIF
- Image/video dimension extraction
- File size calculation
- Location GPS auto-update from media

Usage:
    # Standard import with Immich integration
    python scripts/db_import_v012.py --source /path/to/photos --metadata metadata.json

    # Import without Immich (fallback if service unavailable)
    python scripts/db_import_v012.py --source /path/to/photos --metadata metadata.json --no-immich

Version: 0.1.2
Last Updated: 2025-11-17
"""

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

from scripts.utils import (
    generate_uuid,
    calculate_sha256,
    generate_filename,
    determine_file_type,
    check_sha256_collision,
    check_location_name_collision
)
from scripts.normalize import (
    normalize_location_name,
    normalize_state_code,
    normalize_location_type,
    normalize_datetime,
    normalize_extension,
    normalize_author
)
from scripts.immich_integration import (
    get_immich_adapter,
    process_media_for_immich,
    update_location_gps
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


def load_metadata(metadata_path: str) -> dict:
    """Load import metadata from JSON file."""
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # Validate required fields
    required = ['loc_name', 'state', 'type']
    missing = [f for f in required if not metadata.get(f)]
    if missing:
        raise ValueError(f"Metadata missing required fields: {missing}")

    return metadata


def import_with_immich(
    db_path: str,
    source_dir: str,
    staging_dir: str,
    loc_uuid: str,
    imp_author: str,
    enable_immich: bool = True
) -> dict:
    """
    Import media files with Immich integration.

    Args:
        db_path: Path to database
        source_dir: Source directory with media files
        staging_dir: Staging directory for imports
        loc_uuid: Location UUID
        imp_author: Import author name
        enable_immich: Whether to enable Immich uploads

    Returns:
        Dictionary with import statistics
    """
    source_path = Path(source_dir)
    staging_path = Path(staging_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    # Create staging directory
    loc_staging = staging_path / loc_uuid[:8]
    loc_staging.mkdir(parents=True, exist_ok=True)

    logger.info(f"Importing from: {source_dir}")
    logger.info(f"Staging to: {loc_staging}")
    logger.info(f"Immich integration: {'enabled' if enable_immich else 'disabled'}")

    # Get Immich adapter if enabled
    immich_adapter = None
    if enable_immich:
        immich_adapter = get_immich_adapter()
        if immich_adapter is None:
            logger.warning("Immich unavailable - continuing without Immich integration")

    # Collect files
    files = [f for f in source_path.rglob('*') if f.is_file()]
    logger.info(f"Found {len(files)} files to process")

    # Connect to database
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    cursor = conn.cursor()

    stats = {
        'total': 0,
        'images': 0,
        'videos': 0,
        'documents': 0,
        'duplicates': 0,
        'errors': 0,
        'uploaded_to_immich': 0,
        'gps_extracted': 0,
        'location_gps_updated': False
    }

    timestamp = normalize_datetime(datetime.now())

    try:
        conn.execute("BEGIN TRANSACTION")

        for i, file_path in enumerate(files, 1):
            try:
                # Progress indicator
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(files)} files")

                # Get file type
                ext = normalize_extension(file_path.suffix)
                file_type = determine_file_type(ext)

                if file_type == 'other':
                    logger.debug(f"Skipping unknown file type: {file_path.name}")
                    continue

                # Calculate SHA256
                sha256 = calculate_sha256(str(file_path))

                # Check for duplicates
                if check_sha256_collision(cursor, sha256, file_type):
                    logger.info(f"Duplicate detected: {file_path.name}")
                    stats['duplicates'] += 1
                    continue

                # Process media for Immich
                media_metadata = {}
                if file_type in ['image', 'video']:
                    media_metadata = process_media_for_immich(
                        str(file_path),
                        file_type,
                        immich_adapter
                    )

                    if media_metadata.get('immich_asset_id'):
                        stats['uploaded_to_immich'] += 1

                    if media_metadata.get('gps_lat') and media_metadata.get('gps_lon'):
                        stats['gps_extracted'] += 1

                        # Update location GPS if needed
                        if not stats['location_gps_updated']:
                            if update_location_gps(
                                cursor,
                                loc_uuid,
                                media_metadata['gps_lat'],
                                media_metadata['gps_lon']
                            ):
                                stats['location_gps_updated'] = True

                # Generate filename and copy to staging
                media_type = 'img' if file_type == 'image' else 'vid' if file_type == 'video' else 'doc'
                new_filename = generate_filename(media_type, loc_uuid, sha256, ext)
                staging_file = loc_staging / new_filename

                import shutil
                shutil.copy2(file_path, staging_file)

                # Insert into database
                if file_type == 'image':
                    cursor.execute(
                        """
                        INSERT INTO images (
                            img_sha256, img_name, img_loc, loc_uuid,
                            img_loco, img_nameo, img_add, img_update, imp_author,
                            immich_asset_id, img_width, img_height,
                            img_size_bytes, gps_lat, gps_lon
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sha256, new_filename, str(staging_file), loc_uuid,
                            str(file_path.parent), file_path.name,
                            timestamp, timestamp, imp_author,
                            media_metadata.get('immich_asset_id'),
                            media_metadata.get('width'),
                            media_metadata.get('height'),
                            media_metadata.get('file_size'),
                            media_metadata.get('gps_lat'),
                            media_metadata.get('gps_lon')
                        )
                    )
                    stats['images'] += 1

                elif file_type == 'video':
                    cursor.execute(
                        """
                        INSERT INTO videos (
                            vid_sha256, vid_name, vid_loc, loc_uuid,
                            vid_loco, vid_nameo, vid_add, vid_update, imp_author,
                            immich_asset_id, vid_width, vid_height,
                            vid_duration_sec, vid_size_bytes, gps_lat, gps_lon
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sha256, new_filename, str(staging_file), loc_uuid,
                            str(file_path.parent), file_path.name,
                            timestamp, timestamp, imp_author,
                            media_metadata.get('immich_asset_id'),
                            media_metadata.get('width'),
                            media_metadata.get('height'),
                            media_metadata.get('duration'),
                            media_metadata.get('file_size'),
                            media_metadata.get('gps_lat'),
                            media_metadata.get('gps_lon')
                        )
                    )
                    stats['videos'] += 1

                elif file_type == 'document':
                    cursor.execute(
                        """
                        INSERT INTO documents (
                            doc_sha256, doc_name, doc_loc, doc_ext, loc_uuid,
                            doc_loco, doc_nameo, doc_add, doc_update, imp_author
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sha256, new_filename, str(staging_file), ext, loc_uuid,
                            str(file_path.parent), file_path.name,
                            timestamp, timestamp, imp_author
                        )
                    )
                    stats['documents'] += 1

                stats['total'] += 1

            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                stats['errors'] += 1
                continue

        # Commit transaction
        conn.commit()
        logger.info("Import completed successfully")

    except Exception as e:
        logger.error(f"Import failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AUPAT Import v0.1.2 with Immich Integration'
    )
    parser.add_argument(
        '--source',
        required=True,
        help='Source directory containing media files'
    )
    parser.add_argument(
        '--metadata',
        required=True,
        help='Path to metadata.json file'
    )
    parser.add_argument(
        '--config',
        help='Path to user.json config file'
    )
    parser.add_argument(
        '--author',
        default='AUPAT',
        help='Import author name'
    )
    parser.add_argument(
        '--no-immich',
        action='store_true',
        help='Disable Immich integration'
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = load_user_config(args.config)
        db_path = config['db_loc']
        staging_dir = config['db_ingest']

        # Load metadata
        metadata = load_metadata(args.metadata)

        # Generate location UUID
        loc_uuid = generate_uuid()

        # Normalize location data
        loc_name = normalize_location_name(metadata['loc_name'])
        state = normalize_state_code(metadata['state'])
        loc_type = normalize_location_type(metadata['type'])

        logger.info(f"\nImporting Location:")
        logger.info(f"  Name: {loc_name}")
        logger.info(f"  State: {state}")
        logger.info(f"  Type: {loc_type}")
        logger.info(f"  UUID: {loc_uuid}")
        logger.info("")

        # Create location in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        timestamp = normalize_datetime(datetime.now())

        cursor.execute(
            """
            INSERT INTO locations (
                loc_uuid, loc_name, state, type, loc_add, loc_update, imp_author
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (loc_uuid, loc_name, state, loc_type, timestamp, timestamp, args.author)
        )
        conn.commit()
        conn.close()

        # Import media
        stats = import_with_immich(
            db_path,
            args.source,
            staging_dir,
            loc_uuid,
            args.author,
            enable_immich=not args.no_immich
        )

        # Print summary
        logger.info("\n" + "="*50)
        logger.info("IMPORT SUMMARY")
        logger.info("="*50)
        logger.info(f"Total files imported: {stats['total']}")
        logger.info(f"  Images: {stats['images']}")
        logger.info(f"  Videos: {stats['videos']}")
        logger.info(f"  Documents: {stats['documents']}")
        logger.info(f"Duplicates skipped: {stats['duplicates']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"Uploaded to Immich: {stats['uploaded_to_immich']}")
        logger.info(f"GPS coordinates extracted: {stats['gps_extracted']}")
        logger.info(f"Location GPS updated: {'Yes' if stats['location_gps_updated'] else 'No'}")
        logger.info("="*50)

        if stats['errors'] > 0:
            logger.warning(f"\nImport completed with {stats['errors']} errors. Check logs for details.")
        else:
            logger.info("\nImport completed successfully!")

    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
