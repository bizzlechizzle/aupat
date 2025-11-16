#!/usr/bin/env python3
"""
AUPAT Web Interface
Professional web application matching Abandoned Upstate design system.

Design System:
- Light: Cream (#fffbf7) background, dark gray (#454545) text
- Dark: Dark gray (#474747) background, cream (#fffbf7) text
- Accent: Warm brown (#b9975c)
- Typography: Roboto Mono (headings), Lora (body)

Features:
- Dashboard with statistics
- Locations browser
- Archive manager
- Import interface
- Real-time progress tracking

Version: 3.0.0
Last Updated: 2025-11-16
"""

import json
import logging
import os
import platform
import sqlite3
import subprocess
import sys
import threading
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import (
    Flask,
    render_template_string,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    session
)

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from utils import generate_uuid
from normalize import (
    normalize_location_name,
    normalize_state_code,
    normalize_location_type,
    normalize_sub_type,
    normalize_author
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global state for background tasks (thread-safe)
WORKFLOW_STATUS = {}
WORKFLOW_LOCK = threading.Lock()


def load_config(config_path: str = 'user/user.json') -> dict:
    """Load user configuration."""
    try:
        # Check if config file exists
        if not Path(config_path).exists():
            logger.error(f"Configuration file not found: {config_path}")
            logger.error("Please run setup.sh to create user.json with correct paths")
            return {}

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Check if db_loc is a directory (common misconfiguration)
        config_modified = False
        if 'db_loc' in config:
            db_path = Path(config['db_loc'])
            if db_path.exists() and db_path.is_dir():
                logger.error(f"ERROR: db_loc is a directory, not a file: {config['db_loc']}")
                logger.error(f"Change db_loc to: {config['db_loc']}/aupat.db")
                config['db_loc'] = str(db_path / 'aupat.db')  # Auto-fix
                logger.info(f"Auto-corrected db_loc to: {config['db_loc']}")
                config_modified = True

        # Save corrected config back to file so scripts use correct path
        if config_modified:
            try:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                logger.info(f"Saved auto-corrected configuration to {config_path}")
            except Exception as save_error:
                logger.warning(f"Failed to save corrected config: {save_error}")

        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def get_disk_space(path: str) -> dict:
    """Get disk space information for a given path."""
    import shutil
    try:
        stat = shutil.disk_usage(path)
        return {
            'total': stat.total,
            'used': stat.used,
            'free': stat.free,
            'percent': (stat.used / stat.total * 100) if stat.total > 0 else 0
        }
    except Exception as e:
        logger.error(f"Failed to get disk space for {path}: {e}")
        return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}


def check_disk_space(path: str, required_gb: float = 1.0) -> tuple[bool, str]:
    """Check if enough disk space is available."""
    stats = get_disk_space(path)
    free_gb = stats['free'] / (1024**3)

    if free_gb < required_gb:
        return False, f"Insufficient disk space: {free_gb:.2f}GB free, {required_gb}GB required"

    return True, f"Disk space OK: {free_gb:.2f}GB free"


def check_path_writable(path: str) -> tuple[bool, str]:
    """Check if a path is writable by attempting to create a test file."""
    test_path = Path(path)

    # If it's a file path, check parent directory
    if not test_path.exists() or test_path.is_file():
        test_dir = test_path.parent
    else:
        test_dir = test_path

    # Try to create directory if it doesn't exist
    try:
        test_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return False, f"Cannot create directory {test_dir}: {e}"

    # Try to write a test file
    test_file = test_dir / f'.aupat_write_test_{os.getpid()}'
    try:
        test_file.write_text('test')
        test_file.unlink()
        return True, f"Path is writable: {test_dir}"
    except Exception as e:
        return False, f"Path not writable {test_dir}: {e}"


def cleanup_orphaned_temp_dirs(max_age_hours: int = 24) -> int:
    """Clean up orphaned AUPAT temp directories older than max_age_hours."""
    import tempfile
    import shutil

    cleaned = 0
    temp_root = Path(tempfile.gettempdir())
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    try:
        # Find all aupat_import_* directories
        for temp_dir in temp_root.glob('aupat_import_*'):
            if not temp_dir.is_dir():
                continue

            # Check age
            try:
                dir_age = current_time - temp_dir.stat().st_mtime
                if dir_age > max_age_seconds:
                    logger.info(f"Cleaning up orphaned temp dir: {temp_dir} (age: {dir_age/3600:.1f}h)")
                    shutil.rmtree(temp_dir)
                    cleaned += 1
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_dir}: {e}")

    except Exception as e:
        logger.error(f"Failed to cleanup orphaned temp dirs: {e}")

    return cleaned


def check_database_schema(db_path: str) -> tuple[bool, list[str]]:
    """Verify that required database tables exist."""
    required_tables = ['locations', 'images', 'videos', 'documents', 'versions']

    if not Path(db_path).exists():
        return False, required_tables  # All tables missing

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        conn.close()

        # Check which tables are missing
        missing = [t for t in required_tables if t not in existing_tables]

        return len(missing) == 0, missing

    except Exception as e:
        logger.error(f"Failed to check database schema: {e}")
        return False, required_tables


def validate_config(config: dict) -> tuple[bool, list[str]]:
    """
    Validate configuration is complete and ready for use.
    Returns (is_valid, list_of_issues).
    """
    issues = []

    if not config:
        issues.append('Configuration file not found or invalid')
        return False, issues

    # Check required keys exist
    required_keys = ['db_name', 'db_loc', 'db_backup', 'db_ingest', 'arch_loc']
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        issues.append(f'Missing required configuration keys: {", ".join(missing_keys)}')

    # Check for placeholder paths
    placeholder_keys = []
    for key in required_keys:
        if key in config and config[key].startswith('/absolute/path'):
            placeholder_keys.append(key)
    if placeholder_keys:
        issues.append(f'Configuration has placeholder paths that need to be updated: {", ".join(placeholder_keys)}')

    # Check database location
    if 'db_loc' in config:
        db_path = Path(config['db_loc'])
        if not db_path.exists():
            # Database doesn't exist - check if parent directory exists and is writable
            if not db_path.parent.exists():
                issues.append(f'Database directory does not exist: {db_path.parent}')
            elif not os.access(db_path.parent, os.W_OK):
                issues.append(f'Database directory is not writable: {db_path.parent}')
        elif not os.access(db_path, os.R_OK):
            issues.append(f'Database file is not readable: {db_path}')

    # Check backup directory
    if 'db_backup' in config:
        backup_path = Path(config['db_backup'])
        if not backup_path.exists():
            issues.append(f'Backup directory does not exist: {backup_path}')
        elif not os.access(backup_path, os.W_OK):
            issues.append(f'Backup directory is not writable: {backup_path}')

    # Check ingest directory
    if 'db_ingest' in config:
        ingest_path = Path(config['db_ingest'])
        if not ingest_path.exists():
            issues.append(f'Ingest directory does not exist: {ingest_path}')
        elif not os.access(ingest_path, os.W_OK):
            issues.append(f'Ingest directory is not writable: {ingest_path}')

    # Check archive directory
    if 'arch_loc' in config:
        arch_path = Path(config['arch_loc'])
        if not arch_path.exists():
            issues.append(f'Archive directory does not exist: {arch_path}')
        elif not os.access(arch_path, os.W_OK):
            issues.append(f'Archive directory is not writable: {arch_path}')

    return len(issues) == 0, issues


def get_db_connection(config: dict):
    """Get database connection."""
    db_path = config.get('db_loc', 'aupat.db')
    if not Path(db_path).exists():
        return None
    return sqlite3.connect(db_path)


