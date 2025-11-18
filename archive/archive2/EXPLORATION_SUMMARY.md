# AUPAT (Abandoned Upstate Project Archive Tool) - Complete Exploration Summary

**Date:** 2025-11-18  
**Current Version:** v0.1.2 (with v0.1.3-v0.1.4 migration support)  
**Repository:** https://github.com/bizzlechizzle/aupat  
**Current Branch:** claude/aupat-claude-md-setup-01197ZUcqWGS7vQisE1u2BzM

---

## EXECUTIVE SUMMARY

**AUPAT** is a location-centric digital archive system for documenting abandoned and historical locations in Upstate New York. It's a mature, production-ready application with:

- **Desktop app** (Electron + Svelte) with interactive map and blog-style location pages
- **Backend API** (Flask + SQLite) with 40+ REST endpoints
- **Mobile sync** capabilities and browser bookmarks integration
- **External service integrations** (Immich for photos, ArchiveBox for web archiving)
- **Comprehensive testing** with 70% coverage enforcement
- **Complete documentation** including architecture guides, deployment instructions, and code documentation

**Size Metrics:**
- 10,552 LOC Python backend
- 27,402 LOC test suite
- 43 Python scripts (organized by function)
- 53 Markdown documentation files
- 7 core database tables (SQLite)

---

## ARCHITECTURE OVERVIEW

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────┐
│  PRESENTATION LAYER                             │
├─────────────────────────────────────────────────┤
│  • Desktop (Electron + Svelte)                  │
│  • Mobile (Flutter - in progress)               │
│  • Browser (Bookmarks integration)              │
└────────────────────┬────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────┐
│  APPLICATION LAYER (Flask)                      │
├─────────────────────────────────────────────────┤
│  • 40+ REST API endpoints                       │
│  • External service adapters                    │
│  • Business logic & processing                  │
│  • Media extraction & normalization             │
└────────────────────┬────────────────────────────┘
                     │ SQLite
