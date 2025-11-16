#!/usr/bin/env python3
"""
AUPAT Ingest Script
Moves files from staging to organized archive structure.

This script:
1. Generates standardized filenames
2. Determines destination based on hardware category
3. Moves/hardlinks files to archive
4. Updates database with new locations
5. Preserves original timestamps

Version: 1.0.0
Last Updated: 2025-11-15
"""

import argparse
import logging
import os
import shutil
import sqlite3
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import generate_filename
from normalize import normalize_datetime, normalize_extension

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
        import json
        return json.load(f)


def can_hardlink(src: str, dst_dir: str) -> bool:
    """
    Check if source and destination are on same filesystem.

    Args:
        src: Source file path
        dst_dir: Destination directory path

    Returns:
        bool: True if can hardlink (same device)
    """
    try:
        src_stat = os.stat(src)
        dst_stat = os.stat(dst_dir)
        return src_stat.st_dev == dst_stat.st_dev
    except Exception:
        return False


def move_or_link_file(src: str, dst: str, preserve_times: bool = True) -> str:
    """
    Move or hardlink file from source to destination.

    Uses hardlink if same filesystem, otherwise copies.

    Args:
        src: Source file path
        dst: Destination file path
        preserve_times: Whether to preserve original timestamps

    Returns:
        str: Method used ('hardlink' or 'copy')
    """
    src_path = Path(src)
    dst_path = Path(dst)

    # Create destination directory
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if we can hardlink
    if can_hardlink(src, str(dst_path.parent)):
        # Use hardlink (same disk)
        os.link(src, dst)
        method = 'hardlink'
        logger.debug(f"Hardlinked: {src_path.name}")
    else:
        # Copy file (different disk)
        shutil.copy2(src, dst) if preserve_times else shutil.copy(src, dst)
        method = 'copy'
        logger.debug(f"Copied: {src_path.name}")

    return method


def get_destination_folder(
    category: str,
    media_type: str,
    arch_loc: str,
    state: str,
    loc_type: str,
    loc_name: str,
    loc_uuid8: str
) -> Path:
    """
    Determine destination folder based on hardware category.

    Args:
        category: Hardware category (camera, phone, drone, etc.)
        media_type: Type of media (img, vid, doc)
        arch_loc: Archive root
        state: State code
        loc_type: Location type
        loc_name: Location name (normalized)
        loc_uuid8: Location UUID8

    Returns:
        Path: Destination folder path
    """
    # Normalize location name for folder
    folder_loc_name = loc_name.lower().replace(' ', '-')

    # Base path
    state_type_dir = f"{state}-{loc_type}"
    location_dir = f"{folder_loc_name}_{loc_uuid8}"
    base_path = Path(arch_loc) / state_type_dir / location_dir

    # Determine subfolder based on media type and category
    if media_type == 'img':
        return base_path / 'photos' / f'original_{category}'
    elif media_type == 'vid':
        return base_path / 'videos' / f'original_{category}'
    elif media_type == 'doc':
        # Documents go to specific folders based on extension
        return base_path / 'documents'
    else:
        raise ValueError(f"Unknown media type: {media_type}")


