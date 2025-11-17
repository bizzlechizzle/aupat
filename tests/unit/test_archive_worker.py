"""
Unit Tests: Archive Worker - Background URL archiving daemon

Tests the archive_worker.py background worker that processes pending URLs.
Tests cover:
- Database polling for pending URLs
- Subprocess integration with ArchiveBox CLI
- Snapshot ID extraction from CLI output
- Database updates (successful archiving)
- Retry logic and failure handling
- Graceful shutdown
"""

import json
import sqlite3
import pytest
import subprocess
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Test will run against actual worker functions
# Mock only external dependencies (subprocess, database)


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

    # Insert test URLs with different statuses
    cursor.execute("""
        INSERT INTO urls (url_uuid, loc_uuid, url, url_title, archive_status, url_add)
        VALUES
            ('url-pending-1', 'test-loc-123', 'https://example.com', 'Example', 'pending', '2025-01-01'),
            ('url-pending-2', 'test-loc-123', 'https://httpbin.org/html', 'HTTPBin', 'pending', '2025-01-01'),
            ('url-archived', 'test-loc-123', 'https://archived.com', 'Already Archived', 'archiving', '2025-01-01')
    """)

    conn.commit()
    conn.close()

    return str(db_path)


class TestArchiveWorkerFunctions:
    """Test suite for individual archive worker functions"""

    def test_fetch_pending_urls(self, test_db):
        """Test fetching pending URLs from database"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import fetch_pending_urls

        pending_urls = fetch_pending_urls(test_db, limit=10)

        assert len(pending_urls) == 2  # Only pending URLs
        assert pending_urls[0]['url'] == 'https://example.com'
        assert pending_urls[1]['url'] == 'https://httpbin.org/html'
        assert pending_urls[0]['archive_status'] == 'pending'

    def test_extract_snapshot_id_from_cli_output(self):
        """Test extracting snapshot ID from ArchiveBox CLI output"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import extract_snapshot_id

        # Test various output formats
        output1 = """
        > Adding URL(s) to ArchiveBox...
        > [i] [2025-11-17 12:34:56] 1763405109.545363: https://example.com
        """
        snapshot_id = extract_snapshot_id(output1)
        assert snapshot_id == '1763405109.545363'

        # Test without decimal
        output2 = "Snapshot created: 1763405109"
        snapshot_id = extract_snapshot_id(output2)
        assert snapshot_id == '1763405109'

        # Test with "archive" keyword
        output3 = "Archive ID: 1763405109.12345"
        snapshot_id = extract_snapshot_id(output3)
        assert snapshot_id == '1763405109.12345'

        # Test no match
        output4 = "No timestamp here"
        snapshot_id = extract_snapshot_id(output4)
        assert snapshot_id is None

    def test_update_url_archived(self, test_db):
        """Test updating URL with snapshot_id and status='archiving'"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import update_url_archived

        # Update pending URL
        success = update_url_archived(test_db, 'url-pending-1', '1763405109.545363')
        assert success is True

        # Verify database state
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT archivebox_snapshot_id, archive_status FROM urls WHERE url_uuid = ?",
            ('url-pending-1',)
        )
        row = cursor.fetchone()
        conn.close()

        assert row[0] == '1763405109.545363'
        assert row[1] == 'archiving'

    def test_mark_url_failed(self, test_db):
        """Test marking URL as failed after max retries"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import mark_url_failed

        # Mark URL as failed
        success = mark_url_failed(test_db, 'url-pending-2')
        assert success is True

        # Verify database state
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT archive_status FROM urls WHERE url_uuid = ?",
            ('url-pending-2',)
        )
        row = cursor.fetchone()
        conn.close()

        assert row[0] == 'failed'


