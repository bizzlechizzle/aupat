#!/usr/bin/env python3
"""
AUPAT Database Migration Script for v0.1.3
Consolidated migration including v0.1.2 + v0.1.3 features.

This script:
1. Adds new columns to existing tables (v0.1.2)
2. Creates new tables for Google Maps imports and sync tracking (v0.1.2)
3. Enhances google_maps_exports table with import tracking fields (v0.1.3)
4. Adds source_map_id to locations table for import tracking (v0.1.3)
5. Creates map_locations table for reference mode imports (v0.1.3)
6. Adds performance indexes for map queries and fuzzy matching (v0.1.2 + v0.1.3)
7. Maintains backward compatibility with v0.1.0 schema

Version: 0.1.3 (consolidated migration)
Last Updated: 2025-11-18
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


def create_base_tables(cursor: sqlite3.Cursor) -> None:
    """Create base v0.1.2 schema if tables don't exist."""
    logger.info("Checking for base tables...")

    # Create locations table if it doesn't exist
    if not table_exists(cursor, 'locations'):
        logger.info("Creating locations table with v0.1.2 schema...")
        cursor.execute("""
            CREATE TABLE locations (
                loc_uuid TEXT PRIMARY KEY,
                loc_name TEXT NOT NULL,
                aka_name TEXT,
                state TEXT NOT NULL,
                type TEXT NOT NULL,
                sub_type TEXT,
                org_loc TEXT,
                loc_loc TEXT,
                loc_add TEXT,
                loc_update TEXT,
                imp_author TEXT,
                json_update TEXT,
                lat REAL,
                lon REAL,
                gps_source TEXT,
                gps_confidence REAL,
                street_address TEXT,
                city TEXT,
                state_abbrev TEXT,
                zip_code TEXT,
                country TEXT DEFAULT 'USA',
                address_source TEXT
            )
        """)

    # Create images table if it doesn't exist
    if not table_exists(cursor, 'images'):
        logger.info("Creating images table with v0.1.2 schema...")
        cursor.execute("""
            CREATE TABLE images (
                img_uuid TEXT PRIMARY KEY,
                loc_uuid TEXT NOT NULL,
                sub_uuid TEXT,
                img_sha TEXT NOT NULL,
                img_name TEXT,
                img_ext TEXT,
                img_path TEXT,
                img_taken TEXT,
                img_add TEXT,
                img_update TEXT,
                camera_make TEXT,
                camera_model TEXT,
                camera_type TEXT,
                immich_asset_id TEXT UNIQUE,
                img_width INTEGER,
                img_height INTEGER,
                img_size_bytes INTEGER,
                gps_lat REAL,
                gps_lon REAL,
                FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
            )
        """)

    # Create videos table if it doesn't exist
    if not table_exists(cursor, 'videos'):
        logger.info("Creating videos table with v0.1.2 schema...")
        cursor.execute("""
            CREATE TABLE videos (
                vid_uuid TEXT PRIMARY KEY,
                loc_uuid TEXT NOT NULL,
                sub_uuid TEXT,
                vid_sha TEXT NOT NULL,
                vid_name TEXT,
                vid_ext TEXT,
                vid_path TEXT,
                vid_taken TEXT,
                vid_add TEXT,
                vid_update TEXT,
                camera_make TEXT,
                camera_model TEXT,
                camera_type TEXT,
                immich_asset_id TEXT UNIQUE,
                vid_width INTEGER,
                vid_height INTEGER,
                vid_duration_sec REAL,
                vid_size_bytes INTEGER,
                gps_lat REAL,
                gps_lon REAL,
                FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
            )
        """)

    # Create documents table if it doesn't exist
    if not table_exists(cursor, 'documents'):
        logger.info("Creating documents table with v0.1.2 schema...")
        cursor.execute("""
            CREATE TABLE documents (
                doc_uuid TEXT PRIMARY KEY,
                loc_uuid TEXT NOT NULL,
                sub_uuid TEXT,
                doc_sha TEXT NOT NULL,
                doc_name TEXT,
                doc_ext TEXT,
                doc_path TEXT,
                doc_add TEXT,
                doc_update TEXT,
                FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
            )
        """)

    # Create urls table if it doesn't exist
    if not table_exists(cursor, 'urls'):
        logger.info("Creating urls table with v0.1.2 schema...")
        cursor.execute("""
            CREATE TABLE urls (
                url_uuid TEXT PRIMARY KEY,
                loc_uuid TEXT NOT NULL,
                sub_uuid TEXT,
                url TEXT NOT NULL,
                url_title TEXT,
                url_desc TEXT,
                url_add TEXT,
                url_update TEXT,
                archivebox_snapshot_id TEXT,
                archive_status TEXT DEFAULT 'pending',
                archive_date TEXT,
                FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
            )
        """)

    logger.info("Base tables verified/created")


