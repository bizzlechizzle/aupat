#!/usr/bin/env python3
"""
AUPAT Database Cleanup Script
Performs maintenance and integrity checks on the database.

This script:
1. Runs PRAGMA integrity_check
2. Verifies foreign key relationships
3. Cleans up old backups (retention policy)
4. Vacuums database to reclaim space
5. Generates maintenance report

Version: 1.0.0
Last Updated: 2025-11-15
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

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
        raise FileNotFoundError(f"user.json not found at {config_path}")

    with open(config_path, 'r') as f:
        import json
        return json.load(f)


def check_integrity(db_path: str) -> bool:
    """
    Run PRAGMA integrity_check on database.

    Args:
        db_path: Path to database

    Returns:
        bool: True if integrity check passed
    """
    logger.info("Running database integrity check...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]

        if result == 'ok':
            logger.info("✓ Database integrity check passed")
            return True
        else:
            logger.error(f"✗ Database integrity check failed: {result}")
            return False

    finally:
        conn.close()


def check_foreign_keys(db_path: str) -> int:
    """
    Verify foreign key relationships.

    Args:
        db_path: Path to database

    Returns:
        int: Number of foreign key violations found
    """
    logger.info("Checking foreign key relationships...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()

        if violations:
            logger.error(f"✗ Found {len(violations)} foreign key violations:")
            for violation in violations:
                logger.error(f"  {violation}")
            return len(violations)
        else:
            logger.info("✓ No foreign key violations found")
            return 0

    finally:
        conn.close()


def cleanup_old_backups(backup_dir: str, db_name: str, keep_days: int = 7) -> int:
    """
    Clean up old backups according to retention policy.

    Retention policy:
    - Keep all backups from last keep_days days
    - For older: keep first and last backup of each day
    - Never delete backups less than 24 hours old

    Args:
        backup_dir: Backup directory path
        db_name: Database name
        keep_days: Number of days to keep all backups

    Returns:
        int: Number of backups deleted
    """
    logger.info(f"Cleaning up old backups (retention: {keep_days} days)...")

    backup_path = Path(backup_dir)

    if not backup_path.exists():
        logger.warning(f"Backup directory not found: {backup_dir}")
        return 0

    # Find all backups
    base_name = db_name.replace('.db', '')
    pattern = f"{base_name}-*.db"
    backups = list(backup_path.glob(pattern))

    if not backups:
        logger.info("No backups found")
        return 0

    logger.info(f"Found {len(backups)} backups")

    # Calculate cutoff dates
    now = datetime.now()
    cutoff_recent = now - timedelta(days=keep_days)
    cutoff_24h = now - timedelta(hours=24)

    # Group backups by date
    backups_by_date = {}
    recent_backups = []
    deleted_count = 0

    for backup in backups:
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)

        # Never delete backups less than 24 hours old
        if mtime > cutoff_24h:
            recent_backups.append(backup)
            continue

        # Keep all backups from last keep_days days
        if mtime > cutoff_recent:
            recent_backups.append(backup)
            continue

        # Group older backups by date
        date_key = mtime.date()
        if date_key not in backups_by_date:
            backups_by_date[date_key] = []
        backups_by_date[date_key].append((backup, mtime))

    # For each date, keep first and last backup only
    for date_key, date_backups in backups_by_date.items():
        if len(date_backups) <= 2:
            # 2 or fewer backups - keep them all
            continue

        # Sort by time
        date_backups.sort(key=lambda x: x[1])

        # Keep first and last
        first_backup = date_backups[0][0]
        last_backup = date_backups[-1][0]

        # Delete intermediate backups
        for backup, mtime in date_backups[1:-1]:
            logger.info(f"Deleting old backup: {backup.name}")
            backup.unlink()
            deleted_count += 1

    logger.info(f"Deleted {deleted_count} old backups")
    logger.info(f"Retained {len(backups) - deleted_count} backups")

    return deleted_count


def vacuum_database(db_path: str) -> int:
    """
    Vacuum database to reclaim space.

    Args:
        db_path: Path to database

    Returns:
        int: Bytes reclaimed (approximate)
    """
    logger.info("Vacuuming database...")

    db_file = Path(db_path)
    size_before = db_file.stat().st_size

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("VACUUM")
        conn.commit()

    finally:
        conn.close()

    size_after = db_file.stat().st_size
    reclaimed = size_before - size_after

    logger.info(f"Database vacuumed: {reclaimed:,} bytes reclaimed")

    return reclaimed


def generate_statistics(db_path: str) -> dict:
    """
    Generate database statistics.

    Args:
        db_path: Path to database

    Returns:
        dict: Statistics about database contents
    """
    logger.info("Generating database statistics...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {}

    try:
        # Count records in each table
        cursor.execute("SELECT COUNT(*) FROM locations")
        stats['locations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sub_locations")
        stats['sub_locations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM images")
        stats['images'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM videos")
        stats['videos'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM documents")
        stats['documents'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM urls")
        stats['urls'] = cursor.fetchone()[0]

        # Database file size
        db_size = Path(db_path).stat().st_size
        stats['database_size_bytes'] = db_size
        stats['database_size_mb'] = db_size / (1024 * 1024)

        return stats

    finally:
        conn.close()


def main():
    """Main cleanup workflow."""
    parser = argparse.ArgumentParser(
        description='AUPAT database maintenance and cleanup'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file'
    )
    parser.add_argument(
        '--keep-days',
        type=int,
        default=7,
        help='Number of days to keep all backups (default: 7)'
    )
    parser.add_argument(
        '--no-vacuum',
        action='store_true',
        help='Skip database vacuum'
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

        logger.info("=" * 60)
        logger.info("AUPAT Database Cleanup")
        logger.info("=" * 60)

        # Run integrity check
        integrity_ok = check_integrity(config['db_loc'])

        # Check foreign keys
        fk_violations = check_foreign_keys(config['db_loc'])

        # Clean up old backups
        deleted_backups = cleanup_old_backups(
            config.get('db_backup', ''),
            config['db_name'],
            keep_days=args.keep_days
        )

        # Vacuum database
        if not args.no_vacuum:
            reclaimed = vacuum_database(config['db_loc'])
        else:
            logger.info("Skipping vacuum (--no-vacuum)")
            reclaimed = 0

        # Generate statistics
        stats = generate_statistics(config['db_loc'])

        # Print summary
        logger.info("=" * 60)
        logger.info("Maintenance Summary")
        logger.info("=" * 60)
        logger.info(f"Integrity check: {'PASSED' if integrity_ok else 'FAILED'}")
        logger.info(f"Foreign key violations: {fk_violations}")
        logger.info(f"Backups deleted: {deleted_backups}")
        logger.info(f"Space reclaimed: {reclaimed:,} bytes")
        logger.info("")
        logger.info("Database Statistics:")
        logger.info(f"  Locations: {stats['locations']:,}")
        logger.info(f"  Sub-locations: {stats['sub_locations']:,}")
        logger.info(f"  Images: {stats['images']:,}")
        logger.info(f"  Videos: {stats['videos']:,}")
        logger.info(f"  Documents: {stats['documents']:,}")
        logger.info(f"  URLs: {stats['urls']:,}")
        logger.info(f"  Database size: {stats['database_size_mb']:.2f} MB")
        logger.info("=" * 60)

        # Exit code based on integrity
        if not integrity_ok or fk_violations > 0:
            logger.error("CLEANUP COMPLETED WITH WARNINGS")
            return 1

        logger.info("CLEANUP SUCCESSFUL")
        return 0

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
