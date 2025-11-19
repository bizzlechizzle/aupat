#!/usr/bin/env python3
"""
AUPAT v0.1.0 Database Schema Migration
Creates fresh database schema for v0.1.0 specification ONLY.

This script creates:
- locations table (with all v0.1.0 fields from spec)
- sub_locations table
- images table
- videos table
- documents table
- urls table
- maps table
- bookmarks table (for Browser feature)
- notes table (for User Notes feature)

Version: 0.1.0
Last Updated: 2025-11-18
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


def load_user_config(config_path: str = None) -> dict:
    """Load user configuration from user.json."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"user.json not found at {config_path}. "
            "Create from user/user.json.template"
        )

    with open(config_path, 'r') as f:
        config = json.load(f)

    required = ['db_name', 'db_loc']
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing required keys in user.json: {missing}")

    return config


def create_v010_schema(cursor: sqlite3.Cursor) -> None:
    """Create complete v0.1.0 schema from spec."""
    logger.info("Creating v0.1.0 database schema...")

    # 1. Locations table
    logger.info("Creating locations table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            loc_uuid TEXT PRIMARY KEY,
            loc_name TEXT NOT NULL,
            loc_short TEXT,
            status TEXT,
            explored TEXT,
            type TEXT NOT NULL,
            sub_type TEXT,
            street TEXT,
            state TEXT NOT NULL,
            city TEXT,
            zip_code TEXT,
            county TEXT,
            region TEXT,
            gps_lat REAL,
            gps_lon REAL,
            import_author TEXT,
            historical INTEGER DEFAULT 0,
            pinned INTEGER DEFAULT 0,
            documented INTEGER DEFAULT 1,
            favorite INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 2. Sub-locations table
    logger.info("Creating sub_locations table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sub_locations (
            sub_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            sub_name TEXT NOT NULL,
            sub_short TEXT,
            is_primary INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
        )
    """)

    # 3. Images table
    logger.info("Creating images table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            img_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            sub_uuid TEXT,
            img_sha TEXT NOT NULL,
            original_name TEXT,
            original_path TEXT,
            img_name TEXT NOT NULL,
            img_ext TEXT,
            img_path TEXT,
            created_at TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
            FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
        )
    """)

    # 4. Videos table
    logger.info("Creating videos table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            vid_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            sub_uuid TEXT,
            vid_sha TEXT NOT NULL,
            original_name TEXT,
            original_path TEXT,
            vid_name TEXT NOT NULL,
            vid_ext TEXT,
            vid_path TEXT,
            created_at TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
            FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
        )
    """)

    # 5. Documents table
    logger.info("Creating documents table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            sub_uuid TEXT,
            doc_sha TEXT NOT NULL,
            original_name TEXT,
            original_path TEXT,
            doc_name TEXT NOT NULL,
            doc_ext TEXT,
            doc_path TEXT,
            created_at TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
            FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
        )
    """)

    # 6. URLs table
    logger.info("Creating urls table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            url_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            sub_uuid TEXT,
            url TEXT NOT NULL,
            title TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
            FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
        )
    """)

    # 7. Maps table
    logger.info("Creating maps table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maps (
            map_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            sub_uuid TEXT,
            map_sha TEXT NOT NULL,
            original_name TEXT,
            original_path TEXT,
            map_name TEXT NOT NULL,
            map_ext TEXT,
            map_path TEXT,
            created_at TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
            FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
        )
    """)

    # 8. Bookmarks table (Browser feature)
    logger.info("Creating bookmarks table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            bookmark_uuid TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT,
            state TEXT,
            type TEXT,
            loc_uuid TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE SET NULL
        )
    """)

    # 9. Notes table (User Notes feature)
    logger.info("Creating notes table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            note_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            title TEXT,
            content TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
        )
    """)


def create_indexes(cursor: sqlite3.Cursor) -> None:
    """Create performance indexes for v0.1.0."""
    logger.info("Creating database indexes...")

    indexes = [
        # Locations indexes
        "CREATE INDEX IF NOT EXISTS idx_locations_state ON locations(state)",
        "CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(type)",
        "CREATE INDEX IF NOT EXISTS idx_locations_historical ON locations(historical)",
        "CREATE INDEX IF NOT EXISTS idx_locations_pinned ON locations(pinned DESC)",
        "CREATE INDEX IF NOT EXISTS idx_locations_documented ON locations(documented)",
        "CREATE INDEX IF NOT EXISTS idx_locations_favorite ON locations(favorite)",
        "CREATE INDEX IF NOT EXISTS idx_locations_updated ON locations(updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_locations_gps ON locations(gps_lat, gps_lon)",

        # Sub-locations indexes
        "CREATE INDEX IF NOT EXISTS idx_sub_locations_loc ON sub_locations(loc_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_sub_locations_primary ON sub_locations(is_primary)",

        # Images indexes
        "CREATE INDEX IF NOT EXISTS idx_images_loc ON images(loc_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_images_sub ON images(sub_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_images_sha ON images(img_sha)",

        # Videos indexes
        "CREATE INDEX IF NOT EXISTS idx_videos_loc ON videos(loc_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_videos_sub ON videos(sub_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_videos_sha ON videos(vid_sha)",

        # Documents indexes
        "CREATE INDEX IF NOT EXISTS idx_documents_loc ON documents(loc_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_documents_sha ON documents(doc_sha)",

        # URLs indexes
        "CREATE INDEX IF NOT EXISTS idx_urls_loc ON urls(loc_uuid)",

        # Maps indexes
        "CREATE INDEX IF NOT EXISTS idx_maps_loc ON maps(loc_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_maps_sha ON maps(map_sha)",

        # Bookmarks indexes
        "CREATE INDEX IF NOT EXISTS idx_bookmarks_loc ON bookmarks(loc_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_bookmarks_state ON bookmarks(state)",
        "CREATE INDEX IF NOT EXISTS idx_bookmarks_type ON bookmarks(type)",

        # Notes indexes
        "CREATE INDEX IF NOT EXISTS idx_notes_loc ON notes(loc_uuid)",
    ]

    for idx in indexes:
        cursor.execute(idx)

    logger.info(f"Created {len(indexes)} indexes")


def run_migration(db_path: str) -> None:
    """Run v0.1.0 database migration."""
    logger.info(f"Creating v0.1.0 database: {db_path}")

    # Ensure database directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Connect and enable WAL mode
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    cursor = conn.cursor()

    try:
        # Create schema
        create_v010_schema(cursor)
        create_indexes(cursor)

        # Commit changes
        conn.commit()
        logger.info("Schema created successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='AUPAT v0.1.0 Database Schema Creation'
    )
    parser.add_argument(
        '--config',
        help='Path to user.json config file'
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = load_user_config(args.config)
        db_path = str(Path(config['db_loc']) / config['db_name'])

        # Run migration
        run_migration(db_path)

        logger.info("\nDatabase created successfully!")
        logger.info(f"Location: {db_path}")
        logger.info("Schema version: v0.1.0")

    except Exception as e:
        logger.error(f"Failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
