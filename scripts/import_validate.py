#!/usr/bin/env python3
"""
File validation for AUPAT import workflow.

Validates:
- File types against approved extension lists
- File existence and readability
- Duplicate detection via SHA hash lookup

Usage:
    from scripts.import_validate import validate_file, check_duplicate

LILBITS: One function - file validation
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

from scripts.gensha import generate_file_hash


# Approved file extensions per v0.1.0 spec
APPROVED_EXTENSIONS = {
    'image': {
        '3fr', 'ai', 'arw', 'avif', 'bay', 'bmp', 'cin', 'cr2', 'cr3', 'crw',
        'cur', 'dcr', 'dds', 'dng', 'dpx', 'eip', 'eps', 'erf', 'exr', 'fff',
        'g3', 'gif', 'hdr', 'heic', 'heif', 'ico', 'iiq', 'j2k', 'jls', 'jng',
        'jp2', 'jpf', 'jpe', 'jpeg', 'jpg', 'jpa', 'jpm', 'jpx', 'jxl', 'kdc',
        'mef', 'mfw', 'mos', 'mrw', 'nef', 'nrw', 'orf', 'pbm', 'pcx', 'pct',
        'pdn', 'pef', 'pgm', 'png', 'ppm', 'ps', 'psb', 'psd', 'ptx', 'pxi',
        'qtk', 'raf', 'raw', 'rw2', 'rwl', 'sr2', 'srf', 'svg', 'tga', 'thm',
        'tif', 'tiff', 'vff', 'webp', 'x3f', 'xbm', 'xcf', 'xmp', 'xpm'
    },
    'video': {
        '3gp', '3g2', 'amv', 'asf', 'avi', 'av1', 'bik', 'dat', 'dng', 'dv',
        'f4v', 'flv', 'gif', 'gxf', 'h261', 'h263', 'h264', 'h265', 'hevc',
        'm2t', 'm2ts', 'm2v', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg',
        'mpls', 'mts', 'mxf', 'oga', 'ogg', 'ogm', 'ogv', 'opus', 'qt', 'rm',
        'rmvb', 'swf', 'ts', 'vob', 'vp8', 'vp9', 'webm', 'wmv', 'y4m'
    },
    'map': {
        'kml', 'kmz', 'gpx', 'geojson', 'json', 'topojson', 'shp', 'shx',
        'dbf', 'prj', 'qgz', 'qgs', 'mbtiles', 'pbf', 'osm', 'o5m', 'obf',
        'sid', 'vrt', 'tiff', 'tif', 'geotiff', 'asc', 'grd', 'bil', 'dem',
        'dt0', 'dt1', 'dt2', 'rst', 'xyz', 'gpkg', 'sqlite', 'csv', 'tab',
        'mif', 'mid', 'e00', 'nc', 'netcdf', 'img', 'hgt', 'bz2', 'gz',
        'jp2', 'jpx', 'tifc', 'raster', 'lidar', 'las', 'laz', 'rpf', 'ccf',
        'bsb', 'kap'
    }
}


def get_file_category(file_path: Path) -> Optional[str]:
    """
    Determine file category based on extension.

    Args:
        file_path: Path to file

    Returns:
        'image', 'video', 'map', 'document', or None if invalid

    Example:
        >>> get_file_category(Path('photo.jpg'))
        'image'
        >>> get_file_category(Path('map.kml'))
        'map'
    """
    ext = file_path.suffix.lstrip('.').lower()

    for category, extensions in APPROVED_EXTENSIONS.items():
        if ext in extensions:
            return category

    # If extension not in approved lists, treat as document
    # (per spec: Documents accept "any file type")
    return 'document'


def validate_file(file_path: str | Path) -> Tuple[bool, str, Optional[str]]:
    """
    Validate file for import.

    Checks:
    - File exists and is readable
    - Extension is valid for category

    Args:
        file_path: Path to file

    Returns:
        Tuple of (is_valid, category, error_message)
        - is_valid: True if file is valid
        - category: 'image', 'video', 'map', 'document'
        - error_message: None if valid, error string if invalid

    Example:
        >>> valid, category, error = validate_file('photo.jpg')
        >>> print(valid, category)
        True image
    """
    file_path = Path(file_path)

    # Check file exists
    if not file_path.exists():
        return (False, None, f"File not found: {file_path}")

    # Check is file (not directory)
    if not file_path.is_file():
        return (False, None, f"Not a file: {file_path}")

    # Check readable
    try:
        with open(file_path, 'rb') as f:
            f.read(1)
    except PermissionError:
        return (False, None, f"Cannot read file: {file_path}")
    except Exception as e:
        return (False, None, f"Error reading file: {e}")

    # Determine category
    category = get_file_category(file_path)

    return (True, category, None)


def check_duplicate(file_path: str | Path, db_path: str | Path) -> Optional[dict]:
    """
    Check if file already exists in database (via SHA hash).

    Args:
        file_path: Path to file
        db_path: Path to database

    Returns:
        Dict with existing record info if duplicate found, None otherwise
        Keys: file_uuid, file_name, loc_uuid, category

    Example:
        >>> duplicate = check_duplicate('photo.jpg', 'data/aupat.db')
        >>> if duplicate:
        ...     print(f"Duplicate found: {duplicate['file_name']}")
    """
    # Generate hash for file
    try:
        file_hash = generate_file_hash(file_path, 12)
    except Exception as e:
        raise ValueError(f"Cannot hash file: {e}")

    # Determine category to know which table to check
    category = get_file_category(Path(file_path))

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()

        # Check appropriate table based on category
        if category == 'image':
            cursor.execute("""
                SELECT img_uuid as file_uuid, img_name as file_name, loc_uuid
                FROM images WHERE img_sha = ?
            """, (file_hash,))
        elif category == 'video':
            cursor.execute("""
                SELECT vid_uuid as file_uuid, vid_name as file_name, loc_uuid
                FROM videos WHERE vid_sha = ?
            """, (file_hash,))
        elif category == 'map':
            cursor.execute("""
                SELECT map_uuid as file_uuid, map_name as file_name, loc_uuid
                FROM maps WHERE map_sha = ?
            """, (file_hash,))
        elif category == 'document':
            cursor.execute("""
                SELECT doc_uuid as file_uuid, doc_name as file_name, loc_uuid
                FROM documents WHERE doc_sha = ?
            """, (file_hash,))
        else:
            return None

        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['category'] = category
            return result

        return None

    finally:
        conn.close()


def main():
    """CLI interface for testing."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: import_validate.py <command> <file_path> [db_path]")
        print("\nCommands:")
        print("  validate <file_path>         - Validate file")
        print("  duplicate <file_path> <db>   - Check for duplicate")
        print("  category <file_path>         - Get file category")
        sys.exit(1)

    cmd = sys.argv[1]
    file_path = sys.argv[2]

    try:
        if cmd == 'validate':
            valid, category, error = validate_file(file_path)
            if valid:
                print(f"Valid {category} file: {file_path}")
            else:
                print(f"Invalid: {error}")
                sys.exit(1)

        elif cmd == 'duplicate':
            if len(sys.argv) < 4:
                print("Error: database path required for duplicate check")
                sys.exit(1)
            db_path = sys.argv[3]
            duplicate = check_duplicate(file_path, db_path)
            if duplicate:
                print(f"Duplicate found!")
                print(f"  UUID: {duplicate['file_uuid']}")
                print(f"  Name: {duplicate['file_name']}")
                print(f"  Location: {duplicate['loc_uuid']}")
            else:
                print("No duplicate found")

        elif cmd == 'category':
            category = get_file_category(Path(file_path))
            print(f"Category: {category}")

        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
