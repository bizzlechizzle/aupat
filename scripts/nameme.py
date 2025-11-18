#!/usr/bin/env python3
"""
Generate standardized filenames for AUPAT archive files.

Naming Convention (12-char hashes/UUIDs):
    Location folder: locshort-locuuid12
    Sub-location folder: subshort12-locuuid12

    Images: locuuid12-imgsha12.ext (or locuuid12-subuuid12-imgsha12.ext with sub)
    Videos: locuuid12-vidsha12.ext (or locuuid12-subuuid12-vidsha12.ext with sub)
    Documents: locuuid12-docsha12.ext (or locuuid12-subuuid12-docsha12.ext with sub)
    Maps: locuuid12-mapsha12.ext (or locuuid12-subuuid12-mapsha12.ext with sub)
    URLs: locuuid12-urluuid12 (or locuuid12-subuuid12-urluuid12 with sub)

Usage:
    from scripts.nameme import generate_filename
    name = generate_filename('image', 'abc123def456', 'file789abc012', 'jpg')

LILBITS: One function - generate standardized filenames
"""

from pathlib import Path
from typing import Optional


def generate_filename(
    file_type: str,
    loc_id: str,
    file_id: str,
    extension: Optional[str] = None,
    sub_id: Optional[str] = None
) -> str:
    """
    Generate standardized filename per AUPAT spec.

    Args:
        file_type: Type of file ('image', 'video', 'document', 'map', 'url')
        loc_id: Location UUID (12 chars)
        file_id: File hash/UUID (12 chars) - SHA for files, UUID for URLs
        extension: File extension (optional, no dot)
        sub_id: Sub-location UUID (12 chars, optional)

    Returns:
        Standardized filename

    Examples:
        >>> generate_filename('image', 'abc123def456', 'file789abc01', 'jpg')
        'abc123def456-file789abc01.jpg'

        >>> generate_filename('image', 'abc123def456', 'file789abc01', 'jpg', 'sub456xyz789')
        'abc123def456-sub456xyz789-file789abc01.jpg'

        >>> generate_filename('url', 'abc123def456', 'url890xyz123')
        'abc123def456-url890xyz123'

    Raises:
        ValueError: If IDs are wrong length or file_type invalid
    """
    # Validate file type
    valid_types = {'image', 'video', 'document', 'map', 'url'}
    if file_type not in valid_types:
        raise ValueError(f"Invalid file_type: {file_type}. Must be one of: {valid_types}")

    # Validate ID lengths (should be 12 chars)
    if len(loc_id) != 12:
        raise ValueError(f"Location ID must be 12 characters, got {len(loc_id)}: {loc_id}")

    if len(file_id) != 12:
        raise ValueError(f"File ID must be 12 characters, got {len(file_id)}: {file_id}")

    if sub_id and len(sub_id) != 12:
        raise ValueError(f"Sub-location ID must be 12 characters, got {len(sub_id)}: {sub_id}")

    # Build filename
    if sub_id:
        # With sub-location: locuuid12-subuuid12-filesha12
        base_name = f"{loc_id}-{sub_id}-{file_id}"
    else:
        # Without sub-location: locuuid12-filesha12
        base_name = f"{loc_id}-{file_id}"

    # Add extension if provided
    if extension:
        # Remove leading dot if present
        ext = extension.lstrip('.')
        return f"{base_name}.{ext}"
    else:
        return base_name


def generate_folder_name(loc_short: str, loc_id: str) -> str:
    """
    Generate location folder name per AUPAT spec.

    Format: locshort-locuuid12

    Args:
        loc_short: Location short name (max 12 chars, will be truncated)
        loc_id: Location UUID (12 chars)

    Returns:
        Location folder name

    Examples:
        >>> generate_folder_name('OldMill', 'abc123def456')
        'oldmill-abc123def456'

        >>> generate_folder_name('VeryLongLocationName', 'abc123def456')
        'verylonglo cat-abc123def456'

    Raises:
        ValueError: If loc_id is wrong length
    """
    if len(loc_id) != 12:
        raise ValueError(f"Location ID must be 12 characters, got {len(loc_id)}: {loc_id}")

    # Truncate short name to 12 chars and lowercase
    short = loc_short[:12].lower().replace(' ', '')

    return f"{short}-{loc_id}"


def generate_subfolder_name(sub_short: str, loc_id: str) -> str:
    """
    Generate sub-location folder name per AUPAT spec.

    Format: subshort12-locuuid12

    Args:
        sub_short: Sub-location short name (max 12 chars, will be truncated)
        loc_id: Location UUID (12 chars)

    Returns:
        Sub-location folder name

    Examples:
        >>> generate_subfolder_name('Basement', 'abc123def456')
        'basement-abc123def456'

    Raises:
        ValueError: If loc_id is wrong length
    """
    if len(loc_id) != 12:
        raise ValueError(f"Location ID must be 12 characters, got {len(loc_id)}: {loc_id}")

    # Truncate short name to 12 chars and lowercase
    short = sub_short[:12].lower().replace(' ', '')

    return f"{short}-{loc_id}"


def parse_filename(filename: str) -> dict:
    """
    Parse AUPAT standardized filename to extract components.

    Args:
        filename: Standardized filename

    Returns:
        Dict with keys: loc_id, file_id, sub_id (optional), extension (optional)

    Examples:
        >>> parse_filename('abc123def456-file789abc01.jpg')
        {'loc_id': 'abc123def456', 'file_id': 'file789abc01', 'extension': 'jpg'}

        >>> parse_filename('abc123def456-sub456xyz789-file789abc01.jpg')
        {'loc_id': 'abc123def456', 'sub_id': 'sub456xyz789', 'file_id': 'file789abc01', 'extension': 'jpg'}
    """
    # Remove extension
    name_parts = filename.split('.')
    base_name = name_parts[0]
    extension = name_parts[1] if len(name_parts) > 1 else None

    # Split by dash
    parts = base_name.split('-')

    result = {}

    if len(parts) == 2:
        # No sub-location: locuuid12-filesha12
        result['loc_id'] = parts[0]
        result['file_id'] = parts[1]
    elif len(parts) == 3:
        # With sub-location: locuuid12-subuuid12-filesha12
        result['loc_id'] = parts[0]
        result['sub_id'] = parts[1]
        result['file_id'] = parts[2]
    else:
        raise ValueError(f"Invalid filename format: {filename}")

    if extension:
        result['extension'] = extension

    return result


def main():
    """CLI interface for testing."""
    import sys

    if len(sys.argv) < 4:
        print("Usage: nameme.py <file_type> <loc_id> <file_id> [extension] [sub_id]")
        print("Example: nameme.py image abc123def456 file789abc01 jpg")
        print("Example: nameme.py image abc123def456 file789abc01 jpg sub456xyz789")
        sys.exit(1)

    file_type = sys.argv[1]
    loc_id = sys.argv[2]
    file_id = sys.argv[3]
    extension = sys.argv[4] if len(sys.argv) > 4 else None
    sub_id = sys.argv[5] if len(sys.argv) > 5 else None

    try:
        filename = generate_filename(file_type, loc_id, file_id, extension, sub_id)
        print(f"Generated filename: {filename}")

        # Parse it back
        parsed = parse_filename(filename)
        print(f"Parsed: {parsed}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
