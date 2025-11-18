#!/usr/bin/env python3
"""
Test suite for import_helpers module.
Validates batch tracking, logging, and backup integration.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
import sys
import json

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from import_helpers import (
    load_user_config,
    create_backup_for_import,
    create_import_batch,
    update_import_batch,
    complete_import_batch,
    log_file_import,
    get_import_batch_status,
    get_import_log_for_batch
)


@pytest.fixture
def test_db():
    """Create test database with v0.1.4 schema."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Run migration to create schema
    from db_migrate_v014 import run_migration
    run_migration(path, backup=False)

    yield path

    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def test_config(test_db):
    """Create test configuration."""
    config_dir = Path(test_db).parent
    config = {
        'db_name': 'test.db',
        'db_loc': test_db,
        'db_ingest': str(config_dir / 'ingest'),
        'arch_loc': str(config_dir / 'archive'),
        'db_backup': str(config_dir / 'backup')
    }

    # Create directories
    for key in ['db_ingest', 'arch_loc', 'db_backup']:
        Path(config[key]).mkdir(exist_ok=True)

    # Create config file
    config_file = config_dir / 'test_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f)

    yield config, str(config_file)

    # Cleanup
    try:
        config_file.unlink()
    except:
        pass


@pytest.fixture
def test_location(test_db):
    """Create test location in database."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO locations (loc_uuid, loc_name, state, type)
        VALUES ('test-loc-uuid', 'Test Location', 'NY', 'test')
    """)
    conn.commit()
    conn.close()

    return 'test-loc-uuid'


class TestLoadUserConfig:
    """Test user configuration loading."""

    def test_loads_valid_config(self, test_config):
        """Verify loading valid configuration."""
        config, config_path = test_config

        loaded = load_user_config(config_path)

        assert loaded['db_name'] == config['db_name']
        assert loaded['db_loc'] == config['db_loc']
        assert loaded['db_ingest'] == config['db_ingest']
        assert loaded['arch_loc'] == config['arch_loc']

    def test_raises_on_missing_file(self):
        """Verify error on missing config file."""
        with pytest.raises(FileNotFoundError):
            load_user_config('/nonexistent/path.json')

    def test_raises_on_missing_required_keys(self):
        """Verify error on incomplete configuration."""
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            json.dump({'db_name': 'test.db'}, f)  # Missing db_loc

        try:
            with pytest.raises(ValueError, match="Missing required keys"):
                load_user_config(path)
        finally:
            os.unlink(path)


class TestCreateBackupForImport:
    """Test backup creation before imports."""

    def test_creates_backup_successfully(self, test_config):
        """Verify backup file is created."""
        config, _ = test_config

        success, backup_path, error = create_backup_for_import(config)

        assert success is True
        assert backup_path is not None
        assert error is None
        assert Path(backup_path).exists()
        assert Path(backup_path).stat().st_size > 0

    def test_returns_error_on_failure(self):
        """Verify error handling when backup fails."""
        config = {
            'db_name': 'test.db',
            'db_loc': '/nonexistent/path.db',
            'db_backup': '/tmp/backup'
        }

        success, backup_path, error = create_backup_for_import(config)

        assert success is False
        assert backup_path is None
        assert error is not None


class TestCreateImportBatch:
    """Test import batch creation."""

    def test_creates_batch_record(self, test_db, test_location):
        """Verify batch record is created with correct fields."""
        batch_id = create_import_batch(
            test_db,
            test_location,
            '/test/source/path',
            '/test/backup.db'
        )

        assert batch_id is not None
        assert len(batch_id) == 36  # UUID format

        # Verify in database
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM import_batches WHERE batch_id = ?", (batch_id,))
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_sets_initial_status_to_running(self, test_db, test_location):
        """Verify new batch has 'running' status."""
        batch_id = create_import_batch(
            test_db,
            test_location,
            '/test/source/path'
        )

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM import_batches WHERE batch_id = ?", (batch_id,))
        row = cursor.fetchone()

        assert row['status'] == 'running'
        conn.close()

    def test_stores_backup_path(self, test_db, test_location):
        """Verify backup path is stored correctly."""
        backup_path = '/test/backup.db'

        batch_id = create_import_batch(
            test_db,
            test_location,
            '/test/source/path',
            backup_path
        )

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT backup_path, backup_created FROM import_batches WHERE batch_id = ?", (batch_id,))
        row = cursor.fetchone()

        assert row['backup_path'] == backup_path
        assert row['backup_created'] == 1
        conn.close()