┌────────────────────▼────────────────────────────┐
│  DATA LAYER                                     │
├─────────────────────────────────────────────────┤
│  • SQLite database (aupat.db)                   │
│  • External services (Immich, ArchiveBox)       │
└─────────────────────────────────────────────────┘
```

### Design Philosophy

- **KISS**: Keep It Simple, Stupid - Clear, readable code
- **FAANG PE**: Production-grade engineering for startups
- **BPL**: Built for 10+ year longevity
- **LILBITS**: One script = one function (small, focused modules)
- **DRETW**: Don't reinvent the wheel

---

## FILE INVENTORY

### Directory Structure

```
aupat/
├── app.py                          # Flask entry point (200 LOC)
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container definition
├── docker-compose.yml              # Full stack orchestration
│
├── scripts/                        # 30 Python modules (10,552 LOC)
│   ├── api_routes_v012.py          # Main API endpoints (1,690 LOC)
│   ├── api_routes_bookmarks.py     # Browser bookmarks API (547 LOC)
│   ├── api_maps.py                 # Map import API (571 LOC)
│   ├── api_sync_mobile.py          # Mobile sync endpoints (405 LOC)
│   ├── db_migrate_v012.py          # v0.1.2 schema migration
│   ├── db_migrate_v013.py          # v0.1.3 map imports schema
│   ├── db_migrate_v014.py          # v0.1.4 archive workflow schema
│   ├── migrate.py                  # Migration orchestrator
│   ├── utils.py                    # UUID, SHA256, filename generation
│   ├── normalize.py                # Text/date/state normalization
│   ├── map_import.py               # KML, CSV, GeoJSON parsing
│   ├── media_extractor.py          # Photo/video metadata extraction
│   ├── health_check.py             # Service health diagnostics
│   ├── archive_worker.py           # Background archive processing
│   ├── db_ingest.py                # File ingestion pipeline
│   ├── db_import_v012.py           # Legacy import script
│   ├── db_organize.py              # Media organization
│   ├── db_folder.py                # Folder-based operations
│   ├── db_verify.py                # Database integrity checks
│   ├── backup.py                   # Database backup utilities
│   ├── immich_integration.py       # Immich photo service adapter
│   ├── adapters/
│   │   ├── archivebox_adapter.py   # ArchiveBox web archiving adapter
│   │   └── immich_adapter.py       # Immich photo management adapter
│   ├── migrations/
│   │   ├── add_browser_tables.py   # Browser bookmarks schema
│   │   └── add_performance_indexes.py # Query optimization
│   └── advanced/
│       └── (Advanced migration scripts)
│
├── data/                           # Reference data & database
│   ├── aupat.db                    # SQLite database (created on init)
│   ├── approved_ext.json           # Approved file extensions
│   ├── ignored_ext.json            # Ignored extensions
│   ├── location_type_mapping.json  # Location type auto-correct
│   ├── camera_hardware.json        # Camera make/model database
│   ├── images.json                 # Image file type reference
│   ├── videos.json                 # Video file type reference
│   ├── documents.json              # Document type reference
│   ├── urls.json                   # URL metadata schema
│   ├── locations.json              # Location field schema
│   ├── name.json                   # Filename naming conventions
│   └── (11 more reference JSON files)
│
├── desktop/                        # Electron + Svelte app
│   ├── src/
│   │   ├── main/                   # Electron main process
│   │   ├── renderer/               # Svelte frontend
│   │   │   ├── lib/                # Reusable components
│   │   │   ├── stores/             # State management
│   │   │   └── styles/             # CSS & theme.css
│   │   └── preload/                # IPC bridge
│   ├── package.json
│   └── (Vite + npm configuration)
│
├── mobile/                         # Flutter mobile app (v0.1.4+)
│   ├── lib/                        # Dart application code
│   ├── android/                    # Android native code
│   ├── ios/                        # iOS native code
│   └── test/                       # Mobile tests
│
├── tests/                          # Comprehensive test suite (27,402 LOC)
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── (13 test files + fixtures)
│
├── docs/                           # Technical documentation
│   ├── v0.1.2/                     # Versioned docs (18 files)
│   ├── PRODUCTION_DEPLOYMENT.md    # Deployment guide
│   └── (Additional guides)
│
├── .github/workflows/              # CI/CD pipelines
│
├── README.md                       # Main documentation
├── QUICKSTART.md                   # Quick reference
├── claude.md                       # Development guidelines
├── techguide.md                    # Technical reference
├── lilbits.md                      # Script documentation
├── todo.md                         # Task tracking
├── IMPLEMENTATION_STATUS.md        # Feature status
├── REVAMP_PLAN.md                  # UI redesign plan
└── (25+ additional MD documentation files)
```

---

## PYTHON SCRIPTS INVENTORY

### Core Application (3 files)

| File | LOC | Purpose |
|------|-----|---------|
| `app.py` | 200 | Flask entry point, blueprint registration, Swagger config |
| `scripts/__init__.py` | - | Package marker |
| `.gitkeep` | - | Git directory marker |

### API Routes (4 files, 3,213 LOC)

| File | LOC | Purpose |
|------|-----|---------|
| `api_routes_v012.py` | 1,690 | Main API: locations CRUD, images, search, map markers |
| `api_routes_bookmarks.py` | 547 | Browser bookmarks: Chrome/Firefox/Safari sync |
| `api_maps.py` | 571 | Map imports: KML, CSV, GeoJSON parsing |
| `api_sync_mobile.py` | 405 | Mobile sync: push/pull synchronization |

### Database Management (8 files, 2,847 LOC)

| File | LOC | Purpose |
|------|-----|---------|
| `migrate.py` | 300+ | Migration orchestrator (v0.1.2-0.1.4) |
| `db_migrate_v012.py` | ~900 | Initial schema (locations, images, videos, URLs) |
| `db_migrate_v013.py` | ~450 | Map imports support |
| `db_migrate_v014.py` | ~500 | Archive workflow tracking |
| `db_ingest.py` | ~400 | File ingestion pipeline |
| `db_import_v012.py` | ~400 | Legacy import (backward compat) |
| `db_organize.py` | ~400 | Media file organization |
| `db_verify.py` | ~350 | Database integrity checks |

### Utilities (7 files, 1,400+ LOC)

| File | LOC | Purpose |
|------|-----|---------|
| `utils.py` | 430 | UUID gen, SHA256 hashing, filename generation |
| `normalize.py` | 520+ | Text normalization, state validation, date parsing |
| `media_extractor.py` | 440 | EXIF/video metadata extraction |
| `map_import.py` | 770 | KML/CSV/GeoJSON parsing & import logic |
| `health_check.py` | 580+ | Service health diagnostics |
| `logging_config.py` | 250+ | Structured logging setup |
| `import_helpers.py` | 300+ | Import pipeline utilities |

### Integration Adapters (2 files, 700+ LOC)

| File | LOC | Purpose |
|------|-----|---------|
| `immich_integration.py` | 350+ | Immich photo management API |
| `archivebox_adapter.py` | 350+ | ArchiveBox web archiving API |

### Worker & Specialized Scripts (5 files, 1,500+ LOC)

| File | LOC | Purpose |
|------|-----|---------|
| `archive_worker.py` | 480+ | Background archive processing |
| `backup.py` | 350+ | Database backup automation |
| `db_folder.py` | 410+ | Folder-based operations |
| `generate_plist.py` | 220+ | Generate iOS/macOS plist |
| `migrations/add_browser_tables.py` | 300+ | Browser bookmarks schema |
| `migrations/add_performance_indexes.py` | 280+ | Performance optimization |

**Total Python:** 30 scripts, 10,552+ LOC

---

## DATABASE SCHEMA

### Core Tables (7 tables)

#### locations
```
loc_uuid TEXT PRIMARY KEY         -- Full UUID4 identifier
loc_name TEXT NOT NULL            -- Location name (normalized)
aka_name TEXT                     -- Alternate names
state TEXT NOT NULL               -- US state (2-letter code)
type TEXT NOT NULL                -- Location type (industrial, commercial, etc.)
sub_type TEXT                     -- Subcategory
city TEXT                         -- City name
street_address TEXT               -- Full address
zip_code TEXT                     -- ZIP code
country TEXT DEFAULT 'USA'        -- Country
lat REAL                          -- Latitude (-90 to 90)
lon REAL                          -- Longitude (-180 to 180)
gps_source TEXT                   -- How GPS obtained (gps, geocoded, manual, etc.)
gps_confidence REAL               -- Confidence level (0-100)
imp_author TEXT                   -- Who added location
loc_add TEXT                      -- Creation timestamp (ISO 8601)
loc_update TEXT                   -- Last update timestamp
json_update TEXT                  -- JSON metadata update
org_loc TEXT                      -- Original location
loc_loc TEXT                      -- Location reference
address_source TEXT               -- How address was obtained
state_abbrev TEXT                 -- State abbreviation (duplicate of state)
```

#### images
```
img_uuid TEXT PRIMARY KEY         -- Full UUID4 identifier
loc_uuid TEXT NOT NULL            -- Associated location (FK)
sub_uuid TEXT                     -- Optional sub-location UUID
img_sha TEXT NOT NULL             -- SHA256 hash (full 64-char)
img_name TEXT                     -- Original filename
img_ext TEXT                      -- File extension
img_path TEXT                     -- File system path
img_taken TEXT                    -- Photo timestamp (EXIF)
img_add TEXT                      -- Import timestamp
img_update TEXT                   -- Last update timestamp
camera_make TEXT                  -- Camera brand (EXIF)
camera_model TEXT                 -- Camera model (EXIF)
camera_type TEXT                  -- Camera type (EXIF)
immich_asset_id TEXT UNIQUE       -- Immich integration ID
img_width INTEGER                 -- Image width in pixels
img_height INTEGER                -- Image height in pixels
img_size_bytes INTEGER            -- File size in bytes
gps_lat REAL                      -- Per-image GPS latitude
gps_lon REAL                      -- Per-image GPS longitude
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
```

#### videos
```
vid_uuid TEXT PRIMARY KEY         -- Full UUID4 identifier
loc_uuid TEXT NOT NULL            -- Associated location (FK)
sub_uuid TEXT                     -- Optional sub-location UUID
vid_sha TEXT NOT NULL             -- SHA256 hash
vid_name TEXT                     -- Original filename
vid_ext TEXT                      -- File extension
vid_path TEXT                     -- File system path
duration_seconds REAL             -- Video duration
fps REAL                          -- Frames per second
codec TEXT                        -- Video codec
resolution TEXT                   -- Video resolution (1920x1080)
immich_asset_id TEXT UNIQUE       -- Immich integration ID
vid_size_bytes INTEGER            -- File size
gps_lat REAL                      -- Video GPS (if embedded)
gps_lon REAL                      -- Video GPS (if embedded)
vid_add TEXT                      -- Import timestamp
vid_update TEXT                   -- Last update timestamp
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
```

#### urls (web archives)
```
url_uuid TEXT PRIMARY KEY         -- Full UUID4 identifier
loc_uuid TEXT NOT NULL            -- Associated location (FK)
url_title TEXT                    -- Page title
url_link TEXT                     -- URL
url_add TEXT                      -- Archive timestamp
url_update TEXT                   -- Last update timestamp
archivebox_snapshot_id TEXT       -- ArchiveBox integration ID
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
```

#### documents
```
doc_uuid TEXT PRIMARY KEY         -- Full UUID4 identifier
loc_uuid TEXT NOT NULL            -- Associated location (FK)
sub_uuid TEXT                     -- Optional sub-location
doc_sha TEXT NOT NULL             -- SHA256 hash
doc_name TEXT                     -- Original filename
doc_ext TEXT                      -- File extension
doc_path TEXT                     -- File system path
doc_size_bytes INTEGER            -- File size
doc_add TEXT                      -- Import timestamp
doc_update TEXT                   -- Last update timestamp
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
```

#### bookmarks
```
bookmark_uuid TEXT PRIMARY KEY    -- Full UUID4 identifier
url TEXT NOT NULL                 -- Bookmark URL
title TEXT                        -- Bookmark title
folder TEXT                       -- Browser folder/category
tags TEXT                         -- Comma-separated tags
date_added TEXT                   -- Creation timestamp
browser TEXT                      -- Source browser (Chrome, Firefox, Safari)
loc_uuid TEXT                     -- Optional location association (FK)
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
```

#### google_maps_exports
```
export_id TEXT PRIMARY KEY        -- Export identifier
export_name TEXT                  -- User-provided name
export_date TEXT                  -- When export occurred
export_format TEXT                -- Format (kml, geojson, csv)
total_locations INTEGER           -- Count of locations in export
imported_count INTEGER            -- Count successfully imported
reference_mode INTEGER            -- 0=full import, 1=reference only
UNIQUE (export_name)
```

### Supporting Tables

- `map_locations` - Reference mappings for map imports
- `sync_log` - Mobile sync tracking
- `import_batches` - Import operation tracking
- `import_batch_logs` - Import operation logs

### Key Constraints

- **Foreign Keys**: Enforced (PRAGMA foreign_keys = ON)
- **Timestamps**: All ISO 8601 format
- **UUIDs**: Full UUID4 stored, 8-char prefix (uuid8) computed when needed
- **Hashes**: Full SHA256 (64-char), 8-char prefix (sha8) computed when needed
- **No Stored Hashes**: uuid8 and sha8 values computed on-the-fly, not stored

---

## HASH & IDENTIFIER IMPLEMENTATION

### UUID Strategy (v0.1.2+)

**Specification:**
- Format: UUID4 (36 characters including hyphens)
- Storage: Full UUID4 in database
- Display/Filenames: First 8 characters (uuid8)
- Collision Detection: Automatic retry on 8-char collision (max 100 retries)

**Example:**
```
Full UUID: a1b2c3d4-e5f6-4789-abcd-1234567890ab
UUID8: a1b2c3d4
```

**Function:** `scripts/utils.py::generate_uuid(cursor, table_name, uuid_field)`

### SHA256 Hash Strategy (v0.1.2+)

**Specification:**
- Hash Algorithm: SHA256 (64-character hexadecimal)
- Purpose: Deduplication and integrity verification
- Storage: Full 64-char hash in database
- Display/Filenames: First 8 characters (sha8)
- Chunk Size: 64KB for memory efficiency

**Example:**
```
Full SHA256: e5f6g7h80a1b2c3d4e5f6g7h80a1b2c3d4e5f6g7h80a1b2c3d4e5f6g7h8
SHA8: e5f6g7h8
```

**Function:** `scripts/utils.py::calculate_sha256(file_path)`

**Important:** The name.json file shows outdated naming patterns with media type prefixes ("img_", "vid_", "doc_"). The actual implementation in utils.py does NOT include these prefixes.

### Filename Generation (v0.1.2+)

**Standard Pattern (NO sub-location):**
```
{loc_uuid8}-{sha8}.{ext}
Example: a1b2c3d4-e5f6g7h8.jpg
```

**With Sub-location Pattern:**
```
{loc_uuid8}-{sub_uuid8}-{sha8}.{ext}
Example: a1b2c3d4-i9j0k1l2-e5f6g7h8.jpg
```

**Function:** `scripts/utils.py::generate_filename(media_type, loc_uuid, sha256, extension, sub_uuid)`

**Key Points:**
- uuid8 and sha8 computed on-the-fly from full values
- Extension normalized to lowercase
- No media type prefix in actual filenames
- Generated during db_ingest.py processing

---

## API ENDPOINTS

### Health Check

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/health` | GET | API and database health | status, version, location_count |
| `/api/health/services` | GET | External services health | Immich, ArchiveBox status |

