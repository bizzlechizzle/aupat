#!/usr/bin/env python3
"""
AUPAT Database Migration Script
Creates and manages the SQLite database schema.

This script:
1. Loads schema definitions from JSON files
2. Creates database if it doesn't exist
3. Creates all tables with proper constraints
4. Tracks schema versions in versions table
5. Handles schema migrations

Version: 1.0.0
Last Updated: 2025-11-15
"""

import argparse
import json
import logging
import sqlite3
import sys
import subprocess
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


# Schema definitions for all tables
SCHEMA_SQL = {
    'locations': """
        CREATE TABLE IF NOT EXISTS locations (
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
            json_update TEXT
        )
    """,

    'sub_locations': """
        CREATE TABLE IF NOT EXISTS sub_locations (
            sub_uuid TEXT PRIMARY KEY,
            sub_name TEXT NOT NULL,
            loc_uuid TEXT NOT NULL,
            org_loc TEXT,
            loc_loc TEXT,
            loc_add TEXT,
            loc_update TEXT,
            imp_author TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
        )
    """,

    'images': """
        CREATE TABLE IF NOT EXISTS images (
            img_sha256 TEXT UNIQUE NOT NULL,
            img_name TEXT NOT NULL,
            img_loc TEXT NOT NULL,
            original INTEGER,
            camera INTEGER,
            phone INTEGER,
            drone INTEGER,
            go_pro INTEGER,
            film INTEGER,
            other INTEGER,
            exiftool_hardware TEXT,
            img_hardware TEXT,
            loc_uuid TEXT NOT NULL,
            sub_uuid TEXT,
            img_loco TEXT,
            img_nameo TEXT,
            img_add TEXT,
            img_update TEXT,
            imp_author TEXT,
            img_docs TEXT,
            img_vids TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
            FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
        )
    """,

    'videos': """
        CREATE TABLE IF NOT EXISTS videos (
            vid_sha256 TEXT UNIQUE NOT NULL,
            vid_name TEXT NOT NULL,
            vid_loc TEXT NOT NULL,
            original INTEGER,
            camera INTEGER,
            drone INTEGER,
            phone INTEGER,
            go_pro INTEGER,
            dash_cam INTEGER,
            other INTEGER,
            ffmpeg_hardware TEXT,
            vid_hardware TEXT,
            loc_uuid TEXT NOT NULL,
            sub_uuid TEXT,
            vid_loco TEXT,
            vid_nameo TEXT,
            vid_add TEXT,
            vid_update TEXT,
            imp_author TEXT,
            vid_docs TEXT,
            vid_imgs TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
            FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
        )
    """,

    'documents': """
        CREATE TABLE IF NOT EXISTS documents (
            doc_sha256 TEXT UNIQUE NOT NULL,
            doc_name TEXT NOT NULL,
            doc_loc TEXT NOT NULL,
            doc_ext TEXT NOT NULL,
            loc_uuid TEXT NOT NULL,
            sub_uuid TEXT,
            doc_loco TEXT,
            doc_nameo TEXT,
            doc_add TEXT,
            doc_update TEXT,
            imp_author TEXT,
            docs_img TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
            FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
        )
    """,

    'urls': """
        CREATE TABLE IF NOT EXISTS urls (
            url_uuid TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            domain TEXT NOT NULL,
            url_loc TEXT,
            loc_uuid TEXT NOT NULL,
            sub_uuid TEXT,
            url_add TEXT,
            url_update TEXT,
            imp_author TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
            FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
        )
    """,

    'versions': """
        CREATE TABLE IF NOT EXISTS versions (
            modules TEXT PRIMARY KEY,
            version TEXT NOT NULL,
            ver_updated TEXT NOT NULL
        )
    """
}

# Indexes for performance
INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_locations_state_type ON locations(state, type)",
    "CREATE INDEX IF NOT EXISTS idx_images_loc_uuid ON images(loc_uuid)",
    "CREATE INDEX IF NOT EXISTS idx_images_camera ON images(loc_uuid, camera)",
    "CREATE INDEX IF NOT EXISTS idx_videos_loc_uuid ON videos(loc_uuid)",
    "CREATE INDEX IF NOT EXISTS idx_videos_drone ON videos(loc_uuid, drone)",
    "CREATE INDEX IF NOT EXISTS idx_documents_loc_uuid ON documents(loc_uuid)",
    "CREATE INDEX IF NOT EXISTS idx_documents_ext ON documents(doc_ext)",
    "CREATE INDEX IF NOT EXISTS idx_urls_loc_uuid ON urls(loc_uuid)",
    "CREATE INDEX IF NOT EXISTS idx_urls_domain ON urls(domain)",
]


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


def load_schema_version(schema_file: Path) -> str:
    """Extract version from schema JSON file."""
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
            return schema.get('version', '0.0.0')
    except Exception as e:
        logger.warning(f"Could not load version from {schema_file.name}: {e}")
        return '0.0.0'


