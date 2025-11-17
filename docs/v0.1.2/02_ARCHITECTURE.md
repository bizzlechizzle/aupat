# AUPATOOL v0.1.2 - System Architecture

## Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACES                              │
├──────────────────────┬──────────────────────┬──────────────────┤
│  Desktop App         │  Mobile App          │  Web Interface   │
│  (Electron)          │  (Flutter)           │  (Flask/React)   │
│  - Primary UI        │  - Field GPS         │  - Remote Access │
│  - Web Archive       │  - Offline Maps      │  - Read-Only     │
│  - Bulk Import       │  - Photo Capture     │  - Via Cloudflare│
│  - Map View          │  - Sync Queue        │  - Emergency Use │
└──────────────────────┴──────────────────────┴──────────────────┘
                              │
                              │ REST API (JSON)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUPAT CORE API                               │
│                    (Flask + SQLite)                             │
│                                                                 │
│  - Locations database (authoritative)                           │
│  - Relationships (parent/child, similar)                        │
│  - Metadata orchestration                                       │
│  - Import pipeline coordination                                 │
│  - Sync conflict resolution                                     │
│  - Search/filter queries                                        │
│                                                                 │
│  Database: /data/aupat.db (SQLite with WAL)                    │
└─────────────┬─────────────────┬─────────────────┬──────────────┘
              │                 │                 │
              │ API Calls       │ API Calls       │ API Calls
              ▼                 ▼                 ▼
    ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
    │  IMMICH         │ │ ARCHIVEBOX   │ │  AI SERVICES     │
    │  Photo Storage  │ │ Web Archive  │ │  (Future)        │
    ├─────────────────┤ ├──────────────┤ ├──────────────────┤
    │ - Upload photos │ │ - Archive    │ │ - Ollama (LLM)   │
    │ - Thumbnails    │ │   URLs       │ │ - Florence-2     │
    │ - CLIP tagging  │ │ - Extract    │ │   (Image Tags)   │
    │ - Face recog    │ │   media      │ │ - Tesseract OCR  │
    │ - Timeline      │ │ - WARC       │ │ - Address        │
    │ - Mobile sync   │ │   storage    │ │   extraction     │
    │ - PostgreSQL    │ │ - Playwright │ │                  │
    └─────────────────┘ └──────────────┘ └──────────────────┘
              │                 │                 │
              │ Files           │ Files           │ Processing
              ▼                 ▼                 ▼
    ┌─────────────────────────────────────────────────────────┐
    │              SHARED STORAGE (Docker Volumes)            │
    ├─────────────────────────────────────────────────────────┤
    │  /data/aupat.db          - SQLite database              │
    │  /data/immich/           - Photos (content-addressed)   │
    │  /data/archivebox/       - WARC archives + screenshots  │
    │  /data/documents/        - PDFs, scans, exports         │
    │  /data/backups/          - Automated backups            │
    │  /data/ml-cache/         - AI model weights             │
    └─────────────────────────────────────────────────────────┘