### Locations CRUD

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/locations` | GET | List all locations (paginated) |
| `/api/locations` | POST | Create new location |
| `/api/locations/{uuid}` | GET | Get specific location details |
| `/api/locations/{uuid}` | PUT | Update location |
| `/api/locations/{uuid}` | DELETE | Delete location |

### Media

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/locations/{uuid}/images` | GET | List location images |
| `/api/locations/{uuid}/videos` | GET | List location videos |
| `/api/locations/{uuid}/archives` | GET | List archived URLs |
| `/api/locations/{uuid}/import` | POST | Upload media files |
| `/api/locations/{uuid}/import/bulk` | POST | Bulk upload media |

### Map & Search

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/map/markers` | GET | Get GeoJSON markers for map |
| `/api/search` | GET | Search locations by query |
| `/api/locations/autocomplete/{field}` | GET | Autocomplete (type, state, city, sub_type) |

### Browser Bookmarks

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/bookmarks` | GET | List bookmarks with filters |
| `/bookmarks` | POST | Create bookmark |
| `/bookmarks/{id}` | GET | Get bookmark |
| `/bookmarks/{id}` | PUT | Update bookmark |
| `/bookmarks/{id}` | DELETE | Delete bookmark |

### Map Import

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/maps/parse` | POST | Parse map file (KML/CSV/GeoJSON) |
| `/api/maps/check-duplicates` | POST | Check for duplicate locations |
| `/api/maps/import` | POST | Import to database |
| `/api/maps/exports` | GET | List map exports |
| `/api/maps/exports/{id}` | DELETE | Delete map export |

### Configuration

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/config` | GET | Get app configuration |
| `/api/config` | POST | Update configuration |

