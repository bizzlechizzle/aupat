#!/usr/bin/env python3
"""
Quick diagnostic script to check what's in the database after import.
This helps debug why images might not be showing up.
"""

import json
import sqlite3
import sys
from pathlib import Path

def load_config():
    """Load user config."""
    config_path = Path(__file__).parent / 'user' / 'user.json'
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        print("Please run setup.sh first")
        return None

    with open(config_path) as f:
        return json.load(f)

def check_database(db_path):
    """Check database contents."""
    if not Path(db_path).exists():
        print(f"ERROR: Database does not exist: {db_path}")
        return

    print(f"Database: {db_path}")
    print("=" * 70)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check locations
    cursor.execute("SELECT COUNT(*) FROM locations")
    loc_count = cursor.fetchone()[0]
    print(f"\nLocations: {loc_count}")

    if loc_count > 0:
        cursor.execute("""
            SELECT loc_uuid, loc_name, state, type, loc_add
            FROM locations
            ORDER BY loc_add DESC
            LIMIT 5
        """)
        print("\nMost recent locations:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[0][:8]})")
            print(f"    State: {row[2]}, Type: {row[3]}, Added: {row[4]}")

    # Check images
    cursor.execute("SELECT COUNT(*) FROM images")
    img_count = cursor.fetchone()[0]
    print(f"\nImages: {img_count}")

    if img_count > 0:
        cursor.execute("""
            SELECT i.img_sha256, i.img_name, i.img_loc, l.loc_name
            FROM images i
            LEFT JOIN locations l ON i.loc_uuid = l.loc_uuid
            ORDER BY i.img_add DESC
            LIMIT 5
        """)
        print("\nMost recent images:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[0][:8]})")
            print(f"    Location: {row[3]}")
            print(f"    Path: {row[2]}")

    # Check videos
    cursor.execute("SELECT COUNT(*) FROM videos")
    vid_count = cursor.fetchone()[0]
    print(f"\nVideos: {vid_count}")

    # Check documents
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    print(f"Documents: {doc_count}")

    # Check ingest folder
    print("\n" + "=" * 70)
    print("Checking staging/ingest directory...")

    conn.close()
    return loc_count, img_count, vid_count, doc_count

def check_ingest_folder(ingest_path):
    """Check what files are in the staging/ingest folder."""
    if not ingest_path:
        print("No ingest path configured")
        return

    ingest_dir = Path(ingest_path)
    if not ingest_dir.exists():
        print(f"Ingest directory does not exist: {ingest_path}")
        return

    print(f"\nIngest directory: {ingest_path}")

    # Find all location folders (UUID8 folders)
    loc_folders = [d for d in ingest_dir.iterdir() if d.is_dir()]

    if not loc_folders:
        print("  No location folders found (empty staging)")
        return

    print(f"  Found {len(loc_folders)} location folder(s)")

    for loc_folder in loc_folders:
        files = list(loc_folder.glob('*'))
        if files:
            print(f"\n  {loc_folder.name}/ ({len(files)} files)")
            for f in files[:5]:  # Show first 5
                print(f"    - {f.name}")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")

def check_archive_folder(archive_path):
    """Check what's in the archive folder."""
    if not archive_path:
        print("No archive path configured")
        return

    archive_dir = Path(archive_path)
    if not archive_dir.exists():
        print(f"Archive directory does not exist: {archive_path}")
        return

    print(f"\nArchive directory: {archive_path}")

    # Find all state-type folders
    state_folders = [d for d in archive_dir.iterdir() if d.is_dir()]

    if not state_folders:
        print("  No state folders found (empty archive)")
        return

    print(f"  Found {len(state_folders)} state-type folder(s)")

    total_locations = 0
    for state_folder in state_folders:
        loc_folders = [d for d in state_folder.iterdir() if d.is_dir()]
        total_locations += len(loc_folders)
        if loc_folders:
            print(f"\n  {state_folder.name}/")
            for loc in loc_folders[:3]:
                files = list(loc.rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                print(f"    - {loc.name}/ ({file_count} files)")
            if len(loc_folders) > 3:
                print(f"    ... and {len(loc_folders) - 3} more locations")

    print(f"\n  Total locations in archive: {total_locations}")

if __name__ == '__main__':
    print("AUPAT Import Status Diagnostic")
    print("=" * 70)

    config = load_config()
    if not config:
        sys.exit(1)

    # Check database
    counts = check_database(config.get('db_loc'))

    # Check ingest folder
    check_ingest_folder(config.get('db_ingest'))

    # Check archive folder
    check_archive_folder(config.get('arch_loc'))

    print("\n" + "=" * 70)
    print("DIAGNOSIS:")
    print("=" * 70)

    if counts:
        loc_count, img_count, vid_count, doc_count = counts

        if loc_count > 0 and (img_count > 0 or vid_count > 0 or doc_count > 0):
            print("✓ Import successful - files are in database and staging/ingest folder")
            print("\nNEXT STEPS:")
            print("  1. Run db_organize.py to extract metadata")
            print("  2. Run db_folder.py to create archive folder structure")
            print("  3. Run db_ingest.py to move files from staging to archive")
            print("  4. Run db_verify.py to verify and cleanup")
        elif loc_count > 0:
            print("⚠ Location created but NO FILES imported")
            print("\nPOSSIBLE CAUSES:")
            print("  - Files were not uploaded correctly")
            print("  - File extensions not recognized")
            print("  - Import script failed silently")
        else:
            print("✗ NO DATA in database")
            print("\nPOSSIBLE CAUSES:")
            print("  - Database migration not run")
            print("  - Import never completed")
            print("  - Wrong database file")
