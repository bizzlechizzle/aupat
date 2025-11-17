# AUPATOOL v0.1.2 - Core Modules Deep Breakdown

## Module 1: AUPAT Core API (Flask + SQLite)

### Purpose
Authoritative source of truth for location-centric organization. Orchestrates all other services without duplicating their functionality.

### Inputs
- REST API requests (JSON)
- File paths for import
- Webhook callbacks from ArchiveBox
- Mobile sync payloads (future)

### Outputs
- JSON API responses
- Database writes to SQLite
- API calls to Immich/ArchiveBox
- Import status updates

### Exact Responsibilities
1. Location entity management (CRUD)
2. Sub-location and relationship tracking
3. Cross-referencing: loc_uuid → immich_asset_ids
4. Import pipeline orchestration (not file handling)
5. GPS coordinate aggregation from multiple sources
6. Search and filter queries
7. Mobile sync conflict resolution (future)

### Tech Stack Justification

**Flask 3.x**
- FAANG PE: Production-ready, used by Netflix, Airbnb
- BPA: Industry standard for Python REST APIs
- KISS: Simple request/response model, no ORM overhead
- BPL: Stable API since 2010, minimal breaking changes

**SQLite 3.40+ with WAL Mode**
- FAANG PE: Used by Airbnb internally, browsers, mobile apps
- BPL: SQLite is public domain, guaranteed stable forever
- KISS: Single file, no server process, no configuration
- Performance: 50k reads/sec, 10k writes/sec (sufficient)
- WAL mode: Concurrent reads during writes, crash-safe

**Python 3.11+**
- BPA: LTS version with performance improvements
- Ecosystem: Rich libraries for EXIF, hashing, web scraping
- GPU: Compatible with CUDA for future ML integration

**No ORM (Direct SQL)**
- KISS: No abstraction layer overhead
- Performance: Direct control over queries
- BPL: SQL is stable; ORMs change frequently

### Data Structures / Schemas

**Enhanced Schema (adds to existing)**

```sql
-- GPS coordinates (multiple sources)
ALTER TABLE locations ADD COLUMN lat REAL;
ALTER TABLE locations ADD COLUMN lon REAL;
ALTER TABLE locations ADD COLUMN gps_source TEXT; -- 'exif', 'manual', 'mobile', 'google_maps'
ALTER TABLE locations ADD COLUMN gps_confidence REAL; -- 0.0-1.0 (for AI-extracted)

-- Address extraction
ALTER TABLE locations ADD COLUMN street_address TEXT;
ALTER TABLE locations ADD COLUMN city TEXT;
ALTER TABLE locations ADD COLUMN state TEXT;
ALTER TABLE locations ADD COLUMN zip_code TEXT;
ALTER TABLE locations ADD COLUMN country TEXT DEFAULT 'USA';
ALTER TABLE locations ADD COLUMN address_source TEXT; -- 'manual', 'exif', 'ai_ocr', 'google_maps'

-- Immich integration
ALTER TABLE images ADD COLUMN immich_asset_id TEXT UNIQUE;
ALTER TABLE videos ADD COLUMN immich_asset_id TEXT UNIQUE;

-- ArchiveBox integration
ALTER TABLE urls ADD COLUMN archivebox_snapshot_id TEXT;
ALTER TABLE urls ADD COLUMN archive_status TEXT DEFAULT 'pending'; -- 'pending', 'archived', 'failed'
ALTER TABLE urls ADD COLUMN archive_date TEXT;
ALTER TABLE urls ADD COLUMN media_extracted INTEGER DEFAULT 0; -- count

-- Enhanced metadata
ALTER TABLE images ADD COLUMN img_width INTEGER;
ALTER TABLE images ADD COLUMN img_height INTEGER;
ALTER TABLE images ADD COLUMN img_size_bytes INTEGER;
ALTER TABLE images ADD COLUMN gps_lat REAL;
ALTER TABLE images ADD COLUMN gps_lon REAL;

ALTER TABLE videos ADD COLUMN vid_width INTEGER;
ALTER TABLE videos ADD COLUMN vid_height INTEGER;
ALTER TABLE videos ADD COLUMN vid_duration_sec REAL;
ALTER TABLE videos ADD COLUMN vid_size_bytes INTEGER;
ALTER TABLE videos ADD COLUMN gps_lat REAL;
ALTER TABLE videos ADD COLUMN gps_lon REAL;

-- Google Maps export tracking
CREATE TABLE IF NOT EXISTS google_maps_exports (
  export_id TEXT PRIMARY KEY,
  import_date TEXT NOT NULL,
  file_path TEXT NOT NULL,
  locations_found INTEGER DEFAULT 0,
  addresses_extracted INTEGER DEFAULT 0,
  images_processed INTEGER DEFAULT 0
);

-- Sync tracking (future)
CREATE TABLE IF NOT EXISTS sync_log (
  sync_id TEXT PRIMARY KEY,
  device_id TEXT,
  sync_type TEXT, -- 'mobile_to_desktop', 'desktop_to_mobile'
  timestamp TEXT,
  items_synced INTEGER,
  conflicts INTEGER,
  status TEXT -- 'success', 'partial', 'failed'
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_locations_gps ON locations(lat, lon) WHERE lat IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_images_immich ON images(immich_asset_id) WHERE immich_asset_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_images_location ON images(loc_uuid);
CREATE INDEX IF NOT EXISTS idx_images_gps ON images(gps_lat, gps_lon) WHERE gps_lat IS NOT NULL;
```

