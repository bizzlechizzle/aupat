#!/usr/bin/env python3
"""
AUPAT v0.1.0 Statistics API Routes

Endpoints for dashboard statistics:
- GET /api/stats/dashboard - Get all dashboard stats in one call
- GET /api/stats/pinned - Get pinned locations
- GET /api/stats/recent - Get recent locations
- GET /api/stats/updated - Get recently updated locations
- GET /api/stats/states - Get top states by count
- GET /api/stats/types - Get top types by count
- GET /api/stats/counts - Get aggregate counts

LILBITS: One function - statistics API
"""

from flask import Blueprint, request, jsonify
from scripts.utils import get_db_connection


# Create blueprint
stats_bp = Blueprint('stats_v010', __name__)


@stats_bp.route('/stats/dashboard', methods=['GET'])
def api_dashboard_stats():
    """
    Get all dashboard statistics in a single call.

    Returns:
    {
        "success": true,
        "data": {
            "pinned": [...],
            "recent": [...],
            "updated": [...],
            "states": [...],
            "types": [...],
            "counts": {...}
        }
    }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Pinned locations (top 5)
        cursor.execute("""
            SELECT loc_uuid, loc_name, loc_short, state, type, city,
                   gps_lat, gps_lon, created_at, updated_at
            FROM locations
            WHERE pinned = 1
            ORDER BY updated_at DESC
            LIMIT 5
        """)
        pinned = [dict(row) for row in cursor.fetchall()]

        # Recent locations (last 5)
        cursor.execute("""
            SELECT loc_uuid, loc_name, loc_short, state, type, city,
                   gps_lat, gps_lon, created_at, updated_at
            FROM locations
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent = [dict(row) for row in cursor.fetchall()]

        # Recently updated (last 5, excluding just created)
        cursor.execute("""
            SELECT loc_uuid, loc_name, loc_short, state, type, city,
                   gps_lat, gps_lon, created_at, updated_at
            FROM locations
            WHERE updated_at != created_at
            ORDER BY updated_at DESC
            LIMIT 5
        """)
        updated = [dict(row) for row in cursor.fetchall()]

        # Top 5 states by count
        cursor.execute("""
            SELECT state, COUNT(*) as count
            FROM locations
            WHERE state IS NOT NULL AND state != ''
            GROUP BY state
            ORDER BY count DESC
            LIMIT 5
        """)
        states = [dict(row) for row in cursor.fetchall()]

        # Top 10 types by count
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM locations
            WHERE type IS NOT NULL AND type != ''
            GROUP BY type
            ORDER BY count DESC
            LIMIT 10
        """)
        types = [dict(row) for row in cursor.fetchall()]

        # Aggregate counts
        cursor.execute("SELECT COUNT(*) as total FROM locations")
        total_count = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as count FROM locations WHERE favorite = 1")
        favorites_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM locations WHERE documented = 0")
        undocumented_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM locations WHERE historical = 1")
        historical_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(DISTINCT loc_uuid) as count FROM notes")
        with_notes_count = cursor.fetchone()['count']

        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'pinned': pinned,
                'recent': recent,
                'updated': updated,
                'states': states,
                'types': types,
                'counts': {
                    'total': total_count,
                    'favorites': favorites_count,
                    'undocumented': undocumented_count,
                    'historical': historical_count,
                    'with_notes': with_notes_count
                }
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@stats_bp.route('/stats/random', methods=['GET'])
def api_random_location():
    """
    Get a random location.

    Returns:
    {
        "success": true,
        "data": {location object}
    }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT loc_uuid, loc_name, loc_short, state, type, city,
                   gps_lat, gps_lon
            FROM locations
            ORDER BY RANDOM()
            LIMIT 1
        """)
        location = cursor.fetchone()
        conn.close()

        if location:
            return jsonify({'success': True, 'data': dict(location)}), 200
        else:
            return jsonify({'success': False, 'error': 'No locations found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
