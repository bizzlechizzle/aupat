#!/usr/bin/env python3
"""
AUPAT Database Migration Script for v0.1.3
Adds schema enhancements for Map Import feature with two modes:
1. Full Import Mode - Import all map data into locations table
2. Reference Mode - Keep maps in memory for fuzzy matching suggestions

This script:
1. Enhances google_maps_exports table with better tracking
2. Adds source_map_id to locations table
3. Creates map_reference_cache table for reference mode
4. Creates map_locations table for storing imported map data
5. Adds fuzzy matching indexes for name-based searches

Version: 0.1.3
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


def migrate_google_maps_exports_table(cursor: sqlite3.Cursor) -> None:
    """Enhance google_maps_exports table for better map import tracking."""
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


def migrate_locations_table(cursor: sqlite3.Cursor) -> None:
    """Add source_map_id to locations table."""
    logger.info("Migrating locations table for map imports...")

    existing_columns = get_table_columns(cursor, 'locations')

    if 'source_map_id' not in existing_columns:
        logger.info("  Adding source_map_id column")
        cursor.execute("ALTER TABLE locations ADD COLUMN source_map_id TEXT")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_locations_source_map
            ON locations(source_map_id)
            WHERE source_map_id IS NOT NULL
        """)

    logger.info("Locations table migration complete")


def create_map_locations_table(cursor: sqlite3.Cursor) -> None:
    """Create map_locations table for storing imported map data."""
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


def create_map_reference_cache_table(cursor: sqlite3.Cursor) -> None:
    """Create map_reference_cache table for reference mode caching."""
    logger.info("Creating map_reference_cache table...")

    if not table_exists(cursor, 'map_reference_cache'):
        cursor.execute("""
            CREATE TABLE map_reference_cache (
                cache_id TEXT PRIMARY KEY,
                map_id TEXT NOT NULL,
                cache_data TEXT NOT NULL,
                total_locations INTEGER DEFAULT 0,
                states_covered TEXT,
                last_used TEXT,
                created_date TEXT NOT NULL,
                FOREIGN KEY (map_id) REFERENCES google_maps_exports(export_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("CREATE INDEX idx_map_reference_cache_map_id ON map_reference_cache(map_id)")

        logger.info("map_reference_cache table created")
    else:
        logger.info("map_reference_cache table already exists")


def create_indexes(cursor: sqlite3.Cursor) -> None:
    """Create additional performance indexes for v0.1.3."""
    logger.info("Creating performance indexes for map import...")

    indexes = [
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

    # Update or insert version
    cursor.execute("""
        INSERT OR REPLACE INTO versions (modules, version, ver_updated)
        VALUES ('aupat_core', '0.1.3', ?)
    """, (timestamp,))

    logger.info("Schema version updated to 0.1.3")


def run_migration(db_path: str, backup: bool = True) -> None:
    """Run full v0.1.3 database migration."""
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
        # Run migrations
        migrate_google_maps_exports_table(cursor)
        migrate_locations_table(cursor)
        create_map_locations_table(cursor)
        create_map_reference_cache_table(cursor)
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

    logger.info("v0.1.3 migration complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AUPAT v0.1.3 Database Schema Migration for Map Import Feature'
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
        logger.info("Map import feature tables created")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
