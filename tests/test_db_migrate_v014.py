#!/usr/bin/env python3
"""
Test suite for database migration v0.1.4
Validates schema creation, indexes, and version tracking.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from db_migrate_v014 import (
    create_import_batches_table,
    create_import_log_table,
    migrate_images_table,
    migrate_videos_table,
    update_version,
    run_migration,
    table_exists,
    get_table_columns
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def temp_config(temp_db):
    """Create temporary config file."""
    config = {
        'db_name': 'test.db',
        'db_loc': temp_db,
        'db_ingest': '/tmp/test_ingest',
        'arch_loc': '/tmp/test_archive',
        'db_backup': '/tmp/test_backup'
    }

    fd, config_path = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fd, 'w') as f:
        import json
        json.dump(config, f)

    yield config_path

    # Cleanup
    try:
        os.unlink(config_path)
    except:
        pass


class TestImportBatchesTable:
    """Test import_batches table creation."""

    def test_creates_table_with_all_columns(self, temp_db):
        """Verify import_batches table has all required columns."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        create_import_batches_table(cursor)
        conn.commit()

        # Check table exists
        assert table_exists(cursor, 'import_batches')

        # Check all columns exist
        columns = get_table_columns(cursor, 'import_batches')
        expected_columns = [
            'batch_id', 'loc_uuid', 'source_path', 'batch_start', 'batch_end',
            'status', 'total_files', 'files_imported', 'files_skipped',
            'files_failed', 'duplicates_found', 'total_bytes',
            'backup_created', 'backup_path', 'error_log'
        ]

        for col in expected_columns:
            assert col in columns, f"Missing column: {col}"

        conn.close()

    def test_creates_indexes(self, temp_db):
        """Verify import_batches indexes are created."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        create_import_batches_table(cursor)
        conn.commit()

        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='import_batches'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        assert 'idx_import_batches_loc' in indexes
        assert 'idx_import_batches_status' in indexes
        assert 'idx_import_batches_start' in indexes

        conn.close()

    def test_idempotent(self, temp_db):
        """Verify running twice doesn't fail."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Create twice
        create_import_batches_table(cursor)
        create_import_batches_table(cursor)
        conn.commit()

        # Should still work
        assert table_exists(cursor, 'import_batches')

        conn.close()


class TestImportLogTable:
    """Test import_log table creation."""

    def test_creates_table_with_all_columns(self, temp_db):
        """Verify import_log table has all required columns."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        create_import_log_table(cursor)
        conn.commit()

        # Check table exists
        assert table_exists(cursor, 'import_log')

        # Check all columns exist
        columns = get_table_columns(cursor, 'import_log')
        expected_columns = [
            'log_id', 'batch_id', 'file_path', 'file_name', 'file_sha256',
            'file_size_bytes', 'media_type', 'timestamp', 'stage', 'status',
            'img_uuid', 'vid_uuid', 'hardware_category',
            'staging_path', 'archive_path', 'error_message'
        ]

        for col in expected_columns:
            assert col in columns, f"Missing column: {col}"

        conn.close()

    def test_creates_indexes(self, temp_db):
        """Verify import_log indexes are created."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        create_import_log_table(cursor)
        conn.commit()

        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='import_log'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        assert 'idx_import_log_batch' in indexes
        assert 'idx_import_log_sha256' in indexes
        assert 'idx_import_log_status' in indexes
        assert 'idx_import_log_stage' in indexes

        conn.close()


class TestImagesMigration:
    """Test images table migration."""

    def test_adds_archive_columns(self, temp_db):
        """Verify archive workflow columns added to images."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Create minimal images table first
        cursor.execute("""
            CREATE TABLE images (
                img_uuid TEXT PRIMARY KEY,
                loc_uuid TEXT NOT NULL,
                img_sha TEXT NOT NULL
            )
        """)

        # Run migration
        migrate_images_table(cursor)
        conn.commit()

        # Check new columns exist
        columns = get_table_columns(cursor, 'images')
        expected_new_columns = [
            'hardware_category', 'archive_path', 'staging_path',
            'import_batch_id', 'verified', 'verification_date'
        ]

        for col in expected_new_columns:
            assert col in columns, f"Missing new column: {col}"

        conn.close()

    def test_creates_indexes(self, temp_db):
        """Verify indexes created for new columns."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Create minimal images table
        cursor.execute("""
            CREATE TABLE images (
                img_uuid TEXT PRIMARY KEY,
                loc_uuid TEXT NOT NULL,
                img_sha TEXT NOT NULL
            )
        """)

        # Run migration
        migrate_images_table(cursor)
        conn.commit()

        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='images'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        assert 'idx_images_hardware' in indexes
        assert 'idx_images_batch' in indexes

        conn.close()


