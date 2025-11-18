#!/usr/bin/env python3
"""
AUPAT Helper: Create Folder Structure

LILBITS: One Script = One Primary Function
Purpose: Create organized folder structure for locations

Folder Structure (from v0.1.0 spec):
    Archive/
    └── State-Type/              # Example: ny-hospital
        └── locshort-locsha12/   # Example: buffpsych-a3f5d8e2b1c4
            ├── doc-org-locsha12/
            ├── img-org-locsha12/
            └── vid-org-locsha12/

Why this structure?
- State-Type: Easy to browse by location type per state
- locshort: Human-readable location identifier
- locsha12: Unique ID (prevents conflicts with similar names)
- Separate folders for docs/images/videos (organized)

Version: 1.0.0
Date: 2025-11-18
"""

import sys
from pathlib import Path
from typing import List, Optional


def create_location_folders(
    archive_root: Path,
    state: str,
    location_type: str,
    location_short: str,
    location_uuid12: str,
    create_subfolders: bool = True
) -> List[Path]:
    """
    Create folder structure for a location.

    Args:
        archive_root: Root archive directory (e.g., /data/archive)
        state: State code (e.g., 'ny')
        location_type: Location type (e.g., 'hospital')
        location_short: Short name (e.g., 'buffpsych')
        location_uuid12: 12-char UUID (e.g., 'a3f5d8e2b1c4')
        create_subfolders: Create doc/img/vid subfolders (default: True)

    Returns:
        List[Path]: All created directory paths

    Raises:
        ValueError: If invalid inputs
        PermissionError: If can't create directories

    Example:
        >>> create_location_folders(
        ...     Path("/data/archive"),
        ...     "ny",
        ...     "hospital",
        ...     "buffpsych",
        ...     "a3f5d8e2b1c4"
        ... )
        [
            Path("/data/archive/ny-hospital/buffpsych-a3f5d8e2b1c4"),
            Path("/data/archive/ny-hospital/buffpsych-a3f5d8e2b1c4/doc-org-a3f5d8e2b1c4"),
            Path("/data/archive/ny-hospital/buffpsych-a3f5d8e2b1c4/img-org-a3f5d8e2b1c4"),
            Path("/data/archive/ny-hospital/buffpsych-a3f5d8e2b1c4/vid-org-a3f5d8e2b1c4")
        ]

    Technical Details:
        - Uses Path.mkdir(parents=True) for atomic creation
        - parents=True creates intermediate directories if needed
        - exist_ok=True doesn't fail if directory already exists
        - All paths are returned for verification
    """
    # Validate inputs
    if not archive_root:
        raise ValueError("Archive root cannot be empty")
    if not state:
        raise ValueError("State cannot be empty")
    if not location_type:
        raise ValueError("Location type cannot be empty")
    if not location_short:
        raise ValueError("Location short name cannot be empty")
    if not location_uuid12:
        raise ValueError("Location UUID cannot be empty")

    if len(location_uuid12) != 12:
        raise ValueError(f"UUID must be 12 characters, got: {location_uuid12}")

    # Convert to Path if string
    if not isinstance(archive_root, Path):
        archive_root = Path(archive_root)

    created_paths = []

    try:
        # Step 1: Create State-Type directory
        # Example: /data/archive/ny-hospital
        state_type_dir = archive_root / f"{state}-{location_type}"
        state_type_dir.mkdir(parents=True, exist_ok=True)
        created_paths.append(state_type_dir)

        # Step 2: Create location directory
        # Example: /data/archive/ny-hospital/buffpsych-a3f5d8e2b1c4
        location_dir = state_type_dir / f"{location_short}-{location_uuid12}"
        location_dir.mkdir(parents=True, exist_ok=True)
        created_paths.append(location_dir)

        # Step 3: Create subfolders (if requested)
        if create_subfolders:
            # Document folder
            # Example: buffpsych-a3f5d8e2b1c4/doc-org-a3f5d8e2b1c4
            doc_dir = location_dir / f"doc-org-{location_uuid12}"
            doc_dir.mkdir(exist_ok=True)
            created_paths.append(doc_dir)

            # Image folder
            # Example: buffpsych-a3f5d8e2b1c4/img-org-a3f5d8e2b1c4
            img_dir = location_dir / f"img-org-{location_uuid12}"
            img_dir.mkdir(exist_ok=True)
            created_paths.append(img_dir)

            # Video folder
            # Example: buffpsych-a3f5d8e2b1c4/vid-org-a3f5d8e2b1c4
            vid_dir = location_dir / f"vid-org-{location_uuid12}"
            vid_dir.mkdir(exist_ok=True)
            created_paths.append(vid_dir)

        return created_paths

    except PermissionError as e:
        raise PermissionError(
            f"Cannot create directories in {archive_root}. "
            f"Check permissions."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error creating folders: {e}") from e


def verify_folder_structure(location_dir: Path) -> bool:
    """
    Verify that folder structure is correct.

    Checks:
    1. Location directory exists
    2. doc-org-{uuid12} subfolder exists
    3. img-org-{uuid12} subfolder exists
    4. vid-org-{uuid12} subfolder exists

    Args:
        location_dir: Path to location directory

    Returns:
        bool: True if structure is valid, False otherwise

    Example:
        >>> loc_dir = Path("/data/archive/ny-hospital/buffpsych-a3f5d8e2b1c4")
        >>> verify_folder_structure(loc_dir)
        True
    """
    if not location_dir.exists():
        return False

    if not location_dir.is_dir():
        return False

    # Extract UUID12 from directory name
    # Example: "buffpsych-a3f5d8e2b1c4" -> "a3f5d8e2b1c4"
    dir_name = location_dir.name
    parts = dir_name.split('-')
    if len(parts) < 2:
        return False

    # Last part should be UUID12
    uuid12 = parts[-1]
    if len(uuid12) != 12:
        return False

    # Check for required subfolders
    required_folders = [
        location_dir / f"doc-org-{uuid12}",
        location_dir / f"img-org-{uuid12}",
        location_dir / f"vid-org-{uuid12}"
    ]

    for folder in required_folders:
        if not folder.exists() or not folder.is_dir():
            return False

    return True


def _cli():
    """
    Command-line interface for folderme.py

    Usage:
        python folderme.py <archive_root> <state> <type> <short_name> <uuid12>

    Example:
        python folderme.py /data/archive ny hospital buffpsych a3f5d8e2b1c4
    """
    if len(sys.argv) < 6:
        print("Usage: python folderme.py <archive_root> <state> <type> <short_name> <uuid12>")
        print("Example: python folderme.py /data/archive ny hospital buffpsych a3f5d8e2b1c4")
        sys.exit(1)

    archive_root = Path(sys.argv[1])
    state = sys.argv[2]
    location_type = sys.argv[3]
    location_short = sys.argv[4]
    location_uuid12 = sys.argv[5]

    try:
        created_paths = create_location_folders(
            archive_root, state, location_type, location_short, location_uuid12
        )

        print(f"Created {len(created_paths)} directories:")
        for path in created_paths:
            print(f"  {path}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    _cli()