```

## Responsibilities of Each Component

### 1. AUPAT Core API (Flask + SQLite)

**Owns:**
- Location entities (loc_uuid, names, types, addresses, GPS)
- Relationships between locations
- Cross-system metadata linkage
- Import orchestration
- Query/search logic
- User authentication (future)

**Does NOT own:**
- Photo files (Immich owns)
- WARC files (ArchiveBox owns)
- Thumbnails (Immich generates)
- ML model weights (AI services own)

**API Endpoints:**
```
GET  /locations                    - List all locations
GET  /locations/{uuid}             - Location details
POST /locations                    - Create location
PUT  /locations/{uuid}             - Update location
GET  /locations/{uuid}/images      - Get image references (returns immich_asset_ids)
GET  /locations/{uuid}/archives    - Get archived URLs
POST /import/images                - Trigger image import
POST /import/documents             - Trigger document import
POST /import/google-maps-export    - Process Google Maps export
GET  /search?q=...                 - Search locations
GET  /map/markers                  - Get all GPS coords for map
POST /sync/mobile                  - Mobile sync endpoint
```

**Port:** 5000
**Language:** Python 3.11+
**Framework:** Flask 3.x
**Database:** SQLite 3.40+ (WAL mode)

### 2. Immich (Photo Storage & AI)

**Owns:**
- Photo and video files
- Thumbnail generation (multiple sizes)
- EXIF metadata extraction
- CLIP-based AI tagging
- Facial recognition
- Mobile app photo sync
- Timeline views
- Album organization

**Integration with AUPAT:**
- AUPAT uploads photos via Immich API
- Immich returns asset_id
- AUPAT stores: img_sha256 → immich_asset_id mapping
- Desktop app fetches thumbnails via Immich API
- Desktop app displays full-res via Immich streaming

**API Used:**
```
POST /api/upload                   - Upload photo
GET  /api/asset/{id}/thumbnail     - Get thumbnail
GET  /api/asset/{id}/original      - Get full resolution
GET  /api/search                   - Search by AI tags
POST /api/asset/{id}/tag           - Manual tagging
```

**Ports:**
- 2283 (API + Web UI)
- 3003 (ML microservice)

**Database:** PostgreSQL (Immich-managed)
**Storage:** Content-addressed (similar to AUPAT philosophy)

### 3. ArchiveBox (Web Archiving)

**Owns:**
- WARC archives of web pages
- Screenshots of archived pages
- Extracted media from web pages
- YouTube videos (via yt-dlp)
- Archive metadata (capture date, status)

**Integration with AUPAT:**
- AUPAT sends URL + location context
- ArchiveBox archives page
- ArchiveBox extracts images/videos
- ArchiveBox notifies AUPAT via webhook
- AUPAT uploads extracted media to Immich
- AUPAT links archived URL to location

**Custom Plugins:**
- Playwright-based high-res extractor
- Facebook login support (via Chrome cookie sharing)
- Instagram carousel extractor
- SmugMug original resolution extractor

**API Used:**
```
POST /api/add                      - Add URL to archive
GET  /api/status/{id}              - Check archive status
GET  /api/snapshots/{id}           - Get archived files
POST /api/extract                  - Trigger media extraction
```

**Port:** 8001
**Storage:** Filesystem-based archives
**Database:** SQLite (ArchiveBox-managed)

### 4. Desktop App (Electron)

**Responsibilities:**
- Primary user interface
- Map visualization (200k markers with clustering)
- Embedded browser for web archiving
- Bulk file import (drag-and-drop folders)
- Location management (CRUD)
- Image gallery (via Immich thumbnails)
- Settings management
- Chrome profile integration for cookies

**Technology:**
- Electron 28+ (Chromium 120+)
- React 18+ or Svelte 4+ (decision pending)
- Mapbox GL JS or Leaflet for maps
- Supercluster for marker clustering
- IPC for Flask API communication

**Does NOT:**
- Store photos locally (Immich handles)
- Archive web pages (delegates to ArchiveBox)
- Run AI models (delegates to services)

### 5. Mobile App (Flutter) - Future

**Responsibilities:**
- GPS location capture in field
- Camera photo import
- Offline location catalog
- Stripped-down blog view
- WiFi-based sync to desktop

**Technology:**
- Flutter 3.16+ (Dart)
- SQLite (local subset of AUPAT database)
- flutter_map with MBTiles
- Background sync service

### 6. AI Services (Modular)

**Responsibilities:**
- Address extraction from images (OCR + LLM)
- Image tagging (supplementary to Immich)
- Historical text summarization (future)
- Blog post generation (future)

**Technology:**
- Ollama for LLM (llama3.2, mistral)
- Florence-2 or CLIP for image tagging
- Tesseract for OCR
- Custom Python pipeline

**Ports:** 11434 (Ollama), varies for others

## Data Flow Diagrams

### Import Flow: Desktop Drag-and-Drop Photos

```
User drags folder of 1000 photos into Desktop App
                    │
                    ▼
