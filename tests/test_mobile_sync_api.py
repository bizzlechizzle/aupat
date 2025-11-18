#!/usr/bin/env python3
"""
Unit tests for mobile sync API endpoints
Tests both push and pull sync operations with conflict resolution

Run with: pytest tests/test_mobile_sync_api.py -v
"""

import pytest
import json
import sqlite3
from datetime import datetime
from uuid import uuid4
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app


@pytest.fixture
def client():
    """Create test client with in-memory database."""
    app.config['TESTING'] = True
    app.config['DB_PATH'] = ':memory:'

    with app.test_client() as client:
        # Initialize test database
        with app.app_context():
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()

            # Create minimal schema for testing
            cursor.execute('''
                CREATE TABLE locations (
                    loc_uuid TEXT PRIMARY KEY,
                    loc_name TEXT NOT NULL,
                    lat REAL,
                    lon REAL,
                    type TEXT NOT NULL,
                    loc_add TEXT,
                    json_update TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE sync_log (
                    sync_id TEXT PRIMARY KEY,
                    device_id TEXT,
                    sync_type TEXT,
                    timestamp TEXT,
                    items_synced INTEGER,
                    conflicts INTEGER,
                    status TEXT
                )
            ''')

            conn.commit()
            conn.close()

        yield client


def test_sync_push_new_location(client):
    """Test pushing new location from mobile to desktop."""
    payload = {
        'device_id': 'test-device-001',
        'new_locations': [
            {
                'loc_uuid': str(uuid4()),
                'loc_name': 'Test Abandoned Factory',
                'lat': 42.8142,
                'lon': -73.9396,
                'loc_type': 'factory',
                'created_at': datetime.now().isoformat(),
                'photos': []
            }
        ],
        'updated_locations': [],
        'device_timestamp': datetime.now().isoformat()
    }

    response = client.post(
        '/api/sync/mobile',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['synced_count'] == 1
    assert len(data['conflicts']) == 0


def test_sync_push_conflict_existing_location(client):
    """Test conflict when pushing location that already exists."""
    loc_uuid = str(uuid4())

    # First, create location via direct database insert
    # (simulating it was already synced from desktop)
    conn = sqlite3.connect(app.config['DB_PATH'])
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO locations (loc_uuid, loc_name, lat, lon, type, json_update)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (loc_uuid, 'Existing Location', 42.0, -73.0, 'factory', datetime.now().isoformat()))
    conn.commit()
    conn.close()

    # Now try to push same UUID from mobile
    payload = {
        'device_id': 'test-device-001',
        'new_locations': [
            {
                'loc_uuid': loc_uuid,
                'loc_name': 'Duplicate Location',
                'lat': 42.8142,
                'lon': -73.9396,
                'loc_type': 'factory',
                'created_at': datetime.now().isoformat(),
                'photos': []
            }
        ],
        'updated_locations': [],
        'device_timestamp': datetime.now().isoformat()
    }

    response = client.post(
        '/api/sync/mobile',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['synced_count'] == 0  # Should be skipped
    assert len(data['conflicts']) == 1
    assert data['conflicts'][0]['reason'] == 'location_already_exists'


def test_sync_pull_all_locations(client):
    """Test pulling all locations from desktop to mobile (initial sync)."""
    # Insert test locations
    conn = sqlite3.connect(app.config['DB_PATH'])
    cursor = conn.cursor()

    test_locations = [
        (str(uuid4()), 'Location 1', 42.0, -73.0, 'factory'),
        (str(uuid4()), 'Location 2', 42.1, -73.1, 'mill'),
        (str(uuid4()), 'Location 3', 42.2, -73.2, 'church'),
    ]

    for loc in test_locations:
        cursor.execute('''
            INSERT INTO locations (loc_uuid, loc_name, lat, lon, type, json_update)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (loc[0], loc[1], loc[2], loc[3], loc[4], datetime.now().isoformat()))

    conn.commit()
    conn.close()

    # Pull locations
    response = client.get('/api/sync/mobile/pull')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['count'] == 3
    assert len(data['locations']) == 3
    assert data['has_more'] is False


def test_sync_pull_since_timestamp(client):
    """Test pulling only locations modified after a timestamp."""
    conn = sqlite3.connect(app.config['DB_PATH'])
    cursor = conn.cursor()

    # Insert old location
    old_time = '2025-01-01T00:00:00Z'
    cursor.execute('''
        INSERT INTO locations (loc_uuid, loc_name, lat, lon, type, json_update)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (str(uuid4()), 'Old Location', 42.0, -73.0, 'factory', old_time))

    # Insert recent location
    recent_time = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO locations (loc_uuid, loc_name, lat, lon, type, json_update)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (str(uuid4()), 'Recent Location', 42.1, -73.1, 'mill', recent_time))

    conn.commit()
    conn.close()

    # Pull only recent locations
    since = '2025-11-01T00:00:00Z'
    response = client.get(f'/api/sync/mobile/pull?since={since}')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['count'] == 1  # Only recent location
    assert data['locations'][0]['locName'] == 'Recent Location'


def test_sync_pull_with_limit(client):
    """Test pagination with limit parameter."""
    conn = sqlite3.connect(app.config['DB_PATH'])
    cursor = conn.cursor()

    # Insert 10 test locations
    for i in range(10):
        cursor.execute('''
            INSERT INTO locations (loc_uuid, loc_name, lat, lon, type, json_update)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(uuid4()), f'Location {i}', 42.0 + i * 0.1, -73.0, 'factory', datetime.now().isoformat()))

    conn.commit()
    conn.close()

    # Pull with limit of 5
    response = client.get('/api/sync/mobile/pull?limit=5')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['count'] == 5
    assert data['has_more'] is True


def test_sync_push_missing_device_id(client):
    """Test error handling when device_id is missing."""
    payload = {
        'new_locations': [],
        'updated_locations': [],
        'device_timestamp': datetime.now().isoformat()
    }

    response = client.post(
        '/api/sync/mobile',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'device_id' in data['error']


def test_sync_push_empty_payload(client):
    """Test error handling for empty payload."""
    response = client.post(
        '/api/sync/mobile',
        data='',
        content_type='application/json'
    )

    assert response.status_code == 400


def test_cors_headers(client):
    """Test CORS headers are present for mobile app access."""
    response = client.get('/api/sync/mobile/pull')

    assert response.headers.get('Access-Control-Allow-Origin') == '*'
    assert 'Content-Type' in response.headers.get('Access-Control-Allow-Headers', '')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
