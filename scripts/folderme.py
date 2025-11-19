#!/usr/bin/env python3
"""
Create standardized folder structure for AUPAT archive.

Folder Structure (per spec):
    Archive/State-Type/locshort-locuuid12/
        img/
        vid/
        doc/
        map/

Usage:
    from scripts.folderme import create_location_folders
    paths = create_location_folders('/archive', 'ny', 'industrial', 'oldmill', 'abc123def456')

LILBITS: One function - create folder structure
"""

from pathlib import Path
from typing import Dict, Optional


def create_location_folders(
    archive_root: str | Path,
    state: str,
    location_type: str,
    loc_short: str,
    loc_id: str,
    create: bool = True
) -> Dict[str, Path]:
    """
    Create standardized folder structure for a location.

    Folder structure:
        archive_root/state-type/locshort-locuuid12/
            img/
            vid/
            doc/
            map/

    Args:
        archive_root: Root archive directory path
        state: State code (lowercase, e.g., 'ny')
        location_type: Location type (lowercase, e.g., 'industrial')
        loc_short: Location short name (e.g., 'OldMill')
        loc_id: Location UUID (12 chars)
        create: Whether to actually create directories (default: True)

    Returns:
        Dict with keys: 'root', 'img', 'vid', 'doc', 'map' pointing to Path objects

    Examples:
        >>> paths = create_location_folders('/archive', 'ny', 'industrial', 'oldmill', 'abc123def456')
        >>> print(paths['root'])
        /archive/ny-industrial/oldmill-abc123def456

        >>> print(paths['img'])
        /archive/ny-industrial/oldmill-abc123def456/img

    Raises:
        ValueError: If parameters are invalid
        PermissionError: If can't create directories
    """
    # Validate inputs
    if not archive_root:
        raise ValueError("archive_root cannot be empty")

    if not state or len(state) > 10:
        raise ValueError(f"Invalid state: {state}")

    if not location_type:
        raise ValueError("location_type cannot be empty")

    if not loc_short:
        raise ValueError("loc_short cannot be empty")

    if len(loc_id) != 12:
        raise ValueError(f"Location ID must be 12 characters, got {len(loc_id)}: {loc_id}")

    # Normalize to Path
    archive_root = Path(archive_root)

    # Build paths
    # Level 1: Archive root
    # Level 2: state-type (e.g., "ny-industrial")
    state_type_dir = f"{state.lower()}-{location_type.lower()}"

    # Level 3: locshort-locuuid12 (e.g., "oldmill-abc123def456")
    loc_short_clean = loc_short[:12].lower().replace(' ', '')
    location_dir = f"{loc_short_clean}-{loc_id}"

    # Full location path
    location_root = archive_root / state_type_dir / location_dir

    # Build paths dict
    paths = {
        'root': location_root,
        'img': location_root / 'img',
        'vid': location_root / 'vid',
        'doc': location_root / 'doc',
        'map': location_root / 'map',
    }

    # Create directories if requested
    if create:
        for folder_type, folder_path in paths.items():
            folder_path.mkdir(parents=True, exist_ok=True)

    return paths


def create_sublocation_folder(
    location_root: str | Path,
    sub_short: str,
    loc_id: str,
    create: bool = True
) -> Path:
    """
    Create sub-location folder within location directory.

    Folder structure:
        location_root/subshort12-locuuid12/

    Args:
        location_root: Location root directory path
        sub_short: Sub-location short name
        loc_id: Location UUID (12 chars)
        create: Whether to actually create directory (default: True)

    Returns:
        Path to sub-location folder

    Examples:
        >>> path = create_sublocation_folder('/archive/ny-industrial/oldmill-abc123def456', 'basement', 'abc123def456')
        >>> print(path)
        /archive/ny-industrial/oldmill-abc123def456/basement-abc123def456

    Raises:
        ValueError: If parameters are invalid
    """
    if not location_root:
        raise ValueError("location_root cannot be empty")

    if not sub_short:
        raise ValueError("sub_short cannot be empty")

    if len(loc_id) != 12:
        raise ValueError(f"Location ID must be 12 characters, got {len(loc_id)}: {loc_id}")

    # Normalize to Path
    location_root = Path(location_root)

    # Build sub-location folder name
    sub_short_clean = sub_short[:12].lower().replace(' ', '')
    subfolder_name = f"{sub_short_clean}-{loc_id}"

    # Full path
    subfolder_path = location_root / subfolder_name

    # Create if requested
    if create:
        subfolder_path.mkdir(parents=True, exist_ok=True)

    return subfolder_path


def get_media_folder(
    location_root: str | Path,
    media_type: str,
    sub_folder: Optional[str] = None
) -> Path:
    """
    Get path to media folder (img/vid/doc/map).

    Args:
        location_root: Location root directory path
        media_type: Type of media ('img', 'vid', 'doc', 'map')
        sub_folder: Optional sub-location folder name

    Returns:
        Path to media folder

    Examples:
        >>> get_media_folder('/archive/ny-industrial/oldmill-abc123def456', 'img')
        /archive/ny-industrial/oldmill-abc123def456/img

        >>> get_media_folder('/archive/ny-industrial/oldmill-abc123def456', 'img', 'basement-abc123def456')
        /archive/ny-industrial/oldmill-abc123def456/basement-abc123def456/img

    Raises:
        ValueError: If media_type invalid
    """
    valid_types = {'img', 'vid', 'doc', 'map'}
    if media_type not in valid_types:
        raise ValueError(f"Invalid media_type: {media_type}. Must be one of: {valid_types}")

    location_root = Path(location_root)

    if sub_folder:
        # Media in sub-location folder
        return location_root / sub_folder / media_type
    else:
        # Media in main location folder
        return location_root / media_type


def verify_folder_structure(location_root: str | Path) -> bool:
    """
    Verify that location folder has correct structure.

    Checks for:
        - img/ folder
        - vid/ folder
        - doc/ folder
        - map/ folder

    Args:
        location_root: Location root directory path

    Returns:
        True if structure is valid, False otherwise

    Example:
        >>> verify_folder_structure('/archive/ny-industrial/oldmill-abc123def456')
        True
    """
    location_root = Path(location_root)

    if not location_root.exists() or not location_root.is_dir():
        return False

    required_folders = ['img', 'vid', 'doc', 'map']

    for folder in required_folders:
        folder_path = location_root / folder
        if not folder_path.exists() or not folder_path.is_dir():
            return False

    return True


def main():
    """CLI interface for testing."""
    import sys

    if len(sys.argv) < 6:
        print("Usage: folderme.py <archive_root> <state> <type> <loc_short> <loc_id>")
        print("Example: folderme.py /archive ny industrial OldMill abc123def456")
        sys.exit(1)

    archive_root = sys.argv[1]
    state = sys.argv[2]
    location_type = sys.argv[3]
    loc_short = sys.argv[4]
    loc_id = sys.argv[5]

    try:
        paths = create_location_folders(archive_root, state, location_type, loc_short, loc_id, create=False)

        print("Folder structure (not created, dry run):")
        print(f"  Root: {paths['root']}")
        print(f"  Images: {paths['img']}")
        print(f"  Videos: {paths['vid']}")
        print(f"  Documents: {paths['doc']}")
        print(f"  Maps: {paths['map']}")

        print("\nTo create folders, use this in Python:")
        print(f"  create_location_folders('{archive_root}', '{state}', '{location_type}', '{loc_short}', '{loc_id}')")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
