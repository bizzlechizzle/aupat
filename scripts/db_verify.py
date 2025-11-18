#!/usr/bin/env python3
"""
AUPAT Verification Script
Verifies SHA256 integrity of files after import and cleans up staging.

This script:
1. Verifies all files in archive match database SHA256
2. Cleans up staging directory if verification passes
3. Updates verification timestamps

Version: 1.0.0
Last Updated: 2025-11-15
"""

import argparse
import logging
import shutil
import sqlite3
import sys
from pathlib import Path

from scripts.utils import calculate_sha256
from scripts.normalize import normalize_datetime

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


def verify_files(db_path: str, location_uuid: str = None) -> tuple:
    """
    Verify all files in database match their SHA256 hashes.

    Args:
        db_path: Path to database
        location_uuid: Optional location UUID to verify only files from that location

    Returns:
        tuple: (verified_count, failed_files)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    verified_count = 0
    failed_files = []

    try:
        # Get counts first for progress tracking
        if location_uuid:
            cursor.execute("SELECT COUNT(*) FROM images WHERE loc_uuid = ?", (location_uuid,))
            img_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM videos WHERE loc_uuid = ?", (location_uuid,))
            vid_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM documents WHERE loc_uuid = ?", (location_uuid,))
            doc_count = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM images")
            img_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM videos")
            vid_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]

        total_files = img_count + vid_count + doc_count
        progress_count = 0

        logger.info(f"Verifying {total_files} total files ({img_count} images, {vid_count} videos, {doc_count} documents)")
        print(f"PROGRESS: 0/{total_files} files", flush=True)

        # Verify images
        logger.info("Verifying images...")
        if location_uuid:
            cursor.execute(
                "SELECT img_sha256, img_loc, img_name FROM images WHERE loc_uuid = ?",
                (location_uuid,)
            )
        else:
            cursor.execute("SELECT img_sha256, img_loc, img_name FROM images")
        for sha256_db, img_loc, img_name in cursor.fetchall():
            if not img_loc or not Path(img_loc).exists():
                logger.warning(f"Image file not found: {img_name}")
                failed_files.append(('image', img_name, 'File not found'))
                continue

            try:
                sha256_file = calculate_sha256(img_loc)
                if sha256_file == sha256_db:
                    verified_count += 1
                    progress_count += 1
                    print(f"PROGRESS: {progress_count}/{total_files} files", flush=True)
                else:
                    logger.error(f"SHA256 mismatch for {img_name}")
                    failed_files.append(('image', img_name, 'SHA256 mismatch'))
                    progress_count += 1
                    print(f"PROGRESS: {progress_count}/{total_files} files", flush=True)
            except Exception as e:
                logger.error(f"Failed to verify {img_name}: {e}")
                failed_files.append(('image', img_name, str(e)))

        # Verify videos
        logger.info("Verifying videos...")
        if location_uuid:
            cursor.execute(
                "SELECT vid_sha256, vid_loc, vid_name FROM videos WHERE loc_uuid = ?",
                (location_uuid,)
            )
        else:
            cursor.execute("SELECT vid_sha256, vid_loc, vid_name FROM videos")
        for sha256_db, vid_loc, vid_name in cursor.fetchall():
            if not vid_loc or not Path(vid_loc).exists():
                logger.warning(f"Video file not found: {vid_name}")
                failed_files.append(('video', vid_name, 'File not found'))
                continue

            try:
                sha256_file = calculate_sha256(vid_loc)
                if sha256_file == sha256_db:
                    verified_count += 1
                    progress_count += 1
                    print(f"PROGRESS: {progress_count}/{total_files} files", flush=True)
                else:
                    logger.error(f"SHA256 mismatch for {vid_name}")
                    failed_files.append(('video', vid_name, 'SHA256 mismatch'))
                    progress_count += 1
                    print(f"PROGRESS: {progress_count}/{total_files} files", flush=True)
            except Exception as e:
                logger.error(f"Failed to verify {vid_name}: {e}")
                failed_files.append(('video', vid_name, str(e)))

        # Verify documents
        logger.info("Verifying documents...")
        if location_uuid:
            cursor.execute(
                "SELECT doc_sha256, doc_loc, doc_name FROM documents WHERE loc_uuid = ?",
                (location_uuid,)
            )
        else:
            cursor.execute("SELECT doc_sha256, doc_loc, doc_name FROM documents")
        for sha256_db, doc_loc, doc_name in cursor.fetchall():
            if not doc_loc or not Path(doc_loc).exists():
                logger.warning(f"Document file not found: {doc_name}")
                failed_files.append(('document', doc_name, 'File not found'))
                continue

            try:
                sha256_file = calculate_sha256(doc_loc)
                if sha256_file == sha256_db:
                    verified_count += 1
                    progress_count += 1
                    print(f"PROGRESS: {progress_count}/{total_files} files", flush=True)
                else:
                    logger.error(f"SHA256 mismatch for {doc_name}")
                    failed_files.append(('document', doc_name, 'SHA256 mismatch'))
                    progress_count += 1
                    print(f"PROGRESS: {progress_count}/{total_files} files", flush=True)
            except Exception as e:
                logger.error(f"Failed to verify {doc_name}: {e}")
                failed_files.append(('document', doc_name, str(e)))

    finally:
        conn.close()

    return verified_count, failed_files


def cleanup_staging(ingest_dir: str, dry_run: bool = False) -> int:
    """
    Clean up staging directory after successful verification.

    Args:
        ingest_dir: Path to staging directory
        dry_run: If True, only report what would be deleted

    Returns:
        int: Number of files/directories removed
    """
    ingest_path = Path(ingest_dir)

    if not ingest_path.exists():
        logger.warning(f"Staging directory not found: {ingest_dir}")
        return 0

    removed_count = 0

    # List all items in staging
    items = list(ingest_path.iterdir())

    if not items:
        logger.info("Staging directory is already empty")
        return 0

    logger.info(f"Found {len(items)} items in staging directory")

    for item in items:
        if dry_run:
            logger.info(f"Would remove: {item.name}")
            removed_count += 1
        else:
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                    logger.info(f"Removed directory: {item.name}")
                else:
                    item.unlink()
                    logger.info(f"Removed file: {item.name}")
                removed_count += 1
            except Exception as e:
                logger.error(f"Failed to remove {item.name}: {e}")

    return removed_count


def main():
    """Main verification workflow."""
    parser = argparse.ArgumentParser(
        description='Verify SHA256 integrity and cleanup staging'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file'
    )
    parser.add_argument(
        '--location',
        type=str,
        help='Verify only files from this location UUID (optional)'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip staging cleanup even if verification passes'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - show what would be deleted without deleting'
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
        logger.info("AUPAT File Verification")
        logger.info("=" * 60)

        # Verify all files (or just files from specified location)
        if args.location:
            logger.info(f"Verifying file integrity for location {args.location}...")
        else:
            logger.info("Verifying file integrity...")
        verified_count, failed_files = verify_files(config['db_loc'], args.location)

        # Report results
        logger.info("=" * 60)
        logger.info(f"Verified: {verified_count} files")
        logger.info(f"Failed: {len(failed_files)} files")
        logger.info("=" * 60)

        if failed_files:
            logger.error("Verification failures:")
            for file_type, filename, error in failed_files:
                logger.error(f"  [{file_type}] {filename}: {error}")
            logger.error("=" * 60)
            logger.error("VERIFICATION FAILED - Staging NOT cleaned up")
            logger.error("Fix errors and re-run verification")
            logger.error("=" * 60)
            return 1

        # Verification passed - cleanup staging
        if not args.no_cleanup:
            logger.info("All files verified successfully")
            logger.info("Cleaning up staging directory...")

            removed_count = cleanup_staging(
                config.get('db_ingest', ''),
                dry_run=args.dry_run
            )

            if args.dry_run:
                logger.info(f"Dry run: Would remove {removed_count} items")
            else:
                logger.info(f"Removed {removed_count} items from staging")

        logger.info("=" * 60)
        logger.info("VERIFICATION SUCCESSFUL")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
