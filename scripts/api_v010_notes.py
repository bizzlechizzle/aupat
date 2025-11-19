#!/usr/bin/env python3
"""
AUPAT v0.1.0 Notes API Routes

Endpoints:
- POST   /api/notes          - Create note for location
- GET    /api/notes/:loc_id  - Get all notes for location
- PUT    /api/notes/:id      - Update note
- DELETE /api/notes/:id      - Delete note

LILBITS: One function - notes CRUD API
"""

import json
import sqlite3
from flask import Blueprint, request, jsonify
from pathlib import Path

from scripts.genuuid import generate_uuid
from scripts.normalize import normalize_datetime


# Create blueprint
notes_bp = Blueprint('notes_v010', __name__)


def get_db_connection():
    """Get database connection."""
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    db_path = Path(config['db_loc']) / config['db_name']
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


@notes_bp.route('/notes', methods=['POST'])
def api_create_note():
    """
    Create note for location.

    Request Body:
    {
        "loc_uuid": "abc123def456",
        "title": "Note title",
        "content": "Note content..."
    }

    Returns:
    {
        "note_uuid": "note123abc456"
    }
    """
    try:
        data = request.json

        if not data.get('loc_uuid'):
            return jsonify({'error': 'loc_uuid is required'}), 400

        note_uuid = generate_uuid(12)
        timestamp = normalize_datetime(None)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO notes (
                note_uuid, loc_uuid, title, content, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            note_uuid,
            data['loc_uuid'],
            data.get('title'),
            data.get('content'),
            timestamp,
            timestamp
        ))

        conn.commit()
        conn.close()

        return jsonify({'note_uuid': note_uuid}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notes_bp.route('/notes/<loc_uuid>', methods=['GET'])
def api_get_notes(loc_uuid):
    """
    Get all notes for location.

    Returns:
    [
        {
            "note_uuid": "note123abc456",
            "loc_uuid": "abc123def456",
            "title": "Note title",
            "content": "Note content...",
            "created_at": "2025-11-18T12:00:00",
            "updated_at": "2025-11-18T12:00:00"
        }
    ]
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM notes
            WHERE loc_uuid = ?
            ORDER BY updated_at DESC
        """, (loc_uuid,))

        notes = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(notes), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notes_bp.route('/notes/<note_uuid>', methods=['PUT'])
def api_update_note(note_uuid):
    """
    Update note.

    Request Body:
    {
        "title": "Updated title",
        "content": "Updated content..."
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        timestamp = normalize_datetime(None)

        conn = get_db_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if 'title' in data:
            updates.append("title = ?")
            params.append(data['title'])

        if 'content' in data:
            updates.append("content = ?")
            params.append(data['content'])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        updates.append("updated_at = ?")
        params.append(timestamp)
        params.append(note_uuid)

        cursor.execute(f"""
            UPDATE notes
            SET {', '.join(updates)}
            WHERE note_uuid = ?
        """, params)

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Note not found'}), 404

        conn.commit()
        conn.close()

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notes_bp.route('/notes/<note_uuid>', methods=['DELETE'])
def api_delete_note(note_uuid):
    """Delete note."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM notes WHERE note_uuid = ?", (note_uuid,))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Note not found'}), 404

        conn.commit()
        conn.close()

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
