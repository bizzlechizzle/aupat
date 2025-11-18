#!/usr/bin/env python3
"""
Database migration: Add browser integration tables

Adds bookmarks table and enhances urls table for browser workflow.
Migration is idempotent - safe to run multiple times.

Version: 0.1.2-browser
Created: 2025-11-18
"""

import logging
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from normalize import normalize_datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


def column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    """Check if column exists in table."""
    columns = get_table_columns(cursor, table_name)
    return column_name in columns


def migrate_add_bookmarks_table(cursor: sqlite3.Cursor) -> bool:
    """
    Create bookmarks table if it doesn't exist.

    Returns True if table was created, False if already exists.
    """
    if table_exists(cursor, 'bookmarks'):
        logger.info("  bookmarks table already exists, skipping creation")
        return False

    logger.info("  Creating bookmarks table...")
    cursor.execute("""
        CREATE TABLE bookmarks (
            bookmark_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT,
            url TEXT NOT NULL,
            title TEXT,
            description TEXT,
            favicon_url TEXT,
            folder TEXT,
            tags TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            visit_count INTEGER DEFAULT 0,
            last_visited TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE SET NULL
        )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX idx_bookmarks_loc_uuid ON bookmarks(loc_uuid)")
    cursor.execute("CREATE INDEX idx_bookmarks_folder ON bookmarks(folder)")
    cursor.execute("CREATE INDEX idx_bookmarks_created_at ON bookmarks(created_at)")

    logger.info("  bookmarks table created successfully")
    return True


def migrate_enhance_urls_table(cursor: sqlite3.Cursor) -> int:
    """
    Add browser-related columns to urls table.

    Returns count of columns added.
    """
    columns_added = 0

    if not table_exists(cursor, 'urls'):
        logger.warning("  urls table does not exist, cannot enhance")
        return 0

    # Add bookmark_uuid column
    if not column_exists(cursor, 'urls', 'bookmark_uuid'):
        logger.info("  Adding bookmark_uuid column to urls table...")
        cursor.execute("ALTER TABLE urls ADD COLUMN bookmark_uuid TEXT")
        cursor.execute("CREATE INDEX idx_urls_bookmark_uuid ON urls(bookmark_uuid)")
        columns_added += 1
    else:
        logger.info("  bookmark_uuid column already exists in urls table")

    # Add cookies_used column
    if not column_exists(cursor, 'urls', 'cookies_used'):
        logger.info("  Adding cookies_used column to urls table...")
        cursor.execute("ALTER TABLE urls ADD COLUMN cookies_used INTEGER DEFAULT 0")
        columns_added += 1
    else:
        logger.info("  cookies_used column already exists in urls table")

    # Add extraction_metadata column
    if not column_exists(cursor, 'urls', 'extraction_metadata'):
        logger.info("  Adding extraction_metadata column to urls table...")
        cursor.execute("ALTER TABLE urls ADD COLUMN extraction_metadata TEXT")
        columns_added += 1
    else:
        logger.info("  extraction_metadata column already exists in urls table")

    if columns_added > 0:
        logger.info(f"  Enhanced urls table with {columns_added} new columns")
    else:
        logger.info("  urls table already has all browser columns")

    return columns_added


def run_migration(db_path: str) -> dict:
    """
    Run browser integration migration.

    Args:
        db_path: Path to SQLite database

    Returns:
        Dictionary with migration results
    """
    logger.info(f"Starting browser integration migration on {db_path}")

    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # Create backup before migration
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup.{timestamp}"
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    except Exception as e:
        logger.warning(f"Failed to create backup: {e}")
        # Continue anyway - backup failure should not block migration

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    results = {
        'bookmarks_created': False,
        'urls_columns_added': 0,
        'success': False,
        'error': None,
        'backup_path': backup_path if Path(backup_path).exists() else None
    }

    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # Create bookmarks table
        results['bookmarks_created'] = migrate_add_bookmarks_table(cursor)

        # Enhance urls table
        results['urls_columns_added'] = migrate_enhance_urls_table(cursor)

        # Commit transaction
        conn.commit()
        results['success'] = True

        logger.info("Browser integration migration completed successfully")

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

    parser = argparse.ArgumentParser(
        description='Add browser integration tables to AUPAT database'
    )
    parser.add_argument(
        '--db-path',
        default='data/aupat.db',
        help='Path to SQLite database (default: data/aupat.db)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Check what would be migrated without applying changes'
    )

    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        # Read-only connection
        conn = sqlite3.connect(f"file:{args.db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        print("\nMigration preview:")
        print(f"  Database: {args.db_path}")

        if not table_exists(cursor, 'bookmarks'):
            print("  - Will create bookmarks table")
        else:
            print("  - bookmarks table already exists")

        if table_exists(cursor, 'urls'):
            cols_to_add = []
            if not column_exists(cursor, 'urls', 'bookmark_uuid'):
                cols_to_add.append('bookmark_uuid')
            if not column_exists(cursor, 'urls', 'cookies_used'):
                cols_to_add.append('cookies_used')
            if not column_exists(cursor, 'urls', 'extraction_metadata'):
                cols_to_add.append('extraction_metadata')

            if cols_to_add:
                print(f"  - Will add columns to urls table: {', '.join(cols_to_add)}")
            else:
                print("  - urls table already has all browser columns")
        else:
            print("  - WARNING: urls table does not exist")

        conn.close()
        print("\nRun without --dry-run to apply migration")
        return

    # Run actual migration
    try:
        results = run_migration(args.db_path)

        print("\nMigration Results:")
        print(f"  Success: {results['success']}")
        print(f"  Bookmarks table created: {results['bookmarks_created']}")
        print(f"  URLs columns added: {results['urls_columns_added']}")

        if results['error']:
            print(f"  Error: {results['error']}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