def get_dashboard_stats(config: dict) -> Dict:
    """Get dashboard statistics."""
    stats = {
        'locations': 0,
        'sub_locations': 0,
        'images': 0,
        'videos': 0,
        'documents': 0,
        'total_files': 0,
        'recent_imports': [],
        'storage_used': '0 GB'
    }

    try:
        conn = get_db_connection(config)
        if not conn:
            return stats

        cursor = conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM locations")
        stats['locations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sub_locations")
        stats['sub_locations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM images")
        stats['images'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM videos")
        stats['videos'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM documents")
        stats['documents'] = cursor.fetchone()[0]

        stats['total_files'] = stats['images'] + stats['videos'] + stats['documents']

        # Get recent imports
        cursor.execute("""
            SELECT loc_name, state, type, loc_add
            FROM locations
            ORDER BY loc_add DESC
            LIMIT 5
        """)
        stats['recent_imports'] = [
            {'name': row[0], 'state': row[1], 'type': row[2], 'date': row[3]}
            for row in cursor.fetchall()
        ]

        conn.close()

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")

    return stats


def get_locations_list(config: dict, page: int = 1, per_page: int = 20) -> tuple:
    """Get paginated locations list."""
    locations = []
    total = 0

    try:
        conn = get_db_connection(config)
        if not conn:
            return locations, total

        cursor = conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM locations")
        total = cursor.fetchone()[0]

        # Get page of locations
        offset = (page - 1) * per_page
        cursor.execute("""
            SELECT
                loc_uuid,
                loc_name,
                aka_name,
                state,
                type,
                sub_type,
                loc_add,
                (SELECT COUNT(*) FROM images WHERE loc_uuid = locations.loc_uuid) as img_count,
                (SELECT COUNT(*) FROM videos WHERE loc_uuid = locations.loc_uuid) as vid_count
            FROM locations
            ORDER BY loc_add DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))

        locations = [
            {
                'uuid': row[0],
                'uuid8': row[0][:8],
                'name': row[1],
                'aka_name': row[2],
                'state': row[3],
                'type': row[4],
                'sub_type': row[5],
                'added': row[6],
                'images': row[7],
                'videos': row[8]
            }
            for row in cursor.fetchall()
        ]

        conn.close()

    except Exception as e:
        logger.error(f"Failed to get locations: {e}")

    return locations, total


def get_location_details(config: dict, loc_uuid: str) -> Optional[dict]:
    """Get detailed information about a specific location including all associated files."""
    try:
        conn = get_db_connection(config)
        if not conn:
            return None

        cursor = conn.cursor()

        # Get location basic info
        cursor.execute("""
            SELECT
                loc_uuid,
                loc_name,
                aka_name,
                state,
                type,
                sub_type,
                loc_loc,
                org_loc,
                loc_add,
                loc_update,
                imp_author
            FROM locations
            WHERE loc_uuid = ? OR loc_uuid LIKE ?
        """, (loc_uuid, f"{loc_uuid}%"))

        location_row = cursor.fetchone()
        if not location_row:
            return None

        location = {
            'uuid': location_row[0],
            'uuid8': location_row[0][:8],
            'name': location_row[1],
            'aka_name': location_row[2],
            'state': location_row[3],
            'type': location_row[4],
            'sub_type': location_row[5],
            'location_path': location_row[6],
            'original_path': location_row[7],
            'date_added': location_row[8],
            'date_updated': location_row[9],
            'author': location_row[10]
        }

        # Get images
        cursor.execute("""
            SELECT
                img_sha256,
                img_name,
                img_loc,
                camera,
                phone,
                drone,
                go_pro,
                film,
                img_add
            FROM images
            WHERE loc_uuid = ?
            ORDER BY img_add DESC
        """, (location['uuid'],))

        location['images'] = [
            {
                'sha256': row[0],
                'sha8': row[0][:8],
                'name': row[1],
                'path': row[2],
                'camera': bool(row[3]),
                'phone': bool(row[4]),
                'drone': bool(row[5]),
                'go_pro': bool(row[6]),
                'film': bool(row[7]),
                'date_added': row[8]
            }
            for row in cursor.fetchall()
        ]

        # Get videos
        cursor.execute("""
            SELECT
                vid_sha256,
                vid_name,
                vid_loc,
                camera,
                phone,
                drone,
                go_pro,
                dash_cam,
                vid_add
            FROM videos
            WHERE loc_uuid = ?
            ORDER BY vid_add DESC
        """, (location['uuid'],))

        location['videos'] = [
            {
                'sha256': row[0],
                'sha8': row[0][:8],
                'name': row[1],
                'path': row[2],
                'camera': bool(row[3]),
                'phone': bool(row[4]),
                'drone': bool(row[5]),
                'go_pro': bool(row[6]),
                'dash_cam': bool(row[7]),
                'date_added': row[8]
            }
            for row in cursor.fetchall()
        ]

        # Get documents
        cursor.execute("""
            SELECT
                doc_sha256,
                doc_name,
                doc_loc,
                doc_ext,
                doc_add
            FROM documents
            WHERE loc_uuid = ?
            ORDER BY doc_add DESC
        """, (location['uuid'],))

        location['documents'] = [
            {
                'sha256': row[0],
                'sha8': row[0][:8],
                'name': row[1],
                'path': row[2],
                'extension': row[3],
                'date_added': row[4]
            }
            for row in cursor.fetchall()
        ]

        # Get sub-locations
        cursor.execute("""
            SELECT
                sub_uuid,
                sub_name
            FROM sub_locations
            WHERE loc_uuid = ?
        """, (location['uuid'],))

        location['sub_locations'] = [
            {'uuid': row[0], 'uuid8': row[0][:8], 'name': row[1]}
            for row in cursor.fetchall()
        ]

        # Calculate totals
        location['total_images'] = len(location['images'])
        location['total_videos'] = len(location['videos'])
        location['total_documents'] = len(location['documents'])
        location['total_files'] = location['total_images'] + location['total_videos'] + location['total_documents']

        conn.close()
        return location

    except Exception as e:
        logger.error(f"Failed to get location details: {e}")
        return None


# Base HTML template with Abandoned Upstate design
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AUPAT{% endblock %} - Archive Manager</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&family=Lora:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root, html[data-theme="light"] {
            --background: #fffbf7;
            --foreground: #454545;
            --accent: #b9975c;
            --muted: #e6e6e6;
            --border: #b9975c;
            --header-bg: #45372b;
            --header-fg: #fbfbfb;
        }

        html[data-theme="dark"] {
            --background: #474747;
            --foreground: #fffbf7;
            --accent: #b9975c;
            --muted: #343f60;
            --border: #b9975c;
            --header-bg: #45372b;
            --header-fg: #fbfbfb;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Lora', Georgia, serif;
            font-size: clamp(1rem, 0.95rem + 0.4vw, 1.125rem);
            line-height: 1.65;
            background: var(--background);
            color: var(--foreground);
            transition: background 0.3s, color 0.3s;
        }

        h1, h2, h3 {
            font-family: 'Roboto Mono', monospace;
            font-weight: 700;
            line-height: 1.1;
            letter-spacing: 0.05em;
            margin: 0 0 0.5em;
        }

        h1 {
            font-size: clamp(2.25rem, 1.6rem + 3.5vw, 3.5rem);
            text-transform: uppercase;
        }

        h2 {
            font-size: clamp(1.6rem, 1.3rem + 2vw, 2.25rem);
        }

        h3 {
            font-size: clamp(1.25rem, 1.1rem + 1.2vw, 1.6rem);
        }

        .header {
            background: var(--header-bg);
            color: var(--header-fg);
            padding: 1.5rem 2rem;
            border-bottom: 3px solid var(--accent);
        }

        .header-content {
            max-width: 64rem;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .site-title {
            font-size: 1.5rem;
            font-family: 'Roboto Mono', monospace;
            letter-spacing: 0.1em;
            margin: 0;
        }

        .nav {
            display: flex;
            gap: 2rem;
            align-items: center;
        }

        .nav a {
            color: var(--header-fg);
            text-decoration: none;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 0.5rem 0;
            border-bottom: 2px solid transparent;
            transition: border-color 0.2s;
        }

        .nav a:hover,
        .nav a.active {
            border-bottom-color: var(--accent);
        }

        /* File explorer modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            background: var(--background);
            border: 2px solid var(--accent);
            border-radius: 8px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
        }

        .modal-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h3 {
            margin: 0;
        }

        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--foreground);
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-body {
            padding: 1.5rem;
            overflow-y: auto;
            flex: 1;
        }

        .modal-footer {
            padding: 1.5rem;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: flex-end;
            gap: 1rem;
        }

        .file-explorer {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .current-path {
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            padding: 0.75rem;
            background: var(--muted);
            border-radius: 4px;
            word-break: break-all;
        }

        .directory-list {
            list-style: none;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid var(--border);
            border-radius: 4px;
        }

        .directory-item {
            padding: 0.75rem 1rem;
            cursor: pointer;
            border-bottom: 1px solid var(--muted);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            transition: background 0.2s;
        }

        .directory-item:last-child {
            border-bottom: none;
        }

        .directory-item:hover {
            background: rgba(185, 151, 92, 0.1);
        }

        .directory-item.parent {
            color: var(--accent);
            font-weight: 600;
        }

        .directory-icon {
            font-size: 1.2rem;
        }

        .input-with-browse {
            display: flex;
            gap: 0.5rem;
            align-items: stretch;
        }

        .input-with-browse input {
            flex: 1;
        }

        .btn-browse {
            padding: 0.75rem 1rem;
            white-space: nowrap;
        }

        .settings-info {
            background: rgba(185, 151, 92, 0.1);
            border: 1px solid var(--accent);
            border-radius: 4px;
            padding: 1rem;
            margin-bottom: 1.5rem;
        }

        .settings-info p {
            margin: 0;
            font-size: 0.9rem;
        }

        .theme-toggle {
            background: none;
            border: 2px solid var(--header-fg);
            color: var(--header-fg);
            width: 36px;
            height: 36px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .theme-toggle:hover {
            background: var(--accent);
            border-color: var(--accent);
        }

        .container {
            max-width: 64rem;
            margin: 0 auto;
            padding: 2rem;
        }

        .card {
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.2s;
        }

        .card:hover {
            border-color: var(--accent);
            box-shadow: 0 4px 12px rgba(185, 151, 92, 0.15);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--background);
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        }

        .stat-number {
            font-family: 'Roboto Mono', monospace;
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 0.5rem;
        }

        .stat-label {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--foreground);
            opacity: 0.8;
        }

        .btn {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: var(--accent);
            color: var(--background);
            text-decoration: none;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn:hover {
            background: var(--foreground);
            color: var(--background);
        }

        .btn-secondary {
            background: var(--muted);
            color: var(--foreground);
        }

        .btn-secondary:hover {
            background: var(--border);
        }

        .location-list {
            list-style: none;
        }

        .location-item {
            border-bottom: 1px solid var(--muted);
            padding: 1rem 0;
        }

        .location-item:last-child {
            border-bottom: none;
        }

        .location-name {
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 0.25rem;
        }

        .location-meta {
            font-size: 0.85rem;
            color: var(--foreground);
            opacity: 0.7;
            font-family: 'Roboto Mono', monospace;
        }

        .location-name:hover {
            opacity: 0.8;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            background: rgba(185, 151, 92, 0.2);
            color: var(--accent);
            border-radius: 3px;
            font-size: 0.8rem;
            font-family: 'Roboto Mono', monospace;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .flash {
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            background: rgba(185, 151, 92, 0.1);
            border: 1px solid var(--accent);
        }

        .flash.error {
            background: rgba(220, 53, 69, 0.1);
            border-color: #dc3545;
            color: #dc3545;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .form-group input,
        .form-group select {
            width: 100%;
            padding: 0.75rem;
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--foreground);
            font-family: 'Lora', Georgia, serif;
            font-size: 1rem;
        }

        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(185, 151, 92, 0.1);
        }

        .help-text {
            font-size: 0.85rem;
            margin-top: 0.25rem;
            opacity: 0.7;
        }

        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                gap: 1rem;
            }

            .nav {
                flex-wrap: wrap;
                justify-content: center;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    <script>
        // Theme toggle functionality
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        }

        function updateThemeIcon(theme) {
            const icon = document.querySelector('.theme-toggle');
            if (icon) {
                icon.textContent = theme === 'dark' ? '☀' : '☾';
            }
        }

        // Load saved theme on page load
        document.addEventListener('DOMContentLoaded', () => {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeIcon(savedTheme);
        });

        // File explorer functionality
        let currentPath = '/';
        let currentInputField = null;
        let defaultPath = null;

        async function openFileExplorer(inputId) {
            currentInputField = inputId;
            const input = document.getElementById(inputId);

            // Get default path from server if not already loaded
            if (!defaultPath) {
                try {
                    const response = await fetch('/api/default-path');
                    const data = await response.json();
                    defaultPath = data.path;
                } catch (error) {
                    defaultPath = '/home';
                }
            }

            // Use current value if it looks like a valid path, otherwise use default
            let startPath = defaultPath;
            if (input.value && input.value.length > 0 && !input.value.includes('/absolute')) {
                // Check if it's a valid-looking path (Unix or Windows)
                if (input.value.startsWith('/') || /^[A-Za-z]:[\\\\/]/.test(input.value)) {
                    startPath = input.value;
                }
            }
            currentPath = startPath;

            const modal = document.getElementById('fileExplorerModal');
            modal.classList.add('active');

            loadDirectory(currentPath);
        }

        function closeFileExplorer() {
            const modal = document.getElementById('fileExplorerModal');
            modal.classList.remove('active');
            currentInputField = null;
        }

        function selectDirectory() {
            if (currentInputField && currentPath) {
                const input = document.getElementById(currentInputField);
                input.value = currentPath;
            }
            closeFileExplorer();
        }

        async function loadDirectory(path) {
            try {
                const response = await fetch('/api/browse?path=' + encodeURIComponent(path));
                const data = await response.json();

                if (data.error) {
                    // If access denied, try to fall back to default directory
                    if (response.status === 403 && defaultPath && path !== defaultPath) {
                        loadDirectory(defaultPath);
                        return;
                    }

                    const list = document.getElementById('directoryList');
                    list.innerHTML = '<li class="directory-item" style="color: #dc3545; opacity: 0.8;">' +
                                   '⚠️ ' + data.error + '</li>';
                    return;
                }

                currentPath = data.current_path;
                displayDirectory(data);
            } catch (error) {
                const list = document.getElementById('directoryList');
                list.innerHTML = '<li class="directory-item" style="color: #dc3545; opacity: 0.8;">' +
                               '⚠️ Failed to load directory</li>';
            }
        }

        function displayDirectory(data) {
            document.getElementById('currentPath').textContent = data.current_path;

            const list = document.getElementById('directoryList');
            list.innerHTML = '';

            // Add parent directory link if not at root
            if (data.parent_path) {
                const li = document.createElement('li');
                li.className = 'directory-item parent';
                li.innerHTML = '<span class="directory-icon">⬆️</span> ..';
                li.onclick = () => loadDirectory(data.parent_path);
                list.appendChild(li);
            }

            // Add directories
            data.directories.forEach(dir => {
                const li = document.createElement('li');
                li.className = 'directory-item';
                li.innerHTML = '<span class="directory-icon">📁</span> ' + dir.name;
                li.onclick = () => loadDirectory(dir.path);
                list.appendChild(li);
            });

            // Show message if no directories
            if (data.directories.length === 0 && !data.parent_path) {
                const li = document.createElement('li');
                li.className = 'directory-item';
                li.style.opacity = '0.6';
                li.style.cursor = 'default';
                li.textContent = 'No subdirectories';
                list.appendChild(li);
            }
        }

        // Close modal when clicking outside
        document.addEventListener('DOMContentLoaded', () => {
            const modal = document.getElementById('fileExplorerModal');
            if (modal) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        closeFileExplorer();
                    }
                });
            }
        });
    </script>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <h1 class="site-title"><a href="/" style="text-decoration: none; color: inherit;">Abandoned Upstate</a></h1>
            <nav class="nav">
                <a href="/import" class="{{ 'active' if request.path == '/import' else '' }}">Import</a>
                <a href="/" class="{{ 'active' if request.path == '/' else '' }}">Dashboard</a>
                <a href="/locations" class="{{ 'active' if request.path == '/locations' else '' }}">Locations</a>
                <a href="/archives" class="{{ 'active' if request.path == '/archives' else '' }}">Archives</a>
                <a href="/settings" class="{{ 'active' if request.path == '/settings' else '' }}">Settings</a>
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">☾</button>
            </nav>
        </div>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <footer style="text-align: center; padding: 2rem; opacity: 0.6; font-size: 0.9rem;">
        <p>&copy; 2025 Bryant Neal</p>
    </footer>
</body>
</html>
"""

# Dashboard page
DASHBOARD_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<h2>Archive Dashboard</h2>
<p style="margin-bottom: 2rem; opacity: 0.8;">Overview of your media archive and recent activity</p>

<!-- Active Imports Section -->
<div id="active-imports-section" style="display: none; margin-bottom: 2rem;">
    <div class="card" style="border-color: var(--accent); background: rgba(185, 151, 92, 0.05);">
        <h3 style="margin-bottom: 1.5rem;">Active Imports</h3>
        <div id="active-imports-container"></div>
    </div>
</div>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-number">{{ stats.locations }}</div>
        <div class="stat-label">Locations</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ stats.images }}</div>
        <div class="stat-label">Images</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ stats.videos }}</div>
        <div class="stat-label">Videos</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ stats.total_files }}</div>
        <div class="stat-label">Total Files</div>
    </div>
