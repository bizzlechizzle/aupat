# AUPAT Codebase Dependency Map

## COMPREHENSIVE FILE DEPENDENCY ANALYSIS

### 1. MAIN APPLICATION ENTRY POINT

FILE: /home/user/aupat/app.py
- Imports from project:
  - scripts.api_routes_v012 (register_api_routes)
  - scripts.api_sync_mobile (register_mobile_sync_routes)
- Reads data files: None directly
- Database tables: All (via imported modules)
- API endpoints exposed:
  - GET / (root endpoint with API info)
  - POST/GET /api/* (delegated to registered blueprints)
  - POST/GET /api/sync/* (delegated to registered blueprints)
- External services: None directly
- Called by: Flask application runner

---

## 2. CORE API ROUTES

FILE: /home/user/aupat/scripts/api_routes_v012.py
- Imports from project:
  - scripts.adapters.archivebox_adapter (create_archivebox_adapter)
- Reads data files: None directly
- Database tables:
  - READ: locations, images, videos, documents, urls, google_maps_exports, import_batches
  - WRITE: locations, images, videos, urls, google_maps_exports
  - CREATE: (via registered function)
- API endpoints exposed:
  - GET /api/health (health check)
  - GET /api/health/services (service health check for Immich/ArchiveBox)
  - GET /api/map/markers (map clustering data)
  - GET /api/locations/{loc_uuid} (location details)
  - GET /api/search (search functionality)
  - POST/GET /api/media/* (media endpoints)
  - POST/GET /api/import/* (import endpoints)
  - GET/POST/PUT/DELETE /api/locations/* (location CRUD)
  - POST /api/locations/{loc_uuid}/media/* (media upload)
- External services:
  - Immich (via adapter)
  - ArchiveBox (via adapter)
- Called by: app.py (via register_api_routes)

FILE: /home/user/aupat/scripts/api_routes_bookmarks.py
- Imports from project: None
- Reads data files: None
- Database tables:
  - READ: bookmarks
  - WRITE: bookmarks
- API endpoints exposed:
  - GET /bookmarks (list bookmarks with filters)
  - POST /bookmarks (create bookmark)
  - GET /bookmarks/{id} (get bookmark)
  - PUT /bookmarks/{id} (update bookmark)
  - DELETE /bookmarks/{id} (delete bookmark)
  - GET /bookmarks/folders (list unique folders)
- External services: None
- Called by: Must be registered separately in app.py

FILE: /home/user/aupat/scripts/api_maps.py
- Imports from project:
  - scripts.map_import (parse_csv_map, parse_geojson_map, parse_kml_map, find_duplicates, import_locations_to_db, search_reference_maps, generate_short_uuid)
- Reads data files: None directly (via map_import)
- Database tables:
  - READ: locations, google_maps_exports, map_locations
  - WRITE: google_maps_exports, locations, map_locations
- API endpoints exposed:
  - POST /api/maps/parse (parse map files)
  - POST /api/maps/check-duplicates (check for duplicate locations)
  - POST /api/maps/import (import map to database)
  - GET /api/maps/exports (list all map exports)
  - DELETE /api/maps/exports/{id} (delete map)
  - GET /api/maps/search (search reference maps)
- External services: None
- Called by: app.py (via register_api_routes, but must be explicitly registered)

FILE: /home/user/aupat/scripts/api_sync_mobile.py
- Imports from project: None
- Reads data files: None
- Database tables:
  - READ: locations
  - WRITE: locations, sync_log
- API endpoints exposed:
  - POST /api/sync/mobile (push locations from mobile)
  - GET /api/sync/mobile/pull (pull new locations for mobile)
- External services: None
- Called by: app.py (via register_mobile_sync_routes)

---

## 3. DATABASE MIGRATION SCRIPTS

FILE: /home/user/aupat/scripts/db_migrate_v012.py
- Imports from project:
  - scripts.normalize (normalize_datetime)
- Reads data files: user.json
- Database tables:
  - CREATE: locations, images, videos, documents, urls, google_maps_exports, sync_log, map_locations
- API endpoints: None
- External services: None
- Called by: Manual execution or installation scripts

FILE: /home/user/aupat/scripts/db_migrate_v013.py
- Imports from project:
  - scripts.normalize (normalize_datetime)
- Reads data files: user.json
- Database tables:
  - CREATE: map_reference_cache
  - MODIFY: google_maps_exports (add columns), locations (add source_map_id)
- API endpoints: None
- External services: None
- Called by: Manual execution for upgrades

FILE: /home/user/aupat/scripts/db_migrate_v014.py
- Imports from project:
  - scripts.normalize (normalize_datetime)
- Reads data files: user.json
- Database tables:
  - CREATE: import_batches, import_log
  - MODIFY: images, videos (add hardware_category, archive_path, import_batch_id fields)
- API endpoints: None
- External services: None
- Called by: Manual execution for upgrades

---

## 4. DATABASE OPERATIONS SCRIPTS

FILE: /home/user/aupat/scripts/db_import_v012.py
- Imports from project:
  - scripts.utils (generate_uuid, calculate_sha256, generate_filename, determine_file_type, check_sha256_collision, check_location_name_collision)
  - scripts.normalize (normalize_location_name, normalize_state_code, normalize_location_type, normalize_datetime, normalize_extension, normalize_author)
  - scripts.immich_integration (get_immich_adapter, process_media_for_immich, update_location_gps)
- Reads data files: user.json, metadata.json (parameter)
- Database tables:
  - READ: locations
  - WRITE: locations, images, videos, documents
- API endpoints: None
- External services:
  - Immich (via immich_integration)
- Called by: Manual execution for imports

FILE: /home/user/aupat/scripts/db_organize.py
- Imports from project:
  - scripts.normalize (normalize_datetime)
- Reads data files: user.json, camera_hardware.json
- Database tables:
  - READ: images, videos
  - WRITE: images, videos
- API endpoints: None
- External services:
  - exiftool (subprocess)
  - ffprobe (subprocess)
- Called by: Manual execution in archive workflow

FILE: /home/user/aupat/scripts/db_folder.py
- Imports from project:
  - scripts.normalize (normalize_location_type)
- Reads data files: user.json, folder.json
- Database tables:
  - READ: images, videos, documents (count only)
- API endpoints: None
- External services: None
- Called by: Manual execution in archive workflow

FILE: /home/user/aupat/scripts/db_ingest.py
- Imports from project:
  - scripts.utils (generate_filename)
  - scripts.normalize (normalize_datetime, normalize_extension)
- Reads data files: user.json
- Database tables:
  - READ: images, videos
  - WRITE: images, videos
- API endpoints: None
- External services: None
- Called by: Manual execution in archive workflow

FILE: /home/user/aupat/scripts/db_verify.py
- Imports from project:
  - scripts.utils (calculate_sha256)
  - scripts.normalize (normalize_datetime)
- Reads data files: user.json
- Database tables:
  - READ: images, videos, documents
- API endpoints: None
- External services: None
- Called by: Manual execution in archive workflow

FILE: /home/user/aupat/scripts/backup.py
- Imports from project:
  - scripts.normalize (normalize_datetime)
- Reads data files: user.json
- Database tables:
  - READ: versions table
  - WRITE: versions table
- API endpoints: None
- External services: None
- Called by: Manual execution, import_helpers.py

---

## 5. WORKER DAEMON SCRIPTS

FILE: /home/user/aupat/scripts/archive_worker.py
- Imports from project:
  - scripts.normalize (normalize_datetime)
- Reads data files: user.json
- Database tables:
  - READ: urls
  - WRITE: urls
- API endpoints: None
- External services:
  - ArchiveBox (subprocess CLI)
- Called by: Manual execution as background daemon
- Polling: Every 30 seconds for pending URLs

FILE: /home/user/aupat/scripts/media_extractor.py
- Imports from project:
  - scripts.normalize (normalize_datetime)
  - scripts.utils (generate_uuid, calculate_sha256)
- Reads data files: user.json
- Database tables:
  - READ: urls
  - WRITE: urls, images, videos
- API endpoints: None
- External services:
  - Immich (via adapters)
  - ArchiveBox (file system access)
- Called by: Manual execution as background daemon
- Polling: Every 30 seconds for archived URLs needing media extraction

---

## 6. UTILITY MODULES

FILE: /home/user/aupat/scripts/utils.py
- Imports from project: None
- Reads data files: None
- Database tables:
  - READ: locations, sub_locations, urls (for collision detection)
- API endpoints: None
- External services: None
- Called by:
  - db_import_v012
  - db_ingest
  - db_verify
  - media_extractor
  - map_import
- Key functions:
  - generate_uuid(cursor, table_name, uuid_field) - UUID generation with collision detection
  - calculate_sha256(file_path) - SHA256 hash calculation
  - generate_filename(loc_uuid, file_type, extension) - standardized filenames
  - determine_file_type(file_path) - categorize file as image/video/document
  - check_sha256_collision(cursor, sha256) - detect duplicate files
  - check_location_name_collision(cursor, location_name) - detect duplicate locations

FILE: /home/user/aupat/scripts/normalize.py
- Imports from project: None (optional: unidecode, dateutil, postal)
- Reads data files: location_type_mapping.json
- Database tables: None
- API endpoints: None
- External services: None (optional: libpostal)
- Called by:
  - db_migrate_v012
  - db_migrate_v013
  - db_migrate_v014
  - db_organize
  - db_folder
  - db_import_v012
  - db_ingest
  - db_verify
  - backup
  - archive_worker
  - media_extractor
  - import_helpers
  - api_routes_v012 (via import_helpers)
  - add_browser_tables
- Key functions:
  - normalize_location_name(name) - unidecode + titlecase
  - normalize_state_code(state) - validate and normalize US state codes
  - normalize_location_type(loc_type) - unidecode + titlecase
  - normalize_datetime(date_str) - ISO 8601 format
  - normalize_extension(ext) - lowercase
  - load_type_mapping() - load location_type_mapping.json

FILE: /home/user/aupat/scripts/import_helpers.py
- Imports from project:
  - scripts.normalize (normalize_datetime)
  - scripts.backup (create_backup)
- Reads data files: user.json
- Database tables:
  - WRITE: import_batches, import_log
  - READ: import_batches, import_log
- API endpoints: None
- External services: None
- Called by:
  - api_routes_v012 (for batch tracking during imports)
- Key functions:
  - create_backup_for_import(config) - backup before import
  - start_import_batch(config, import_type, ...) - track import operations
  - log_file_import(config, batch_id, ...) - log individual files

FILE: /home/user/aupat/scripts/map_import.py
- Imports from project: None
- Reads data files: None directly
- Database tables:
  - READ: locations (for duplicate detection)
  - WRITE: locations, map_locations
- API endpoints: None
- External services: None
- Called by:
  - api_maps
- Key functions:
  - parse_csv_map(content) - parse CSV format maps
  - parse_geojson_map(content) - parse GeoJSON format
  - parse_kml_map(content) - parse KML format
  - find_duplicates(locations) - fuzzy match against existing locations
  - import_locations_to_db(cursor, locations, import_mode) - import to DB
  - search_reference_maps(cursor, query) - search reference map cache
  - normalize_state(state_str) - normalize state abbreviations

---

## 7. ADAPTER MODULES (External Service Integration)

FILE: /home/user/aupat/scripts/adapters/immich_adapter.py
- Imports from project: None
- Reads data files: None
- Database tables: None
- API endpoints: None (server-side adapter)
- External services:
  - Immich HTTP API (configurable base_url)
  - Uses: requests, tenacity (retry logic)
- Called by:
  - api_routes_v012 (health check)
  - immich_integration
- Key methods:
  - _request(method, endpoint, **kwargs) - HTTP request with retry logic
  - health_check() - check Immich service availability
  - upload_photo(file_path, filename) - upload photo/video
  - get_asset_metadata(asset_id) - retrieve asset info
  - get_thumbnail_url(asset_id, size) - get thumbnail URL

FILE: /home/user/aupat/scripts/adapters/archivebox_adapter.py
- Imports from project: None
- Reads data files: None
- Database tables: None
- API endpoints: None (server-side adapter)
- External services:
  - ArchiveBox HTTP API (configurable base_url)
  - Uses: requests, tenacity (retry logic)
- Called by:
  - api_routes_v012 (health check)
- Key methods:
  - _request(method, endpoint, **kwargs) - HTTP request with retry logic
  - health_check() - check ArchiveBox service availability
  - archive_url(url) - submit URL for archiving
  - get_status(snapshot_id) - check archive status
  - extract_media(snapshot_id) - extract media files

FILE: /home/user/aupat/scripts/immich_integration.py
- Imports from project:
  - adapters.immich_adapter (create_immich_adapter, ImmichError)
- Reads data files: None
- Database tables:
  - READ: locations (for GPS updates)
  - WRITE: locations
- API endpoints: None
- External services:
  - Immich (via immich_adapter)
  - PIL/Pillow (optional, for image dimensions)
- Called by:
  - db_import_v012
- Key functions:
  - get_immich_adapter() - get configured Immich instance
  - upload_to_immich(file_path, immich_adapter) - upload file and return asset ID
  - process_media_for_immich(file_path) - extract metadata
  - update_location_gps(cursor, loc_uuid, exif_data) - update location GPS from EXIF

---

## 8. DATABASE MIGRATION SCRIPTS (Advanced)

FILE: /home/user/aupat/scripts/migrations/add_browser_tables.py
- Imports from project:
  - scripts.normalize (normalize_datetime)
- Reads data files: None
- Database tables:
  - CREATE: bookmarks
  - MODIFY: urls table (add browser integration fields)
- API endpoints: None
- External services: None
- Called by: Manual migration execution

FILE: /home/user/aupat/scripts/migrations/add_performance_indexes.py
- Imports from project: None
- Reads data files: None
- Database tables:
  - CREATE/ADD: indexes on locations(type), bookmarks(title)
- API endpoints: None
- External services: None
- Called by: Manual migration execution

---

## 9. TEST AND UTILITY SCRIPTS

FILE: /home/user/aupat/test_map_api.py
- Imports from project: None
- Reads data files: test_map_import.csv
- Database tables: None (test script)
- API endpoints: Calls /api/maps/* endpoints
- External services: None
- Called by: Manual testing

---

## DATABASE TABLE DEPENDENCY MATRIX

### Core Tables (v0.1.0-0.1.2)
- locations: Central table
  - ACCESSED BY: api_routes_v012, api_maps, api_sync_mobile, db_verify, map_import, utils, immich_integration
  - FIELDS: loc_uuid (PK), loc_name, aka_name, state, type, sub_type, org_loc, loc_loc, loc_add, lat, lon, ...

- images: Image metadata
  - ACCESSED BY: api_routes_v012, db_ingest, db_organize, db_verify, media_extractor, db_import_v012
  - FIELDS: img_uuid (PK), loc_uuid (FK), img_name, img_loc, img_sha256, camera, ...

- videos: Video metadata
  - ACCESSED BY: api_routes_v012, db_ingest, db_organize, db_verify, media_extractor, db_import_v012
  - FIELDS: vid_uuid (PK), loc_uuid (FK), vid_name, vid_loc, vid_sha256, camera, ...

- documents: Document metadata
  - ACCESSED BY: api_routes_v012, db_verify, db_folder, db_import_v012
  - FIELDS: doc_uuid (PK), loc_uuid (FK), doc_name, doc_loc, doc_sha256, ...

- urls: URL storage for web archiving
  - ACCESSED BY: api_routes_v012, archive_worker, media_extractor
  - FIELDS: url_uuid (PK), url, url_add, url_title, loc_uuid (FK), archive_status, archivebox_snapshot_id, media_extracted

### Map Import Tables (v0.1.2-0.1.3)
- google_maps_exports: Map export tracking
  - ACCESSED BY: api_maps, api_routes_v012
  - FIELDS: export_id (PK), filename, file_size, import_mode, ...

- map_locations: Reference map data
  - ACCESSED BY: api_maps, map_import
  - FIELDS: map_loc_id (PK), map_id, name, state, type, lat, lon, ...

- map_reference_cache: (v0.1.3)
  - ACCESSED BY: api_maps
  - FIELDS: cache_id (PK), map_id, query_hash, results, ...

### Sync & Tracking Tables
- sync_log: Mobile sync tracking
  - ACCESSED BY: api_sync_mobile
  - FIELDS: sync_id (PK), device_id, sync_type, timestamp, items_synced, conflicts, status

- import_batches: (v0.1.4)
  - ACCESSED BY: api_routes_v012, import_helpers
  - FIELDS: batch_id (PK), import_type, start_time, end_time, status, ...

- import_log: (v0.1.4)
  - ACCESSED BY: import_helpers
  - FIELDS: log_id (PK), batch_id (FK), file_path, status, ...

- bookmarks: Browser bookmarks
  - ACCESSED BY: api_routes_bookmarks
  - FIELDS: bookmark_uuid (PK), url, title, folder, tags, ...

### Metadata Tables
- versions: Version tracking
  - ACCESSED BY: backup, db_migrate_*
  - FIELDS: version_id (PK), version_number, applied_at, ...

---

## DATA FILE DEPENDENCY MATRIX

### Configuration Files
- user.json (user/user.json)
  - READ BY: All scripts that need db_path, db_backup, etc.
  - SCRIPTS: db_migrate_v*, db_import_v012, db_organize, db_folder, db_ingest, db_verify, backup, archive_worker, media_extractor, import_helpers, api_routes_v012

### Data/Template Files
- folder.json (data/folder.json)
  - READ BY: db_folder
  - PURPOSE: Defines folder structure for media organization

- camera_hardware.json (data/camera_hardware.json)
  - READ BY: db_organize
  - PURPOSE: Hardware classification rules for EXIF-based categorization

- location_type_mapping.json (data/location_type_mapping.json)
  - READ BY: normalize.py
  - PURPOSE: Type suggestions and mappings for location normalization

### Dynamic Files
- metadata.json (parameter to db_import_v012)
  - READ BY: db_import_v012
  - PURPOSE: Import metadata for batch operations

- Map files (CSV, GeoJSON, KML, KMZ)
  - READ BY: api_maps, map_import
  - PURPOSE: Import location data from various formats

- test_map_import.csv (test file)
  - READ BY: test_map_api.py
  - PURPOSE: Testing map import functionality

---

## EXTERNAL SERVICE INTEGRATION MATRIX

### Immich Photo Storage
- ACCESS POINTS:
  - api_routes_v012: health check endpoint
  - db_import_v012: automatic upload during import
  - immich_integration: wrapper module
- MODULES:
  - immich_adapter: HTTP API abstraction
  - immich_integration: workflow integration
- OPERATIONS:
  - Upload photos/videos
  - Retrieve asset metadata
  - Generate thumbnail URLs
  - Extract GPS from EXIF

### ArchiveBox Web Archiving
- ACCESS POINTS:
  - api_routes_v012: health check endpoint
  - api_routes_v012: URL archiving endpoints
  - archive_worker: background polling daemon
  - media_extractor: extract media from archives
- MODULES:
  - archivebox_adapter: HTTP API abstraction
- OPERATIONS:
  - Submit URLs for archiving
  - Check archive status
  - Extract media from snapshots
  - Retrieve archived content

### External Tools (subprocess)
- exiftool: db_organize.py
  - PURPOSE: Extract EXIF metadata from images
  - OPERATION: subprocess call with JSON output

- ffprobe: db_organize.py
  - PURPOSE: Extract video metadata
  - OPERATION: subprocess call with JSON output

- ArchiveBox CLI: archive_worker.py
  - PURPOSE: Archive URLs from database
  - OPERATION: subprocess call

---

## CIRCULAR DEPENDENCY ANALYSIS

### Potential Circular Dependencies: NONE DETECTED

Analysis shows clean dependency flow:
- Adapters (immich_adapter, archivebox_adapter) have no dependencies on other project modules
- Utils and normalize are leaf modules with no project imports
- Core scripts import only utils/normalize + adapters (unidirectional)
- API routes import only from core modules (unidirectional)
- Migrations are standalone utilities

### Dependency Direction (all healthy):
1. app.py -> api_routes_v012, api_sync_mobile (top-level)
2. api_routes_v012 -> adapters, utils, normalize (downward)
3. db_migrate_v* -> normalize only (downward)
4. db_*_v* -> normalize, utils, adapters (downward)
5. immich_integration -> immich_adapter (downward)
6. import_helpers -> backup, normalize (downward)
7. Adapters -> external services only (no project deps)

NO CIRCULAR DEPENDENCIES FOUND ✓

---

## IMPORT DEPENDENCY GRAPH (by module)

```
app.py
├── scripts.api_routes_v012
│   └── scripts.adapters.archivebox_adapter
├── scripts.api_sync_mobile
└── (all routes register using register_* functions)

scripts.api_routes_v012
├── scripts.adapters.archivebox_adapter
├── scripts.adapters.immich_adapter (indirect via health check)
└── scripts.normalize (indirect via functions)

scripts.api_routes_bookmarks
└── (standalone, must be registered)

scripts.api_maps
└── scripts.map_import
    ├── (no internal imports, uses data files)

scripts.api_sync_mobile
└── (standalone, uses database directly)

scripts.db_import_v012
├── scripts.utils
├── scripts.normalize
└── scripts.immich_integration
    ├── scripts.adapters.immich_adapter
    └── PIL/Pillow (optional external)

scripts.db_migrate_v012/v013/v014
└── scripts.normalize

scripts.db_organize
└── scripts.normalize
    └── (subprocess: exiftool, ffprobe)

scripts.db_folder
└── scripts.normalize

scripts.db_ingest
├── scripts.utils
└── scripts.normalize

scripts.db_verify
├── scripts.utils
└── scripts.normalize

scripts.backup
└── scripts.normalize

scripts.archive_worker
└── scripts.normalize
    └── (subprocess: archivebox CLI)

scripts.media_extractor
├── scripts.normalize
├── scripts.utils
└── scripts.adapters.immich_adapter (optional)

scripts.import_helpers
├── scripts.normalize
└── scripts.backup

scripts.migrations.add_browser_tables
└── scripts.normalize

scripts.migrations.add_performance_indexes
└── (standalone)

Leaf Modules (no internal imports):
- scripts.utils
- scripts.normalize
- scripts.adapters.immich_adapter
- scripts.adapters.archivebox_adapter
- scripts.map_import (conceptually, uses data files not modules)
```

---

## PROBLEMATIC PATTERNS IDENTIFIED

### 1. HARDCODED PATH IN api_routes_bookmarks.py
- Line 38: `conn = sqlite3.connect('data/aupat.db')`
- ISSUE: Uses relative path instead of config
- IMPACT: Will fail if run from different directory
- RECOMMENDATION: Use current_app.config['DB_PATH'] like other modules

### 2. MISSING BLUEPRINT REGISTRATION
- api_routes_bookmarks.py and api_maps.py define blueprints but are NOT registered in app.py
- ISSUE: Endpoints won't be available
- RECOMMENDATION: Add `app.register_blueprint(bookmarks_bp, url_prefix='/api')` to app.py

### 3. OPTIONAL IMPORTS NOT HANDLED CONSISTENTLY
- immich_integration.py tries to import from adapters with relative path: `from adapters.immich_adapter`
- ISSUE: Should be `from scripts.adapters.immich_adapter`
- IMPACT: Import will fail when run from project root

### 4. LOOSE SCHEMA ASSUMPTIONS
- Multiple scripts assume table/column existence without proper checks
- RECOMMENDATION: More robust column existence checks before ALTER TABLE operations

### 5. NO TRANSACTION ISOLATION
- Several scripts perform multi-step operations without explicit transactions
- IMPACT: Potential data inconsistency if process crashes mid-operation
- RECOMMENDATION: Wrap operations in BEGIN/COMMIT blocks

---

## CRITICAL DEPENDENCY NOTES

1. **Database Migrations Must Run In Order**: v0.1.2 -> v0.1.3 -> v0.1.4
2. **user.json is Essential**: All scripts require this configuration file
3. **External Services Are Optional**: Code gracefully degrades if Immich/ArchiveBox unavailable
4. **Data Files Should Be Bundled**: folder.json, camera_hardware.json, location_type_mapping.json
5. **Background Daemons Need Management**: archive_worker.py and media_extractor.py should run continuously

---

## FILE IMPORT COUNT SUMMARY

Scripts importing most external dependencies:
1. api_routes_v012.py - imports adapters, uses all tables
2. db_import_v012.py - imports utils, normalize, immich_integration
3. immich_integration.py - imports immich_adapter
4. media_extractor.py - imports normalize, utils, immich_adapter
5. archive_worker.py - imports normalize

Leaf modules (no internal imports):
1. utils.py
2. normalize.py
3. immich_adapter.py
4. archivebox_adapter.py
5. map_import.py

