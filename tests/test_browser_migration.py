"""
Test suite for browser integration database migration

Tests schema additions for bookmarks table and urls table enhancements.

Version: 0.1.2-browser
Last Updated: 2025-11-18
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

# Import migration module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'migrations'))

from add_browser_tables import (
    get_table_columns,
    table_exists,
    column_exists,
    migrate_add_bookmarks_table,
    migrate_enhance_urls_table,
    run_migration
)


@pytest.fixture
def empty_db():
    """Create empty test database."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    Path(db_path).unlink()  # Remove empty file
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def base_db():
    """Create test database with base v0.1.2 schema (locations + urls)."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Create locations table
    cursor.execute("""
        CREATE TABLE locations (
            loc_uuid TEXT PRIMARY KEY,
            loc_name TEXT NOT NULL,
            state TEXT
        )
    """)

    # Create urls table (without browser columns)
    cursor.execute("""
        CREATE TABLE urls (
            url_uuid TEXT PRIMARY KEY,
            loc_uuid TEXT NOT NULL,
            url TEXT NOT NULL,
            url_title TEXT,
            url_desc TEXT,
            domain TEXT,
            archivebox_snapshot_id TEXT,
            archive_status TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    conn.commit()
    conn.close()

    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def migrated_db(base_db):
    """Create database with migration already applied."""
    run_migration(base_db)
    return base_db


class TestUtilityFunctions:
    """Test utility functions for schema inspection."""

    def test_table_exists_true(self, base_db):
        """Test table_exists returns True for existing table."""
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()
        assert table_exists(cursor, 'locations')
        assert table_exists(cursor, 'urls')
        conn.close()

    def test_table_exists_false(self, base_db):
        """Test table_exists returns False for non-existent table."""
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()
        assert not table_exists(cursor, 'bookmarks')
        assert not table_exists(cursor, 'nonexistent')
        conn.close()

    def test_get_table_columns(self, base_db):
        """Test get_table_columns returns column list."""
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()
        columns = get_table_columns(cursor, 'locations')
        assert 'loc_uuid' in columns
        assert 'loc_name' in columns
        assert 'state' in columns
        conn.close()

    def test_column_exists_true(self, base_db):
        """Test column_exists returns True for existing column."""
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()
        assert column_exists(cursor, 'locations', 'loc_uuid')
        assert column_exists(cursor, 'urls', 'url')
        conn.close()

    def test_column_exists_false(self, base_db):
        """Test column_exists returns False for non-existent column."""
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()
        assert not column_exists(cursor, 'urls', 'bookmark_uuid')
        assert not column_exists(cursor, 'urls', 'cookies_used')
        conn.close()


class TestBookmarksTableMigration:
    """Test bookmarks table creation."""

    def test_create_bookmarks_table(self, base_db):
        """Test creating bookmarks table."""
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()

        # Table should not exist initially
        assert not table_exists(cursor, 'bookmarks')

        # Run migration
        result = migrate_add_bookmarks_table(cursor)
        conn.commit()

        # Verify table created
        assert result is True
        assert table_exists(cursor, 'bookmarks')

        # Verify columns
        columns = get_table_columns(cursor, 'bookmarks')
        expected_columns = [
            'bookmark_uuid', 'loc_uuid', 'url', 'title', 'description',
            'favicon_url', 'folder', 'tags', 'created_at', 'updated_at',
            'visit_count', 'last_visited'
        ]
        for col in expected_columns:
            assert col in columns

        # Verify indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='bookmarks'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        assert 'idx_bookmarks_loc_uuid' in indexes
        assert 'idx_bookmarks_folder' in indexes

        conn.close()

    def test_create_bookmarks_table_idempotent(self, migrated_db):
        """Test creating bookmarks table when it already exists."""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()

        # Table should already exist
        assert table_exists(cursor, 'bookmarks')

        # Run migration again
        result = migrate_add_bookmarks_table(cursor)
        conn.commit()

        # Should return False (already exists)
        assert result is False
        assert table_exists(cursor, 'bookmarks')

        conn.close()


class TestUrlsTableEnhancement:
    """Test urls table column additions."""

    def test_enhance_urls_table(self, base_db):
        """Test adding browser columns to urls table."""
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()

        # Columns should not exist initially
        assert not column_exists(cursor, 'urls', 'bookmark_uuid')
        assert not column_exists(cursor, 'urls', 'cookies_used')
        assert not column_exists(cursor, 'urls', 'extraction_metadata')

        # Run migration
        columns_added = migrate_enhance_urls_table(cursor)
        conn.commit()

        # Verify columns added
        assert columns_added == 3
        assert column_exists(cursor, 'urls', 'bookmark_uuid')
        assert column_exists(cursor, 'urls', 'cookies_used')
        assert column_exists(cursor, 'urls', 'extraction_metadata')

        # Verify index exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='urls'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        assert 'idx_urls_bookmark_uuid' in indexes

        conn.close()

    def test_enhance_urls_table_idempotent(self, migrated_db):
        """Test enhancing urls table when columns already exist."""
        conn = sqlite3.connect(migrated_db)
        cursor = conn.cursor()

        # Columns should already exist
        assert column_exists(cursor, 'urls', 'bookmark_uuid')
        assert column_exists(cursor, 'urls', 'cookies_used')
        assert column_exists(cursor, 'urls', 'extraction_metadata')

        # Run migration again
        columns_added = migrate_enhance_urls_table(cursor)
        conn.commit()

        # Should return 0 (no columns added)
        assert columns_added == 0

        conn.close()


class TestFullMigration:
    """Test complete migration process."""

    def test_full_migration_new_database(self, base_db):
        """Test running complete migration on fresh database."""
        results = run_migration(base_db)

        assert results['success'] is True
        assert results['bookmarks_created'] is True
        assert results['urls_columns_added'] == 3
        assert results['error'] is None

        # Verify final state
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()

        assert table_exists(cursor, 'bookmarks')
        assert column_exists(cursor, 'urls', 'bookmark_uuid')

        conn.close()

    def test_full_migration_idempotent(self, migrated_db):
        """Test running migration multiple times is safe."""
        # Run migration again
        results = run_migration(migrated_db)

        assert results['success'] is True
        assert results['bookmarks_created'] is False  # Already existed
        assert results['urls_columns_added'] == 0  # Already existed
        assert results['error'] is None

    def test_full_migration_with_data(self, base_db):
        """Test migration preserves existing data."""
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()

        # Insert test data
        cursor.execute("""
            INSERT INTO locations (loc_uuid, loc_name, state)
            VALUES ('test-1', 'Test Location', 'NY')
        """)
        cursor.execute("""
            INSERT INTO urls (url_uuid, loc_uuid, url, url_title, domain)
            VALUES ('url-1', 'test-1', 'https://example.com', 'Example', 'example.com')
        """)
        conn.commit()
        conn.close()

        # Run migration
        results = run_migration(base_db)
        assert results['success'] is True

        # Verify data preserved
        conn = sqlite3.connect(base_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM locations WHERE loc_uuid = 'test-1'")
        location = cursor.fetchone()
        assert location is not None

        cursor.execute("SELECT * FROM urls WHERE url_uuid = 'url-1'")
        url_row = cursor.fetchone()
        assert url_row is not None

        # New columns should exist with NULL/default values
        columns = get_table_columns(cursor, 'urls')
        assert 'bookmark_uuid' in columns
        assert 'cookies_used' in columns

        conn.close()

    def test_migration_rollback_on_error(self, empty_db):
        """Test migration rolls back on error."""
        # Create database without urls table (will cause foreign key error)
        conn = sqlite3.connect(empty_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE locations (
                loc_uuid TEXT PRIMARY KEY,
                loc_name TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        # Run migration - should fail due to missing urls table
        with pytest.raises(Exception):
            run_migration(empty_db)

        # Verify bookmarks table was not created (transaction rolled back)
        conn = sqlite3.connect(empty_db)
        cursor = conn.cursor()
        assert not table_exists(cursor, 'bookmarks')
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
