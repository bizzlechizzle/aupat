#!/usr/bin/env python3
"""
AUPAT Fresh Start Script
Cleans database and temporary files for development reset.

LILBITS: One script = one function (development cleanup)

WARNING: This is destructive! Use only in development.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Colors for output (NME compliant)
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color


def log_info(msg):
    print(f"{YELLOW}[INFO]{NC} {msg}")


def log_success(msg):
    print(f"{GREEN}[OK]{NC} {msg}")


def log_error(msg):
    print(f"{RED}[ERROR]{NC} {msg}")


def load_config():
    """Load user.json configuration."""
    script_dir = Path(__file__).parent
    user_json = script_dir / 'user' / 'user.json'

    if not user_json.exists():
        log_error("user.json not found. Run bootstrap first.")
        sys.exit(1)

    with open(user_json, 'r') as f:
        return json.load(f)


def get_size(path):
    """Get size of file or directory in MB."""
    if not os.path.exists(path):
        return 0

    if os.path.isfile(path):
        return os.path.getsize(path) / (1024 * 1024)

    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)


def backup_database(config):
    """Create backup before deleting."""
    db_path = Path(config['db_loc']) / config['db_name']

    if not db_path.exists():
        log_info("No database to backup")
        return None

    # Create backup directory
    backup_dir = Path(config.get('backup_loc', 'backups'))
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'pre_freshstart_{timestamp}.db'

    log_info(f"Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    log_success(f"Backup created ({get_size(backup_path):.2f} MB)")

    return backup_path


def main():
    print("")
    print("=" * 50)
    print("  AUPAT Fresh Start - Development Reset")
    print("=" * 50)
    print("")

    # Load config
    try:
        config = load_config()
    except Exception as e:
        log_error(f"Failed to load config: {e}")
        sys.exit(1)

    # Paths to clean
    db_path = Path(config['db_loc']) / config['db_name']
    staging_path = Path(config.get('staging_loc', 'staging'))
    ingest_path = Path(config.get('ingest_loc', 'ingest'))

    # Desktop cache (Electron)
    desktop_cache = Path(__file__).parent / 'desktop' / 'dist-electron'

    # Show what will be deleted
    print("The following will be DELETED:")
    print("")

    items_to_delete = []
    total_size = 0

    if db_path.exists():
        size = get_size(db_path)
        items_to_delete.append(('Database', db_path, size))
        total_size += size
        print(f"  - Database: {db_path} ({size:.2f} MB)")

    if staging_path.exists():
        size = get_size(staging_path)
        items_to_delete.append(('Staging', staging_path, size))
        total_size += size
        print(f"  - Staging: {staging_path} ({size:.2f} MB)")

    if ingest_path.exists():
        size = get_size(ingest_path)
        items_to_delete.append(('Ingest', ingest_path, size))
        total_size += size
        print(f"  - Ingest: {ingest_path} ({size:.2f} MB)")

    if desktop_cache.exists():
        size = get_size(desktop_cache)
        items_to_delete.append(('Desktop cache', desktop_cache, size))
        total_size += size
        print(f"  - Desktop cache: {desktop_cache} ({size:.2f} MB)")

    print("")
    print(f"Total: {total_size:.2f} MB")
    print("")

    if not items_to_delete:
        log_success("Nothing to clean - already fresh!")
        sys.exit(0)

    # Safety note
    print(f"{RED}WARNING:{NC} Archive folder will NOT be touched (your media is safe)")
    print("")

    # Confirmation
    response = input("Continue? [y/N]: ").strip().lower()

    if response != 'y':
        log_info("Cancelled")
        sys.exit(0)

    print("")

    # Optional backup
    if db_path.exists():
        backup_response = input("Create backup of database first? [Y/n]: ").strip().lower()
        if backup_response != 'n':
            try:
                backup_database(config)
                print("")
            except Exception as e:
                log_error(f"Backup failed: {e}")
                sys.exit(1)

    # Delete items
    log_info("Starting cleanup...")
    print("")

    for name, path, size in items_to_delete:
        try:
            if path.is_file():
                path.unlink()
                log_success(f"Deleted {name}: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                log_success(f"Deleted {name}: {path}")
        except Exception as e:
            log_error(f"Failed to delete {name}: {e}")

    print("")
    log_success("Fresh start complete!")
    print("")
    print("Next steps:")
    print("  1. Run: ./bootstrap_v010.sh")
    print("  2. Or run: python3 scripts/db_migrate_v010.py")
    print("  3. Then: ./start_aupat.sh")
    print("")


if __name__ == '__main__':
    main()
