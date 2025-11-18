"""
Test suite for bookmark API endpoints

Tests CRUD operations, validation, filtering, and error handling
for the bookmark management system.

Version: 0.1.2-browser
Last Updated: 2025-11-18
"""

import json
import pytest
import sqlite3
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

# Import from scripts directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from api_routes_bookmarks import (
    bookmarks_bp,
    validate_url,
    validate_uuid,
    get_db_connection
)


@pytest.fixture
def test_db():
    """Create temporary test database with schema."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Create locations table (for foreign key)
    cursor.execute("""
        CREATE TABLE locations (
            loc_uuid TEXT PRIMARY KEY,
            loc_name TEXT NOT NULL,
            state TEXT
        )
    """)

    # Create bookmarks table
    cursor.execute("""
        CREATE TABLE bookmarks (
            bookmark_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT,
            url TEXT NOT NULL,
            title TEXT,
            description TEXT,
            favicon_url TEXT,
            folder TEXT,
            tags TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            visit_count INTEGER DEFAULT 0,
            last_visited TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE SET NULL
        )
    """)

    cursor.execute("CREATE INDEX idx_bookmarks_loc_uuid ON bookmarks(loc_uuid)")
    cursor.execute("CREATE INDEX idx_bookmarks_folder ON bookmarks(folder)")

    # Insert test location
    cursor.execute("""
        INSERT INTO locations (loc_uuid, loc_name, state)
        VALUES ('test-loc-1', 'Test Location', 'NY')
    """)

    conn.commit()
    conn.close()

    # Override db connection in module
    original_db = 'data/aupat.db'
    import api_routes_bookmarks
    api_routes_bookmarks.get_db_connection = lambda: sqlite3.connect(db_path)

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def app(test_db):
    """Create Flask test app with bookmarks blueprint."""
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(bookmarks_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


class TestValidation:
    """Test input validation functions."""

    def test_validate_url_valid(self):
        """Test URL validation with valid URLs."""
        assert validate_url('http://example.com')
        assert validate_url('https://example.com')
        assert validate_url('https://example.com/path?query=value')

    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        assert not validate_url('ftp://example.com')
        assert not validate_url('example.com')
        assert not validate_url('')
        assert not validate_url(None)
        assert not validate_url('javascript:alert(1)')

    def test_validate_uuid_valid(self):
        """Test UUID validation with valid UUIDs."""
        assert validate_uuid(str(uuid.uuid4()))
        assert validate_uuid('123e4567-e89b-12d3-a456-426614174000')

    def test_validate_uuid_invalid(self):
        """Test UUID validation with invalid UUIDs."""
        assert not validate_uuid('not-a-uuid')
        assert not validate_uuid('')
        assert not validate_uuid(None)
        assert not validate_uuid('123')


class TestCreateBookmark:
    """Test bookmark creation endpoint."""

    def test_create_bookmark_minimal(self, client):
        """Test creating bookmark with minimal required fields."""
        response = client.post('/api/bookmarks', json={
            'url': 'https://example.com'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert 'bookmark_uuid' in data
        assert data['url'] == 'https://example.com'
        assert 'created_at' in data

    def test_create_bookmark_full(self, client):
        """Test creating bookmark with all fields."""
        response = client.post('/api/bookmarks', json={
            'url': 'https://example.com/page',
            'title': 'Example Page',
            'description': 'A test bookmark',
            'loc_uuid': 'test-loc-1',
            'folder': 'Research/NY',
            'tags': ['test', 'example']
        })

        assert response.status_code == 201
        data = response.get_json()
        assert 'bookmark_uuid' in data

    def test_create_bookmark_missing_url(self, client):
        """Test creating bookmark without URL fails."""
        response = client.post('/api/bookmarks', json={
            'title': 'No URL'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_create_bookmark_invalid_url(self, client):
        """Test creating bookmark with invalid URL fails."""
        response = client.post('/api/bookmarks', json={
            'url': 'not-a-url'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid URL format' in data['error']

    def test_create_bookmark_invalid_loc_uuid(self, client):
        """Test creating bookmark with invalid location UUID fails."""
        response = client.post('/api/bookmarks', json={
            'url': 'https://example.com',
            'loc_uuid': 'not-a-uuid'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid location UUID' in data['error']


class TestListBookmarks:
    """Test bookmark listing endpoint."""

    @pytest.fixture(autouse=True)
    def setup_bookmarks(self, client):
        """Create test bookmarks before each test."""
        self.bookmarks = []
        for i in range(5):
            response = client.post('/api/bookmarks', json={
                'url': f'https://example.com/page{i}',
                'title': f'Page {i}',
                'folder': 'Research' if i % 2 == 0 else 'Archive',
                'loc_uuid': 'test-loc-1' if i < 3 else None
            })
            data = response.get_json()
            self.bookmarks.append(data['bookmark_uuid'])

    def test_list_bookmarks_default(self, client):
        """Test listing all bookmarks with default parameters."""
        response = client.get('/api/bookmarks')

        assert response.status_code == 200
        data = response.get_json()
        assert 'bookmarks' in data
        assert 'total' in data
        assert data['total'] == 5
        assert len(data['bookmarks']) == 5

    def test_list_bookmarks_with_limit(self, client):
        """Test listing bookmarks with limit."""
        response = client.get('/api/bookmarks?limit=3')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['bookmarks']) == 3
        assert data['total'] == 5

    def test_list_bookmarks_with_offset(self, client):
        """Test listing bookmarks with offset."""
        response = client.get('/api/bookmarks?limit=2&offset=2')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['bookmarks']) == 2
        assert data['offset'] == 2

    def test_list_bookmarks_filter_by_folder(self, client):
        """Test filtering bookmarks by folder."""
        response = client.get('/api/bookmarks?folder=Research')

        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 3  # 3 bookmarks in Research folder
        for bookmark in data['bookmarks']:
            assert bookmark['folder'] == 'Research'

    def test_list_bookmarks_filter_by_location(self, client):
        """Test filtering bookmarks by location."""
        response = client.get('/api/bookmarks?loc_uuid=test-loc-1')

        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 3  # 3 bookmarks linked to test-loc-1

    def test_list_bookmarks_search(self, client):
        """Test searching bookmarks."""
        response = client.get('/api/bookmarks?search=Page 2')

        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] >= 1
        assert any('Page 2' in b['title'] for b in data['bookmarks'])


class TestGetBookmark:
    """Test get single bookmark endpoint."""

    @pytest.fixture
    def bookmark_uuid(self, client):
        """Create a test bookmark."""
        response = client.post('/api/bookmarks', json={
            'url': 'https://example.com/test',
            'title': 'Test Bookmark'
        })
        return response.get_json()['bookmark_uuid']

    def test_get_bookmark_success(self, client, bookmark_uuid):
        """Test getting existing bookmark."""
        response = client.get(f'/api/bookmarks/{bookmark_uuid}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['bookmark_uuid'] == bookmark_uuid
        assert data['url'] == 'https://example.com/test'
        assert data['title'] == 'Test Bookmark'
        assert 'tags' in data

    def test_get_bookmark_not_found(self, client):
        """Test getting non-existent bookmark."""
        fake_uuid = str(uuid.uuid4())
        response = client.get(f'/api/bookmarks/{fake_uuid}')

        assert response.status_code == 404
        data = response.get_json()
        assert 'not found' in data['error'].lower()

    def test_get_bookmark_invalid_uuid(self, client):
        """Test getting bookmark with invalid UUID."""
        response = client.get('/api/bookmarks/not-a-uuid')

        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid' in data['error']


class TestUpdateBookmark:
    """Test bookmark update endpoint."""

    @pytest.fixture
    def bookmark_uuid(self, client):
        """Create a test bookmark."""
        response = client.post('/api/bookmarks', json={
            'url': 'https://example.com/test',
            'title': 'Original Title',
            'folder': 'Old Folder'
        })
        return response.get_json()['bookmark_uuid']

    def test_update_bookmark_title(self, client, bookmark_uuid):
        """Test updating bookmark title."""
        response = client.put(f'/api/bookmarks/{bookmark_uuid}', json={
            'title': 'New Title'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['bookmark_uuid'] == bookmark_uuid

        # Verify update
        get_response = client.get(f'/api/bookmarks/{bookmark_uuid}')
        bookmark = get_response.get_json()
        assert bookmark['title'] == 'New Title'

    def test_update_bookmark_multiple_fields(self, client, bookmark_uuid):
        """Test updating multiple bookmark fields."""
        response = client.put(f'/api/bookmarks/{bookmark_uuid}', json={
            'title': 'Updated Title',
            'description': 'Updated description',
            'folder': 'New Folder',
            'tags': ['new', 'tags']
        })

        assert response.status_code == 200

        # Verify updates
        get_response = client.get(f'/api/bookmarks/{bookmark_uuid}')
        bookmark = get_response.get_json()
        assert bookmark['title'] == 'Updated Title'
        assert bookmark['description'] == 'Updated description'
        assert bookmark['folder'] == 'New Folder'
        assert bookmark['tags'] == ['new', 'tags']

    def test_update_bookmark_not_found(self, client):
        """Test updating non-existent bookmark."""
        fake_uuid = str(uuid.uuid4())
        response = client.put(f'/api/bookmarks/{fake_uuid}', json={
            'title': 'New Title'
        })

        assert response.status_code == 404

    def test_update_bookmark_no_data(self, client, bookmark_uuid):
        """Test updating bookmark with no data fails."""
        response = client.put(f'/api/bookmarks/{bookmark_uuid}', json={})

        assert response.status_code == 400


class TestDeleteBookmark:
    """Test bookmark deletion endpoint."""

    @pytest.fixture
    def bookmark_uuid(self, client):
        """Create a test bookmark."""
        response = client.post('/api/bookmarks', json={
            'url': 'https://example.com/test'
        })
        return response.get_json()['bookmark_uuid']

    def test_delete_bookmark_success(self, client, bookmark_uuid):
        """Test deleting existing bookmark."""
        response = client.delete(f'/api/bookmarks/{bookmark_uuid}')

        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f'/api/bookmarks/{bookmark_uuid}')
        assert get_response.status_code == 404

    def test_delete_bookmark_not_found(self, client):
        """Test deleting non-existent bookmark."""
        fake_uuid = str(uuid.uuid4())
        response = client.delete(f'/api/bookmarks/{fake_uuid}')

        assert response.status_code == 404


class TestListFolders:
    """Test folder listing endpoint."""

    @pytest.fixture(autouse=True)
    def setup_bookmarks(self, client):
        """Create bookmarks in different folders."""
        folders = ['Research/NY', 'Research/MA', 'Archive', 'Archive/2023']
        for folder in folders:
            client.post('/api/bookmarks', json={
                'url': f'https://example.com/{folder}',
                'folder': folder
            })

    def test_list_folders(self, client):
        """Test listing all unique folders."""
        response = client.get('/api/bookmarks/folders')

        assert response.status_code == 200
        data = response.get_json()
        assert 'folders' in data
        assert len(data['folders']) == 4
        assert 'Research/NY' in data['folders']
        assert 'Archive' in data['folders']


class TestRecordVisit:
    """Test visit recording endpoint."""

    @pytest.fixture
    def bookmark_uuid(self, client):
        """Create a test bookmark."""
        response = client.post('/api/bookmarks', json={
            'url': 'https://example.com/test'
        })
        return response.get_json()['bookmark_uuid']

    def test_record_visit(self, client, bookmark_uuid):
        """Test recording a bookmark visit."""
        response = client.post(f'/api/bookmarks/{bookmark_uuid}/visit')

        assert response.status_code == 200
        data = response.get_json()
        assert 'last_visited' in data

        # Verify visit count increased
        get_response = client.get(f'/api/bookmarks/{bookmark_uuid}')
        bookmark = get_response.get_json()
        assert bookmark['visit_count'] == 1
        assert bookmark['last_visited'] is not None

    def test_record_multiple_visits(self, client, bookmark_uuid):
        """Test recording multiple visits."""
        for _ in range(3):
            client.post(f'/api/bookmarks/{bookmark_uuid}/visit')

        get_response = client.get(f'/api/bookmarks/{bookmark_uuid}')
        bookmark = get_response.get_json()
        assert bookmark['visit_count'] == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
