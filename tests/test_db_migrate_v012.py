"""
Unit and integration tests for db_migrate_v012.py

Tests:
- Column addition to existing tables
- New table creation
- Index creation
- Idempotent migration (run twice safely)
- Version tracking
- Error handling
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from db_migrate_v012 import (
    migrate_locations_table,
    migrate_images_table,
    migrate_videos_table,
    migrate_urls_table,
    create_google_maps_exports_table,
    create_sync_log_table,
    create_indexes,
    update_version,
    get_table_columns,
    table_exists
)


@pytest.fixture
def temp_db():
    """Create temporary SQLite database with base schema."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create base v0.1.0 schema
    cursor.execute("""
        CREATE TABLE locations (
            loc_uuid TEXT PRIMARY KEY,
            loc_name TEXT NOT NULL,
            state TEXT NOT NULL,
            type TEXT NOT NULL,
            loc_add TEXT,
            loc_update TEXT,
            imp_author TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE images (
            img_sha256 TEXT UNIQUE NOT NULL,
            img_name TEXT NOT NULL,
            img_loc TEXT NOT NULL,
            loc_uuid TEXT NOT NULL,
            img_add TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    cursor.execute("""
        CREATE TABLE videos (
            vid_sha256 TEXT UNIQUE NOT NULL,
            vid_name TEXT NOT NULL,
            vid_loc TEXT NOT NULL,
            loc_uuid TEXT NOT NULL,
            vid_add TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    cursor.execute("""
        CREATE TABLE urls (
            url_uuid TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            loc_uuid TEXT NOT NULL,
            url_add TEXT,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink()


def test_migrate_locations_table(temp_db):
    """Test that locations table migration adds all required columns."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Run migration
    migrate_locations_table(cursor)
    conn.commit()

    # Check columns exist
    columns = get_table_columns(cursor, 'locations')

    expected_columns = [
        'lat', 'lon', 'gps_source', 'gps_confidence',
        'street_address', 'city', 'state_abbrev', 'zip_code',
        'country', 'address_source'
    ]

    for col in expected_columns:
        assert col in columns, f"Column {col} not found in locations table"

    conn.close()


def test_migrate_images_table(temp_db):
    """Test that images table migration adds all required columns."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    migrate_images_table(cursor)
    conn.commit()

    columns = get_table_columns(cursor, 'images')

    expected_columns = [
        'immich_asset_id', 'img_width', 'img_height',
        'img_size_bytes', 'gps_lat', 'gps_lon'
    ]

    for col in expected_columns:
        assert col in columns, f"Column {col} not found in images table"

    conn.close()


def test_migrate_videos_table(temp_db):
    """Test that videos table migration adds all required columns."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    migrate_videos_table(cursor)
    conn.commit()

    columns = get_table_columns(cursor, 'videos')

    expected_columns = [
        'immich_asset_id', 'vid_width', 'vid_height',
        'vid_duration_sec', 'vid_size_bytes', 'gps_lat', 'gps_lon'
    ]

    for col in expected_columns:
        assert col in columns, f"Column {col} not found in videos table"

    conn.close()


def test_migrate_urls_table(temp_db):
    """Test that urls table migration adds all required columns."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    migrate_urls_table(cursor)
    conn.commit()

    columns = get_table_columns(cursor, 'urls')

    expected_columns = [
        'archivebox_snapshot_id', 'archive_status',
        'archive_date', 'media_extracted'
    ]

    for col in expected_columns:
        assert col in columns, f"Column {col} not found in urls table"

    conn.close()


def test_create_new_tables(temp_db):
    """Test creation of new tables."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Create google_maps_exports table
    create_google_maps_exports_table(cursor)
    assert table_exists(cursor, 'google_maps_exports')

    # Check columns
    columns = get_table_columns(cursor, 'google_maps_exports')
    expected = ['export_id', 'import_date', 'file_path', 'locations_found']
    for col in expected:
        assert col in columns

    # Create sync_log table
    create_sync_log_table(cursor)
    assert table_exists(cursor, 'sync_log')

    columns = get_table_columns(cursor, 'sync_log')
    expected = ['sync_id', 'device_id', 'sync_type', 'timestamp']
    for col in expected:
        assert col in columns

    conn.close()


def test_idempotent_migration(temp_db):
    """Test that migration can be run multiple times safely."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Run migration first time
    migrate_locations_table(cursor)
    migrate_images_table(cursor)
    migrate_videos_table(cursor)
    migrate_urls_table(cursor)
    create_google_maps_exports_table(cursor)
    create_sync_log_table(cursor)
    conn.commit()

    # Get column counts
    loc_cols_1 = len(get_table_columns(cursor, 'locations'))
    img_cols_1 = len(get_table_columns(cursor, 'images'))

    # Run migration second time (should not error)
    migrate_locations_table(cursor)
    migrate_images_table(cursor)
    migrate_videos_table(cursor)
    migrate_urls_table(cursor)
    create_google_maps_exports_table(cursor)
    create_sync_log_table(cursor)
    conn.commit()

    # Column counts should be same
    loc_cols_2 = len(get_table_columns(cursor, 'locations'))
    img_cols_2 = len(get_table_columns(cursor, 'images'))

    assert loc_cols_1 == loc_cols_2, "Idempotent migration changed column count"
    assert img_cols_1 == img_cols_2, "Idempotent migration changed column count"

    conn.close()


def test_create_indexes(temp_db):
    """Test that indexes are created successfully."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Run migrations first
    migrate_locations_table(cursor)
    migrate_images_table(cursor)
    migrate_videos_table(cursor)
    conn.commit()

    # Create indexes
    create_indexes(cursor)
    conn.commit()

    # Check indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]

    expected_indexes = [
        'idx_locations_gps',
        'idx_images_immich',
        'idx_videos_immich',
        'idx_images_gps',
        'idx_videos_gps'
    ]

    for idx in expected_indexes:
        assert idx in indexes, f"Index {idx} not created"

    conn.close()


def test_version_tracking(temp_db):
    """Test that schema version is updated correctly."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Create versions table
    cursor.execute("""
        CREATE TABLE versions (
            modules TEXT PRIMARY KEY,
            version TEXT NOT NULL,
            ver_updated TEXT NOT NULL
        )
    """)
    conn.commit()

    # Update version
    update_version(cursor)
    conn.commit()

    # Check version
    cursor.execute("SELECT version FROM versions WHERE modules = 'aupat_core'")
    row = cursor.fetchone()

    assert row is not None, "Version not inserted"
    assert row[0] == '0.1.2', f"Expected version 0.1.2, got {row[0]}"

    conn.close()


def test_migration_with_existing_data(temp_db):
    """Test that migration preserves existing data."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Insert test data
    cursor.execute("""
        INSERT INTO locations (loc_uuid, loc_name, state, type, loc_add, loc_update, imp_author)
        VALUES ('test-uuid', 'Test Location', 'NY', 'industrial', '2024-01-01', '2024-01-01', 'tester')
    """)
    conn.commit()

    # Run migration
    migrate_locations_table(cursor)
    conn.commit()

    # Check data still exists
    cursor.execute("SELECT loc_name FROM locations WHERE loc_uuid = 'test-uuid'")
    row = cursor.fetchone()

    assert row is not None, "Data lost during migration"
    assert row[0] == 'Test Location', "Data corrupted during migration"

    conn.close()


def test_foreign_key_preservation(temp_db):
    """Test that foreign keys are preserved after migration."""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Insert test data with foreign key relationship
    cursor.execute("""
        INSERT INTO locations (loc_uuid, loc_name, state, type)
        VALUES ('loc-1', 'Test', 'NY', 'industrial')
    """)
    cursor.execute("""
        INSERT INTO images (img_sha256, img_name, img_loc, loc_uuid)
        VALUES ('abc123', 'test.jpg', '/tmp/test.jpg', 'loc-1')
    """)
    conn.commit()

    # Run migration
    migrate_images_table(cursor)
    conn.commit()

    # Try to insert image with non-existent location (should fail)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO images (img_sha256, img_name, img_loc, loc_uuid)
            VALUES ('def456', 'test2.jpg', '/tmp/test2.jpg', 'non-existent')
        """)
        conn.commit()

    conn.close()
