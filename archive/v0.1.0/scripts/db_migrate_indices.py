#!/usr/bin/env python3
"""
Database Index Migration Script
Adds performance indices to AUPAT database for fast SHA256 and UUID lookups.

This script is idempotent - safe to run multiple times.

Usage:
    python scripts/db_migrate_indices.py
    python scripts/db_migrate_indices.py --config /path/to/user.json

Version: 1.0.0
Last Updated: 2025-11-17
"""

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

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


def add_database_indices(db_path: str) -> dict:
    """
    Add performance indices to database tables.

    Indices added:
    - SHA256 indices for fast duplicate detection
    - Location UUID indices for fast location queries
    - Hardware indices for fast filtering by camera type

    All indices use IF NOT EXISTS so script is idempotent.

    Args:
        db_path: Path to SQLite database file

    Returns:
        dict: Statistics about indices created

    Raises:
        sqlite3.Error: If database operations fail
    """
    stats = {
        'indices_created': 0,
        'indices_already_existed': 0,
        'errors': []
    }

    # Index definitions
    indices = [
        # SHA256 indices for duplicate detection
        ('idx_images_sha256', 'CREATE INDEX IF NOT EXISTS idx_images_sha256 ON images(img_sha256)'),
        ('idx_videos_sha256', 'CREATE INDEX IF NOT EXISTS idx_videos_sha256 ON videos(vid_sha256)'),
        ('idx_documents_sha256', 'CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(doc_sha256)'),

        # Location UUID indices for location queries
        ('idx_images_loc_uuid', 'CREATE INDEX IF NOT EXISTS idx_images_loc_uuid ON images(loc_uuid)'),
        ('idx_videos_loc_uuid', 'CREATE INDEX IF NOT EXISTS idx_videos_loc_uuid ON videos(loc_uuid)'),
        ('idx_documents_loc_uuid', 'CREATE INDEX IF NOT EXISTS idx_documents_loc_uuid ON documents(loc_uuid)'),

        # Hardware indices for filtering by camera type
        ('idx_images_hardware', 'CREATE INDEX IF NOT EXISTS idx_images_hardware ON images(hardware)'),
        ('idx_videos_hardware', 'CREATE INDEX IF NOT EXISTS idx_videos_hardware ON videos(hardware)'),

        # Composite indices for common query patterns
        ('idx_images_loc_hardware', 'CREATE INDEX IF NOT EXISTS idx_images_loc_hardware ON images(loc_uuid, hardware)'),
        ('idx_videos_loc_hardware', 'CREATE INDEX IF NOT EXISTS idx_videos_loc_hardware ON videos(loc_uuid, hardware)'),
    ]

    logger.info(f"Adding indices to database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check which indices already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        existing_indices = {row[0] for row in cursor.fetchall()}
        logger.info(f"Found {len(existing_indices)} existing indices")

        # Create each index
        for idx_name, sql in indices:
            try:
                if idx_name in existing_indices:
                    logger.info(f"  Index already exists: {idx_name}")
                    stats['indices_already_existed'] += 1
                else:
                    logger.info(f"  Creating index: {idx_name}")
                    cursor.execute(sql)
                    stats['indices_created'] += 1
                    logger.info(f"    ✓ Created: {idx_name}")
            except sqlite3.Error as e:
                error_msg = f"Failed to create index {idx_name}: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)

        conn.commit()
        logger.info(f"Index migration complete")
        logger.info(f"  Created: {stats['indices_created']}")
        logger.info(f"  Already existed: {stats['indices_already_existed']}")

        if stats['errors']:
            logger.warning(f"  Errors: {len(stats['errors'])}")
            for error in stats['errors']:
                logger.warning(f"    - {error}")

        # Verify indices were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        final_indices = {row[0] for row in cursor.fetchall()}
        logger.info(f"Total indices in database: {len(final_indices)}")

    finally:
        conn.close()

    return stats


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Add performance indices to AUPAT database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default config location
  python scripts/db_migrate_indices.py

  # Use custom config
  python scripts/db_migrate_indices.py --config /path/to/user.json

This script is idempotent - safe to run multiple times.
Indices use IF NOT EXISTS so existing indices are not recreated.
        """
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file'
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

        if 'db_loc' not in config:
            logger.error("db_loc not found in user.json")
            return 1

        db_path = Path(config['db_loc'])

        # Check database exists
        if not db_path.exists():
            logger.error(f"Database not found: {db_path}")
            logger.error("Run db_migrate.py first to create the database schema")
            return 1

        # Add indices
        logger.info("=" * 60)
        logger.info("Database Index Migration")
        logger.info("=" * 60)

        stats = add_database_indices(str(db_path))

        logger.info("=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Indices created: {stats['indices_created']}")
        logger.info(f"Indices already existed: {stats['indices_already_existed']}")

        if stats['errors']:
            logger.error(f"Errors: {len(stats['errors'])}")
            return 1
        else:
            logger.info("MIGRATION SUCCESSFUL")
            return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Run setup.sh to create user.json with correct paths")
        return 1
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
