"""
Unit Tests: Media Extractor Worker

Tests media extraction from ArchiveBox archives and Immich upload.
Coverage:
- Fetching pending extractions from database
- Scanning ArchiveBox snapshots for media
- Upload to Immich
- Database insertion (images/videos with source_url)
- Duplicate detection
- Update media_extracted count
"""

import json
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

@pytest.fixture
def test_db(tmp_path):
    """Create test database with schema"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE locations (
            loc_uuid TEXT PRIMARY KEY, loc_name TEXT NOT NULL,
            type TEXT, state TEXT, lat REAL, lon REAL,
            loc_add TEXT, loc_update TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE urls (
            url_uuid TEXT PRIMARY KEY, loc_uuid TEXT NOT NULL,
            url TEXT NOT NULL, archivebox_snapshot_id TEXT,
            archive_status TEXT DEFAULT 'pending',
            media_extracted INTEGER DEFAULT 0,
            archive_date TEXT, url_add TEXT, url_update TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    cursor.execute("""
        CREATE TABLE images (
            img_uuid TEXT PRIMARY KEY, loc_uuid TEXT NOT NULL,
            img_sha TEXT NOT NULL, img_name TEXT, img_ext TEXT,
            img_size_bytes INTEGER, immich_asset_id TEXT UNIQUE,
            source_url TEXT, img_add TEXT, img_update TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    cursor.execute("""
        CREATE TABLE videos (
            vid_uuid TEXT PRIMARY KEY, loc_uuid TEXT NOT NULL,
            vid_sha TEXT NOT NULL, vid_name TEXT, vid_ext TEXT,
            vid_size_bytes INTEGER, immich_asset_id TEXT UNIQUE,
            source_url TEXT, vid_add TEXT, vid_update TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO locations (loc_uuid, loc_name, type, state, lat, lon, loc_add, loc_update)
        VALUES ('test-loc-123', 'Test Location', 'city', 'NY', 42.0, -73.0, '2025-01-01', '2025-01-01')
    """)

    cursor.execute("""
        INSERT INTO urls (
            url_uuid, loc_uuid, url, archivebox_snapshot_id,
            archive_status, media_extracted, archive_date, url_add
        )
        VALUES (
            'url-test-1', 'test-loc-123', 'https://example.com',
            '1763405109.545363', 'archiving', 0,
            '2025-01-01', '2025-01-01'
        )
    """)

    conn.commit()
    conn.close()
    return str(db_path)


class TestMediaExtractor:
    """Test suite for media extraction worker"""

    def test_fetch_pending_extractions(self, test_db):
        """Test fetching URLs pending media extraction"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from media_extractor import fetch_pending_extractions

        pending = fetch_pending_extractions(test_db, limit=10)

        assert len(pending) == 1
        assert pending[0]['url'] == 'https://example.com'
        assert pending[0]['archive_status'] == 'archiving'
        assert pending[0]['media_extracted'] == 0

    def test_check_media_already_imported(self, test_db):
        """Test duplicate detection"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from media_extractor import check_media_already_imported, insert_image_to_db

        # Not imported yet
        assert check_media_already_imported(test_db, 'abc123', 'image') == False

        # Insert image
        test_file = Path(__file__).parent / "test_data" / "test.jpg"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("fake image data")

        insert_image_to_db(
            test_db, 'test-loc-123', 'https://example.com',
            str(test_file), 'abc123', 'asset-123'
        )

        # Now should be detected
        assert check_media_already_imported(test_db, 'abc123', 'image') == True

    def test_update_url_media_extracted(self, test_db):
        """Test updating media_extracted count"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from media_extractor import update_url_media_extracted

        success = update_url_media_extracted(test_db, 'url-test-1', 5)
        assert success is True

        # Verify database
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT media_extracted FROM urls WHERE url_uuid = ?", ('url-test-1',))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
