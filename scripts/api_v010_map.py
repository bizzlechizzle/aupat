#!/usr/bin/env python3
"""
AUPAT v0.1.0 Map API Routes

Endpoints:
- GET /api/map/markers  - Get all locations with GPS coordinates
- GET /api/map/states   - Get states list with counts
- GET /api/map/types    - Get location types with counts

LILBITS: One function - map API
"""

import json
import sqlite3
from flask import Blueprint, request, jsonify
from pathlib import Path


# Create blueprint
map_bp = Blueprint('map_v010', __name__)


def get_db_connection():
    """Get database connection."""
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    db_path = Path(config['db_loc']) / config['db_name']
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


@map_bp.route('/map/markers', methods=['GET'])
def api_map_markers():
    """
    Get all locations with GPS coordinates for map display.

    Query Parameters:
    - state: Filter by state
    - type: Filter by type

    Returns:
    [
        {
            "loc_uuid": "abc123def456",
            "loc_name": "Old Mill",
            "loc_short": "oldmill",
            "state": "ny",
            "type": "industrial",
            "gps_lat": 42.8864,
            "gps_lon": -78.8784,
            "status": "Abandoned",
            "media_count": 15
        }
    ]
    """
    try:
        state = request.args.get('state')
        location_type = request.args.get('type')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query - only locations with GPS coordinates
        where_clauses = ["gps_lat IS NOT NULL", "gps_lon IS NOT NULL"]
        params = []

        if state:
            where_clauses.append("state = ?")
            params.append(state.lower())

        if location_type:
            where_clauses.append("type = ?")
            params.append(location_type.lower())

        where_sql = " AND ".join(where_clauses)

        cursor.execute(f"""
            SELECT
                loc_uuid, loc_name, loc_short, state, type,
                gps_lat, gps_lon, status,
                (SELECT COUNT(*) FROM images WHERE loc_uuid = locations.loc_uuid) +
                (SELECT COUNT(*) FROM videos WHERE loc_uuid = locations.loc_uuid) as media_count
            FROM locations
            WHERE {where_sql}
        """, params)

        markers = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(markers), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@map_bp.route('/map/states', methods=['GET'])
def api_map_states():
    """
    Get list of states with location counts.

    Returns:
    [
        {
            "state": "ny",
            "count": 25
        },
        {
            "state": "pa",
            "count": 15
        }
    ]
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT state, COUNT(*) as count
            FROM locations
            GROUP BY state
            ORDER BY count DESC, state
        """)

        states = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(states), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@map_bp.route('/map/types', methods=['GET'])
def api_map_types():
    """
    Get list of location types with counts.

    Returns:
    [
        {
            "type": "industrial",
            "count": 45
        },
        {
            "type": "residential",
            "count": 30
        }
    ]
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM locations
            GROUP BY type
            ORDER BY count DESC, type
        """)

        types = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(types), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
