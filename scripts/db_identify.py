#!/usr/bin/env python3
"""
AUPAT JSON Export Script
Generates master JSON export files for each location.

This script:
1. Queries all data for each location
2. Compiles comprehensive JSON structure
3. Writes to location's archive folder
4. Updates json_update timestamp

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

from utils import generate_master_json_filename
from normalize import normalize_datetime

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


def export_location_json(loc_uuid: str, db_path: str, arch_loc: str) -> str:
    """
    Export comprehensive JSON for a location.

    Args:
        loc_uuid: Location UUID
        db_path: Path to database
        arch_loc: Archive root directory

    Returns:
        str: Path to created JSON file
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    try:
        # Get location details
        cursor.execute("SELECT * FROM locations WHERE loc_uuid = ?", (loc_uuid,))
        loc_row = cursor.fetchone()

        if not loc_row:
            raise ValueError(f"Location not found: {loc_uuid}")

        location = dict(loc_row)

        # Get sub-locations
        cursor.execute("SELECT * FROM sub_locations WHERE loc_uuid = ?", (loc_uuid,))
        sub_locations = [dict(row) for row in cursor.fetchall()]

        # Get images
        cursor.execute("SELECT * FROM images WHERE loc_uuid = ?", (loc_uuid,))
        images = [dict(row) for row in cursor.fetchall()]

        # Get videos
        cursor.execute("SELECT * FROM videos WHERE loc_uuid = ?", (loc_uuid,))
        videos = [dict(row) for row in cursor.fetchall()]

        # Get documents
        cursor.execute("SELECT * FROM documents WHERE loc_uuid = ?", (loc_uuid,))
        documents = [dict(row) for row in cursor.fetchall()]

        # Get URLs
        cursor.execute("SELECT * FROM urls WHERE loc_uuid = ?", (loc_uuid,))
        urls = [dict(row) for row in cursor.fetchall()]

        # Compile master JSON
        master_data = {
            "location": location,
            "sub_locations": sub_locations,
            "images": images,
            "videos": videos,
            "documents": documents,
            "urls": urls,
            "metadata": {
                "export_date": normalize_datetime(None),
                "total_images": len(images),
                "total_videos": len(videos),
                "total_documents": len(documents),
                "total_urls": len(urls),
                "total_sub_locations": len(sub_locations)
            }
        }

        # Determine output path
        loc_uuid8 = loc_uuid[:8]
        loc_name = location['loc_name'].lower().replace(' ', '-')
        state = location['state']
        loc_type = location['type']

        state_type_dir = f"{state}-{loc_type}"
        location_dir = f"{loc_name}_{loc_uuid8}"
        output_dir = Path(arch_loc) / state_type_dir / location_dir

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        json_filename = generate_master_json_filename(loc_uuid)
        output_file = output_dir / json_filename

        # Write JSON
        logger.info(f"Writing JSON to: {output_file}")
        with open(output_file, 'w') as f:
            json.dump(master_data, f, indent=2)

        # Update json_update timestamp in database
        timestamp = normalize_datetime(None)
        cursor.execute(
            "UPDATE locations SET json_update = ? WHERE loc_uuid = ?",
            (timestamp, loc_uuid)
        )
        conn.commit()

        logger.info(f"JSON export complete: {json_filename}")

        return str(output_file)

    finally:
        conn.close()


def export_all_locations(db_path: str, arch_loc: str) -> dict:
    """
    Export JSON for all locations.

    Args:
        db_path: Path to database
        arch_loc: Archive root directory

    Returns:
        dict: Mapping of loc_uuid to exported JSON path
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    results = {}

    try:
        # Get all location UUIDs
        cursor.execute("SELECT loc_uuid, loc_name FROM locations")
        locations = cursor.fetchall()

        logger.info(f"Found {len(locations)} locations to export")

        for loc_uuid, loc_name in locations:
            logger.info(f"Exporting location: {loc_name} ({loc_uuid[:8]})")

            try:
                json_path = export_location_json(loc_uuid, db_path, arch_loc)
                results[loc_uuid] = json_path
            except Exception as e:
                logger.error(f"Failed to export {loc_name}: {e}")
                results[loc_uuid] = None

        return results

    finally:
        conn.close()


def main():
    """Main JSON export workflow."""
    parser = argparse.ArgumentParser(
        description='Generate master JSON exports for AUPAT locations'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file'
    )
    parser.add_argument(
        '--location',
        type=str,
        help='Export specific location UUID (default: all locations)'
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
        logger.info("AUPAT JSON Export")
        logger.info("=" * 60)

        if args.location:
            # Export specific location
            logger.info(f"Exporting location: {args.location}")
            json_path = export_location_json(
                args.location,
                config['db_loc'],
                config['arch_loc']
            )
            logger.info(f"Exported to: {json_path}")

        else:
            # Export all locations
            logger.info("Exporting all locations...")
            results = export_all_locations(
                config['db_loc'],
                config['arch_loc']
            )

            # Summary
            success_count = sum(1 for v in results.values() if v is not None)
            total_count = len(results)

            logger.info("=" * 60)
            logger.info(f"Exported {success_count}/{total_count} locations successfully")
            logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"JSON export failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
