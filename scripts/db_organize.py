#!/usr/bin/env python3
"""
AUPAT Organization Script
Extracts metadata and categorizes imported media.

This script:
1. Extracts EXIF from images using exiftool
2. Extracts metadata from videos using ffprobe
3. Categorizes by hardware (DSLR, phone, drone, etc.)
4. Matches live photos to videos
5. Links documents to media files

Version: 1.0.0
Last Updated: 2025-11-15
"""

import argparse
import json
import logging
import sqlite3
import subprocess
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

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


def load_camera_hardware() -> dict:
    """Load camera hardware classification rules."""
    hardware_path = Path(__file__).parent.parent / 'data' / 'camera_hardware.json'

    if not hardware_path.exists():
        logger.warning("camera_hardware.json not found - using default classification")
        return {}

    with open(hardware_path, 'r') as f:
        return json.load(f)


def extract_exif(file_path: str) -> dict:
    """
    Extract EXIF metadata using exiftool.

    Args:
        file_path: Path to image file

    Returns:
        dict: EXIF metadata as JSON
    """
    try:
        result = subprocess.run(
            ['exiftool', '-j', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data[0] if data else {}
        else:
            logger.warning(f"exiftool failed for {file_path}: {result.stderr}")
            return {}

    except FileNotFoundError:
        logger.error("exiftool not found - install with: brew install exiftool")
        return {}
    except Exception as e:
        logger.error(f"Failed to extract EXIF from {file_path}: {e}")
        return {}


def extract_video_metadata(file_path: str) -> dict:
    """
    Extract video metadata using ffprobe.

    Args:
        file_path: Path to video file

    Returns:
        dict: Video metadata as JSON
    """
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logger.warning(f"ffprobe failed for {file_path}: {result.stderr}")
            return {}

    except FileNotFoundError:
        logger.error("ffprobe not found - install with: brew install ffmpeg")
        return {}
    except Exception as e:
        logger.error(f"Failed to extract metadata from {file_path}: {e}")
        return {}


def categorize_hardware(make: str, model: str, hardware_rules: dict) -> str:
    """
    Categorize hardware based on make/model.

    Args:
        make: Camera/device make
        model: Camera/device model
        hardware_rules: Classification rules from camera_hardware.json

    Returns:
        str: Category (camera, phone, drone, go_pro, dash_cam, film, other)
    """
    if not make or not hardware_rules:
        return 'other'

    make_lower = make.lower()

    # Check each category
    for category, rules in hardware_rules.get('categories', {}).items():
        if 'makes' in rules:
            for rule_make in rules['makes']:
                if rule_make.lower() in make_lower:
                    return category.lower().replace(' ', '_')

    return 'other'


def organize_images(db_path: str) -> int:
    """
    Organize and categorize image files.

    Args:
        db_path: Path to database

    Returns:
        int: Number of images processed
    """
    logger.info("Organizing images...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    hardware_rules = load_camera_hardware()
    processed_count = 0

    try:
        # Get all images without hardware categorization
        cursor.execute(
            "SELECT img_sha256, img_loc, img_loco FROM images WHERE camera IS NULL"
        )
        images = cursor.fetchall()

        logger.info(f"Found {len(images)} images to process")
        print(f"PROGRESS: 0/{len(images)} images", flush=True)

        for img_sha256, img_loc, img_loco in images:
            if not img_loc or not Path(img_loc).exists():
                logger.warning(f"Image file not found: {img_loc}")
                continue

            # Extract EXIF
            exif = extract_exif(img_loc)

            make = exif.get('Make', '')
            model = exif.get('Model', '')

            # Categorize hardware
            category = categorize_hardware(make, model, hardware_rules)

            # Update database
            cursor.execute(
                """
                UPDATE images
                SET
                    exiftool_hardware = ?,
                    img_hardware = ?,
                    original = 1,
                    camera = ?,
                    phone = ?,
                    drone = ?,
                    go_pro = ?,
                    film = ?,
                    other = ?,
                    img_update = ?
                WHERE img_sha256 = ?
                """,
                (
                    1 if exif else 0,
                    json.dumps({'make': make, 'model': model}),
                    1 if category == 'camera' else 0,
                    1 if category == 'phone' else 0,
                    1 if category == 'drone' else 0,
                    1 if category == 'go_pro' else 0,
                    1 if category == 'film' else 0,
                    1 if category == 'other' else 0,
                    normalize_datetime(None),
                    img_sha256
                )
            )

            processed_count += 1
            logger.debug(f"Categorized image as {category}: {Path(img_loc).name}")
            print(f"PROGRESS: {processed_count}/{len(images)} images", flush=True)

        conn.commit()
        logger.info(f"Processed {processed_count} images")

    finally:
        conn.close()

    return processed_count


def organize_videos(db_path: str) -> int:
    """
    Organize and categorize video files.

    Args:
        db_path: Path to database

    Returns:
        int: Number of videos processed
    """
    logger.info("Organizing videos...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    hardware_rules = load_camera_hardware()
    processed_count = 0

    try:
        # Get all videos without hardware categorization
        cursor.execute(
            "SELECT vid_sha256, vid_loc FROM videos WHERE camera IS NULL"
        )
        videos = cursor.fetchall()

        logger.info(f"Found {len(videos)} videos to process")
        print(f"PROGRESS: 0/{len(videos)} videos", flush=True)

        for vid_sha256, vid_loc in videos:
            if not vid_loc or not Path(vid_loc).exists():
                logger.warning(f"Video file not found: {vid_loc}")
                continue

            # Extract metadata
            metadata = extract_video_metadata(vid_loc)

            # Try to get make/model from format tags
            tags = metadata.get('format', {}).get('tags', {})
            make = tags.get('make', tags.get('Make', ''))
            model = tags.get('model', tags.get('Model', ''))

            # Categorize hardware
            category = categorize_hardware(make, model, hardware_rules)

            # Update database
            cursor.execute(
                """
                UPDATE videos
                SET
                    ffmpeg_hardware = ?,
                    vid_hardware = ?,
                    original = 1,
                    camera = ?,
                    phone = ?,
                    drone = ?,
                    go_pro = ?,
                    dash_cam = ?,
                    other = ?,
                    vid_update = ?
                WHERE vid_sha256 = ?
                """,
                (
                    1 if metadata else 0,
                    json.dumps({'make': make, 'model': model}),
                    1 if category == 'camera' else 0,
                    1 if category == 'phone' else 0,
                    1 if category == 'drone' else 0,
                    1 if category == 'go_pro' else 0,
                    1 if category == 'dash_cam' else 0,
                    1 if category == 'other' else 0,
                    normalize_datetime(None),
                    vid_sha256
                )
            )

            processed_count += 1
            logger.debug(f"Categorized video as {category}: {Path(vid_loc).name}")
            print(f"PROGRESS: {processed_count}/{len(videos)} videos", flush=True)

        conn.commit()
        logger.info(f"Processed {processed_count} videos")

    finally:
        conn.close()

    return processed_count


def main():
    """Main organization workflow."""
    parser = argparse.ArgumentParser(
        description='Extract metadata and categorize AUPAT media'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file'
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
        logger.info("AUPAT Media Organization")
        logger.info("=" * 60)

        # Organize images
        images_count = organize_images(config['db_loc'])

        # Organize videos
        videos_count = organize_videos(config['db_loc'])

        # Summary
        logger.info("=" * 60)
        logger.info("Organization Summary")
        logger.info("=" * 60)
        logger.info(f"Images processed: {images_count}")
        logger.info(f"Videos processed: {videos_count}")
        logger.info("=" * 60)
        logger.info("ORGANIZATION SUCCESSFUL")
        logger.info("\nNext steps:")
        logger.info("  1. Run db_folder.py to create folder structure")
        logger.info("  2. Run db_ingest.py to move files to archive")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Organization failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
