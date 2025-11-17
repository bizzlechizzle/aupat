#!/usr/bin/env python3
"""
freshstart.py - Clean slate script for fresh import testing

This script clears:
- SQLite database file
- Staging/ingest directory contents
- Archive directory contents (optional)
- Backup directory contents (optional)

Usage:
    python freshstart.py                    # Interactive mode with prompts
    python freshstart.py --yes              # Skip confirmations (danger!)
    python freshstart.py --keep-archive     # Keep archive directory
    python freshstart.py --keep-backups     # Keep backup files
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path


def load_config():
    """Load user configuration from user/user.json"""
    config_path = Path(__file__).parent / "user" / "user.json"

    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        print("Please create user/user.json from user/user.json.template")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {config_path}: {e}")
        sys.exit(1)


def confirm_action(message, auto_yes=False):
    """Ask user for confirmation unless auto_yes is True"""
    if auto_yes:
        return True

    response = input(f"{message} (yes/no): ").strip().lower()
    return response in ['yes', 'y']


def clear_database(db_path, auto_yes=False):
    """Remove the SQLite database file"""
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"✓ Database file doesn't exist: {db_file}")
        return True

    print(f"\n📁 Database file found: {db_file}")
    print(f"   Size: {db_file.stat().st_size / 1024 / 1024:.2f} MB")

    if not confirm_action("Delete database file?", auto_yes):
        print("  Skipped database deletion")
        return False

    try:
        db_file.unlink()
        print(f"✓ Deleted database: {db_file}")
        return True
    except Exception as e:
        print(f"✗ Error deleting database: {e}")
        return False


def clear_directory(dir_path, dir_name, auto_yes=False):
    """Clear all contents of a directory"""
    directory = Path(dir_path)

    if not directory.exists():
        print(f"✓ {dir_name} directory doesn't exist: {directory}")
        return True

    # Count contents
    try:
        contents = list(directory.iterdir())
        if not contents:
            print(f"✓ {dir_name} directory already empty: {directory}")
            return True

        print(f"\n📁 {dir_name} directory: {directory}")
        print(f"   Contains {len(contents)} items")

        # Show first few items
        for i, item in enumerate(contents[:5]):
            item_type = "dir" if item.is_dir() else "file"
            print(f"   - {item.name} ({item_type})")
        if len(contents) > 5:
            print(f"   ... and {len(contents) - 5} more items")

        if not confirm_action(f"Clear {dir_name} directory?", auto_yes):
            print(f"  Skipped {dir_name} cleanup")
            return False

        # Delete all contents
        deleted_count = 0
        for item in contents:
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"✗ Error deleting {item.name}: {e}")

        print(f"✓ Cleared {deleted_count} items from {dir_name}")
        return True

    except Exception as e:
        print(f"✗ Error accessing {dir_name} directory: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Clear database and import directories for fresh testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python freshstart.py                  # Interactive with confirmations
  python freshstart.py --yes            # Auto-confirm all (DANGER!)
  python freshstart.py --keep-archive   # Keep archive directory
  python freshstart.py --keep-backups   # Keep backup files
        """
    )
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip all confirmations (use with caution!)')
    parser.add_argument('--keep-archive', action='store_true',
                        help='Do not clear archive directory')
    parser.add_argument('--keep-backups', action='store_true',
                        help='Do not clear backup directory')
    parser.add_argument('--keep-staging', action='store_true',
                        help='Do not clear staging/ingest directory')

    args = parser.parse_args()

    print("=" * 60)
    print("FRESHSTART - Clean Slate for Import Testing")
    print("=" * 60)

    # Load configuration
    config = load_config()

    # Extract paths
    db_path = config.get('db_loc')
    staging_path = config.get('db_ingest')
    archive_path = config.get('arch_loc')
    backup_path = config.get('db_backup')

    # Validate required paths
    if not db_path:
        print("ERROR: db_loc not configured in user/user.json")
        sys.exit(1)

    print("\nConfiguration loaded from user/user.json:")
    print(f"  Database:  {db_path}")
    print(f"  Staging:   {staging_path or 'Not configured'}")
    print(f"  Archive:   {archive_path or 'Not configured'}")
    print(f"  Backups:   {backup_path or 'Not configured'}")

    if not args.yes:
        print("\n⚠️  WARNING: This will delete data!")
        print("   Make sure you have backups if needed.")
        if not confirm_action("\nProceed with cleanup?", False):
            print("\nCancelled by user")
            sys.exit(0)

    print("\n" + "=" * 60)
    print("Starting cleanup...")
    print("=" * 60)

    # Clear database
    clear_database(db_path, args.yes)

    # Clear staging/ingest directory
    if staging_path and not args.keep_staging:
        clear_directory(staging_path, "Staging/Ingest", args.yes)
    elif args.keep_staging:
        print("\n⏭️  Skipped staging directory (--keep-staging)")

    # Clear archive directory
    if archive_path and not args.keep_archive:
        clear_directory(archive_path, "Archive", args.yes)
    elif args.keep_archive:
        print("\n⏭️  Skipped archive directory (--keep-archive)")

    # Clear backup directory
    if backup_path and not args.keep_backups:
        clear_directory(backup_path, "Backups", args.yes)
    elif args.keep_backups:
        print("\n⏭️  Skipped backup directory (--keep-backups)")

    print("\n" + "=" * 60)
    print("✓ FRESHSTART COMPLETE")
    print("=" * 60)
    print("\nYou can now run a fresh import test:")
    print("  1. python scripts/db_migrate.py")
    print("  2. python scripts/db_import.py")
    print("  3. Continue with your import pipeline...")
    print()


if __name__ == "__main__":
    main()