**API Endpoint Definitions**

```python
# /api/locations
GET    /api/locations                    # List all locations (paginated)
POST   /api/locations                    # Create new location
GET    /api/locations/{uuid}             # Get location details
PUT    /api/locations/{uuid}             # Update location
DELETE /api/locations/{uuid}             # Soft delete (future)

# /api/locations/{uuid}/media
GET    /api/locations/{uuid}/images      # Returns [{img_sha256, immich_asset_id, ...}]
GET    /api/locations/{uuid}/videos      # Returns [{vid_sha256, immich_asset_id, ...}]
GET    /api/locations/{uuid}/documents   # Returns document list

# /api/locations/{uuid}/archive
GET    /api/locations/{uuid}/archives    # List archived URLs
POST   /api/locations/{uuid}/archive     # Archive new URL

# /api/import
POST   /api/import/images                # Import images to location
POST   /api/import/videos                # Import videos to location
POST   /api/import/documents             # Import documents
POST   /api/import/google-maps           # Process Google Maps export
GET    /api/import/status/{job_id}       # Check import job status

# /api/map
GET    /api/map/markers                  # All locations with GPS (for clustering)
GET    /api/map/bounds                   # Bounding box stats

# /api/search
GET    /api/search?q={query}             # Full-text search
GET    /api/search/nearby?lat={}&lon={}  # Find nearby locations

# /api/sync (future)
POST   /api/sync/mobile                  # Mobile device sync

# /api/health
GET    /api/health                       # Health check
GET    /api/health/services              # Check Immich, ArchiveBox status
```

### Success Metrics
- Import 1000 images in < 10 minutes
- Search query returns in < 1 second
- Map endpoint returns 200k locations in < 2 seconds
- Zero data loss during 30-day stability test
- Database size < 500 MB for 200k images (metadata only)

### Security / Integrity Considerations
- Input validation: Reject malformed UUIDs, SQL injection prevention
- File path sanitization: Prevent directory traversal
- SHA256 verification: Detect file corruption
- WAL mode: Crash recovery without data loss
- No authentication in v0.1.2 (single-user, localhost only)
- Cloudflare tunnel handles TLS for remote access

### Long-Term Maintenance Risks
- SQLite concurrent write limits (mitigated by WAL + single desktop writer)
- Schema migrations complexity (use Alembic for versioned migrations)
- Flask security updates (pin versions, update quarterly)
- Python version upgrades (test thoroughly, pin in Docker)

### Alternatives via DRETW

**PostgREST + PostgreSQL**
- Pros: Auto-generates REST API from schema, supports multi-user
- Cons: Overkill for single-user, adds PostgreSQL dependency
- Verdict: SQLite is simpler, adequate for scale

**Hasura + PostgreSQL**
- Pros: GraphQL API, real-time subscriptions, powerful queries
- Cons: Complexity overhead, requires PostgreSQL
- Verdict: Too complex for our needs

**Django REST Framework**
- Pros: Batteries-included, admin interface, ORM
- Cons: Heavier than Flask, ORM abstraction we don't need
- Verdict: Flask is lighter, more control

**FastAPI**
- Pros: Modern async, automatic OpenAPI docs, type hints
- Cons: Async complexity not needed for single-user
- Verdict: Flask is proven, simpler for this use case

**Existing Codebase**
- We already have Flask app (web_interface.py) and all scripts
- 90% complete: db_import.py, db_organize.py, db_export.py
- DRETW wins here: Build on existing code, don't rewrite

### WWYDD
I would keep Flask + SQLite exactly as planned. The existing codebase is solid, and these technologies are battle-tested for this scale. The only enhancement I'd suggest: Add API versioning (e.g., /api/v1/...) from day one to enable backward compatibility during future updates.

---

## Module 2: Immich (Photo Storage & AI)

### Purpose
Handle all photo/video storage, thumbnail generation, AI tagging, and mobile sync. AUPAT treats Immich as the source of truth for media files.

### Inputs
- Photos/videos uploaded via API
- EXIF metadata extracted by Immich
- User tags and albums (future)

### Outputs
- Thumbnails (multiple sizes: 250px, 720px, 1080px)
- AI tags from CLIP model
- Asset IDs (UUIDs) for AUPAT to reference
- Streaming video transcodes

