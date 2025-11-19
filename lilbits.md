# LILBITS - AUPAT Script Documentation

Version: 3.0.0 (v0.1.0 Features Complete)
Last Updated: 2025-11-19

This document catalogs all scripts in the AUPAT project, following the LILBITS principle: one script = one function. Each script is documented with its purpose, inputs, outputs, and dependencies.

---

## CRITICAL: 12-CHARACTER HASH STANDARD (2025-11-18)

**ALL new scripts must use 12-char hashes:**
- `uuid12 = uuid_full[:12]`
- `sha12 = sha256_full[:12]`
- Filenames: `{uuid12}-{sha12}.{ext}`

See claude.md for full rationale.

---

## TABLE OF CONTENTS

1. [Main Application](#main-application)
2. [API Routes](#api-routes)
3. [Database Migrations](#database-migrations)
4. [Database Operations](#database-operations)
5. [Worker Daemons](#worker-daemons)
6. [Utility Modules](#utility-modules)
7. [External Adapters](#external-adapters)
8. [Advanced Migrations](#advanced-migrations)
9. [Startup Scripts](#startup-scripts)
10. [Testing Scripts](#testing-scripts)

---

## MAIN APPLICATION

### app.py

**Location:** `/home/user/aupat/app.py`
**LOC:** 200 lines
**Purpose:** Flask application entry point and configuration

**What it does:**
- Initializes Flask application
- Configures database path from environment
- Registers API route blueprints
- Sets up Swagger/OpenAPI documentation (v0.1.6)
- Sets up health check endpoints
- Configures CORS for cross-origin requests
- Checks external tool availability on startup

**Key functions:**
- Application initialization
- Blueprint registration
- Swagger UI configuration
- Root endpoint with API info
- External tool availability checks (exiftool, ffmpeg)

**Dependencies:**
- Flask
- flasgger (OpenAPI/Swagger documentation)
- scripts.api_routes_v012
- scripts.api_sync_mobile
- scripts.api_routes_bookmarks
- scripts.api_maps

**Database tables:** None directly (delegates to blueprints)

**Configuration:**
- DB_PATH environment variable (default: /app/data/aupat.db)
- API_HOST environment variable (default: localhost:5002)
- PORT (default: 5002)

**How to run:**
```bash
python app.py
```

**Health check:**
```bash
curl http://localhost:5002/api/health
```

**NEW: Interactive API Documentation:**
Visit `http://localhost:5002/api/docs` for Swagger UI
- Try out API endpoints interactively
- View complete request/response schemas
- Download OpenAPI spec from `/api/apispec.json`

---

## V0.1.0 NEW COMPONENTS (2025-11-19)

### scripts/api_v010_stats.py

**Location:** `/home/user/aupat/scripts/api_v010_stats.py`
**LOC:** 180 lines (LILBITS compliant)
**Purpose:** Dashboard statistics API endpoints

**What it does:**
- Provides statistics endpoints for LocationsDashboard
- Single endpoint returns all dashboard data in one call
- Calculates top states, types, counts
- Returns pinned, recent, updated locations

**Key endpoints:**
- `GET /api/stats/dashboard` - All dashboard statistics
- `GET /api/stats/random` - Random location

**Dependencies:**
- scripts.utils (get_db_connection)

**Database tables:**
- READ: locations

**How to use:**
```bash
curl http://localhost:5002/api/stats/dashboard
```

**Integration:** Registered in scripts/api_routes_v010.py

---

### scripts/db_migrate_add_stats_columns.py

**Location:** `/home/user/aupat/scripts/db_migrate_add_stats_columns.py`
**LOC:** 131 lines (LILBITS compliant)
**Purpose:** Database migration to add statistics columns

**What it does:**
- Adds pinned, documented, favorite columns to locations table
- Creates 3 performance indexes
- Flexible path detection (CLI arg, env var, user.json)
- Idempotent (safe to run multiple times)

**Columns added:**
- pinned INTEGER DEFAULT 0
- documented INTEGER DEFAULT 1
- favorite INTEGER DEFAULT 0

**Indexes created:**
- idx_locations_pinned ON locations(pinned DESC)
- idx_locations_documented ON locations(documented)
- idx_locations_favorite ON locations(favorite)

**How to run:**
```bash
python scripts/db_migrate_add_stats_columns.py
# Or with custom path
python scripts/db_migrate_add_stats_columns.py /path/to/aupat.db
```

---

## DESKTOP COMPONENTS (Svelte)

### desktop/src/renderer/lib/LocationsDashboard.svelte

**Location:** `/home/user/aupat/desktop/src/renderer/lib/LocationsDashboard.svelte`
**LOC:** 243 lines
**Purpose:** Main locations dashboard with all 6 sections

**What it displays:**
- Quick Links (Favorites, Random, Un-Documented, Historical, With Notes)
- Pinned Locations (top 5)
- Recent Locations (last 5)
- Recently Updated (last 5)
- Top States (top 5)
- Top Types (top 10)

**Dependencies:**
- LocationCard.svelte (location display)
- StatsCard.svelte (statistics display)

**API calls:**
- window.api.stats.getDashboard()
- window.api.stats.getRandom()

**Events emitted:**
- locationClick - Navigate to location page
- quickLink - Filter by criteria

**LILBITS compliance:** Single responsibility (dashboard display)

---

### desktop/src/renderer/lib/LocationCard.svelte

**Location:** `/home/user/aupat/desktop/src/renderer/lib/LocationCard.svelte`
**LOC:** 67 lines
**Purpose:** Reusable location card component

**What it displays:**
- Location name
- Type and state
- City
- GPS indicator
- Optional date (created/updated)

**Props:**
- location (object) - Location data
- showDate (boolean) - Show date
- dateLabel (string) - Date label text

**Events emitted:**
- click - Location clicked

**Used by:** LocationsDashboard, search results

---

### desktop/src/renderer/lib/StatsCard.svelte

**Location:** `/home/user/aupat/desktop/src/renderer/lib/StatsCard.svelte`
**LOC:** 54 lines
**Purpose:** Statistics display card

**What it displays:**
- Title
- List of items with counts
- Grid or list layout

**Props:**
- title (string) - Card title
- items (array) - Array of {state/type, count}
- type (string) - "list" or "grid" layout

**Events emitted:**
- itemClick - Item clicked

**Used by:** LocationsDashboard (states and types)

---

### desktop/src/renderer/lib/NotesSection.svelte

**Location:** `/home/user/aupat/desktop/src/renderer/lib/NotesSection.svelte`
**LOC:** 270 lines
**Purpose:** Complete CRUD interface for location notes

**What it provides:**
- Create note (modal form)
- Read notes (list display)
- Update note (edit in modal)
- Delete note (with confirmation)

**Props:**
- locationUuid (string) - Location UUID

**API calls:**
- window.api.notes.getByLocation(locationUuid)
- window.api.notes.create(noteData)
- window.api.notes.update(noteUuid, noteData)
- window.api.notes.delete(noteUuid)

**Form fields:**
- Title (required)
- Note text (required)

**LILBITS compliance:** 270 lines (acceptable for full CRUD interface with template)

---

### desktop/src/renderer/lib/SubLocationsList.svelte

**Location:** `/home/user/aupat/desktop/src/renderer/lib/SubLocationsList.svelte`
**LOC:** 63 lines
**Purpose:** Display sub-locations for a location

**What it displays:**
- Sub-location name
- Short name
- Primary indicator

**Props:**
- subLocations (array) - Array of sub-location objects
- locationName (string) - Parent location name

**Events emitted:**
- sublocationClick - Sub-location clicked (for navigation)

**Used by:** LocationPage

---

### desktop/src/renderer/lib/DocumentsList.svelte

**Location:** `/home/user/aupat/desktop/src/renderer/lib/DocumentsList.svelte`
**LOC:** 93 lines
**Purpose:** Display documents list for a location

**What it displays:**
- Document filename
- File size (formatted)
- File type icon
- Download link

**Props:**
- documents (array) - Array of document objects
- locationUuid (string) - Location UUID

**Helper functions:**
- formatFileSize(bytes) - Converts bytes to KB/MB/GB

**Used by:** LocationPage

---

### desktop/src/renderer/lib/NerdStats.svelte

**Location:** `/home/user/aupat/desktop/src/renderer/lib/NerdStats.svelte`
**LOC:** 192 lines
**Purpose:** Technical metadata and statistics display

**What it displays:**
- Location UUID
- GPS coordinates
- Created/Updated dates
- Media counts (images, videos, documents, notes)
- Sub-locations count
- All technical details

**Props:**
- location (object) - Location data
- imagesCount (number)
- videosCount (number)
- documentsCount (number)
- notesCount (number)
- subLocationsCount (number)

**Helper functions:**
- formatDate(dateStr) - Format ISO date to readable
- formatCoordinates(lat, lon) - Format GPS coords

**Used by:** LocationPage

---

### desktop/src/renderer/lib/Browser.svelte

**Location:** `/home/user/aupat/desktop/src/renderer/lib/Browser.svelte`
**LOC:** 247 lines
**Purpose:** Embedded web browser with bookmark support

**What it provides:**
- Electron webview integration
- Navigation (back, forward, reload, stop)
- URL bar with auto-protocol handling
- Bookmark save dialog
- Page title tracking
- Loading state indicators

**Components used:**
- BrowserToolbar.svelte

**Events:**
- did-start-loading
- did-stop-loading
- did-navigate
- did-navigate-in-page
- page-title-updated

**API calls:**
- window.api.bookmarks.create(bookmarkData)

**Technical:**
- Uses Electron `<webview>` tag
- Sandboxed for security
- Allows popups (allowpopups attribute)

---

### desktop/src/renderer/lib/BrowserToolbar.svelte

**Location:** `/home/user/aupat/desktop/src/renderer/lib/BrowserToolbar.svelte`
**LOC:** 115 lines
**Purpose:** Browser navigation toolbar

**What it provides:**
- Back/forward buttons (with disabled states)
- URL input field
- Reload and stop buttons
- Bookmark button

**Props:**
- url (string, bind) - Current URL
- canGoBack (boolean) - Enable back button
- canGoForward (boolean) - Enable forward button
- isLoading (boolean) - Show loading state

**Events emitted:**
- back - Go back
- forward - Go forward
- reload - Reload page
- stop - Stop loading
- navigate - Navigate to URL
- bookmark - Save bookmark

**Used by:** Browser.svelte

---

## API ROUTES

### scripts/api_routes_v012.py

**Location:** `/home/user/aupat/scripts/api_routes_v012.py`
**LOC:** 1,690 lines
**Purpose:** Main REST API endpoints for AUPAT Core

**What it does:**
- Provides 40+ REST API endpoints
- Handles location CRUD operations
- Manages image/video/document uploads
- Implements search and filtering
- Integrates with Immich and ArchiveBox
- Handles map import operations

**Key endpoints:**
- `GET /api/health` - Health check
- `GET /api/health/services` - External service health
- `GET /api/locations` - List all locations
- `GET /api/locations/{uuid}` - Get specific location
- `POST /api/locations` - Create location
- `PUT /api/locations/{uuid}` - Update location
- `DELETE /api/locations/{uuid}` - Delete location
- `GET /api/locations/{uuid}/images` - Get location images
- `POST /api/locations/{uuid}/import` - Upload media
- `GET /api/map/markers` - Get map markers (GeoJSON)
- `GET /api/search` - Search locations
- `GET /api/locations/autocomplete/{field}` - Autocomplete suggestions

**Dependencies:**
- scripts.adapters.archivebox_adapter
- SQLite database (all tables)

**Database tables:**
- READ: locations, images, videos, documents, urls, google_maps_exports
- WRITE: locations, images, videos, urls, google_maps_exports

**External services:**
- Immich (photo management)
- ArchiveBox (web archiving)

**Returns:** JSON responses with status codes

**Error handling:** Try/catch with 400/500 responses

---

### scripts/api_routes_bookmarks.py

**Location:** `/home/user/aupat/scripts/api_routes_bookmarks.py`
**LOC:** 547 lines
**Purpose:** Browser bookmarks integration API

**What it does:**
- Provides REST API for browser bookmarks
- Supports Chrome, Firefox, Safari bookmarks
- Filters by folder, tags, dates
- Associates bookmarks with locations

**Key endpoints:**
- `GET /bookmarks` - List bookmarks with filters
- `POST /bookmarks` - Create bookmark
- `GET /bookmarks/{id}` - Get bookmark
- `PUT /bookmarks/{id}` - Update bookmark
- `DELETE /bookmarks/{id}` - Delete bookmark
- `GET /bookmarks/folders` - List unique folders

**Dependencies:** None

**Database tables:**
- READ/WRITE: bookmarks

**WARNING:** Currently uses hardcoded database path `'data/aupat.db'` at line 38. Should use `current_app.config['DB_PATH']` instead.

**Status:** Blueprint defined but NOT registered in app.py (needs fix)

---

### scripts/api_maps.py

**Location:** `/home/user/aupat/scripts/api_maps.py`
**LOC:** 571 lines
**Purpose:** Map file import API

**What it does:**
- Parses map files (CSV, GeoJSON, KML)
- Checks for duplicate locations
- Imports locations to database
- Manages map export tracking
- Implements reference mode imports

**Key endpoints:**
- `POST /api/maps/parse` - Parse map file
- `POST /api/maps/check-duplicates` - Check for duplicates
- `POST /api/maps/import` - Import to database
- `GET /api/maps/exports` - List map exports
- `DELETE /api/maps/exports/{id}` - Delete map export
- `GET /api/maps/search` - Search reference maps

**Dependencies:**
- scripts.map_import

**Database tables:**
- READ: locations, google_maps_exports, map_locations
- WRITE: google_maps_exports, locations, map_locations

**Status:** Blueprint defined but NOT registered in app.py (needs fix)

---

### scripts/api_sync_mobile.py

**Location:** `/home/user/aupat/scripts/api_sync_mobile.py`
**LOC:** 11.7K lines
**Purpose:** Mobile app synchronization API

**What it does:**
- Handles mobile app push/pull sync
- Tracks sync operations in sync_log
- Resolves sync conflicts
- Supports incremental sync

**Key endpoints:**
- `POST /api/sync/mobile` - Push locations from mobile
- `GET /api/sync/mobile/pull` - Pull new locations

**Dependencies:** None

**Database tables:**
- READ: locations
- WRITE: locations, sync_log

**Sync strategy:** Last-write-wins with conflict logging

---

## DATABASE MIGRATIONS

### scripts/migrate.py (NEW - Migration Orchestrator)

**Location:** `/home/user/aupat/scripts/migrate.py`
**LOC:** ~470 lines
**Purpose:** Database migration orchestrator and version manager

**What it does:**
- Detects current schema version from versions table
- Lists all available migrations in dependency order
- Runs pending migrations automatically
- Tracks which migrations have been applied
- Backs up database before each migration
- Provides safe upgrade path from any version

**Migrations managed:**
- 0.1.2: initial_schema - Base tables (locations, images, videos, URLs)
- 0.1.3: map_imports - KML/CSV/GeoJSON import support
- 0.1.4: archive_workflow - Import batch tracking
- 0.1.4-browser: browser_tables - Browser bookmarks
- 0.1.4-indexes: performance_indexes - Query optimization

**How to run:**
```bash
# Show current version and pending migrations
python scripts/migrate.py --status

# List all available migrations
python scripts/migrate.py --list

# Upgrade to latest version
python scripts/migrate.py --upgrade

# Upgrade to specific version
python scripts/migrate.py --upgrade 0.1.4

# Upgrade without backups (faster, not recommended)
python scripts/migrate.py --upgrade --no-backup
```

**When to run:** After git pull when database schema changes

**Dependencies:**
- All migration scripts (db_migrate_v012.py, v013, v014, etc.)

**Database tables:**
- READ/WRITE: versions (migration tracking)

**Features:**
- Automatic version detection
- Sequential migration execution
- Idempotent (safe to re-run)
- Automatic database backup
- Transaction-safe migrations
- Detailed progress logging

**Exit codes:**
- 0: Success
- 1: Migration failed or error occurred

---

### scripts/db_migrate_v012.py

**Location:** `/home/user/aupat/scripts/db_migrate_v012.py`
**LOC:** 658 lines
**Purpose:** Create base database schema (v0.1.2)

**What it does:**
- Creates all core tables
- Initializes database on first run
- Can be run safely multiple times (idempotent)

**Tables created:**
- locations (main location records)
- images (photo metadata)
- videos (video metadata)
- documents (document metadata)
- urls (web page archives)
- google_maps_exports (map import tracking)
- sync_log (mobile sync tracking)
- map_locations (reference map data)

**Dependencies:**
- scripts.normalize

**Data files:**
- user/user.json (configuration)

**How to run:**
```bash
python scripts/db_migrate_v012.py
```

**When to run:** First time setup or database recreation

---

### scripts/db_migrate_v013.py

**Location:** `/home/user/aupat/scripts/db_migrate_v013.py`
**LOC:** 11.4K lines
**Purpose:** Upgrade schema to v0.1.3 (map improvements)

**What it does:**
- Adds map_reference_cache table
- Adds columns to google_maps_exports
- Adds source_map_id to locations

**Prerequisites:** Must run db_migrate_v012.py first

**Dependencies:**
- scripts.normalize

**How to run:**
```bash
python scripts/db_migrate_v013.py
```

---

### scripts/db_migrate_v014.py

**Location:** `/home/user/aupat/scripts/db_migrate_v014.py`
**LOC:** 13.2K lines
**Purpose:** Upgrade schema to v0.1.4 (import tracking)

**What it does:**
- Adds import_batches table
- Adds import_log table
- Adds columns to images/videos for batch tracking

**Prerequisites:** Must run db_migrate_v013.py first

**Dependencies:**
- scripts.normalize

**How to run:**
```bash
python scripts/db_migrate_v014.py
```

---

## DATABASE OPERATIONS

### scripts/db_import_v012.py

**Location:** `/home/user/aupat/scripts/db_import_v012.py`
**LOC:** 412 lines
**Purpose:** Import photos, videos, documents to database

**What it does:**
- Imports media from metadata.json
- Generates UUIDs and SHA256 hashes
- Uploads to Immich (optional)
- Extracts GPS from EXIF
- Updates location coordinates

**Dependencies:**
- scripts.utils (UUID generation, SHA256)
- scripts.normalize (name/type normalization)
- scripts.immich_integration (Immich upload)

**Data files:**
- user/user.json
- metadata.json (import manifest)

**Database tables:**
- READ: locations
- WRITE: locations, images, videos, documents

**External services:**
- Immich (optional photo upload)

**How to run:**
```bash
python scripts/db_import_v012.py /path/to/metadata.json
```

**Output:** Import summary with counts and errors

---

### scripts/db_organize.py

**Location:** `/home/user/aupat/scripts/db_organize.py`
**LOC:** 422 lines
**Purpose:** Extract EXIF/metadata and categorize media

**What it does:**
- Runs exiftool on images for EXIF extraction
- Runs ffprobe on videos for metadata
- Categorizes by hardware (camera model)
- Updates database with extracted metadata

**Dependencies:**
- scripts.normalize

**Data files:**
- user/user.json
- camera_hardware.json (hardware categorization rules)

**Database tables:**
- READ/WRITE: images, videos

**External tools:**
- exiftool (must be installed)
- ffprobe (must be installed)

**How to run:**
```bash
python scripts/db_organize.py
```

**When to run:** After db_import, before db_folder

---

### scripts/db_folder.py

**Location:** `/home/user/aupat/scripts/db_folder.py`
**LOC:** 371 lines
**Purpose:** Create archive folder structure

**What it does:**
- Creates organized folder hierarchy
- Groups by location type
- Creates subfolders by hardware category
- Prepares for file ingestion

**Dependencies:**
- scripts.normalize

**Data files:**
- user/user.json
- folder.json (folder structure template)

**Database tables:**
- READ: images, videos, documents (counts only)

**How to run:**
```bash
python scripts/db_folder.py
```

**When to run:** After db_organize, before db_ingest

---

### scripts/db_ingest.py

**Location:** `/home/user/aupat/scripts/db_ingest.py`
**LOC:** 464 lines
**Purpose:** Move/hardlink files to archive structure

**What it does:**
- Moves files from staging to archive
- Creates hardlinks (or copies) to preserve originals
- Updates database with new file paths
- Verifies file operations

**Dependencies:**
- scripts.utils (filename generation)
- scripts.normalize

**Data files:**
- user/user.json

**Database tables:**
- READ/WRITE: images, videos

**How to run:**
```bash
python scripts/db_ingest.py
```

**When to run:** After db_folder, before db_verify

---

### scripts/db_verify.py

**Location:** `/home/user/aupat/scripts/db_verify.py`
**LOC:** 354 lines
**Purpose:** Verify database integrity and file consistency

**What it does:**
- Verifies SHA256 hashes match
- Checks file existence
- Reports missing/corrupted files
- Validates database schema

**Dependencies:**
- scripts.utils (SHA256 calculation)
- scripts.normalize

**Data files:**
- user/user.json

**Database tables:**
- READ: images, videos, documents

**How to run:**
```bash
python scripts/db_verify.py
```

**When to run:** After db_ingest or periodically for maintenance

**Output:** Verification report with errors (if any)

---

### scripts/backup.py

**Location:** `/home/user/aupat/scripts/backup.py`
**LOC:** 378 lines
**Purpose:** Backup and restore database

**What it does:**
- Creates timestamped database backups
- Restores from backup
- Tracks backup versions
- Manages backup directory

**Dependencies:**
- scripts.normalize

**Data files:**
- user/user.json

**Database tables:**
- READ/WRITE: versions (backup tracking)

**How to run:**
```bash
# Create backup
python scripts/backup.py

# Restore from backup
python scripts/backup.py --restore /path/to/backup.db
```

**Backup location:** Configured in user.json (db_backup path)

**When to run:** Before major operations (imports, migrations)

---

## WORKER DAEMONS

### scripts/archive_worker.py

**Location:** `/home/user/aupat/scripts/archive_worker.py`
**LOC:** 545 lines
**Purpose:** Background worker for web archiving

**What it does:**
- Polls database every 30 seconds
- Finds URLs with archive_status='pending'
- Calls ArchiveBox CLI to archive URLs
- Updates database with snapshot IDs
- Implements graceful shutdown

**Dependencies:**
- scripts.normalize

**Data files:**
- user/user.json

**Database tables:**
- READ/WRITE: urls

**External services:**
- ArchiveBox (subprocess CLI calls)

**How to run:**
```bash
# Start daemon
python scripts/archive_worker.py

# Or run as macOS service
launchctl load com.aupat.worker.plist
```

**Shutdown:** Ctrl+C or SIGTERM signal

**Logs:** stdout/stderr (configure logging in user.json)

---

### scripts/media_extractor.py

**Location:** `/home/user/aupat/scripts/media_extractor.py`
**LOC:** 644 lines
**Purpose:** Extract media from archived web pages

**What it does:**
- Polls for archived URLs needing media extraction
- Scans ArchiveBox snapshots for images/videos
- Uploads extracted media to Immich
- Links media to locations
- Updates media_extracted count

**Dependencies:**
- scripts.normalize
- scripts.utils (UUID, SHA256)

**Data files:**
- user/user.json

**Database tables:**
- READ: urls
- WRITE: urls, images, videos

**External services:**
- ArchiveBox (file system access)
- Immich (optional upload)

**How to run:**
```bash
python scripts/media_extractor.py
```

**Poll interval:** 30 seconds

**When to run:** Continuously in background after archive_worker

---

## UTILITY MODULES

### scripts/logging_config.py (NEW - Structured Logging)

**Location:** `/home/user/aupat/scripts/logging_config.py`
**LOC:** ~285 lines
**Purpose:** Centralized structured JSON logging configuration

**What it provides:**
- JSON formatted logging (optional)
- Correlation IDs for request tracing
- Sensitive data redaction (passwords, tokens, API keys)
- Configurable log levels via environment variables
- Both JSON and text format support

**Key functions:**
- `get_logger(name, level=None, force_json=False)` - Get configured logger
- `correlation_context(correlation_id)` - Context manager for correlation IDs
- `set_correlation_id(id)` / `clear_correlation_id()` - Manual correlation ID management
- `init_logging(module_name, json_format=False)` - Initialize logging for a module

**Usage:**
```python
from scripts.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Processing started", extra={"location_id": "abc123", "count": 10})
```

**Correlation ID example:**
```python
from scripts.logging_config import correlation_context

with correlation_context("req-123"):
    logger.info("Request processing")  # Will include correlation_id in logs
```

**Environment variables:**
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `LOG_FORMAT` - json or text (default: text for backward compatibility)

**Dependencies:**
- `python-json-logger>=2.0.7` (optional, falls back to text if not installed)

**Used by:** New scripts (opt-in, backward compatible)

**No direct execution** - import as module

**Features:**
- Automatic sensitive data redaction
- Correlation IDs for distributed tracing
- JSON output for log aggregation systems
- Backward compatible with existing logging code

---

### scripts/utils.py

**Location:** `/home/user/aupat/scripts/utils.py`
**LOC:** 430 lines
**Purpose:** Common utility functions

**What it provides:**
- UUID generation with collision detection
- SHA256 hash calculation
- Filename generation (standardized format)
- File type determination
- Duplicate detection

**Key functions:**
- `generate_uuid(cursor, table_name, uuid_field)` - Generate unique UUID
- `calculate_sha256(file_path)` - Calculate file hash
- `generate_filename(loc_uuid, file_type, extension)` - Create standardized filename
- `determine_file_type(file_path)` - Categorize as image/video/document
- `check_sha256_collision(cursor, sha256)` - Find duplicate files
- `check_location_name_collision(cursor, location_name)` - Find duplicate locations

**Dependencies:** None (leaf module)

**Database tables:**
- READ: locations, urls (for collision detection)

**Used by:** db_import_v012, db_ingest, db_verify, media_extractor, map_import

**No direct execution** - import as module

---

### scripts/normalize.py

**Location:** `/home/user/aupat/scripts/normalize.py`
**LOC:** 500 lines
**Purpose:** Text normalization and standardization

**What it provides:**
- Location name normalization
- State code validation
- Date/time standardization
- File extension normalization
- Author name standardization

**Key functions:**
- `normalize_location_name(name)` - Unidecode + titlecase
- `normalize_state_code(state)` - Validate US state codes
- `normalize_location_type(loc_type)` - Standardize type names
- `normalize_datetime(date_str)` - Convert to ISO 8601
- `normalize_extension(ext)` - Lowercase extension
- `normalize_author(author)` - Standardize author names
- `load_type_mapping()` - Load location type mappings

**Dependencies:**
- unidecode (optional, for Unicode normalization)
- dateutil (optional, for date parsing)
- postal (optional, for address parsing)

**Data files:**
- location_type_mapping.json

**Used by:** 13 different modules (most imported module)

**No direct execution** - import as module

---

### scripts/import_helpers.py

**Location:** `/home/user/aupat/scripts/import_helpers.py`
**LOC:** 338 lines
**Purpose:** Import batch tracking and logging

**What it provides:**
- Import batch creation
- File-level import logging
- Backup integration for imports
- Import status tracking

**Key functions:**
- `create_backup_for_import(config)` - Backup before import
- `start_import_batch(config, import_type, ...)` - Start batch tracking
- `log_file_import(config, batch_id, ...)` - Log individual files
- `complete_import_batch(config, batch_id)` - Mark batch complete
- `fail_import_batch(config, batch_id, error)` - Mark batch failed

**Dependencies:**
- scripts.normalize
- scripts.backup

**Data files:**
- user/user.json

**Database tables:**
- WRITE: import_batches, import_log
- READ: import_batches, import_log

**Used by:** api_routes_v012 (for API imports)

**No direct execution** - import as module

---

### scripts/map_import.py

**Location:** `/home/user/aupat/scripts/map_import.py`
**LOC:** 791 lines
**Purpose:** Map file parsing and import

**What it provides:**
- CSV map parsing
- GeoJSON map parsing
- KML/KMZ map parsing
- Duplicate detection (fuzzy matching)
- Reference mode imports
- Map search

**Key functions:**
- `parse_csv_map(content)` - Parse CSV format
- `parse_geojson_map(content)` - Parse GeoJSON format
- `parse_kml_map(content)` - Parse KML format
- `find_duplicates(locations)` - Find existing locations
- `import_locations_to_db(cursor, locations, mode)` - Import to database
- `search_reference_maps(cursor, query)` - Search reference maps
- `normalize_state(state_str)` - Normalize state abbreviations

**Dependencies:** None (leaf module - reads data files only)

**Database tables:**
- READ: locations (duplicate detection)
- WRITE: locations, map_locations

**Used by:** api_maps

**No direct execution** - import as module

---

### scripts/immich_integration.py

**Location:** `/home/user/aupat/scripts/immich_integration.py`
**LOC:** 415 lines
**Purpose:** Immich photo management integration

**What it provides:**
- Immich adapter initialization
- Photo/video upload workflow
- GPS extraction from EXIF
- Location GPS updates from photos

**Key functions:**
- `get_immich_adapter()` - Get configured Immich instance
- `upload_to_immich(file_path, adapter)` - Upload and return asset ID
- `process_media_for_immich(file_path)` - Extract metadata
- `update_location_gps(cursor, loc_uuid, exif_data)` - Update location GPS

**Dependencies:**
- adapters.immich_adapter (WARNING: uses relative path, should be scripts.adapters.immich_adapter)
- PIL/Pillow (optional, for image dimensions)

**Database tables:**
- READ/WRITE: locations (GPS updates)

**External services:**
- Immich API

**Used by:** db_import_v012

**No direct execution** - import as module

---

## EXTERNAL ADAPTERS

### scripts/adapters/immich_adapter.py

**Location:** `/home/user/aupat/scripts/adapters/immich_adapter.py`
**LOC:** ~500 lines
**Purpose:** Immich HTTP API wrapper

**What it provides:**
- HTTP client for Immich API
- Retry logic with exponential backoff
- Health check endpoint
- Photo/video upload
- Asset metadata retrieval
- Thumbnail URL generation

**Key methods:**
- `_request(method, endpoint, **kwargs)` - HTTP request with retries
- `health_check()` - Check service availability
- `upload_photo(file_path, filename)` - Upload media
- `get_asset_metadata(asset_id)` - Get asset info
- `get_thumbnail_url(asset_id, size)` - Get thumbnail URL

**Dependencies:**
- requests (HTTP client)
- tenacity (retry logic)

**Configuration:**
- IMMICH_URL environment variable
- IMMICH_API_KEY environment variable

**External services:**
- Immich photo management server

**Used by:** api_routes_v012, immich_integration

**Example:**
```python
from scripts.adapters.immich_adapter import create_immich_adapter

adapter = create_immich_adapter()
asset_id = adapter.upload_photo('/path/to/photo.jpg', 'photo.jpg')
```

---

### scripts/adapters/archivebox_adapter.py

**Location:** `/home/user/aupat/scripts/adapters/archivebox_adapter.py`
**LOC:** ~530 lines
**Purpose:** ArchiveBox HTTP API wrapper

**What it provides:**
- HTTP client for ArchiveBox API
- Retry logic with exponential backoff
- Health check endpoint
- URL archiving
- Snapshot status checking
- Media extraction

**Key methods:**
- `_request(method, endpoint, **kwargs)` - HTTP request with retries
- `health_check()` - Check service availability
- `archive_url(url)` - Submit URL for archiving
- `get_status(snapshot_id)` - Check archive status
- `extract_media(snapshot_id)` - Extract media files

**Dependencies:**
- requests (HTTP client)
- tenacity (retry logic)

**Configuration:**
- ARCHIVEBOX_URL environment variable
- ARCHIVEBOX_USERNAME environment variable
- ARCHIVEBOX_PASSWORD environment variable

**External services:**
- ArchiveBox web archiving server

**Used by:** api_routes_v012

**Example:**
```python
from scripts.adapters.archivebox_adapter import create_archivebox_adapter

adapter = create_archivebox_adapter()
snapshot_id = adapter.archive_url('https://example.com')
```

---

## ADVANCED MIGRATIONS

### scripts/migrations/add_browser_tables.py

**Location:** `/home/user/aupat/scripts/migrations/add_browser_tables.py`
**LOC:** 8.4K lines
**Purpose:** Add browser bookmarks support (v0.1.2-browser)

**What it does:**
- Creates bookmarks table
- Adds browser integration fields to urls table
- Initializes browser sync schema

**Prerequisites:** Must run after db_migrate_v012.py

**Dependencies:**
- scripts.normalize

**Database tables:**
- CREATE: bookmarks
- MODIFY: urls (add browser fields)

**How to run:**
```bash
python scripts/migrations/add_browser_tables.py
```

**When to run:** If you want browser bookmarks integration

---

### scripts/migrations/add_performance_indexes.py

**Location:** `/home/user/aupat/scripts/migrations/add_performance_indexes.py`
**LOC:** 6.5K lines
**Purpose:** Add database indexes for query optimization

**What it does:**
- Creates indexes on frequently queried fields
- Optimizes location type queries
- Optimizes bookmark title queries
- Improves search performance

**Prerequisites:** Can run after any migration

**Dependencies:** None

**Database tables:**
- CREATE/ADD: indexes on locations(type), bookmarks(title)

**How to run:**
```bash
python scripts/migrations/add_performance_indexes.py
```

**When to run:** After initial data import or when queries are slow

---

## STARTUP SCRIPTS

### start_aupat.sh (v0.1.0 Smart Startup)

**Location:** `/home/user/aupat/start_aupat.sh`
**LOC:** 168 lines (LILBITS compliant)
**Purpose:** Smart startup with first-run intelligence for v0.1.0

**What it does:**
- Checks port 5002 availability
- Activates Python virtual environment (with helpful error if missing)
- Sets PYTHONPATH for proper module imports
- Runs health_check_simple.py automatically
- Offers fixes for common issues (missing database, missing desktop deps)
- Auto-installs desktop dependencies if missing
- Starts Flask API on port 5002
- Starts Electron desktop app with dev server
- Implements graceful shutdown (Ctrl+C)

**How to run:**
```bash
# Normal startup with health checks
./start_aupat.sh

# Skip health checks (advanced users)
./start_aupat.sh --skip-health
```

**Ports used:**
- 5002: Flask API
- 5173: Electron dev server (auto-assigned by vite)

**First-Run Experience:**
- Detects missing virtual environment
- Detects missing user.json
- Detects missing database
- Detects missing desktop node_modules
- Auto-installs desktop dependencies
- Prompts user to fix issues or run bootstrap
- Allows override to continue anyway

**Exit Behavior:**
- Graceful shutdown on Ctrl+C
- Cleans up both backend and frontend PIDs
- Force kills if processes don't exit gracefully

**LILBITS Compliance:** ✓ One script = one function (smart startup)

---

### start_server.sh

**Location:** `/home/user/aupat/start_server.sh`
**LOC:** ~50 lines
**Purpose:** Start API server only (no desktop app)

**What it does:**
- Starts Flask API on port 5000
- Prompts to create database if missing
- Runs in foreground

**How to run:**
```bash
./start_server.sh
```

**Port used:** 5000

**Use case:** Headless deployments, API-only mode

---

### scripts/advanced/start_api.sh

**Location:** `/home/user/aupat/scripts/advanced/start_api.sh`
**LOC:** 213 lines
**Purpose:** Advanced API server startup with PID management

**What it does:**
- Checks if server already running
- Manages PID file for process tracking
- Can force restart with --force flag
- Shows status with --status flag
- Implements health checks
- Comprehensive logging

**How to run:**
```bash
# Start server
./scripts/advanced/start_api.sh

# Force restart
./scripts/advanced/start_api.sh --force

# Show status
./scripts/advanced/start_api.sh --status
```

**PID file:** api_server.pid
**Log file:** api_server.log

**Use case:** Production deployments, systemd integration

---

### docker-start.sh

**Location:** `/home/user/aupat/docker-start.sh`
**LOC:** ~100 lines
**Purpose:** Start full stack with Docker Compose

**What it does:**
- Pre-flight checks (Docker installed, daemon running)
- Creates required directories
- Pulls latest images
- Builds AUPAT Core container
- Starts all services
- Waits for health checks

**Services started:**
- AUPAT Core (port 5001)
- Immich (port 2283)
- ArchiveBox (port 8001)
- PostgreSQL (internal)
- Redis (internal)

**How to run:**
```bash
./docker-start.sh
```

**Use case:** Full stack with all external services

---

### launch.sh (NEW - Unified Launch Script)

**Location:** `/home/user/aupat/launch.sh`
**LOC:** ~500 lines
**Purpose:** Unified launcher for all startup modes

**What it does:**
- Consolidates all startup methods into single script
- Supports development, API-only, Docker, status, and health check modes
- Manages PID files and graceful shutdown
- Provides comprehensive status checking

**Modes:**
- `--dev, -d` - Start full stack (API + Desktop) for development
- `--api, -a` - Start API server only
- `--docker` - Start with Docker Compose
- `--status, -s` - Show status of running services
- `--stop` - Stop all running services
- `--health, -h` - Run comprehensive health checks
- `--help` - Show help message

**How to run:**
```bash
# Start development environment
./launch.sh --dev

# Start API only
./launch.sh --api

# Check status
./launch.sh --status

# Stop everything
./launch.sh --stop

# Run health checks
./launch.sh --health

# With custom port
./launch.sh --api --port 5000
```

**Features:**
- Color-coded output
- Port conflict detection
- Prerequisites checking
- PID file management
- Graceful shutdown
- Health check integration

**When to run:** Primary method for starting AUPAT (replaces start_aupat.sh)

**Dependencies:** bash, Python 3, virtual environment

---

### install.sh

**Location:** `/home/user/aupat/install.sh`
**LOC:** ~150 lines
**Purpose:** System setup and dependency installation

**What it does:**
- Detects OS (macOS/Linux)
- Installs system dependencies
- Creates Python virtual environment
- Installs Python packages
- Checks Docker availability

**How to run:**
```bash
./install.sh [--skip-docker]
```

**Installs:**
- Python 3.8+
- Node.js 16+
- exiftool
- ffmpeg
- Python packages from requirements.txt

**When to run:** First time setup

---

### update_and_start.sh

**Location:** `/home/user/aupat/update_and_start.sh`
**LOC:** ~30 lines
**Purpose:** Update dependencies and restart app

**What it does:**
- Updates npm dependencies in desktop/
- Restarts the application

**How to run:**
```bash
./update_and_start.sh
```

**When to run:** After git pull

---

### scripts/generate_plist.py (NEW)

**Location:** `/home/user/aupat/scripts/generate_plist.py`
**LOC:** ~200 lines
**Purpose:** Generate macOS LaunchAgent plist from template

**What it does:**
- Generates com.aupat.worker.plist from template
- Replaces {{PLACEHOLDERS}} with actual system paths
- Automatically detects project root, Python path, venv path
- Ensures logs directory exists
- Shows installation instructions

**Why it exists:**
- Original plist had hardcoded paths: `/Users/bryant/Documents/tools/aupat/`
- Wouldn't work on other machines
- Now portable across any macOS system

**How to run:**
```bash
# Generate with default output
python scripts/generate_plist.py

# Generate with custom output path
python scripts/generate_plist.py --output /path/to/output.plist
```

**What it generates:**
- Replaces `{{PYTHON_PATH}}` with actual Python interpreter
- Replaces `{{PROJECT_PATH}}` with actual project directory
- Replaces `{{VENV_PATH}}` with actual venv directory
- Adds environment variables (DB_PATH, PATH)

**Output:**
- Creates com.aupat.worker.plist
- File is in .gitignore (regenerate on each machine)
- Shows installation commands for macOS LaunchAgent

**Installation on macOS:**
```bash
# Generate the plist
python scripts/generate_plist.py

# Install
cp com.aupat.worker.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.aupat.worker.plist

# Check status
launchctl list | grep aupat
```

**When to run:**
- First time setup on new machine
- After moving project to different directory
- After changing Python version or venv

**Dependencies:**
- None (uses standard library only)

**Follows LILBITS principle:** One script, one purpose - generate plist

---

## SYSTEM HEALTH

### scripts/health_check_simple.py (v0.1.0 Health Check)

**Location:** `/home/user/aupat/scripts/health_check_simple.py`
**LOC:** 177 lines (LILBITS compliant)
**Purpose:** Simple health check for v0.1.0 first-run experience

**What it checks:**
- Python version (3.11+ required)
- Virtual environment activation status
- user.json existence and validity
- Database existence and accessibility
- Desktop dependencies (node_modules)
- External tools (exiftool, ffmpeg) - optional

**How to run:**
```bash
# Run standalone
python scripts/health_check_simple.py

# Or via start_aupat.sh (automatic)
./start_aupat.sh

# Returns exit code 0 if healthy, 1 if problems
```

**Output:**
- Color-coded console output
- Clear [OK]/[FAIL]/[WARN]/[SKIP] statuses
- Helpful fix suggestions
- Exit code for scripting

**Integration:**
- Called automatically by start_aupat.sh
- Can be skipped with --skip-health flag
- Blocks startup if critical checks fail (with override option)

**LILBITS Compliance:** ✓ One script = one function (health check)

---

### scripts/health_check.py (Comprehensive Health Check)

**Location:** `/home/user/aupat/scripts/health_check.py`
**LOC:** ~500 lines
**Purpose:** Comprehensive system health verification for v0.1.2+

**What it checks:**
- Database connectivity and write capability
- File system access and write permissions
- Disk space availability (warns if <1GB)
- External tools (exiftool, ffmpeg)
- External services (Immich, ArchiveBox)

**How to run:**
```bash
# Run standalone
python scripts/health_check.py

# Or via launch script
./launch.sh --health

# Returns JSON with detailed results
```

**Output:**
- Console output with color-coded status
- JSON file: health_check_results.json
- Exit code 0 (pass/warn) or 1 (fail)

**Check statuses:**
- `pass` - Check succeeded (green ✓)
- `fail` - Check failed (red ✗)
- `warn` - Check passed with warnings (yellow ⚠)
- `skip` - Check skipped (blue ○)

**JSON output format:**
```json
{
  "overall_status": "pass",
  "checks": {
    "database_connectivity": {
      "status": "pass",
      "message": "Database accessible (42 locations)"
    },
    "database_write": {
      "status": "pass",
      "message": "Database is writable"
    }
  },
  "summary": {
    "passed": 6,
    "failed": 0,
    "warnings": 2,
    "skipped": 0,
    "total": 8
  },
  "warnings": [],
  "errors": []
}
```

**Dependencies:**
- sqlite3 (standard library)
- requests (optional, for service checks)

**When to run:**
- After installation
- Before major operations
- When troubleshooting issues
- As part of monitoring

**Integration:**
- Can be called from API endpoints
- Used by launch.sh --health
- Suitable for monitoring systems

---

## TESTING SCRIPTS

### test_map_api.py

**Location:** `/home/user/aupat/test_map_api.py`
**LOC:** 105 lines
**Purpose:** Test map import API endpoints

**What it tests:**
- CSV map parsing
- Duplicate detection
- Map import to database

**Test data:**
- test_map_import.csv

**How to run:**
```bash
# Start API server first
./start_server.sh

# In another terminal
python test_map_api.py
```

**Requirements:** API server running on localhost:5002

---

## SCRIPT EXECUTION WORKFLOWS

### Full Import Workflow

Execute in this order:

1. **Backup** - Create database backup
   ```bash
   python scripts/backup.py
   ```

2. **Import** - Import media with metadata
   ```bash
   python scripts/db_import_v012.py metadata.json
   ```

3. **Organize** - Extract EXIF/metadata
   ```bash
   python scripts/db_organize.py
   ```

4. **Folder** - Create archive folder structure
   ```bash
   python scripts/db_folder.py
   ```

5. **Ingest** - Move files to archive
   ```bash
   python scripts/db_ingest.py
   ```

6. **Verify** - Verify integrity
   ```bash
   python scripts/db_verify.py
   ```

### Migration Workflow

Execute in this order:

1. **v0.1.2 Base Schema**
   ```bash
   python scripts/db_migrate_v012.py
   ```

2. **v0.1.3 Map Improvements**
   ```bash
   python scripts/db_migrate_v013.py
   ```

3. **v0.1.4 Import Tracking**
   ```bash
   python scripts/db_migrate_v014.py
   ```

4. **Browser Support** (optional)
   ```bash
   python scripts/migrations/add_browser_tables.py
   ```

5. **Performance Indexes** (optional)
   ```bash
   python scripts/migrations/add_performance_indexes.py
   ```

### Background Workers

Run continuously:

1. **Archive Worker** - Web archiving daemon
   ```bash
   python scripts/archive_worker.py &
   ```

2. **Media Extractor** - Extract media from archives
   ```bash
   python scripts/media_extractor.py &
   ```

---

## SCRIPT DEPENDENCY SUMMARY

**Most imported modules:**
1. scripts.normalize (13 files depend on it)
2. scripts.utils (5 files depend on it)
3. scripts.adapters.* (multiple API routes)

**Leaf modules (no project imports):**
- scripts.utils
- scripts.normalize
- scripts.adapters.immich_adapter
- scripts.adapters.archivebox_adapter
- scripts.map_import

**Scripts with external dependencies:**
- db_organize (exiftool, ffprobe)
- archive_worker (ArchiveBox CLI)
- immich_integration (Immich API, PIL/Pillow)
- All adapters (requests, tenacity)

---

## SCRIPT MAINTENANCE

### Adding a New Script

1. Create script in appropriate directory
2. Follow LILBITS principles (one function, max 200 lines)
3. Add type hints and docstrings
4. Include error handling
5. Write unit tests
6. Document in this file

### Script Template

```python
#!/usr/bin/env python3
"""
Brief description of script purpose.

Detailed description with usage examples.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def main_function(param: str) -> Optional[Dict[str, Any]]:
    """
    Main function description.

    Args:
        param: Parameter description

    Returns:
        Result description

    Raises:
        ValueError: When validation fails
    """
    try:
        # Implementation
        result = {}
        return result
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    # CLI handling
    main_function("example")
```

---

## KNOWN ISSUES

1. **api_routes_bookmarks.py:38** - Hardcoded database path, should use config
2. **immich_integration.py** - Uses relative import path, should use scripts.adapters.immich_adapter
3. **api_routes_bookmarks.py** - Blueprint not registered in app.py
4. **api_maps.py** - Blueprint not registered in app.py
5. Multiple scripts lack explicit transaction boundaries

See docs/dependency_map.md for full issue list.

---

## VERSION HISTORY

- 1.0.0 (2025-11-18): Initial documentation of all scripts

---

## REFERENCES

- claude.md: Development rules and processes
- techguide.md: Technical architecture guide
- docs/dependency_map.md: Complete file dependency map
- README.md: Project overview and quick start

---

End of LILBITS documentation.