def migrate_locations_table(cursor: sqlite3.Cursor) -> None:
    """Add v0.1.2 and v0.1.3 columns to locations table."""
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

    # v0.1.3: Map import tracking
    if 'source_map_id' not in existing_columns:
        logger.info("  Adding source_map_id column (v0.1.3)")
        cursor.execute("ALTER TABLE locations ADD COLUMN source_map_id TEXT")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_locations_source_map
            ON locations(source_map_id)
            WHERE source_map_id IS NOT NULL
        """)

    logger.info("Locations table migration complete")


def migrate_images_table(cursor: sqlite3.Cursor) -> None:
    """Add v0.1.2 columns to images table."""
    logger.info("Migrating images table...")

    existing_columns = get_table_columns(cursor, 'images')

    # Immich integration
    if 'immich_asset_id' not in existing_columns:
        logger.info("  Adding immich_asset_id column")
        cursor.execute("ALTER TABLE images ADD COLUMN immich_asset_id TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_images_immich_asset_id ON images(immich_asset_id)")

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

    # Phase D: Media extraction tracking
    if 'source_url' not in existing_columns:
        logger.info("  Adding source_url column (Phase D)")
        cursor.execute("ALTER TABLE images ADD COLUMN source_url TEXT")

    logger.info("Images table migration complete")


def migrate_videos_table(cursor: sqlite3.Cursor) -> None:
    """Add v0.1.2 columns to videos table."""
    logger.info("Migrating videos table...")

    existing_columns = get_table_columns(cursor, 'videos')

    # Immich integration
    if 'immich_asset_id' not in existing_columns:
        logger.info("  Adding immich_asset_id column")
        cursor.execute("ALTER TABLE videos ADD COLUMN immich_asset_id TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_videos_immich_asset_id ON videos(immich_asset_id)")

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

    # Phase D: Media extraction tracking
    if 'source_url' not in existing_columns:
        logger.info("  Adding source_url column (Phase D)")
        cursor.execute("ALTER TABLE videos ADD COLUMN source_url TEXT")

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


def migrate_google_maps_exports_table(cursor: sqlite3.Cursor) -> None:
    """Enhance google_maps_exports table for better map import tracking (v0.1.3)."""
    logger.info("Migrating google_maps_exports table...")

    existing_columns = get_table_columns(cursor, 'google_maps_exports')

    # Add new tracking columns
    if 'filename' not in existing_columns:
        logger.info("  Adding filename column")
        cursor.execute("ALTER TABLE google_maps_exports ADD COLUMN filename TEXT")

    if 'import_mode' not in existing_columns:
        logger.info("  Adding import_mode column (full/reference)")
        cursor.execute("ALTER TABLE google_maps_exports ADD COLUMN import_mode TEXT DEFAULT 'full'")

    if 'file_format' not in existing_columns:
        logger.info("  Adding file_format column (csv/geojson/kml)")
        cursor.execute("ALTER TABLE google_maps_exports ADD COLUMN file_format TEXT")

    if 'import_status' not in existing_columns:
        logger.info("  Adding import_status column")
        cursor.execute("ALTER TABLE google_maps_exports ADD COLUMN import_status TEXT DEFAULT 'completed'")

    if 'source_description' not in existing_columns:
        logger.info("  Adding source_description column")
        cursor.execute("ALTER TABLE google_maps_exports ADD COLUMN source_description TEXT")

    if 'locations_imported' not in existing_columns:
        logger.info("  Adding locations_imported column")
        cursor.execute("ALTER TABLE google_maps_exports ADD COLUMN locations_imported INTEGER DEFAULT 0")

    if 'locations_skipped' not in existing_columns:
        logger.info("  Adding locations_skipped column")
        cursor.execute("ALTER TABLE google_maps_exports ADD COLUMN locations_skipped INTEGER DEFAULT 0")

    if 'duplicates_found' not in existing_columns:
        logger.info("  Adding duplicates_found column")
        cursor.execute("ALTER TABLE google_maps_exports ADD COLUMN duplicates_found INTEGER DEFAULT 0")

    logger.info("google_maps_exports table migration complete")


def create_google_maps_exports_table(cursor: sqlite3.Cursor) -> None:
    """Create google_maps_exports table for tracking Google Maps imports."""
    logger.info("Creating google_maps_exports table...")

    if not table_exists(cursor, 'google_maps_exports'):
        cursor.execute("""
            CREATE TABLE google_maps_exports (
                export_id TEXT PRIMARY KEY,
                import_date TEXT NOT NULL,
                file_path TEXT NOT NULL,
                filename TEXT,
                import_mode TEXT DEFAULT 'full',
                file_format TEXT,
                import_status TEXT DEFAULT 'completed',
                source_description TEXT,
                locations_found INTEGER DEFAULT 0,
                locations_imported INTEGER DEFAULT 0,
                locations_skipped INTEGER DEFAULT 0,
                duplicates_found INTEGER DEFAULT 0,
                addresses_extracted INTEGER DEFAULT 0,
                images_processed INTEGER DEFAULT 0
            )
        """)
        logger.info("google_maps_exports table created with full schema")
    else:
        logger.info("google_maps_exports table already exists - migrating if needed")
        migrate_google_maps_exports_table(cursor)


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


def create_map_locations_table(cursor: sqlite3.Cursor) -> None:
    """Create map_locations table for storing imported map data (v0.1.3)."""
    logger.info("Creating map_locations table...")

    if not table_exists(cursor, 'map_locations'):
        cursor.execute("""
            CREATE TABLE map_locations (
                map_loc_id TEXT PRIMARY KEY,
                map_id TEXT NOT NULL,
                name TEXT NOT NULL,
                state TEXT,
                state_abbrev TEXT,
                type TEXT,
                lat REAL,
                lon REAL,
                street_address TEXT,
                city TEXT,
                zip_code TEXT,
                notes TEXT,
                original_data TEXT,
                created_date TEXT NOT NULL,
                FOREIGN KEY (map_id) REFERENCES google_maps_exports(export_id) ON DELETE CASCADE
            )
        """)

        # Create indexes for fast lookups
        cursor.execute("CREATE INDEX idx_map_locations_map_id ON map_locations(map_id)")
        cursor.execute("CREATE INDEX idx_map_locations_name_state ON map_locations(name, state_abbrev)")
        cursor.execute("CREATE INDEX idx_map_locations_gps ON map_locations(lat, lon) WHERE lat IS NOT NULL")

        logger.info("map_locations table created")
    else:
        logger.info("map_locations table already exists")


def create_indexes(cursor: sqlite3.Cursor) -> None:
    """Create performance indexes for v0.1.2 and v0.1.3."""
    logger.info("Creating performance indexes...")

    indexes = [
        # v0.1.2 indexes
        ("idx_locations_gps", "CREATE INDEX IF NOT EXISTS idx_locations_gps ON locations(lat, lon) WHERE lat IS NOT NULL"),
        ("idx_images_immich", "CREATE INDEX IF NOT EXISTS idx_images_immich ON images(immich_asset_id) WHERE immich_asset_id IS NOT NULL"),
        ("idx_videos_immich", "CREATE INDEX IF NOT EXISTS idx_videos_immich ON videos(immich_asset_id) WHERE immich_asset_id IS NOT NULL"),
        ("idx_images_gps", "CREATE INDEX IF NOT EXISTS idx_images_gps ON images(gps_lat, gps_lon) WHERE gps_lat IS NOT NULL"),
        ("idx_videos_gps", "CREATE INDEX IF NOT EXISTS idx_videos_gps ON videos(gps_lat, gps_lon) WHERE gps_lat IS NOT NULL"),
        ("idx_urls_archive_status", "CREATE INDEX IF NOT EXISTS idx_urls_archive_status ON urls(archive_status)"),
        # v0.1.3 indexes for map import and fuzzy matching
        ("idx_locations_name", "CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(loc_name)"),
        ("idx_locations_state", "CREATE INDEX IF NOT EXISTS idx_locations_state ON locations(state)"),
        ("idx_locations_name_state", "CREATE INDEX IF NOT EXISTS idx_locations_name_state ON locations(loc_name, state)"),
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

    timestamp = normalize_datetime(None)  # None = current time

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

    # Update or insert version (now at v0.1.3 with map import features)
    cursor.execute("""
        INSERT OR REPLACE INTO versions (modules, version, ver_updated)
        VALUES ('aupat_core', '0.1.3', ?)
    """, (timestamp,))

    logger.info("Schema version updated to 0.1.3 (includes v0.1.2 + map import features)")


def run_migration(db_path: str, backup: bool = True) -> None:
    """Run full v0.1.3 database migration (includes v0.1.2 + map import features)."""
    logger.info(f"Starting v0.1.3 migration for database: {db_path}")

    # Ensure database directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Backup database if it exists and backup is requested
    if backup and db_file.exists():
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
        # Create base tables if they don't exist (for fresh databases)
        create_base_tables(cursor)

        # Run migrations (for existing v0.1.0 databases)
        migrate_locations_table(cursor)  # Includes v0.1.3 source_map_id
        migrate_images_table(cursor)
        migrate_videos_table(cursor)
        migrate_urls_table(cursor)
        create_google_maps_exports_table(cursor)  # Includes v0.1.3 columns
        create_sync_log_table(cursor)
        create_map_locations_table(cursor)  # v0.1.3 new table
        create_indexes(cursor)  # Includes v0.1.3 name-based indexes
        update_version(cursor)  # Updates to v0.1.3

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

    logger.info("v0.1.3 migration complete (includes v0.1.2 + map import features)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AUPAT v0.1.3 Database Schema Migration (consolidated v0.1.2 + v0.1.3)'
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
        logger.info("Database is now at schema version 0.1.3")
        logger.info("Includes: v0.1.2 features + Map Import with KML/CSV/GeoJSON support")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