</div>

<div class="card">
    <h3>Recent Imports</h3>
    {% if stats.recent_imports %}
        <ul class="location-list">
            {% for location in stats.recent_imports %}
                <li class="location-item">
                    <a href="/location/{{ location.uuid8 }}" style="text-decoration: none; color: inherit;">
                        <div class="location-name" style="color: var(--accent); transition: opacity 0.2s;">{{ location.name }}</div>
                    </a>
                    <div class="location-meta">
                        {{ location.state | upper }} · {{ location.type | title }} · {{ location.date[:10] }}
                    </div>
                </li>
            {% endfor %}
        </ul>
    {% else %}
        <p style="opacity: 0.6;">No locations imported yet. <a href="/import" style="color: var(--accent);">Start importing</a></p>
    {% endif %}
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 2rem;">
    <div class="card">
        <h3>Quick Actions</h3>
        <p style="margin-bottom: 1rem;">Import new media or manage existing locations</p>
        <a href="/import" class="btn">Import Media</a>
    </div>
    <div class="card">
        <h3>System Status</h3>
        <p style="margin-bottom: 1rem;">
            {% if stats.locations > 0 %}
                <span style="color: var(--accent);">✓</span> Database initialized<br>
                <span style="color: var(--accent);">✓</span> {{ stats.total_files }} files archived
            {% else %}
                <span style="opacity: 0.6;">No data yet - import your first location to get started</span>
            {% endif %}
        </p>
    </div>
</div>

<script>
// Poll for active imports
let pollInterval = null;
let lastTaskCount = 0;

function updateActiveImports() {
    fetch('/api/task-status')
        .then(response => response.json())
        .then(tasks => {
            const container = document.getElementById('active-imports-container');
            const section = document.getElementById('active-imports-section');

            const taskIds = Object.keys(tasks);

            if (taskIds.length === 0) {
                section.style.display = 'none';

                // If we had tasks before and now we don't, refresh the page to show new data
                if (lastTaskCount > 0) {
                    console.log('Import completed - refreshing page...');
                    setTimeout(() => window.location.reload(), 1000);
                }
                lastTaskCount = 0;
                return;
            }

            lastTaskCount = taskIds.length;
            section.style.display = 'block';
            container.innerHTML = '';

            taskIds.forEach(taskId => {
                const task = tasks[taskId];
                const taskDiv = document.createElement('div');
                taskDiv.style.marginBottom = '1.5rem';
                taskDiv.style.paddingBottom = '1.5rem';
                taskDiv.style.borderBottom = '1px solid var(--muted)';

                // Task header
                const header = document.createElement('div');
                header.style.marginBottom = '0.75rem';
                header.style.display = 'flex';
                header.style.justifyContent = 'space-between';
                header.style.alignItems = 'center';

                const locationName = document.createElement('div');
                locationName.style.fontWeight = '600';
                locationName.style.fontSize = '1.1rem';
                locationName.textContent = task.location_name;

                const status = document.createElement('div');
                status.style.fontSize = '0.9rem';
                status.style.fontFamily = "'Roboto Mono', monospace";
                status.style.opacity = '0.8';

                if (task.error) {
                    status.textContent = 'Failed';
                    status.style.color = '#dc3545';
                } else if (task.completed) {
                    status.textContent = 'Completed';
                    status.style.color = 'var(--accent)';
                } else if (task.running) {
                    status.textContent = 'Running...';
                    status.style.color = 'var(--accent)';
                } else {
                    status.textContent = 'Stopped';
                }

                header.appendChild(locationName);
                header.appendChild(status);
                taskDiv.appendChild(header);

                // Current step
                const stepDiv = document.createElement('div');
                stepDiv.style.fontSize = '0.9rem';
                stepDiv.style.marginBottom = '0.75rem';
                stepDiv.style.opacity = '0.8';
                stepDiv.textContent = task.current_step;
                taskDiv.appendChild(stepDiv);

                // Progress bar
                const progressContainer = document.createElement('div');
                progressContainer.style.background = 'var(--muted)';
                progressContainer.style.borderRadius = '8px';
                progressContainer.style.overflow = 'hidden';
                progressContainer.style.height = '32px';
                progressContainer.style.position = 'relative';
                progressContainer.style.marginBottom = '0.5rem';

                const progressBar = document.createElement('div');
                progressBar.style.background = task.error ? '#dc3545' : 'var(--accent)';
                progressBar.style.height = '100%';
                progressBar.style.width = task.progress + '%';
                progressBar.style.transition = 'width 0.3s ease';
                progressBar.style.display = 'flex';
                progressBar.style.alignItems = 'center';
                progressBar.style.justifyContent = 'center';

                const progressText = document.createElement('span');
                progressText.style.color = 'var(--background)';
                progressText.style.fontFamily = "'Roboto Mono', monospace";
                progressText.style.fontWeight = '700';
                progressText.style.fontSize = '0.9rem';
                progressText.style.position = 'absolute';
                progressText.style.width = '100%';
                progressText.style.textAlign = 'center';
                progressText.textContent = task.progress + '%';

                progressContainer.appendChild(progressBar);
                progressContainer.appendChild(progressText);
                taskDiv.appendChild(progressContainer);

                // Error message
                if (task.error) {
                    const errorDiv = document.createElement('div');
                    errorDiv.style.color = '#dc3545';
                    errorDiv.style.fontSize = '0.85rem';
                    errorDiv.style.marginTop = '0.5rem';
                    errorDiv.style.padding = '0.5rem';
                    errorDiv.style.background = 'rgba(220, 53, 69, 0.1)';
                    errorDiv.style.borderRadius = '4px';
                    errorDiv.textContent = task.error;
                    taskDiv.appendChild(errorDiv);
                }

                // Recent logs
                if (task.logs && task.logs.length > 0) {
                    const logsDiv = document.createElement('div');
                    logsDiv.style.marginTop = '0.75rem';
                    logsDiv.style.fontSize = '0.75rem';
                    logsDiv.style.fontFamily = "'Roboto Mono', monospace";
                    logsDiv.style.opacity = '0.6';
                    logsDiv.style.maxHeight = '100px';
                    logsDiv.style.overflow = 'auto';
                    logsDiv.textContent = task.logs.slice(-3).join('\\n');
                    taskDiv.appendChild(logsDiv);
                }

                container.appendChild(taskDiv);
            });
        })
        .catch(error => {
            console.error('Failed to fetch task status:', error);
        });
}

// Start polling when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Check immediately
    updateActiveImports();

    // Then poll every 2 seconds
    pollInterval = setInterval(updateActiveImports, 2000);
});

// Stop polling when page unloads
window.addEventListener('beforeunload', () => {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
});
</script>
{% endblock %}
""")

# Locations page
LOCATIONS_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
    <div>
        <h2>Locations</h2>
        <p style="opacity: 0.8;">{{ total }} locations in archive</p>
    </div>
    <a href="/import" class="btn">Import New</a>
</div>

{% if locations %}
    <div class="card">
        {% for location in locations %}
            <div class="location-item">
                <a href="/location/{{ location.uuid8 }}" style="text-decoration: none; color: inherit;">
                    <div class="location-name" style="color: var(--accent); transition: opacity 0.2s;">{{ location.name }}</div>
                </a>
                {% if location.aka_name %}
                    <div style="font-style: italic; font-size: 0.9rem; margin-bottom: 0.25rem;">
                        AKA: {{ location.aka_name }}
                    </div>
                {% endif %}
                <div class="location-meta">
                    UUID: {{ location.uuid8 }} ·
                    {{ location.state | upper }} ·
                    {{ location.type | title }}{% if location.sub_type %} ({{ location.sub_type | title }}){% endif %} ·
                    {{ location.images }} images ·
                    {{ location.videos }} videos
                </div>
            </div>
        {% endfor %}
    </div>

    {% if total > 20 %}
        <div style="text-align: center; margin-top: 2rem;">
            <p style="opacity: 0.6;">Showing first 20 locations</p>
        </div>
    {% endif %}
{% else %}
    <div class="card">
        <p style="text-align: center; opacity: 0.6;">
            No locations found. <a href="/import" style="color: var(--accent);">Import your first location</a>
        </p>
    </div>
{% endif %}
{% endblock %}
""")

# Location detail page
LOCATION_DETAIL_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div style="margin-bottom: 2rem;">
    <a href="/locations" style="color: var(--accent); text-decoration: none; font-family: 'Roboto Mono', monospace; font-size: 0.9rem;">
        ← Back to Locations
    </a>
</div>

<div style="border-bottom: 2px solid var(--accent); padding-bottom: 1.5rem; margin-bottom: 2rem;">
    <h1 style="margin-bottom: 0.5rem;">{{ location.name }}</h1>
    {% if location.aka_name %}
        <p class="post-tagline" style="margin: 0.5rem 0 1rem;">AKA: {{ location.aka_name }}</p>
    {% endif %}

    <div style="font-family: 'Roboto Mono', monospace; font-size: 0.9rem; opacity: 0.8; margin-top: 1rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div>
                <strong style="color: var(--accent);">UUID:</strong> {{ location.uuid8 }}
            </div>
            <div>
                <strong style="color: var(--accent);">State:</strong> {{ location.state | upper }}
            </div>
            <div>
                <strong style="color: var(--accent);">Type:</strong> {{ location.type | title }}
            </div>
            {% if location.sub_type %}
            <div>
                <strong style="color: var(--accent);">Sub-type:</strong> {{ location.sub_type | title }}
            </div>
            {% endif %}
            <div>
                <strong style="color: var(--accent);">Added:</strong> {{ location.date_added[:10] }}
            </div>
            {% if location.author %}
            <div>
                <strong style="color: var(--accent);">Author:</strong> {{ location.author | title }}
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Statistics Cards -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
    <div class="stat-card">
        <div class="stat-number">{{ location.total_images }}</div>
        <div class="stat-label">Images</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ location.total_videos }}</div>
        <div class="stat-label">Videos</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ location.total_documents }}</div>
        <div class="stat-label">Documents</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ location.total_files }}</div>
        <div class="stat-label">Total Files</div>
    </div>
