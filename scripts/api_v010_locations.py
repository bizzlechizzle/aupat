#!/usr/bin/env python3
"""
AUPAT v0.1.0 Locations API Routes

Endpoints:
- GET    /api/locations       - List all locations
- GET    /api/locations/:id   - Get location details
- PUT    /api/locations/:id   - Update location
- DELETE /api/locations/:id   - Delete location

LILBITS: One function - locations CRUD API
"""

import json
import sqlite3
from flask import Blueprint, request, jsonify
from pathlib import Path


# Create blueprint
locations_bp = Blueprint('locations_v010', __name__)


def get_db_connection():
    """Get database connection."""
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    db_path = Path(config['db_loc']) / config['db_name']
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


@locations_bp.route('/locations', methods=['GET'])
def api_list_locations():
    """
    List all locations with optional filtering.

    Query Parameters:
    - state: Filter by state
    - type: Filter by type
    - historical: Filter by historical (true/false)
    - limit: Max results (default: 100)
    - offset: Offset for pagination (default: 0)

    Returns:
    {
        "total": 150,
        "locations": [...]
    }
    """
    try:
        state = request.args.get('state')
        location_type = request.args.get('type')
        historical = request.args.get('historical')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        where_clauses = []
        params = []

        if state:
            where_clauses.append("state = ?")
            params.append(state.lower())

        if location_type:
            where_clauses.append("type = ?")
            params.append(location_type.lower())

        if historical:
            where_clauses.append("historical = ?")
            params.append(1 if historical.lower() == 'true' else 0)

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Get total count
        cursor.execute(f"SELECT COUNT(*) as count FROM locations{where_sql}", params)
        total = cursor.fetchone()['count']

        # Get locations
        params.extend([limit, offset])
        cursor.execute(f"""
            SELECT * FROM locations{where_sql}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """, params)

        locations = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'total': total,
            'locations': locations
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@locations_bp.route('/locations/<loc_uuid>', methods=['GET'])
def api_get_location(loc_uuid):
    """
    Get location details including sub-locations and media counts.

    Returns:
    {
        "location": {...},
        "sub_locations": [...],
        "stats": {
            "images": 15,
            "videos": 3,
            "documents": 5,
            "maps": 2,
            "notes": 4
        }
    }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get location
        cursor.execute("SELECT * FROM locations WHERE loc_uuid = ?", (loc_uuid,))
        location = cursor.fetchone()

        if not location:
            return jsonify({'error': 'Location not found'}), 404

        # Get sub-locations
        cursor.execute("""
            SELECT * FROM sub_locations
            WHERE loc_uuid = ?
            ORDER BY is_primary DESC, sub_name
        """, (loc_uuid,))
        sub_locations = [dict(row) for row in cursor.fetchall()]

        # Get media counts
        cursor.execute("SELECT COUNT(*) as count FROM images WHERE loc_uuid = ?", (loc_uuid,))
        images_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM videos WHERE loc_uuid = ?", (loc_uuid,))
        videos_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE loc_uuid = ?", (loc_uuid,))
        docs_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM maps WHERE loc_uuid = ?", (loc_uuid,))
        maps_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM notes WHERE loc_uuid = ?", (loc_uuid,))
        notes_count = cursor.fetchone()['count']

        conn.close()

        return jsonify({
            'location': dict(location),
            'sub_locations': sub_locations,
            'stats': {
                'images': images_count,
                'videos': videos_count,
                'documents': docs_count,
                'maps': maps_count,
                'notes': notes_count
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@locations_bp.route('/locations/<loc_uuid>', methods=['PUT'])
def api_update_location(loc_uuid):
    """
    Update location.

    Request Body: (all fields optional)
    {
        "loc_name": "Updated Name",
        "status": "Demolished",
        "gps_lat": 42.8864,
        "gps_lon": -78.8784,
        ...
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build update query
        allowed_fields = [
            'loc_name', 'loc_short', 'status', 'explored', 'type', 'sub_type',
            'street', 'state', 'city', 'zip_code', 'county', 'region',
            'gps_lat', 'gps_lon', 'import_author', 'historical'
        ]

        updates = []
        params = []

        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Add updated_at timestamp
        from scripts.normalize import normalize_datetime
        updates.append("updated_at = ?")
        params.append(normalize_datetime(None))

        # Add loc_uuid to params
        params.append(loc_uuid)

        cursor.execute(f"""
            UPDATE locations
            SET {', '.join(updates)}
            WHERE loc_uuid = ?
        """, params)

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Location not found'}), 404

        conn.commit()
        conn.close()

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
