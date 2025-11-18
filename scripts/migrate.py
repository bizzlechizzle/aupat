#!/usr/bin/env python3
"""
AUPAT Database Migration Orchestrator

Manages database schema migrations in the correct order, tracking
which migrations have been applied and providing safe upgrade paths.

Usage:
    python scripts/migrate.py --status          # Show current version and pending migrations
    python scripts/migrate.py --list            # List all available migrations
    python scripts/migrate.py --upgrade         # Run all pending migrations
    python scripts/migrate.py --upgrade 0.1.4   # Upgrade to specific version

Version: 1.0.0
Last Updated: 2025-11-18
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Migration registry - defines all migrations in execution order
MIGRATIONS = [
    {
        'version': '0.1.2',
        'name': 'initial_schema',
        'description': 'Initial AUPAT schema (locations, images, videos, URLs)',
        'module': 'db_migrate_v012',
        'function': 'run_migration',
        'required': True
    },
    {
        'version': '0.1.3',
        'name': 'map_imports',
        'description': 'Map import support (KML, CSV, GeoJSON)',
        'module': 'db_migrate_v013',
        'function': 'run_migration',
        'required': False
    },
    {
        'version': '0.1.4',
        'name': 'archive_workflow',
        'description': 'Archive workflow tracking and import batches',
        'module': 'db_migrate_v014',
        'function': 'run_migration',
        'required': False
    },
    {
        'version': '0.1.4-browser',
        'name': 'browser_tables',
        'description': 'Browser bookmarks integration',
        'module': 'migrations.add_browser_tables',
        'function': 'run_migration',
        'required': False
    },
    {
        'version': '0.1.4-indexes',
        'name': 'performance_indexes',
        'description': 'Performance optimization indexes',
        'module': 'migrations.add_performance_indexes',
        'function': 'run_migration',
        'required': False
    }
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


def init_versions_table(cursor: sqlite3.Cursor) -> None:
    """Initialize or upgrade the versions table for migration tracking."""
    # Check if versions table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='versions'"
    )
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        logger.info("Creating versions table for migration tracking...")
        cursor.execute("""
            CREATE TABLE versions (
                migration_name TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                description TEXT,
                applied_at TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 1
            )
        """)
    else:
        # Check if it's the old schema (modules column)
        cursor.execute("PRAGMA table_info(versions)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'modules' in columns and 'migration_name' not in columns:
            logger.info("Upgrading versions table schema...")
            # Old schema - migrate to new schema
            cursor.execute("ALTER TABLE versions RENAME TO versions_old")

            cursor.execute("""
                CREATE TABLE versions (
                    migration_name TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    description TEXT,
                    applied_at TEXT NOT NULL,
                    success INTEGER NOT NULL DEFAULT 1
                )
            """)

            # Copy old data
            cursor.execute("""
                INSERT INTO versions (migration_name, version, applied_at, success)
                SELECT modules, version, ver_updated, 1
                FROM versions_old
            """)

            cursor.execute("DROP TABLE versions_old")
            logger.info("Versions table upgraded to new schema")


def get_applied_migrations(cursor: sqlite3.Cursor) -> List[str]:
    """Get list of migration names that have been applied."""
    try:
        cursor.execute("SELECT migration_name FROM versions WHERE success = 1")
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return []


def get_current_version(cursor: sqlite3.Cursor) -> Optional[str]:
    """Get the current schema version (highest applied migration version)."""
    try:
        cursor.execute("""
            SELECT version
            FROM versions
            WHERE success = 1
            ORDER BY applied_at DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.OperationalError:
        return None


def record_migration(cursor: sqlite3.Cursor, migration: Dict, success: bool = True) -> None:
    """Record a migration in the versions table."""
    timestamp = datetime.utcnow().isoformat() + 'Z'

    cursor.execute("""
        INSERT OR REPLACE INTO versions (migration_name, version, description, applied_at, success)
        VALUES (?, ?, ?, ?, ?)
    """, (
        migration['name'],
        migration['version'],
        migration['description'],
        timestamp,
        1 if success else 0
    ))


