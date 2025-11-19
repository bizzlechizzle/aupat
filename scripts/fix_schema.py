#!/usr/bin/env python3
"""
Quick fix to add missing columns to locations table.
Adds: pinned, favorite, documented
"""

import sqlite3
import sys
from pathlib import Path

def add_missing_columns():
    # Connect to database
    db_path = Path('/home/user/aupat/data/aupat.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(locations)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    print(f"Existing columns: {existing_columns}")

    # Add missing columns
    columns_to_add = {
        'pinned': 'INTEGER DEFAULT 0',
        'favorite': 'INTEGER DEFAULT 0',
        'documented': 'INTEGER DEFAULT 1'
    }

    for col_name, col_def in columns_to_add.items():
        if col_name not in existing_columns:
            print(f"Adding column: {col_name}")
            cursor.execute(f"ALTER TABLE locations ADD COLUMN {col_name} {col_def}")
        else:
            print(f"Column {col_name} already exists")

    # Create indexes for new columns
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_pinned ON locations(pinned)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_favorite ON locations(favorite)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_documented ON locations(documented)")

    conn.commit()
    conn.close()

    print("\nSchema fixed successfully!")

if __name__ == '__main__':
    add_missing_columns()