Desktop App: Shows import dialog, selects location
                    │
                    ▼
Desktop App → AUPAT Core API: POST /import/images
  {
    location_uuid: "...",
    file_paths: ["/path/to/img1.jpg", ...],
    import_to_immich: true
  }
                    │
                    ▼
AUPAT Core: For each image:
  1. Calculate SHA256
  2. Extract EXIF (timestamps, GPS, camera)
  3. Check if duplicate (SHA256 exists)
  4. Upload to Immich → get asset_id
  5. Insert to database:
     images(img_sha256, immich_asset_id, loc_uuid, ...)
  6. Extract GPS → update location if missing
                    │
                    ▼
Immich: Generates thumbnails, runs CLIP tagging
                    │
                    ▼
AUPAT Core → Desktop App: Import complete
  {
    imported: 987,
    duplicates: 13,
    failed: 0,
    gps_extracted: 45
  }
                    │
                    ▼
Desktop App: Refreshes location view, shows new photos
```

### Archive Flow: Web Archiving with Media Extraction

```
User browses Instagram post in Desktop App embedded browser
                    │
                    ▼
User clicks "Archive to Location"
                    │
                    ▼
Desktop App → AUPAT Core API: POST /locations/{uuid}/archive
  {
    url: "https://instagram.com/p/xyz",
    high_res_mode: true,
    chrome_cookies: true
  }
                    │
                    ▼
AUPAT Core → ArchiveBox API: POST /api/add
  {
    url: "...",
    plugins: ["playwright_instagram_extractor"]
  }
                    │
                    ▼
ArchiveBox:
  1. Archives page (WARC + screenshot)
  2. Runs Playwright plugin:
     - Loads Chrome cookies for login
     - Navigates to post
     - Finds carousel images
     - Extracts highest-resolution variants
  3. Saves extracted media to /data/archivebox/media/
  4. Sends webhook to AUPAT Core
                    │
                    ▼
AUPAT Core (webhook handler):
  1. Receives list of extracted media files
  2. For each file:
     - Calculate SHA256
     - Upload to Immich → get asset_id
     - Insert to images table with source_url
  3. Update urls table with archive_status = 'completed'
                    │
                    ▼
Desktop App (polling or websocket):
  Shows notification: "Archived! 5 images added to location."
```

### Map View Flow: Loading 200k Locations

```
User opens Desktop App → Map View
                    │
                    ▼
Desktop App → AUPAT Core API: GET /map/markers
                    │
                    ▼
AUPAT Core: SELECT loc_uuid, lat, lon, loc_name FROM locations WHERE lat IS NOT NULL
  Returns JSON array of ~200k points
                    │
                    ▼
Desktop App (client-side):
  1. Load all markers into Supercluster
  2. Supercluster creates hierarchical index
  3. Map renders visible clusters only (e.g., 500 clusters at zoom 5)
  4. User zooms in → Supercluster recalculates → shows more detail
  5. User clicks marker → Fetch location details
                    │
                    ▼
Desktop App → AUPAT Core API: GET /locations/{uuid}
                    │
                    ▼
AUPAT Core: Returns location metadata + list of image references
  {
    loc_uuid: "...",
    loc_name: "Abandoned Factory A",
    images: [
      {img_sha256: "abc123...", immich_asset_id: "xyz..."},
      ...
    ]
  }
                    │
                    ▼
Desktop App: Renders sidebar with location details
  - Fetches thumbnails from Immich: GET /api/asset/{id}/thumbnail
  - Displays gallery of photos
  - Shows archived URLs
```

### Mobile Sync Flow (Future)

```
User adds new location on mobile in field (no WiFi)
                    │
                    ▼