class TestUpdateImportBatch:
    """Test batch status updates."""

    def test_updates_single_field(self, test_db, test_location):
        """Verify updating single field."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        update_import_batch(test_db, batch_id, total_files=100)

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT total_files FROM import_batches WHERE batch_id = ?", (batch_id,))
        row = cursor.fetchone()

        assert row['total_files'] == 100
        conn.close()

    def test_updates_multiple_fields(self, test_db, test_location):
        """Verify updating multiple fields at once."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        update_import_batch(
            test_db,
            batch_id,
            total_files=100,
            files_imported=50,
            files_skipped=10,
            duplicates_found=5
        )

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM import_batches WHERE batch_id = ?", (batch_id,))
        row = cursor.fetchone()

        assert row['total_files'] == 100
        assert row['files_imported'] == 50
        assert row['files_skipped'] == 10
        assert row['duplicates_found'] == 5
        conn.close()


class TestCompleteImportBatch:
    """Test batch completion."""

    def test_marks_batch_as_completed(self, test_db, test_location):
        """Verify batch marked as completed with end time."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        complete_import_batch(test_db, batch_id, status='completed')

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT status, batch_end FROM import_batches WHERE batch_id = ?", (batch_id,))
        row = cursor.fetchone()

        assert row['status'] == 'completed'
        assert row['batch_end'] is not None
        conn.close()

    def test_marks_batch_as_failed_with_error_log(self, test_db, test_location):
        """Verify failed batch records error log."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        complete_import_batch(
            test_db,
            batch_id,
            status='failed',
            error_log='Test error message'
        )

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT status, error_log FROM import_batches WHERE batch_id = ?", (batch_id,))
        row = cursor.fetchone()

        assert row['status'] == 'failed'
        assert row['error_log'] == 'Test error message'
        conn.close()


class TestLogFileImport:
    """Test file import logging."""

    def test_creates_log_entry(self, test_db, test_location):
        """Verify log entry is created with all fields."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        log_id = log_file_import(
            test_db,
            batch_id,
            '/test/source/photo.jpg',
            'abc123',  # SHA256
            'staging',
            'success',
            file_size_bytes=1024,
            media_type='image',
            hardware_category='phone'
        )

        assert log_id is not None

        # Verify in database
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM import_log WHERE log_id = ?", (log_id,))
        row = cursor.fetchone()

        assert row['batch_id'] == batch_id
        assert row['file_name'] == 'photo.jpg'
        assert row['file_sha256'] == 'abc123'
        assert row['stage'] == 'staging'
        assert row['status'] == 'success'
        assert row['file_size_bytes'] == 1024
        assert row['media_type'] == 'image'
        assert row['hardware_category'] == 'phone'
        conn.close()

    def test_logs_failure_with_error_message(self, test_db, test_location):
        """Verify failure logging includes error message."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        log_id = log_file_import(
            test_db,
            batch_id,
            '/test/source/photo.jpg',
            'abc123',
            'staging',
            'failed',
            error_message='File corrupted'
        )

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT error_message FROM import_log WHERE log_id = ?", (log_id,))
        row = cursor.fetchone()

        assert row['error_message'] == 'File corrupted'
        conn.close()


