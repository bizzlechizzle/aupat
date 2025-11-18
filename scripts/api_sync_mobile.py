"""
AUPAT Mobile Sync API Endpoints
Bidirectional sync between mobile app and desktop.

Endpoints:
- POST /api/sync/mobile - Push new locations from mobile to desktop
- GET /api/sync/mobile/pull - Pull new locations from desktop to mobile

Version: 0.1.2
Last Updated: 2025-11-18
"""

import logging
import sqlite3
import json
from datetime import datetime
from uuid import uuid4
from flask import Blueprint, jsonify, request, current_app
from pathlib import Path

logger = logging.getLogger(__name__)

# Create Blueprint for mobile sync API routes
api_sync_mobile = Blueprint('api_sync_mobile', __name__, url_prefix='/api/sync')


@api_sync_mobile.after_request
def add_cors_headers(response):
    """Add CORS headers to all mobile sync API responses."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response


def get_db_connection():
    """Get database connection from Flask app config."""
    db_path = current_app.config.get('DB_PATH')
    if not db_path:
        raise ValueError("DB_PATH not configured")

    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@api_sync_mobile.route('/mobile', methods=['POST', 'OPTIONS'])
def sync_mobile_push():
    """
    Push new locations from mobile to desktop.

    Request Body:
        {
            "device_id": "mobile-uuid",
            "new_locations": [
                {
                    "loc_uuid": "...",
                    "loc_name": "...",
                    "lat": 42.8142,
                    "lon": -73.9396,
                    "loc_type": "factory",
                    "created_at": "2025-11-18T10:30:00Z",
                    "photos": ["file:///path/to/photo1.jpg"]
                }
            ],
            "updated_locations": [],
            "device_timestamp": "2025-11-18T10:35:00Z"
        }

    Returns:
        {
            "status": "success",
            "synced_count": 5,
            "conflicts": [],
            "next_sync_after": "2025-11-18T10:36:00Z"
        }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204

    try:
        payload = request.get_json(force=True, silent=True)
        if not payload:
            return jsonify({'status': 'error', 'error': 'Missing or invalid JSON payload'}), 400

        device_id = payload.get('device_id')
        new_locations = payload.get('new_locations', [])
        updated_locations = payload.get('updated_locations', [])
        device_timestamp = payload.get('device_timestamp')

        if not device_id:
            return jsonify({'status': 'error', 'error': 'device_id required'}), 400

        logger.info(f"Mobile sync push from device {device_id}: {len(new_locations)} new, {len(updated_locations)} updated")

        conn = get_db_connection()
        cursor = conn.cursor()

        synced_count = 0
        conflicts = []

        # Process new locations
        for loc_data in new_locations:
            try:
                # Check if location already exists (conflict detection)
                existing = cursor.execute(
                    'SELECT loc_uuid FROM locations WHERE loc_uuid = ?',
                    (loc_data['loc_uuid'],)
                ).fetchone()

                if existing:
                    # Conflict: Location already exists
                    # Strategy: Skip (mobile will pull this location in next sync)
                    conflicts.append({
                        'loc_uuid': loc_data['loc_uuid'],
                        'reason': 'location_already_exists',
                    })
                    logger.warning(f"Conflict: Location {loc_data['loc_uuid']} already exists")
                    continue

                # Insert new location
                # Using simplified schema (can expand as needed)
                cursor.execute('''
                    INSERT INTO locations (
                        loc_uuid, loc_name, lat, lon, type, loc_add, json_update
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    loc_data['loc_uuid'],
                    loc_data['loc_name'],
                    loc_data['lat'],
                    loc_data['lon'],
                    loc_data.get('loc_type', 'other'),
                    loc_data.get('created_at', datetime.now().isoformat()),
                    datetime.now().isoformat(),
                ))

                synced_count += 1
                logger.info(f"Inserted location {loc_data['loc_uuid']}: {loc_data['loc_name']}")

                # TODO: Process photos
                # For each photo in loc_data['photos']:
                # 1. Upload to Immich via immich_adapter
                # 2. Insert to images table with immich_asset_id
                # This is deferred to Phase 8

            except Exception as e:
                logger.error(f"Failed to sync location {loc_data.get('loc_uuid')}: {e}")
                conflicts.append({
                    'loc_uuid': loc_data.get('loc_uuid'),
                    'reason': f'sync_error: {str(e)}',
                })

        # Process updated locations (future)
        for loc_data in updated_locations:
            # Merge strategy: Desktop timestamp wins
            # For v0.1.2, this is simplified (no updates from mobile yet)
            pass

        conn.commit()

        # Log sync event
        sync_id = str(uuid4())
        cursor.execute('''
            INSERT INTO sync_log (sync_id, device_id, sync_type, timestamp, items_synced, conflicts, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            sync_id,
            device_id,
            'mobile_to_desktop',
            datetime.now().isoformat(),
            synced_count,
            len(conflicts),
            'success' if not conflicts else 'partial',
        ))
        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'synced_count': synced_count,
            'conflicts': conflicts,
            'next_sync_after': datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Mobile sync push failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
        }), 500


