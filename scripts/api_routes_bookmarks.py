"""
AUPAT Core API - Bookmark Management Endpoints

Handles bookmark CRUD operations for browser integration.
Bookmarks can be associated with locations and organized in folders.

Version: 0.1.2-browser
Last Updated: 2025-11-18
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

# Validation limits
MAX_URL_LENGTH = 2048  # RFC 7230
MAX_TAGS_COUNT = 50
MAX_FOLDER_DEPTH = 10

# Create blueprint
bookmarks_bp = Blueprint('bookmarks', __name__)


def get_db_connection():
    """
    Get database connection with proper settings.

    Returns:
        sqlite3.Connection with row_factory configured
    """
    db_path = current_app.config.get('DB_PATH', 'data/aupat.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_pagination_response(data, total, limit, offset, data_key='data'):
    """
    Create standardized pagination response.

    Args:
        data: List of items
        total: Total count of items
        limit: Limit per page
        offset: Current offset
        data_key: Key name for data array (default: 'data')

    Returns:
        dict: Standardized response with pagination metadata
    """
    return {
        data_key: data,
        'pagination': {
            'limit': limit,
            'offset': offset,
            'total': total,
            'has_more': offset + limit < total
        }
    }


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        True if valid HTTP/HTTPS URL, False otherwise
    """
    if not url:
        return False

    url = url.strip()

    # Check protocol
    if not (url.startswith('http://') or url.startswith('https://')):
        return False

    # Check length (max 2048 chars per RFC 7230)
    if len(url) > 2048:
        return False

    return True


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format.

    Args:
        uuid_str: UUID string to validate

    Returns:
        True if valid UUID format, False otherwise
    """
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


@bookmarks_bp.route('/api/bookmarks', methods=['POST'])
def create_bookmark():
    """
    Create a new bookmark.

    Request body (JSON):
        {
          "url": "https://example.com",
          "title": "Example Site",
          "description": "Optional description",
          "loc_uuid": "abc-123",  // Optional
          "folder": "Research/NY",  // Optional
          "tags": ["instagram", "photos"]  // Optional
        }

    Returns:
        201: Bookmark created
        400: Invalid input
        500: Database error
    """
    try:
        data = request.json

        # Validate required fields
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400

        url = data['url'].strip()
        if not validate_url(url):
            return jsonify({'error': 'Invalid URL format (must start with http:// or https://)'}), 400

        # Validate optional loc_uuid
        loc_uuid = data.get('loc_uuid')
        if loc_uuid and not validate_uuid(loc_uuid):
            return jsonify({'error': 'Invalid location UUID format'}), 400

        # Generate bookmark UUID
        bookmark_uuid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'

        # Extract fields
        title = data.get('title')
        description = data.get('description')
        folder = data.get('folder')
        tags = data.get('tags', [])

        # Ensure tags is JSON string
        tags_json = json.dumps(tags) if isinstance(tags, list) else tags

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO bookmarks (
                    bookmark_uuid, loc_uuid, url, title, description,
                    folder, tags, created_at, updated_at, visit_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bookmark_uuid,
                loc_uuid,
                url,
                title,
                description,
                folder,
                tags_json,
                now,
                now,
                0
            ))

            conn.commit()

            logger.info(f"Created bookmark {bookmark_uuid} for URL: {url}")

            return jsonify({
                'bookmark_uuid': bookmark_uuid,
                'url': url,
                'created_at': now
            }), 201

        except sqlite3.IntegrityError as e:
            logger.error(f"Database integrity error creating bookmark: {e}")
            return jsonify({'error': 'Database constraint violation'}), 400

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error creating bookmark: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/api/bookmarks', methods=['GET'])
def list_bookmarks():
    """
    List bookmarks with optional filtering.

    Query parameters:
        folder: Filter by folder (exact match)
        loc_uuid: Filter by location UUID
        search: Search in title/description/URL
        limit: Max results (default 50, max 500)
        offset: Pagination offset (default 0)
        order: Sort order: 'created' (default), 'updated', 'title', 'visits'

    Returns:
        200: List of bookmarks
        400: Invalid parameters
        500: Database error
    """
    try:
        folder = request.args.get('folder')
        loc_uuid = request.args.get('loc_uuid')
        search = request.args.get('search')
        limit = min(int(request.args.get('limit', 50)), 500)
        offset = int(request.args.get('offset', 0))
        order = request.args.get('order', 'created')

        # Validate limit and offset
        if limit < 1 or offset < 0:
            return jsonify({'error': 'Invalid limit or offset'}), 400

        # Validate order parameter
        order_map = {
            'created': 'created_at DESC',
            'updated': 'updated_at DESC',
            'title': 'title ASC',
            'visits': 'visit_count DESC'
        }
        if order not in order_map:
            return jsonify({'error': 'Invalid order parameter'}), 400

        order_clause = order_map[order]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM bookmarks WHERE 1=1"
        params = []

        if folder:
            query += " AND folder = ?"
            params.append(folder)

        if loc_uuid:
            if not validate_uuid(loc_uuid):
                return jsonify({'error': 'Invalid location UUID'}), 400
            query += " AND loc_uuid = ?"
            params.append(loc_uuid)

        if search:
            query += " AND (title LIKE ? OR description LIKE ? OR url LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        # Use window function to get total count in single query
        query_with_count = query.replace("SELECT *", "SELECT *, COUNT(*) OVER() as total_count", 1)
        query_with_count += f" ORDER BY {order_clause} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query_with_count, params)
        rows = cursor.fetchall()

        bookmarks = []
        total = 0
        for row in rows:
            bookmark = dict(row)
            # Extract total count from first row
            total = bookmark.pop('total_count', 0)

            # Parse tags JSON
            if bookmark.get('tags'):
                try:
                    bookmark['tags'] = json.loads(bookmark['tags'])
                except json.JSONDecodeError:
                    bookmark['tags'] = []
            else:
                bookmark['tags'] = []

            bookmarks.append(bookmark)

        conn.close()

        return jsonify(create_pagination_response(
            data=bookmarks,
            total=total,
            limit=limit,
            offset=offset
        )), 200

    except ValueError:
        return jsonify({'error': 'Invalid limit or offset format'}), 400
    except Exception as e:
        logger.error(f"Error listing bookmarks: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/api/bookmarks/<bookmark_uuid>', methods=['GET'])
def get_bookmark(bookmark_uuid):
    """
    Get a single bookmark by UUID.

    Args:
        bookmark_uuid: Bookmark UUID

    Returns:
        200: Bookmark data
        400: Invalid UUID
        404: Bookmark not found
        500: Database error
    """
    try:
        if not validate_uuid(bookmark_uuid):
            return jsonify({'error': 'Invalid bookmark UUID format'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM bookmarks WHERE bookmark_uuid = ?", (bookmark_uuid,))
        row = cursor.fetchone()

        conn.close()

        if not row:
            return jsonify({'error': 'Bookmark not found'}), 404

        bookmark = dict(row)

        # Parse tags JSON
        if bookmark.get('tags'):
            try:
                bookmark['tags'] = json.loads(bookmark['tags'])
            except json.JSONDecodeError:
                bookmark['tags'] = []
        else:
            bookmark['tags'] = []

        return jsonify(bookmark), 200

    except Exception as e:
        logger.error(f"Error getting bookmark {bookmark_uuid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/api/bookmarks/<bookmark_uuid>', methods=['PUT'])
def update_bookmark(bookmark_uuid):
    """
    Update a bookmark.

    Args:
        bookmark_uuid: Bookmark UUID

    Request body (JSON):
        {
          "title": "New Title",
          "description": "New description",
          "folder": "New/Folder",
          "tags": ["tag1", "tag2"],
          "loc_uuid": "new-location-uuid"
        }

    All fields are optional. Only provided fields will be updated.

    Returns:
        200: Bookmark updated
        400: Invalid input
        404: Bookmark not found
        500: Database error
    """
    try:
        if not validate_uuid(bookmark_uuid):
            return jsonify({'error': 'Invalid bookmark UUID format'}), 400

        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate loc_uuid if provided
        if 'loc_uuid' in data and data['loc_uuid']:
            if not validate_uuid(data['loc_uuid']):
                return jsonify({'error': 'Invalid location UUID format'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if bookmark exists
        cursor.execute("SELECT bookmark_uuid FROM bookmarks WHERE bookmark_uuid = ?", (bookmark_uuid,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Bookmark not found'}), 404

        # Build update query
        update_fields = []
        params = []

        if 'title' in data:
            update_fields.append('title = ?')
            params.append(data['title'])

        if 'description' in data:
            update_fields.append('description = ?')
            params.append(data['description'])

        if 'folder' in data:
            update_fields.append('folder = ?')
            params.append(data['folder'])

        if 'tags' in data:
            tags_json = json.dumps(data['tags']) if isinstance(data['tags'], list) else data['tags']
            update_fields.append('tags = ?')
            params.append(tags_json)

        if 'loc_uuid' in data:
            update_fields.append('loc_uuid = ?')
            params.append(data['loc_uuid'])

        if not update_fields:
            conn.close()
            return jsonify({'error': 'No valid fields to update'}), 400

        # Always update updated_at
        update_fields.append('updated_at = ?')
        now = datetime.utcnow().isoformat() + 'Z'
        params.append(now)

        # Add bookmark_uuid to params
        params.append(bookmark_uuid)

        query = f"UPDATE bookmarks SET {', '.join(update_fields)} WHERE bookmark_uuid = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()

        logger.info(f"Updated bookmark {bookmark_uuid}")

        return jsonify({
            'bookmark_uuid': bookmark_uuid,
            'updated_at': now
        }), 200

    except Exception as e:
        logger.error(f"Error updating bookmark {bookmark_uuid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/api/bookmarks/<bookmark_uuid>', methods=['DELETE'])
def delete_bookmark(bookmark_uuid):
    """
    Delete a bookmark.

    Args:
        bookmark_uuid: Bookmark UUID

    Returns:
        204: Bookmark deleted
        400: Invalid UUID
        404: Bookmark not found
        500: Database error
    """
    try:
        if not validate_uuid(bookmark_uuid):
            return jsonify({'error': 'Invalid bookmark UUID format'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if bookmark exists
        cursor.execute("SELECT bookmark_uuid FROM bookmarks WHERE bookmark_uuid = ?", (bookmark_uuid,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Bookmark not found'}), 404

        cursor.execute("DELETE FROM bookmarks WHERE bookmark_uuid = ?", (bookmark_uuid,))
        conn.commit()
        conn.close()

        logger.info(f"Deleted bookmark {bookmark_uuid}")

        return '', 204

    except Exception as e:
        logger.error(f"Error deleting bookmark {bookmark_uuid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/api/bookmarks/folders', methods=['GET'])
def list_folders():
    """
    List all unique folders used in bookmarks.

    Returns:
        200: List of folder paths
        500: Database error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT folder
            FROM bookmarks
            WHERE folder IS NOT NULL AND folder != ''
            ORDER BY folder
        """)
        rows = cursor.fetchall()
        conn.close()

        folders = [row['folder'] for row in rows]

        return jsonify({'folders': folders}), 200

    except Exception as e:
        logger.error(f"Error listing folders: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/api/bookmarks/<bookmark_uuid>/visit', methods=['POST'])
def record_visit(bookmark_uuid):
    """
    Record a visit to a bookmark (increment visit count, update last_visited).

    Args:
        bookmark_uuid: Bookmark UUID

    Returns:
        200: Visit recorded
        400: Invalid UUID
        404: Bookmark not found
        500: Database error
    """
    try:
        if not validate_uuid(bookmark_uuid):
            return jsonify({'error': 'Invalid bookmark UUID format'}), 400

        now = datetime.utcnow().isoformat() + 'Z'

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE bookmarks
            SET visit_count = visit_count + 1, last_visited = ?
            WHERE bookmark_uuid = ?
        """, (now, bookmark_uuid))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Bookmark not found'}), 404

        conn.commit()
        conn.close()

        logger.info(f"Recorded visit to bookmark {bookmark_uuid}")

        return jsonify({'last_visited': now}), 200

    except Exception as e:
        logger.error(f"Error recording visit to bookmark {bookmark_uuid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