class TestGetImportBatchStatus:
    """Test batch status retrieval."""

    def test_returns_batch_dict(self, test_db, test_location):
        """Verify batch status returned as dict."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')
        update_import_batch(test_db, batch_id, total_files=100)

        status = get_import_batch_status(test_db, batch_id)

        assert status is not None
        assert isinstance(status, dict)
        assert status['batch_id'] == batch_id
        assert status['total_files'] == 100

    def test_returns_none_for_nonexistent_batch(self, test_db):
        """Verify None returned for missing batch."""
        status = get_import_batch_status(test_db, 'nonexistent-batch-id')

        assert status is None


class TestGetImportLogForBatch:
    """Test import log retrieval."""

    def test_returns_all_logs_for_batch(self, test_db, test_location):
        """Verify all log entries returned."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        # Create multiple log entries
        log_file_import(test_db, batch_id, '/test/file1.jpg', 'sha1', 'staging', 'success')
        log_file_import(test_db, batch_id, '/test/file2.jpg', 'sha2', 'staging', 'success')
        log_file_import(test_db, batch_id, '/test/file3.jpg', 'sha3', 'staging', 'failed')

        logs = get_import_log_for_batch(test_db, batch_id)

        assert len(logs) == 3
        assert all(isinstance(log, dict) for log in logs)

    def test_filters_by_stage(self, test_db, test_location):
        """Verify filtering by stage."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        log_file_import(test_db, batch_id, '/test/file1.jpg', 'sha1', 'staging', 'success')
        log_file_import(test_db, batch_id, '/test/file2.jpg', 'sha2', 'organize', 'success')
        log_file_import(test_db, batch_id, '/test/file3.jpg', 'sha3', 'staging', 'success')

        logs = get_import_log_for_batch(test_db, batch_id, stage='staging')

        assert len(logs) == 2
        assert all(log['stage'] == 'staging' for log in logs)

    def test_filters_by_status(self, test_db, test_location):
        """Verify filtering by status."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        log_file_import(test_db, batch_id, '/test/file1.jpg', 'sha1', 'staging', 'success')
        log_file_import(test_db, batch_id, '/test/file2.jpg', 'sha2', 'staging', 'failed')
        log_file_import(test_db, batch_id, '/test/file3.jpg', 'sha3', 'staging', 'success')

        logs = get_import_log_for_batch(test_db, batch_id, status='failed')

        assert len(logs) == 1
        assert logs[0]['status'] == 'failed'

    def test_filters_by_stage_and_status(self, test_db, test_location):
        """Verify filtering by both stage and status."""
        batch_id = create_import_batch(test_db, test_location, '/test/path')

        log_file_import(test_db, batch_id, '/test/file1.jpg', 'sha1', 'staging', 'success')
        log_file_import(test_db, batch_id, '/test/file2.jpg', 'sha2', 'staging', 'failed')
        log_file_import(test_db, batch_id, '/test/file3.jpg', 'sha3', 'organize', 'failed')

        logs = get_import_log_for_batch(test_db, batch_id, stage='staging', status='failed')

        assert len(logs) == 1
        assert logs[0]['stage'] == 'staging'
        assert logs[0]['status'] == 'failed'


class TestBatchLifecycle:
    """Integration tests for full batch lifecycle."""

    def test_complete_import_workflow(self, test_db, test_location, test_config):
        """Verify complete batch lifecycle from creation to completion."""
        config, _ = test_config

        # Create backup
        success, backup_path, _ = create_backup_for_import(config)
        assert success

        # Create batch
        batch_id = create_import_batch(
            test_db,
            test_location,
            '/test/source/path',
            backup_path
        )

        # Log some file imports
        log_file_import(test_db, batch_id, '/test/file1.jpg', 'sha1', 'staging', 'success')
        log_file_import(test_db, batch_id, '/test/file2.jpg', 'sha2', 'staging', 'duplicate')
        log_file_import(test_db, batch_id, '/test/file3.jpg', 'sha3', 'staging', 'success')

        # Update batch progress
        update_import_batch(
            test_db,
            batch_id,
            total_files=3,
            files_imported=2,
            duplicates_found=1
        )

        # Complete batch
        complete_import_batch(test_db, batch_id, status='completed')

        # Verify final state
        status = get_import_batch_status(test_db, batch_id)
        assert status['status'] == 'completed'
        assert status['total_files'] == 3
        assert status['files_imported'] == 2
        assert status['duplicates_found'] == 1
        assert status['batch_end'] is not None

        logs = get_import_log_for_batch(test_db, batch_id)
        assert len(logs) == 3
