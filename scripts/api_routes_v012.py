"""
AUPAT v0.1.2 API Routes
Additional REST API endpoints for desktop app integration.

This module provides:
- Health check endpoints
- Map data endpoints (GPS coordinates for clustering)
- Location detail endpoints
- Media listing endpoints with Immich references

Version: 0.1.2
Last Updated: 2025-11-17
"""

import logging
import sqlite3
from flask import Blueprint, jsonify, request, current_app
from pathlib import Path

logger = logging.getLogger(__name__)

# Create Blueprint for v0.1.2 API routes
api_v012 = Blueprint('api_v012', __name__, url_prefix='/api')


def get_db_connection():
    """Get database connection from Flask app config."""
    db_path = current_app.config.get('DB_PATH')
    if not db_path:
        raise ValueError("DB_PATH not configured")

    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@api_v012.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON with service status
    """
    try:
        # Check database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM locations")
        location_count = cursor.fetchone()[0]
        conn.close()

        return jsonify({
            'status': 'ok',
            'version': '0.1.2',
            'database': 'connected',
            'location_count': location_count
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'version': '0.1.2',
            'database': 'disconnected',
            'error': str(e)
        }), 500


@api_v012.route('/health/services', methods=['GET'])
def health_check_services():
    """
    Check health of external services (Immich, ArchiveBox).

    Returns:
        JSON with service health status
    """
    services = {
        'immich': 'unknown',
        'archivebox': 'unknown'
    }

    # Check Immich
    try:
        from adapters.immich_adapter import create_immich_adapter
        immich = create_immich_adapter()
        services['immich'] = 'healthy' if immich.health_check() else 'unhealthy'
    except Exception as e:
        services['immich'] = 'unavailable'
        logger.debug(f"Immich health check failed: {e}")

    # Check ArchiveBox
    try:
        from adapters.archivebox_adapter import create_archivebox_adapter
        archivebox = create_archivebox_adapter()
        services['archivebox'] = 'healthy' if archivebox.health_check() else 'unhealthy'
    except Exception as e:
        services['archivebox'] = 'unavailable'
        logger.debug(f"ArchiveBox health check failed: {e}")

    # Determine overall status
    statuses = list(services.values())
    if all(s == 'healthy' for s in statuses):
        overall = 'ok'
    elif all(s == 'unavailable' for s in statuses):
        overall = 'error'
    else:
        overall = 'degraded'

    return jsonify({
        'status': overall,
        'services': services
    }), 200


@api_v012.route('/map/markers', methods=['GET'])
def get_map_markers():
    """
    Get all locations with GPS coordinates for map display.

    Query parameters:
        - bounds: Optional bounding box filter (format: "minLat,minLon,maxLat,maxLon")
        - limit: Maximum number of results (default: unlimited, max 200000)

    Returns:
        JSON array of locations with GPS data
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for bounding box filter
        bounds = request.args.get('bounds')
        limit = request.args.get('limit', type=int)

        # Validate limit
        if limit is not None and limit > 200000:
            limit = 200000

        if bounds:
            try:
                min_lat, min_lon, max_lat, max_lon = map(float, bounds.split(','))
                if limit:
                    cursor.execute(
                        """
                        SELECT loc_uuid, loc_name, lat, lon, type, state
                        FROM locations
                        WHERE lat IS NOT NULL
                        AND lon IS NOT NULL
                        AND lat BETWEEN ? AND ?
                        AND lon BETWEEN ? AND ?
                        LIMIT ?
                        """,
                        (min_lat, max_lat, min_lon, max_lon, limit)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT loc_uuid, loc_name, lat, lon, type, state
                        FROM locations
                        WHERE lat IS NOT NULL
                        AND lon IS NOT NULL
                        AND lat BETWEEN ? AND ?
                        AND lon BETWEEN ? AND ?
                        """,
                        (min_lat, max_lat, min_lon, max_lon)
                    )
            except ValueError:
                return jsonify({'error': 'Invalid bounds format'}), 400
        else:
            if limit:
                cursor.execute(
                    """
                    SELECT loc_uuid, loc_name, lat, lon, type, state
                    FROM locations
                    WHERE lat IS NOT NULL AND lon IS NOT NULL
                    LIMIT ?
                    """,
                    (limit,)
                )
            else:
                cursor.execute(
                    """
                    SELECT loc_uuid, loc_name, lat, lon, type, state
                    FROM locations
                    WHERE lat IS NOT NULL AND lon IS NOT NULL
                    """
                )

        rows = cursor.fetchall()
        conn.close()

        markers = []
        for row in rows:
            markers.append({
                'loc_uuid': row['loc_uuid'],
                'loc_name': row['loc_name'],
                'lat': row['lat'],
                'lon': row['lon'],
                'type': row['type'],
                'state': row['state']
            })

        return jsonify(markers), 200

    except Exception as e:
        logger.error(f"Failed to get map markers: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/locations/<loc_uuid>', methods=['GET'])
def get_location_details(loc_uuid):
    """
    Get detailed information for a location.

    Args:
        loc_uuid: Location UUID

    Returns:
        JSON with location details and media counts
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get location data
        cursor.execute(
            """
            SELECT *
            FROM locations
            WHERE loc_uuid = ?
            """,
            (loc_uuid,)
        )

        location = cursor.fetchone()
        if not location:
            conn.close()
            return jsonify({'error': 'Location not found'}), 404

        # Get media counts
        cursor.execute("SELECT COUNT(*) FROM images WHERE loc_uuid = ?", (loc_uuid,))
        image_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM videos WHERE loc_uuid = ?", (loc_uuid,))
        video_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM documents WHERE loc_uuid = ?", (loc_uuid,))
        document_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM urls WHERE loc_uuid = ?", (loc_uuid,))
        url_count = cursor.fetchone()[0]

        conn.close()

        # Build response
        result = dict(location)
        result['counts'] = {
            'images': image_count,
            'videos': video_count,
            'documents': document_count,
            'urls': url_count
        }

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Failed to get location details: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/locations/<loc_uuid>/images', methods=['GET'])
def get_location_images(loc_uuid):
    """
    Get images for a location.

    Args:
        loc_uuid: Location UUID

    Query parameters:
        - limit: Maximum number of results (default: 100)
        - offset: Offset for pagination (default: 0)

    Returns:
        JSON array of image records with Immich asset IDs
    """
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                img_sha256, img_name, img_loc,
                immich_asset_id, img_width, img_height,
                img_size_bytes, gps_lat, gps_lon,
                img_hardware, camera, phone, drone, go_pro, film,
                img_add
            FROM images
            WHERE loc_uuid = ?
            ORDER BY img_add DESC
            LIMIT ? OFFSET ?
            """,
            (loc_uuid, limit, offset)
        )

        rows = cursor.fetchall()
        conn.close()

        images = [dict(row) for row in rows]

        return jsonify(images), 200

    except Exception as e:
        logger.error(f"Failed to get location images: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/locations/<loc_uuid>/videos', methods=['GET'])
def get_location_videos(loc_uuid):
    """
    Get videos for a location.

    Args:
        loc_uuid: Location UUID

    Query parameters:
        - limit: Maximum number of results (default: 100)
        - offset: Offset for pagination (default: 0)

    Returns:
        JSON array of video records with Immich asset IDs
    """
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                vid_sha256, vid_name, vid_loc,
                immich_asset_id, vid_width, vid_height,
                vid_duration_sec, vid_size_bytes,
                gps_lat, gps_lon,
                vid_hardware, camera, phone, drone, go_pro, dash_cam,
                vid_add
            FROM videos
            WHERE loc_uuid = ?
            ORDER BY vid_add DESC
            LIMIT ? OFFSET ?
            """,
            (loc_uuid, limit, offset)
        )

        rows = cursor.fetchall()
        conn.close()

        videos = [dict(row) for row in rows]

        return jsonify(videos), 200

    except Exception as e:
        logger.error(f"Failed to get location videos: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/locations/<loc_uuid>/archives', methods=['GET'])
def get_location_archives(loc_uuid):
    """
    Get archived URLs for a location.

    Args:
        loc_uuid: Location UUID

    Returns:
        JSON array of URL records with ArchiveBox data
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                url_uuid, url, domain,
                archivebox_snapshot_id, archive_status,
                archive_date, media_extracted,
                url_add
            FROM urls
            WHERE loc_uuid = ?
            ORDER BY url_add DESC
            """,
            (loc_uuid,)
        )

        rows = cursor.fetchall()
        conn.close()

        archives = [dict(row) for row in rows]

        return jsonify(archives), 200

    except Exception as e:
        logger.error(f"Failed to get location archives: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/search', methods=['GET'])
def search_locations():
    """
    Search locations by name or other criteria.

    Query parameters:
        - q: Search query (matches location name)
        - state: Filter by state code
        - type: Filter by location type
        - limit: Maximum results (default: 50)

    Returns:
        JSON array of matching locations
    """
    try:
        query = request.args.get('q', '')
        state = request.args.get('state')
        loc_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query dynamically
        sql = "SELECT * FROM locations WHERE 1=1"
        params = []

        if query:
            sql += " AND loc_name LIKE ?"
            params.append(f"%{query}%")

        if state:
            sql += " AND state = ?"
            params.append(state)

        if loc_type:
            sql += " AND type = ?"
            params.append(loc_type)

        sql += " ORDER BY loc_name LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        results = [dict(row) for row in rows]

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return jsonify({'error': str(e)}), 500


def register_api_routes(app):
    """
    Register v0.1.2 API routes with Flask app.

    Args:
        app: Flask application instance
    """
    # Enable CORS for API routes (for desktop app)
    @api_v012.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response

    app.register_blueprint(api_v012)
    logger.info("Registered v0.1.2 API routes")
