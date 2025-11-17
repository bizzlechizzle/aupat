#!/usr/bin/env python3
"""
AUPAT Database Migration Script for v0.1.2
Adds schema enhancements for Immich integration, ArchiveBox integration,
GPS coordinates, address fields, and enhanced metadata.

This script:
1. Adds new columns to existing tables
2. Creates new tables for Google Maps imports and sync tracking
3. Adds performance indexes for map queries
4. Maintains backward compatibility with v0.1.0 schema

Version: 0.1.2
Last Updated: 2025-11-17
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from normalize import normalize_datetime

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
        raise FileNotFoundError(
            f"user.json not found at {config_path}. "
            "Create from user/user.json.template or run setup.sh"
        )

    with open(config_path, 'r') as f:
        config = json.load(f)

    required = ['db_name', 'db_loc']
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing required keys in user.json: {missing}")

    return config


def get_table_columns(cursor: sqlite3.Cursor, table_name: str) -> list:
    """Get list of column names for a table."""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """Check if table exists."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def migrate_locations_table(cursor: sqlite3.Cursor) -> None:
    """Add v0.1.2 columns to locations table."""
    logger.info("Migrating locations table...")

    existing_columns = get_table_columns(cursor, 'locations')

    # GPS coordinate fields
    if 'lat' not in existing_columns:
        logger.info("  Adding lat column")
        cursor.execute("ALTER TABLE locations ADD COLUMN lat REAL")

    if 'lon' not in existing_columns:
        logger.info("  Adding lon column")
        cursor.execute("ALTER TABLE locations ADD COLUMN lon REAL")

    if 'gps_source' not in existing_columns:
        logger.info("  Adding gps_source column")
        cursor.execute("ALTER TABLE locations ADD COLUMN gps_source TEXT")

    if 'gps_confidence' not in existing_columns:
        logger.info("  Adding gps_confidence column")
        cursor.execute("ALTER TABLE locations ADD COLUMN gps_confidence REAL")

    # Address fields
    if 'street_address' not in existing_columns:
        logger.info("  Adding street_address column")
        cursor.execute("ALTER TABLE locations ADD COLUMN street_address TEXT")

    if 'city' not in existing_columns:
        logger.info("  Adding city column")
        cursor.execute("ALTER TABLE locations ADD COLUMN city TEXT")

    if 'state_abbrev' not in existing_columns:
        logger.info("  Adding state_abbrev column (for 2-letter state code)")
        cursor.execute("ALTER TABLE locations ADD COLUMN state_abbrev TEXT")

    if 'zip_code' not in existing_columns:
        logger.info("  Adding zip_code column")
        cursor.execute("ALTER TABLE locations ADD COLUMN zip_code TEXT")

    if 'country' not in existing_columns:
        logger.info("  Adding country column (default USA)")
        cursor.execute("ALTER TABLE locations ADD COLUMN country TEXT DEFAULT 'USA'")

    if 'address_source' not in existing_columns:
        logger.info("  Adding address_source column")
        cursor.execute("ALTER TABLE locations ADD COLUMN address_source TEXT")

    logger.info("Locations table migration complete")


def migrate_images_table(cursor: sqlite3.Cursor) -> None:
    """Add v0.1.2 columns to images table."""
    logger.info("Migrating images table...")

    existing_columns = get_table_columns(cursor, 'images')

    # Immich integration
    if 'immich_asset_id' not in existing_columns:
        logger.info("  Adding immich_asset_id column")
        cursor.execute("ALTER TABLE images ADD COLUMN immich_asset_id TEXT UNIQUE")

    # Enhanced metadata
    if 'img_width' not in existing_columns:
        logger.info("  Adding img_width column")
        cursor.execute("ALTER TABLE images ADD COLUMN img_width INTEGER")

    if 'img_height' not in existing_columns:
        logger.info("  Adding img_height column")
        cursor.execute("ALTER TABLE images ADD COLUMN img_height INTEGER")

    if 'img_size_bytes' not in existing_columns:
        logger.info("  Adding img_size_bytes column")
        cursor.execute("ALTER TABLE images ADD COLUMN img_size_bytes INTEGER")

    # Per-image GPS coordinates
    if 'gps_lat' not in existing_columns:
        logger.info("  Adding gps_lat column")
        cursor.execute("ALTER TABLE images ADD COLUMN gps_lat REAL")

    if 'gps_lon' not in existing_columns:
        logger.info("  Adding gps_lon column")
        cursor.execute("ALTER TABLE images ADD COLUMN gps_lon REAL")

    logger.info("Images table migration complete")