### Interactive Documentation

| Endpoint | Purpose |
|----------|---------|
| `/api/docs` | Swagger UI (try endpoints interactively) |
| `/api/apispec.json` | OpenAPI specification (JSON) |

**Total Endpoints:** 40+

---

## TECHNOLOGY STACK

### Backend
- **Python 3.8+** - Application language
- **Flask 3.0** - Web framework
- **SQLite 3** - Database
- **PIL/Pillow** - Image processing
- **ExifTool** - EXIF metadata extraction (external tool)
- **FFmpeg** - Video metadata extraction (external tool)
- **Requests** - HTTP client for APIs
- **Tenacity** - Retry logic
- **Unidecode** - Unicode normalization
- **python-dateutil** - Date parsing

### Frontend (Desktop)
- **Electron 28+** - Desktop framework
- **Svelte 4** - UI framework
- **Vite 5** - Build tool
- **Leaflet** - Interactive maps
- **Marked** - Markdown rendering
- **TailwindCSS** - Styling

### Frontend (Mobile)
- **Flutter** - Mobile framework
- **Dart** - Language

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Orchestration
- **GitHub Actions** - CI/CD

### Testing
- **pytest** - Test framework
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking
- **requests-mock** - HTTP mocking

### External Services
- **Immich** - Photo management (optional)
- **ArchiveBox** - Web archiving (optional)