def ingest_images(db_path: str, arch_loc: str, ingest_dir: str = None) -> int:
    """
    Ingest images from staging to archive.

    Args:
        db_path: Path to database
        arch_loc: Archive root directory
        ingest_dir: Staging/ingest directory path (required for detecting staging files)

    Returns:
        int: Number of images ingested
    """
    logger.info("Ingesting images...")

    if not ingest_dir:
        logger.warning("No ingest_dir specified - cannot determine which files are in staging")
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    ingested_count = 0

    try:
        # Get images that need ingesting (img_loc points to staging, not archive)
        # Images in staging will have img_loc starting with ingest_dir path
        cursor.execute(
            """
            SELECT
                i.img_sha256, i.img_name, i.img_loco, i.img_loc,
                i.camera, i.phone, i.drone, i.go_pro, i.film, i.other,
                i.loc_uuid, i.sub_uuid,
                l.loc_name, l.state, l.type
            FROM images i
            JOIN locations l ON i.loc_uuid = l.loc_uuid
            WHERE i.img_loc LIKE ? OR i.img_loc IS NULL OR i.img_loc = ''
            """,
            (f"{ingest_dir}%",)
        )
        images = cursor.fetchall()

        logger.info(f"Found {len(images)} images to ingest")

        for row in images:
            (img_sha256, img_name, img_loco, img_loc,
             camera, phone, drone, go_pro, film, other,
             loc_uuid, sub_uuid,
             loc_name, state, loc_type) = row

            # Determine category
            if camera:
                category = 'camera'
            elif phone:
                category = 'phone'
            elif drone:
                category = 'drone'
            elif go_pro:
                category = 'go-pro'
            elif film:
                category = 'film'
            else:
                category = 'other'

            # Source file is currently at img_loc (staging path set by db_import)
            # Use img_loc as the source if it exists, otherwise try fallback paths
            source_file = None
            if img_loc and Path(img_loc).exists():
                source_file = Path(img_loc)
            elif img_loco and Path(img_loco).exists():
                # Fallback to original location (shouldn't happen in normal flow)
                source_file = Path(img_loco)
            elif ingest_dir and img_name:
                # Fallback: construct staging path from ingest_dir/loc_uuid8/img_name
                loc_uuid8 = loc_uuid[:8]
                staging_path = Path(ingest_dir) / loc_uuid8 / img_name
                if staging_path.exists():
                    source_file = staging_path

            if not source_file:
                logger.warning(f"Source file not found for {img_name} (img_loc: {img_loc}, img_loco: {img_loco})")
                continue

            # Get file extension
            ext = normalize_extension(source_file.suffix)

            # Generate standardized filename (should match img_name, but regenerate for consistency)
            filename = generate_filename('img', loc_uuid, img_sha256, ext, sub_uuid)

            # Determine destination
            loc_uuid8 = loc_uuid[:8]
            dest_folder = get_destination_folder(
                category, 'img', arch_loc, state, loc_type, loc_name, loc_uuid8
            )
            dest_file = dest_folder / filename

            try:
                method = move_or_link_file(str(source_file), str(dest_file))

                # Update database
                cursor.execute(
                    """
                    UPDATE images
                    SET img_loc = ?, img_name = ?, img_update = ?
                    WHERE img_sha256 = ?
                    """,
                    (str(dest_file), filename, normalize_datetime(None), img_sha256)
                )

                ingested_count += 1
                logger.debug(f"Ingested ({method}): {filename}")

            except Exception as e:
                logger.error(f"Failed to ingest {img_name}: {e}")

        conn.commit()
        logger.info(f"Ingested {ingested_count} images")

    finally:
        conn.close()

    return ingested_count