### Exact Responsibilities
1. Store photos/videos in content-addressed filesystem
2. Generate thumbnails on upload
3. Extract EXIF metadata (GPS, timestamps, camera)
4. Run CLIP AI tagging (categories, objects, scenes)
5. Provide API for thumbnail/original retrieval
6. Handle mobile app photo sync (iOS/Android)
7. Facial recognition (optional, can disable)
8. Album and timeline organization (AUPAT can ignore)

### Tech Stack Justification

**Immich v1.91+ (Latest Stable)**
- DRETW: Mature open-source project, 100k+ photos tested
- FAANG PE: Microservices architecture (server, ML, DB separate)
- BPA: Active development, follows photo storage best practices
- BPL: TypeScript + Python stack, standard technologies
- Community: 20k+ GitHub stars, active Discord support

**PostgreSQL (Immich Requirement)**
- Immich's chosen database for relational data
- Handles EXIF, tags, user data, relationships
- pgvecto-rs extension for vector similarity (CLIP embeddings)

**CLIP ML Model**
- OpenAI open-source vision model
- GPU-accelerated (runs on 3090)
- Can fall back to CPU if GPU unavailable

**Why Not Build Custom?**
- Immich solves: Storage, thumbnails, EXIF, AI, mobile apps
- Building from scratch: 6-12 months development
- DRETW strongly favors using Immich

### Data Structures / Schemas

Immich manages its own PostgreSQL schema. AUPAT only stores:

```sql
-- In AUPAT database
images(
  img_sha256 TEXT PRIMARY KEY,        -- AUPAT's identifier
  immich_asset_id TEXT UNIQUE,        -- Immich's identifier
  loc_uuid TEXT,                      -- Link to location
  ...
)
```

Relationship: SHA256 (AUPAT) ↔ asset_id (Immich)

This dual-key strategy allows:
- AUPAT to track files by content hash (deduplication)
- Immich to manage files by its own ID system
- Migration away from Immich if needed (SHA256 is portable)

### Success Metrics
- Upload 1000 photos in < 5 minutes
- Thumbnail generation completes in < 30 seconds
- CLIP tagging processes 1000 images in < 15 minutes (GPU)
- Mobile app syncs 100 photos in < 2 minutes on WiFi
- Gallery loads 100 thumbnails in < 2 seconds
- Zero photo loss during 30-day test

### Security / Integrity Considerations
- API key authentication for AUPAT uploads
- Content-addressed storage prevents tampering
- PostgreSQL backups separate from AUPAT backups
- No public internet exposure (Docker internal network + Cloudflare tunnel)

### Long-Term Maintenance Risks
- Immich API changes: Pin to stable release, abstract API calls behind adapter
- GPU driver compatibility: CUDA version must match Immich ML container
- PostgreSQL upgrades: Test before applying
- Disk space: Photos accumulate; monitor and alert at 80% capacity

### Alternatives via DRETW

**PhotoPrism**
- Pros: Similar feature set, nice UI, TensorFlow AI
- Cons: Slower AI tagging, less active development
- Verdict: Immich is faster and more actively maintained

**Piwigo**
- Pros: Mature (20+ years), plugin ecosystem
- Cons: PHP-based, no AI tagging, dated architecture
- Verdict: Too old-school for modern needs

**Custom S3 + Thumbor**
- Pros: Complete control, cloud-scalable
- Cons: Must build: AI, EXIF extraction, mobile apps, UI
- Verdict: Massive development effort, violates DRETW

**LibrePhotos**
- Pros: Open source, AI-powered, face recognition
- Cons: Less polished than Immich, smaller community
- Verdict: Immich has better momentum and features

**Photoprism + Immich Comparison**
- Immich wins on: Speed, AI quality, mobile apps, active development
- PhotoPrism wins on: Stability (older project)
- For BPL, Immich's active development is actually better (bugs get fixed)

### WWYDD
I would use Immich exactly as planned with one addition: Create an adapter layer in AUPAT Core that abstracts all Immich API calls. This makes it easier to swap photo backends in the future if Immich dies or better alternatives emerge.

```python
# aupat_core/adapters/photo_storage.py
class PhotoStorageAdapter:
    """Abstract interface for photo storage backends"""
    def upload(self, file_path: str) -> str:
        """Returns asset_id"""
        pass

    def get_thumbnail_url(self, asset_id: str, size: str) -> str:
        pass

    def get_original_url(self, asset_id: str) -> str:
        pass

class ImmichAdapter(PhotoStorageAdapter):
    """Immich-specific implementation"""
    def upload(self, file_path: str) -> str:
        response = requests.post(f"{IMMICH_URL}/api/upload", ...)
        return response.json()["id"]
    # ... etc

# If Immich dies in 2030, write S3Adapter(PhotoStorageAdapter) and swap
```

---

## Module 3: ArchiveBox (Web Archiving)

