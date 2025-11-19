#!/usr/bin/env python3
"""
AUPAT Utility Functions
Consolidated utility functions for UUID generation, SHA256 hashing, and filename generation.

This module consolidates functionality from:
- gen_uuid.py: UUID4 generation with collision detection
- gen_sha.py: SHA256 hash calculation
- name.py: Standardized filename generation

Version: 1.0.0
Last Updated: 2025-11-15
"""

import hashlib
import json
import logging
import sqlite3
import uuid
from pathlib import Path
from typing import Optional, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Get database connection using configuration from user.json.

    Returns:
        sqlite3.Connection: Database connection with row_factory set to sqlite3.Row

    Raises:
        FileNotFoundError: If user.json or database file not found
        json.JSONDecodeError: If user.json is invalid

    Example:
        >>> conn = get_db_connection()
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT * FROM locations")
        >>> conn.close()
    """
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    db_path = Path(config['db_loc']) / config['db_name']
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def generate_uuid(cursor: sqlite3.Cursor, table_name: str, uuid_field: str = 'loc_uuid') -> str:
    """
    Generate a unique UUID4 identifier with collision detection.

    Generates a UUID4 and verifies that the first 8 characters are unique
    in the specified table. If a collision is detected, generates a new UUID
    and retries until a unique value is found.

    Args:
        cursor: SQLite database cursor
        table_name: Name of the table to check for uniqueness ('locations', 'sub_locations', 'urls')
        uuid_field: Name of the UUID field in the table (default: 'loc_uuid')

    Returns:
        str: Full UUID4 as a string (uuid8 can be computed as uuid[:8])

    Raises:
        ValueError: If table_name or uuid_field is invalid

    Example:
        >>> cursor = conn.cursor()
        >>> loc_uuid = generate_uuid(cursor, 'locations', 'loc_uuid')
        >>> loc_uuid8 = loc_uuid[:8]  # Compute 8-char version

    Notes:
        - UUID collision probability for 8 hex chars: ~1 in 4.3 billion
        - Collisions are logged for monitoring
        - Returns only full UUID; uuid8 should be computed when needed
    """
    max_retries = 100  # Safety limit to prevent infinite loop
    retries = 0

    while retries < max_retries:
        # Generate new UUID4
        new_uuid = str(uuid.uuid4())
        uuid8 = new_uuid[:8]

        # Check if first 8 chars already exist in database
        query = f"SELECT {uuid_field} FROM {table_name} WHERE SUBSTR({uuid_field}, 1, 8) = ?"
        cursor.execute(query, (uuid8,))
        existing = cursor.fetchone()

        if not existing:
            # No collision - return the UUID
            if retries > 0:
                logger.info(f"UUID generated after {retries} collision(s): {uuid8}")
            return new_uuid

        # Collision detected - log and retry
        logger.warning(f"UUID8 collision detected: {uuid8} (attempt {retries + 1})")
        retries += 1

    # Should never reach here
    raise RuntimeError(f"Failed to generate unique UUID after {max_retries} attempts")


def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA256 hash of a file.

    Reads the file in chunks for memory efficiency, suitable for large files.
    Returns the full 64-character hexadecimal SHA256 hash.

    Args:
        file_path: Absolute path to the file

    Returns:
        str: SHA256 hash as 64-character hexadecimal string (sha8 can be computed as sha256[:8])

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
        IOError: If file read fails

    Example:
        >>> sha256 = calculate_sha256('/path/to/image.jpg')
        >>> sha8 = sha256[:8]  # Compute 8-char version
        >>> print(f"SHA256: {sha256}")
        >>> print(f"SHA8: {sha8}")

    Notes:
        - Reads file in 64KB chunks (memory efficient for large files)
        - Returns only full SHA256; sha8 should be computed when needed
        - Used for deduplication and integrity verification
    """
    # Validate file exists
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Calculate SHA256 hash
    sha256_hash = hashlib.sha256()
    chunk_size = 65536  # 64KB chunks

    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    except Exception as e:
        logger.error(f"Failed to calculate SHA256 for {file_path}: {e}")
        raise