</div>

<!-- Sub-locations -->
{% if location.sub_locations %}
<div class="card" style="margin-bottom: 2rem;">
    <h3 style="margin-bottom: 1rem; color: var(--accent);">Sub-Locations</h3>
    <div style="display: grid; gap: 0.5rem;">
        {% for sub in location.sub_locations %}
        <div style="padding: 0.75rem; background: rgba(185, 151, 92, 0.1); border-radius: 4px;">
            <strong>{{ sub.name }}</strong> <span style="opacity: 0.6; font-size: 0.9rem;">({{ sub.uuid8 }})</span>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}

<!-- Images -->
{% if location.images %}
<div class="card" style="margin-bottom: 2rem;">
    <h3 style="margin-bottom: 1.5rem; color: var(--accent);">
        Images <span style="opacity: 0.6; font-size: 0.9rem; font-weight: normal;">({{ location.total_images }})</span>
    </h3>
    <div style="max-height: 400px; overflow-y: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
            <thead style="position: sticky; top: 0; background: var(--background); border-bottom: 2px solid var(--accent);">
                <tr style="text-align: left; font-family: 'Roboto Mono', monospace;">
                    <th style="padding: 0.75rem;">Filename</th>
                    <th style="padding: 0.75rem;">Type</th>
                    <th style="padding: 0.75rem;">SHA8</th>
                    <th style="padding: 0.75rem;">Date</th>
                </tr>
            </thead>
            <tbody>
                {% for img in location.images %}
                <tr style="border-bottom: 1px solid rgba(185, 151, 92, 0.2);">
                    <td style="padding: 0.75rem; font-family: 'Roboto Mono', monospace; font-size: 0.85rem;">
                        {{ img.name }}
                    </td>
                    <td style="padding: 0.75rem;">
                        {% if img.camera %}
                            <span class="badge">Camera</span>
                        {% elif img.phone %}
                            <span class="badge">Phone</span>
                        {% elif img.drone %}
                            <span class="badge">Drone</span>
                        {% elif img.go_pro %}
                            <span class="badge">GoPro</span>
                        {% elif img.film %}
                            <span class="badge">Film</span>
                        {% else %}
                            <span class="badge">Other</span>
                        {% endif %}
                    </td>
                    <td style="padding: 0.75rem; font-family: 'Roboto Mono', monospace; font-size: 0.85rem; opacity: 0.7;">
                        {{ img.sha8 }}
                    </td>
                    <td style="padding: 0.75rem; font-size: 0.85rem; opacity: 0.7;">
                        {{ img.date_added[:10] }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}

<!-- Videos -->
{% if location.videos %}
<div class="card" style="margin-bottom: 2rem;">
    <h3 style="margin-bottom: 1.5rem; color: var(--accent);">
        Videos <span style="opacity: 0.6; font-size: 0.9rem; font-weight: normal;">({{ location.total_videos }})</span>
    </h3>
    <div style="max-height: 400px; overflow-y: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
            <thead style="position: sticky; top: 0; background: var(--background); border-bottom: 2px solid var(--accent);">
                <tr style="text-align: left; font-family: 'Roboto Mono', monospace;">
                    <th style="padding: 0.75rem;">Filename</th>
                    <th style="padding: 0.75rem;">Type</th>
                    <th style="padding: 0.75rem;">SHA8</th>
                    <th style="padding: 0.75rem;">Date</th>
                </tr>
            </thead>
            <tbody>
                {% for vid in location.videos %}
                <tr style="border-bottom: 1px solid rgba(185, 151, 92, 0.2);">
                    <td style="padding: 0.75rem; font-family: 'Roboto Mono', monospace; font-size: 0.85rem;">
                        {{ vid.name }}
                    </td>
                    <td style="padding: 0.75rem;">
                        {% if vid.camera %}
                            <span class="badge">Camera</span>
                        {% elif vid.phone %}
                            <span class="badge">Phone</span>
                        {% elif vid.drone %}
                            <span class="badge">Drone</span>
                        {% elif vid.go_pro %}
                            <span class="badge">GoPro</span>
                        {% elif vid.dash_cam %}
                            <span class="badge">Dashcam</span>
                        {% else %}
                            <span class="badge">Other</span>
                        {% endif %}
                    </td>
                    <td style="padding: 0.75rem; font-family: 'Roboto Mono', monospace; font-size: 0.85rem; opacity: 0.7;">
                        {{ vid.sha8 }}
                    </td>
                    <td style="padding: 0.75rem; font-size: 0.85rem; opacity: 0.7;">
                        {{ vid.date_added[:10] }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}

<!-- Documents -->
{% if location.documents %}
<div class="card" style="margin-bottom: 2rem;">
    <h3 style="margin-bottom: 1.5rem; color: var(--accent);">
        Documents <span style="opacity: 0.6; font-size: 0.9rem; font-weight: normal;">({{ location.total_documents }})</span>
    </h3>
    <div style="max-height: 400px; overflow-y: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
            <thead style="position: sticky; top: 0; background: var(--background); border-bottom: 2px solid var(--accent);">
                <tr style="text-align: left; font-family: 'Roboto Mono', monospace;">
                    <th style="padding: 0.75rem;">Filename</th>
                    <th style="padding: 0.75rem;">Type</th>
                    <th style="padding: 0.75rem;">SHA8</th>
                    <th style="padding: 0.75rem;">Date</th>
                </tr>
            </thead>
            <tbody>
                {% for doc in location.documents %}
                <tr style="border-bottom: 1px solid rgba(185, 151, 92, 0.2);">
                    <td style="padding: 0.75rem; font-family: 'Roboto Mono', monospace; font-size: 0.85rem;">
                        {{ doc.name }}
                    </td>
                    <td style="padding: 0.75rem;">
                        <span class="badge">{{ doc.extension | upper }}</span>
                    </td>
                    <td style="padding: 0.75rem; font-family: 'Roboto Mono', monospace; font-size: 0.85rem; opacity: 0.7;">
                        {{ doc.sha8 }}
                    </td>
                    <td style="padding: 0.75rem; font-size: 0.85rem; opacity: 0.7;">
                        {{ doc.date_added[:10] }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}

{% if not location.images and not location.videos and not location.documents %}
<div class="card" style="text-align: center; padding: 3rem;">
    <p style="opacity: 0.6; font-size: 1.1rem;">No files found for this location.</p>
</div>
{% endif %}

