"""
Unit Tests: Phase B - ArchiveBox Integration for POST /api/locations/{loc_uuid}/urls

Tests the ArchiveBox archiving functionality added in Phase B.
Tests cover:
- Successful archiving (snapshot_id returned and stored)
- ArchiveBox returns None (URL saved as pending)
- ArchiveBox connection error (graceful degradation)
- ArchiveBox archiving error (graceful degradation)
- Database state verification
"""

import json
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Test will run against actual Flask app
# Mock only external dependencies (ArchiveBox adapter)


@pytest.fixture
def test_db(tmp_path):
    """Create temporary test database with schema"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create locations table
    cursor.execute("""
        CREATE TABLE locations (
            loc_uuid TEXT PRIMARY KEY,
            loc_name TEXT NOT NULL,
            type TEXT,
            state TEXT,
            lat REAL,
            lon REAL,
            loc_add TEXT,
            loc_update TEXT
        )
    """)

    # Create urls table
    cursor.execute("""
        CREATE TABLE urls (
            url_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            url TEXT NOT NULL,
            url_title TEXT,
            url_desc TEXT,
            archivebox_snapshot_id TEXT,
            archive_status TEXT DEFAULT 'pending',
            archive_date TEXT,
            media_extracted INTEGER DEFAULT 0,
            url_add TEXT,
            url_update TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    # Insert test location
    cursor.execute("""
        INSERT INTO locations (loc_uuid, loc_name, type, state, lat, lon, loc_add, loc_update)
        VALUES ('test-loc-123', 'Test Location', 'city', 'NY', 42.6526, -73.7562, '2025-01-01', '2025-01-01')
    """)

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def flask_app(test_db, monkeypatch):
    """Create Flask app with test database"""
    # Mock environment variables
    monkeypatch.setenv('DB_PATH', test_db)
    monkeypatch.setenv('ARCHIVEBOX_URL', 'http://archivebox:8000')

    # Import after setting env vars
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from app import app
    app.config['TESTING'] = True
    app.config['DB_PATH'] = test_db

    return app


class TestArchiveURLPhaseB:
    """Test suite for Phase B ArchiveBox integration"""

    def test_successful_archiving(self, flask_app, test_db):
        """
        Test successful archiving flow:
        1. URL saved to database
        2. ArchiveBox archives URL successfully
        3. Database updated with snapshot_id and status='archiving'
        """
        with flask_app.test_client() as client:
            # Mock ArchiveBox adapter to return snapshot_id
            with patch('scripts.api_routes_v012.create_archivebox_adapter') as mock_create:
                mock_adapter = MagicMock()
                mock_adapter.archive_url.return_value = '1234567890'
                mock_create.return_value = mock_adapter

                response = client.post(
                    '/api/locations/test-loc-123/urls',
                    json={
                        'url': 'https://example.com',
                        'title': 'Example Site',
                        'description': 'Test archive'
                    },
                    content_type='application/json'
                )

                # Verify HTTP response
                assert response.status_code == 201
                data = json.loads(response.data)
                assert data['url'] == 'https://example.com'
                assert data['url_title'] == 'Example Site'
                assert data['archivebox_snapshot_id'] == '1234567890'
                assert data['archive_status'] == 'archiving'

                # Verify ArchiveBox adapter was called
                mock_adapter.archive_url.assert_called_once_with('https://example.com')

                # Verify database state
                conn = sqlite3.connect(test_db)
                cursor = conn.cursor()
                cursor.execute("SELECT archivebox_snapshot_id, archive_status FROM urls WHERE url_uuid = ?", (data['url_uuid'],))
                row = cursor.fetchone()
                assert row[0] == '1234567890'
                assert row[1] == 'archiving'
                conn.close()

    def test_archivebox_returns_none(self, flask_app, test_db):
        """
        Test when ArchiveBox returns None for snapshot_id:
        1. URL saved to database
        2. ArchiveBox called but returns None
        3. Status remains 'pending'
        """
        with flask_app.test_client() as client:
            with patch('scripts.api_routes_v012.create_archivebox_adapter') as mock_create:
                mock_adapter = MagicMock()
                mock_adapter.archive_url.return_value = None
                mock_create.return_value = mock_adapter

                response = client.post(
                    '/api/locations/test-loc-123/urls',
                    json={'url': 'https://no-snapshot.com'},
                    content_type='application/json'
                )

                assert response.status_code == 201
                data = json.loads(response.data)
                assert data['archivebox_snapshot_id'] is None
                assert data['archive_status'] == 'pending'

    def test_archivebox_connection_error(self, flask_app, test_db):
        """
        Test graceful degradation when ArchiveBox is unreachable:
        1. URL saved to database
        2. ArchiveBox connection fails
        3. Exception caught, URL remains with status='pending'
        4. HTTP 201 still returned (fail-safe)
        """
        with flask_app.test_client() as client:
            with patch('scripts.api_routes_v012.create_archivebox_adapter') as mock_create:
                mock_adapter = MagicMock()
                mock_adapter.archive_url.side_effect = Exception("Connection refused")
                mock_create.return_value = mock_adapter

                response = client.post(
                    '/api/locations/test-loc-123/urls',
                    json={'url': 'https://connection-fail.com'},
                    content_type='application/json'
                )

                # URL should still be saved successfully
                assert response.status_code == 201
                data = json.loads(response.data)
                assert data['url'] == 'https://connection-fail.com'
                assert data['archivebox_snapshot_id'] is None
                assert data['archive_status'] == 'pending'

    def test_archivebox_archiving_error(self, flask_app, test_db):
        """
        Test graceful degradation when ArchiveBox archiving fails:
        1. URL saved to database
        2. ArchiveBox API call fails with error
        3. Exception caught, logged, URL saved as pending
        """
        with flask_app.test_client() as client:
            with patch('scripts.api_routes_v012.create_archivebox_adapter') as mock_create:
                from scripts.adapters.archivebox_adapter import ArchiveBoxArchiveError
                mock_adapter = MagicMock()
                mock_adapter.archive_url.side_effect = ArchiveBoxArchiveError("Archive failed")
                mock_create.return_value = mock_adapter

                response = client.post(
                    '/api/locations/test-loc-123/urls',
                    json={'url': 'https://archive-fail.com'},
                    content_type='application/json'
                )

                assert response.status_code == 201
                data = json.loads(response.data)
                assert data['archive_status'] == 'pending'
                assert data['archivebox_snapshot_id'] is None

    def test_database_integrity(self, flask_app, test_db):
        """
        Test that database transaction is committed before archiving attempt:
        1. URL must exist in database even if archiving fails completely
        2. Verify URL can be fetched even if ArchiveBox crashes
        """
        with flask_app.test_client() as client:
            with patch('scripts.api_routes_v012.create_archivebox_adapter') as mock_create:
                # Simulate catastrophic failure
                mock_create.side_effect = Exception("ArchiveBox completely unavailable")

                response = client.post(
                    '/api/locations/test-loc-123/urls',
                    json={'url': 'https://database-test.com'},
                    content_type='application/json'
                )

                # URL should be saved despite ArchiveBox being down
                assert response.status_code == 201
                data = json.loads(response.data)

                # Verify URL exists in database
                conn = sqlite3.connect(test_db)
                cursor = conn.cursor()
                cursor.execute("SELECT url, archive_status FROM urls WHERE url = ?", ('https://database-test.com',))
                row = cursor.fetchone()
                assert row is not None
                assert row[0] == 'https://database-test.com'
                assert row[1] == 'pending'
                conn.close()

    def test_invalid_location_still_fails(self, flask_app, test_db):
        """
        Test that invalid location still returns 404 (before archiving):
        1. Validation happens before any archiving attempt
        2. ArchiveBox should never be called for invalid location
        """
        with flask_app.test_client() as client:
            with patch('scripts.api_routes_v012.create_archivebox_adapter') as mock_create:
                mock_adapter = MagicMock()
                mock_create.return_value = mock_adapter

                response = client.post(
                    '/api/locations/invalid-loc-999/urls',
                    json={'url': 'https://example.com'},
                    content_type='application/json'
                )

                assert response.status_code == 404
                # ArchiveBox should not be called
                mock_adapter.archive_url.assert_not_called()

    def test_missing_url_still_fails(self, flask_app, test_db):
        """
        Test that missing URL still returns 400 (validation before archiving)
        """
        with flask_app.test_client() as client:
            with patch('scripts.api_routes_v012.create_archivebox_adapter') as mock_create:
                mock_adapter = MagicMock()
                mock_create.return_value = mock_adapter

                response = client.post(
                    '/api/locations/test-loc-123/urls',
                    json={},
                    content_type='application/json'
                )

                assert response.status_code == 400
                data = json.loads(response.data)
                assert 'url is required' in data['error']
                # ArchiveBox should not be called
                mock_adapter.archive_url.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