def ingest_videos(db_path: str, arch_loc: str, ingest_dir: str = None) -> int:
    """
    Ingest videos from staging to archive.

    Args:
        db_path: Path to database
        arch_loc: Archive root directory
        ingest_dir: Staging/ingest directory path (required for detecting staging files)

    Returns:
        int: Number of videos ingested
    """
    logger.info("Ingesting videos...")

    if not ingest_dir:
        logger.warning("No ingest_dir specified - cannot determine which files are in staging")
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    ingested_count = 0

    try:
        # Get videos that need ingesting (vid_loc points to staging, not archive)
        # Videos in staging will have vid_loc starting with ingest_dir path
        cursor.execute(
            """
            SELECT
                v.vid_sha256, v.vid_name, v.vid_loco, v.vid_loc,
                v.camera, v.phone, v.drone, v.go_pro, v.dash_cam, v.other,
                v.loc_uuid, v.sub_uuid,
                l.loc_name, l.state, l.type
            FROM videos v
            JOIN locations l ON v.loc_uuid = l.loc_uuid
            WHERE v.vid_loc LIKE ? OR v.vid_loc IS NULL OR v.vid_loc = ''
            """,
            (f"{ingest_dir}%",)
        )
        videos = cursor.fetchall()

        logger.info(f"Found {len(videos)} videos to ingest")

        for row in videos:
            (vid_sha256, vid_name, vid_loco, vid_loc,
             camera, phone, drone, go_pro, dash_cam, other,
             loc_uuid, sub_uuid,
             loc_name, state, loc_type) = row

            # Determine category
            if camera:
                category = 'camera'
            elif phone:
                category = 'phone'
            elif drone:
                category = 'drone'
            elif go_pro:
                category = 'go-pro'
            elif dash_cam:
                category = 'dash-cam'
            else:
                category = 'other'

            # Source file is currently at vid_loc (staging path set by db_import)
            # Use vid_loc as the source if it exists, otherwise try fallback paths
            source_file = None
            if vid_loc and Path(vid_loc).exists():
                source_file = Path(vid_loc)
            elif vid_loco and Path(vid_loco).exists():
                # Fallback to original location (shouldn't happen in normal flow)
                source_file = Path(vid_loco)
            elif ingest_dir and vid_name:
                # Fallback: construct staging path from ingest_dir/loc_uuid8/vid_name
                loc_uuid8 = loc_uuid[:8]
                staging_path = Path(ingest_dir) / loc_uuid8 / vid_name
                if staging_path.exists():
                    source_file = staging_path

            if not source_file:
                logger.warning(f"Source file not found for {vid_name} (vid_loc: {vid_loc}, vid_loco: {vid_loco})")
                continue

            # Get file extension
            ext = normalize_extension(source_file.suffix)

            # Generate standardized filename (should match vid_name, but regenerate for consistency)
            filename = generate_filename('vid', loc_uuid, vid_sha256, ext, sub_uuid)

            # Determine destination
            loc_uuid8 = loc_uuid[:8]
            dest_folder = get_destination_folder(
                category, 'vid', arch_loc, state, loc_type, loc_name, loc_uuid8
            )
            dest_file = dest_folder / filename

            try:
                method = move_or_link_file(str(source_file), str(dest_file))

                # Update database
                cursor.execute(
                    """
                    UPDATE videos
                    SET vid_loc = ?, vid_name = ?, vid_update = ?
                    WHERE vid_sha256 = ?
                    """,
                    (str(dest_file), filename, normalize_datetime(None), vid_sha256)
                )

                ingested_count += 1
                logger.debug(f"Ingested ({method}): {filename}")

            except Exception as e:
                logger.error(f"Failed to ingest {vid_name}: {e}")

        conn.commit()
        logger.info(f"Ingested {ingested_count} videos")

    finally:
        conn.close()

    return ingested_count


def main():
    """Main ingest workflow."""
    parser = argparse.ArgumentParser(
        description='Move files from staging to AUPAT archive'
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
        logger.info("AUPAT File Ingest")
        logger.info("=" * 60)

        # Ingest images
        images_count = ingest_images(
            config['db_loc'],
            config['arch_loc'],
            config.get('db_ingest')
        )

        # Ingest videos
        videos_count = ingest_videos(
            config['db_loc'],
            config['arch_loc'],
            config.get('db_ingest')
        )

        # Summary
        logger.info("=" * 60)
        logger.info("Ingest Summary")
        logger.info("=" * 60)
        logger.info(f"Images ingested: {images_count}")
        logger.info(f"Videos ingested: {videos_count}")
        logger.info("=" * 60)
        logger.info("INGEST SUCCESSFUL")
        logger.info("\nNext steps:")
        logger.info("  1. Run db_verify.py to verify integrity")
        logger.info("  2. Run db_identify.py to generate JSON exports")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Ingest failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