### Purpose
Preserve web pages, extract media, and create archival records of online research for abandoned places.

### Inputs
- URLs from desktop app
- Chrome cookies for authenticated sites
- Extraction instructions (high-res mode, etc.)

### Outputs
- WARC archives (web archive format)
- Screenshots (PNG)
- Extracted images/videos
- HTML snapshots
- PDF exports

### Exact Responsibilities
1. Archive entire web pages (HTML + resources)
2. Capture screenshots for visual reference
3. Extract media using site-specific logic
4. Download YouTube videos (yt-dlp built-in)
5. Store archives in organized filesystem structure
6. Provide API for archive status and retrieval
7. Run Playwright plugins for complex extractions

### Tech Stack Justification

**ArchiveBox v0.7+**
- DRETW: Mature web archiving solution, used by Internet Archive
- BPA: Follows WARC standards (ISO 28500)
- FAANG PE: Modular architecture, plugin system
- BPL: Python-based, well-maintained, 17k+ GitHub stars
- Ecosystem: Integrates wget, yt-dlp, Chromium, Playwright

**WARC Format**
- ISO standard for web archiving
- Used by Internet Archive, Library of Congress
- Future-proof: Will be readable in 50+ years

**Playwright Integration**
- Handles JavaScript-heavy sites
- Can use Chrome cookies for authenticated sessions
- Headless Chromium for automation

**yt-dlp**
- Successor to youtube-dl
- Downloads videos from 1000+ sites
- Actively maintained

### Data Structures / Schemas

ArchiveBox uses its own SQLite database for archive metadata. AUPAT links via:

```sql
-- In AUPAT database
urls(
  url_uuid TEXT PRIMARY KEY,
  loc_uuid TEXT,                        -- Link to location
  url TEXT,
  archivebox_snapshot_id TEXT,          -- ArchiveBox's identifier
  archive_status TEXT,                  -- 'pending', 'archived', 'failed'
  archive_date TEXT,
  media_extracted INTEGER DEFAULT 0,
  FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
)
```

Workflow:
1. AUPAT adds URL to database (status='pending')
2. AUPAT calls ArchiveBox API to archive
3. ArchiveBox returns snapshot_id
4. AUPAT updates: archivebox_snapshot_id, status='archived'
5. ArchiveBox webhook notifies of extracted media
6. AUPAT uploads media to Immich, updates media_extracted count

### Success Metrics
- Archive simple page (no media) in < 30 seconds
- Archive complex page (Instagram carousel) in < 2 minutes
- Extract 10 high-res images in < 3 minutes
- YouTube video download in < time-to-download (varies by size)
- Zero corruption of WARC files
- Successfully handle 1000+ archived URLs

### Security / Integrity Considerations
- Chrome cookie sharing: Read-only access to Chrome profile
- Sandbox Playwright: Prevent malicious JS execution
- Disk space monitoring: WARC files can be large (50 MB - 1 GB each)
- URL validation: Prevent archiving of malicious sites

### Long-Term Maintenance Risks
- ArchiveBox updates: API changes (pin version, abstract calls)
- WARC file format changes: Unlikely (ISO standard)
- Disk space: Archives accumulate; implement pruning strategy
- Website changes: Site-specific extractors break (Instagram, Facebook)
  - Mitigation: Playwright plugins are maintainable code

### Alternatives via DRETW

**Wget (--warc)**
- Pros: Simple, lightweight, built into Linux
- Cons: No JavaScript rendering, no complex extraction
- Verdict: Good for simple sites, not enough for Instagram/Facebook

**Heritrix**
- Pros: Used by Internet Archive, industrial-scale crawling
- Cons: Java-based, complex configuration, overkill for single-user
- Verdict: Too heavy for our needs

**Browsertrix Crawler**
- Pros: Modern, headless Chrome-based, WARC output
- Cons: Newer project, less mature than ArchiveBox
- Verdict: Good alternative, but ArchiveBox is more established

**SingleFile (Browser Extension)**
- Pros: Simple, captures page as single HTML file
- Cons: Manual process, no automation, not WARC format
- Verdict: Not suitable for programmatic archiving

**HTTrack**
- Pros: Mature, mirrors entire websites
- Cons: No WARC format, no JavaScript rendering
- Verdict: Outdated for modern web

**Custom Playwright + Wget**
- Pros: Full control, minimal dependencies
- Cons: Must implement: Screenshot, WARC creation, media extraction, yt-dlp integration
- Verdict: Violates DRETW; ArchiveBox does all this

### WWYDD
Use ArchiveBox as planned, but implement a plugin architecture for site-specific extractors:

```python
# archivebox-plugins/extractors/instagram.py
from playwright.sync_api import sync_playwright

def extract_instagram_high_res(url: str, cookies_path: str) -> list:
    """Extract highest-resolution images from Instagram post"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        context.add_cookies(load_cookies(cookies_path))
        page = context.new_page()
        page.goto(url)

        # Wait for carousel
        page.wait_for_selector('div[role="presentation"]')

        # Find all image elements
        images = page.query_selector_all('img[srcset]')

        high_res_urls = []
        for img in images:
            srcset = img.get_attribute('srcset')
            # Parse srcset, find highest resolution
            urls = parse_srcset(srcset)
            high_res_urls.append(max(urls, key=lambda x: x['width']))

        return high_res_urls

# Register plugin with ArchiveBox
ArchiveBox.register_extractor('instagram.com', extract_instagram_high_res)
```

This approach:
- Keeps site-specific logic maintainable
- Easy to update when sites change
- Can share plugins with community
- Doesn't require forking ArchiveBox

---

## Module 4: Desktop App (Electron)

### Purpose
Primary user interface for power-user workflows: bulk imports, web archiving, map visualization, and location management.

### Inputs
- User interactions (clicks, drag-and-drop)
- File system access (folders of photos)
- Chrome profile for cookies
- REST API responses from AUPAT Core

### Outputs
- Visual UI (map, galleries, forms)
- API calls to AUPAT Core
- Embedded browser for archiving
- Settings persistence

### Exact Responsibilities
1. Map view with 200k location markers (clustered)
2. Image gallery using Immich thumbnails
3. Location CRUD interface
4. Embedded Chromium browser for web archiving
5. Bulk import interface (drag-and-drop folders)
6. Settings management (API endpoints, Chrome profile path)
7. Archive workflow (browse → click Archive → show status)

### Tech Stack Justification

**Electron 28+**
- FAANG PE: Used by Slack, VS Code, Figma, Discord
- BPA: Industry standard for cross-platform desktop apps
- KISS: Single codebase for Mac + Linux + Windows
- BPL: Chromium + Node.js are stable, long-term technologies
- Embedded browser: Chromium built-in (needed for archiving)

**React 18+ or Svelte 4+**
- Decision pending (prototype both)
- React: Larger ecosystem, more developers, Meta-backed
- Svelte: Smaller bundle, better performance, simpler syntax
- WWYDD: I'd choose Svelte for desktop app (performance > ecosystem)

**Mapbox GL JS**
- Pros: Vector tiles, smooth zoom, beautiful rendering, Supercluster works
- Cons: Costs money after 50k loads/month (free tier adequate for single-user)
- Alternative: Leaflet (free, raster tiles, slightly less smooth)
- WWYDD: Start with Leaflet (free, good enough), upgrade to Mapbox if needed

**Supercluster**
- Fast marker clustering (tested with 1M points)
- Works with both Mapbox GL JS and Leaflet
- No alternatives needed (best in class)

**IPC (Inter-Process Communication)**
- Electron's built-in IPC for main ↔ renderer communication
- Main process: Handles filesystem, API calls
- Renderer process: UI, map, gallery

### Data Structures / Schemas

Desktop app is stateless; all data lives in AUPAT Core. Local storage only for:

```json
// Electron user settings (localStorage)
{
  "api_url": "http://localhost:5000",
  "immich_url": "http://localhost:2283",
  "archivebox_url": "http://localhost:8001",
  "chrome_profile_path": "/Users/bryant/Library/Application Support/Google/Chrome/Default",
  "map_default_zoom": 8,
  "map_default_center": [42.8142, -73.9396], // Albany, NY
  "enable_high_res_extraction": true,
  "auto_extract_gps": true
}
```

### Success Metrics
- App launch in < 3 seconds
- Map loads 200k markers in < 3 seconds
- Clicking location shows details in < 500ms
- Gallery loads 100 thumbnails in < 2 seconds
- Embedded browser loads page in < 2 seconds
- Import 1000 photos: Shows progress, completes in < 10 minutes
- Memory usage < 1 GB with map + gallery open

### Security / Integrity Considerations
- Content Security Policy: Restrict inline scripts
- Sandbox renderer process: Prevent arbitrary code execution
- Chrome profile: Read-only access to cookies
- No remote code execution: All updates via standard app updates
- Local API only: No public internet API calls (via Cloudflare tunnel if needed)

### Long-Term Maintenance Risks
- Electron updates: Security patches required, test before updating
- Chromium vulnerabilities: Keep Electron updated for security
- Node.js breaking changes: Pin version, test upgrades
- Map API changes: Abstract map library behind interface
- Bundle size: Electron apps are large (~150 MB base)

### Alternatives via DRETW