def generate_filename(
    media_type: str,
    loc_uuid: str,
    sha256: str,
    extension: str,
    sub_uuid: Optional[str] = None
) -> str:
    """
    Generate standardized filename for media files.

    Creates filenames following the AUPAT naming convention:
    - Without sub-location: {loc_uuid8}-{sha8}.{ext}
    - With sub-location: {loc_uuid8}-{sub_uuid8}-{sha8}.{ext}

    All uuid8 and sha8 values are computed from the full values.

    Args:
        media_type: Type of media ('img', 'vid', or 'doc') - used for validation only
        loc_uuid: Full location UUID (uuid8 computed as loc_uuid[:8])
        sha256: Full SHA256 hash (sha8 computed as sha256[:8])
        extension: File extension without dot (e.g., 'jpg', 'mp4', 'pdf')
        sub_uuid: Optional full sub-location UUID (sub_uuid8 computed as sub_uuid[:8])

    Returns:
        str: Standardized filename

    Raises:
        ValueError: If media_type is invalid or parameters are missing

    Examples:
        >>> # Image without sub-location
        >>> filename = generate_filename('img', 'a1b2c3d4-...', 'e5f6g7h8...', 'jpg')
        >>> # Returns: 'a1b2c3d4-e5f6g7h8.jpg'

        >>> # Video with sub-location
        >>> filename = generate_filename('vid', 'a1b2c3d4-...', 'e5f6g7h8...', 'mp4', 'i9j0k1l2-...')
        >>> # Returns: 'a1b2c3d4-i9j0k1l2-e5f6g7h8.mp4'

    Notes:
        - media_type must be one of: 'img', 'vid', 'doc' (validated but not included in filename)
        - Extension should be lowercase (normalized)
        - uuid8 and sha8 are computed, not retrieved from database
        - Naming pattern defined in data/name.json
    """
    # Validate media_type
    valid_types = {'img', 'vid', 'doc'}
    if media_type not in valid_types:
        raise ValueError(f"Invalid media_type: {media_type}. Must be one of: {valid_types}")

    # Validate required parameters
    if not all([loc_uuid, sha256, extension]):
        raise ValueError("loc_uuid, sha256, and extension are required")

    # Compute 8-character versions
    loc_uuid8 = loc_uuid[:8]
    sha8 = sha256[:8]

    # Normalize extension (remove leading dot if present, convert to lowercase)
    ext = extension.lstrip('.').lower()

    # Generate filename based on whether sub-location exists
    if sub_uuid:
        sub_uuid8 = sub_uuid[:8]
        filename = f"{loc_uuid8}-{sub_uuid8}-{sha8}.{ext}"
    else:
        filename = f"{loc_uuid8}-{sha8}.{ext}"

    return filename


def generate_master_json_filename(loc_uuid: str) -> str:
    """
    Generate filename for master JSON export.

    Args:
        loc_uuid: Full location UUID

    Returns:
        str: Master JSON filename (e.g., 'a1b2c3d4_master.json')

    Example:
        >>> filename = generate_master_json_filename('a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6')
        >>> # Returns: 'a1b2c3d4_master.json'
    """
    loc_uuid8 = loc_uuid[:8]
    return f"{loc_uuid8}_master.json"


# Convenience function for getting both full hash and 8-char version
def calculate_sha256_with_short(file_path: str) -> Tuple[str, str]:
    """
    Calculate SHA256 hash and return both full and 8-char versions.

    This is a convenience function that returns both the full SHA256
    and the first 8 characters in a single call.

    Args:
        file_path: Absolute path to the file

    Returns:
        tuple: (sha256_full, sha8) - Full 64-char hash and first 8 chars

    Example:
        >>> sha256, sha8 = calculate_sha256_with_short('/path/to/file.jpg')
        >>> print(f"Full: {sha256}, Short: {sha8}")

    Note:
        This is a convenience function. In most cases, you should use
        calculate_sha256() and compute sha8 as needed with [:8]
    """
    sha256 = calculate_sha256(file_path)
    sha8 = sha256[:8]
    return sha256, sha8


# File type detection based on extension
IMAGE_EXTENSIONS: Set[str] = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.heic', '.heif', '.webp', '.raw', '.cr2', '.nef', '.dng',
    '.arw', '.orf', '.rw2', '.pef', '.srw', '.raf', '.3fr',
    '.fff', '.iiq', '.k25', '.kdc', '.mef', '.mos', '.mrw',
    '.nrw', '.ptx', '.pxn', '.r3d', '.rwl', '.sr2', '.srf', '.x3f'
}

VIDEO_EXTENSIONS: Set[str] = {
    '.mp4', '.mov', '.avi', '.mkv', '.m4v', '.mpg', '.mpeg',
    '.wmv', '.flv', '.webm', '.3gp', '.mts', '.m2ts', '.ts',
    '.vob', '.ogv', '.ogg', '.drc', '.gifv', '.mng', '.qt',
    '.yuv', '.rm', '.rmvb', '.asf', '.amv', '.m4p', '.m4v',
    '.mpv', '.mp2', '.mpe', '.mpv', '.m2v', '.svi', '.3g2',
    '.mxf', '.roq', '.nsv', '.f4v', '.f4p', '.f4a', '.f4b'
}

DOCUMENT_EXTENSIONS: Set[str] = {
    '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
    '.srt', '.xml', '.json', '.csv', '.xls', '.xlsx',
    '.ppt', '.pptx', '.odp', '.ods', '.pages', '.numbers',
    '.keynote', '.log', '.ini', '.cfg'
}


