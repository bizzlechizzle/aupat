"""
AUPAT Map Import API Routes
REST API endpoints for map import functionality.

Provides endpoints for:
- Uploading and parsing map files (CSV, GeoJSON)
- Full import mode (import all data to locations table)
- Reference mode (store maps for fuzzy matching)
- Duplicate detection and preview
- Reference map searching

Version: 0.1.3
Last Updated: 2025-11-17
"""

import logging
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from pathlib import Path

from scripts.map_import import (
    parse_csv_map,
    parse_geojson_map,
    parse_kml_map,
    find_duplicates,
    import_locations_to_db,
    search_reference_maps,
    generate_short_uuid
)

logger = logging.getLogger(__name__)

# Create Blueprint for map import API routes
api_maps = Blueprint('api_maps', __name__, url_prefix='/api/maps')


# Enable CORS for API routes
@api_maps.after_request
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


@api_maps.route('/parse', methods=['POST'])
def parse_map_file():
    """
    Parse a map file and return preview of locations.

    Does NOT import into database - just parses and validates.

    Request JSON:
        {
            "filename": "my_map.csv",
            "format": "csv" | "geojson",
            "content": "file content as string"
        }

    Returns:
        JSON with:
        - locations: List of parsed locations
        - errors: List of parsing errors
        - statistics: Count of valid/invalid entries
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        filename = data.get('filename', '')
        file_format = data.get('format', '').lower()
        content = data.get('content', '')

        if not content:
            return jsonify({'error': 'No file content provided'}), 400

        # Auto-detect format if not specified
        if not file_format:
            if filename.endswith('.csv'):
                file_format = 'csv'
            elif filename.endswith('.json') or filename.endswith('.geojson'):
                file_format = 'geojson'
            elif filename.endswith('.kml'):
                file_format = 'kml'
            elif filename.endswith('.kmz'):
                file_format = 'kmz'
            else:
                return jsonify({'error': 'Unknown file format. Use .csv, .json, .geojson, .kml, or .kmz'}), 400

        # Parse based on format
        if file_format == 'csv':
            locations, errors = parse_csv_map(content)
        elif file_format in ['geojson', 'json']:
            locations, errors = parse_geojson_map(content)
        elif file_format == 'kml':
            # KML/KMZ requires bytes, not string
            content_bytes = content.encode('utf-8') if isinstance(content, str) else content
            locations, errors = parse_kml_map(content_bytes, is_kmz=False)
        elif file_format == 'kmz':
            # KMZ is binary, ensure we have bytes
            content_bytes = content if isinstance(content, bytes) else content.encode('utf-8')
            locations, errors = parse_kml_map(content_bytes, is_kmz=True)
        else:
            return jsonify({'error': f'Unsupported format: {file_format}'}), 400

        # Calculate statistics
        total = len(locations) + len([e for e in errors if 'Missing required' in e])
        has_gps = sum(1 for loc in locations if loc.get('lat') and loc.get('lon'))
        has_state = sum(1 for loc in locations if loc.get('state'))

        return jsonify({
            'success': True,
            'locations': locations,
            'errors': errors,
            'statistics': {
                'total_rows': total,
                'valid_locations': len(locations),
                'invalid_rows': len(errors),
                'with_gps': has_gps,
                'with_state': has_state,
                'format': file_format
            }
        }), 200

    except Exception as e:
        logger.error(f"Map parsing failed: {e}")
        return jsonify({'error': str(e)}), 500


@api_maps.route('/check-duplicates', methods=['POST'])
def check_duplicates():
    """
    Check parsed locations for duplicates in database.

    Request JSON:
        {
            "locations": [
                {
                    "name": "Old Mill",
                    "state": "AZ",
                    "lat": 34.9,
                    "lon": -111.8,
                    ...
                },
                ...
            ]
        }

    Returns:
        JSON with duplicate analysis for each location
    """
    try:
        data = request.get_json()

        if not data or not data.get('locations'):
            return jsonify({'error': 'No locations provided'}), 400

        locations = data['locations']

        conn = get_db_connection()
        cursor = conn.cursor()

        results = []
        total_duplicates = 0

        for idx, location in enumerate(locations):
            duplicates = find_duplicates(cursor, location)

            if duplicates:
                total_duplicates += 1

            results.append({
                'index': idx,
                'name': location.get('name'),
                'state': location.get('state'),
                'duplicates': duplicates,
                'has_duplicates': len(duplicates) > 0
            })

        conn.close()

        return jsonify({
            'success': True,
            'results': results,
            'statistics': {
                'total_checked': len(locations),
                'with_duplicates': total_duplicates,
                'duplicate_rate': round(total_duplicates / len(locations) * 100, 1) if locations else 0
            }
        }), 200

    except Exception as e:
        logger.error(f"Duplicate check failed: {e}")
        return jsonify({'error': str(e)}), 500


@api_maps.route('/import', methods=['POST'])
def import_map():
    """
    Import a map file into the database.

    Supports two modes:
    - full: Import all locations into main locations table
    - reference: Store in map_locations table for reference matching

    Request JSON:
        {
            "filename": "my_map.csv",
            "format": "csv" | "geojson",
            "mode": "full" | "reference",
            "content": "file content",
            "description": "Optional description",
            "skip_duplicates": true
        }

    Returns:
        JSON with import results and statistics
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        filename = data.get('filename', 'unknown')
        file_format = data.get('format', '').lower()
        import_mode = data.get('mode', 'full').lower()
        content = data.get('content', '')
        description = data.get('description', '')
        skip_duplicates = data.get('skip_duplicates', True)

        # Validate mode
        if import_mode not in ['full', 'reference']:
            return jsonify({'error': 'Mode must be "full" or "reference"'}), 400

        # Parse file
        if file_format == 'csv':
            locations, parse_errors = parse_csv_map(content)
        elif file_format in ['geojson', 'json']:
            locations, parse_errors = parse_geojson_map(content)
        elif file_format == 'kml':
            content_bytes = content.encode('utf-8') if isinstance(content, str) else content
            locations, parse_errors = parse_kml_map(content_bytes, is_kmz=False)
        elif file_format == 'kmz':
            content_bytes = content if isinstance(content, bytes) else content.encode('utf-8')
            locations, parse_errors = parse_kml_map(content_bytes, is_kmz=True)
        else:
            return jsonify({'error': f'Unsupported format: {file_format}. Use csv, geojson, kml, or kmz'}), 400

        if not locations:
            return jsonify({
                'error': 'No valid locations found in file',
                'parse_errors': parse_errors
            }), 400

        # Import to database
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Create import record
            map_id = generate_short_uuid()
            timestamp = datetime.utcnow().isoformat() + 'Z'

            cursor.execute(
                """
                INSERT INTO google_maps_exports (
                    export_id, import_date, file_path, filename,
                    import_mode, file_format, import_status,
                    source_description, locations_found
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    map_id,
                    timestamp,
                    filename,  # Store filename in file_path for now
                    filename,
                    import_mode,
                    file_format,
                    'processing',
                    description,
                    len(locations)
                )
            )

            # Import locations
            stats = import_locations_to_db(
                cursor,
                locations,
                map_id,
                import_mode=import_mode,
                skip_duplicates=skip_duplicates
            )

            # Update import record with results
            cursor.execute(
                """
                UPDATE google_maps_exports
                SET import_status = ?,
                    locations_imported = ?,
                    locations_skipped = ?,
                    duplicates_found = ?
                WHERE export_id = ?
                """,
                (
                    'completed' if not stats['errors'] else 'completed_with_errors',
                    stats['imported'],
                    stats['skipped'],
                    stats['duplicates'],
                    map_id
                )
            )

            conn.commit()

            return jsonify({
                'success': True,
                'map_id': map_id,
                'mode': import_mode,
                'statistics': stats,
                'parse_errors': parse_errors
            }), 200

        except Exception as e:
            conn.rollback()
            raise

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Map import failed: {e}")
        return jsonify({'error': str(e)}), 500


@api_maps.route('/list', methods=['GET'])
def list_imported_maps():
    """
    Get list of all imported maps.

    Returns:
        JSON array of imported map records
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                export_id, import_date, filename, import_mode,
                file_format, import_status, source_description,
                locations_found, locations_imported, locations_skipped,
                duplicates_found
            FROM google_maps_exports
            ORDER BY import_date DESC
            """
        )

        maps = []
        for row in cursor.fetchall():
            maps.append({
                'map_id': row[0],
                'import_date': row[1],
                'filename': row[2],
                'mode': row[3],
                'format': row[4],
                'status': row[5],
                'description': row[6],
                'locations_found': row[7],
                'locations_imported': row[8],
                'locations_skipped': row[9],
                'duplicates_found': row[10]
            })

        conn.close()

        return jsonify({
            'success': True,
            'maps': maps,
            'total': len(maps)
        }), 200

    except Exception as e:
        logger.error(f"Failed to list maps: {e}")
        return jsonify({'error': str(e)}), 500


@api_maps.route('/<map_id>', methods=['GET', 'DELETE'])
def manage_map(map_id):
    """
    Get details or delete an imported map.

    GET: Returns map details and statistics
    DELETE: Removes map and optionally associated locations

    Query parameters for DELETE:
        - delete_locations: true|false (delete associated locations, default: false)

    Returns:
        JSON with map details or deletion confirmation
    """
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get map details
            cursor.execute(
                """
                SELECT * FROM google_maps_exports
                WHERE export_id = ?
                """,
                (map_id,)
            )

            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({'error': 'Map not found'}), 404

            map_data = dict(row)

            # Get associated locations count
            if row['import_mode'] == 'full':
                cursor.execute(
                    "SELECT COUNT(*) FROM locations WHERE source_map_id = ?",
                    (map_id,)
                )
            else:  # reference mode
                cursor.execute(
                    "SELECT COUNT(*) FROM map_locations WHERE map_id = ?",
                    (map_id,)
                )

            current_locations = cursor.fetchone()[0]

            conn.close()

            return jsonify({
                'success': True,
                'map': map_data,
                'current_locations': current_locations
            }), 200

        except Exception as e:
            logger.error(f"Failed to get map details: {e}")
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            delete_locations = request.args.get('delete_locations', 'false').lower() == 'true'

            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if map exists
            cursor.execute(
                "SELECT import_mode FROM google_maps_exports WHERE export_id = ?",
                (map_id,)
            )
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({'error': 'Map not found'}), 404

            import_mode = row[0]

            # Delete associated locations if requested
            deleted_locations = 0
            if delete_locations:
                if import_mode == 'full':
                    cursor.execute(
                        "DELETE FROM locations WHERE source_map_id = ?",
                        (map_id,)
                    )
                else:  # reference mode
                    cursor.execute(
                        "DELETE FROM map_locations WHERE map_id = ?",
                        (map_id,)
                    )
                deleted_locations = cursor.rowcount

            # Delete map record (will cascade delete map_locations if not already deleted)
            cursor.execute(
                "DELETE FROM google_maps_exports WHERE export_id = ?",
                (map_id,)
            )

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Map deleted successfully',
                'deleted_locations': deleted_locations
            }), 200

        except Exception as e:
            logger.error(f"Failed to delete map: {e}")
            return jsonify({'error': str(e)}), 500


@api_maps.route('/search', methods=['GET'])
def search_maps():
    """
    Search reference maps for location matches.

    Query parameters:
        - q: Location name to search for (required)
        - state: Optional state filter (2-letter code)
        - limit: Maximum results (default: 5)

    Returns:
        JSON array of matching locations from reference maps
    """
    try:
        query = request.args.get('q', '').strip()
        state = request.args.get('state', '').strip().upper() or None
        limit = int(request.args.get('limit', 5))

        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        matches = search_reference_maps(cursor, query, state, limit)

        conn.close()

        return jsonify({
            'success': True,
            'query': query,
            'state': state,
            'matches': matches,
            'count': len(matches)
        }), 200

    except Exception as e:
        logger.error(f"Map search failed: {e}")
        return jsonify({'error': str(e)}), 500