{% endblock %}
""")

# Import page
IMPORT_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<h2>Import Media</h2>
<p style="margin-bottom: 1rem; opacity: 0.8;">Import a new location and associated media files</p>
<div style="background: rgba(185, 151, 92, 0.1); border-left: 3px solid var(--accent); padding: 1rem; margin-bottom: 2rem; font-size: 0.9rem;">
    <strong>Import Pipeline:</strong> This will run a 5-stage automated process:<br>
    1. Import files to staging<br>
    2. Extract metadata (EXIF, hardware detection)<br>
    3. Create organized folder structure<br>
    4. Move files to archive<br>
    5. Verify integrity and cleanup
</div>

<div class="card">
    <form method="POST" action="/import/submit" enctype="multipart/form-data" id="importForm">
        <div class="form-group">
            <label>Location Name * <span id="collision-warning" style="color: #dc3545; font-size: 0.85rem; display: none;">⚠️ Location already exists</span></label>
            <input type="text" id="loc_name" name="loc_name" required placeholder="Abandoned Factory Building" autocomplete="off">
            <div id="loc_name_suggestions" class="autocomplete-dropdown"></div>
            <div class="help-text">Location name will be checked for duplicates</div>
        </div>

        <div class="form-group">
            <label>Also Known As</label>
            <input type="text" name="aka_name" placeholder="Alternative names">
        </div>

        <div class="form-group">
            <label>Type *</label>
            <input type="text" id="type" name="type" required placeholder="Start typing..." autocomplete="off">
            <div id="type_suggestions" class="autocomplete-dropdown"></div>
            <div class="help-text">Auto-fills based on existing database</div>
        </div>

        <div class="form-group">
            <label>Sub-Type</label>
            <input type="text" id="sub_type" name="sub_type" placeholder="Start typing..." autocomplete="off">
            <div id="sub_type_suggestions" class="autocomplete-dropdown"></div>
            <div class="help-text">Filtered based on selected type</div>
        </div>

        <div class="form-group">
            <label>State *</label>
            <input type="text" id="state" name="state" required maxlength="2" placeholder="NY" style="text-transform: uppercase;" autocomplete="off">
            <div id="state_suggestions" class="autocomplete-dropdown"></div>
            <div class="help-text">Two-letter USPS state code (e.g., NY, PA, VT)</div>
        </div>

        <div class="form-group">
            <label>Author</label>
            <input type="text" id="imp_author" name="imp_author" placeholder="Your name" autocomplete="off">
            <div id="imp_author_suggestions" class="autocomplete-dropdown"></div>
            <div class="help-text">Auto-fills based on existing database</div>
        </div>

        <hr style="border: 1px solid var(--muted); margin: 2rem 0;">

        <h3>Upload Media</h3>
        <p style="margin-bottom: 1.5rem; opacity: 0.7; font-size: 0.9rem;">
            You can use any combination of the upload options below
        </p>

        <div class="form-group">
            <label>Images & Videos</label>
            <input type="file" name="media_files" id="media_files" multiple accept="image/*,video/*">
            <div class="help-text">Select image and video files (JPG, PNG, MP4, etc.)</div>
        </div>

        <div class="form-group">
            <label>Documents</label>
            <input type="file" name="document_files" id="document_files" multiple accept=".pdf,.doc,.docx,.txt,.md">
            <div class="help-text">Select document files (PDF, Word, text, etc.)</div>
        </div>

        <div id="folder-upload-group" class="form-group">
            <label>Upload Folder <span style="font-size: 0.85rem; opacity: 0.6; font-weight: normal;">(preserves subfolder structure)</span></label>
            <input type="file" name="folder_files" id="folder_files" webkitdirectory directory multiple>
            <div class="help-text">Select a folder - all files and subfolders will be imported</div>
            <div id="folder-not-supported-warning" class="help-text" style="color: #dc3545; margin-top: 0.5rem; display: none;">
                <strong>⚠️ Note:</strong> Folder upload is not supported on this browser/device.
                Please use individual file upload or access from a desktop browser (Chrome, Edge, or Safari).
            </div>
        </div>

        <div class="form-group">
            <label>Web URLs</label>
            <textarea name="web_urls" id="web_urls" rows="3" placeholder="One URL per line" style="width: 100%; padding: 0.75rem; border: 1px solid var(--border); border-radius: 4px; background: var(--background); color: var(--foreground); font-family: 'Roboto Mono', monospace; font-size: 0.9rem;"></textarea>
            <div class="help-text">Enter web URLs, one per line</div>
        </div>

        <div class="form-group">
            <label>
                <input type="checkbox" id="is_film" name="is_film" style="width: auto; margin-right: 0.5rem;">
                Film Photography
            </label>
        </div>

        <div class="form-group" id="film_stock_group" style="display: none;">
            <label>Film Stock</label>
            <input type="text" name="film_stock" id="film_stock" placeholder="e.g., Kodak Portra 400">
            <div class="help-text">Film stock used for photography</div>
        </div>

        <div class="form-group" id="film_format_group" style="display: none;">
            <label>Film Format</label>
            <input type="text" name="film_format" id="film_format" placeholder="e.g., 35mm, 120, 4x5">
            <div class="help-text">Film format/size</div>
        </div>

        <div style="display: flex; gap: 1rem; margin-top: 2rem;">
            <button type="submit" class="btn" id="submit-btn">Import Location</button>
            <a href="/" class="btn btn-secondary">Cancel</a>
        </div>
    </form>

    <!-- Upload Progress Bar -->
    <div id="upload-progress" style="display: none; margin-top: 2rem;">
        <h3>Upload Progress</h3>
        <div style="background: var(--muted); border-radius: 8px; overflow: hidden; height: 40px; position: relative; margin-bottom: 1rem;">
            <div id="progress-bar" style="background: var(--accent); height: 100%; width: 0%; transition: width 0.3s ease; display: flex; align-items: center; justify-content: center;">
                <span id="progress-text" style="color: var(--background); font-family: 'Roboto Mono', monospace; font-weight: 700; position: absolute; width: 100%; text-align: center;">0%</span>
            </div>
        </div>
        <div id="progress-status" style="font-family: 'Roboto Mono', monospace; font-size: 0.9rem; opacity: 0.8;">
            Preparing upload...
        </div>
    </div>
</div>

<style>
.autocomplete-dropdown {
    position: absolute;
    background: var(--background);
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 4px 4px;
    max-height: 200px;
    overflow-y: auto;
    z-index: 1000;
    display: none;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.autocomplete-item {
    padding: 0.75rem;
    cursor: pointer;
    font-family: 'Roboto Mono', monospace;
    font-size: 0.9rem;
    border-bottom: 1px solid var(--muted);
}

.autocomplete-item:last-child {
    border-bottom: none;
}

.autocomplete-item:hover {
    background: rgba(185, 151, 92, 0.1);
}

.form-group {
    position: relative;
}
</style>

<script>
// Autocomplete functionality
let debounceTimers = {};

function setupAutocomplete(inputId, endpoint, onSelect = null) {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(inputId + '_suggestions');

    if (!input || !dropdown) return;

    input.addEventListener('input', function() {
        const query = this.value.trim();

        // Clear existing timer
        if (debounceTimers[inputId]) {
            clearTimeout(debounceTimers[inputId]);
        }

        if (query.length === 0) {
            dropdown.style.display = 'none';
            return;
        }

        // Debounce API calls
        debounceTimers[inputId] = setTimeout(async () => {
            try {
                let url = endpoint + '?q=' + encodeURIComponent(query);

                // Add type filter for sub-type autocomplete
                if (inputId === 'sub_type') {
                    const typeInput = document.getElementById('type');
                    if (typeInput && typeInput.value) {
                        url += '&type=' + encodeURIComponent(typeInput.value);
                    }
                }

                const response = await fetch(url);
                const data = await response.json();

                if (data.suggestions && data.suggestions.length > 0) {
                    dropdown.innerHTML = '';
                    data.suggestions.forEach(suggestion => {
                        const item = document.createElement('div');
                        item.className = 'autocomplete-item';
                        item.textContent = suggestion;
                        item.onclick = () => {
                            input.value = suggestion;
                            dropdown.style.display = 'none';
                            if (onSelect) onSelect(suggestion);
                        };
                        dropdown.appendChild(item);
                    });
                    dropdown.style.display = 'block';
                } else {
                    dropdown.style.display = 'none';
                }

                // Set most popular as placeholder on first load
                if (data.most_popular && !input.value) {
                    input.placeholder = data.most_popular;
                }
            } catch (error) {
                console.error('Autocomplete error:', error);
                dropdown.style.display = 'none';
            }
        }, 300);
    });

    // Hide dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target !== input) {
            dropdown.style.display = 'none';
        }
    });

    // Load most popular value on page load
    fetch(endpoint + '?q=')
        .then(r => r.json())
        .then(data => {
            if (data.most_popular) {
                input.placeholder = data.most_popular;
            }
        })
        .catch(e => console.error('Failed to load popular value:', e));
}

// Collision checking for location name
let collisionCheckTimer = null;
document.addEventListener('DOMContentLoaded', function() {
    const locNameInput = document.getElementById('loc_name');
    const collisionWarning = document.getElementById('collision-warning');
    const submitBtn = document.getElementById('submit-btn');

    if (locNameInput && collisionWarning) {
        locNameInput.addEventListener('input', function() {
            const name = this.value.trim();

            if (collisionCheckTimer) {
                clearTimeout(collisionCheckTimer);
            }

            if (name.length === 0) {
                collisionWarning.style.display = 'none';
                submitBtn.disabled = false;
                return;
            }

            collisionCheckTimer = setTimeout(async () => {
                try {
                    const response = await fetch('/api/check-collision?name=' + encodeURIComponent(name));
                    const data = await response.json();

                    if (data.exists) {
                        collisionWarning.style.display = 'inline';
                        submitBtn.disabled = true;
                    } else {
                        collisionWarning.style.display = 'none';
                        submitBtn.disabled = false;
                    }
                } catch (error) {
                    console.error('Collision check error:', error);
                }
            }, 500);
        });
    }

    // Setup all autocomplete fields
    setupAutocomplete('loc_name', '/api/autocomplete/location-names');
    setupAutocomplete('type', '/api/autocomplete/types', function(value) {
        // Reload sub-type suggestions when type changes
        const subTypeInput = document.getElementById('sub_type');
        if (subTypeInput) {
            subTypeInput.value = '';
            subTypeInput.placeholder = 'Loading...';
            fetch('/api/autocomplete/sub-types?q=&type=' + encodeURIComponent(value))
                .then(r => r.json())
                .then(data => {
                    if (data.most_popular) {
                        subTypeInput.placeholder = data.most_popular;
                    }
                })
                .catch(e => console.error('Failed to update sub-type:', e));
        }
    });
    setupAutocomplete('sub_type', '/api/autocomplete/sub-types');
    setupAutocomplete('state', '/api/autocomplete/states');
    setupAutocomplete('imp_author', '/api/autocomplete/authors');

    // Film checkbox toggle
    const isFilmCheckbox = document.getElementById('is_film');
    const filmStockGroup = document.getElementById('film_stock_group');
    const filmFormatGroup = document.getElementById('film_format_group');

    if (isFilmCheckbox) {
        isFilmCheckbox.addEventListener('change', function() {
            if (this.checked) {
                filmStockGroup.style.display = 'block';
                filmFormatGroup.style.display = 'block';
            } else {
                filmStockGroup.style.display = 'none';
                filmFormatGroup.style.display = 'none';
            }
        });
    }
});

// Detect browser support for folder uploads
function checkFolderUploadSupport() {
    const folderGroup = document.getElementById('folder-upload-group');
    const folderInput = document.getElementById('folder_files');
    const warning = document.getElementById('folder-not-supported-warning');

    if (!folderInput || !folderGroup) return;

    // Check if browser supports directory upload
    const supportsDirectoryUpload = 'webkitdirectory' in folderInput || 'directory' in folderInput;

    // Additional check for mobile devices which may not support folder upload even with the attribute
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

    if (!supportsDirectoryUpload || (isMobile && /iPhone|iPad|iPod/.test(navigator.userAgent))) {
        // Hide folder upload section entirely and show warning
        folderGroup.style.display = 'none';
    }
}

// Validate files before submission
function validateFiles() {
    // Collect files from all inputs
    const mediaFiles = document.getElementById('media_files').files;
    const docFiles = document.getElementById('document_files').files;
    const folderFiles = document.getElementById('folder_files').files;

    const allFiles = [...mediaFiles, ...docFiles, ...folderFiles];

    // Check if any files selected
    if (allFiles.length === 0) {
        alert('Please select at least one file or folder to import.');
        return false;
    }

    // Validate file extensions
    const validExtensions = [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif',
        '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v',
        '.pdf', '.doc', '.docx', '.txt', '.md'
    ];

    const invalidFiles = [];
    for (const file of allFiles) {
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!validExtensions.includes(ext)) {
            invalidFiles.push(file.name);
        }
    }

    if (invalidFiles.length > 0) {
        const maxShow = 5;
        const fileList = invalidFiles.slice(0, maxShow).join('\n  • ');
        const more = invalidFiles.length > maxShow ? `\n  ... and ${invalidFiles.length - maxShow} more` : '';

        const proceed = confirm(
            `${invalidFiles.length} file(s) have unsupported extensions and will be skipped:\n\n  • ${fileList}${more}\n\nContinue with import?`
        );

        if (!proceed) {
            return false;
        }
    }

    return true;
}

// Upload with progress tracking
function uploadWithProgress(formData) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Show progress bar
        const progressContainer = document.getElementById('upload-progress');
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const progressStatus = document.getElementById('progress-status');

        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressText.textContent = '0%';

        // Upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percentComplete + '%';
                progressText.textContent = percentComplete + '%';

                const loadedMB = (e.loaded / (1024 * 1024)).toFixed(2);
                const totalMB = (e.total / (1024 * 1024)).toFixed(2);
                progressStatus.textContent = `Uploading files: ${loadedMB} MB / ${totalMB} MB`;
            }
        });

        // Upload complete (server is now processing)
        xhr.upload.addEventListener('load', () => {
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            progressStatus.textContent = 'Upload complete - Processing files on server...';
        });

        // Request complete
        xhr.addEventListener('load', () => {
            if (xhr.status === 200 || xhr.status === 302) {
                progressStatus.textContent = 'Import complete! Redirecting...';
                // Follow redirect
                if (xhr.responseURL) {
                    window.location.href = xhr.responseURL;
                } else {
                    // Parse redirect from response
                    window.location.href = '/locations';
                }
                resolve(xhr);
            } else {
                progressStatus.textContent = 'Import failed - See error below';
                reject(new Error('Upload failed with status: ' + xhr.status));
            }
        });

        // Error handling
        xhr.addEventListener('error', () => {
            progressStatus.textContent = 'Upload failed - Network error';
            reject(new Error('Network error'));
        });

        xhr.addEventListener('abort', () => {
            progressStatus.textContent = 'Upload cancelled';
            reject(new Error('Upload cancelled'));
        });

        // Send request
        xhr.open('POST', '/import/submit');
        xhr.send(formData);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    checkFolderUploadSupport();

    // Add form validation
    const importForm = document.getElementById('importForm');
    if (importForm) {
        importForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Always prevent default, we'll handle upload manually

            if (!validateFiles()) {
                return false;
            }

            // Disable submit button to prevent double submission
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Uploading...';
            }

            // Create FormData from form
            const formData = new FormData(importForm);

            // Upload with progress tracking
            uploadWithProgress(formData)
                .then(() => {
                    // Success - redirect handled in uploadWithProgress
                })
                .catch((error) => {
                    console.error('Upload error:', error);
                    // Re-enable submit button
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Import Location';
                    }
                    alert('Upload failed: ' + error.message + '\n\nPlease try again or check the server logs.');
                });
        });
    }
});
</script>
{% endblock %}
""")

# Settings page
SETTINGS_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<h2>Settings</h2>
<p style="margin-bottom: 2rem; opacity: 0.8;">Configure AUPAT system paths and options</p>

