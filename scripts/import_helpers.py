#!/usr/bin/env python3
"""
AUPAT Import Helper Functions
Wrapper functions for archive workflow operations.

This module provides helper functions for:
- Database backups before imports
- Batch tracking and logging
- Hardware categorization
- Archive folder management

Version: 0.1.4
Last Updated: 2025-11-18
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from scripts.normalize import normalize_datetime
from scripts.backup import create_backup as _create_backup

logger = logging.getLogger(__name__)


def load_user_config(config_path: str = None) -> dict:
    """Load user configuration from user.json."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"user.json not found at {config_path}. "
            "Create from user/user.json.template"
        )

    with open(config_path, 'r') as f:
        config = json.load(f)

    required = ['db_name', 'db_loc']
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing required keys in user.json: {missing}")

    return config


def create_backup_for_import(config: dict) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Create database backup before import operation.

    This is Step 1 of the 6-step archive workflow from backup.py.

    Args:
        config: User configuration dict with db_name, db_loc, db_backup

    Returns:
        tuple: (success: bool, backup_path: str or None, error: str or None)
    """
    try:
        db_name = config['db_name']
        db_loc = config['db_loc']
        db_backup = config.get('db_backup', str(Path(db_loc).parent / 'backups'))

        logger.info(f"Creating backup before import...")
        backup_path = _create_backup(db_loc, db_backup, db_name)
        logger.info(f"Backup created: {backup_path}")

        return True, backup_path, None

    except Exception as e:
        error_msg = f"Backup failed: {e}"
        logger.error(error_msg)
        return False, None, error_msg


def create_import_batch(
    db_path: str,
    loc_uuid: str,
    source_path: str,
    backup_path: Optional[str] = None
) -> str:
    """
    Create a new import batch record in the database.

    Args:
        db_path: Path to database
        loc_uuid: Location UUID for this import
        source_path: Source directory path
        backup_path: Path to backup file (if backup was created)

    Returns:
        str: Generated batch_id
    """
    batch_id = str(uuid.uuid4())
    timestamp = normalize_datetime(None)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO import_batches (
                batch_id, loc_uuid, source_path, batch_start,
                status, backup_created, backup_path
            ) VALUES (?, ?, ?, ?, 'running', ?, ?)
        """, (
            batch_id,
            loc_uuid,
            source_path,
            timestamp,
            1 if backup_path else 0,
            backup_path
        ))

        conn.commit()
        logger.info(f"Import batch created: {batch_id}")

    finally:
        conn.close()

    return batch_id


def update_import_batch(
    db_path: str,
    batch_id: str,
    **kwargs
) -> None:
    """
    Update import batch record with progress/stats.

    Args:
        db_path: Path to database
        batch_id: Batch ID to update
        **kwargs: Fields to update (status, total_files, files_imported, etc.)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Build UPDATE query dynamically
        fields = []
        values = []

        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        # Add batch_id for WHERE clause
        values.append(batch_id)

        query = f"""
            UPDATE import_batches
            SET {', '.join(fields)}
            WHERE batch_id = ?
        """

        cursor.execute(query, values)
        conn.commit()

    finally:
        conn.close()


def complete_import_batch(
    db_path: str,
    batch_id: str,
    status: str = 'completed',
    error_log: Optional[str] = None
) -> None:
    """
    Mark import batch as complete.

    Args:
        db_path: Path to database
        batch_id: Batch ID to complete
        status: Final status ('completed', 'failed', 'partial')
        error_log: Error log text if any errors occurred
    """
    timestamp = normalize_datetime(None)

    update_import_batch(
        db_path,
        batch_id,
        batch_end=timestamp,
        status=status,
        error_log=error_log
    )

    logger.info(f"Import batch {batch_id} completed with status: {status}")


def log_file_import(
    db_path: str,
    batch_id: str,
    file_path: str,
    file_sha256: str,
    stage: str,
    status: str,
    **kwargs
) -> str:
    """
    Log individual file import to import_log table.

    Args:
        db_path: Path to database
        batch_id: Batch ID this file belongs to
        file_path: Source file path
        file_sha256: SHA256 hash of file
        stage: Import stage (staging/organize/folder/ingest/verify)
        status: Status (success/failed/skipped/duplicate)
        **kwargs: Additional fields (media_type, img_uuid, hardware_category, etc.)

    Returns:
        str: Generated log_id
    """
    log_id = str(uuid.uuid4())
    timestamp = normalize_datetime(None)
    file_name = Path(file_path).name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO import_log (
                log_id, batch_id, file_path, file_name, file_sha256,
                timestamp, stage, status,
                file_size_bytes, media_type, img_uuid, vid_uuid,
                hardware_category, staging_path, archive_path, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id,
            batch_id,
            file_path,
            file_name,
            file_sha256,
            timestamp,
            stage,
            status,
            kwargs.get('file_size_bytes'),
            kwargs.get('media_type'),
            kwargs.get('img_uuid'),
            kwargs.get('vid_uuid'),
            kwargs.get('hardware_category'),
            kwargs.get('staging_path'),
            kwargs.get('archive_path'),
            kwargs.get('error_message')
        ))

        conn.commit()

    finally:
        conn.close()

    return log_id


def get_import_batch_status(db_path: str, batch_id: str) -> Optional[Dict[str, Any]]:
    """
    Get import batch status and statistics.

    Args:
        db_path: Path to database
        batch_id: Batch ID to query

    Returns:
        dict: Batch status dict or None if not found
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM import_batches WHERE batch_id = ?
        """, (batch_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return dict(row)

    finally:
        conn.close()


def get_import_log_for_batch(
    db_path: str,
    batch_id: str,
    stage: Optional[str] = None,
    status: Optional[str] = None
) -> list:
    """
    Get import log entries for a batch.

    Args:
        db_path: Path to database
        batch_id: Batch ID to query
        stage: Optional stage filter
        status: Optional status filter

    Returns:
        list: List of log entry dicts
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        query = "SELECT * FROM import_log WHERE batch_id = ?"
        params = [batch_id]

        if stage:
            query += " AND stage = ?"
            params.append(stage)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY timestamp"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()
