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


@api_v012.route('/locations/<loc_uuid>/import/bulk', methods=['POST'])
def bulk_import_media_to_location(loc_uuid):
    """
    Bulk import media from a source directory using archive scripts workflow.

    This implements the EXACT workflow from archive/v0.1.0/scripts:
    1. Backup database (backup.py)
    2. Import to staging with SHA256 deduplication (db_import_v012.py)
    3. Extract metadata & categorize by hardware (db_organize.py)
    4. Create organized folder structure (db_folder.py)
    5. Move to archive with hardlinks (db_ingest.py)
    6. Verify integrity with SHA256 checks (db_verify.py)

    Args:
        loc_uuid: Location UUID

    Request JSON:
        {
            "source_path": "/path/to/media/directory",
            "author": "Optional import author name"
        }

    Returns:
        JSON with import statistics and batch ID for tracking
    """
    import json
    import subprocess
    import sys
    import os
    import tempfile
    from pathlib import Path
    from scripts.import_helpers import (
        load_user_config,
        create_backup_for_import,
        create_import_batch,
        update_import_batch,
        complete_import_batch
    )

    batch_id = None

    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        source_path = data.get('source_path', '').strip()
        author = data.get('author', '').strip() or 'web-import'

        if not source_path:
            return jsonify({'error': 'source_path is required'}), 400

        # Validate source directory exists
        source_dir = Path(source_path)
        if not source_dir.exists():
            return jsonify({'error': f'Source directory not found: {source_path}'}), 404

        if not source_dir.is_dir():
            return jsonify({'error': f'Path is not a directory: {source_path}'}), 400

        # Validate location exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT loc_name FROM locations WHERE loc_uuid = ?", (loc_uuid,))
        loc_row = cursor.fetchone()
        if not loc_row:
            conn.close()
            return jsonify({'error': 'Location not found'}), 404

        loc_name = loc_row[0]
        conn.close()

        logger.info(f"Starting 6-step bulk import for location {loc_uuid} ({loc_name})")
        logger.info(f"Source: {source_path}")
        logger.info(f"Author: {author}")

        # Load user config
        try:
            user_config = load_user_config()
        except Exception as e:
            return jsonify({
                'error': 'Configuration error',
                'message': str(e)
            }), 500

        db_path = user_config.get('db_loc')
        staging_dir = user_config.get('db_ingest')
        archive_dir = user_config.get('arch_loc')

        if not all([db_path, staging_dir, archive_dir]):
            return jsonify({
                'error': 'Configuration incomplete',
                'message': 'user.json must specify db_loc, db_ingest, and arch_loc'
            }), 500

        # STEP 0: Create backup
        logger.info("STEP 0: Creating database backup...")
        backup_success, backup_path, backup_error = create_backup_for_import(user_config)

        if not backup_success:
            logger.warning(f"Backup failed: {backup_error}")
            # Continue anyway - backup failure shouldn't block import

        # STEP 1: Create import batch record
        logger.info("STEP 1: Creating import batch record...")
        batch_id = create_import_batch(db_path, loc_uuid, source_path, backup_path)
        logger.info(f"Import batch created: {batch_id}")

        # Prepare metadata for import scripts
        metadata = {
            'loc_uuid': loc_uuid,
            'loc_name': loc_name,
            'imp_author': author,
            'batch_id': batch_id
        }

        # Create metadata file
        metadata_fd, metadata_path = tempfile.mkstemp(suffix='.json', prefix='aupat_import_meta_')
        config_path = Path(__file__).parent.parent / 'user' / 'user.json'

        try:
            with os.fdopen(metadata_fd, 'w') as f:
                json.dump(metadata, f)

            scripts_dir = Path(__file__).parent
            workflow_steps = [
                ('STEP 2: Import to staging', 'db_import_v012.py', ['--source', str(source_path), '--metadata', metadata_path, '--config', str(config_path)]),
                ('STEP 3: Organize and categorize', 'db_organize.py', ['--loc-uuid', loc_uuid, '--config', str(config_path)]),
                ('STEP 4: Create archive folders', 'db_folder.py', ['--loc-uuid', loc_uuid, '--config', str(config_path)]),
                ('STEP 5: Ingest to archive', 'db_ingest.py', ['--loc-uuid', loc_uuid, '--config', str(config_path)]),
                ('STEP 6: Verify integrity', 'db_verify.py', ['--loc-uuid', loc_uuid, '--config', str(config_path)])
            ]

            workflow_results = []

            for step_name, script_name, script_args in workflow_steps:
                logger.info(f"{step_name}...")

                script_path = scripts_dir / script_name
                if not script_path.exists():
                    logger.warning(f"Script not found: {script_path} - skipping")
                    workflow_results.append({
                        'step': step_name,
                        'status': 'skipped',
                        'reason': 'script not found'
                    })
                    continue

                # Run the workflow step
                result = subprocess.run(
                    [sys.executable, str(script_path)] + script_args,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout per step
                )

                if result.returncode == 0:
                    logger.info(f"{step_name} completed successfully")
                    workflow_results.append({
                        'step': step_name,
                        'status': 'success',
                        'output': result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
                    })
                else:
                    logger.error(f"{step_name} failed")
                    logger.error(f"STDERR: {result.stderr}")
                    workflow_results.append({
                        'step': step_name,
                        'status': 'error',
                        'error': result.stderr,
                        'output': result.stdout
                    })

                    # Update batch with partial status
                    error_log = f"{step_name} failed: {result.stderr}"
                    complete_import_batch(db_path, batch_id, status='partial', error_log=error_log)

                    return jsonify({
                        'status': 'partial',
                        'message': f'{step_name} failed - import partially completed',
                        'batch_id': batch_id,
                        'location_uuid': loc_uuid,
                        'source_path': source_path,
                        'backup_path': backup_path,
                        'workflow_results': workflow_results
                    }), 500

            # All steps completed successfully
            logger.info(f"All 6 workflow steps completed successfully for {loc_uuid}")
            complete_import_batch(db_path, batch_id, status='completed')

            return jsonify({
                'status': 'success',
                'message': 'All 6 workflow steps completed successfully',
                'batch_id': batch_id,
                'location_uuid': loc_uuid,
                'source_path': source_path,
                'backup_path': backup_path,
                'workflow_results': workflow_results
            }), 200

        finally:
            # Clean up metadata file
            if os.path.exists(metadata_path):
                try:
                    os.unlink(metadata_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up metadata file: {e}")

    except subprocess.TimeoutExpired:
        logger.error(f"Bulk import timed out after 1 hour for {loc_uuid}")
        if batch_id:
            from scripts.import_helpers import complete_import_batch
            db_path = current_app.config.get('DB_PATH')
            complete_import_batch(db_path, batch_id, status='failed', error_log='Import timed out after 1 hour')
        return jsonify({
            'status': 'error',
            'message': 'Import timed out after 1 hour',
            'batch_id': batch_id
        }), 500

    except Exception as e:
        logger.error(f"Bulk import failed: {e}")
        if batch_id:
            from scripts.import_helpers import complete_import_batch
            db_path = current_app.config.get('DB_PATH')
            complete_import_batch(db_path, batch_id, status='failed', error_log=str(e))
        return jsonify({
            'status': 'error',
            'message': str(e),
            'batch_id': batch_id
        }), 500


@api_v012.route('/config', methods=['GET'])
def get_config():
    """
    Get user configuration paths.

    Returns:
        JSON with configuration paths (staging, archive, backup)
    """
    import json
    from pathlib import Path

    try:
        config_path = Path(__file__).parent.parent / 'user' / 'user.json'

        if not config_path.exists():
            return jsonify({
                'configured': False,
                'message': 'user.json not found. Please create configuration file.',
                'template_path': str(Path(__file__).parent.parent / 'user' / 'user.json.template')
            }), 404

        with open(config_path, 'r') as f:
            config = json.load(f)

        return jsonify({
            'configured': True,
            'db_path': config.get('db_loc'),
            'staging_path': config.get('db_ingest'),
            'archive_path': config.get('arch_loc'),
            'backup_path': config.get('db_backup')
        }), 200

    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/import/batches', methods=['GET'])
def list_import_batches():
    """
    List all import batches with optional filtering.

    Query parameters:
        loc_uuid: Filter by location UUID
        status: Filter by status (running/completed/failed/partial)
        limit: Maximum number of results (default 50)
        offset: Result offset for pagination (default 0)

    Returns:
        JSON with list of import batches
    """
    try:
        loc_uuid = request.args.get('loc_uuid')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM import_batches WHERE 1=1"
        params = []

        if loc_uuid:
            query += " AND loc_uuid = ?"
            params.append(loc_uuid)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY batch_start DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        batches = [dict(row) for row in rows]
        conn.close()

        return jsonify({
            'batches': batches,
            'count': len(batches),
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        logger.error(f"Failed to list import batches: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/import/batches/<batch_id>', methods=['GET'])
def get_import_batch_status(batch_id):
    """
    Get detailed status for a specific import batch.

    Args:
        batch_id: Import batch UUID

    Returns:
        JSON with batch details and statistics
    """
    from scripts.import_helpers import get_import_batch_status

    try:
        db_path = current_app.config.get('DB_PATH')
        batch = get_import_batch_status(db_path, batch_id)

        if not batch:
            return jsonify({'error': 'Import batch not found'}), 404

        return jsonify(batch), 200

    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        return jsonify({'error': str(e)}), 500


@api_v012.route('/import/batches/<batch_id>/logs', methods=['GET'])
def get_import_batch_logs(batch_id):
    """
    Get import logs for a specific batch.

    Args:
        batch_id: Import batch UUID

    Query parameters:
        stage: Filter by stage (staging/organize/folder/ingest/verify)
        status: Filter by status (success/failed/skipped/duplicate)

    Returns:
        JSON with list of import log entries
    """
    from scripts.import_helpers import get_import_log_for_batch

    try:
        db_path = current_app.config.get('DB_PATH')
        stage = request.args.get('stage')
        status = request.args.get('status')

        logs = get_import_log_for_batch(db_path, batch_id, stage, status)

        return jsonify({
            'batch_id': batch_id,
            'logs': logs,
            'count': len(logs)
        }), 200

    except Exception as e:
        logger.error(f"Failed to get batch logs: {e}")
        return jsonify({'error': str(e)}), 500


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
            imp_author = (data.get('imp_author') or '').strip() or None

            # Check for name collision
            cursor.execute("SELECT loc_uuid FROM locations WHERE LOWER(loc_name) = LOWER(?)", (loc_name,))
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return jsonify({'error': 'A location with this name already exists', 'collision': True}), 409

            # Insert location
            cursor.execute(
                """
                INSERT INTO locations (
                    loc_uuid, loc_name, aka_name, state, type, sub_type,
                    street_address, city, zip_code,
                    lat, lon, gps_source, imp_author,
                    loc_add, loc_update
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    loc_uuid, loc_name, aka_name, state, loc_type, sub_type,
                    street_address, city, zip_code,
                    lat, lon, gps_source, imp_author,
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
            logger.info(f"[API] PUT request received for location {loc_uuid}")

            data = request.get_json()
            logger.debug(f"[API] Request data: {data}")

            if not data:
                logger.warning("[API] No request body provided")
                return jsonify({'error': 'Request body is required'}), 400

            from scripts.normalize import normalize_datetime

            conn = get_db_connection()
            cursor = conn.cursor()

            # Verify location exists
            logger.debug(f"[API] Verifying location exists: {loc_uuid}")
            cursor.execute("SELECT loc_uuid, loc_name FROM locations WHERE loc_uuid = ?", (loc_uuid,))
            existing = cursor.fetchone()
            if not existing:
                logger.warning(f"[API] Location not found: {loc_uuid}")
                conn.close()
                return jsonify({'error': 'Location not found'}), 404

            logger.info(f"[API] Updating location: {existing['loc_name']} ({loc_uuid})")

            # Build update query dynamically
            allowed_fields = [
                'loc_name', 'aka_name', 'state', 'type', 'sub_type',
                'street_address', 'city', 'zip_code',
                'lat', 'lon', 'gps_source', 'imp_author'
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

            logger.debug(f"[API] Fields to update: {update_fields}")

            if not update_fields:
                logger.warning("[API] No fields to update in request")
                conn.close()
                return jsonify({'error': 'No fields to update'}), 400

            # Validate required fields if they're being updated
            if 'loc_name' in data:
                if not data['loc_name'] or not data['loc_name'].strip():
                    logger.warning("[API] Invalid update: loc_name cannot be empty")
                    conn.close()
                    return jsonify({'error': 'loc_name cannot be empty'}), 400

            if 'state' in data:
                if not data['state'] or not data['state'].strip():
                    logger.warning("[API] Invalid update: state cannot be empty")
                    conn.close()
                    return jsonify({'error': 'state cannot be empty'}), 400

            if 'type' in data:
                if not data['type'] or not data['type'].strip():
                    logger.warning("[API] Invalid update: type cannot be empty")
                    conn.close()
                    return jsonify({'error': 'type cannot be empty'}), 400

            # Add timestamp
            timestamp = normalize_datetime(None)
            update_fields.append("loc_update = ?")
            update_values.append(timestamp)
            update_values.append(loc_uuid)

            # Execute update
            sql = f"UPDATE locations SET {', '.join(update_fields)} WHERE loc_uuid = ?"
            logger.debug(f"[API] Executing SQL: {sql}")
            logger.debug(f"[API] With values: {update_values}")

            cursor.execute(sql, update_values)
            conn.commit()
            logger.info(f"[API] Database update committed")

            # Fetch updated location
            cursor.execute("SELECT * FROM locations WHERE loc_uuid = ?", (loc_uuid,))
            result = dict(cursor.fetchone())
            conn.close()

            logger.info(f"[API] Successfully updated location: {loc_uuid}")

            return jsonify(result), 200

        except Exception as e:
            logger.error(f"[API] Failed to update location {loc_uuid}: {str(e)}")
            logger.error(f"[API] Error type: {type(e).__name__}")
            logger.error(f"[API] Error details: {repr(e)}")
            import traceback
            logger.error(f"[API] Traceback: {traceback.format_exc()}")
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


@api_v012.route('/locations/autocomplete/<field>', methods=['GET'])
def location_autocomplete(field):
    """
    Get autocomplete suggestions for location fields.

    Supported fields: type, sub_type, state, imp_author

    Query params:
        type: Filter sub_type by type (optional, for sub_type field only)
        limit: Max number of results (default: 20)

    Returns:
        JSON array of distinct values with counts, ordered by frequency
    """
    try:
        allowed_fields = ['type', 'sub_type', 'state', 'imp_author', 'city']
        if field not in allowed_fields:
            return jsonify({'error': f'Invalid field. Allowed: {", ".join(allowed_fields)}'}), 400

        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # Cap at 100

        conn = get_db_connection()
        cursor = conn.cursor()

        # For sub_type, optionally filter by type
        if field == 'sub_type':
            type_filter = request.args.get('type')
            if type_filter:
                cursor.execute(f"""
                    SELECT {field}, COUNT(*) as count
                    FROM locations
                    WHERE {field} IS NOT NULL
                    AND {field} != ''
                    AND type = ?
                    GROUP BY LOWER({field})
                    ORDER BY count DESC, {field} ASC
                    LIMIT ?
                """, (type_filter.lower(), limit))
            else:
                cursor.execute(f"""
                    SELECT {field}, COUNT(*) as count
                    FROM locations
                    WHERE {field} IS NOT NULL
                    AND {field} != ''
                    GROUP BY LOWER({field})
                    ORDER BY count DESC, {field} ASC
                    LIMIT ?
                """, (limit,))
        else:
            cursor.execute(f"""
                SELECT {field}, COUNT(*) as count
                FROM locations
                WHERE {field} IS NOT NULL
                AND {field} != ''
                GROUP BY LOWER({field})
                ORDER BY count DESC, {field} ASC
                LIMIT ?
            """, (limit,))

        results = [{'value': row[field], 'count': row['count']} for row in cursor.fetchall()]
        conn.close()

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Failed to fetch autocomplete for {field}: {e}")
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
    from scripts.api_routes_bookmarks import bookmarks_bp

    app.register_blueprint(api_v012)
    app.register_blueprint(api_maps)
    app.register_blueprint(bookmarks_bp)
    logger.info("Registered v0.1.2 API routes")
    logger.info("Registered map import API routes")
    logger.info("Registered bookmarks API routes")
