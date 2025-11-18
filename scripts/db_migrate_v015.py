#!/usr/bin/env python3
"""
AUPAT Database Migration Script for v0.1.5
Adds v0.1.0 completion features: Notes and Location Filters

This script adds:
1. notes table - User notes for locations (multiple notes per location)
2. is_favorite flag to locations - Mark favorite locations
3. is_historical flag to locations - Mark historically significant locations
4. is_undocumented flag to locations - Mark locations needing documentation

Version: 0.1.5
Last Updated: 2025-11-18
Purpose: Complete v0.1.0 specification requirements
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """
    Load database configuration from user/user.json.

    Returns:
        dict: Configuration with db_path

    Raises:
        FileNotFoundError: If user.json not found
        ValueError: If required keys missing
    """
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'

    if not config_path.exists():
        # Fallback to data/aupat.db if user.json doesn't exist
        return {'db_path': str(Path(__file__).parent.parent / 'data' / 'aupat.db')}

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Support both old (db_name + db_loc) and new (db_path) formats
    if 'db_path' in config:
        return config
    elif 'db_name' in config and 'db_loc' in config:
        db_path = Path(config['db_loc']) / config['db_name']
        return {'db_path': str(db_path)}
    else:
        raise ValueError("user.json must have 'db_path' or 'db_name'+'db_loc'")


def table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """
    Check if table exists in database.

    Args:
        cursor: Database cursor
        table_name: Name of table to check

    Returns:
        bool: True if table exists
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    """
    Check if column exists in table.

    Args:
        cursor: Database cursor
        table_name: Name of table
        column_name: Name of column to check

    Returns:
        bool: True if column exists
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def create_notes_table(cursor: sqlite3.Cursor) -> None:
    """
    Create notes table for user notes on locations.

    Multiple notes can be attached to each location.
    Notes have titles and content, with creation/update timestamps.

    Args:
        cursor: Database cursor
    """
    if table_exists(cursor, 'notes'):
        logger.info("notes table already exists, skipping creation")
        return

    logger.info("Creating notes table...")
    cursor.execute("""
        CREATE TABLE notes (
            note_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            title TEXT,
            content TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
        )
    """)

    # Index for fast lookups by location
    cursor.execute("""
        CREATE INDEX idx_notes_loc_uuid ON notes(loc_uuid)
    """)

    # Index for searching notes by title
    cursor.execute("""
        CREATE INDEX idx_notes_title ON notes(title)
    """)

    logger.info("notes table created successfully")


def add_location_filter_flags(cursor: sqlite3.Cursor) -> None:
    """
    Add filter flags to locations table.

    Adds:
    - is_favorite: Mark locations as favorites
    - is_historical: Mark historically significant locations
    - is_undocumented: Mark locations needing documentation

    All default to 0 (false) for existing locations.

    Args:
        cursor: Database cursor
    """
    if not table_exists(cursor, 'locations'):
        raise ValueError("locations table does not exist - run db_migrate_v012.py first")

    flags_to_add = [
        ('is_favorite', 'INTEGER DEFAULT 0'),
        ('is_historical', 'INTEGER DEFAULT 0'),
        ('is_undocumented', 'INTEGER DEFAULT 0')
    ]

    for flag_name, flag_type in flags_to_add:
        if column_exists(cursor, 'locations', flag_name):
            logger.info(f"Column {flag_name} already exists, skipping")
            continue

        logger.info(f"Adding {flag_name} column to locations table...")
        cursor.execute(f"""
            ALTER TABLE locations
            ADD COLUMN {flag_name} {flag_type}
        """)
        logger.info(f"{flag_name} column added successfully")

    # Add indexes for filter queries
    indexes_to_create = [
        ('idx_locations_favorite', 'is_favorite'),
        ('idx_locations_historical', 'is_historical'),
        ('idx_locations_undocumented', 'is_undocumented')
    ]

    for index_name, column_name in indexes_to_create:
        # Check if index exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            (index_name,)
        )
        if cursor.fetchone():
            logger.info(f"Index {index_name} already exists, skipping")
            continue

        logger.info(f"Creating index {index_name}...")
        cursor.execute(f"""
            CREATE INDEX {index_name} ON locations({column_name})
        """)
        logger.info(f"Index {index_name} created successfully")


def update_version_tracking(cursor: sqlite3.Cursor, version: str) -> None:
    """
    Update version tracking table.

    Records migration execution in versions table.
    Creates versions table if it doesn't exist.

    Args:
        cursor: Database cursor
        version: Version string (e.g., '0.1.5')
    """
    if not table_exists(cursor, 'versions'):
        logger.info("Creating versions table...")
        cursor.execute("""
            CREATE TABLE versions (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT
            )
        """)

    timestamp = datetime.now().isoformat()
    description = "v0.1.5: Add notes table and location filter flags"

    cursor.execute("""
        INSERT OR REPLACE INTO versions (version, applied_at, description)
        VALUES (?, ?, ?)
    """, (version, timestamp, description))

    logger.info(f"Version {version} recorded in database")


def run_migration(db_path: str) -> bool:
    """
    Execute v0.1.5 migration.

    Args:
        db_path: Path to SQLite database file

    Returns:
        bool: True if migration successful

    Raises:
        sqlite3.Error: If migration fails
    """
    logger.info(f"Starting v0.1.5 migration for database: {db_path}")

    # Check database exists
    if not Path(db_path).exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. "
            "Run db_migrate_v012.py first to create base schema."
        )

    try:
        # Connect with WAL mode for better concurrency
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        cursor = conn.cursor()

        # Run migrations in transaction
        cursor.execute("BEGIN")

        # 1. Create notes table
        create_notes_table(cursor)

        # 2. Add filter flags to locations
        add_location_filter_flags(cursor)

        # 3. Update version tracking
        update_version_tracking(cursor, '0.1.5')

        # Commit transaction
        conn.commit()
        logger.info("Migration completed successfully!")

        # Verify changes
        logger.info("\nVerification:")
        logger.info(f"  - notes table exists: {table_exists(cursor, 'notes')}")
        logger.info(f"  - is_favorite column exists: {column_exists(cursor, 'locations', 'is_favorite')}")
        logger.info(f"  - is_historical column exists: {column_exists(cursor, 'locations', 'is_historical')}")
        logger.info(f"  - is_undocumented column exists: {column_exists(cursor, 'locations', 'is_undocumented')}")

        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description='AUPAT v0.1.5 Database Migration - Add notes and filter flags'
    )
    parser.add_argument(
        '--db-path',
        help='Path to database file (overrides user.json)',
        default=None
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Check what would be migrated without making changes'
    )

    args = parser.parse_args()

    try:
        # Load configuration
        if args.db_path:
            db_path = args.db_path
        else:
            config = load_config()
            db_path = config['db_path']

        logger.info(f"Database: {db_path}")

        if args.dry_run:
            logger.info("DRY RUN - No changes will be made")
            logger.info("\nWould perform:")
            logger.info("  1. Create notes table")
            logger.info("  2. Add is_favorite column to locations")
            logger.info("  3. Add is_historical column to locations")
            logger.info("  4. Add is_undocumented column to locations")
            logger.info("  5. Create indexes for filter queries")
            logger.info("  6. Update version tracking to 0.1.5")
            return 0

        # Run migration
        success = run_migration(db_path)

        if success:
            logger.info("\n" + "="*60)
            logger.info("v0.1.5 migration completed successfully!")
            logger.info("="*60)
            logger.info("\nNext steps:")
            logger.info("  1. Test notes API endpoints")
            logger.info("  2. Test filter functionality in GUI")
            logger.info("  3. Verify indexes improve query performance")
            return 0
        else:
            return 1

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
