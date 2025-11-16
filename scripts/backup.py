#!/usr/bin/env python3
"""
AUPAT Database Backup Script
Creates timestamped backups of the SQLite database using SQLite's backup API.

This script:
1. Loads database configuration from user.json
2. Creates timestamped backup using SQLite backup API
3. Verifies backup was created successfully
4. Records backup in versions table

Version: 1.0.0
Last Updated: 2025-11-15
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
    """
    Load user configuration from user.json.

    Args:
        config_path: Optional path to user.json (default: ../user/user.json)

    Returns:
        dict: Configuration with db_name, db_loc, db_backup paths

    Raises:
        FileNotFoundError: If user.json not found
        ValueError: If required keys missing
    """
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

    # Validate required keys
    required = ['db_name', 'db_loc', 'db_backup']
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing required keys in user.json: {missing}")

    return config


def get_most_recent_backup(backup_dir: Path, db_name: str) -> tuple:
    """
    Find the most recent backup in backup directory.

    Args:
        backup_dir: Path to backup directory
        db_name: Database name (e.g., 'aupat.db')

    Returns:
        tuple: (most_recent_path, most_recent_mtime) or (None, None)
    """
    if not backup_dir.exists():
        return None, None

    # Find all backups matching pattern: dbname-*.db
    base_name = db_name.replace('.db', '')
    pattern = f"{base_name}-*.db"
    backups = list(backup_dir.glob(pattern))

    if not backups:
        return None, None

    # Find most recent by modification time
    most_recent = max(backups, key=lambda p: p.stat().st_mtime)
    most_recent_mtime = most_recent.stat().st_mtime

    return most_recent, most_recent_mtime


def create_backup(source_db: str, backup_dir: str, db_name: str) -> str:
    """
    Create timestamped backup of database using SQLite backup API.

    Args:
        source_db: Path to source database
        backup_dir: Directory to store backup
        db_name: Database name for backup filename

    Returns:
        str: Path to created backup file

    Raises:
        FileNotFoundError: If source database doesn't exist
        IOError: If backup fails
    """
    source_path = Path(source_db)
    backup_path = Path(backup_dir)

    # Validate source exists
    if not source_path.exists():
        # Check if parent directory exists
        if not source_path.parent.exists():
            raise FileNotFoundError(
                f"Database directory does not exist: {source_path.parent}\n\n"
                f"Please ensure:\n"
                f"1. The directory '{source_path.parent}' exists\n"
                f"2. user.json has valid database path (not placeholder)\n"
                f"3. Create directory with: mkdir -p {source_path.parent}"
            )
        else:
            # Directory exists but database doesn't - this is OK for first run
            logger.info(f"Database file not found but directory exists. Will be created on first import: {source_db}")
            # Create empty database so backup can proceed
            conn = sqlite3.connect(source_db)
            conn.close()
            logger.info(f"Created new database file: {source_db}")

    # Create backup directory if it doesn't exist
    backup_path.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for backup filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    base_name = db_name.replace('.db', '')
    backup_filename = f"{base_name}-{timestamp}.db"
    backup_file = backup_path / backup_filename

    logger.info(f"Creating backup: {backup_file}")

    # Use SQLite backup API for safe backup
    try:
        # Connect to source and destination
        source_conn = sqlite3.connect(source_db)
        dest_conn = sqlite3.connect(str(backup_file))

        # Perform backup
        with dest_conn:
            source_conn.backup(dest_conn)

        # Close connections
        source_conn.close()
        dest_conn.close()

        logger.info(f"Backup created successfully: {backup_file}")
        return str(backup_file)

    except sqlite3.Error as e:
        logger.error(f"SQLite error during backup: {e}")
        # Clean up partial backup if it exists
        if backup_file.exists():
            backup_file.unlink()
        raise IOError(
            f"Failed to create database backup: {e}\n\n"
            f"This usually means:\n"
            f"1. Database file is corrupted or locked\n"
            f"2. Insufficient permissions to read database: {source_db}\n"
            f"3. Insufficient permissions to write backup: {backup_dir}"
        )
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        # Clean up partial backup if it exists
        if backup_file.exists():
            backup_file.unlink()
        raise IOError(f"Failed to create backup: {e}")


def verify_backup(backup_file: str, previous_mtime: float = None) -> bool:
    """
    Verify backup was created successfully.

    Args:
        backup_file: Path to backup file
        previous_mtime: Modification time of previous backup (optional)

    Returns:
        bool: True if backup is valid and newer than previous

    Raises:
        FileNotFoundError: If backup file doesn't exist
        ValueError: If backup is not newer than previous
    """
    backup_path = Path(backup_file)

    # Check backup exists
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    # Check backup has content
    size = backup_path.stat().st_size
    if size == 0:
        raise ValueError(f"Backup file is empty: {backup_file}")

    logger.info(f"Backup size: {size:,} bytes")

    # Check backup is newer than previous (if provided)
    if previous_mtime is not None:
        current_mtime = backup_path.stat().st_mtime
        if current_mtime <= previous_mtime:
            raise ValueError(
                f"New backup is not newer than previous backup. "
                f"Previous: {previous_mtime}, Current: {current_mtime}"
            )
        logger.info("Backup is newer than previous backup")

    # Try to open backup to verify it's valid SQLite
    try:
        conn = sqlite3.connect(str(backup_file))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        logger.info(f"Backup verified - {len(tables)} tables found")
        return True
    except Exception as e:
        raise ValueError(f"Backup file is not a valid SQLite database: {e}")


def record_backup_version(db_path: str, backup_file: str) -> None:
    """
    Record backup in versions table.

    Args:
        db_path: Path to source database
        backup_file: Path to created backup
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if versions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='versions'"
        )
        if not cursor.fetchone():
            logger.warning("versions table does not exist - skipping version record")
            conn.close()
            return

        # Record backup
        timestamp = normalize_datetime(None)  # Current time
        backup_name = Path(backup_file).name

        cursor.execute(
            """
            INSERT OR REPLACE INTO versions (modules, version, ver_updated)
            VALUES (?, ?, ?)
            """,
            (f"backup_{backup_name}", "1.0.0", timestamp)
        )

        conn.commit()
        conn.close()
        logger.info(f"Backup recorded in versions table: {backup_name}")

    except Exception as e:
        logger.warning(f"Failed to record backup in versions table: {e}")