class TestVideosMigration:
    """Test videos table migration."""

    def test_adds_archive_columns(self, temp_db):
        """Verify archive workflow columns added to videos."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Create minimal videos table first
        cursor.execute("""
            CREATE TABLE videos (
                vid_uuid TEXT PRIMARY KEY,
                loc_uuid TEXT NOT NULL,
                vid_sha TEXT NOT NULL
            )
        """)

        # Run migration
        migrate_videos_table(cursor)
        conn.commit()

        # Check new columns exist
        columns = get_table_columns(cursor, 'videos')
        expected_new_columns = [
            'hardware_category', 'archive_path', 'staging_path',
            'import_batch_id', 'verified', 'verification_date'
        ]

        for col in expected_new_columns:
            assert col in columns, f"Missing new column: {col}"

        conn.close()


class TestVersionTracking:
    """Test version tracking functionality."""

    def test_sets_version_to_014(self, temp_db):
        """Verify version set to 0.1.4."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        update_version(cursor)
        conn.commit()

        # Check version
        cursor.execute("SELECT version FROM versions WHERE modules = 'aupat_core'")
        row = cursor.fetchone()

        assert row is not None, "Version record not found"
        assert row[0] == '0.1.4', f"Wrong version: {row[0]}"

        conn.close()

    def test_creates_versions_table_if_missing(self, temp_db):
        """Verify versions table created if doesn't exist."""
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Ensure table doesn't exist
        assert not table_exists(cursor, 'versions')

        update_version(cursor)
        conn.commit()

        # Check table created
        assert table_exists(cursor, 'versions')

        conn.close()


class TestFullMigration:
    """Test complete migration flow."""

    def test_fresh_database_migration(self, temp_db):
        """Test migration on fresh database."""
        # Run full migration
        run_migration(temp_db, backup=False)

        # Verify all tables exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Debug: List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        actual_tables = [row[0] for row in cursor.fetchall()]
        print(f"\nActual tables created: {actual_tables}")

        expected_tables = [
            'locations', 'images', 'videos', 'documents', 'urls',
            'import_batches', 'import_log', 'versions',
            'google_maps_exports', 'map_locations', 'sync_log'
        ]

        for table in expected_tables:
            assert table_exists(cursor, table), f"Missing table: {table}. Found: {actual_tables}"

        # Verify version
        cursor.execute("SELECT version FROM versions WHERE modules = 'aupat_core'")
        version = cursor.fetchone()[0]
        assert version == '0.1.4'

        conn.close()

    def test_preserves_existing_data(self, temp_db):
        """Test migration preserves existing data in tables."""
        # Create v0.1.3 database with test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Run v0.1.3 migration first
        from db_migrate_v012 import run_migration as run_v013_migration
        run_v013_migration(temp_db, backup=False)

        # Insert test data
        cursor.execute("""
            INSERT INTO locations (loc_uuid, loc_name, state, type)
            VALUES ('test-uuid', 'Test Location', 'NY', 'abandoned')
        """)
        cursor.execute("""
            INSERT INTO images (img_uuid, loc_uuid, img_sha, img_name)
            VALUES ('img-uuid', 'test-uuid', 'sha256hash', 'test.jpg')
        """)
        conn.commit()
        conn.close()

        # Run v0.1.4 migration
        run_migration(temp_db, backup=False)

        # Verify data preserved
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT loc_name FROM locations WHERE loc_uuid = 'test-uuid'")
        assert cursor.fetchone()[0] == 'Test Location'

        cursor.execute("SELECT img_name FROM images WHERE img_uuid = 'img-uuid'")
        assert cursor.fetchone()[0] == 'test.jpg'

        # Verify new columns exist
        columns = get_table_columns(cursor, 'images')
        assert 'hardware_category' in columns
        assert 'archive_path' in columns

        conn.close()

    def test_wal_mode_enabled(self, temp_db):
        """Verify WAL mode is enabled after migration."""
        run_migration(temp_db, backup=False)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]

        assert mode.lower() == 'wal', f"Wrong journal mode: {mode}"

        conn.close()

    def test_foreign_keys_enabled(self, temp_db):
        """Verify foreign keys can be enabled (test DB integrity)."""
        run_migration(temp_db, backup=False)

        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys")
        enabled = cursor.fetchone()[0]

        assert enabled == 1, "Foreign keys cannot be enabled"

        # Test that foreign key constraints are enforced
        cursor.execute("""
            INSERT INTO locations (loc_uuid, loc_name, state, type)
            VALUES ('test-loc', 'Test', 'NY', 'test')
        """)

        # This should fail - referencing non-existent location
        try:
            cursor.execute("""
                INSERT INTO images (img_uuid, loc_uuid, img_sha)
                VALUES ('test-img', 'non-existent', 'sha')
            """)
            conn.commit()
            assert False, "Foreign key constraint not enforced"
        except sqlite3.IntegrityError:
            # Expected - foreign key constraint works
            pass

        conn.close()


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_handles_missing_directory(self):
        """Test migration creates parent directory if missing."""
        import tempfile
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, 'subdir', 'test.db')

        try:
            run_migration(db_path, backup=False)
            assert os.path.exists(db_path)
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_migration_idempotent(self, temp_db):
        """Test running migration twice is safe."""
        run_migration(temp_db, backup=False)
        run_migration(temp_db, backup=False)  # Run again

        # Should succeed without errors
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Verify still at v0.1.4
        cursor.execute("SELECT version FROM versions WHERE modules = 'aupat_core'")
        version = cursor.fetchone()[0]
        assert version == '0.1.4'

        conn.close()