def determine_file_type(extension: str) -> str:
    """
    Determine file type (image/video/document) based on file extension.

    Args:
        extension: File extension with or without leading dot (e.g., '.jpg' or 'jpg')

    Returns:
        str: File type - 'image', 'video', 'document', or 'other'

    Examples:
        >>> determine_file_type('.jpg')
        'image'
        >>> determine_file_type('mp4')
        'video'
        >>> determine_file_type('.PDF')
        'document'
        >>> determine_file_type('.xyz')
        'other'

    Notes:
        - Case insensitive
        - Handles extensions with or without leading dot
        - Returns 'other' for unknown extensions
        - Based on approved_ext.json and common media formats
    """
    # Normalize: lowercase and ensure leading dot
    ext = extension.lower()
    if not ext.startswith('.'):
        ext = f'.{ext}'

    if ext in IMAGE_EXTENSIONS:
        return 'image'
    elif ext in VIDEO_EXTENSIONS:
        return 'video'
    elif ext in DOCUMENT_EXTENSIONS:
        return 'document'
    else:
        return 'other'


def check_sha256_collision(cursor: sqlite3.Cursor, sha256: str, file_type: str) -> bool:
    """
    Check if SHA256 hash already exists in the appropriate media table.

    Args:
        cursor: SQLite database cursor
        sha256: Full SHA256 hash to check
        file_type: Type of file ('image', 'video', or 'document')

    Returns:
        bool: True if collision detected (hash exists), False if unique

    Raises:
        ValueError: If file_type is invalid

    Examples:
        >>> cursor = conn.cursor()
        >>> collision = check_sha256_collision(cursor, sha256_hash, 'image')
        >>> if collision:
        >>>     print("Duplicate image detected!")

    Notes:
        - Checks the appropriate table based on file_type
        - Returns True if hash already exists (duplicate)
        - Returns False if hash is unique (safe to import)
    """
    # Map file type to table and hash field
    table_map = {
        'image': ('images', 'img_sha'),
        'video': ('videos', 'vid_sha'),
        'document': ('documents', 'doc_sha')
    }

    if file_type not in table_map:
        raise ValueError(f"Invalid file_type: {file_type}. Must be 'image', 'video', or 'document'")

    table, sha_field = table_map[file_type]

    try:
        cursor.execute(f"SELECT {sha_field} FROM {table} WHERE {sha_field} = ?", (sha256,))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking SHA256 collision in {table}: {e}")
        return False


def check_location_name_collision(cursor: sqlite3.Cursor, loc_name: str) -> Optional[str]:
    """
    Check if location name already exists in database.

    Args:
        cursor: SQLite database cursor
        loc_name: Location name to check

    Returns:
        Optional[str]: UUID of existing location if found, None if unique

    Examples:
        >>> cursor = conn.cursor()
        >>> existing_uuid = check_location_name_collision(cursor, "Old Factory")
        >>> if existing_uuid:
        >>>     print(f"Location already exists: {existing_uuid}")

    Notes:
        - Case-sensitive comparison
        - Returns UUID of first match if found
        - Returns None if location name is unique
        - Helps prevent duplicate locations
    """
    try:
        cursor.execute("SELECT loc_uuid FROM locations WHERE loc_name = ?", (loc_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error checking location name collision: {e}")
        return None


if __name__ == '__main__':
    # Example usage and testing
    print("AUPAT Utilities Module")
    print("=" * 50)

    # Example: SHA256 calculation
    print("\nExample: SHA256 Calculation")
    print("-" * 50)
    # sha256 = calculate_sha256('/path/to/file.jpg')
    # print(f"SHA256: {sha256}")
    # print(f"SHA8: {sha256[:8]}")

    # Example: Filename generation
    print("\nExample: Filename Generation")
    print("-" * 50)
    example_uuid = "a1b2c3d4-e5f6-4789-abcd-1234567890ab"
    example_sha = "e5f6g7h8" + "0" * 56  # Padded to 64 chars

    # Image without sub-location
    img_name = generate_filename('img', example_uuid, example_sha, 'jpg')
    print(f"Image (no sub): {img_name}")

    # Video with sub-location
    example_sub_uuid = "i9j0k1l2-m3n4-5678-efgh-9876543210zy"
    vid_name = generate_filename('vid', example_uuid, example_sha, 'mp4', example_sub_uuid)
    print(f"Video (with sub): {vid_name}")

    # Master JSON filename
    json_name = generate_master_json_filename(example_uuid)
    print(f"Master JSON: {json_name}")

    print("\n" + "=" * 50)
    print("Module ready for use in AUPAT scripts")