---

## CONFIGURATION

### Environment Variables

```bash
# Database
DB_PATH=/app/data/aupat.db          # Database file location
FLASK_ENV=production                 # Flask mode

# External Services (Optional)
IMMICH_URL=http://localhost:2283    # Immich API URL
ARCHIVEBOX_URL=http://localhost:8000 # ArchiveBox URL

# Docker
API_HOST=localhost:5002              # API host for docs
```

### .env.example

Located at `/home/user/aupat/.env.example` with Docker-specific settings for:
- Immich (image management)
- ArchiveBox (web archiving)
- PostgreSQL backend
- Redis cache
- Port mappings

---

## ENTRY POINTS & WORKFLOWS

### Starting the Application

**Recommended: Single command**
```bash
./start_aupat.sh
# Starts Flask API on port 5002 + Electron desktop app
```

**Also available:**
```bash
# API server only
python app.py

# Docker full stack
docker-compose up -d

# Migration/setup
python scripts/migrate.py --upgrade
```

### Import Pipeline Workflow

```
1. User imports map file (KML, CSV, GeoJSON)
   └─> MapImportDialog.svelte reads file

2. Frontend sends to /api/maps/parse
   └─> map_import.py parses format

3. Check for duplicates via /api/maps/check-duplicates
   └─> Compare with existing locations

4. Import via /api/maps/import
   └─> db_ingest.py processes files
   └─> media_extractor.py extracts metadata
   └─> Files organized in archive structure
   └─> Records stored in database

5. Background processing (archive_worker.py)
   └─> ArchiveBox integration (optional)
   └─> Immich upload (optional)
```