<div class="settings-info">
    <p><strong>Note:</strong> These settings are stored in <code>user/user.json</code>. The system will auto-correct paths if needed.</p>
    <p style="margin-top: 0.5rem; font-size: 0.9rem;">
        <strong>Important:</strong> Database Location must be a FILE path (ending in .db), all others must be DIRECTORY paths (ending in /).
    </p>
</div>

<div class="card">
    <form method="POST" action="/settings/save">
        <div class="form-group">
            <label>Database Name</label>
            <input type="text" name="db_name" id="db_name" value="{{ config.get('db_name', 'aupat.db') }}" required>
            <div class="help-text">Database filename (e.g., aupat.db)</div>
        </div>

        <div class="form-group">
            <label>Database Location <span style="color: var(--accent); font-weight: normal;">(must be a FILE path)</span></label>
            <div class="input-with-browse">
                <input type="text" name="db_loc" id="db_loc" value="{{ config.get('db_loc', '') }}" required placeholder="/absolute/path/to/database/aupat.db">
                <button type="button" class="btn btn-browse" onclick="openFileExplorer('db_loc')">Browse</button>
            </div>
            <div class="help-text">Must end with .db - Example: /path/to/tempdata/database/aupat.db</div>
        </div>

        <div class="form-group">
            <label>Backup Location</label>
            <div class="input-with-browse">
                <input type="text" name="db_backup" id="db_backup" value="{{ config.get('db_backup', '') }}" required placeholder="/absolute/path/to/backups/">
                <button type="button" class="btn btn-browse" onclick="openFileExplorer('db_backup')">Browse</button>
            </div>
            <div class="help-text">Directory for database backups</div>
        </div>

        <div class="form-group">
            <label>Ingest/Staging Location</label>
            <div class="input-with-browse">
                <input type="text" name="db_ingest" id="db_ingest" value="{{ config.get('db_ingest', '') }}" required placeholder="/absolute/path/to/ingest/staging/">
                <button type="button" class="btn btn-browse" onclick="openFileExplorer('db_ingest')">Browse</button>
            </div>
            <div class="help-text">Staging area for incoming files before import</div>
        </div>

        <div class="form-group">
            <label>Archive Location</label>
            <div class="input-with-browse">
                <input type="text" name="arch_loc" id="arch_loc" value="{{ config.get('arch_loc', '') }}" required placeholder="/absolute/path/to/archive/">
                <button type="button" class="btn btn-browse" onclick="openFileExplorer('arch_loc')">Browse</button>
            </div>
            <div class="help-text">Archive root directory for organized media storage</div>
        </div>

        <div style="display: flex; gap: 1rem; margin-top: 2rem;">
            <button type="submit" class="btn">Save Settings</button>
            <a href="/" class="btn btn-secondary">Cancel</a>
        </div>
    </form>
</div>

<!-- File Explorer Modal -->
<div id="fileExplorerModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Select Directory</h3>
            <button class="modal-close" onclick="closeFileExplorer()">&times;</button>
        </div>
        <div class="modal-body">
            <div class="file-explorer">
                <div class="current-path" id="currentPath">/</div>
                <ul class="directory-list" id="directoryList">
                    <li class="directory-item" style="opacity: 0.6;">Loading...</li>
                </ul>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeFileExplorer()">Cancel</button>
            <button class="btn" onclick="selectDirectory()">Select This Directory</button>
        </div>
    </div>
</div>
{% endblock %}
""")


# Routes
@app.route('/')
def dashboard():
    """Dashboard page."""
    config = load_config()

    # Check if config is valid
    if not config:
        flash('Configuration error: user.json not found. Please run setup.sh to initialize the project.', 'error')
    else:
        is_valid, issues = validate_config(config)
        if not is_valid:
            for issue in issues:
                flash(f'Configuration issue: {issue}', 'error')

    stats = get_dashboard_stats(config)
    return render_template_string(DASHBOARD_TEMPLATE, stats=stats)


@app.route('/locations')
def locations():
    """Locations list page."""
    config = load_config()
    page = request.args.get('page', 1, type=int)
    locations_list, total = get_locations_list(config, page=page)
    return render_template_string(LOCATIONS_TEMPLATE, locations=locations_list, total=total)


@app.route('/location/<uuid>')
def location_detail(uuid):
    """Location detail page showing all associated files."""
    config = load_config()
    location = get_location_details(config, uuid)

    if not location:
        flash(f'Location not found: {uuid}', 'error')
        return redirect(url_for('locations'))

    return render_template_string(LOCATION_DETAIL_TEMPLATE, location=location)


@app.route('/archives')
def archives():
    """Archives page (placeholder)."""
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<h2>Archives</h2>
<p>Archive management coming soon...</p>
{% endblock %}
"""))


@app.route('/import')
def import_form():
    """Import form page."""
    config = load_config()
    return render_template_string(IMPORT_TEMPLATE, config=config)


@app.route('/api/autocomplete/location-names')
def api_autocomplete_location_names():
    """Get autocomplete suggestions for location names."""
    try:
        query = request.args.get('q', '').lower()
        config = load_config()
        conn = get_db_connection(config)
        if not conn:
            return jsonify({'suggestions': []})

        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT loc_name, aka_name
            FROM locations
            WHERE LOWER(loc_name) LIKE ? OR LOWER(aka_name) LIKE ?
            ORDER BY loc_add DESC
            LIMIT 10
        """, (f'%{query}%', f'%{query}%'))

        suggestions = list(set([row[0] for row in cursor.fetchall() if row[0]]))
        conn.close()

        return jsonify({'suggestions': suggestions})
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        return jsonify({'suggestions': []})


@app.route('/api/autocomplete/types')
def api_autocomplete_types():
    """Get autocomplete suggestions for location types with most popular first."""
    try:
        query = request.args.get('q', '').lower()
        config = load_config()
        conn = get_db_connection(config)
        if not conn:
            return jsonify({'suggestions': [], 'most_popular': None})

        cursor = conn.cursor()

        # Get most popular type
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM locations
            WHERE type IS NOT NULL AND type != ''
            GROUP BY type
            ORDER BY count DESC
            LIMIT 1
        """)
        most_popular_row = cursor.fetchone()
        most_popular = most_popular_row[0] if most_popular_row else None

        # Get matching types
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM locations
            WHERE LOWER(type) LIKE ? AND type IS NOT NULL AND type != ''
            GROUP BY type
            ORDER BY count DESC
            LIMIT 10
        """, (f'%{query}%',))

        suggestions = [row[0] for row in cursor.fetchall()]
        conn.close()

        return jsonify({'suggestions': suggestions, 'most_popular': most_popular})
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        return jsonify({'suggestions': [], 'most_popular': None})


@app.route('/api/autocomplete/sub-types')
def api_autocomplete_sub_types():
    """Get autocomplete suggestions for sub-types filtered by type."""
    try:
        query = request.args.get('q', '').lower()
        type_filter = request.args.get('type', '')
        config = load_config()
        conn = get_db_connection(config)
        if not conn:
            return jsonify({'suggestions': [], 'most_popular': None})

        cursor = conn.cursor()

        # Get most popular sub-type for this type
        if type_filter:
            cursor.execute("""
                SELECT sub_type, COUNT(*) as count
                FROM locations
                WHERE type = ? AND sub_type IS NOT NULL AND sub_type != ''
                GROUP BY sub_type
                ORDER BY count DESC
                LIMIT 1
            """, (type_filter,))
        else:
            cursor.execute("""
                SELECT sub_type, COUNT(*) as count
                FROM locations
                WHERE sub_type IS NOT NULL AND sub_type != ''
                GROUP BY sub_type
                ORDER BY count DESC
                LIMIT 1
            """)

        most_popular_row = cursor.fetchone()
        most_popular = most_popular_row[0] if most_popular_row else None

        # Get matching sub-types
        if type_filter:
            cursor.execute("""
                SELECT sub_type, COUNT(*) as count
                FROM locations
                WHERE type = ? AND LOWER(sub_type) LIKE ? AND sub_type IS NOT NULL AND sub_type != ''
                GROUP BY sub_type
                ORDER BY count DESC
                LIMIT 10
            """, (type_filter, f'%{query}%'))
        else:
            cursor.execute("""
                SELECT sub_type, COUNT(*) as count
                FROM locations
                WHERE LOWER(sub_type) LIKE ? AND sub_type IS NOT NULL AND sub_type != ''
                GROUP BY sub_type
                ORDER BY count DESC
                LIMIT 10
            """, (f'%{query}%',))

        suggestions = [row[0] for row in cursor.fetchall()]
        conn.close()

        return jsonify({'suggestions': suggestions, 'most_popular': most_popular})
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        return jsonify({'suggestions': [], 'most_popular': None})


@app.route('/api/autocomplete/states')
def api_autocomplete_states():
    """Get autocomplete suggestions for states with most popular first."""
    try:
        query = request.args.get('q', '').upper()
        config = load_config()
        conn = get_db_connection(config)
        if not conn:
            return jsonify({'suggestions': [], 'most_popular': None})

        cursor = conn.cursor()

        # Get most popular state
        cursor.execute("""
            SELECT state, COUNT(*) as count
            FROM locations
            WHERE state IS NOT NULL AND state != ''
            GROUP BY state
            ORDER BY count DESC
            LIMIT 1
        """)
        most_popular_row = cursor.fetchone()
        most_popular = most_popular_row[0] if most_popular_row else None

        # Get matching states
        cursor.execute("""
            SELECT DISTINCT state, COUNT(*) as count
            FROM locations
            WHERE UPPER(state) LIKE ? AND state IS NOT NULL AND state != ''
            GROUP BY state
            ORDER BY count DESC
            LIMIT 10
        """, (f'%{query}%',))

        suggestions = [row[0] for row in cursor.fetchall()]
        conn.close()

        return jsonify({'suggestions': suggestions, 'most_popular': most_popular})
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        return jsonify({'suggestions': [], 'most_popular': None})


@app.route('/api/autocomplete/authors')
def api_autocomplete_authors():
    """Get autocomplete suggestions for authors with most popular first."""
    try:
        query = request.args.get('q', '').lower()
        config = load_config()
        conn = get_db_connection(config)
        if not conn:
            return jsonify({'suggestions': [], 'most_popular': None})

        cursor = conn.cursor()

        # Get most popular author
        cursor.execute("""
            SELECT imp_author, COUNT(*) as count
            FROM locations
            WHERE imp_author IS NOT NULL AND imp_author != ''
            GROUP BY imp_author
            ORDER BY count DESC
            LIMIT 1
        """)
        most_popular_row = cursor.fetchone()
        most_popular = most_popular_row[0] if most_popular_row else None

        # Get matching authors
        cursor.execute("""
            SELECT DISTINCT imp_author, COUNT(*) as count
            FROM locations
            WHERE LOWER(imp_author) LIKE ? AND imp_author IS NOT NULL AND imp_author != ''
            GROUP BY imp_author
            ORDER BY count DESC
            LIMIT 10
        """, (f'%{query}%',))

        suggestions = [row[0] for row in cursor.fetchall()]
        conn.close()

        return jsonify({'suggestions': suggestions, 'most_popular': most_popular})
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        return jsonify({'suggestions': [], 'most_popular': None})


@app.route('/api/check-collision')
def api_check_collision():
    """Check if location name already exists."""
    try:
        name = request.args.get('name', '')
        config = load_config()
        conn = get_db_connection(config)
        if not conn:
            return jsonify({'exists': False})

        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM locations WHERE LOWER(loc_name) = LOWER(?)
        """, (name,))

        exists = cursor.fetchone()[0] > 0
        conn.close()

        return jsonify({'exists': exists})
    except Exception as e:
        logger.error(f"Collision check error: {e}")
        return jsonify({'exists': False})


