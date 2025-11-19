#!/usr/bin/env python3
"""
AUPAT v0.1.0 Database Migration - Add Stats Columns

Adds columns for dashboard statistics:
- pinned (INTEGER) - Pin location to dashboard
- documented (INTEGER) - Location has been documented
- favorite (INTEGER) - Mark as favorite

LILBITS: One function - add stats columns
"""

import sys
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_stats_columns(db_path: str) -> bool:
    """
    Add stats columns to locations table.

    Args:
        db_path: Path to SQLite database

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(locations)")
        columns = [col[1] for col in cursor.fetchall()]

        columns_to_add = []
        if 'pinned' not in columns:
            columns_to_add.append(('pinned', 'INTEGER DEFAULT 0'))
        if 'documented' not in columns:
            columns_to_add.append(('documented', 'INTEGER DEFAULT 1'))
        if 'favorite' not in columns:
            columns_to_add.append(('favorite', 'INTEGER DEFAULT 0'))

        if not columns_to_add:
            logger.info("All stats columns already exist")
            conn.close()
            return True

        # Add missing columns
        for col_name, col_def in columns_to_add:
            logger.info(f"Adding column: {col_name}")
            cursor.execute(f"ALTER TABLE locations ADD COLUMN {col_name} {col_def}")

        # Create indexes for performance
        logger.info("Creating indexes...")

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_pinned ON locations(pinned DESC)")
        except sqlite3.OperationalError:
            pass  # Index might already exist

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_documented ON locations(documented)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_favorite ON locations(favorite)")
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()

        logger.info("Successfully added stats columns and indexes")
        return True

    except Exception as e:
        logger.error(f"Failed to add stats columns: {e}")
        return False


if __name__ == '__main__':
    # Get database path from user.json
    import json

    try:
        user_json_path = Path(__file__).parent.parent / 'user' / 'user.json'

        if not user_json_path.exists():
            logger.error(f"user.json not found at {user_json_path}")
            sys.exit(1)

        with open(user_json_path, 'r') as f:
            config = json.load(f)

        db_loc = config.get('db_loc')
        db_name = config.get('db_name')

        if not db_loc or not db_name:
            logger.error("db_loc or db_name not found in user.json")
            sys.exit(1)

        db_path = Path(db_loc) / db_name

        if not db_path.exists():
            logger.error(f"Database not found at {db_path}")
            sys.exit(1)

        logger.info(f"Migrating database: {db_path}")

        if add_stats_columns(str(db_path)):
            logger.info("Migration completed successfully")
            sys.exit(0)
        else:
            logger.error("Migration failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Migration error: {e}")
        sys.exit(1)