def run_migration(db_path: str, migration: Dict, backup: bool = True) -> bool:
    """
    Run a single migration.

    Args:
        db_path: Path to database file
        migration: Migration definition dictionary
        backup: Whether to backup database before migration

    Returns:
        bool: True if migration succeeded, False otherwise
    """
    logger.info(f"\nRunning migration: {migration['name']}")
    logger.info(f"Version: {migration['version']}")
    logger.info(f"Description: {migration['description']}")

    try:
        # Import the migration module dynamically
        module_path = f"scripts.{migration['module']}"
        logger.debug(f"Importing {module_path}")

        # Import the module
        import importlib
        module = importlib.import_module(module_path)

        # Get the migration function
        if not hasattr(module, migration['function']):
            logger.error(f"Migration function '{migration['function']}' not found in {module_path}")
            return False

        migrate_func = getattr(module, migration['function'])

        # Run the migration (pass backup flag if supported)
        try:
            migrate_func(db_path, backup=backup)
        except TypeError:
            # Function doesn't accept backup parameter
            migrate_func(db_path)

        logger.info(f"Migration {migration['name']} completed successfully")
        return True

    except ImportError as e:
        logger.error(f"Failed to import migration module: {e}")
        return False
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_status(db_path: str) -> None:
    """Show current migration status."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    init_versions_table(cursor)
    conn.commit()

    applied = get_applied_migrations(cursor)
    current_version = get_current_version(cursor)

    print("\n" + "=" * 70)
    print("AUPAT DATABASE MIGRATION STATUS")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Current Version: {current_version or 'None (fresh database)'}\n")

    print("Available Migrations:")
    print("-" * 70)
    print(f"{'Version':<12} {'Name':<20} {'Status':<10} {'Description'}")
    print("-" * 70)

    for migration in MIGRATIONS:
        status = "APPLIED" if migration['name'] in applied else "PENDING"
        required = " (required)" if migration['required'] else ""
        print(f"{migration['version']:<12} {migration['name']:<20} {status:<10} {migration['description']}{required}")

    print("-" * 70)

    pending_count = sum(1 for m in MIGRATIONS if m['name'] not in applied)
    print(f"\nApplied: {len(applied)}/{len(MIGRATIONS)}")
    print(f"Pending: {pending_count}")

    if pending_count > 0:
        print("\nTo upgrade: python scripts/migrate.py --upgrade")

    conn.close()


def list_migrations() -> None:
    """List all available migrations."""
    print("\n" + "=" * 70)
    print("AVAILABLE MIGRATIONS")
    print("=" * 70)
    print(f"\n{'Version':<12} {'Name':<20} {'Required':<10} {'Description'}")
    print("-" * 70)

    for migration in MIGRATIONS:
        required = "Yes" if migration['required'] else "No"
        print(f"{migration['version']:<12} {migration['name']:<20} {required:<10} {migration['description']}")

    print("-" * 70)
    print(f"\nTotal migrations: {len(MIGRATIONS)}")


def upgrade(db_path: str, target_version: str = None, backup: bool = True) -> bool:
    """
    Upgrade database to target version or latest.

    Args:
        db_path: Path to database file
        target_version: Target version to upgrade to (None = latest)
        backup: Whether to backup before each migration

    Returns:
        bool: True if all migrations succeeded
    """
    # Ensure database file exists
    db_file = Path(db_path)
    if not db_file.exists():
        logger.error(f"Database file not found: {db_path}")
        logger.info("Run db_migrate_v012.py to create initial schema")
        return False

    # Connect and initialize versions table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    init_versions_table(cursor)
    conn.commit()

    applied = get_applied_migrations(cursor)
    current_version = get_current_version(cursor)

    conn.close()

    logger.info(f"Current version: {current_version or 'None'}")

    # Determine which migrations to run
    migrations_to_run = []
    for migration in MIGRATIONS:
        if migration['name'] in applied:
            continue  # Already applied

        migrations_to_run.append(migration)

        # Stop if we've reached target version
        if target_version and migration['version'] == target_version:
            break

    if not migrations_to_run:
        logger.info("Database is already up to date!")
        return True

    logger.info(f"\nWill apply {len(migrations_to_run)} migration(s):")
    for m in migrations_to_run:
        logger.info(f"  - {m['version']}: {m['name']}")

    # Run each migration
    all_success = True
    for migration in migrations_to_run:
        success = run_migration(db_path, migration, backup=backup)

        # Record migration result
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        record_migration(cursor, migration, success=success)
        conn.commit()
        conn.close()

        if not success:
            logger.error(f"Migration {migration['name']} failed!")
            all_success = False
            break

    if all_success:
        logger.info("\n" + "=" * 70)
        logger.info("ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)

        # Show final status
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        final_version = get_current_version(cursor)
        conn.close()

        logger.info(f"\nDatabase upgraded to version: {final_version}")

    return all_success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AUPAT Database Migration Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migrate.py --status              Show current migration status
  python scripts/migrate.py --list                List all available migrations
  python scripts/migrate.py --upgrade             Upgrade to latest version
  python scripts/migrate.py --upgrade 0.1.4       Upgrade to specific version
  python scripts/migrate.py --upgrade --no-backup Upgrade without backups (faster, not recommended)
        """
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current migration status'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available migrations'
    )

    parser.add_argument(
        '--upgrade',
        nargs='?',
        const='latest',
        metavar='VERSION',
        help='Upgrade to VERSION or latest if no version specified'
    )

    parser.add_argument(
        '--config',
        help='Path to user.json config file'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip database backup before migrations (not recommended)'
    )

    args = parser.parse_args()

    # Require at least one command
    if not any([args.status, args.list, args.upgrade]):
        parser.print_help()
        return 0

    try:
        # --list doesn't need database configuration
        if args.list:
            list_migrations()
            return 0

        # Load configuration for database operations
        config = load_user_config(args.config)
        db_path = config['db_loc']

        if args.status:
            show_status(db_path)

        elif args.upgrade:
            target_version = None if args.upgrade == 'latest' else args.upgrade
            backup = not args.no_backup

            success = upgrade(db_path, target_version=target_version, backup=backup)
            return 0 if success else 1

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