def main():
    """Main backup workflow."""
    parser = argparse.ArgumentParser(
        description='Create timestamped backup of AUPAT database'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file (default: ../user/user.json)'
    )
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip backup verification (not recommended)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Step 1: Load configuration
        logger.info("Loading configuration from user.json...")
        config = load_user_config(args.config)

        db_name = config['db_name']
        db_loc = config['db_loc']
        db_backup = config['db_backup']

        logger.info(f"Database: {db_loc}")
        logger.info(f"Backup directory: {db_backup}")

        # Step 2: Get most recent backup (for verification)
        logger.info("Checking for previous backups...")
        backup_dir = Path(db_backup)
        previous_backup, previous_mtime = get_most_recent_backup(backup_dir, db_name)

        if previous_backup:
            logger.info(f"Most recent backup: {previous_backup.name}")
        else:
            logger.info("No previous backups found")

        # Step 3: Create backup
        logger.info("Creating backup...")
        backup_file = create_backup(db_loc, db_backup, db_name)

        # Step 4: Verify backup (unless skipped)
        if not args.no_verify:
            logger.info("Verifying backup...")
            verify_backup(backup_file, previous_mtime)
        else:
            logger.warning("Backup verification skipped (--no-verify)")

        # Step 5: Record in versions table
        logger.info("Recording backup in versions table...")
        record_backup_version(db_loc, backup_file)

        # Success
        logger.info("=" * 60)
        logger.info("BACKUP SUCCESSFUL")
        logger.info(f"Backup file: {backup_file}")
        logger.info("=" * 60)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except IOError as e:
        logger.error(f"I/O error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
