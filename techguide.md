# AUPAT Technical Guide

Version: 1.0.0
Last Updated: 2025-11-18

Complete technical reference for the Abandoned Upstate Photo & Archive Tracker (AUPAT) project.

---

## TABLE OF CONTENTS

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Directory Structure](#directory-structure)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [File Dependencies](#file-dependencies)
8. [Configuration](#configuration)
9. [Deployment Modes](#deployment-modes)
10. [External Services](#external-services)
11. [Development Workflow](#development-workflow)
12. [Key Rules and Patterns](#key-rules-and-patterns)
13. [Troubleshooting](#troubleshooting)

---

## PROJECT OVERVIEW

### What is AUPAT?

AUPAT is a location-centric digital archive system for documenting abandoned and historical locations. It provides:

- Interactive map interface with Leaflet
- Blog-style location pages with rich metadata
- Photo management with EXIF extraction
- Web page archiving via ArchiveBox integration
- Browser bookmarks synchronization
- Cross-platform support (desktop, mobile, web)

### Key Metrics

- **10,552 LOC** in Python backend
- **27,402 LOC** in test suite (70% coverage enforced)
- **43 Python scripts** organized by function
- **40+ REST API endpoints**
- **7 core database tables** (SQLite)
- **3-tier architecture** (Frontend, API, Database)

### Version

Current: v0.1.2 (with v0.1.3 and v0.1.4 migrations available)

---

## ARCHITECTURE

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Desktop    │    │    Mobile    │    │   Browser    │     │
│  │  (Electron)  │    │   (Flutter)  │    │ (Bookmarks)  │     │
│  │   Svelte     │    │    Dart      │    │   Native     │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└────────────────────────┬──────────────────────────────────────┘
                         │ REST API (HTTP/JSON)
┌────────────────────────▼──────────────────────────────────────┐
│                    APPLICATION LAYER                           │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           Flask Application (app.py)                 │    │
│  │  ┌────────────────────────────────────────────┐     │    │
│  │  │      API Routes (api_routes_v012.py)      │     │    │
│  │  │  • Locations CRUD • Images • Search       │     │    │
│  │  │  • Map markers • Health checks            │     │    │
│  │  └────────────────────────────────────────────┘     │    │
│  │  ┌────────────────────────────────────────────┐     │    │
│  │  │      External Service Adapters            │     │    │
│  │  │  • Immich (photos) • ArchiveBox (web)     │     │    │
│  │  └────────────────────────────────────────────┘     │    │
│  │  ┌────────────────────────────────────────────┐     │    │
│  │  │      Business Logic & Processing           │     │    │
│  │  │  • Media extraction • Data normalization   │     │    │
│  │  │  • Import handling • Background workers    │     │    │
│  │  └────────────────────────────────────────────┘     │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────┬──────────────────────────────────────┘
                         │ SQLite
┌────────────────────────▼──────────────────────────────────────┐
│                       DATA LAYER                               │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  SQLite Database (data/aupat.db)                     │    │
│  │  • locations • images • videos • urls                │    │
│  │  • bookmarks • google_maps_exports • sync_log        │    │
│  └──────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  External Services (Optional)                        │    │
│  │  • Immich (photo management)                         │    │
│  │  • ArchiveBox (web archiving)                        │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Clear separation of concerns** - Frontend, API, Database
2. **Modular design** - Each script does one thing (LILBITS principle)
3. **Graceful degradation** - External services optional
4. **Data integrity** - Transaction boundaries, SHA256 verification
5. **Extensibility** - Easy to add new location types, adapters

---

## TECHNOLOGY STACK

### Backend
- **Python 3.11+** - Application language
- **Flask 3.0** - Web framework
- **SQLite 3** - Database
- **PIL/Pillow** - Image processing
- **ExifTool** - EXIF metadata extraction
- **FFmpeg** - Video metadata extraction
- **Requests** - HTTP client
- **Tenacity** - Retry logic

### Frontend (Desktop)
- **Electron 33.0.0** - Desktop app framework
- **Svelte 4** - UI framework
- **Vite 5** - Build tool
- **Leaflet** - Interactive maps
- **Marked** - Markdown rendering
- **TailwindCSS** - Styling

### Frontend (Mobile)
- **Flutter** - Mobile framework
- **Dart** - Programming language

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **GitHub Actions** - CI/CD
- **pytest** - Testing framework

### External Services (Optional)
- **Immich** - Photo management
- **ArchiveBox** - Web archiving
- **PostgreSQL** - Immich database
- **Redis** - Immich caching

---

## DIRECTORY STRUCTURE

```
aupat/
├── app.py                          # Flask application entry point
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Test configuration
│
├── claude.md                       # Development rules and processes
├── techguide.md                    # This file - technical reference
├── lilbits.md                      # Script documentation
├── todo.md                         # Task tracking
├── README.md                       # Project documentation
│
├── scripts/                        # Backend Python modules (10.5K LOC)
│   ├── __init__.py
│   │
│   ├── api_routes_v012.py         # Main API routes (1.7K LOC)
│   ├── api_routes_bookmarks.py    # Bookmarks API (547 LOC)
│   ├── api_maps.py                # Map import API (571 LOC)
│   ├── api_sync_mobile.py         # Mobile sync API (11.7K LOC)
│   │
│   ├── db_migrate_v012.py         # Schema v0.1.2 (658 LOC)
│   ├── db_migrate_v013.py         # Schema v0.1.3 (11.4K LOC)
│   ├── db_migrate_v014.py         # Schema v0.1.4 (13.2K LOC)
│   │
│   ├── db_import_v012.py          # Import media (412 LOC)
│   ├── db_organize.py             # Extract EXIF (422 LOC)
│   ├── db_folder.py               # Create folders (371 LOC)
│   ├── db_ingest.py               # Move files (464 LOC)
│   ├── db_verify.py               # Verify integrity (354 LOC)
│   ├── backup.py                  # Backup/restore (378 LOC)
│   │
│   ├── archive_worker.py          # Web archiving daemon (545 LOC)
│   ├── media_extractor.py         # Media extraction daemon (644 LOC)
│   │
│   ├── utils.py                   # Common utilities (430 LOC)
│   ├── normalize.py               # Text normalization (500 LOC)
│   ├── import_helpers.py          # Import tracking (338 LOC)
│   ├── map_import.py              # Map parsing (791 LOC)
│   ├── immich_integration.py      # Immich integration (415 LOC)
│   │
│   ├── adapters/                  # External service adapters
│   │   ├── __init__.py
│   │   ├── immich_adapter.py      # Immich HTTP API (~500 LOC)
│   │   └── archivebox_adapter.py  # ArchiveBox HTTP API (~530 LOC)
│   │
│   ├── migrations/                # Database migrations
│   │   ├── add_browser_tables.py     # Browser support (8.4K LOC)
│   │   └── add_performance_indexes.py # Indexes (6.5K LOC)
│   │
│   └── advanced/
│       └── start_api.sh           # Advanced startup script
│
├── tests/                         # Test suite (27.4K LOC, 70% coverage)
│   ├── test_*.py                  # Unit and integration tests
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── conftest.py                # Test fixtures
│
├── desktop/                       # Electron desktop app (1.7M)
│   ├── package.json
│   ├── src/
│   │   ├── main/                  # Electron main process
│   │   │   ├── index.js           # Main process (28.7K LOC)
│   │   │   ├── api-client.js      # API client (5.3K LOC)
│   │   │   └── browser-manager.js # Browser integration (11.4K LOC)
│   │   ├── renderer/              # Svelte UI
│   │   │   ├── lib/               # Svelte components
│   │   │   │   ├── Map.svelte
│   │   │   │   ├── LocationPage.svelte
│   │   │   │   ├── LocationsList.svelte
│   │   │   │   └── ...
│   │   │   └── stores/            # State management
│   │   └── preload/               # IPC bridge
│   └── tests/                     # Desktop tests
│
├── mobile/                        # Flutter mobile app
│   ├── pubspec.yaml
│   ├── lib/
│   │   ├── api/                   # API client
│   │   ├── screens/               # UI screens
│   │   └── services/              # Services
│   └── test/
│
├── data/                          # Data files and database
│   ├── aupat.db                   # SQLite database (gitignored)
│   ├── locations.json             # Location type definitions
│   ├── camera_hardware.json       # Camera database
│   ├── folder.json                # Folder structure template
│   ├── location_type_mapping.json # Type mappings
│   └── ...
│
├── user/                          # User configuration
│   └── user.json.template         # Config template
│
├── docs/                          # Documentation
│   ├── v0.1.2/                    # Versioned docs
│   └── dependency_*.* # Dependency maps
│
├── archive/                       # Archived v0.1.0 code
│   └── v0.1.0/                    # Historical reference
│
├── start_aupat.sh                 # Start full stack
├── start_server.sh                # Start API only
├── docker-start.sh                # Start with Docker
├── install.sh                     # System setup
├── update_and_start.sh            # Update and restart
│
├── docker-compose.yml             # Docker Compose config
├── Dockerfile                     # Python container
└── .env.example                   # Environment template
```

---

## DATABASE SCHEMA

### Core Tables

#### locations
Main location records

```sql
CREATE TABLE locations (
    loc_uuid TEXT PRIMARY KEY,      -- Unique identifier
    loc_name TEXT NOT NULL,          -- Location name
    aka_name TEXT,                   -- Alternate names
    type TEXT,                       -- Location type (industrial, residential, etc.)
    sub_type TEXT,                   -- Subcategory
    state TEXT,                      -- US state code (NY, PA, etc.)
    city TEXT,                       -- City name
    street_address TEXT,             -- Street address
    zip_code TEXT,                   -- ZIP code
    lat REAL,                        -- Latitude
    lon REAL,                        -- Longitude
    gps_source TEXT,                 -- How GPS obtained (manual, exif, geocoded)
    org_loc TEXT,                    -- Original location string
    loc_loc TEXT,                    -- File system location
    imp_author TEXT,                 -- Author who added location
    loc_add TEXT,                    -- Date added (ISO 8601)
    loc_update TEXT,                 -- Date last updated (ISO 8601)
    source_map_id TEXT,              -- Reference to import source (v0.1.3+)
    -- Additional fields for description, notes, etc.
);

CREATE INDEX idx_locations_type ON locations(type);
CREATE INDEX idx_locations_state ON locations(state);
```

#### images
Photo metadata

```sql
CREATE TABLE images (
    img_uuid TEXT PRIMARY KEY,       -- Unique identifier
    loc_uuid TEXT,                   -- Associated location (FK)
    img_name TEXT,                   -- Display name
    img_fn TEXT,                     -- Original filename
    img_loc TEXT,                    -- File system path
    img_sha256 TEXT UNIQUE,          -- Content hash (deduplication)
    img_width INTEGER,               -- Width in pixels
    img_height INTEGER,              -- Height in pixels
    img_size_bytes INTEGER,          -- File size
    camera TEXT,                     -- Camera model
    hardware_category TEXT,          -- Hardware classification (v0.1.4+)
    gps_lat REAL,                    -- GPS latitude from EXIF
    gps_lon REAL,                    -- GPS longitude from EXIF
    img_add TEXT,                    -- Date added
    img_taken TEXT,                  -- Date photo taken (from EXIF)
    immich_asset_id TEXT,            -- Immich integration
    archive_path TEXT,               -- Archive location (v0.1.4+)
    import_batch_id TEXT,            -- Import batch tracking (v0.1.4+)
    FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
);

CREATE INDEX idx_images_loc_uuid ON images(loc_uuid);
CREATE INDEX idx_images_sha256 ON images(img_sha256);
```

#### videos
Video metadata

```sql
CREATE TABLE videos (
    vid_uuid TEXT PRIMARY KEY,       -- Unique identifier
    loc_uuid TEXT,                   -- Associated location (FK)
    vid_name TEXT,                   -- Display name
    vid_fn TEXT,                     -- Original filename
    vid_loc TEXT,                    -- File system path
    vid_sha256 TEXT UNIQUE,          -- Content hash
    vid_width INTEGER,               -- Width in pixels
    vid_height INTEGER,              -- Height in pixels
    vid_duration REAL,               -- Duration in seconds
    vid_size_bytes INTEGER,          -- File size
    camera TEXT,                     -- Camera model
    hardware_category TEXT,          -- Hardware classification (v0.1.4+)
    gps_lat REAL,                    -- GPS latitude
    gps_lon REAL,                    -- GPS longitude
    vid_add TEXT,                    -- Date added
    vid_taken TEXT,                  -- Date video taken
    immich_asset_id TEXT,            -- Immich integration
    archive_path TEXT,               -- Archive location (v0.1.4+)
    import_batch_id TEXT,            -- Import batch tracking (v0.1.4+)
    FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
);

CREATE INDEX idx_videos_loc_uuid ON videos(loc_uuid);
```

#### urls
Archived web pages

```sql
CREATE TABLE urls (
    url_uuid TEXT PRIMARY KEY,       -- Unique identifier
    loc_uuid TEXT,                   -- Associated location (FK)
    url_link TEXT NOT NULL,          -- URL
    url_title TEXT,                  -- Page title
    url_add TEXT,                    -- Date added
    archive_status TEXT,             -- Status: pending, archived, failed
    archivebox_snapshot_id TEXT,     -- ArchiveBox integration
    media_extracted INTEGER DEFAULT 0, -- Media extraction count
    FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
);

CREATE INDEX idx_urls_loc_uuid ON urls(loc_uuid);
CREATE INDEX idx_urls_status ON urls(archive_status);
```

#### bookmarks
Browser bookmarks (v0.1.2-browser+)

```sql
CREATE TABLE bookmarks (
    bookmark_uuid TEXT PRIMARY KEY,   -- Unique identifier
    url TEXT NOT NULL,                -- Bookmark URL
    title TEXT,                       -- Bookmark title
    folder TEXT,                      -- Browser folder
    tags TEXT,                        -- Comma-separated tags
    browser TEXT,                     -- Browser source (chrome, firefox, safari)
    loc_uuid TEXT,                    -- Associated location (FK, nullable)
    date_added TEXT,                  -- Date added
    FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
);

CREATE INDEX idx_bookmarks_url ON bookmarks(url);
CREATE INDEX idx_bookmarks_title ON bookmarks(title);
```

### Support Tables

#### google_maps_exports
Map import tracking

```sql
CREATE TABLE google_maps_exports (
    export_id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,           -- Original filename
    file_size INTEGER,                -- File size in bytes
    file_hash TEXT,                   -- SHA256 hash
    import_date TEXT,                 -- Import timestamp
    import_mode TEXT,                 -- Mode: full or reference
    location_count INTEGER,           -- Number of locations
    status TEXT,                      -- Import status
    -- Additional fields from v0.1.3+
);
```

#### sync_log
Mobile sync tracking

```sql
CREATE TABLE sync_log (
    sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,          -- Mobile device ID
    sync_type TEXT,                   -- Type: push or pull
    timestamp TEXT,                   -- Sync timestamp
    items_synced INTEGER,             -- Number of items
    conflicts INTEGER,                -- Number of conflicts
    status TEXT                       -- Success or error
);
```

#### import_batches
Import batch tracking (v0.1.4+)

```sql
CREATE TABLE import_batches (
    batch_id TEXT PRIMARY KEY,        -- Batch UUID
    import_type TEXT,                 -- Type: media, map, manual
    start_time TEXT,                  -- Start timestamp
    end_time TEXT,                    -- End timestamp
    status TEXT,                      -- Status: pending, completed, failed
    total_files INTEGER,              -- Total files processed
    success_count INTEGER,            -- Successful imports
    error_count INTEGER,              -- Failed imports
    notes TEXT                        -- Additional notes
);
```

### Migration Sequence

Migrations must be run in this order:

1. **db_migrate_v012.py** - Base schema (locations, images, videos, urls, etc.)
2. **db_migrate_v013.py** - Map improvements (map_reference_cache, source_map_id)
3. **db_migrate_v014.py** - Import tracking (import_batches, import_log)
4. **migrations/add_browser_tables.py** - Browser bookmarks (bookmarks table)
5. **migrations/add_performance_indexes.py** - Query optimization indexes

---

## API ENDPOINTS

### Base URL
```
http://localhost:5002/api
```

### Health & Status

```
GET /api/health
```
Basic health check. Returns database status and version.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.2",
  "database": "connected",
  "location_count": 42
}
```

```
GET /api/health/services
```
Check external services (Immich, ArchiveBox).

**Response:**
```json
{
  "immich": "healthy",
  "archivebox": "unavailable"
}
```

### Locations

```
GET /api/locations
```
List all locations (WARNING: no pagination, returns all).

**Query parameters:**
- None currently (TODO: add pagination)

**Response:**
```json
{
  "locations": [
    {
      "loc_uuid": "abc123",
      "loc_name": "Abandoned Hospital",
      "type": "medical",
      "state": "NY",
      "lat": 42.123,
      "lon": -73.456
    }
  ]
}
```

```
GET /api/locations/{uuid}
```
Get specific location with full details.

**Response:**
```json
{
  "loc_uuid": "abc123",
  "loc_name": "Abandoned Hospital",
  "aka_name": "Old County Hospital",
  "type": "medical",
  "sub_type": "hospital",
  "state": "NY",
  "city": "Albany",
  "lat": 42.123,
  "lon": -73.456,
  "gps_source": "manual",
  "imp_author": "explorer",
  "loc_add": "2024-01-15T10:30:00Z",
  "loc_update": "2024-02-20T14:15:00Z"
}
```

```
POST /api/locations
```
Create new location.

**Request body:**
```json
{
  "loc_name": "New Location",
  "type": "industrial",
  "state": "NY",
  "lat": 42.5,
  "lon": -73.8
}
```

```
PUT /api/locations/{uuid}
```
Update existing location.

```
DELETE /api/locations/{uuid}
```
Delete location (and associated media).

### Images

```
GET /api/locations/{uuid}/images
```
Get images for location.

**Query parameters:**
- `limit` (default: 50)
- `offset` (default: 0)

**Response:**
```json
{
  "images": [
    {
      "img_uuid": "img123",
      "img_name": "Front View",
      "img_fn": "DSC_1234.jpg",
      "img_width": 1920,
      "img_height": 1080,
      "camera": "Nikon D750",
      "img_taken": "2024-01-15T12:00:00Z"
    }
  ]
}
```

```
POST /api/locations/{uuid}/import
```
Upload image to location.

**Request:** multipart/form-data with file

**Response:**
```json
{
  "status": "success",
  "img_uuid": "img123",
  "immich_asset_id": "immich_abc"
}
```

```
GET /api/images/{uuid}/file
```
Download image file.

### Map Data

```
GET /api/map/markers
```
Get all locations as GeoJSON for map display.

**Query parameters:**
- `limit` (default: 1000)

**Response:** GeoJSON FeatureCollection
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-73.456, 42.123]
      },
      "properties": {
        "loc_uuid": "abc123",
        "loc_name": "Abandoned Hospital",
        "type": "medical",
        "state": "NY"
      }
    }
  ]
}
```

### Search

```
GET /api/search
```
Search locations by various criteria.

**Query parameters:**
- `q` - Search query (searches name, aka_name)
- `state` - Filter by state code
- `type` - Filter by location type
- `city` - Filter by city

**Response:** Same as GET /api/locations

### Autocomplete

```
GET /api/locations/autocomplete/type
GET /api/locations/autocomplete/state
GET /api/locations/autocomplete/city
GET /api/locations/autocomplete/sub_type?type={type}
```

Get autocomplete suggestions for form fields.

**Response:**
```json
{
  "suggestions": ["industrial", "residential", "commercial"]
}
```

### Map Import (WARN: Not registered in app.py yet)

```
POST /api/maps/parse
```
Parse map file (CSV, GeoJSON, KML).

```
POST /api/maps/check-duplicates
```
Check for duplicate locations.

```
POST /api/maps/import
```
Import parsed locations to database.

### Bookmarks (WARN: Not registered in app.py yet)

```
GET /api/bookmarks
POST /api/bookmarks
GET /api/bookmarks/{id}
PUT /api/bookmarks/{id}
DELETE /api/bookmarks/{id}
GET /api/bookmarks/folders
```

### Mobile Sync

```
POST /api/sync/mobile
```
Push locations from mobile device.

```
GET /api/sync/mobile/pull
```
Pull new locations to mobile device.

---

## FILE DEPENDENCIES

### Import Chain

```
app.py
├── api_routes_v012
│   └── adapters.archivebox_adapter
└── api_sync_mobile

api_routes_v012
├── adapters.archivebox_adapter
└── (uses database directly)

db_import_v012
├── utils
├── normalize
└── immich_integration
    └── adapters.immich_adapter

Most imported modules:
1. normalize.py - imported by 13 files
2. utils.py - imported by 5 files
```

### Leaf Modules (no internal imports)
- scripts/utils.py
- scripts/normalize.py
- scripts/adapters/immich_adapter.py
- scripts/adapters/archivebox_adapter.py
- scripts/map_import.py

### Critical Dependencies
- All scripts depend on user/user.json for configuration
- Database migrations must run in sequence (v012 → v013 → v014)
- External services (Immich, ArchiveBox) are optional

### Known Issues
1. **api_routes_bookmarks.py:38** - Hardcoded database path 'data/aupat.db'
2. **immich_integration.py** - Uses relative import path for adapters
3. **api_routes_bookmarks.py** - Blueprint not registered in app.py
4. **api_maps.py** - Blueprint not registered in app.py

See docs/dependency_map.md for complete dependency analysis.

---

## CONFIGURATION

### Environment Variables

```bash
# Database
DB_PATH=/path/to/aupat.db        # Database location (default: data/aupat.db)

# API
FLASK_ENV=development             # Flask environment
PORT=5002                         # API port (default: 5002)

# Immich (optional)
IMMICH_URL=http://localhost:2283  # Immich API URL
IMMICH_API_KEY=your-api-key       # Immich API key

# ArchiveBox (optional)
ARCHIVEBOX_URL=http://localhost:8000     # ArchiveBox URL
ARCHIVEBOX_USERNAME=admin                # ArchiveBox username
ARCHIVEBOX_PASSWORD=your-password        # ArchiveBox password
```

### user.json Configuration

Located at: `user/user.json` (copy from user/user.json.template)

```json
{
  "db_path": "data/aupat.db",
  "db_backup": "data/backups/",
  "staging_path": "/path/to/staging/",
  "archive_path": "/path/to/archive/",
  "immich_url": "http://localhost:2283",
  "immich_api_key": "your-key",
  "archivebox_url": "http://localhost:8000"
}
```

**Required fields:**
- db_path
- db_backup

**Optional fields:**
- staging_path (for imports)
- archive_path (for organized storage)
- immich_url, immich_api_key (for photo management)
- archivebox_url (for web archiving)

---

## DEPLOYMENT MODES

### 1. Development Mode (Local)

Start full stack with hot reload:

```bash
./start_aupat.sh
```

**What runs:**
- Flask API on port 5002
- Electron desktop app with dev server on port 5173
- Hot reload enabled

**Use case:** Development and testing

---

### 2. API Server Only

Start API without desktop app:

```bash
./start_server.sh
```

**What runs:**
- Flask API on port 5000
- No desktop app

**Use case:** Headless deployments, mobile app development

---

### 3. Advanced API Server

Start with PID management and logging:

```bash
./scripts/advanced/start_api.sh

# Or with options
./scripts/advanced/start_api.sh --force    # Force restart
./scripts/advanced/start_api.sh --status   # Show status
```

**Features:**
- PID file tracking (api_server.pid)
- Health check verification
- Comprehensive logging (api_server.log)
- Idempotent (safe to run multiple times)

**Use case:** Production deployments, systemd integration

---

### 4. Docker Compose

Start full stack with all services:

```bash
./docker-start.sh
```

**Services started:**
- AUPAT Core (port 5001)
- Immich (port 2283)
- ArchiveBox (port 8001)
- PostgreSQL (internal)
- Redis (internal)

**Use case:** Complete deployment with external services

---

### 5. Background Workers

Start daemons for async processing:

```bash
# Web archiving
python scripts/archive_worker.py &

# Media extraction
python scripts/media_extractor.py &
```

**archive_worker:**
- Polls every 30 seconds for pending URLs
- Archives via ArchiveBox CLI
- Updates database with snapshot IDs

**media_extractor:**
- Polls every 30 seconds for archived URLs
- Extracts media from ArchiveBox snapshots
- Uploads to Immich (optional)
- Links to locations

**Use case:** Production deployments with web archiving

---

## EXTERNAL SERVICES

### Immich Photo Management

**Purpose:** Professional photo organization and management

**Integration points:**
- API health check endpoint
- Automatic upload during import
- GPS extraction from EXIF
- Thumbnail generation

**Configuration:**
```bash
IMMICH_URL=http://localhost:2283
IMMICH_API_KEY=your-api-key
```

**Graceful degradation:** App works without Immich (optional service)

**See:** scripts/adapters/immich_adapter.py, scripts/immich_integration.py

---

### ArchiveBox Web Archiving

**Purpose:** Preserve web pages related to locations

**Integration points:**
- API health check endpoint
- URL submission via API
- Background worker (archive_worker.py)
- Media extraction (media_extractor.py)

**Configuration:**
```bash
ARCHIVEBOX_URL=http://localhost:8000
ARCHIVEBOX_USERNAME=admin
ARCHIVEBOX_PASSWORD=password
```

**Graceful degradation:** App works without ArchiveBox (optional service)

**See:** scripts/adapters/archivebox_adapter.py, scripts/archive_worker.py

---

### External Tools

**exiftool** - EXIF metadata extraction
- Used by: db_organize.py
- Required for: GPS extraction, camera detection
- Install: `brew install exiftool` (macOS) or `apt-get install libimage-exiftool-perl` (Linux)

**ffmpeg** - Video metadata extraction
- Used by: db_organize.py
- Required for: Video duration, resolution
- Install: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux)

---

## DEVELOPMENT WORKFLOW

### Setting Up Development Environment

1. **Clone repository:**
   ```bash
   git clone https://github.com/bizzlechizzle/aupat.git
   cd aupat
   ```

2. **Run installation:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Start development server:**
   ```bash
   ./start_aupat.sh
   ```

### Making Changes

1. **Read the rules:** Check claude.md for development principles
2. **Check dependencies:** Review lilbits.md and techguide.md
3. **Make changes:** Follow LILBITS principle (small, focused functions)
4. **Write tests:** Maintain 70% coverage minimum
5. **Update docs:** Update lilbits.md, techguide.md if needed
6. **Commit:** Clear commit message following guidelines in claude.md

### Running Tests

```bash
# All tests
pytest -v

# With coverage
pytest --cov=scripts --cov-report=term-missing

# Specific test file
pytest tests/test_api_routes.py -v

# Specific test function
pytest tests/test_api_routes.py::test_health_check -v
```

### Import Workflow (Full Process)

Execute scripts in this order:

1. **Backup:**
   ```bash
   python scripts/backup.py
   ```

2. **Import:**
   ```bash
   python scripts/db_import_v012.py metadata.json
   ```

3. **Organize:**
   ```bash
   python scripts/db_organize.py
   ```

4. **Folder:**
   ```bash
   python scripts/db_folder.py
   ```

5. **Ingest:**
   ```bash
   python scripts/db_ingest.py
   ```

6. **Verify:**
   ```bash
   python scripts/db_verify.py
   ```

---

## KEY RULES AND PATTERNS

### Development Rules (from claude.md)

- **KISS:** Keep it simple, stupid
- **FAANG PE:** FAANG-level engineering for small team
- **BPL:** Bulletproof long-term (3-10+ years)
- **BPA:** Best practices always (check latest docs)
- **NME:** No emojis ever
- **WWYDD:** What would you do differently (suggest improvements)
- **DRETW:** Don't reinvent the wheel
- **LILBITS:** Write scripts in little bits (one function per file)

### API Endpoint Pattern

```python
@app.route('/api/resource', methods=['GET'])
def get_resource():
    """Get resource with validation and error handling."""
    try:
        # Validate input
        validate_request()

        # Get data
        data = fetch_data()

        # Transform
        result = transform_data(data)

        # Return
        return jsonify({'status': 'success', 'data': result}), 200

    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

    except Exception as e:
        logger.exception("Unexpected error")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
```

### Database Operation Pattern

```python
def db_operation(param: str) -> Optional[dict]:
    """Database operation with connection management."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM table WHERE field = ?",
            (param,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()
```

### File Operation Pattern

```python
def file_operation(path: str) -> str:
    """File operation with validation and error handling."""
    # Validate
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    if not os.access(path, os.R_OK):
        raise PermissionError(f"Cannot read file: {path}")

    # Read
    try:
        with open(path, 'r') as f:
            return f.read()
    except IOError as e:
        logger.error(f"Failed to read {path}: {e}")
        raise
```

---

## TROUBLESHOOTING

### Port Already in Use

**Symptom:** "Address already in use" error when starting server

**Solution:**
```bash
# Find process using port 5002
lsof -i :5002

# Kill process
kill -9 <PID>

# Or use pkill
pkill -f "python.*app.py"
```

---

### Database Locked

**Symptom:** "database is locked" error

**Cause:** Another process accessing database

**Solution:**
```bash
# Check for open connections
fuser data/aupat.db

# Wait for operations to complete or restart app
```

---

### Import Errors

**Symptom:** ModuleNotFoundError

**Solution:**
```bash
# Ensure virtual environment activated
source venv/bin/activate

# Verify Python path includes project root
export PYTHONPATH=/home/user/aupat:$PYTHONPATH

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Blueprint Not Found (404 errors)

**Symptom:** 404 errors for /api/bookmarks or /api/maps endpoints

**Cause:** Blueprints not registered in app.py

**Solution:** See todo.md task #2 - Fix Blueprint Registration

---

### exiftool or ffmpeg Not Found

**Symptom:** "exiftool not found" error in db_organize.py

**Solution:**
```bash
# macOS
brew install exiftool ffmpeg

# Linux
sudo apt-get install libimage-exiftool-perl ffmpeg
```

---

## REFERENCES

### Key Documentation Files

- **claude.md** - Development rules and core process (10-step workflow)
- **lilbits.md** - Complete script documentation with examples
- **todo.md** - Task tracking and project gaps
- **README.md** - Project overview and quick start
- **docs/dependency_map.md** - Complete file dependency analysis
- **CODEBASE_AUDIT_COMPLETE.md** - Comprehensive codebase audit

### External Documentation

- Flask: https://flask.palletsprojects.com/
- SQLite: https://www.sqlite.org/docs.html
- Electron: https://www.electronjs.org/docs
- Svelte: https://svelte.dev/docs
- Immich: https://immich.app/docs
- ArchiveBox: https://docs.archivebox.io/

---

## VERSION HISTORY

- 1.0.0 (2025-11-18): Initial comprehensive technical guide

---

**End of Technical Guide**

For specific script documentation, see lilbits.md
For development workflow, see claude.md
For current tasks, see todo.md