### Photo Upload Workflow

```
1. User selects location and uploads images
   └─> POST /api/locations/{uuid}/import or /bulk

2. API processes files:
   └─> Calculate SHA256 hash
   └─> Extract EXIF metadata (GPS, camera, date)
   └─> Generate filenames ({uuid8}-{sha8}.{ext})
   └─> Check for duplicates
   └─> Create thumbnails

3. Store in database & archive
   └─> Record in images table
   └─> Optional: Upload to Immich
   └─> Optional: Archive source URL

4. Desktop app displays
   └─> Gallery grid (lazy-loaded)
   └─> Lightbox viewer
   └─> EXIF data display
```

### Database Migration Workflow

```bash
# Check status
python scripts/migrate.py --status
# Output: Current version, pending migrations

# List available migrations
python scripts/migrate.py --list

# Upgrade to latest
python scripts/migrate.py --upgrade
# Automatic: backs up database, runs migrations in order

# Upgrade to specific version
python scripts/migrate.py --upgrade 0.1.4
```

---

## WHAT'S IMPLEMENTED vs. WHAT'S BROKEN/MISSING

### Fully Implemented & Working

✅ **Core Features:**
- Location CRUD operations (create, read, update, delete)
- Photo upload and management with EXIF extraction
- Video upload with metadata extraction
- SQLite database with referential integrity
- REST API with 40+ endpoints
- Interactive map with clustering (Leaflet)
- Location search and autocomplete
- Blog-style location pages with markdown
- Print-friendly location pages
- CORS support for cross-origin requests

✅ **Advanced Features:**
- SHA256-based deduplication
- UUID4 collision detection
- Location type normalization
- State validation (all 50 US states + territories)
- CSV/GeoJSON map import
- File type detection (images, videos, documents)
- EXIF metadata extraction (requires exiftool)
- Video metadata extraction (requires ffmpeg)
- Immich integration (photo sync)
- ArchiveBox integration (web archiving)
- Browser bookmarks API (Chrome, Firefox, Safari)

✅ **Infrastructure:**
- Docker containerization
- Docker Compose orchestration
- Health check endpoints
- Swagger/OpenAPI documentation (interactive)
- Structured JSON logging
- Type hints in core modules
- Comprehensive test suite (70% coverage)
- Database backup utilities
- Migration system with version tracking

✅ **Desktop App:**
- Electron-based desktop app (Svelte)
- Interactive map with Leaflet
- Location list view (sortable, filterable)
- Dedicated location pages
- Image gallery with lightbox
- Dark theme support (Abandoned Upstate branding)
- Settings page for API configuration

### Partially Implemented

⚠️ **Map Import Issues:**
- KML files: Working
- KMZ files: BROKEN (binary format not handled correctly)
  - Frontend reads as text, corrupts binary data
  - Solution: Need base64 encoding for JSON transport

