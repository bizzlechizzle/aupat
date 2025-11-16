#!/usr/bin/env python3
"""
AUPAT Folder Creation Script
Creates organized folder structure for locations based on folder.json template.

This script:
1. Loads folder structure from folder.json
2. Creates state-type directory (e.g., "ny-industrial")
3. Creates location directory with UUID8
4. Creates all media subdirectories
5. Creates document subdirectories

Version: 1.0.0
Last Updated: 2025-11-15
"""

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from normalize import normalize_location_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_user_config(config_path: str = None) -> dict:
    """Load user configuration from user.json."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"user.json not found at {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)


def load_folder_template() -> dict:
    """Load folder structure template from folder.json."""
    template_path = Path(__file__).parent.parent / 'data' / 'folder.json'

    if not template_path.exists():
        raise FileNotFoundError(f"folder.json not found at {template_path}")

    with open(template_path, 'r') as f:
        return json.load(f)


def create_folder_structure(
    arch_loc: str,
    loc_name: str,
    loc_uuid: str,
    state: str,
    loc_type: str
) -> list:
    """
    Create folder structure for a location - only creates folders for existing media.

    Args:
        arch_loc: Archive root directory
        loc_name: Location name (normalized)
        loc_uuid: Location UUID (uuid8 computed from first 8 chars)
        state: State code (lowercase)
        loc_type: Location type (lowercase)

    Returns:
        list: Paths of all created directories
    """
    # Load folder template
    template = load_folder_template()

    # Compute uuid8
    loc_uuid8 = loc_uuid[:8]

    # Normalize location name for folder (replace spaces with hyphens, lowercase)
    folder_loc_name = loc_name.lower().replace(' ', '-')

    # Build paths
    state_type_dir = f"{state}-{loc_type}"
    location_dir = f"{folder_loc_name}_{loc_uuid8}"

    base_path = Path(arch_loc) / state_type_dir / location_dir

    logger.info(f"Creating folder structure at: {base_path}")

    created_paths = []

    # Create base location directory
    base_path.mkdir(parents=True, exist_ok=True)
    created_paths.append(str(base_path))
    logger.info(f"  Created: {base_path}")

    # Query database to check what media exists for this location
    config = load_user_config()
    conn = sqlite3.connect(config['db_loc'])
    cursor = conn.cursor()

    # Check which image hardware categories have files
    cursor.execute("""
        SELECT
            SUM(CASE WHEN camera = 1 THEN 1 ELSE 0 END) as camera_count,
            SUM(CASE WHEN phone = 1 THEN 1 ELSE 0 END) as phone_count,
            SUM(CASE WHEN drone = 1 THEN 1 ELSE 0 END) as drone_count,
            SUM(CASE WHEN go_pro = 1 THEN 1 ELSE 0 END) as gopro_count,
            SUM(CASE WHEN film = 1 THEN 1 ELSE 0 END) as film_count,
            SUM(CASE WHEN other = 1 THEN 1 ELSE 0 END) as other_count
        FROM images
        WHERE loc_uuid = ?
    """, (loc_uuid,))

    img_result = cursor.fetchone()
    # Handle None values from SUM() when no rows match
    img_counts = tuple(c if c is not None else 0 for c in img_result) if img_result else (0, 0, 0, 0, 0, 0)
    has_images = sum(img_counts) > 0

    # Check which video hardware categories have files
    cursor.execute("""
        SELECT
            SUM(CASE WHEN camera = 1 THEN 1 ELSE 0 END) as camera_count,
            SUM(CASE WHEN phone = 1 THEN 1 ELSE 0 END) as phone_count,
            SUM(CASE WHEN drone = 1 THEN 1 ELSE 0 END) as drone_count,
            SUM(CASE WHEN go_pro = 1 THEN 1 ELSE 0 END) as gopro_count,
            SUM(CASE WHEN dash_cam = 1 THEN 1 ELSE 0 END) as dashcam_count,
            SUM(CASE WHEN other = 1 THEN 1 ELSE 0 END) as other_count
        FROM videos
        WHERE loc_uuid = ?
    """, (loc_uuid,))

    vid_result = cursor.fetchone()
    # Handle None values from SUM() when no rows match
    vid_counts = tuple(c if c is not None else 0 for c in vid_result) if vid_result else (0, 0, 0, 0, 0, 0)
    has_videos = sum(vid_counts) > 0

    # Check if we have documents
    cursor.execute("SELECT COUNT(*) FROM documents WHERE loc_uuid = ?", (loc_uuid,))
    doc_count = cursor.fetchone()[0]
    has_documents = doc_count > 0

    conn.close()

    logger.info(f"  Media check: {sum(img_counts)} images, {sum(vid_counts)} videos, {doc_count} documents")

    # Only create photos/ folder and subdirectories if we have images
    if has_images:
        photos_folders = template['location_structure']['subdirectories']['photos']['folders']

        # Map folder names to database counts
        folder_map = {
            'original_camera': img_counts[0],
            'original_phone': img_counts[1],
            'original_drone': img_counts[2],
            'original_go-pro': img_counts[3],
            'original_film': img_counts[4],
            'original_other': img_counts[5]
        }

        # Only create hardware-specific folders we need
        for folder in photos_folders:
            if folder_map.get(folder, 0) > 0:
                path = base_path / 'photos' / folder
                path.mkdir(parents=True, exist_ok=True)
                created_paths.append(str(path))
                logger.info(f"    Created: photos/{folder} ({folder_map[folder]} files)")

    # Only create videos/ folder and subdirectories if we have videos
    if has_videos:
        videos_folders = template['location_structure']['subdirectories']['videos']['folders']

        # Map folder names to database counts
        folder_map = {
            'original_camera': vid_counts[0],
            'original_phone': vid_counts[1],
            'original_drone': vid_counts[2],
            'original_go-pro': vid_counts[3],
            'original_dash-cam': vid_counts[4],
            'original_other': vid_counts[5]
        }

        # Only create hardware-specific folders we need
        for folder in videos_folders:
            if folder_map.get(folder, 0) > 0:
                path = base_path / 'videos' / folder
                path.mkdir(parents=True, exist_ok=True)
                created_paths.append(str(path))
                logger.info(f"    Created: videos/{folder} ({folder_map[folder]} files)")

    # Only create documents/ folder and subdirectories if we have documents
    if has_documents:
        docs_folders = template['location_structure']['subdirectories']['documents']['folders']
        for folder in docs_folders:
            path = base_path / 'documents' / folder
            path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(path))
            logger.debug(f"    Created: documents/{folder}")

    logger.info(f"  Total directories created: {len(created_paths)}")

    return created_paths


def create_folders_for_location(loc_uuid: str, config: dict) -> list:
    """
    Create folder structure for a specific location from database.

    Args:
        loc_uuid: Location UUID to create folders for
        config: User configuration dict

    Returns:
        list: Paths of created directories
    """
    db_path = config['db_loc']
    arch_loc = config['arch_loc']

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get location details
        cursor.execute(
            """
            SELECT loc_uuid, loc_name, state, type
            FROM locations
            WHERE loc_uuid = ?
            """,
            (loc_uuid,)
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Location not found: {loc_uuid}")

        loc_uuid_db, loc_name, state, loc_type = row

        # Create folder structure
        created_paths = create_folder_structure(
            arch_loc, loc_name, loc_uuid_db, state, loc_type
        )

        return created_paths

    finally:
        conn.close()


def create_folders_for_all_locations(config: dict) -> dict:
    """
    Create folder structures for all locations in database.

    Args:
        config: User configuration dict

    Returns:
        dict: Mapping of loc_uuid to list of created paths
    """
    db_path = config['db_loc']
    arch_loc = config['arch_loc']

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    results = {}

    try:
        # Get all locations
        cursor.execute("SELECT loc_uuid, loc_name, state, type FROM locations")
        locations = cursor.fetchall()

        logger.info(f"Found {len(locations)} locations to process")

        for loc_uuid, loc_name, state, loc_type in locations:
            logger.info(f"Processing location: {loc_name} ({loc_uuid[:8]})")

            try:
                created_paths = create_folder_structure(
                    arch_loc, loc_name, loc_uuid, state, loc_type
                )
                results[loc_uuid] = created_paths

            except Exception as e:
                logger.error(f"Failed to create folders for {loc_name}: {e}")
                results[loc_uuid] = None

        return results

    finally:
        conn.close()


def main():
    """Main folder creation workflow."""
    parser = argparse.ArgumentParser(
        description='Create organized folder structure for AUPAT locations'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file'
    )
    parser.add_argument(
        '--location',
        type=str,
        help='Create folders for specific location UUID (default: all locations)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_user_config(args.config)

        logger.info("=" * 60)
        logger.info("AUPAT Folder Creation")
        logger.info("=" * 60)

        if args.location:
            # Create for specific location
            logger.info(f"Creating folders for location: {args.location}")
            created_paths = create_folders_for_location(args.location, config)
            logger.info(f"Created {len(created_paths)} directories")

        else:
            # Create for all locations
            logger.info("Creating folders for all locations...")
            results = create_folders_for_all_locations(config)

            # Summary
            success_count = sum(1 for v in results.values() if v is not None)
            total_count = len(results)

            logger.info("=" * 60)
            logger.info(f"Processed {success_count}/{total_count} locations successfully")
            logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Folder creation failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