def run_import_task(task_id: str, temp_dir: Path, data: dict, config: dict):
    """
    Run import task in background thread with health checks and timeout.

    This function monitors the import subprocess and updates task status.
    """
    import shutil
    import signal

    # Set maximum execution time (2 hours)
    MAX_EXECUTION_TIME = 7200

    start_time = time.time()

    try:
        # P0 HEALTH CHECK: Disk space validation
        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id]['current_step'] = 'Checking system health'
            WORKFLOW_STATUS[task_id]['progress'] = 5

        logger.info(f"[Task {task_id}] Running pre-import health checks...")

        # Check disk space (require 5GB free)
        disk_ok, disk_msg = check_disk_space(config.get('db_ingest', '/tmp'), required_gb=5.0)
        if not disk_ok:
            error_msg = f"Health check failed: {disk_msg}"
            logger.error(f"[Task {task_id}] {error_msg}")
            with WORKFLOW_LOCK:
                WORKFLOW_STATUS[task_id]['error'] = error_msg
                WORKFLOW_STATUS[task_id]['running'] = False
            return

        logger.info(f"[Task {task_id}] {disk_msg}")

        # Check path writability
        for path_key in ['db_ingest', 'db_backup', 'arch_loc']:
            if path_key in config:
                writable, write_msg = check_path_writable(config[path_key])
                if not writable:
                    error_msg = f"Health check failed: {write_msg}"
                    logger.error(f"[Task {task_id}] {error_msg}")
                    with WORKFLOW_LOCK:
                        WORKFLOW_STATUS[task_id]['error'] = error_msg
                        WORKFLOW_STATUS[task_id]['running'] = False
                    return
                logger.info(f"[Task {task_id}] {write_msg}")

        # Check database schema
        schema_ok, missing_tables = check_database_schema(config['db_loc'])
        if not schema_ok and Path(config['db_loc']).exists():
            logger.warning(f"[Task {task_id}] Database exists but missing tables: {missing_tables}")
            logger.info(f"[Task {task_id}] Migration will create missing tables")

        # Cleanup orphaned temp directories
        cleaned = cleanup_orphaned_temp_dirs(max_age_hours=24)
        if cleaned > 0:
            logger.info(f"[Task {task_id}] Cleaned up {cleaned} orphaned temp directories")

        # Update status: Starting migration
        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id]['current_step'] = 'Initializing database schema'
            WORKFLOW_STATUS[task_id]['progress'] = 10

        logger.info(f"[Task {task_id}] Health checks passed - starting import")
        logger.info(f"[Task {task_id}] Running database migration...")

        # Run db_migrate.py
        migrate_result = subprocess.run(
            [
                sys.executable,
                'scripts/db_migrate.py',
                '--config', 'user/user.json'
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if migrate_result.returncode != 0:
            error_msg = f"Database migration failed: {migrate_result.stderr}"
            logger.error(f"[Task {task_id}] {error_msg}")
            with WORKFLOW_LOCK:
                WORKFLOW_STATUS[task_id]['error'] = error_msg
                WORKFLOW_STATUS[task_id]['running'] = False
            return

        logger.info(f"[Task {task_id}] Database migration completed")

        # Update status: Starting import (Stage 1/5)
        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id]['current_step'] = f'Stage 1/5: Importing files to staging'
            WORKFLOW_STATUS[task_id]['progress'] = 10

        logger.info(f"[Task {task_id}] Starting import process...")

        # Run import with Popen to monitor output
        # Pass --metadata to tell script to read metadata.json instead of prompting
        process = subprocess.Popen(
            [
                sys.executable,
                'scripts/db_import.py',
                '--source', str(temp_dir),
                '--config', 'user/user.json',
                '--metadata', str(temp_dir / 'metadata.json'),
                '--skip-backup'  # Already ran migration above
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Monitor output for progress with timeout
        import_logs = []
        while True:
            # P1 HEALTH CHECK: Timeout monitoring
            elapsed = time.time() - start_time
            if elapsed > MAX_EXECUTION_TIME:
                logger.error(f"[Task {task_id}] Import timeout after {elapsed/3600:.1f} hours")
                process.kill()
                with WORKFLOW_LOCK:
                    WORKFLOW_STATUS[task_id]['error'] = f'Import timed out after {elapsed/3600:.1f} hours'
                    WORKFLOW_STATUS[task_id]['running'] = False
                return

            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                import_logs.append(line)
                logger.info(f"[Task {task_id}] {line}")

                # Update progress based on output
                with WORKFLOW_LOCK:
                    WORKFLOW_STATUS[task_id]['logs'] = import_logs[-10:]  # Keep last 10 lines
                    WORKFLOW_STATUS[task_id]['elapsed_time'] = int(elapsed)

                    # Parse progress from output if available (Stage 1: 10-20%)
                    if 'Processing file' in line or 'Imported' in line:
                        WORKFLOW_STATUS[task_id]['progress'] = min(20, WORKFLOW_STATUS[task_id]['progress'] + 1)

        # Get final status
        stderr = process.stderr.read()
        returncode = process.poll()

        if returncode != 0:
            error_msg = f"Import failed: {stderr}"
            logger.error(f"[Task {task_id}] {error_msg}")
            with WORKFLOW_LOCK:
                WORKFLOW_STATUS[task_id]['error'] = error_msg
                WORKFLOW_STATUS[task_id]['running'] = False
            return

        logger.info(f"[Task {task_id}] Stage 1/5: Import to staging completed")

        # STAGE 2: Extract metadata (db_organize.py)
        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id]['current_step'] = 'Extracting metadata from images and videos'
            WORKFLOW_STATUS[task_id]['progress'] = 20

        logger.info(f"[Task {task_id}] Stage 2/5: Running db_organize.py...")

        organize_result = subprocess.run(
            [
                sys.executable,
                'scripts/db_organize.py',
                '--config', 'user/user.json'
            ],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for metadata extraction
        )

        if organize_result.returncode != 0:
            error_msg = f"Metadata extraction failed: {organize_result.stderr}"
            logger.error(f"[Task {task_id}] {error_msg}")
            with WORKFLOW_LOCK:
                WORKFLOW_STATUS[task_id]['error'] = error_msg
                WORKFLOW_STATUS[task_id]['running'] = False
            return

        logger.info(f"[Task {task_id}] Stage 2/5: Metadata extraction completed")

        # STAGE 3: Create folder structure (db_folder.py)
        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id]['current_step'] = 'Creating organized folder structure'
            WORKFLOW_STATUS[task_id]['progress'] = 40

        logger.info(f"[Task {task_id}] Stage 3/5: Running db_folder.py...")

        folder_result = subprocess.run(
            [
                sys.executable,
                'scripts/db_folder.py',
                '--config', 'user/user.json'
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for folder creation
        )

        if folder_result.returncode != 0:
            error_msg = f"Folder creation failed: {folder_result.stderr}"
            logger.error(f"[Task {task_id}] {error_msg}")
            with WORKFLOW_LOCK:
                WORKFLOW_STATUS[task_id]['error'] = error_msg
                WORKFLOW_STATUS[task_id]['running'] = False
            return

        logger.info(f"[Task {task_id}] Stage 3/5: Folder structure created")

        # STAGE 4: Move files to archive (db_ingest.py)
        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id]['current_step'] = 'Moving files from staging to archive'
            WORKFLOW_STATUS[task_id]['progress'] = 60

        logger.info(f"[Task {task_id}] Stage 4/5: Running db_ingest.py...")

        ingest_result = subprocess.run(
            [
                sys.executable,
                'scripts/db_ingest.py',
                '--config', 'user/user.json'
            ],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout for file movement
        )

        if ingest_result.returncode != 0:
            error_msg = f"File ingest failed: {ingest_result.stderr}"
            logger.error(f"[Task {task_id}] {error_msg}")
            with WORKFLOW_LOCK:
                WORKFLOW_STATUS[task_id]['error'] = error_msg
                WORKFLOW_STATUS[task_id]['running'] = False
            return

        logger.info(f"[Task {task_id}] Stage 4/5: Files moved to archive")

        # STAGE 5: Verify integrity and cleanup (db_verify.py)
        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id]['current_step'] = 'Verifying file integrity and cleaning up'
            WORKFLOW_STATUS[task_id]['progress'] = 80

        logger.info(f"[Task {task_id}] Stage 5/5: Running db_verify.py...")

        verify_result = subprocess.run(
            [
                sys.executable,
                'scripts/db_verify.py',
                '--config', 'user/user.json'
            ],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for verification
        )

        if verify_result.returncode != 0:
            error_msg = f"Verification failed: {verify_result.stderr}"
            logger.error(f"[Task {task_id}] {error_msg}")
            with WORKFLOW_LOCK:
                WORKFLOW_STATUS[task_id]['error'] = error_msg
                WORKFLOW_STATUS[task_id]['running'] = False
            return

        logger.info(f"[Task {task_id}] Stage 5/5: Verification completed")

        # All stages completed successfully
        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id]['current_step'] = 'Import pipeline completed successfully'
            WORKFLOW_STATUS[task_id]['progress'] = 100
            WORKFLOW_STATUS[task_id]['running'] = False
            WORKFLOW_STATUS[task_id]['completed'] = True

        logger.info(f"[Task {task_id}] ✓ FULL IMPORT PIPELINE COMPLETED")
        logger.info(f"[Task {task_id}] Location: {data['loc_name']}")
        logger.info(f"[Task {task_id}] Files are now in the archive with metadata extracted")

    except Exception as e:
        error_msg = f"Task error: {str(e)}"
        logger.error(f"[Task {task_id}] {error_msg}", exc_info=True)
        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id]['error'] = error_msg
            WORKFLOW_STATUS[task_id]['running'] = False

    finally:
        # Clean up temporary directory
        try:
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"[Task {task_id}] Cleaned up temporary directory: {temp_dir}")
        except Exception as cleanup_error:
            logger.warning(f"[Task {task_id}] Failed to clean up temp directory: {cleanup_error}")

        # Schedule task cleanup after 1 hour
        def cleanup_task():
            time.sleep(3600)
            with WORKFLOW_LOCK:
                if task_id in WORKFLOW_STATUS:
                    del WORKFLOW_STATUS[task_id]
                    logger.info(f"[Task {task_id}] Cleaned up task status")

        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()


