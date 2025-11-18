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
from scripts.adapters.archivebox_adapter import create_archivebox_adapter

logger = logging.getLogger(__name__)

# Create Blueprint for v0.1.2 API routes
api_v012 = Blueprint('api_v012', __name__, url_prefix='/api')


# Enable CORS for API routes (for desktop app)
@api_v012.after_request
def after_request(response):
    """Add CORS headers to all API responses."""
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
        from scripts.adapters.immich_adapter import create_immich_adapter
        immich = create_immich_adapter()
        services['immich'] = 'healthy' if immich.health_check() else 'unhealthy'
    except Exception as e:
        services['immich'] = 'unavailable'
        logger.error(f"Immich adapter import or health check failed: {e}")

    # Check ArchiveBox
    try:
        archivebox = create_archivebox_adapter()
        services['archivebox'] = 'healthy' if archivebox.health_check() else 'unhealthy'
    except Exception as e:
        services['archivebox'] = 'unavailable'
        logger.error(f"ArchiveBox adapter import or health check failed: {e}")

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
                img_uuid, img_sha, img_name,
                immich_asset_id, img_width, img_height,
                img_size_bytes, gps_lat, gps_lon,
                camera_make, camera_model, camera_type,
                img_taken, img_add, img_update
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
                url_uuid, url, url_title, url_desc,
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