Mobile App: Saves to local SQLite
  locations_pending_sync(loc_uuid, lat, lon, photos, timestamp)
                    │
                    ▼
User arrives home, connects to WiFi
                    │
                    ▼
Mobile App (background sync service):
  Detects WiFi + AUPAT API reachable
                    │
                    ▼
Mobile App → AUPAT Core API: POST /sync/mobile
  {
    device_id: "...",
    new_locations: [...],
    new_photos: [...],
    updates: [...]
  }
                    │
                    ▼
AUPAT Core:
  1. Conflict detection (check if loc_uuid exists)
  2. Merge strategy: Mobile GPS always wins for new locations
  3. Insert to database
  4. Upload photos to Immich
  5. Return sync receipt
                    │
                    ▼
Mobile App:
  - Marks items as synced
  - Downloads new locations from desktop
  - Updates local SQLite
```

## Failure-Mode Expectations

### Immich Service Down
- Desktop app shows error: "Photo service unavailable"
- Can still view location metadata and map
- Cannot view photos or import new photos
- Queue imports to retry when service restored

### ArchiveBox Service Down
- Desktop app shows error: "Archive service unavailable"
- Can still browse and view locations
- Archive requests queued or fail gracefully
- User can retry manually

### SQLite Database Corruption
- WAL mode prevents most corruption scenarios
- Automated backups every 24 hours (git commits)
- Restore from backup procedure documented
- Database integrity check on startup

### Disk Full
- Health check monitors disk usage
- Alerts at 80% capacity
- Graceful degradation: Disable imports, archiving
- Admin can prune old archives or move data

### Network Partition (Docker Services)
- Each service has health checks
- Docker restart policies (restart: unless-stopped)
- Services can run degraded (e.g., Immich without ML)
- User sees which services are unhealthy

### GPU Unavailable for ML
- Immich ML falls back to CPU (slower but works)
- Can disable ML entirely in settings
- Desktop app shows "AI tagging disabled"

## Long-Term Operational Considerations

### Backup Strategy
- Automated daily SQLite backups (rsync + git commit)
- Immich photos backed up separately (content-addressed, easy to rsync)
- ArchiveBox archives backed up weekly (large, low-priority)
- Disaster recovery tested quarterly

### Update Strategy
- Pin Docker image versions (no :latest tags)
- Test updates in staging environment first
- Database migrations via Alembic (versioned)
- Rollback plan for each update

### Monitoring
- Docker health checks for all services
- Prometheus + Grafana for metrics (optional, future)
- Log aggregation to single location
- Disk usage alerts

### Performance Targets
- Map load (200k markers): < 3 seconds
- Photo gallery (100 thumbnails): < 2 seconds
- Import 1000 photos: < 10 minutes
- Archive 1 URL with media extraction: < 60 seconds
- Database query (search): < 1 second

### Scalability Limits
- SQLite: 140 TB max database size (not a concern)
- Immich: Tested with 500k+ photos (exceeds our needs)
- ArchiveBox: Disk-limited (each archive ~10-50 MB)
- Desktop app: Electron memory ~500 MB baseline + maps

## Simplicity Constraints

### No Microservice Orchestration (Kubernetes)
- Use Docker Compose only
- Single-host deployment
- Easier to debug and maintain

### No Message Queues (Kafka, RabbitMQ)
- Use simple HTTP webhooks
- Polling for status checks
- Acceptable latency for single-user system

### No Distributed Database
- Single SQLite file
- No sharding or replication complexity
- Backups handle disaster recovery

### No Custom Photo Storage
- Use Immich entirely (don't build parallel system)
- Trust their content-addressing and deduplication
- Reduces maintenance burden

### No Real-Time Sync
- Mobile sync is WiFi-triggered batch process
- No websockets or push notifications required
- Simpler architecture, adequate for use case

### No User Authentication (v0.1.2)
- Single-user system behind Cloudflare tunnel
- Authentication in future multi-user version
- Reduces initial complexity
