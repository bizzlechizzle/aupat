"""
Unit and integration tests for API routes (api_routes_v012.py)

Tests:
- Health check endpoints
- Map markers endpoint
- Location details endpoint
- Location images/videos endpoints
- Search endpoint
- Error handling
- CORS headers
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from flask import Flask
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from api_routes_v012 import api_v012, register_api_routes


@pytest.fixture
def test_app():
    """Create Flask test app with API routes registered."""
    app = Flask(__name__)
    app.config['TESTING'] = True

    # Create temporary database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()

    app.config['DB_PATH'] = db_path

    # Create test database schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE locations (
            loc_uuid TEXT PRIMARY KEY,
            loc_name TEXT NOT NULL,
            lat REAL,
            lon REAL,
            type TEXT,
            state TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE images (
            img_sha256 TEXT PRIMARY KEY,
            img_name TEXT,
            img_loc TEXT,
            immich_asset_id TEXT,
            img_width INTEGER,
            img_height INTEGER,
            img_size_bytes INTEGER,
            gps_lat REAL,
            gps_lon REAL,
            img_hardware TEXT,
            camera INTEGER,
            phone INTEGER,
            drone INTEGER,
            go_pro INTEGER,
            film INTEGER,
            img_add TEXT,
            loc_uuid TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    cursor.execute("""
        CREATE TABLE videos (
            vid_sha256 TEXT PRIMARY KEY,
            vid_name TEXT,
            vid_loc TEXT,
            immich_asset_id TEXT,
            vid_width INTEGER,
            vid_height INTEGER,
            vid_duration_sec REAL,
            vid_size_bytes INTEGER,
            gps_lat REAL,
            gps_lon REAL,
            vid_hardware TEXT,
            camera INTEGER,
            phone INTEGER,
            drone INTEGER,
            go_pro INTEGER,
            dash_cam INTEGER,
            vid_add TEXT,
            loc_uuid TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    cursor.execute("""
        CREATE TABLE documents (
            doc_sha256 TEXT PRIMARY KEY,
            loc_uuid TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    cursor.execute("""
        CREATE TABLE urls (
            url_uuid TEXT PRIMARY KEY,
            url TEXT,
            url_title TEXT,
            url_desc TEXT,
            domain TEXT,
            archivebox_snapshot_id TEXT,
            archive_status TEXT,
            archive_date TEXT,
            media_extracted INTEGER,
            url_add TEXT,
            loc_uuid TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO locations (loc_uuid, loc_name, lat, lon, type, state)
        VALUES
            ('loc-1', 'Test Location 1', 42.7565, -73.9385, 'industrial', 'ny'),
            ('loc-2', 'Test Location 2', 42.8142, -73.9396, 'hospital', 'ny'),
            ('loc-3', 'Test Location 3', NULL, NULL, 'school', 'ny')
    """)

    cursor.execute("""
        INSERT INTO images (
            img_sha256, img_name, img_loc, immich_asset_id,
            img_width, img_height, img_size_bytes,
            gps_lat, gps_lon, camera, phone, img_add, loc_uuid
        )
        VALUES
            ('sha-img-1', 'test1.jpg', '/tmp/test1.jpg', 'asset-1',
             6000, 4000, 15728640, 42.7565, -73.9385, 1, 0, '2024-01-01', 'loc-1'),
            ('sha-img-2', 'test2.jpg', '/tmp/test2.jpg', 'asset-2',
             4000, 3000, 10485760, 42.7565, -73.9385, 0, 1, '2024-01-02', 'loc-1')
    """)

    cursor.execute("""
        INSERT INTO videos (
            vid_sha256, vid_name, vid_loc, immich_asset_id,
            vid_width, vid_height, vid_duration_sec, vid_size_bytes,
            gps_lat, gps_lon, camera, phone, vid_add, loc_uuid
        )
        VALUES
            ('sha-vid-1', 'test1.mp4', '/tmp/test1.mp4', 'asset-v1',
             1920, 1080, 45.5, 104857600, 42.7565, -73.9385, 1, 0, '2024-01-01', 'loc-1')
    """)

    cursor.execute("""
        INSERT INTO urls (
            url_uuid, url, domain, archivebox_snapshot_id,
            archive_status, media_extracted, url_add, loc_uuid
        )
        VALUES
            ('url-1', 'https://example.com', 'example.com', 'snap-123',
             'archived', 5, '2024-01-01', 'loc-1')
    """)

    conn.commit()
    conn.close()

    # Register API routes
    register_api_routes(app)

    yield app

    # Cleanup
    Path(db_path).unlink()


def test_health_check_endpoint(test_app):
    """Test health check endpoint returns correct status."""
    client = test_app.test_client()
    response = client.get('/api/health')

    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['version'] == '0.1.2'
    assert data['database'] == 'connected'
    assert data['location_count'] == 3


def test_health_check_services_endpoint(test_app):
    """Test service health check endpoint."""
    client = test_app.test_client()
    response = client.get('/api/health/services')

    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'services' in data
    assert 'immich' in data['services']
    assert 'archivebox' in data['services']
    # Services will be 'unavailable' since not running, but endpoint should work
    assert data['services']['immich'] in ['healthy', 'unhealthy', 'unavailable']


def test_map_markers_endpoint(test_app):
    """Test map markers endpoint returns locations with GPS."""
    client = test_app.test_client()
    response = client.get('/api/map/markers')

    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 2  # Only 2 locations have GPS

    # Check first marker
    marker = data[0]
    assert 'loc_uuid' in marker
    assert 'loc_name' in marker
    assert 'lat' in marker
    assert 'lon' in marker
    assert 'type' in marker
    assert 'state' in marker


def test_map_markers_with_bounds(test_app):
    """Test map markers endpoint with bounding box filter."""
    client = test_app.test_client()

    # Bounds that include both locations
    response = client.get('/api/map/markers?bounds=42.0,-74.0,43.0,-73.0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2

    # Bounds that exclude all locations
    response = client.get('/api/map/markers?bounds=40.0,-75.0,41.0,-74.0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 0


def test_map_markers_invalid_bounds(test_app):
    """Test map markers endpoint rejects invalid bounds."""
    client = test_app.test_client()
    response = client.get('/api/map/markers?bounds=invalid')

    assert response.status_code == 400

    data = json.loads(response.data)
    assert 'error' in data


def test_get_location_details(test_app):
    """Test getting location details."""
    client = test_app.test_client()
    response = client.get('/api/locations/loc-1')

    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['loc_uuid'] == 'loc-1'
    assert data['loc_name'] == 'Test Location 1'
    assert 'counts' in data
    assert data['counts']['images'] == 2
    assert data['counts']['videos'] == 1
    assert data['counts']['urls'] == 1


def test_get_location_details_not_found(test_app):
    """Test getting non-existent location."""
    client = test_app.test_client()
    response = client.get('/api/locations/nonexistent')

    assert response.status_code == 404

    data = json.loads(response.data)
    assert 'error' in data


def test_get_location_images(test_app):
    """Test getting images for a location."""
    client = test_app.test_client()
    response = client.get('/api/locations/loc-1/images')

    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 2

    # Check first image
    img = data[0]
    assert 'img_sha256' in img
    assert 'immich_asset_id' in img
    assert 'img_width' in img
    assert 'img_height' in img
    assert 'gps_lat' in img
    assert 'gps_lon' in img


def test_get_location_images_with_pagination(test_app):
    """Test image pagination."""
    client = test_app.test_client()

    # Get first image only
    response = client.get('/api/locations/loc-1/images?limit=1&offset=0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1

    # Get second image
    response = client.get('/api/locations/loc-1/images?limit=1&offset=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1


def test_get_location_videos(test_app):
    """Test getting videos for a location."""
    client = test_app.test_client()
    response = client.get('/api/locations/loc-1/videos')

    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 1

    # Check video
    vid = data[0]
    assert 'vid_sha256' in vid
    assert 'immich_asset_id' in vid
    assert 'vid_width' in vid
    assert 'vid_height' in vid
    assert 'vid_duration_sec' in vid


def test_get_location_archives(test_app):
    """Test getting archived URLs for a location."""
    client = test_app.test_client()
    response = client.get('/api/locations/loc-1/archives')

    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 1

    # Check archive
    archive = data[0]
    assert 'url_uuid' in archive
    assert 'url' in archive
    assert 'archivebox_snapshot_id' in archive
    assert 'archive_status' in archive
    assert archive['archive_status'] == 'archived'


def test_search_locations(test_app):
    """Test location search."""
    client = test_app.test_client()

    # Search by name
    response = client.get('/api/search?q=Test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 3  # All locations match "Test"

    # Search by state
    response = client.get('/api/search?state=ny')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 3

    # Search by type
    response = client.get('/api/search?type=hospital')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['loc_uuid'] == 'loc-2'


def test_search_locations_with_limit(test_app):
    """Test search with limit parameter."""
    client = test_app.test_client()
    response = client.get('/api/search?q=Test&limit=2')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2


def test_cors_headers(test_app):
    """Test that CORS headers are present."""
    client = test_app.test_client()
    response = client.get('/api/health')

    assert 'Access-Control-Allow-Origin' in response.headers
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    assert 'Access-Control-Allow-Methods' in response.headers


def test_error_handling_database_error(test_app):
    """Test API handles database errors gracefully."""
    # Close and delete database to simulate error
    db_path = test_app.config['DB_PATH']
    Path(db_path).unlink()

    client = test_app.test_client()
    response = client.get('/api/health')

    assert response.status_code == 500

    data = json.loads(response.data)
    assert 'error' in data or data['status'] == 'error'