@api_v012.route('/locations/<loc_uuid>/urls', methods=['POST'])
def archive_url(loc_uuid):
    """
    Archive a new URL for a location.

    Args:
        loc_uuid: Location UUID

    Request JSON:
        {
            "url": "https://example.com",
            "title": "Optional title",
            "description": "Optional description"
        }

    Returns:
        JSON with created URL record
    """
    try:
        # Validate request
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'url is required'}), 400

        url = data['url'].strip()
        if not url:
            return jsonify({'error': 'url cannot be empty'}), 400

        # Optional fields
        title = data.get('title', '').strip() or None
        description = data.get('description', '').strip() or None

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify location exists
        cursor.execute("SELECT loc_uuid FROM locations WHERE loc_uuid = ?", (loc_uuid,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Location not found'}), 404

        # Generate UUID and timestamp
        from scripts.utils import generate_uuid
        from scripts.normalize import normalize_datetime

        url_uuid = generate_uuid(cursor, 'urls', 'url_uuid')
        timestamp = normalize_datetime(None)

        # Insert URL record
        cursor.execute(
            """
            INSERT INTO urls (
                url_uuid, loc_uuid, url, url_title, url_desc,
                archive_status, url_add, url_update
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (url_uuid, loc_uuid, url, title, description, timestamp, timestamp)
        )

        conn.commit()
        conn.close()

        # Phase B: Attempt to archive URL via ArchiveBox
        # Database connection closed before network call to prevent blocking
        try:
            logger.info(f"Archiving URL via ArchiveBox: {url}")
            archivebox = create_archivebox_adapter()
            snapshot_id = archivebox.archive_url(url)

            if snapshot_id:
                # Reopen database to update with snapshot ID
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE urls
                    SET archivebox_snapshot_id = ?,
                        archive_status = 'archiving',
                        url_update = ?
                    WHERE url_uuid = ?
                    """,
                    (snapshot_id, timestamp, url_uuid)
                )
                conn.commit()
                conn.close()
                logger.info(f"ArchiveBox snapshot created: {snapshot_id}")
            else:
                logger.warning(f"ArchiveBox returned no snapshot ID for {url}")

        except Exception as e:
            # Graceful degradation: Log error but continue
            # URL is already saved to database with status='pending'
            # Background worker (Phase C) can retry
            logger.warning(f"ArchiveBox archiving failed, URL saved as pending: {e}")

        # Fetch final record
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                url_uuid, url, url_title, url_desc,
                archivebox_snapshot_id, archive_status,
                archive_date, media_extracted, url_add
            FROM urls
            WHERE url_uuid = ?
            """,
            (url_uuid,)
        )

        result = dict(cursor.fetchone())
        conn.close()

        logger.info(f"URL saved for location {loc_uuid}: {url} (status: {result['archive_status']})")
        return jsonify(result), 201

    except Exception as e:
        logger.error(f"Failed to archive URL: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/urls/<url_uuid>', methods=['DELETE'])
def delete_url(url_uuid):
    """
    Delete an archived URL.

    Args:
        url_uuid: URL UUID

    Returns:
        JSON with success status
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify URL exists
        cursor.execute("SELECT url_uuid FROM urls WHERE url_uuid = ?", (url_uuid,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'URL not found'}), 404

        # Delete URL
        cursor.execute("DELETE FROM urls WHERE url_uuid = ?", (url_uuid,))
        conn.commit()
        conn.close()

        logger.info(f"Deleted URL {url_uuid}")
        return jsonify({'success': True, 'message': 'URL deleted'}), 200

    except Exception as e:
        logger.error(f"Failed to delete URL: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/locations/<loc_uuid>/import', methods=['POST'])
def import_file_to_location(loc_uuid):
    """
    Import a media file to a location.

    Accepts base64-encoded file data from desktop app, uploads to Immich,
    extracts metadata, and creates database record.

    Args:
        loc_uuid: Location UUID

    Request JSON:
        {
            "filename": "photo.jpg",
            "category": "image" | "video",
            "size": 1234567,
            "data": "base64-encoded-file-data"
        }

    Returns:
        JSON with import result and asset metadata
    """
    import base64
    import tempfile
    import os
    from pathlib import Path

    temp_file = None

    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Validate required fields
        required_fields = ['filename', 'category', 'size', 'data']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({'error': f'Missing required fields: {missing}'}), 400

        filename = data['filename'].strip()
        category = data['category'].strip().lower()
        file_size = data['size']
        base64_data = data['data']

        # Validate category
        if category not in ['image', 'video']:
            return jsonify({'error': f'Invalid category: {category}. Must be "image" or "video"'}), 400

        # Validate location exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT loc_uuid FROM locations WHERE loc_uuid = ?", (loc_uuid,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Location not found'}), 404
        conn.close()

        # Decode base64 data
        try:
            file_data = base64.b64decode(base64_data)
        except Exception as e:
            return jsonify({'error': f'Invalid base64 data: {e}'}), 400

        # Validate decoded size matches declared size
        if len(file_data) != file_size:
            logger.warning(f"Size mismatch: declared {file_size}, actual {len(file_data)}")

        # Write to temporary file
        file_ext = Path(filename).suffix
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext, prefix='aupat_import_')
        temp_file = temp_path

        try:
            os.write(temp_fd, file_data)
            os.close(temp_fd)
        except Exception as e:
            os.close(temp_fd)
            raise e

        logger.info(f"Importing {category} file: {filename} ({file_size} bytes) to location {loc_uuid}")

        # Import utility functions
        from scripts.utils import calculate_sha256, generate_uuid, check_sha256_collision
        from scripts.normalize import normalize_datetime
        from scripts.immich_integration import (
            upload_to_immich,
            extract_gps_from_exif,
            get_image_dimensions,
            get_video_dimensions,
            get_file_size
        )

        # Calculate SHA256
        sha256_full = calculate_sha256(temp_path)
        sha256_short = sha256_full[:8]

        # Check for duplicate
        conn = get_db_connection()
        cursor = conn.cursor()

        if check_sha256_collision(cursor, sha256_full, category):
            conn.close()
            logger.warning(f"Duplicate {category} detected: {filename} (SHA256: {sha256_short})")
            return jsonify({
                'error': 'Duplicate file detected',
                'sha256': sha256_short,
                'message': f'This {category} already exists in the database'
            }), 409

        # Upload to Immich
        immich_asset_id = upload_to_immich(temp_path)
        if not immich_asset_id:
            logger.warning(f"Immich upload failed for {filename}, continuing without Immich integration")

        # Extract metadata
        timestamp = normalize_datetime(None)
        gps_coords = extract_gps_from_exif(temp_path)
        gps_lat = gps_coords[0] if gps_coords else None
        gps_lon = gps_coords[1] if gps_coords else None

        if category == 'image':
            # Image-specific metadata
            dimensions = get_image_dimensions(temp_path)
            width = dimensions[0] if dimensions else None
            height = dimensions[1] if dimensions else None

            # Generate UUID
            img_uuid = generate_uuid(cursor, 'images', 'img_uuid')

            # Insert into images table
            cursor.execute(
                """
                INSERT INTO images (
                    img_uuid, loc_uuid, img_sha, img_name, img_ext,
                    img_add, img_update, immich_asset_id,
                    img_width, img_height, img_size_bytes,
                    gps_lat, gps_lon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    img_uuid, loc_uuid, sha256_full, filename, file_ext,
                    timestamp, timestamp, immich_asset_id,
                    width, height, file_size,
                    gps_lat, gps_lon
                )
            )

            conn.commit()
            conn.close()

            logger.info(f"Image imported: {filename} -> {img_uuid} (SHA256: {sha256_short})")

            return jsonify({
                'success': True,
                'category': 'image',
                'uuid': img_uuid,
                'sha256': sha256_short,
                'immich_asset_id': immich_asset_id,
                'width': width,
                'height': height,
                'size_bytes': file_size,
                'gps': {'lat': gps_lat, 'lon': gps_lon} if gps_coords else None
            }), 201

        else:  # category == 'video'
            # Video-specific metadata
            vid_data = get_video_dimensions(temp_path)
            width = vid_data[0] if vid_data else None
            height = vid_data[1] if vid_data else None
            duration = vid_data[2] if vid_data else None

            # Generate UUID
            vid_uuid = generate_uuid(cursor, 'videos', 'vid_uuid')

            # Insert into videos table
            cursor.execute(
                """
                INSERT INTO videos (
                    vid_uuid, loc_uuid, vid_sha, vid_name, vid_ext,
                    vid_add, vid_update, immich_asset_id,
                    vid_width, vid_height, vid_duration_sec, vid_size_bytes,
                    gps_lat, gps_lon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vid_uuid, loc_uuid, sha256_full, filename, file_ext,
                    timestamp, timestamp, immich_asset_id,
                    width, height, duration, file_size,
                    gps_lat, gps_lon
                )
            )

            conn.commit()
            conn.close()

            logger.info(f"Video imported: {filename} -> {vid_uuid} (SHA256: {sha256_short})")

            return jsonify({
                'success': True,
                'category': 'video',
                'uuid': vid_uuid,
                'sha256': sha256_short,
                'immich_asset_id': immich_asset_id,
                'width': width,
                'height': height,
                'duration_sec': duration,
                'size_bytes': file_size,
                'gps': {'lat': gps_lat, 'lon': gps_lon} if gps_coords else None
            }), 201

    except Exception as e:
        logger.error(f"Import failed for {filename}: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file}: {e}")


@api_v012.route('/locations', methods=['GET', 'POST'])
def locations_list_create():
    """
    List all locations or create a new location.

    GET: Returns list of all locations
    POST: Creates a new location

    Request JSON (POST):
        {
            "loc_name": "Location Name",
            "aka_name": "Optional alternate name",
            "state": "ny",
            "type": "industrial",
            "sub_type": "Optional sub type",
            "street_address": "Optional address",
            "city": "Optional city",
            "zip_code": "Optional ZIP",
            "lat": 42.6526,
            "lon": -73.7562,
            "gps_source": "manual"
        }

    Returns:
        GET: JSON array of all locations
        POST: JSON with created location
    """
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM locations ORDER BY loc_name")
            rows = cursor.fetchall()
            conn.close()

            locations_list = [dict(row) for row in rows]

            return jsonify(locations_list), 200

        except Exception as e:
            logger.error(f"Failed to list locations: {e}")
            return jsonify({'error': str(e)}), 500

    else:  # POST
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400

            # Validate required fields
            if 'loc_name' not in data or not data['loc_name'] or not data['loc_name'].strip():
                return jsonify({'error': 'loc_name is required'}), 400

            if 'state' not in data or not data['state'] or not data['state'].strip():
                return jsonify({'error': 'state is required'}), 400

            if 'type' not in data or not data['type'] or not data['type'].strip():
                return jsonify({'error': 'type is required'}), 400

            from scripts.utils import generate_uuid
            from scripts.normalize import normalize_datetime

            conn = get_db_connection()
            cursor = conn.cursor()

            # Generate UUID
            loc_uuid = generate_uuid(cursor, 'locations', 'loc_uuid')
            timestamp = normalize_datetime(None)

            # Extract fields
            loc_name = data['loc_name'].strip()
            aka_name = (data.get('aka_name') or '').strip() or None
            state = data['state'].strip().lower()
            loc_type = data['type'].strip().lower()
            sub_type = (data.get('sub_type') or '').strip() or None
            street_address = (data.get('street_address') or '').strip() or None
            city = (data.get('city') or '').strip() or None
            zip_code = (data.get('zip_code') or '').strip() or None
            lat = data.get('lat')
            lon = data.get('lon')
            gps_source = data.get('gps_source', 'manual') if (lat and lon) else None

            # Insert location
            cursor.execute(
                """
                INSERT INTO locations (
                    loc_uuid, loc_name, aka_name, state, type, sub_type,
                    street_address, city, zip_code,
                    lat, lon, gps_source,
                    loc_add, loc_update
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    loc_uuid, loc_name, aka_name, state, loc_type, sub_type,
                    street_address, city, zip_code,
                    lat, lon, gps_source,
                    timestamp, timestamp
                )
            )

            conn.commit()

            # Fetch created location
            cursor.execute("SELECT * FROM locations WHERE loc_uuid = ?", (loc_uuid,))
            result = dict(cursor.fetchone())
            conn.close()

            logger.info(f"Created location: {loc_name} ({loc_uuid})")

            return jsonify(result), 201

        except Exception as e:
            logger.error(f"Failed to create location: {e}")
            return jsonify({'error': str(e)}), 500


@api_v012.route('/locations/<loc_uuid>', methods=['PUT', 'DELETE'])
def location_update_delete(loc_uuid):
    """
    Update or delete a location.

    PUT: Updates location fields
    DELETE: Deletes location (cascades to all media)

    Request JSON (PUT):
        {
            "loc_name": "Updated Name",
            ... other fields ...
        }

    Returns:
        PUT: JSON with updated location
        DELETE: JSON with success message
    """
    if request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400

            from scripts.normalize import normalize_datetime

            conn = get_db_connection()
            cursor = conn.cursor()

            # Verify location exists
            cursor.execute("SELECT loc_uuid FROM locations WHERE loc_uuid = ?", (loc_uuid,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Location not found'}), 404

            # Build update query dynamically
            allowed_fields = [
                'loc_name', 'aka_name', 'state', 'type', 'sub_type',
                'street_address', 'city', 'zip_code',
                'lat', 'lon', 'gps_source'
            ]

            update_fields = []
            update_values = []

            for field in allowed_fields:
                if field in data:
                    value = data[field]
                    if isinstance(value, str):
                        value = value.strip() if value else None
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)

            if not update_fields:
                conn.close()
                return jsonify({'error': 'No fields to update'}), 400

            # Add timestamp
            timestamp = normalize_datetime(None)
            update_fields.append("loc_update = ?")
            update_values.append(timestamp)
            update_values.append(loc_uuid)

            # Execute update
            sql = f"UPDATE locations SET {', '.join(update_fields)} WHERE loc_uuid = ?"
            cursor.execute(sql, update_values)
            conn.commit()

            # Fetch updated location
            cursor.execute("SELECT * FROM locations WHERE loc_uuid = ?", (loc_uuid,))
            result = dict(cursor.fetchone())
            conn.close()

            logger.info(f"Updated location: {loc_uuid}")

            return jsonify(result), 200

        except Exception as e:
            logger.error(f"Failed to update location: {e}")
            return jsonify({'error': str(e)}), 500

    else:  # DELETE
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Verify location exists
            cursor.execute("SELECT loc_uuid, loc_name FROM locations WHERE loc_uuid = ?", (loc_uuid,))
            location = cursor.fetchone()
            if not location:
                conn.close()
                return jsonify({'error': 'Location not found'}), 404

            loc_name = location['loc_name']

            # Delete location (cascades to images, videos, documents, urls)
            cursor.execute("DELETE FROM locations WHERE loc_uuid = ?", (loc_uuid,))
            conn.commit()
            conn.close()

            logger.info(f"Deleted location: {loc_name} ({loc_uuid})")

            return jsonify({'success': True, 'message': f'Deleted location: {loc_name}'}), 200

        except Exception as e:
            logger.error(f"Failed to delete location: {e}")
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
    from scripts.api_maps import api_maps

    app.register_blueprint(api_v012)
    app.register_blueprint(api_maps)
    logger.info("Registered v0.1.2 API routes")
    logger.info("Registered map import API routes")