def get_current_versions(cursor: sqlite3.Cursor) -> dict:
    """Get current schema versions from versions table."""
    try:
        cursor.execute("SELECT modules, version FROM versions")
        return {row[0]: row[1] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        # versions table doesn't exist yet
        return {}


def get_table_columns(cursor: sqlite3.Cursor, table_name: str) -> list:
    """Get list of column names for a table."""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def add_missing_columns(cursor: sqlite3.Cursor) -> None:
    """Add missing columns to existing tables for schema migrations."""
    migrations = [
        # Schema migrations will be added here as needed
        # Film photography fields should be in images table only, not locations table
    ]

    for migration in migrations:
        table = migration['table']
        existing_columns = get_table_columns(cursor, table)

        if not existing_columns:
            # Table doesn't exist yet, will be created with full schema
            continue

        for column_name, column_def in migration['columns']:
            if column_name not in existing_columns:
                logger.info(f"  Adding column {column_name} to {table}")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}")
            else:
                logger.debug(f"  Column {column_name} already exists in {table}")


def create_database(db_path: str, backup_first: bool = True) -> None:
    """
    Create or update database schema.

    Args:
        db_path: Path to database file
        backup_first: Whether to backup existing database first
    """
    db_file = Path(db_path)
    db_exists = db_file.exists()

    # Backup existing database if requested
    if db_exists and backup_first:
        logger.info("Backing up existing database...")
        try:
            # Call backup.py script
            backup_script = Path(__file__).parent / 'backup.py'
            result = subprocess.run(
                ['python3', str(backup_script)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                raise RuntimeError("Backup failed - aborting migration")
            logger.info("Backup successful")
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            raise RuntimeError("Backup failed - aborting migration")

    # Connect to database
    logger.info(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode = WAL")

    try:
        # Get current versions
        current_versions = get_current_versions(cursor)
        logger.info(f"Current schema versions: {current_versions}")

        # Load schema versions from JSON files
        data_dir = Path(__file__).parent.parent / 'data'
        schema_files = {
            'locations.json': data_dir / 'locations.json',
            'sub-locations.json': data_dir / 'sub-locations.json',
            'images.json': data_dir / 'images.json',
            'videos.json': data_dir / 'videos.json',
            'documents.json': data_dir / 'documents.json',
            'urls.json': data_dir / 'urls.json',
            'versions.json': data_dir / 'versions.json',
        }

        new_versions = {}
        for name, path in schema_files.items():
            if path.exists():
                new_versions[name] = load_schema_version(path)
            else:
                logger.warning(f"Schema file not found: {path}")
                new_versions[name] = '0.0.0'

        logger.info(f"Schema file versions: {new_versions}")

        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")

        # Create all tables
        logger.info("Creating/updating tables...")
        for table_name, sql in SCHEMA_SQL.items():
            logger.info(f"  Creating table: {table_name}")
            cursor.execute(sql)

        # Add missing columns to existing tables (migrations)
        logger.info("Checking for missing columns...")
        add_missing_columns(cursor)

        # Create indexes
        logger.info("Creating indexes...")
        for idx_sql in INDEXES_SQL:
            cursor.execute(idx_sql)

        # Update versions table
        logger.info("Updating versions table...")
        timestamp = normalize_datetime(None)

        for schema_name, version in new_versions.items():
            cursor.execute(
                """
                INSERT OR REPLACE INTO versions (modules, version, ver_updated)
                VALUES (?, ?, ?)
                """,
                (schema_name, version, timestamp)
            )

        # Record db_migrate.py version
        cursor.execute(
            """
            INSERT OR REPLACE INTO versions (modules, version, ver_updated)
            VALUES (?, ?, ?)
            """,
            ('db_migrate.py', '1.0.0', timestamp)
        )

        # Commit transaction
        conn.commit()
        logger.info("Schema migration successful")

        # Verify versions were recorded
        logger.info("Verifying versions table...")
        final_versions = get_current_versions(cursor)
        logger.info(f"Final versions: {final_versions}")

        # Check all schemas were recorded
        for schema_name in new_versions.keys():
            if schema_name not in final_versions:
                raise ValueError(f"Version not recorded for {schema_name}")

        logger.info("Verification successful")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise

    finally:
        conn.close()


def main():
    """Main migration workflow."""
    parser = argparse.ArgumentParser(
        description='Create/migrate AUPAT database schema'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file (default: ../user/user.json)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup before migration (not recommended)'
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
        db_path = config['db_loc']

        # Create/migrate database
        logger.info("=" * 60)
        logger.info("AUPAT Database Migration")
        logger.info("=" * 60)

        create_database(db_path, backup_first=not args.no_backup)

        logger.info("=" * 60)
        logger.info("MIGRATION SUCCESSFUL")
        logger.info(f"Database: {db_path}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