def migrate_videos_table(cursor: sqlite3.Cursor) -> None:
    """Add v0.1.2 columns to videos table."""
    logger.info("Migrating videos table...")

    existing_columns = get_table_columns(cursor, 'videos')

    # Immich integration
    if 'immich_asset_id' not in existing_columns:
        logger.info("  Adding immich_asset_id column")
        cursor.execute("ALTER TABLE videos ADD COLUMN immich_asset_id TEXT UNIQUE")

    # Enhanced metadata
    if 'vid_width' not in existing_columns:
        logger.info("  Adding vid_width column")
        cursor.execute("ALTER TABLE videos ADD COLUMN vid_width INTEGER")

    if 'vid_height' not in existing_columns:
        logger.info("  Adding vid_height column")
        cursor.execute("ALTER TABLE videos ADD COLUMN vid_height INTEGER")

    if 'vid_duration_sec' not in existing_columns:
        logger.info("  Adding vid_duration_sec column")
        cursor.execute("ALTER TABLE videos ADD COLUMN vid_duration_sec REAL")

    if 'vid_size_bytes' not in existing_columns:
        logger.info("  Adding vid_size_bytes column")
        cursor.execute("ALTER TABLE videos ADD COLUMN vid_size_bytes INTEGER")

    # Per-video GPS coordinates
    if 'gps_lat' not in existing_columns:
        logger.info("  Adding gps_lat column")
        cursor.execute("ALTER TABLE videos ADD COLUMN gps_lat REAL")

    if 'gps_lon' not in existing_columns:
        logger.info("  Adding gps_lon column")
        cursor.execute("ALTER TABLE videos ADD COLUMN gps_lon REAL")

    logger.info("Videos table migration complete")


def migrate_urls_table(cursor: sqlite3.Cursor) -> None:
    """Add v0.1.2 columns to urls table."""
    logger.info("Migrating urls table...")

    existing_columns = get_table_columns(cursor, 'urls')

    # ArchiveBox integration
    if 'archivebox_snapshot_id' not in existing_columns:
        logger.info("  Adding archivebox_snapshot_id column")
        cursor.execute("ALTER TABLE urls ADD COLUMN archivebox_snapshot_id TEXT")

    if 'archive_status' not in existing_columns:
        logger.info("  Adding archive_status column")
        cursor.execute("ALTER TABLE urls ADD COLUMN archive_status TEXT DEFAULT 'pending'")

    if 'archive_date' not in existing_columns:
        logger.info("  Adding archive_date column")
        cursor.execute("ALTER TABLE urls ADD COLUMN archive_date TEXT")

    if 'media_extracted' not in existing_columns:
        logger.info("  Adding media_extracted column")
        cursor.execute("ALTER TABLE urls ADD COLUMN media_extracted INTEGER DEFAULT 0")

    logger.info("URLs table migration complete")


def create_google_maps_exports_table(cursor: sqlite3.Cursor) -> None:
    """Create google_maps_exports table for tracking Google Maps imports."""
    logger.info("Creating google_maps_exports table...")

    if not table_exists(cursor, 'google_maps_exports'):
        cursor.execute("""
            CREATE TABLE google_maps_exports (
                export_id TEXT PRIMARY KEY,
                import_date TEXT NOT NULL,
                file_path TEXT NOT NULL,
                locations_found INTEGER DEFAULT 0,
                addresses_extracted INTEGER DEFAULT 0,
                images_processed INTEGER DEFAULT 0
            )
        """)
        logger.info("google_maps_exports table created")
    else:
        logger.info("google_maps_exports table already exists")


