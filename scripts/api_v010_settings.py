#!/usr/bin/env python3
"""
AUPAT v0.1.0 Settings API Routes

Endpoints:
- GET /api/settings - Get user settings
- PUT /api/settings - Update settings

LILBITS: One function - settings API
"""

import json
from flask import Blueprint, request, jsonify
from pathlib import Path


# Create blueprint
settings_bp = Blueprint('settings_v010', __name__)


@settings_bp.route('/settings', methods=['GET'])
def api_get_settings():
    """
    Get user settings from user.json.

    Returns:
    {
        "archive_loc": "/home/user/aupat/archive",
        "db_loc": "/home/user/aupat/data",
        "db_name": "aupat.db",
        "staging_loc": "/home/user/aupat/staging",
        "backup_loc": "/home/user/aupat/backups",
        "ingest_loc": "/home/user/aupat/ingest",
        "delete_import_media": false,
        "default_author": "bryant",
        "author_mode": "single"
    }
    """
    try:
        config_path = Path(__file__).parent.parent / 'user' / 'user.json'

        with open(config_path, 'r') as f:
            settings = json.load(f)

        return jsonify(settings), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/settings', methods=['PUT'])
def api_update_settings():
    """
    Update user settings in user.json.

    Request Body: (all fields optional)
    {
        "archive_loc": "/new/path/archive",
        "delete_import_media": true,
        "default_author": "new_author",
        ...
    }

    Returns:
    {
        "success": true
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        config_path = Path(__file__).parent.parent / 'user' / 'user.json'

        # Read current settings
        with open(config_path, 'r') as f:
            settings = json.load(f)

        # Update allowed fields
        allowed_fields = [
            'archive_loc', 'db_loc', 'db_name', 'staging_loc',
            'backup_loc', 'ingest_loc', 'delete_import_media',
            'default_author', 'author_mode'
        ]

        updated = False
        for field in allowed_fields:
            if field in data:
                settings[field] = data[field]
                updated = True

        if not updated:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Write back to file
        with open(config_path, 'w') as f:
            json.dump(settings, f, indent=2)

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Alias for /config (used by frontend)
@settings_bp.route('/config', methods=['GET'])
def api_get_config():
    """Alias for /settings endpoint (for frontend compatibility)."""
    return api_get_settings()
