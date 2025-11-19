#!/usr/bin/env python3
"""
AUPAT v0.1.0 Import API Routes

Endpoints:
- POST /api/import - Import media files with location

LILBITS: One function - import API
"""

from flask import Blueprint, request, jsonify
from pathlib import Path

from scripts.import_location import create_location, lookup_location, create_sub_location
from scripts.import_media import import_file


# Create blueprint
import_bp = Blueprint('import_v010', __name__)


@import_bp.route('/import', methods=['POST'])
def api_import():
    """
    Import media file(s) with location.

    Request Body:
    {
        "file_path": "/path/to/file.jpg",  # Single file (required)
        "location": {
            "name": "Old Mill",           # Required
            "state": "NY",                # Required
            "type": "industrial",         # Required
            "loc_short": "oldmill",       # Optional
            "status": "Abandoned",        # Optional
            "explored": "Interior",       # Optional
            "sub_type": "factory",        # Optional
            "street": "123 Main St",      # Optional
            "city": "Buffalo",            # Optional
            "zip_code": "14201",          # Optional
            "county": "Erie",             # Optional
            "region": "Western NY",       # Optional
            "gps": "42.8864, -78.8784",   # Optional
            "import_author": "bryant",    # Optional
            "historical": false           # Optional
        },
        "sub_location": {                  # Optional
            "name": "Basement",
            "loc_short": "basement",
            "is_primary": false
        },
        "delete_source": false             # Optional (default: false)
    }

    Returns:
    {
        "success": true,
        "file_uuid": "abc123def456",
        "loc_uuid": "xyz789abc012",
        "sub_uuid": "sub456xyz789"  # If sub-location created
    }
    """
    try:
        data = request.json

        # Validate required fields
        if not data.get('file_path'):
            return jsonify({'error': 'file_path is required'}), 400

        if not data.get('location'):
            return jsonify({'error': 'location is required'}), 400

        location_data = data['location']

        # Check if location exists (by name lookup)
        loc_name = location_data.get('name')
        if not loc_name:
            return jsonify({'error': 'location.name is required'}), 400

        # Look up existing location
        existing_locs = lookup_location(loc_name)
        loc_uuid = None
        loc_short = None

        if existing_locs:
            # Use first match (exact match logic could be added)
            loc = existing_locs[0]
            loc_uuid = loc['loc_uuid']
            loc_short = loc['loc_short']
        else:
            # Create new location
            state = location_data.get('state')
            location_type = location_data.get('type')

            if not state:
                return jsonify({'error': 'location.state is required'}), 400
            if not location_type:
                return jsonify({'error': 'location.type is required'}), 400

            loc_uuid, loc_short = create_location(
                name=loc_name,
                state=state,
                location_type=location_type,
                loc_short=location_data.get('loc_short'),
                status=location_data.get('status'),
                explored=location_data.get('explored'),
                sub_type=location_data.get('sub_type'),
                street=location_data.get('street'),
                city=location_data.get('city'),
                zip_code=location_data.get('zip_code'),
                county=location_data.get('county'),
                region=location_data.get('region'),
                gps=location_data.get('gps'),
                import_author=location_data.get('import_author'),
                historical=location_data.get('historical', False)
            )

        # Handle sub-location if provided
        sub_uuid = None
        if data.get('sub_location'):
            sub_data = data['sub_location']
            sub_name = sub_data.get('name')
            if sub_name:
                sub_uuid = create_sub_location(
                    loc_uuid=loc_uuid,
                    sub_name=sub_name,
                    sub_short=sub_data.get('sub_short'),
                    is_primary=sub_data.get('is_primary', False)
                )

        # Import file
        success, file_uuid, error = import_file(
            file_path=data['file_path'],
            loc_uuid=loc_uuid,
            loc_short=loc_short,
            state=location_data.get('state'),
            location_type=location_data.get('type'),
            sub_uuid=sub_uuid,
            delete_source=data.get('delete_source', False)
        )

        if not success:
            return jsonify({'error': error}), 400

        response = {
            'success': True,
            'file_uuid': file_uuid,
            'loc_uuid': loc_uuid
        }

        if sub_uuid:
            response['sub_uuid'] = sub_uuid

        return jsonify(response), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@import_bp.route('/locations/search', methods=['GET'])
def api_search_locations():
    """
    Search locations by name (for autocomplete).

    Query Parameters:
    - q: Search query

    Returns:
    [
        {
            "loc_uuid": "abc123def456",
            "loc_name": "Old Mill",
            "loc_short": "oldmill",
            "state": "ny",
            "type": "industrial"
        }
    ]
    """
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify([]), 200

        results = lookup_location(query)
        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