def create_sync_log_table(cursor: sqlite3.Cursor) -> None:
    """Create sync_log table for future mobile sync tracking."""
    logger.info("Creating sync_log table...")

    if not table_exists(cursor, 'sync_log'):
        cursor.execute("""
            CREATE TABLE sync_log (
                sync_id TEXT PRIMARY KEY,
                device_id TEXT,
                sync_type TEXT,
                timestamp TEXT,
                items_synced INTEGER,
                conflicts INTEGER,
                status TEXT
            )
        """)
        logger.info("sync_log table created")
    else:
        logger.info("sync_log table already exists")


def create_indexes(cursor: sqlite3.Cursor) -> None:
    """Create performance indexes for v0.1.2."""
    logger.info("Creating performance indexes...")

    indexes = [
        ("idx_locations_gps", "CREATE INDEX IF NOT EXISTS idx_locations_gps ON locations(lat, lon) WHERE lat IS NOT NULL"),
        ("idx_images_immich", "CREATE INDEX IF NOT EXISTS idx_images_immich ON images(immich_asset_id) WHERE immich_asset_id IS NOT NULL"),
        ("idx_videos_immich", "CREATE INDEX IF NOT EXISTS idx_videos_immich ON videos(immich_asset_id) WHERE immich_asset_id IS NOT NULL"),
        ("idx_images_gps", "CREATE INDEX IF NOT EXISTS idx_images_gps ON images(gps_lat, gps_lon) WHERE gps_lat IS NOT NULL"),
        ("idx_videos_gps", "CREATE INDEX IF NOT EXISTS idx_videos_gps ON videos(gps_lat, gps_lon) WHERE gps_lat IS NOT NULL"),
        ("idx_urls_archive_status", "CREATE INDEX IF NOT EXISTS idx_urls_archive_status ON urls(archive_status)"),
    ]

    for idx_name, idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
            logger.info(f"  Created index: {idx_name}")
        except sqlite3.OperationalError as e:
            logger.warning(f"  Index {idx_name} already exists or error: {e}")

    logger.info("Index creation complete")


def update_version(cursor: sqlite3.Cursor) -> None:
    """Update schema version in versions table."""
    logger.info("Updating schema version...")

    timestamp = normalize_datetime(datetime.now())

    # Check if versions table exists
    if not table_exists(cursor, 'versions'):
        logger.warning("versions table does not exist, creating it...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                modules TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                ver_updated TEXT NOT NULL
            )
        """)

    # Update or insert version
    cursor.execute("""
        INSERT OR REPLACE INTO versions (modules, version, ver_updated)
        VALUES ('aupat_core', '0.1.2', ?)
    """, (timestamp,))

    logger.info("Schema version updated to 0.1.2")


def run_migration(db_path: str, backup: bool = True) -> None:
    """Run full v0.1.2 database migration."""
    logger.info(f"Starting v0.1.2 migration for database: {db_path}")

    # Check if database exists
    db_file = Path(db_path)
    if not db_file.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. "
            "Run db_migrate.py first to create initial schema."
        )

    # Backup database if requested
    if backup:
        try:
            from backup import backup_database
            backup_database(db_path)
            logger.info("Database backup created")
        except ImportError:
            logger.warning("backup.py not found - skipping backup")
        except Exception as e:
            logger.warning(f"Backup failed (continuing anyway): {e}")

    # Connect and enable WAL mode
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    cursor = conn.cursor()

    try:
        # Run migrations
        migrate_locations_table(cursor)
        migrate_images_table(cursor)
        migrate_videos_table(cursor)
        migrate_urls_table(cursor)
        create_google_maps_exports_table(cursor)
        create_sync_log_table(cursor)
        create_indexes(cursor)
        update_version(cursor)

        # Commit changes
        conn.commit()
        logger.info("All migrations committed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        logger.info("Rolled back changes")
        raise

    finally:
        conn.close()

    logger.info("v0.1.2 migration complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AUPAT v0.1.2 Database Schema Migration'
    )
    parser.add_argument(
        '--config',
        help='Path to user.json config file'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip database backup before migration'
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = load_user_config(args.config)
        db_path = config['db_loc']

        # Run migration
        run_migration(db_path, backup=not args.no_backup)

        logger.info("\nMigration successful!")
        logger.info("Database is now at schema version 0.1.2")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