class TestArchiveWorkerSubprocess:
    """Test suite for subprocess integration"""

    def test_archive_url_cli_success(self):
        """Test successful archiving via CLI"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import archive_url_cli

        with patch('subprocess.run') as mock_run:
            # Mock successful subprocess execution
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[i] [2025-11-17 12:34:56] 1763405109.545363: https://example.com",
                stderr=""
            )

            snapshot_id = archive_url_cli('https://example.com')

            assert snapshot_id == '1763405109.545363'
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == 'docker'
            assert call_args[1] == 'compose'
            assert call_args[2] == 'exec'
            assert call_args[3] == '-T'
            assert call_args[4] == 'archivebox'
            assert call_args[5] == 'archivebox'
            assert call_args[6] == 'add'
            assert call_args[7] == 'https://example.com'

    def test_archive_url_cli_failure(self):
        """Test handling of failed archiving"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import archive_url_cli

        with patch('subprocess.run') as mock_run:
            # Mock failed subprocess execution
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Error: Connection refused"
            )

            snapshot_id = archive_url_cli('https://example.com')

            assert snapshot_id is None

    def test_archive_url_cli_timeout(self):
        """Test handling of subprocess timeout"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import archive_url_cli

        with patch('subprocess.run') as mock_run:
            # Mock timeout
            mock_run.side_effect = subprocess.TimeoutExpired(cmd='docker', timeout=120)

            snapshot_id = archive_url_cli('https://example.com')

            assert snapshot_id is None


class TestArchiveWorkerRetryLogic:
    """Test suite for retry logic and failure handling"""

    def test_process_pending_urls_success(self, test_db):
        """Test processing pending URLs with successful archiving"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import process_pending_urls

        with patch('archive_worker.archive_url_cli') as mock_archive:
            # Mock successful archiving
            mock_archive.return_value = '1763405109.545363'

            successful, failed = process_pending_urls(test_db, max_retries=3)

            assert successful == 2  # Both pending URLs
            assert failed == 0
            assert mock_archive.call_count == 2

    def test_process_pending_urls_with_failures(self, test_db):
        """Test processing with archiving failures and retries"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import process_pending_urls

        with patch('archive_worker.archive_url_cli') as mock_archive:
            # Mock archiving failures
            mock_archive.return_value = None

            successful, failed = process_pending_urls(test_db, max_retries=3)

            assert successful == 0
            assert failed == 2  # Both URLs failed

    def test_max_retries_exceeded(self, test_db):
        """Test that URLs are marked as failed after max retries"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import process_pending_urls

        # Clear retry tracker
        if hasattr(process_pending_urls, 'retry_tracker'):
            process_pending_urls.retry_tracker = {}

        with patch('archive_worker.archive_url_cli') as mock_archive:
            mock_archive.return_value = None  # Always fail

            # First 3 attempts
            for i in range(3):
                successful, failed = process_pending_urls(test_db, max_retries=3)
                assert failed == 2  # Both URLs fail each time

            # Fourth attempt should mark as failed
            successful, failed = process_pending_urls(test_db, max_retries=3)

            # Verify URLs marked as failed in database
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM urls WHERE archive_status = 'failed'"
            )
            failed_count = cursor.fetchone()[0]
            conn.close()

            assert failed_count == 2  # Both URLs marked as failed


class TestArchiveWorkerConfiguration:
    """Test suite for configuration and initialization"""

    def test_load_user_config_success(self, tmp_path):
        """Test loading valid user.json configuration"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import load_user_config

        # Create test user.json
        config_file = tmp_path / "user.json"
        config_data = {
            "db_name": "test.db",
            "db_loc": str(tmp_path / "test.db")
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = load_user_config(str(config_file))

        assert config['db_name'] == 'test.db'
        assert config['db_loc'] == str(tmp_path / "test.db")

    def test_load_user_config_missing_file(self, tmp_path):
        """Test error handling when user.json is missing"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import load_user_config

        with pytest.raises(FileNotFoundError):
            load_user_config(str(tmp_path / "nonexistent.json"))

    def test_load_user_config_missing_keys(self, tmp_path):
        """Test error handling when required keys are missing"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from archive_worker import load_user_config

        # Create incomplete config
        config_file = tmp_path / "user.json"
        config_data = {"db_name": "test.db"}  # Missing db_loc
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with pytest.raises(ValueError):
            load_user_config(str(config_file))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
