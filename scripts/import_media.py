#!/usr/bin/env python3
"""
Main import workflow for AUPAT media files.

Import Process (v0.1.0 spec):
1. Scan files and record original name/location
2. Assign unique keys (SHA256 for files, UUID4 for URLs)
3. Create folders
4. Import media to archive
5. Verify files
6. Delete source media (if configured)

Usage:
    from scripts.import_media import import_file

LILBITS: One function - import file workflow
"""

import json
import shutil
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, Dict

from scripts.gensha import generate_file_hash
from scripts.genuuid import generate_uuid
from scripts.nameme import generate_filename
from scripts.folderme import create_location_folders, get_media_folder
from scripts.import_validate import validate_file, check_duplicate, get_file_category
from scripts.normalize import normalize_datetime


def load_config() -> dict:
    """Load user configuration."""
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def import_file(
    file_path: str | Path,
    loc_uuid: str,
    loc_short: str,
    state: str,
    location_type: str,
    sub_uuid: Optional[str] = None,
    delete_source: bool = False
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Import file into AUPAT archive.

    Process:
    1. Validate file
    2. Check for duplicates
    3. Generate hash/UUID
    4. Create folder structure
    5. Copy file to archive with standardized name
    6. Insert database record
    7. Verify file integrity
    8. Delete source (if configured)

    Args:
        file_path: Source file path
        loc_uuid: Location UUID (12 chars)
        loc_short: Location short name
        state: State code
        location_type: Location type
        sub_uuid: Sub-location UUID (optional, 12 chars)
        delete_source: Delete source file after successful import

    Returns:
        Tuple of (success, file_uuid, error_message)

    Example:
        >>> success, file_uuid, error = import_file(
        ...     'photo.jpg',
        ...     'abc123def456',
        ...     'oldmill',
        ...     'ny',
        ...     'industrial'
        ... )
    """
    file_path = Path(file_path)
    config = load_config()
    archive_root = Path(config['archive_loc'])
    db_path = Path(config['db_loc']) / config['db_name']

    # STEP 1: Validate file
    valid, category, error = validate_file(file_path)
    if not valid:
        return (False, None, f"Validation failed: {error}")

    # STEP 2: Check for duplicates
    duplicate = check_duplicate(file_path, db_path)
    if duplicate:
        return (False, None, f"Duplicate file exists: {duplicate['file_name']} in location {duplicate['loc_uuid']}")

    # STEP 3: Generate hash/UUID and get file info
    original_name = file_path.name
    original_path = str(file_path.absolute())
    extension = file_path.suffix.lstrip('.').lower()

    file_hash = generate_file_hash(file_path, 12)
    file_uuid = generate_uuid(12)

    # STEP 4: Create folder structure
    folders = create_location_folders(
        archive_root, state, location_type, loc_short, loc_uuid
    )

    # Get target media folder
    media_type_map = {'image': 'img', 'video': 'vid', 'document': 'doc', 'map': 'map'}
    media_type = media_type_map.get(category, 'doc')
    target_folder = folders[media_type]

    # STEP 5: Generate standardized filename and copy file
    new_filename = generate_filename(category, loc_uuid, file_hash, extension, sub_uuid)
    target_path = target_folder / new_filename

    try:
        shutil.copy2(file_path, target_path)
    except Exception as e:
        return (False, None, f"Copy failed: {e}")

    # STEP 6: Insert database record
    timestamp = normalize_datetime(None)
    conn = sqlite3.connect(str(db_path))

    try:
        cursor = conn.cursor()

        table_map = {
            'image': ('images', 'img'),
            'video': ('videos', 'vid'),
            'document': ('documents', 'doc'),
            'map': ('maps', 'map')
        }

        table, prefix = table_map.get(category, ('documents', 'doc'))

        cursor.execute(f"""
            INSERT INTO {table} (
                {prefix}_uuid, loc_uuid, sub_uuid, {prefix}_sha,
                original_name, original_path, {prefix}_name, {prefix}_ext,
                {prefix}_path, created_at, verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_uuid, loc_uuid, sub_uuid, file_hash,
            original_name, original_path, new_filename, extension,
            str(target_path), timestamp, 0
        ))

        conn.commit()

    except Exception as e:
        # Rollback and cleanup
        conn.rollback()
        if target_path.exists():
            target_path.unlink()
        return (False, None, f"Database insert failed: {e}")

    finally:
        conn.close()

    # STEP 7: Verify file integrity
    try:
        verify_hash = generate_file_hash(target_path, 12)
        if verify_hash != file_hash:
            target_path.unlink()
            return (False, None, "Verification failed: hash mismatch")

        # Update verified flag
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {table} SET verified = 1 WHERE {prefix}_uuid = ?", (file_uuid,))
        conn.commit()
        conn.close()

    except Exception as e:
        return (False, None, f"Verification failed: {e}")

    # STEP 8: Delete source (if configured)
    if delete_source:
        try:
            file_path.unlink()
        except Exception as e:
            # Don't fail import if source deletion fails
            pass

    return (True, file_uuid, None)


def main():
    """CLI interface for testing."""
    import sys

    if len(sys.argv) < 6:
        print("Usage: import_media.py <file> <loc_uuid> <loc_short> <state> <type> [sub_uuid] [delete]")
        print("\nExample:")
        print("  import_media.py photo.jpg abc123def456 oldmill ny industrial")
        print("  import_media.py photo.jpg abc123def456 oldmill ny industrial sub456xyz789 true")
        sys.exit(1)

    file_path = sys.argv[1]
    loc_uuid = sys.argv[2]
    loc_short = sys.argv[3]
    state = sys.argv[4]
    location_type = sys.argv[5]
    sub_uuid = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] != 'true' else None
    delete_source = sys.argv[-1].lower() == 'true'

    try:
        success, file_uuid, error = import_file(
            file_path, loc_uuid, loc_short, state, location_type, sub_uuid, delete_source
        )

        if success:
            print(f"Import successful!")
            print(f"File UUID: {file_uuid}")
        else:
            print(f"Import failed: {error}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