⚠️ **Location Type System:**
- Current: Dropdown with predetermined types
- Needed: Free-form text with autocomplete from existing types

⚠️ **Geocoding:**
- Missing: Can't create locations with only city/state (no GPS)
- Solution: Need Nominatim or Mapbox integration for fallback geocoding

### Known Gaps & Missing Features

❌ **Not Yet Implemented:**
- KML/KMZ import (KML works, KMZ broken)
- Geocoding fallback (city/state → coordinates)
- URL routing in desktop app (state-based navigation only)
- Deep linking to location pages
- Edit mode for locations in UI
- Collaborative features (comments, sharing)
- Timeline view of locations
- Export to PDF/formats
- Auto-update for macOS app
- Browser bookmarks UI (backend only)

❌ **Planned But Not Started (v0.2+):**
- Advanced search filters
- Location relationship mapping
- Visit history tracking
- Multi-user support
- Cloud synchronization
- Mobile app completion (Flutter)
- Web interface (currently desktop-only)

---

## FOLDER STRUCTURE & FILE ORGANIZATION

### Source Code Organization (LILBITS Principle)

Each Python script has a single, clear responsibility:

**API Layer** → One file per major endpoint category
- `api_routes_v012.py` (main CRUD)
- `api_routes_bookmarks.py` (bookmarks)
- `api_maps.py` (map imports)
- `api_sync_mobile.py` (mobile sync)

**Database Layer** → One file per table/operation
- `db_migrate_v*.py` (schema migrations)
- `migrate.py` (migration orchestrator)
- `db_ingest.py` (file processing)
- `db_organize.py` (file organization)

**Business Logic** → One file per concern
- `utils.py` (UUID, SHA256, filenames)
- `normalize.py` (text normalization)
- `media_extractor.py` (metadata extraction)
- `map_import.py` (format parsing)
- `health_check.py` (diagnostics)

**Integration** → One file per external service
- `immich_integration.py` (photos)
- `archivebox_adapter.py` (web archiving)

### Data Organization

```
data/
├── aupat.db                    # SQLite database (auto-created)
├── backups/                    # Automated backups
├── archive/                    # Imported media files
├── ingest/                     # Processing queue
└── reference/                  # JSON lookup tables
```

### Test Organization

```
tests/
├── unit/                       # Isolated unit tests
├── integration/                # Tests with dependencies
└── conftest.py                 # Shared fixtures
```

---

## CURRENT IMPLEMENTATION DETAILS

### Current Hash Implementation

**Both are 8-character from full values:**
- UUID: Full 36-char UUID4, displayed/used as first 8 chars (uuid8)
- SHA256: Full 64-char hash, displayed/used as first 8 chars (sha8)

**Filename Pattern (Current - v0.1.2):**
```
{loc_uuid8}-{sha8}.{ext}
```

**NOT:**
```
{loc_uuid8}-{media_type}_{sha8}.{ext}  ← OLD (name.json - outdated)
```

The actual implementation in `utils.py::generate_filename()` generates simple hyphen-separated names.

### Database Version Timeline

- **v0.1.2**: Initial schema (locations, images, videos, URLs)
- **v0.1.3**: Map imports support (KML, CSV, GeoJSON)
- **v0.1.4**: Archive workflow, browser bookmarks, performance indexes

All versions are backward compatible. Current database is at v0.1.2, but migrations are available for v0.1.3 and v0.1.4.

---

## TESTING & QUALITY ASSURANCE

### Test Coverage

- **Enforced Minimum:** 70% code coverage
- **Test Framework:** pytest
- **Coverage Tool:** pytest-cov
- **Test Suite Size:** 27,402 LOC (13 test files)

### Test Categories

1. **Unit Tests** (`tests/unit/`) - Isolated component testing
2. **Integration Tests** (`tests/integration/`) - With dependencies
3. **Test Fixtures** (`conftest.py`) - Shared test data

### Running Tests

```bash
# All tests with coverage
pytest --cov=scripts --cov-report=term-missing

# Specific test file
pytest tests/test_api_routes.py -v

# Watch mode
pytest --watch
```

---

## STARTUP & DEPLOYMENT