**Tauri**
- Pros: Rust-based, smaller bundle (~15 MB), faster startup, uses system webview
- Cons: Newer project, smaller ecosystem, no embedded Chromium (can't control browser version)
- Verdict: Chromium is critical for archiving; need consistent browser

**Web App (PWA)**
- Pros: No install, works on all platforms
- Cons: Can't embed browser, limited filesystem access, no clustering for 200k markers
- Verdict: Not powerful enough for our needs

**Native Apps (Swift for Mac, GTK for Linux)**
- Pros: Best performance, native feel
- Cons: Separate codebases, 2-3x development time
- Verdict: Violates KISS; Electron is simpler

**NW.js**
- Pros: Similar to Electron, Node.js + Chromium
- Cons: Smaller community, less polished
- Verdict: Electron is more established

### WWYDD

Use Electron + Svelte with these architectural decisions:

1. **Svelte over React**: Smaller bundle, better performance, simpler code for desktop
2. **Leaflet over Mapbox**: Free, adequate for single-user, can upgrade later
3. **Module federation**: Split app into lazy-loaded modules (map, gallery, archive)
   - Map module loads only when user opens map view
   - Reduces initial memory footprint
4. **Virtual scrolling**: For image galleries (only render visible thumbnails)
5. **Web Workers**: Use for heavy computations (SHA256 hashing during import)

```
desktop-app/
├── src/
│   ├── main/           # Electron main process (Node.js)
│   │   ├── api/        # API client for AUPAT Core
│   │   ├── fs/         # Filesystem operations
│   │   └── ipc/        # IPC handlers
│   ├── renderer/       # Electron renderer (Svelte UI)
│   │   ├── routes/     # SvelteKit routes
│   │   │   ├── map/    # Map view
│   │   │   ├── gallery/# Gallery view
│   │   │   ├── archive/# Archive browser
│   │   │   └── settings/
│   │   ├── components/ # Reusable UI components
│   │   └── lib/        # Utilities
│   └── preload/        # Electron preload script
├── package.json
├── electron-builder.yml
└── README.md
```

---

## Module 5: Mobile App (Flutter) - Future Phase

### Purpose
Field tool for GPS location capture, offline catalog viewing, and photo import during exploration.

### Inputs
- Device GPS coordinates
- Camera photos
- User input (location names, notes)
- Sync data from AUPAT Core

### Outputs
- New locations with GPS
- Photos uploaded to Immich (via WiFi)
- Sync requests to AUPAT Core
- Offline database updates

### Exact Responsibilities
1. Capture device GPS when adding locations
2. Import photos from camera or gallery
3. Offline SQLite database (subset of AUPAT Core)
4. Map view with offline MBTiles
5. "Near Me" search using local database
6. WiFi-based sync to desktop (bidirectional)
7. Stripped blog post viewer (text only, no media)

### Tech Stack Justification

**Flutter 3.16+**
- FAANG PE: Used by Google (Google Pay, Google Ads apps)
- BPA: Cross-platform (iOS + Android + Desktop) from single codebase
- KISS: One language (Dart), one framework, compile to native
- BPL: Backed by Google, stable API, strong ecosystem
- Performance: Compiles to native ARM/x64 code (fast)

**SQLite (sqflite package)**
- Same database engine as desktop
- Offline-first: Works with zero connectivity
- Syncs to AUPAT Core when online

**flutter_map + MBTiles**
- Open-source map widget
- Supports offline MBTiles (raster or vector)
- Lightweight compared to Google Maps SDK

**Why Not Native (Swift/Kotlin)?**
- Separate codebases for iOS + Android
- 2x development time, 2x maintenance
- Flutter's single codebase is KISS win

**Why Not React Native?**
- Flutter has better offline support and SQLite integration
- Flutter performance is closer to native

### Data Structures / Schemas

Mobile app has stripped-down SQLite schema:

```sql
-- Subset of AUPAT database for offline use
CREATE TABLE locations_mobile (
  loc_uuid TEXT PRIMARY KEY,
  loc_name TEXT,
  lat REAL,
  lon REAL,
  loc_type TEXT,
  synced INTEGER DEFAULT 1  -- 0 = pending sync
);

CREATE TABLE locations_pending_sync (
  loc_uuid TEXT PRIMARY KEY,
  loc_name TEXT,
  lat REAL,
  lon REAL,
  photos TEXT,  -- JSON array of local file paths
  created_at TEXT
);

CREATE TABLE blog_posts_mobile (
  post_id TEXT PRIMARY KEY,
  loc_uuid TEXT,
  title TEXT,
  content_text TEXT,  -- Markdown, no embedded images
  published_at TEXT
);

-- Offline map tiles
-- Stored as MBTiles file (separate from SQLite)
```

### Success Metrics
- GPS capture accuracy: < 10 meter error
- Offline database size: < 10 MB for 1000 locations
- Map tiles for region: < 500 MB
- "Near Me" search: < 1 second
- Photo upload on WiFi: 100 photos in < 2 minutes
- Sync completes in < 30 seconds
- Works offline for 90% of field tasks

### Security / Integrity Considerations
- GPS spoofing detection: Verify location via photo EXIF
- Sync authentication: API key or OAuth (future)
- Local database encryption: Encrypt SQLite with SQLCipher (optional)
- Photo privacy: Photos stay on device until explicit WiFi sync

### Long-Term Maintenance Risks
- Flutter breaking changes: Major versions have breaking changes, pin version
- iOS/Android API changes: Permissions, background services
- MBTiles format changes: Unlikely (stable format)
- GPS API deprecation: Use platform-agnostic geolocator package

### Alternatives via DRETW

**PWA (Progressive Web App)**
- Pros: No app store, works on all platforms, web-based
- Cons: Limited GPS background access, no offline MBTiles, worse performance
- Verdict: Not powerful enough for field use

**Capacitor (Ionic)**
- Pros: Web technologies (HTML/CSS/JS), cross-platform
- Cons: Hybrid architecture, slower than native
- Verdict: Flutter is faster and better for offline

**Native Apps**
- Pros: Best performance, platform-specific features
- Cons: Separate codebases, 2x development time
- Verdict: Flutter is adequate, KISS wins

### WWYDD

Implement mobile app in Phase 5 (after desktop is stable). Use Flutter with offline-first architecture:

```dart
// Mobile app sync strategy
class SyncService {
  Future<void> syncToDesktop() async {
    // 1. Upload pending locations
    for (location in pendingLocations) {
      await aupatApi.createLocation(location);
      await uploadPhotosToImmich(location.photos);
      markAsSynced(location);
    }

    // 2. Download new locations from desktop
    final newLocations = await aupatApi.getLocationsSince(lastSyncTime);
    await localDb.insertLocations(newLocations);

    // 3. Download blog posts (text only)
    final posts = await aupatApi.getBlogPosts();
    await localDb.insertBlogPosts(posts);

    lastSyncTime = DateTime.now();
  }

  bool shouldSync() {
    // Only sync on WiFi and when charging (battery-friendly)
    return isOnWiFi() && (isCharging() || batteryLevel > 50);
  }
}
```

---

## Module 6: AI Services (Address Extraction & Future ML)

### Purpose
Extract structured data from images, videos, and documents using AI. Initially focused on address extraction from Google Maps exports and general photos.

### Inputs
- Images (JPEG, PNG)
- Videos (extract frames first)
- Google Maps export data (KML, JSON, or folder of screenshots)
- Text documents

### Outputs
- Extracted addresses (structured: street, city, state, zip)
- GPS coordinates (via geocoding)
- Confidence scores (0.0-1.0)
- Source attribution

### Exact Responsibilities
1. OCR: Extract text from images (signs, documents)
2. LLM: Parse extracted text to identify addresses
3. Geocoding: Convert addresses to GPS coordinates
4. Google Maps export processing: Extract location data from exports
5. Video frame extraction: Screenshot videos, OCR on frames (future)
6. Historical text summarization (future Phase 6)

### Tech Stack Justification

**Tesseract 5.x (OCR)**
- DRETW: Battle-tested, used everywhere
- BPA: Industry standard for open-source OCR
- BPL: 30+ years of development, stable API
- Performance: CPU-based, no GPU needed
- Accuracy: 90%+ on clear text

**PaddleOCR (Alternative)**
- Pros: Better accuracy than Tesseract (95%+), GPU-accelerated
- Cons: Larger model size, requires Python ML stack
- WWYDD: Use PaddleOCR if Tesseract accuracy insufficient

**Ollama + llama3.2 (LLM)**
- DRETW: Local LLM runtime, no API costs
- BPA: Supports all major open models (Llama, Mistral, etc.)
- KISS: Single binary, easy to install
- BPL: Stable API, active development
- GPU: Runs on 3090, falls back to CPU

**Why Local LLM vs OpenAI API?**
- Cost: OpenAI costs $0.01-0.03 per 1k tokens (adds up)
- Privacy: Local = no data leaves machine
- Reliability: No internet dependency
- BPL: Not locked into vendor pricing changes

**Geopy (Geocoding)**
- DRETW: Python library for geocoding
- Supports multiple backends: Nominatim (OSM), Google, Bing
- Free tier adequate for our volume

### Data Structures / Schemas

```sql
-- AI extraction results
CREATE TABLE ai_extractions (
  extraction_id TEXT PRIMARY KEY,
  img_sha256 TEXT,  -- or vid_sha256
  extraction_type TEXT,  -- 'address', 'date', 'caption'
  extracted_text TEXT,
  structured_data TEXT,  -- JSON: {"street": "123 Main St", "city": "Albany", ...}
  confidence REAL,  -- 0.0-1.0
  model_used TEXT,  -- 'tesseract+llama3.2', 'paddleocr+gpt4'
  created_at TEXT,
  FOREIGN KEY (img_sha256) REFERENCES images(img_sha256)
);

-- Google Maps export processing
CREATE TABLE google_maps_imports (
  import_id TEXT PRIMARY KEY,
  file_path TEXT,
  processed_at TEXT,
  locations_found INTEGER,
  addresses_extracted INTEGER,
  status TEXT  -- 'success', 'partial', 'failed'
);
```

### Success Metrics
- OCR accuracy: > 85% on clear signs
- Address extraction: > 90% precision (few false positives)
- Geocoding: < 5% failure rate
- Processing speed: 1 image in < 5 seconds (OCR + LLM)
- Google Maps export: 100 locations processed in < 5 minutes

### Security / Integrity Considerations
- Model weights: Verify checksums before loading (prevent tampering)
- LLM prompt injection: Sanitize extracted text before LLM processing
- API keys: Geocoding APIs require keys (store securely in env vars)
- Rate limiting: Respect geocoding API limits (Nominatim: 1 req/sec)

### Long-Term Maintenance Risks
- Tesseract updates: Rare, but test before updating
- LLM model changes: Models improve, reprocess old data?
- Geocoding API changes: Abstract behind interface for easy swapping
- Accuracy drift: Monitor confidence scores, retrain/update models

### Alternatives via DRETW

**Google Cloud Vision API (OCR)**
- Pros: Best accuracy (98%+), handles handwriting
- Cons: Costs $1.50 per 1000 images, internet dependency
- Verdict: Use Tesseract/PaddleOCR first, upgrade if needed

**OpenAI GPT-4 Vision**
- Pros: Can do OCR + address extraction in one step
- Cons: Expensive ($0.01 per image), internet dependency
- Verdict: Use for comparison/benchmarking only

**AWS Rekognition + Textract**
- Pros: Good accuracy, integrated with AWS
- Cons: Costs money, vendor lock-in
- Verdict: Local models preferred (BPL)

**EasyOCR**
- Pros: GPU-accelerated, 80+ languages, good accuracy
- Cons: Slower than Tesseract, larger model
- Verdict: Good alternative to PaddleOCR

**Custom ML Model Training**
- Pros: Perfect for our specific use case (abandoned place signs)
- Cons: Requires labeled training data, ML expertise, maintenance
- Verdict: Overkill for v0.1.2; use pre-trained models first

### WWYDD

Implement address extraction pipeline in Phase 2:

```python
# ai_services/address_extractor.py

class AddressExtractor:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')  # or Tesseract
        self.llm = Ollama(model='llama3.2')
        self.geocoder = Nominatim(user_agent='aupat')

    def extract_from_image(self, img_path: str) -> dict:
        # 1. OCR: Extract text
        ocr_result = self.ocr.ocr(img_path, cls=True)
        text = ' '.join([line[1][0] for line in ocr_result[0]])

        # 2. LLM: Parse address
        prompt = f"""Extract address from this text. Return JSON.
        Text: {text}

        Return format: {{"street": "...", "city": "...", "state": "...", "zip": "...", "confidence": 0.0-1.0}}
        If no address found, return {{"confidence": 0.0}}
        """

        response = self.llm.generate(prompt)
        address = json.loads(response)

        # 3. Geocode: Get GPS coordinates
        if address['confidence'] > 0.7:
            location = self.geocoder.geocode(f"{address['street']}, {address['city']}, {address['state']}")
            if location:
                address['lat'] = location.latitude
                address['lon'] = location.longitude

        return address

# Usage:
extractor = AddressExtractor()
result = extractor.extract_from_image('/path/to/sign.jpg')
# {"street": "123 Main St", "city": "Albany", "state": "NY", "zip": "12203", "lat": 42.65, "lon": -73.75, "confidence": 0.92}
```

**Google Maps Export Processing:**

```python
# ai_services/google_maps_processor.py

def process_google_maps_export(export_path: str) -> list:
    """
    Process Google Maps Takeout export.
    Supports: KML, JSON, or folder of location screenshots.
    """
    results = []

    # Case 1: KML file (Google Maps Timeline export)
    if export_path.endswith('.kml'):
        locations = parse_kml(export_path)
        for loc in locations:
            results.append({
                'name': loc['name'],
                'lat': loc['lat'],
                'lon': loc['lon'],
                'timestamp': loc['timestamp'],
                'source': 'google_maps_kml'
            })

    # Case 2: Folder of screenshots
    elif os.path.isdir(export_path):
        images = glob(f"{export_path}/**/*.jpg", recursive=True)
        extractor = AddressExtractor()
        for img in images:
            address = extractor.extract_from_image(img)
            if address['confidence'] > 0.7:
                results.append({
                    'name': address.get('name', 'Unknown'),
                    'address': address,
                    'lat': address.get('lat'),
                    'lon': address.get('lon'),
                    'source': 'google_maps_screenshot',
                    'source_image': img
                })

    return results

# Usage:
locations = process_google_maps_export('/path/to/Google Takeout/Maps/')
# Import to AUPAT database
for loc in locations:
    aupat_api.create_location(loc)
```

This approach:
- Handles multiple Google Maps export formats
- Extracts addresses from any image source
- Provides confidence scores for manual review
- Modular: Easy to swap OCR/LLM backends
- Local: No API costs, works offline
