#!/usr/bin/env python3
"""
AUPAT Database Migration Script for v0.1.4
Adds import batch tracking for archive workflow.

This script adds:
1. import_batches table - Track bulk import operations
2. import_log table - Track individual file import operations
3. hardware_category field to images/videos - Track device type (phone/DSLR/drone)
4. archive_path field to images/videos - Track final archive location
5. import_batch_id field to images/videos - Link files to import batches

This implements the exact workflow from archive/v0.1.0/scripts:
- backup.py → Import batch tracking
- db_import.py → File staging and SHA256 deduplication
- db_organize.py → EXIF extraction and hardware categorization
- db_folder.py → Archive folder structure creation
- db_ingest.py → Hardlink staging → archive
- db_verify.py → Integrity verification and cleanup

Version: 0.1.4 (archive workflow tracking)
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


def create_import_batches_table(cursor: sqlite3.Cursor) -> None:
    """Create import_batches table for tracking bulk import operations."""
    logger.info("Creating import_batches table...")

    if not table_exists(cursor, 'import_batches'):
        cursor.execute("""
            CREATE TABLE import_batches (
                batch_id TEXT PRIMARY KEY,
                loc_uuid TEXT NOT NULL,
                source_path TEXT NOT NULL,
                batch_start TEXT NOT NULL,
                batch_end TEXT,
                status TEXT DEFAULT 'running',
                total_files INTEGER DEFAULT 0,
                files_imported INTEGER DEFAULT 0,
                files_skipped INTEGER DEFAULT 0,
                files_failed INTEGER DEFAULT 0,
                duplicates_found INTEGER DEFAULT 0,
                total_bytes INTEGER DEFAULT 0,
                backup_created INTEGER DEFAULT 0,
                backup_path TEXT,
                error_log TEXT,
                FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_import_batches_loc ON import_batches(loc_uuid)")
        cursor.execute("CREATE INDEX idx_import_batches_status ON import_batches(status)")
        cursor.execute("CREATE INDEX idx_import_batches_start ON import_batches(batch_start)")

        logger.info("import_batches table created")
    else:
        logger.info("import_batches table already exists")


def create_import_log_table(cursor: sqlite3.Cursor) -> None:
    """Create import_log table for tracking individual file imports."""
    logger.info("Creating import_log table...")

    if not table_exists(cursor, 'import_log'):
        cursor.execute("""
            CREATE TABLE import_log (
                log_id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_sha256 TEXT NOT NULL,
                file_size_bytes INTEGER,
                media_type TEXT,
                timestamp TEXT NOT NULL,
                stage TEXT NOT NULL,
                status TEXT NOT NULL,
                img_uuid TEXT,
                vid_uuid TEXT,
                hardware_category TEXT,
                staging_path TEXT,
                archive_path TEXT,
                error_message TEXT,
                FOREIGN KEY (batch_id) REFERENCES import_batches(batch_id) ON DELETE CASCADE,
                FOREIGN KEY (img_uuid) REFERENCES images(img_uuid) ON DELETE SET NULL,
                FOREIGN KEY (vid_uuid) REFERENCES videos(vid_uuid) ON DELETE SET NULL
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_import_log_batch ON import_log(batch_id)")
        cursor.execute("CREATE INDEX idx_import_log_sha256 ON import_log(file_sha256)")
        cursor.execute("CREATE INDEX idx_import_log_status ON import_log(status)")
        cursor.execute("CREATE INDEX idx_import_log_stage ON import_log(stage)")

        logger.info("import_log table created")
    else:
        logger.info("import_log table already exists")


def migrate_images_table(cursor: sqlite3.Cursor) -> None:
    """Add archive workflow columns to images table."""
    logger.info("Migrating images table for archive workflow...")

    # Check if table exists first
    if not table_exists(cursor, 'images'):
        logger.info("Images table does not exist - skipping migration (will be created by v0.1.3)")
        return

    existing_columns = get_table_columns(cursor, 'images')

    if 'hardware_category' not in existing_columns:
        logger.info("  Adding hardware_category column (phone/dslr/drone)")
        cursor.execute("ALTER TABLE images ADD COLUMN hardware_category TEXT")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_hardware ON images(hardware_category)")

    if 'archive_path' not in existing_columns:
        logger.info("  Adding archive_path column")
        cursor.execute("ALTER TABLE images ADD COLUMN archive_path TEXT")

    if 'staging_path' not in existing_columns:
        logger.info("  Adding staging_path column")
        cursor.execute("ALTER TABLE images ADD COLUMN staging_path TEXT")

    if 'import_batch_id' not in existing_columns:
        logger.info("  Adding import_batch_id column")
        cursor.execute("ALTER TABLE images ADD COLUMN import_batch_id TEXT")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_batch ON images(import_batch_id)")

    if 'verified' not in existing_columns:
        logger.info("  Adding verified column (SHA256 verification)")
        cursor.execute("ALTER TABLE images ADD COLUMN verified INTEGER DEFAULT 0")

    if 'verification_date' not in existing_columns:
        logger.info("  Adding verification_date column")
        cursor.execute("ALTER TABLE images ADD COLUMN verification_date TEXT")

    logger.info("Images table migration complete")


def migrate_videos_table(cursor: sqlite3.Cursor) -> None:
    """Add archive workflow columns to videos table."""
    logger.info("Migrating videos table for archive workflow...")

    # Check if table exists first
    if not table_exists(cursor, 'videos'):
        logger.info("Videos table does not exist - skipping migration (will be created by v0.1.3)")
        return

    existing_columns = get_table_columns(cursor, 'videos')

    if 'hardware_category' not in existing_columns:
        logger.info("  Adding hardware_category column (phone/dslr/drone)")
        cursor.execute("ALTER TABLE videos ADD COLUMN hardware_category TEXT")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_hardware ON videos(hardware_category)")

    if 'archive_path' not in existing_columns:
        logger.info("  Adding archive_path column")
        cursor.execute("ALTER TABLE videos ADD COLUMN archive_path TEXT")

    if 'staging_path' not in existing_columns:
        logger.info("  Adding staging_path column")
        cursor.execute("ALTER TABLE videos ADD COLUMN staging_path TEXT")

    if 'import_batch_id' not in existing_columns:
        logger.info("  Adding import_batch_id column")
        cursor.execute("ALTER TABLE videos ADD COLUMN import_batch_id TEXT")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_batch ON videos(import_batch_id)")

    if 'verified' not in existing_columns:
        logger.info("  Adding verified column (SHA256 verification)")
        cursor.execute("ALTER TABLE videos ADD COLUMN verified INTEGER DEFAULT 0")

    if 'verification_date' not in existing_columns:
        logger.info("  Adding verification_date column")
        cursor.execute("ALTER TABLE videos ADD COLUMN verification_date TEXT")

    logger.info("Videos table migration complete")


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
        VALUES ('aupat_core', '0.1.4', ?)
    """, (timestamp,))

    logger.info("Schema version updated to 0.1.4 (archive workflow tracking)")


def run_migration(db_path: str, backup: bool = True) -> None:
    """Run v0.1.4 database migration (archive workflow tracking)."""
    logger.info(f"Starting v0.1.4 migration for database: {db_path}")

    # Ensure database directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if database has schema (not just if file exists)
    needs_v013_migration = False
    if db_file.exists():
        # File exists - check if it has the base schema
        try:
            check_conn = sqlite3.connect(db_path)
            check_cursor = check_conn.cursor()
            check_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='locations'"
            )
            if not check_cursor.fetchone():
                needs_v013_migration = True
            check_conn.close()
        except sqlite3.DatabaseError:
            # Corrupt or empty database
            needs_v013_migration = True
    else:
        # File doesn't exist
        needs_v013_migration = True

    # Backup database if it exists and has data
    if backup and db_file.exists() and not needs_v013_migration:
        try:
            from backup import backup_database
            backup_database(db_path)
            logger.info("Database backup created")
        except ImportError:
            logger.warning("backup.py not found - skipping backup")
        except Exception as e:
            logger.warning(f"Backup failed (continuing anyway): {e}")

    # If database needs v0.1.3 migration, run it first
    if needs_v013_migration:
        logger.info("Database needs v0.1.3 schema - running v0.1.3 migration first...")
        try:
            from db_migrate_v012 import run_migration as run_v013_migration
            run_v013_migration(db_path, backup=False)
            logger.info("v0.1.3 migration complete")
        except Exception as e:
            logger.error(f"v0.1.3 migration failed: {e}")
            raise

    # Connect and enable WAL mode
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    cursor = conn.cursor()

    try:
        # Create new tables
        create_import_batches_table(cursor)
        create_import_log_table(cursor)

        # Migrate existing tables
        migrate_images_table(cursor)
        migrate_videos_table(cursor)

        # Update version
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

    logger.info("v0.1.4 migration complete (archive workflow tracking)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AUPAT v0.1.4 Database Schema Migration (archive workflow tracking)'
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
        logger.info("Database is now at schema version 0.1.4")
        logger.info("Archive workflow tracking features added:")
        logger.info("  - import_batches table (track bulk imports)")
        logger.info("  - import_log table (track individual files)")
        logger.info("  - hardware_category field (phone/dslr/drone)")
        logger.info("  - archive_path tracking")
        logger.info("  - SHA256 verification tracking")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