@api_sync_mobile.route('/mobile/pull', methods=['GET', 'OPTIONS'])
def sync_mobile_pull():
    """
    Pull new/updated locations from desktop to mobile.

    Query Parameters:
        - since: ISO timestamp of last sync (optional)
        - limit: Maximum locations to return (default: 1000)

    Returns:
        {
            "status": "success",
            "locations": [
                {
                    "locUuid": "...",
                    "locName": "...",
                    "lat": 42.8142,
                    "lon": -73.9396,
                    "locType": "factory",
                    "streetAddress": "...",
                    "city": "...",
                    "stateAbbrev": "NY",
                    "synced": 1,
                    "lastModifiedAt": "2025-11-18T10:00:00Z"
                }
            ],
            "count": 150,
            "has_more": false
        }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204

    try:
        since_param = request.args.get('since', '')
        limit = request.args.get('limit', 1000, type=int)

        # Validate limit
        if limit > 10000:
            limit = 10000  # Safety cap

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        if since_param:
            # Return locations modified after 'since' timestamp
            query = '''
                SELECT loc_uuid, loc_name, lat, lon, type,
                       street_address, city, state_abbrev,
                       json_update as last_modified_at
                FROM locations
                WHERE json_update > ?
                ORDER BY json_update DESC
                LIMIT ?
            '''
            cursor.execute(query, (since_param, limit))
        else:
            # Return all locations (initial sync)
            query = '''
                SELECT loc_uuid, loc_name, lat, lon, type,
                       street_address, city, state_abbrev,
                       json_update as last_modified_at
                FROM locations
                ORDER BY json_update DESC
                LIMIT ?
            '''
            cursor.execute(query, (limit,))

        rows = cursor.fetchall()

        # Convert to mobile-friendly format
        locations = []
        for row in rows:
            locations.append({
                'locUuid': row['loc_uuid'],
                'locName': row['loc_name'],
                'lat': row['lat'],
                'lon': row['lon'],
                'locType': row['type'] or 'other',
                'streetAddress': row['street_address'],
                'city': row['city'],
                'stateAbbrev': row['state_abbrev'],
                'synced': 1,  # All desktop locations are synced by definition
                'lastModifiedAt': row['last_modified_at'],
            })

        conn.close()

        # Check if there are more results
        has_more = len(locations) == limit

        logger.info(f"Mobile pull: Returning {len(locations)} locations (since: {since_param or 'all'})")

        return jsonify({
            'status': 'success',
            'locations': locations,
            'count': len(locations),
            'has_more': has_more,
        }), 200

    except Exception as e:
        logger.error(f"Mobile sync pull failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
        }), 500


def register_mobile_sync_routes(app):
    """Register mobile sync routes with Flask app."""
    app.register_blueprint(api_sync_mobile)
