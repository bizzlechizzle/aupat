#!/usr/bin/env python3
"""
AUPAT Database Schema (v0.1.0)

LILBITS: One Script = One Primary Function
Purpose: Define SQLite database schema for AUPAT

Design Philosophy:
- Store FULL hashes (UUID4 36-char, SHA256 64-char) in database
- Compute 12-char versions when needed for filenames
- Normalize all text fields before insert
- Use foreign keys for data integrity

Version: 1.0.0
Date: 2025-11-18
"""

import sqlite3
from pathlib import Path
from typing import Optional


# Database schema version (for migrations)
SCHEMA_VERSION = 1


def create_database(db_path: Path) -> sqlite3.Connection:
    """
    Create new AUPAT database with schema.

    Creates all tables with proper indexes and foreign keys.
    Returns connection for further operations.

    Args:
        db_path: Path to SQLite database file

    Returns:
        sqlite3.Connection: Database connection

    Example:
        >>> conn = create_database(Path("aupat.db"))
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT COUNT(*) FROM locations")
        >>> conn.close()

    Technical Details:
        - Uses WAL mode for better concurrency
        - Foreign keys enabled for referential integrity
        - Indexes on frequently queried fields
        - All text fields use TEXT type (SQLite best practice)
        - Timestamps as ISO 8601 strings
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable WAL mode for better concurrency
    # (allows reads while writing)
    cursor.execute("PRAGMA journal_mode=WAL")

    # Enable foreign keys for referential integrity
    cursor.execute("PRAGMA foreign_keys=ON")

    # Create schema version table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert schema version
    cursor.execute(
        "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
        (SCHEMA_VERSION,)
    )

    # Create locations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            loc_uuid TEXT PRIMARY KEY,           -- Full UUID4 (36 chars)
            loc_name TEXT NOT NULL,               -- Normalized name (title case)
            loc_short TEXT NOT NULL,              -- Short name (filesystem-safe)
            sub_location TEXT,                    -- Sub-location name (optional)
            is_primary_sub BOOLEAN DEFAULT 0,     -- Primary sub-location flag
            status TEXT,                          -- Abandoned, Demolished, etc.
            explored TEXT,                        -- Interior, Exterior, etc.
            type TEXT NOT NULL,                   -- Location type
            sub_type TEXT,                        -- Location sub-type
            street TEXT,                          -- Street address
            city TEXT,                            -- City
            state TEXT NOT NULL,                  -- 2-letter state code (lowercase)
            zip_code TEXT,                        -- ZIP code
            county TEXT,                          -- County name
            region TEXT,                          -- Region name
            gps_lat REAL,                         -- GPS latitude
            gps_lon REAL,                         -- GPS longitude
            gps_source TEXT,                      -- GPS source (manual, exif, etc.)
            import_author TEXT,                   -- Author who imported
            historical BOOLEAN DEFAULT 0,         -- Historical flag
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create images table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            img_sha256 TEXT PRIMARY KEY,          -- Full SHA256 (64 chars)
            loc_uuid TEXT NOT NULL,               -- Location UUID
            sub_uuid TEXT,                        -- Sub-location UUID (optional)
            img_name TEXT NOT NULL,               -- Filename (locuuid12-imgsha12.ext)
            img_path TEXT NOT NULL,               -- Full path in archive
            img_original_name TEXT,               -- Original filename
            img_original_path TEXT,               -- Original location
            img_extension TEXT NOT NULL,          -- File extension (.jpg, .png, etc.)
            img_size_bytes INTEGER,               -- File size
            img_width INTEGER,                    -- Image width (pixels)
            img_height INTEGER,                   -- Image height (pixels)
            exif_make TEXT,                       -- Camera make (from EXIF)
            exif_model TEXT,                      -- Camera model (from EXIF)
            exif_datetime TEXT,                   -- Photo taken datetime (from EXIF)
            exif_gps_lat REAL,                    -- GPS from EXIF
            exif_gps_lon REAL,                    -- GPS from EXIF
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
        )
    """)

    # Create videos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            vid_sha256 TEXT PRIMARY KEY,          -- Full SHA256 (64 chars)
            loc_uuid TEXT NOT NULL,               -- Location UUID
            sub_uuid TEXT,                        -- Sub-location UUID (optional)
            vid_name TEXT NOT NULL,               -- Filename (locuuid12-vidsha12.ext)
            vid_path TEXT NOT NULL,               -- Full path in archive
            vid_original_name TEXT,               -- Original filename
            vid_original_path TEXT,               -- Original location
            vid_extension TEXT NOT NULL,          -- File extension (.mp4, .mov, etc.)
            vid_size_bytes INTEGER,               -- File size
            vid_width INTEGER,                    -- Video width (pixels)
            vid_height INTEGER,                   -- Video height (pixels)
            vid_duration_seconds REAL,            -- Duration in seconds
            vid_codec TEXT,                       -- Video codec
            vid_make TEXT,                        -- Camera make (from metadata)
            vid_model TEXT,                       -- Camera model (from metadata)
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
        )
    """)

    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_sha256 TEXT PRIMARY KEY,          -- Full SHA256 (64 chars)
            loc_uuid TEXT NOT NULL,               -- Location UUID
            sub_uuid TEXT,                        -- Sub-location UUID (optional)
            doc_name TEXT NOT NULL,               -- Filename (locuuid12-docsha12.ext)
            doc_path TEXT NOT NULL,               -- Full path in archive
            doc_original_name TEXT,               -- Original filename
            doc_original_path TEXT,               -- Original location
            doc_extension TEXT NOT NULL,          -- File extension (.pdf, .docx, etc.)
            doc_size_bytes INTEGER,               -- File size
            doc_type TEXT,                        -- Document type (auto-detected)
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
        )
    """)

    # Create urls table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            url_uuid TEXT PRIMARY KEY,            -- Full UUID4 (36 chars)
            loc_uuid TEXT NOT NULL,               -- Location UUID
            sub_uuid TEXT,                        -- Sub-location UUID (optional)
            url TEXT NOT NULL,                    -- URL
            url_title TEXT,                       -- Page title (from scraping)
            url_archived BOOLEAN DEFAULT 0,       -- Archived with ArchiveBox
            url_archived_path TEXT,               -- Path to archived copy
            added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
        )
    """)

    # Create maps table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maps (
            map_sha256 TEXT PRIMARY KEY,          -- Full SHA256 (64 chars)
            loc_uuid TEXT NOT NULL,               -- Location UUID
            sub_uuid TEXT,                        -- Sub-location UUID (optional)
            map_name TEXT NOT NULL,               -- Filename (locuuid12-mapsha12.ext)
            map_path TEXT NOT NULL,               -- Full path in archive
            map_original_name TEXT,               -- Original filename
            map_original_path TEXT,               -- Original location
            map_extension TEXT NOT NULL,          -- File extension (.kml, .gpx, etc.)
            map_size_bytes INTEGER,               -- File size
            map_format TEXT,                      -- Map format (KML, GPX, GeoJSON, etc.)
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
        )
    """)

    # Create indexes for frequently queried fields
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_state ON locations(state)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_loc ON images(loc_uuid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_loc ON videos(loc_uuid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_loc ON documents(loc_uuid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_urls_loc ON urls(loc_uuid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_maps_loc ON maps(loc_uuid)")

    # Commit and return
    conn.commit()
    return conn


def get_schema_version(conn: sqlite3.Connection) -> Optional[int]:
    """
    Get current schema version from database.

    Args:
        conn: Database connection

    Returns:
        int: Schema version, or None if not set
    """
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return None


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python schema.py <database_path>")
        print("Example: python schema.py aupat.db")
        sys.exit(1)

    db_path = Path(sys.argv[1])

    print(f"Creating database: {db_path}")
    conn = create_database(db_path)

    version = get_schema_version(conn)
    print(f"Schema version: {version}")

    # Show table stats
    cursor = conn.cursor()
    tables = ['locations', 'images', 'videos', 'documents', 'urls', 'maps']

    print("\nTable Counts:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count}")

    conn.close()
    print("\nDatabase created successfully!")
