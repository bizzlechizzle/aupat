#!/usr/bin/env python3
"""
Database migration: Add performance indexes for API endpoints

Adds indexes to improve query performance for:
- locations table: type, sub_type for autocomplete queries
- bookmarks table: title for search queries

Migration is idempotent - safe to run multiple times.

Version: 0.1.4-perf
Created: 2025-11-18
"""

import logging
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def index_exists(cursor: sqlite3.Cursor, index_name: str) -> bool:
    """Check if index exists."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,)
    )
    return cursor.fetchone() is not None


def table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """Check if table exists."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def add_locations_indexes(cursor: sqlite3.Cursor) -> int:
    """
    Add performance indexes to locations table.

    Returns count of indexes created.
    """
    if not table_exists(cursor, 'locations'):
        logger.warning("  locations table does not exist, skipping")
        return 0

    indexes_created = 0

    # Index for type filtering (autocomplete endpoint)
    if not index_exists(cursor, 'idx_locations_type'):
        logger.info("  Creating idx_locations_type...")
        cursor.execute("CREATE INDEX idx_locations_type ON locations(type) WHERE type IS NOT NULL")
        indexes_created += 1
    else:
        logger.info("  idx_locations_type already exists")

    # Index for sub_type filtering (autocomplete endpoint)
    if not index_exists(cursor, 'idx_locations_sub_type'):
        logger.info("  Creating idx_locations_sub_type...")
        cursor.execute("CREATE INDEX idx_locations_sub_type ON locations(sub_type) WHERE sub_type IS NOT NULL")
        indexes_created += 1
    else:
        logger.info("  idx_locations_sub_type already exists")

    # Composite index for type + sub_type queries
    if not index_exists(cursor, 'idx_locations_type_sub_type'):
        logger.info("  Creating idx_locations_type_sub_type...")
        cursor.execute("CREATE INDEX idx_locations_type_sub_type ON locations(type, sub_type) WHERE type IS NOT NULL")
        indexes_created += 1
    else:
        logger.info("  idx_locations_type_sub_type already exists")

    return indexes_created


def add_bookmarks_indexes(cursor: sqlite3.Cursor) -> int:
    """
    Add performance indexes to bookmarks table.

    Returns count of indexes created.
    """
    if not table_exists(cursor, 'bookmarks'):
        logger.warning("  bookmarks table does not exist, skipping")
        return 0

    indexes_created = 0

    # Index for title searches (LIKE queries)
    if not index_exists(cursor, 'idx_bookmarks_title'):
        logger.info("  Creating idx_bookmarks_title...")
        cursor.execute("CREATE INDEX idx_bookmarks_title ON bookmarks(title) WHERE title IS NOT NULL")
        indexes_created += 1
    else:
        logger.info("  idx_bookmarks_title already exists")

    return indexes_created


def run_migration(db_path: str) -> dict:
    """
    Run performance indexes migration.

    Args:
        db_path: Path to SQLite database

    Returns:
        Dictionary with migration results
    """
    logger.info(f"Starting performance indexes migration on {db_path}")

    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    results = {
        'locations_indexes_created': 0,
        'bookmarks_indexes_created': 0,
        'success': False,
        'error': None
    }

    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # Add locations indexes
        logger.info("Adding locations indexes...")
        results['locations_indexes_created'] = add_locations_indexes(cursor)

        # Add bookmarks indexes
        logger.info("Adding bookmarks indexes...")
        results['bookmarks_indexes_created'] = add_bookmarks_indexes(cursor)

        # Commit transaction
        conn.commit()
        results['success'] = True

        total = results['locations_indexes_created'] + results['bookmarks_indexes_created']
        logger.info(f"Performance indexes migration completed successfully ({total} indexes created)")

    except Exception as e:
        conn.rollback()
        results['error'] = str(e)
        logger.error(f"Migration failed: {e}")
        raise

    finally:
        conn.close()

    return results


def main():
    """Main entry point for migration script."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description='Add performance indexes to AUPAT database'
    )
    parser.add_argument(
        '--db-path',
        help='Path to SQLite database (defaults to user.json config)'
    )
    parser.add_argument(
        '--config',
        help='Path to user.json config file'
    )

    args = parser.parse_args()

    # Determine database path
    if args.db_path:
        db_path = args.db_path
    else:
        # Load from user.json
        config_path = args.config or Path(__file__).parent.parent.parent / 'user' / 'user.json'
        config_path = Path(config_path)

        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            logger.error("Use --db-path or --config to specify database location")
            sys.exit(1)

        with open(config_path, 'r') as f:
            config = json.load(f)

        db_path = config.get('db_loc')
        if not db_path:
            logger.error("db_loc not found in config file")
            sys.exit(1)

    # Run migration
    try:
        results = run_migration(db_path)

        print("\nMigration Results:")
        print(f"  Success: {results['success']}")
        print(f"  Locations indexes created: {results['locations_indexes_created']}")
        print(f"  Bookmarks indexes created: {results['bookmarks_indexes_created']}")

        if results['error']:
            print(f"  Error: {results['error']}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
