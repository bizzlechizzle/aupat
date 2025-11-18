#!/usr/bin/env python3
"""
AUPAT ArchiveBox Background Worker
Processes URLs with archive_status='pending' by calling ArchiveBox CLI.

This worker:
1. Polls database for pending URLs every 30 seconds
2. Archives URLs using ArchiveBox CLI via subprocess
3. Updates database with snapshot_id and status='archiving'
4. Handles failures gracefully with retry logic
5. Runs as long-running daemon until interrupted

Version: 0.1.2
Last Updated: 2025-11-17
"""

import argparse
import json
import logging
import os
import re
import signal
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from scripts.normalize import normalize_datetime

# Configure logging
def setup_logging():
    """Setup logging with file and console handlers."""
    # Determine log file path
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)  # Ensure logs directory exists
    log_file = log_dir / 'archive_worker.log'

    # Create handlers
    handlers = [logging.StreamHandler()]

    try:
        handlers.append(logging.FileHandler(log_file))
    except (PermissionError, OSError) as e:
        # Fall back to console-only logging if file creation fails
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
        dict: Configuration with database path

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

    # Validate db_loc is a file path, not a directory
    db_path = Path(config['db_loc'])
    if db_path.exists() and db_path.is_dir():
        raise ValueError(
            f"db_loc must be a file path, not a directory: {config['db_loc']}"
        )

    # Ensure parent directory exists
    db_parent = db_path.parent
    if not db_parent.exists():
        raise FileNotFoundError(
            f"Database directory does not exist: {db_parent}. "
            "Run setup.sh or create directory manually."
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


def fetch_pending_urls(db_path: str, limit: int = 10) -> List[Dict]:
    """
    Fetch URLs with archive_status='pending' from database.

    Args:
        db_path: Path to database file
        limit: Maximum number of URLs to fetch (default: 10)

    Returns:
        List of dictionaries with url_uuid, url, url_add, url_title, archive_status fields
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url_uuid, url, url_add, url_title, archive_status
            FROM urls
            WHERE archive_status = 'pending'
            ORDER BY url_add ASC
            LIMIT ?
        """, (limit,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    except Exception as e:
        logger.error(f"Failed to fetch pending URLs: {e}")
        return []


def archive_url_cli(url: str) -> Optional[str]:
    """
    Archive URL using ArchiveBox CLI via subprocess.

    Executes: docker compose exec -T --user=archivebox archivebox archivebox add <url>

    Args:
        url: URL to archive

    Returns:
        Optional[str]: Snapshot ID (timestamp) if successful, None if failed

    Raises:
        subprocess.CalledProcessError: If docker command fails
    """
    try:
        logger.info(f"Archiving via CLI: {url}")

        # Run docker compose exec command
        # -T flag disables pseudo-TTY allocation (required for subprocess)
        # --user=archivebox runs as archivebox user, not root (security requirement)
        result = subprocess.run(
            ['docker', 'compose', 'exec', '-T', '--user=archivebox', 'archivebox', 'archivebox', 'add', url],
            cwd=Path(__file__).parent.parent,  # Run from project root
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            check=False  # Don't raise on non-zero exit
        )

        # Log output for debugging
        if result.stdout:
            logger.debug(f"ArchiveBox stdout: {result.stdout[:500]}")
        if result.stderr:
            logger.debug(f"ArchiveBox stderr: {result.stderr[:500]}")

        # Check if command succeeded
        if result.returncode != 0:
            logger.warning(f"ArchiveBox CLI failed with exit code {result.returncode}")
            return None

        # Parse output to extract snapshot_id (timestamp)
        # ArchiveBox output includes lines like:
        # > Adding URL(s) to ArchiveBox...
        # > [i] [2025-11-17 12:34:56] 1763405109.545363: https://example.com
        # The timestamp is the snapshot_id

        snapshot_id = extract_snapshot_id(result.stdout)

        if snapshot_id:
            logger.info(f"Archive successful, snapshot_id: {snapshot_id}")
            return snapshot_id
        else:
            logger.warning(f"Could not extract snapshot_id from ArchiveBox output")
            # Return a timestamp-based fallback if parsing fails but command succeeded
            return str(time.time())

    except subprocess.TimeoutExpired:
        logger.error(f"ArchiveBox CLI timeout for {url}")
        return None

    except Exception as e:
        logger.error(f"ArchiveBox CLI error for {url}: {e}")
        return None


def extract_snapshot_id(output: str) -> Optional[str]:
    """
    Extract snapshot ID (timestamp) from ArchiveBox CLI output.

    Looks for patterns like:
    - 1763405109.545363
    - [timestamp] followed by URL

    Args:
        output: ArchiveBox CLI stdout

    Returns:
        Optional[str]: Snapshot ID if found, None otherwise
    """
    # Pattern 1: Timestamp with decimal (e.g., 1763405109.545363)
    match = re.search(r'\b(\d{10,}\.\d+)\b', output)
    if match:
        return match.group(1)

    # Pattern 2: Timestamp without decimal (e.g., 1763405109)
    match = re.search(r'\b(\d{10,})\b', output)
    if match:
        return match.group(1)

    # Pattern 3: Look for "snapshot" or "archive" followed by ID
    match = re.search(r'(?:snapshot|archive).*?(\d{10,}(?:\.\d+)?)', output, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def update_url_archived(db_path: str, url_uuid: str, snapshot_id: str) -> bool:
    """
    Update URL in database with snapshot_id and status='archiving'.

    Args:
        db_path: Path to database file
        url_uuid: UUID of URL to update
        snapshot_id: ArchiveBox snapshot ID (timestamp)

    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        timestamp = normalize_datetime(None)  # Current timestamp

        cursor.execute("""
            UPDATE urls
            SET archivebox_snapshot_id = ?,
                archive_status = 'archiving',
                archive_date = ?,
                url_update = ?
            WHERE url_uuid = ?
        """, (snapshot_id, timestamp, timestamp, url_uuid))

        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()

        if rows_affected > 0:
            logger.info(f"Updated URL {url_uuid}: snapshot_id={snapshot_id}, status='archiving'")
            return True
        else:
            logger.warning(f"No rows updated for url_uuid={url_uuid}")
            return False

    except Exception as e:
        logger.error(f"Failed to update URL {url_uuid}: {e}")
        return False


def mark_url_failed(db_path: str, url_uuid: str) -> bool:
    """
    Mark URL as failed after max retry attempts.

    Args:
        db_path: Path to database file
        url_uuid: UUID of URL to mark as failed

    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        timestamp = normalize_datetime(None)

        cursor.execute("""
            UPDATE urls
            SET archive_status = 'failed',
                url_update = ?
            WHERE url_uuid = ?
        """, (timestamp, url_uuid))

        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()

        if rows_affected > 0:
            logger.warning(f"Marked URL {url_uuid} as failed after max retries")
            return True
        else:
            logger.warning(f"No rows updated when marking {url_uuid} as failed")
            return False

    except Exception as e:
        logger.error(f"Failed to mark URL {url_uuid} as failed: {e}")
        return False


def process_pending_urls(db_path: str, max_retries: int = 3) -> Tuple[int, int]:
    """
    Process all pending URLs from database.

    Args:
        db_path: Path to database file
        max_retries: Maximum archiving attempts per URL (default: 3)

    Returns:
        Tuple[int, int]: (successful_count, failed_count)
    """
    # Track retry attempts in memory (resets on worker restart)
    retry_tracker = getattr(process_pending_urls, 'retry_tracker', {})

    pending_urls = fetch_pending_urls(db_path, limit=10)

    if not pending_urls:
        logger.debug("No pending URLs to process")
        return (0, 0)

    logger.info(f"Processing {len(pending_urls)} pending URL(s)")

    successful = 0
    failed = 0

    for url_data in pending_urls:
        if shutdown_requested:
            logger.info("Shutdown requested, stopping URL processing")
            break

        url_uuid = url_data['url_uuid']
        url = url_data['url']

        # Check retry count
        retry_count = retry_tracker.get(url_uuid, 0)

        if retry_count >= max_retries:
            logger.warning(f"Max retries ({max_retries}) exceeded for {url}")
            mark_url_failed(db_path, url_uuid)
            failed += 1
            continue

        # Attempt to archive
        snapshot_id = archive_url_cli(url)

        # Rate limiting: Small delay between archives to avoid overloading ArchiveBox
        time.sleep(1)

        if snapshot_id:
            # Success - update database
            if update_url_archived(db_path, url_uuid, snapshot_id):
                successful += 1
                # Remove from retry tracker
                retry_tracker.pop(url_uuid, None)
            else:
                # Database update failed - increment retry
                retry_tracker[url_uuid] = retry_count + 1
                failed += 1
        else:
            # Archive failed - increment retry count
            retry_tracker[url_uuid] = retry_count + 1
            logger.warning(f"Archive failed for {url} (attempt {retry_count + 1}/{max_retries})")
            failed += 1

    # Store retry tracker for next iteration
    process_pending_urls.retry_tracker = retry_tracker

    return (successful, failed)


def run_worker(db_path: str, poll_interval: int = 30, max_retries: int = 3):
    """
    Run background worker daemon.

    Continuously polls database for pending URLs and archives them.
    Runs until SIGINT (Ctrl+C) or SIGTERM received.

    Args:
        db_path: Path to database file
        poll_interval: Seconds between polling cycles (default: 30)
        max_retries: Maximum archiving attempts per URL (default: 3)
    """
    logger.info("="*60)
    logger.info("AUPAT ArchiveBox Background Worker Started")
    logger.info(f"Database: {db_path}")
    logger.info(f"Poll Interval: {poll_interval} seconds")
    logger.info(f"Max Retries: {max_retries}")
    logger.info("="*60)

    # Verify database exists
    if not Path(db_path).exists():
        logger.error(f"Database not found: {db_path}")
        logger.error("Run db_migrate_v012.py to create database")
        sys.exit(1)

    # Verify docker compose is available
    try:
        subprocess.run(['docker', 'compose', 'version'], capture_output=True, check=True)
    except Exception as e:
        logger.error(f"Docker Compose not available: {e}")
        logger.error("Ensure Docker Compose is installed and running")
        sys.exit(1)

    cycle_count = 0
    total_successful = 0
    total_failed = 0

    while not shutdown_requested:
        cycle_count += 1
        logger.info(f"--- Polling Cycle {cycle_count} ---")

        try:
            successful, failed = process_pending_urls(db_path, max_retries)
            total_successful += successful
            total_failed += failed

            if successful > 0 or failed > 0:
                logger.info(f"Cycle {cycle_count} complete: {successful} successful, {failed} failed")

        except Exception as e:
            logger.error(f"Error in polling cycle {cycle_count}: {e}")

        # Sleep for poll interval (check shutdown flag every second)
        for _ in range(poll_interval):
            if shutdown_requested:
                break
            time.sleep(1)

    logger.info("="*60)
    logger.info("AUPAT ArchiveBox Background Worker Stopped")
    logger.info(f"Total Processed: {total_successful} successful, {total_failed} failed")
    logger.info("="*60)


def main():
    """Main entry point for archive worker."""
    parser = argparse.ArgumentParser(
        description="AUPAT ArchiveBox Background Worker - Archives pending URLs"
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to user.json config file (default: ../user/user.json)'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=30,
        help='Polling interval in seconds (default: 30)'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts per URL (default: 3)'
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

        if args.once:
            # Run once and exit (useful for cron)
            logger.info("Running in single-shot mode")
            successful, failed = process_pending_urls(db_path, args.max_retries)
            logger.info(f"Processed: {successful} successful, {failed} failed")
            sys.exit(0 if failed == 0 else 1)
        else:
            # Run as daemon
            run_worker(db_path, args.poll_interval, args.max_retries)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