@app.route('/import/submit', methods=['POST'])
def import_submit():
    """Handle import submission - starts background task and redirects to dashboard."""
    import tempfile

    try:
        config = load_config()

        # Validate configuration before proceeding
        is_valid, issues = validate_config(config)
        if not is_valid:
            error_msg = 'Configuration error:\n' + '\n'.join(f'• {issue}' for issue in issues)
            flash(error_msg, 'error')
            logger.error(f"Configuration validation failed: {issues}")
            return redirect(url_for('import_form'))

        # Get and normalize form data - collect ALL fields
        data = {
            'loc_uuid': request.form.get('loc_uuid'),
            'loc_name': normalize_location_name(request.form.get('loc_name')),
            'aka_name': normalize_location_name(request.form.get('aka_name')) if request.form.get('aka_name') else None,
            'state': normalize_state_code(request.form.get('state')),
            'type': normalize_location_type(request.form.get('type')),
            'sub_type': normalize_sub_type(request.form.get('sub_type')) if request.form.get('sub_type') else None,
            'imp_author': normalize_author(request.form.get('imp_author')) if request.form.get('imp_author') else None,
            # Film photography data
            'is_film': request.form.get('is_film') == 'on',
            'film_stock': request.form.get('film_stock', '').strip() or None,
            'film_format': request.form.get('film_format', '').strip() or None,
            # Web URLs
            'web_urls': [url.strip() for url in request.form.get('web_urls', '').split('\n') if url.strip()]
        }

        # Handle uploaded files (both individual files and folder uploads)
        media_files = request.files.getlist('media_files')
        document_files = request.files.getlist('document_files')
        folder_files = request.files.getlist('folder_files')

        # Combine all uploaded files
        all_files = media_files + document_files + folder_files

        # Check if any files were uploaded
        uploaded_files = [f for f in all_files if f.filename]

        if not uploaded_files:
            flash('No files uploaded. Please select at least one file or folder to import.', 'error')
            return redirect(url_for('import_form'))

        # Create temporary directory for uploaded files
        temp_dir = Path(tempfile.mkdtemp(prefix='aupat_import_'))
        logger.info(f"Created temporary directory: {temp_dir}")

        # Save uploaded files to temp directory
        for file in uploaded_files:
            if file.filename:
                # For folder uploads, preserve directory structure
                # The filename includes the relative path for folder uploads
                from werkzeug.utils import secure_filename

                # Normalize path separators
                rel_path = file.filename.replace('\\', '/')

                # Secure each part of the path
                path_parts = rel_path.split('/')
                secured_parts = [secure_filename(part) for part in path_parts if part]

                # Create subdirectories if needed
                if len(secured_parts) > 1:
                    subdir = temp_dir / Path(*secured_parts[:-1])
                    subdir.mkdir(parents=True, exist_ok=True)
                    file_path = temp_dir / Path(*secured_parts)
                else:
                    file_path = temp_dir / secured_parts[0]

                file.save(str(file_path))
                logger.info(f"Saved uploaded file: {'/'.join(secured_parts)}")

        # Write metadata.json to temp directory for db_import.py to read
        metadata_file = temp_dir / 'metadata.json'
        metadata = {
            'loc_name': data['loc_name'],
            'aka_name': data['aka_name'],
            'state': data['state'],
            'type': data['type'],
            'sub_type': data['sub_type'],
            'imp_author': data['imp_author'],
            'is_film': data['is_film'],
            'film_stock': data['film_stock'],
            'film_format': data['film_format'],
            'web_urls': data['web_urls']
        }

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Created metadata file: {metadata_file}")
        logger.info(f"Metadata: {metadata}")

        # Create background task
        task_id = str(uuid.uuid4())

        with WORKFLOW_LOCK:
            WORKFLOW_STATUS[task_id] = {
                'running': True,
                'current_step': 'Preparing import',
                'progress': 5,
                'logs': [],
                'error': None,
                'location_name': data['loc_name'],
                'started_at': datetime.now().isoformat(),
                'completed': False
            }

        # Start background thread
        thread = threading.Thread(
            target=run_import_task,
            args=(task_id, temp_dir, data, config),
            daemon=True
        )
        thread.start()

        logger.info(f"Started background import task {task_id} for {data['loc_name']}")

        # Store task_id in session for dashboard to pick up
        session['last_import_task'] = task_id

        # Redirect to dashboard immediately
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Import error: {str(e)}', 'error')
        logger.error(f"Import error: {e}", exc_info=True)
        return redirect(url_for('import_form'))


@app.route('/api/task-status')
def api_task_status():
    """Get status of all active tasks."""
    with WORKFLOW_LOCK:
        # Return all active tasks
        active_tasks = {
            task_id: {
                'running': status['running'],
                'current_step': status['current_step'],
                'progress': status['progress'],
                'logs': status.get('logs', []),
                'error': status.get('error'),
                'location_name': status.get('location_name', 'Unknown'),
                'started_at': status.get('started_at'),
                'completed': status.get('completed', False)
            }
            for task_id, status in WORKFLOW_STATUS.items()
        }
    return jsonify(active_tasks)


@app.route('/api/task-status/<task_id>')
def api_task_status_single(task_id):
    """Get status of a specific task."""
    with WORKFLOW_LOCK:
        if task_id in WORKFLOW_STATUS:
            return jsonify(WORKFLOW_STATUS[task_id])
        else:
            return jsonify({'error': 'Task not found'}), 404


@app.route('/api/health')
def api_health():
    """Get system health status."""
    try:
        config = load_config()
        health = {
            'status': 'healthy',
            'checks': {},
            'timestamp': datetime.now().isoformat()
        }

        # Disk space check
        if 'db_ingest' in config:
            disk_ok, disk_msg = check_disk_space(config['db_ingest'], required_gb=5.0)
            health['checks']['disk_space'] = {
                'status': 'pass' if disk_ok else 'fail',
                'message': disk_msg
            }
            if not disk_ok:
                health['status'] = 'degraded'

        # Database schema check
        if 'db_loc' in config:
            schema_ok, missing = check_database_schema(config['db_loc'])
            health['checks']['database_schema'] = {
                'status': 'pass' if schema_ok else 'fail',
                'missing_tables': missing if not schema_ok else []
            }
            if not schema_ok and Path(config['db_loc']).exists():
                health['status'] = 'degraded'

        # Path writability checks
        health['checks']['paths'] = {}
        for path_key in ['db_ingest', 'db_backup', 'arch_loc']:
            if path_key in config:
                writable, msg = check_path_writable(config[path_key])
                health['checks']['paths'][path_key] = {
                    'status': 'pass' if writable else 'fail',
                    'message': msg
                }
                if not writable:
                    health['status'] = 'unhealthy'

        # Active tasks count
        with WORKFLOW_LOCK:
            running_tasks = sum(1 for t in WORKFLOW_STATUS.values() if t.get('running'))
            health['checks']['active_tasks'] = {
                'count': running_tasks,
                'status': 'pass'
            }

        return jsonify(health)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/settings')
def settings():
    """Settings page."""
    config = load_config()
    return render_template_string(SETTINGS_TEMPLATE, config=config)


@app.route('/settings/save', methods=['POST'])
def settings_save():
    """Save settings to user.json."""
    try:
        # Get form data
        new_config = {
            'db_name': request.form.get('db_name'),
            'db_loc': request.form.get('db_loc'),
            'db_backup': request.form.get('db_backup'),
            'db_ingest': request.form.get('db_ingest'),
            'arch_loc': request.form.get('arch_loc')
        }

        # Auto-correct db_loc if it's a directory path
        db_loc = new_config.get('db_loc', '')
        if db_loc:
            # Remove trailing slashes
            db_loc = db_loc.rstrip('/')

            # If it doesn't end with .db, assume it's a directory and add the filename
            if not db_loc.endswith('.db'):
                db_name = new_config.get('db_name', 'aupat.db')
                new_config['db_loc'] = f"{db_loc}/{db_name}"
                flash(f'Auto-corrected database path to: {new_config["db_loc"]}', 'success')
                logger.info(f"Auto-corrected db_loc from '{db_loc}' to '{new_config['db_loc']}'")

        # Validate and create parent directory for database
        if 'db_loc' in new_config and new_config['db_loc']:
            db_path = Path(new_config['db_loc'])
            if not db_path.parent.exists():
                try:
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created database directory: {db_path.parent}")
                except Exception as e:
                    flash(f'Warning: Could not create database directory {db_path.parent}: {str(e)}', 'error')

        # Validate paths exist or can be created
        paths_to_check = ['db_backup', 'db_ingest', 'arch_loc']
        for path_key in paths_to_check:
            path = new_config.get(path_key)
            if path:
                # Ensure directory paths end with /
                if not path.endswith('/'):
                    new_config[path_key] = path + '/'

                path_obj = Path(new_config[path_key])
                # If it's a directory that doesn't exist, try to create it
                if not path_obj.exists():
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created directory: {path_obj}")
                    except Exception as e:
                        flash(f'Warning: Could not create directory {path_obj}: {str(e)}', 'error')

        # Save to user/user.json
        config_path = 'user/user.json'
        config_dir = Path('user')
        config_dir.mkdir(exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(new_config, f, indent=2)

        flash('Settings saved successfully!', 'success')
        logger.info(f"Settings saved to {config_path}")
        return redirect(url_for('settings'))

    except Exception as e:
        flash(f'Failed to save settings: {str(e)}', 'error')
        logger.error(f"Failed to save settings: {e}")
        return redirect(url_for('settings'))


def get_allowed_prefixes():
    """Get allowed directory prefixes based on the operating system."""
    system = platform.system()

    if system == 'Windows':
        # Windows: Allow all drive letters and common network paths
        allowed = []
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            allowed.append(f'{letter}:\\')
            allowed.append(f'{letter}:/')
        allowed.extend(['\\\\', '//'])  # Network paths
        return allowed
    elif system == 'Darwin':  # macOS
        return ['/Users', '/Volumes', '/Applications', '/Library', '/opt', '/var', '/srv', '/data', '/storage', '/backup']
    else:  # Linux and other Unix-like
        return ['/home', '/mnt', '/media', '/opt', '/var', '/srv', '/data', '/storage', '/backup']


def get_default_home_path():
    """Get the default home directory for the current OS."""
    return str(Path.home())


@app.route('/api/default-path')
def api_default_path():
    """Get the default starting path for file explorer."""
    return jsonify({'path': get_default_home_path()})


@app.route('/api/browse')
def api_browse():
    """Browse filesystem directories for file explorer."""
    try:
        path = request.args.get('path', get_default_home_path())
        path_obj = Path(path).resolve()

        # Security: Prevent directory traversal attacks
        # Only allow browsing within reasonable directories
        allowed_prefixes = get_allowed_prefixes()
        path_str = str(path_obj)

        # Normalize path for comparison (handle both / and \ on Windows)
        normalized_path = path_str.replace('\\', '/')

        is_allowed = False
        for prefix in allowed_prefixes:
            normalized_prefix = prefix.replace('\\', '/')
            if normalized_path.startswith(normalized_prefix):
                is_allowed = True
                break

        if not is_allowed:
            system = platform.system()
            if system == 'Windows':
                error_msg = 'Access denied. Please browse from a local drive (C:, D:, etc.) or network path'
            elif system == 'Darwin':
                error_msg = 'Access denied. Allowed locations: /Users, /Volumes, /Applications, common system directories'
            else:
                error_msg = 'Access denied. Allowed locations: /home, /mnt, /media, /opt, /var, /srv, /data, /storage, /backup'
            return jsonify({'error': error_msg}), 403

        if not path_obj.exists() or not path_obj.is_dir():
            return jsonify({'error': 'Directory does not exist'}), 404

        # Get directories
        directories = []
        try:
            for item in sorted(path_obj.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    directories.append({
                        'name': item.name,
                        'path': str(item)
                    })
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403

        # Get parent directory
        parent_path = None
        # Check if we're at a root (works for both Unix / and Windows C:\)
        if path_obj.parent != path_obj:
            parent_path = str(path_obj.parent)

        return jsonify({
            'current_path': str(path_obj),
            'parent_path': parent_path,
            'directories': directories
        })

    except Exception as e:
        logger.error(f"Browse error: {e}")
        return jsonify({'error': str(e)}), 500


def main():
    """Start the web interface."""
    import argparse

    parser = argparse.ArgumentParser(description='AUPAT Web Interface v3.0')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("AUPAT Web Interface v3.0 - Abandoned Upstate Design")
    logger.info("=" * 60)
    logger.info(f"URL: http://{args.host}:{args.port}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