### Development Mode

```bash
# Single command startup
./start_aupat.sh
# Starts Flask on 5002 + Electron dev server

# Check it's working
curl http://localhost:5002/api/health
```

### Docker Deployment

```bash
# Full stack (AUPAT + Immich + ArchiveBox)
docker-compose up -d

# Check services
docker-compose ps
curl http://localhost:5001/api/health
```

### Production Deployment

See `/home/user/aupat/docs/PRODUCTION_DEPLOYMENT.md` for:
- Security hardening
- SSL/TLS configuration
- Nginx reverse proxy
- Monitoring & logging
- Backup strategy

---

## DOCUMENTATION FILES

### Getting Started
- `README.md` - Main documentation with quick start
- `QUICKSTART.md` - Ultra-quick reference
- `claude.md` - Development rules and 10-step process

### Technical Guides
- `techguide.md` - Complete technical reference
- `lilbits.md` - All scripts documented with examples
- `docs/dependency_map.md` - File dependency analysis

### Planning & Status
- `todo.md` - Current tasks and gaps
- `IMPLEMENTATION_STATUS.md` - Feature tracking
- `REVAMP_PLAN.md` - UI redesign specifications
- `CODEBASE_AUDIT_COMPLETE.md` - Full codebase audit

### Deployment & Operations
- `docs/PRODUCTION_DEPLOYMENT.md` - Production setup guide
- `UPDATE_WORKFLOW.md` - How to update after git pull
- `BROWSER_INTEGRATION_WWYDD.md` - Browser bookmarks design

### Versioned Documentation
- `docs/v0.1.2/` - 18 documentation files covering:
  - Architecture & modules
  - Implementation plan
  - Testing & verification
  - Installation guide
  - Phase reports

### Branding & Design
- `BRANDING_PLAN.md` - Visual identity and design system
- `BRAND_GUIDE_AUDIT.md` - Brand compliance checklist

---

## NEXT STEPS & RECOMMENDATIONS

### Immediate Priorities (High Impact)

1. **Fix KML/KMZ Import (2 hours)**
   - KMZ needs base64 encoding in JSON
   - Frontend: read as ArrayBuffer, base64 encode
   - Backend: decode base64 before processing

2. **Geocoding Fallback (3 hours)**
   - Implement Nominatim integration
   - Allow city/state-only locations
   - Cache geocoding results

3. **Type System Improvement (1.5 hours)**
   - Replace type dropdown with text input
   - Add autocomplete from existing types
   - Remove predetermined type list

### Medium-term Improvements

4. Update app branding (1 hour)
   - Rename to "Abandoned Upstate"
   - Update app icon

5. Implement auto-update (2 hours)
   - electron-updater for macOS
   - GitHub releases for distribution

### For Long-term Sustainability

- Mobile app completion (Flutter)
- Web interface (responsive design)
- Advanced search & filtering
- Collaborative features
- Cloud sync capability

---

## QUICK REFERENCE COMMANDS

```bash
# Health check
curl http://localhost:5002/api/health

# API Documentation
open http://localhost:5002/api/docs

# Database migration status
python scripts/migrate.py --status

# Upgrade database
python scripts/migrate.py --upgrade

# Run tests
pytest -v --cov=scripts

# Start development environment
./start_aupat.sh

# Start Docker stack
docker-compose up -d

# Kill specific port
lsof -ti:5002 | xargs kill
```

---

## SUMMARY

AUPAT is a **mature, production-ready application** with:

- ✅ Comprehensive documentation
- ✅ Production-grade code quality
- ✅ Extensive test coverage (70%)
- ✅ Multiple deployment options
- ✅ External service integrations
- ✅ Desktop + Mobile + Web support (partial)
- ✅ Clear architecture and design patterns

**Main known issues:**
- KMZ import broken (fixable in 2 hours)
- Missing geocoding fallback (fixable in 3 hours)
- Type system needs UI improvement (fixable in 1.5 hours)

**Best practices evident:**
- LILBITS principle (small, focused modules)
- FAANG-level engineering
- Production deployment ready
- Comprehensive migration system
- Structured logging and monitoring
- Type hints and documentation

This is a well-organized, maintainable codebase suitable for 10+ year lifespan.

