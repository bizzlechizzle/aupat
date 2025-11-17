#!/usr/bin/env python3
"""
AUPAT Media Extractor Worker
Extracts media from archived URLs and uploads to Immich.

This worker:
1. Polls database for archived URLs with media_extracted=0
2. Scans ArchiveBox archive directories for media files
3. Uploads media to Immich
4. Links media to locations via images/videos tables
5. Updates media_extracted count
6. Runs as long-running daemon until interrupted

Version: 0.1.2
Last Updated: 2025-11-17
"""

import argparse
import json
import logging
import os
import signal
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from normalize import normalize_datetime
from utils import generate_uuid, calculate_sha256

# Configure logging
def setup_logging():
    """Setup logging with file and console handlers."""
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'media_extractor.log'

    handlers = [logging.StreamHandler()]

    try:
        handlers.append(logging.FileHandler(log_file))
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not create log file {log_file}: {e}")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

setup_logging()
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle SIGINT and SIGTERM for graceful shutdown."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


def load_user_config(config_path: str = None) -> dict:
    """
    Load user configuration from user.json.

    Args:
        config_path: Path to user.json (defaults to ../user/user.json)

    Returns:
        dict: Configuration with database path and ArchiveBox directory

    Raises:
        FileNotFoundError: If user.json doesn't exist
        ValueError: If required keys are missing
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"user.json not found at {config_path}. "
            "Create from user/user.json.template or run setup.sh"
        )

    with open(config_path, 'r') as f:
        config = json.load(f)

    required = ['db_name', 'db_loc']
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing required keys in user.json: {missing}")

    # Validate db_loc is a file path
    db_path = Path(config['db_loc'])
    if db_path.exists() and db_path.is_dir():
        raise ValueError(
            f"db_loc must be a file path, not a directory: {config['db_loc']}"
        )

    # Ensure parent directory exists
    db_parent = db_path.parent
    if not db_parent.exists():
        raise FileNotFoundError(
            f"Database directory does not exist: {db_parent}"
        )

    return config


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Create database connection with proper configuration.

    Args:
        db_path: Path to SQLite database file

    Returns:
        sqlite3.Connection: Configured database connection
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_pending_extractions(db_path: str, limit: int = 5) -> List[Dict]:
    """
    Fetch URLs with media to extract from database.

    Args:
        db_path: Path to database file
        limit: Maximum number of URLs to fetch (default: 5)

    Returns:
        List of dictionaries with url_uuid, url, archivebox_snapshot_id, loc_uuid
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url_uuid, url, archivebox_snapshot_id, loc_uuid
            FROM urls
            WHERE archive_status = 'archiving'
              AND media_extracted = 0
              AND archivebox_snapshot_id IS NOT NULL
            ORDER BY archive_date ASC
            LIMIT ?
        """, (limit,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    except Exception as e:
        logger.error(f"Failed to fetch pending extractions: {e}")
        return []


def get_media_from_snapshot(snapshot_id: str, archivebox_data_dir: str) -> List[Dict]:
    """
    Get media files from ArchiveBox snapshot using adapter.

    Args:
        snapshot_id: ArchiveBox snapshot ID (timestamp)
        archivebox_data_dir: Path to ArchiveBox data directory

    Returns:
        List of media file dictionaries
    """
    try:
        from adapters.archivebox_adapter import create_archivebox_adapter

        adapter = create_archivebox_adapter()
        media_files = adapter.get_snapshot_files(snapshot_id, archivebox_data_dir)

        logger.info(f"Found {len(media_files)} media files in snapshot {snapshot_id}")
        return media_files

    except Exception as e:
        logger.error(f"Failed to get media from snapshot {snapshot_id}: {e}")
        return []


def upload_media_to_immich(file_path: str) -> Optional[str]:
    """
    Upload media file to Immich.

    Args:
        file_path: Absolute path to media file

    Returns:
        Optional[str]: Immich asset_id if successful, None if failed
    """
    try:
        from adapters.immich_adapter import create_immich_adapter

        adapter = create_immich_adapter()
        asset_id = adapter.upload(file_path, device_id='aupat-media-extractor')

        if asset_id:
            logger.info(f"Uploaded to Immich: {Path(file_path).name} → {asset_id}")
            return asset_id
        else:
            logger.warning(f"Immich upload returned no asset_id for {file_path}")
            return None

    except Exception as e:
        logger.error(f"Immich upload failed for {file_path}: {e}")
        return None


def insert_image_to_db(db_path: str, loc_uuid: str, source_url: str,
                      file_path: str, sha256: str, asset_id: str) -> bool:
    """
    Insert image record to database.

    Args:
        db_path: Path to database file
        loc_uuid: Location UUID
        source_url: Original URL the media was extracted from
        file_path: Path to image file
        sha256: SHA256 hash of file
        asset_id: Immich asset ID

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        file_obj = Path(file_path)
        timestamp = normalize_datetime(None)

        # Generate UUID
        img_uuid = generate_uuid(cursor, 'images', 'img_uuid')

        # Get file metadata
        img_ext = file_obj.suffix.lstrip('.')
        img_size = file_obj.stat().st_size

        cursor.execute("""
            INSERT INTO images (
                img_uuid, loc_uuid, img_sha, img_name, img_ext,
                img_size_bytes, immich_asset_id, source_url,
                img_add, img_update
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            img_uuid, loc_uuid, sha256, file_obj.stem, img_ext,
            img_size, asset_id, source_url,
            timestamp, timestamp
        ))

        conn.commit()
        conn.close()

        logger.info(f"Inserted image to database: {img_uuid}")
        return True

    except Exception as e:
        logger.error(f"Failed to insert image to database: {e}")
        return False


def insert_video_to_db(db_path: str, loc_uuid: str, source_url: str,
                      file_path: str, sha256: str, asset_id: str) -> bool:
    """
    Insert video record to database.

    Args:
        db_path: Path to database file
        loc_uuid: Location UUID
        source_url: Original URL the media was extracted from
        file_path: Path to video file
        sha256: SHA256 hash of file
        asset_id: Immich asset ID

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        file_obj = Path(file_path)
        timestamp = normalize_datetime(None)

        # Generate UUID
        vid_uuid = generate_uuid(cursor, 'videos', 'vid_uuid')

        # Get file metadata
        vid_ext = file_obj.suffix.lstrip('.')
        vid_size = file_obj.stat().st_size

        cursor.execute("""
            INSERT INTO videos (
                vid_uuid, loc_uuid, vid_sha, vid_name, vid_ext,
                vid_size_bytes, immich_asset_id, source_url,
                vid_add, vid_update
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vid_uuid, loc_uuid, sha256, file_obj.stem, vid_ext,
            vid_size, asset_id, source_url,
            timestamp, timestamp
        ))

        conn.commit()
        conn.close()

        logger.info(f"Inserted video to database: {vid_uuid}")
        return True

    except Exception as e:
        logger.error(f"Failed to insert video to database: {e}")
        return False


def check_media_already_imported(db_path: str, sha256: str, media_type: str) -> bool:
    """
    Check if media with this SHA256 is already imported.

    Args:
        db_path: Path to database file
        sha256: SHA256 hash to check
        media_type: 'image' or 'video'

    Returns:
        bool: True if already imported, False otherwise
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        if media_type == 'image':
            cursor.execute("SELECT img_uuid FROM images WHERE img_sha = ?", (sha256,))
        else:  # video
            cursor.execute("SELECT vid_uuid FROM videos WHERE vid_sha = ?", (sha256,))

        result = cursor.fetchone()
        conn.close()

        return result is not None

    except Exception as e:
        logger.error(f"Error checking media import status: {e}")
        return False


def update_url_media_extracted(db_path: str, url_uuid: str, count: int) -> bool:
    """
    Update URL with media_extracted count.

    Args:
        db_path: Path to database file
        url_uuid: UUID of URL to update
        count: Number of media files extracted

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        timestamp = normalize_datetime(None)

        cursor.execute("""
            UPDATE urls
            SET media_extracted = ?,
                url_update = ?
            WHERE url_uuid = ?
        """, (count, timestamp, url_uuid))

        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()

        if rows_affected > 0:
            logger.info(f"Updated URL {url_uuid}: media_extracted={count}")
            return True
        else:
            logger.warning(f"No rows updated for url_uuid={url_uuid}")
            return False

    except Exception as e:
        logger.error(f"Failed to update URL {url_uuid}: {e}")
        return False


def process_pending_extractions(db_path: str, archivebox_data_dir: str) -> Tuple[int, int]:
    """
    Process all URLs pending media extraction.

    Args:
        db_path: Path to database file
        archivebox_data_dir: Path to ArchiveBox data directory

    Returns:
        Tuple[int, int]: (total_media_extracted, urls_processed)
    """
    pending_urls = fetch_pending_extractions(db_path, limit=5)

    if not pending_urls:
        logger.debug("No pending media extractions")
        return (0, 0)

    logger.info(f"Processing {len(pending_urls)} URL(s) for media extraction")

    total_media = 0
    urls_processed = 0

    for url_data in pending_urls:
        if shutdown_requested:
            logger.info("Shutdown requested, stopping extraction")
            break

        url_uuid = url_data['url_uuid']
        url = url_data['url']
        snapshot_id = url_data['archivebox_snapshot_id']
        loc_uuid = url_data['loc_uuid']

        logger.info(f"Extracting media from: {url}")

        # Get media files from snapshot
        media_files = get_media_from_snapshot(snapshot_id, archivebox_data_dir)

        if not media_files:
            logger.info(f"  No media found in snapshot {snapshot_id}")
            # Still update to mark as processed (avoid reprocessing)
            update_url_media_extracted(db_path, url_uuid, 0)
            urls_processed += 1
            continue

        extracted_count = 0

        for media_file in media_files:
            if shutdown_requested:
                break

            file_path = media_file['path']
            media_type = media_file['type']

            logger.info(f"  Processing {media_type}: {Path(file_path).name}")

            # Calculate SHA256
            try:
                sha256 = calculate_sha256(file_path)
            except Exception as e:
                logger.error(f"  Failed to calculate SHA256 for {file_path}: {e}")
                continue

            # Check if already imported
            if check_media_already_imported(db_path, sha256, media_type):
                logger.info(f"  Already imported (SHA256: {sha256[:16]}...), skipping")
                continue

            # Upload to Immich
            asset_id = upload_media_to_immich(file_path)

            if not asset_id:
                logger.warning(f"  Failed to upload {file_path}")
                continue

            # Rate limiting: delay between uploads
            time.sleep(2)

            # Insert to database
            if media_type == 'image':
                success = insert_image_to_db(
                    db_path, loc_uuid, url, file_path, sha256, asset_id
                )
            else:  # video
                success = insert_video_to_db(
                    db_path, loc_uuid, url, file_path, sha256, asset_id
                )

            if success:
                extracted_count += 1
                total_media += 1
            else:
                logger.warning(f"  Failed to insert {media_type} to database")

        # Update URL with extraction count
        update_url_media_extracted(db_path, url_uuid, extracted_count)
        urls_processed += 1

        logger.info(f"  Extracted {extracted_count} media file(s) from {url}")

    return (total_media, urls_processed)


def run_worker(db_path: str, archivebox_data_dir: str, poll_interval: int = 60):
    """
    Run media extraction worker daemon.

    Continuously polls database for URLs with media to extract.
    Runs until SIGINT (Ctrl+C) or SIGTERM received.

    Args:
        db_path: Path to database file
        archivebox_data_dir: Path to ArchiveBox data directory
        poll_interval: Seconds between polling cycles (default: 60)
    """
    logger.info("="*60)
    logger.info("AUPAT Media Extraction Worker Started")
    logger.info(f"Database: {db_path}")
    logger.info(f"ArchiveBox Data Dir: {archivebox_data_dir}")
    logger.info(f"Poll Interval: {poll_interval} seconds")
    logger.info("="*60)

    # Verify database exists
    if not Path(db_path).exists():
        logger.error(f"Database not found: {db_path}")
        logger.error("Run db_migrate_v012.py to create database")
        sys.exit(1)

    # Verify ArchiveBox directory exists
    archivebox_path = Path(archivebox_data_dir)
    if not archivebox_path.exists():
        logger.error(f"ArchiveBox directory not found: {archivebox_data_dir}")
        sys.exit(1)

    cycle_count = 0
    total_media_extracted = 0
    total_urls_processed = 0

    while not shutdown_requested:
        cycle_count += 1
        logger.info(f"--- Polling Cycle {cycle_count} ---")

        try:
            media_count, url_count = process_pending_extractions(
                db_path, archivebox_data_dir
            )

            total_media_extracted += media_count
            total_urls_processed += url_count

            if media_count > 0 or url_count > 0:
                logger.info(
                    f"Cycle {cycle_count} complete: "
                    f"{media_count} media extracted from {url_count} URL(s)"
                )

        except Exception as e:
            logger.error(f"Error in polling cycle {cycle_count}: {e}")

        # Sleep for poll interval (check shutdown flag every second)
        for _ in range(poll_interval):
            if shutdown_requested:
                break
            time.sleep(1)

    logger.info("="*60)
    logger.info("AUPAT Media Extraction Worker Stopped")
    logger.info(f"Total Media Extracted: {total_media_extracted}")
    logger.info(f"Total URLs Processed: {total_urls_processed}")
    logger.info("="*60)


def main():
    """Main entry point for media extraction worker."""
    parser = argparse.ArgumentParser(
        description="AUPAT Media Extraction Worker - Extracts media from archived URLs"
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to user.json config file (default: ../user/user.json)'
    )
    parser.add_argument(
        '--archivebox-dir',
        type=str,
        default=None,
        help='Path to ArchiveBox data directory (default: auto-detect from project root)'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=60,
        help='Polling interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing/cron)'
    )

    args = parser.parse_args()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Load configuration
        config = load_user_config(args.config)
        db_path = config['db_loc']

        # Auto-detect ArchiveBox directory if not provided
        if args.archivebox_dir is None:
            project_root = Path(__file__).parent.parent
            archivebox_dir = str(project_root / 'data' / 'archivebox')
            logger.info(f"Using auto-detected ArchiveBox directory: {archivebox_dir}")
        else:
            archivebox_dir = args.archivebox_dir

        if args.once:
            # Run once and exit
            logger.info("Running in single-shot mode")
            media_count, url_count = process_pending_extractions(
                db_path, archivebox_dir
            )
            logger.info(
                f"Processed: {media_count} media extracted from {url_count} URL(s)"
            )
            sys.exit(0 if media_count >= 0 else 1)
        else:
            # Run as daemon
            run_worker(db_path, archivebox_dir, args.poll_interval)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
