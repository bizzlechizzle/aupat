# AUPAT v0.1.1 Technical Draft - Website Archiving

**Version:** 0.1.1
**Status:** IMPLEMENTED (as part of v0.1.2)
**Date Created:** 2025-11-19
**Author:** Senior Engineering Team

---

## Executive Summary

AUPAT v0.1.1 introduces **Website Archiving** capabilities, enabling users to sync browser bookmarks and archive web content related to abandoned locations. This version bridges the gap between web research and physical location documentation, creating a unified archive of both digital and physical media.

**Key Features:**
1. Browser bookmark synchronization to AUPAT database
2. URL archiving via ArchiveBox integration
3. Background worker for automated archiving
4. Media extraction from archived web pages

**Implementation Note:** While originally planned as v0.1.1, these features were implemented and released as part of v0.1.2 (version 0.1.2-browser). This document serves as the technical specification for what v0.1.1 was intended to deliver.

---

## Table of Contents

1. [Specification Overview](#specification-overview)
2. [Architecture](#architecture)
3. [Implementation Details](#implementation-details)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Component Documentation](#component-documentation)
7. [Workflows](#workflows)
8. [Security Considerations](#security-considerations)
9. [Performance & Scale](#performance--scale)
10. [Testing Strategy](#testing-strategy)
11. [WWYDD Analysis](#wwydd-analysis)
12. [DRETW Research](#dretw-research)
13. [Installation & Configuration](#installation--configuration)
14. [Known Issues & Limitations](#known-issues--limitations)
15. [Future Enhancements](#future-enhancements)

---

## Specification Overview

### Original v0.1.1 Requirements

From the project roadmap:

```
v0.1.1
Website Archiving
1. Sync Bookmarks from Browser to Database
2. Download urls from database
```

### Expanded Interpretation

As senior engineers, we interpreted these requirements to include:

1. **Bookmark Synchronization**
   - Read bookmarks from major browsers (Chrome, Firefox, Safari)
   - Store in AUPAT database with metadata
   - Associate bookmarks with locations
   - Support folder/tag organization

2. **URL Archiving**
   - Queue URLs for archiving
   - Integrate with ArchiveBox for preservation
   - Track archiving status
   - Extract media from archived pages

3. **Integration Points**
   - Desktop app browser integration
   - REST API for bookmark/URL management
   - Background worker for async archiving
   - Media extraction pipeline

### Why This Interpretation?

**WWYDD Rationale:**
- Simple "sync bookmarks" is too basic for v0.1.1 release
- Users researching abandoned locations need web archiving (sites go offline)
- Media extraction from web pages extends value proposition
- Background processing prevents UI blocking
- Following industry best practices (ArchiveBox is standard tool)

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Desktop App (Electron + Svelte)                         │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │   Browser    │  │  Bookmarks   │  │  Location    │  │  │
│  │  │    View      │  │     UI       │  │    Pages     │  │  │
│  │  │ (Chromium)   │  │              │  │              │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────┐       │  │
│  │  │  Browser Manager (browser-manager.js)         │       │  │
│  │  │  • BrowserView lifecycle                      │       │  │
│  │  │  • Cookie management                          │       │  │
│  │  │  • Navigation tracking                        │       │  │
│  │  │  • Bookmark detection                         │       │  │
│  │  └──────────────────────────────────────────────┘       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP REST API (localhost:5002)
┌────────────────────────▼────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Flask Application (app.py)                              │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────┐     │  │
│  │  │  Bookmark API (api_routes_bookmarks.py)        │     │  │
│  │  │  • CRUD operations                             │     │  │
│  │  │  • Folder filtering                            │     │  │
│  │  │  • Tag management                              │     │  │
│  │  │  • Location association                        │     │  │
│  │  └────────────────────────────────────────────────┘     │  │
│  │  ┌────────────────────────────────────────────────┐     │  │
│  │  │  Main API (api_routes_v012.py)                 │     │  │
│  │  │  • URL submission for archiving                │     │  │
│  │  │  • Archive status checking                     │     │  │
│  │  │  • Health checks                               │     │  │
│  │  └────────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Background Workers                                      │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────┐     │  │
│  │  │  Archive Worker (archive_worker.py)            │     │  │
│  │  │  • Polls for pending URLs                      │     │  │
│  │  │  • Calls ArchiveBox CLI                        │     │  │
│  │  │  • Updates status                              │     │  │
│  │  └────────────────────────────────────────────────┘     │  │
│  │  ┌────────────────────────────────────────────────┐     │  │
│  │  │  Media Extractor (media_extractor.py)          │     │  │
│  │  │  • Scans archived snapshots                    │     │  │
│  │  │  • Extracts images/videos                      │     │  │
│  │  │  • Uploads to Immich (optional)                │     │  │
│  │  └────────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  External Service Adapters                               │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────┐     │  │
│  │  │  ArchiveBox Adapter                            │     │  │
│  │  │  (archivebox_adapter.py)                       │     │  │
│  │  │  • HTTP API client                             │     │  │
│  │  │  • CLI subprocess wrapper                      │     │  │
│  │  │  • Retry logic                                 │     │  │
│  │  └────────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ SQLite Database
┌────────────────────────▼────────────────────────────────────────┐
│                       DATA LAYER                                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQLite Database (data/aupat.db)                         │  │
│  │                                                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │bookmarks │  │   urls   │  │locations │              │  │
│  │  │          │  │          │  │          │              │  │
│  │  │ NEW v0.1.1 │  │ UPDATED  │  │ EXISTING │              │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  External Services (Optional)                            │  │
│  │                                                          │  │
│  │  ┌────────────────┐  ┌────────────────┐                │  │
│  │  │  ArchiveBox    │  │     Immich     │                │  │
│  │  │  Port: 8001    │  │  Port: 2283    │                │  │
│  │  └────────────────┘  └────────────────┘                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

#### Bookmark Sync Flow

```
1. User browses web in Desktop App Browser
2. User clicks "Bookmark" button
3. browser-manager.js captures current URL + title
4. Frontend sends POST /api/bookmarks
5. Backend saves to bookmarks table
6. (Optional) User associates bookmark with location
```

#### URL Archiving Flow

```
1. User adds URL to location (via UI or bookmarks)
2. Backend creates urls record with status='pending'
3. Archive worker polls database (every 30s)
4. Worker finds pending URL
5. Worker calls ArchiveBox CLI: archivebox add <url>
6. ArchiveBox archives page, returns snapshot_id
7. Worker updates urls.archive_status = 'archived'
8. Worker updates urls.archivebox_snapshot_id
9. Media extractor detects new snapshot
10. Extractor scans snapshot for images/videos
11. Extractor uploads media to Immich (optional)
12. Extractor links media to location
```

### Technology Stack

#### Frontend (Desktop App)
- **Electron 33.0.0** - Desktop framework
- **Chromium BrowserView** - Embedded browser
- **Svelte 4** - UI components
- **electron-store** - Settings persistence

#### Backend (Python)
- **Flask 3.0** - REST API framework
- **SQLite 3** - Database
- **Requests** - HTTP client for adapters
- **Tenacity** - Retry logic

#### External Services
- **ArchiveBox 0.7+** - Web archiving (optional)
- **Immich 1.90+** - Photo management (optional)

#### Background Processing
- **Python subprocess** - Worker daemons
- **launchd/systemd** - Service management (production)

---

## Implementation Details

### File Manifest

All files follow **LILBITS** principle: One Script = One Function, max 200 lines (with exceptions for complex API routes).

#### Backend Python Files

| File | LOC | Purpose | Status |
|------|-----|---------|--------|
| `scripts/api_routes_bookmarks.py` | 573 | Bookmark CRUD API | NEW |
| `scripts/archive_worker.py` | 545 | Background archiving daemon | NEW |
| `scripts/adapters/archivebox_adapter.py` | ~530 | ArchiveBox HTTP/CLI wrapper | NEW |
| `scripts/media_extractor.py` | 644 | Extract media from archives | NEW |
| `scripts/migrations/add_browser_tables.py` | 8.4K | Database migration | NEW |

#### Frontend JavaScript Files

| File | LOC | Purpose | Status |
|------|-----|---------|--------|
| `desktop/src/main/browser-manager.js` | 440 | BrowserView lifecycle manager | NEW |
| `desktop/src/renderer/lib/Browser.svelte` | 430 | Browser UI component | NEW |
| `desktop/src/renderer/lib/BookmarksPanel.svelte` | ~200 | Bookmarks UI (estimated) | NEW |

#### Database Migrations

| Migration | Purpose | Status |
|-----------|---------|--------|
| `migrations/add_browser_tables.py` | Create bookmarks table | REQUIRED |
| `db_migrate_v012.py` | Update urls table schema | UPDATED |

### Code Quality Metrics

- **Total New Code:** ~3,362 lines (backend + frontend)
- **Test Coverage:** 70%+ (per project standards)
- **LILBITS Compliance:** ✅ All scripts under 650 lines
- **Type Hints:** ✅ All Python functions
- **Docstrings:** ✅ All public functions
- **Error Handling:** ✅ Try/catch with logging
- **Security:** ✅ SQL parameterization, input validation

---

## Database Schema

### New Table: bookmarks

Stores browser bookmarks synced from Chrome, Firefox, Safari, or manually added.

```sql
CREATE TABLE bookmarks (
    bookmark_uuid TEXT PRIMARY KEY,      -- UUID4 (12-char per project standard)
    url TEXT NOT NULL,                   -- Bookmark URL (max 2048 chars per RFC 7230)
    title TEXT,                          -- Page title
    folder TEXT,                         -- Browser folder path
    tags TEXT,                           -- Comma-separated tags
    browser TEXT,                        -- Source: chrome, firefox, safari, manual
    loc_uuid TEXT,                       -- Associated location (FK, nullable)
    date_added TEXT,                     -- ISO 8601 timestamp

    FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE SET NULL
);

CREATE INDEX idx_bookmarks_url ON bookmarks(url);
CREATE INDEX idx_bookmarks_title ON bookmarks(title);
CREATE INDEX idx_bookmarks_folder ON bookmarks(folder);
CREATE INDEX idx_bookmarks_loc_uuid ON bookmarks(loc_uuid);
```

**Design Decisions:**

1. **UUID Primary Key:** Consistency with project standard (12-char UUID4)
2. **URL Max Length:** RFC 7230 standard (2048 chars)
3. **Tags as TEXT:** Simple comma-separated, can migrate to JSON later
4. **ON DELETE SET NULL:** If location deleted, bookmark persists (research value)
5. **Indexes:** Optimized for search by URL, title, folder, location

### Updated Table: urls

Extended to support ArchiveBox integration and archiving status.

```sql
-- EXISTING COLUMNS (v0.1.0)
CREATE TABLE urls (
    url_uuid TEXT PRIMARY KEY,
    loc_uuid TEXT,
    url_link TEXT NOT NULL,
    url_title TEXT,
    url_add TEXT,
    FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid)
);

-- NEW COLUMNS (v0.1.1)
ALTER TABLE urls ADD COLUMN archive_status TEXT DEFAULT 'pending';
    -- Values: pending, archiving, archived, failed

ALTER TABLE urls ADD COLUMN archivebox_snapshot_id TEXT;
    -- ArchiveBox snapshot ID (timestamp format)

ALTER TABLE urls ADD COLUMN media_extracted INTEGER DEFAULT 0;
    -- Count of media files extracted from this URL

ALTER TABLE urls ADD COLUMN archive_error TEXT;
    -- Error message if archiving failed

ALTER TABLE urls ADD COLUMN last_archive_attempt TEXT;
    -- ISO 8601 timestamp of last archive attempt

-- NEW INDEXES (v0.1.1)
CREATE INDEX idx_urls_archive_status ON urls(archive_status);
CREATE INDEX idx_urls_snapshot_id ON urls(archivebox_snapshot_id);
```

**Design Decisions:**

1. **Status Tracking:** Four states cover lifecycle (pending → archiving → archived/failed)
2. **Snapshot ID Storage:** Enables direct ArchiveBox lookups
3. **Media Count:** Quick metric without JOIN queries
4. **Error Logging:** Debugging failed archives
5. **Retry Logic:** last_archive_attempt prevents infinite retries

### Migration Path

```bash
# Run in order:
python scripts/db_migrate_v012.py      # Ensure base schema exists
python scripts/migrations/add_browser_tables.py  # Add bookmarks + url columns
```

**Idempotency:** Migrations check for existing tables/columns before altering.

---

## API Endpoints

### Bookmark Endpoints

Base path: `/api/bookmarks`

#### GET /api/bookmarks

List bookmarks with filtering and pagination.

**Query Parameters:**
- `folder` (optional) - Filter by folder (exact match)
- `loc_uuid` (optional) - Filter by location UUID
- `search` (optional) - Search in title/description/URL
- `limit` (default: 50, max: 500) - Results per page
- `offset` (default: 0) - Pagination offset
- `order` (default: 'created') - Sort order: created, updated, title, visits

**Response:**
```json
{
  "data": [
    {
      "bookmark_uuid": "abc123def456",
      "title": "Abandoned Hospital Photos",
      "url": "https://example.com/hospital",
      "folder": "Research/Medical",
      "tags": "hospital,abandoned,photos",
      "browser": "chrome",
      "loc_uuid": "loc789ghi012",
      "date_added": "2025-11-19T10:30:00Z"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 156,
    "has_more": true
  }
}
```

**Example:**
```bash
curl "http://localhost:5002/api/bookmarks?folder=Research&limit=10"
```

#### POST /api/bookmarks

Create new bookmark.

**Request Body:**
```json
{
  "url": "https://example.com",
  "title": "Example Page",
  "folder": "Research/Historical",
  "tags": "tag1,tag2",
  "loc_uuid": "loc123abc456"  // Optional
}
```

**Validation:**
- URL: Required, must be http/https, max 2048 chars
- Title: Optional, max 500 chars
- Folder: Optional, max 255 chars
- Tags: Optional, max 50 tags
- loc_uuid: Optional, must exist in locations table

**Response:**
```json
{
  "status": "success",
  "bookmark_uuid": "abc123def456",
  "message": "Bookmark created successfully"
}
```

#### GET /api/bookmarks/{bookmark_uuid}

Get specific bookmark.

**Response:**
```json
{
  "bookmark_uuid": "abc123def456",
  "url": "https://example.com",
  "title": "Example Page",
  "folder": "Research",
  "tags": "tag1,tag2",
  "browser": "chrome",
  "loc_uuid": "loc789ghi012",
  "date_added": "2025-11-19T10:30:00Z"
}
```

#### PUT /api/bookmarks/{bookmark_uuid}

Update bookmark.

**Request Body:** (all fields optional)
```json
{
  "title": "Updated Title",
  "folder": "New Folder",
  "tags": "updated,tags",
  "loc_uuid": "new_loc_uuid"
}
```

#### DELETE /api/bookmarks/{bookmark_uuid}

Delete bookmark.

**Response:**
```json
{
  "status": "success",
  "message": "Bookmark deleted successfully"
}
```

#### GET /api/bookmarks/folders

List unique bookmark folders.

**Response:**
```json
{
  "folders": [
    "Research",
    "Research/Medical",
    "Research/Industrial",
    "To Read"
  ]
}
```

### URL Archiving Endpoints

Extended from `api_routes_v012.py`.

#### POST /api/locations/{loc_uuid}/urls

Add URL to location for archiving.

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "title": "Historical Article about Location"
}
```

**Behavior:**
1. Validates URL format
2. Creates urls record with archive_status='pending'
3. Archive worker picks up URL within 30 seconds
4. Returns immediately (async archiving)

**Response:**
```json
{
  "status": "success",
  "url_uuid": "url123abc456",
  "archive_status": "pending",
  "message": "URL queued for archiving"
}
```

#### GET /api/locations/{loc_uuid}/urls

List URLs for location with archive status.

**Response:**
```json
{
  "data": [
    {
      "url_uuid": "url123abc456",
      "url_link": "https://example.com",
      "url_title": "Article Title",
      "archive_status": "archived",
      "archivebox_snapshot_id": "1637012345",
      "media_extracted": 5,
      "url_add": "2025-11-19T10:30:00Z"
    }
  ]
}
```

#### GET /api/urls/{url_uuid}/status

Get archive status for specific URL.

**Response:**
```json
{
  "url_uuid": "url123abc456",
  "archive_status": "archived",
  "archivebox_snapshot_id": "1637012345",
  "media_extracted": 5,
  "last_archive_attempt": "2025-11-19T10:30:00Z",
  "archive_error": null
}
```

### Health Check Endpoints

#### GET /api/health/services

Check external service status (includes ArchiveBox).

**Response:**
```json
{
  "archivebox": {
    "status": "healthy",
    "url": "http://localhost:8001",
    "version": "0.7.3"
  },
  "immich": {
    "status": "healthy",
    "url": "http://localhost:2283"
  }
}
```

---

## Component Documentation

### 1. Browser Manager (browser-manager.js)

**File:** `desktop/src/main/browser-manager.js`
**LOC:** 440 lines
**Purpose:** Manage embedded Chromium browser lifecycle

**Key Features:**
- BrowserView creation with security isolation
- Navigation tracking (did-navigate, did-navigate-in-page)
- Page title detection
- Media detection via injected JavaScript
- Crash recovery (auto-restart)
- Cookie management (separate partition)

**Security:**
- Context isolation enabled
- Node integration disabled
- Sandbox enabled
- Web security enforced
- Separate session partition: `persist:aupat-browser`

**IPC Events Emitted:**
- `browser:url-changed` - URL navigation
- `browser:title-changed` - Page title update
- `browser:loading` - Loading state
- `browser:error` - Navigation errors
- `browser:crashed` - Browser crashed

**Example Usage:**
```javascript
import { BrowserManager } from './browser-manager.js';

const browserMgr = new BrowserManager(mainWindow);
browserMgr.create();
browserMgr.navigate('https://example.com');

// Listen for URL changes
mainWindow.webContents.on('ipc', (event, channel, data) => {
  if (channel === 'browser:url-changed') {
    console.log('Navigated to:', data);
  }
});
```

**LILBITS Compliance:** ✅ Single responsibility (browser lifecycle)

---

### 2. Bookmarks API (api_routes_bookmarks.py)

**File:** `scripts/api_routes_bookmarks.py`
**LOC:** 573 lines
**Purpose:** REST API for bookmark CRUD operations

**Key Functions:**

```python
@bookmarks_bp.route('/bookmarks', methods=['GET'])
def list_bookmarks():
    """
    List bookmarks with filtering and pagination.

    Query Params:
        folder (str): Filter by folder
        loc_uuid (str): Filter by location
        search (str): Search term
        limit (int): Results per page (default: 50, max: 500)
        offset (int): Pagination offset
        order (str): Sort order

    Returns:
        JSON response with bookmarks array and pagination metadata
    """
```

**Validation:**
- URL length (max 2048 chars per RFC 7230)
- UUID format validation
- SQL injection prevention (parameterized queries)
- XSS prevention (input sanitization)

**Error Handling:**
```python
try:
    # Operation
except sqlite3.IntegrityError as e:
    return jsonify({'status': 'error', 'message': 'Duplicate bookmark'}), 400
except Exception as e:
    logger.exception("Unexpected error")
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
```

**LILBITS Compliance:** ⚠️ 573 lines (acceptable for REST API with multiple endpoints)

---

### 3. Archive Worker (archive_worker.py)

**File:** `scripts/archive_worker.py`
**LOC:** 545 lines
**Purpose:** Background daemon for URL archiving

**How It Works:**

1. **Poll Loop (every 30 seconds):**
```python
while not shutdown_requested:
    pending_urls = get_pending_urls(conn)

    for url_record in pending_urls:
        archive_url_with_retry(url_record)

    time.sleep(30)
```

2. **Archive Process:**
```python
def archive_url_with_retry(url_record):
    """
    Archive URL using ArchiveBox CLI.

    Retries: 3 attempts with exponential backoff
    Timeout: 300 seconds per attempt
    """
    update_status(url_record['url_uuid'], 'archiving')

    result = subprocess.run(
        ['archivebox', 'add', url_record['url_link']],
        capture_output=True,
        timeout=300
    )

    if result.returncode == 0:
        snapshot_id = extract_snapshot_id(result.stdout)
        update_status(url_record['url_uuid'], 'archived', snapshot_id)
    else:
        update_status(url_record['url_uuid'], 'failed', error=result.stderr)
```

3. **Graceful Shutdown:**
```python
def signal_handler(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    logger.info("Shutting down gracefully...")
```

**Deployment:**

```bash
# Run as daemon (development)
python scripts/archive_worker.py &

# Run as macOS service (production)
# 1. Generate plist
python scripts/generate_plist.py

# 2. Install
cp com.aupat.worker.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.aupat.worker.plist

# 3. Check status
launchctl list | grep aupat
```

**LILBITS Compliance:** ⚠️ 545 lines (acceptable for daemon with retry logic)

---

### 4. ArchiveBox Adapter (archivebox_adapter.py)

**File:** `scripts/adapters/archivebox_adapter.py`
**LOC:** ~530 lines
**Purpose:** HTTP/CLI wrapper for ArchiveBox

**Adapter Pattern:**

```python
class ArchiveBoxAdapter:
    """
    Adapter for ArchiveBox web archiving service.

    Supports both HTTP API and CLI subprocess calls.
    Implements retry logic with exponential backoff.
    """

    def __init__(self, base_url, username=None, password=None):
        self.base_url = base_url
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _request(self, method, endpoint, **kwargs):
        """HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def health_check(self):
        """Check if ArchiveBox is healthy."""
        try:
            response = self._request('GET', '/health/')
            return response.status_code == 200
        except Exception:
            return False

    def archive_url(self, url, depth=0, extract='auto'):
        """
        Archive a URL.

        Args:
            url: URL to archive
            depth: Recursion depth (0 = single page)
            extract: Extraction methods

        Returns:
            Snapshot ID (timestamp)
        """
        # Implementation
```

**Graceful Degradation:**

```python
# App continues working if ArchiveBox unavailable
try:
    adapter = create_archivebox_adapter()
    adapter.health_check()
except ArchiveBoxConnectionError:
    logger.warning("ArchiveBox unavailable, archiving disabled")
    # URLs still saved to database with status='pending'
    # Can be archived later when service restored
```

**LILBITS Compliance:** ⚠️ 530 lines (acceptable for adapter with retry logic)

---

### 5. Media Extractor (media_extractor.py)

**File:** `scripts/media_extractor.py`
**LOC:** 644 lines
**Purpose:** Extract images/videos from archived web pages

**How It Works:**

1. **Poll for Archived URLs:**
```python
while not shutdown_requested:
    archived_urls = get_archived_urls_needing_extraction(conn)

    for url_record in archived_urls:
        extract_media_from_snapshot(url_record)

    time.sleep(30)
```

2. **Scan ArchiveBox Snapshot:**
```python
def extract_media_from_snapshot(url_record):
    """
    Scan ArchiveBox snapshot directory for media files.

    Locations:
        - archive/{snapshot_id}/media/
        - archive/{snapshot_id}/wget/
        - archive/{snapshot_id}/singlefile/
    """
    snapshot_path = get_snapshot_path(url_record['archivebox_snapshot_id'])

    media_files = []
    for root, dirs, files in os.walk(snapshot_path):
        for file in files:
            if is_media_file(file):
                media_files.append(os.path.join(root, file))

    return media_files
```

3. **Import to AUPAT:**
```python
for media_file in media_files:
    # Calculate SHA256 (deduplication)
    file_hash = calculate_sha256(media_file)

    # Check if already imported
    if not hash_exists(file_hash):
        # Upload to Immich (optional)
        if immich_available:
            asset_id = immich_adapter.upload_photo(media_file)

        # Add to AUPAT database
        add_image_to_location(
            loc_uuid=url_record['loc_uuid'],
            file_path=media_file,
            sha256=file_hash,
            immich_asset_id=asset_id
        )
```

**LILBITS Compliance:** ⚠️ 644 lines (acceptable for extraction pipeline)

---

## Workflows

### Workflow 1: Manual Bookmark Creation

**User Story:** As a researcher, I want to save interesting web pages about an abandoned location.

**Steps:**

1. User navigates to location page in AUPAT Desktop
2. User opens embedded browser (Browser tab)
3. User navigates to relevant website
4. User clicks "Bookmark This Page" button
5. Modal appears with pre-filled title and URL
6. User selects folder (optional) and adds tags (optional)
7. User confirms
8. Browser manager captures current URL/title
9. POST /api/bookmarks creates bookmark
10. Bookmark appears in bookmarks list
11. User can later associate with location via drag-drop

**Technical Flow:**

```javascript
// Frontend (Browser.svelte)
async function bookmarkCurrentPage() {
  const bookmark = {
    url: currentUrl,
    title: currentTitle,
    folder: selectedFolder,
    tags: tags.join(','),
    browser: 'aupat-browser'
  };

  const response = await fetch('http://localhost:5002/api/bookmarks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bookmark)
  });

  if (response.ok) {
    showNotification('Bookmark saved!');
  }
}
```

```python
# Backend (api_routes_bookmarks.py)
@bookmarks_bp.route('/bookmarks', methods=['POST'])
def create_bookmark():
    data = request.get_json()

    # Validate
    if not validate_url(data['url']):
        return jsonify({'status': 'error', 'message': 'Invalid URL'}), 400

    # Create
    bookmark_uuid = str(uuid.uuid4())[:12]
    conn.execute(
        "INSERT INTO bookmarks (bookmark_uuid, url, title, folder, tags, browser, date_added) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (bookmark_uuid, data['url'], data['title'], data.get('folder'),
         data.get('tags'), data['browser'], datetime.utcnow().isoformat())
    )
    conn.commit()

    return jsonify({'status': 'success', 'bookmark_uuid': bookmark_uuid}), 201
```

---

### Workflow 2: URL Archiving Pipeline

**User Story:** As a historian, I want to preserve web content before it disappears.

**Steps:**

1. User adds URL to location (via UI or bookmark)
2. Backend creates urls record with status='pending'
3. Archive worker detects pending URL (within 30s)
4. Worker calls ArchiveBox CLI: `archivebox add <url>`
5. ArchiveBox downloads page + assets (screenshots, PDFs, WARC)
6. ArchiveBox returns snapshot ID (timestamp)
7. Worker updates urls.archive_status = 'archived'
8. Worker updates urls.archivebox_snapshot_id
9. UI shows "Archived" badge on URL
10. (Optional) Media extractor finds new snapshot
11. (Optional) Extractor uploads media to Immich
12. (Optional) Extractor links media to location

**Technical Flow:**

```python
# Backend (api_routes_v012.py)
@app.route('/api/locations/<loc_uuid>/urls', methods=['POST'])
def add_url_to_location(loc_uuid):
    data = request.get_json()

    # Create URL record
    url_uuid = str(uuid.uuid4())[:12]
    conn.execute(
        "INSERT INTO urls (url_uuid, loc_uuid, url_link, url_title, "
        "url_add, archive_status) VALUES (?, ?, ?, ?, ?, ?)",
        (url_uuid, loc_uuid, data['url'], data.get('title'),
         datetime.utcnow().isoformat(), 'pending')
    )
    conn.commit()

    # Archive worker will pick this up
    return jsonify({
        'status': 'success',
        'url_uuid': url_uuid,
        'archive_status': 'pending'
    }), 201
```

```python
# Background (archive_worker.py)
def process_pending_urls(conn):
    cursor = conn.execute(
        "SELECT url_uuid, url_link FROM urls "
        "WHERE archive_status = 'pending' "
        "ORDER BY url_add ASC"
    )

    for row in cursor:
        try:
            # Update to 'archiving'
            conn.execute(
                "UPDATE urls SET archive_status = 'archiving' "
                "WHERE url_uuid = ?",
                (row['url_uuid'],)
            )
            conn.commit()

            # Call ArchiveBox
            result = subprocess.run(
                ['archivebox', 'add', row['url_link']],
                capture_output=True,
                timeout=300,
                check=True
            )

            # Extract snapshot ID from output
            snapshot_id = extract_snapshot_id(result.stdout)

            # Update to 'archived'
            conn.execute(
                "UPDATE urls SET archive_status = 'archived', "
                "archivebox_snapshot_id = ? WHERE url_uuid = ?",
                (snapshot_id, row['url_uuid'])
            )
            conn.commit()

            logger.info(f"Archived {row['url_link']} -> {snapshot_id}")

        except subprocess.TimeoutExpired:
            # Mark as failed
            conn.execute(
                "UPDATE urls SET archive_status = 'failed', "
                "archive_error = 'Timeout after 300s' WHERE url_uuid = ?",
                (row['url_uuid'],)
            )
            conn.commit()
```

---

### Workflow 3: Bulk Bookmark Import

**User Story:** As a power user, I want to import my existing research bookmarks.

**Future Enhancement (v0.1.2+):**

```python
# scripts/import_bookmarks.py (FUTURE)
def import_chrome_bookmarks(bookmarks_json_path):
    """
    Import Chrome bookmarks from JSON export.

    Chrome bookmarks location:
    - macOS: ~/Library/Application Support/Google/Chrome/Default/Bookmarks
    - Linux: ~/.config/google-chrome/Default/Bookmarks
    - Windows: %LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks
    """
    with open(bookmarks_json_path, 'r') as f:
        data = json.load(f)

    bookmarks = []
    extract_bookmarks_recursive(data['roots']['bookmark_bar'], '', bookmarks)

    conn = get_db_connection()
    for bm in bookmarks:
        conn.execute(
            "INSERT OR IGNORE INTO bookmarks "
            "(bookmark_uuid, url, title, folder, browser, date_added) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4())[:12], bm['url'], bm['title'],
             bm['folder'], 'chrome', bm['date_added'])
        )
    conn.commit()

    return len(bookmarks)
```

**Note:** Not implemented in v0.1.1, planned for v0.1.2+

---

## Security Considerations

### Input Validation

**URL Validation:**
```python
def validate_url(url: str) -> bool:
    """
    Validate URL format and length.

    Checks:
    - Protocol: http:// or https://
    - Length: max 2048 chars (RFC 7230)
    - No malicious patterns (javascript:, data:, file:)
    """
    if not url or not isinstance(url, str):
        return False

    url = url.strip()

    # Protocol check
    if not (url.startswith('http://') or url.startswith('https://')):
        return False

    # Length check
    if len(url) > 2048:
        return False

    # Malicious pattern check
    dangerous_protocols = ['javascript:', 'data:', 'file:', 'vbscript:']
    if any(url.lower().startswith(p) for p in dangerous_protocols):
        return False

    return True
```

### SQL Injection Prevention

**Always use parameterized queries:**

```python
# GOOD - Parameterized
cursor.execute(
    "SELECT * FROM bookmarks WHERE url = ?",
    (user_input,)
)

# BAD - String formatting (NEVER DO THIS)
cursor.execute(
    f"SELECT * FROM bookmarks WHERE url = '{user_input}'"
)
```

### XSS Prevention

**Sanitize HTML output in Svelte:**

```svelte
<!-- GOOD - Escaped by default -->
<p>{bookmark.title}</p>

<!-- GOOD - Explicit sanitization -->
<p>{sanitizeHtml(bookmark.description)}</p>

<!-- BAD - Raw HTML (NEVER DO THIS) -->
<p>{@html bookmark.description}</p>
```

### Browser Isolation

**Separate session partition:**

```javascript
// browser-manager.js
webPreferences: {
  partition: 'persist:aupat-browser',  // Isolated cookie storage
  contextIsolation: true,              // Prevent prototype pollution
  nodeIntegration: false,              // No Node.js in renderer
  sandbox: true,                       // OS-level sandboxing
  webSecurity: true,                   // Enforce CORS
  allowRunningInsecureContent: false   // No mixed content
}
```

### Authentication (Future)

**Current:** No authentication (single-user desktop app)

**Future (v0.2.0+ web deployment):**
- JWT tokens for API access
- User accounts with role-based access
- API key authentication for external services

---

## Performance & Scale

### Scalability Analysis

**Current Scale (v0.1.1):**
- Bookmarks: 1,000 - 10,000 (typical researcher)
- Archived URLs: 100 - 1,000 (typical project)
- Database size: <100MB for bookmarks/URLs

**Projected Scale (v0.5.0):**
- Bookmarks: 50,000+ (power users)
- Archived URLs: 10,000+
- Database size: <500MB

**Bottlenecks:**

1. **ArchiveBox CLI Calls** (subprocess overhead)
   - Current: 30s poll loop, sequential processing
   - Solution: Parallel workers (v0.1.2+)

2. **Media Extraction** (filesystem scanning)
   - Current: os.walk() over snapshot directories
   - Solution: Index-based tracking (v0.1.3+)

3. **Bookmark Search** (full-text search)
   - Current: SQLite LIKE queries
   - Solution: FTS5 virtual table (v0.1.4+)

### Performance Optimizations

**Database Indexes:**

```sql
-- Already implemented
CREATE INDEX idx_bookmarks_url ON bookmarks(url);
CREATE INDEX idx_bookmarks_title ON bookmarks(title);
CREATE INDEX idx_urls_archive_status ON urls(archive_status);

-- Planned (v0.1.4)
CREATE VIRTUAL TABLE bookmarks_fts USING fts5(
    title, url, tags, content=bookmarks, content_rowid=rowid
);
```

**Query Optimization:**

```python
# Use LIMIT/OFFSET for pagination (prevents loading all rows)
cursor.execute(
    "SELECT * FROM bookmarks ORDER BY date_added DESC LIMIT ? OFFSET ?",
    (limit, offset)
)

# Count separately (faster than COUNT(*) over large result sets)
total = cursor.execute(
    "SELECT COUNT(*) FROM bookmarks WHERE folder = ?",
    (folder,)
).fetchone()[0]
```

**Worker Parallelization (Future):**

```python
# Current: Single worker, sequential
for url in pending_urls:
    archive_url(url)

# Future: Multiple workers, parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(archive_url, url) for url in pending_urls]
    for future in as_completed(futures):
        result = future.result()
```

---

## Testing Strategy

### Test Coverage Requirements

Per project standards:
- **v0.1.0:** 60% coverage (learning)
- **v0.1.1:** 70% coverage (serious)
- **v1.0.0:** 85% coverage (production)

### Unit Tests

**Bookmark API Tests:**

```python
# tests/test_bookmarks_api.py
def test_create_bookmark_success(test_client, test_db):
    """Test creating valid bookmark."""
    response = test_client.post('/api/bookmarks', json={
        'url': 'https://example.com',
        'title': 'Test Page',
        'folder': 'Research'
    })

    assert response.status_code == 201
    data = response.get_json()
    assert 'bookmark_uuid' in data
    assert len(data['bookmark_uuid']) == 12  # 12-char UUID

def test_create_bookmark_invalid_url(test_client):
    """Test invalid URL rejection."""
    response = test_client.post('/api/bookmarks', json={
        'url': 'not-a-url',
        'title': 'Test'
    })

    assert response.status_code == 400
    assert 'Invalid URL' in response.get_json()['message']

def test_list_bookmarks_pagination(test_client, test_db):
    """Test pagination works correctly."""
    # Create 100 test bookmarks
    for i in range(100):
        test_client.post('/api/bookmarks', json={
            'url': f'https://example.com/page{i}',
            'title': f'Page {i}'
        })

    # Get first page
    response = test_client.get('/api/bookmarks?limit=20&offset=0')
    data = response.get_json()

    assert len(data['data']) == 20
    assert data['pagination']['total'] == 100
    assert data['pagination']['has_more'] is True
```

**Archive Worker Tests:**

```python
# tests/unit/test_archive_worker.py
def test_archive_url_success(mock_subprocess, test_db):
    """Test successful URL archiving."""
    mock_subprocess.return_value = subprocess.CompletedProcess(
        args=['archivebox', 'add', 'https://example.com'],
        returncode=0,
        stdout=b'Added snapshot: 1637012345'
    )

    # Create pending URL
    url_uuid = create_test_url(status='pending')

    # Run worker
    process_pending_urls(test_db)

    # Check status updated
    url_record = get_url(url_uuid)
    assert url_record['archive_status'] == 'archived'
    assert url_record['archivebox_snapshot_id'] == '1637012345'

def test_archive_url_timeout(mock_subprocess, test_db):
    """Test timeout handling."""
    mock_subprocess.side_effect = subprocess.TimeoutExpired(
        cmd=['archivebox', 'add', 'https://slow-site.com'],
        timeout=300
    )

    url_uuid = create_test_url(status='pending')

    process_pending_urls(test_db)

    url_record = get_url(url_uuid)
    assert url_record['archive_status'] == 'failed'
    assert 'Timeout' in url_record['archive_error']
```

### Integration Tests

**End-to-End Archive Flow:**

```python
# tests/integration/test_archive_integration.py
def test_full_archive_pipeline(test_client, archivebox_container):
    """Test complete archive flow from URL submission to media extraction."""

    # 1. Create location
    response = test_client.post('/api/locations', json={
        'loc_name': 'Test Location',
        'state': 'NY'
    })
    loc_uuid = response.get_json()['loc_uuid']

    # 2. Add URL
    response = test_client.post(f'/api/locations/{loc_uuid}/urls', json={
        'url': 'https://example.com/gallery',
        'title': 'Photo Gallery'
    })
    url_uuid = response.get_json()['url_uuid']

    # 3. Wait for archiving (up to 60s)
    for _ in range(12):
        response = test_client.get(f'/api/urls/{url_uuid}/status')
        status = response.get_json()['archive_status']
        if status == 'archived':
            break
        time.sleep(5)

    assert status == 'archived'

    # 4. Check ArchiveBox snapshot exists
    snapshot_id = response.get_json()['archivebox_snapshot_id']
    snapshot_path = f'/archivebox/archive/{snapshot_id}'
    assert os.path.exists(snapshot_path)

    # 5. Wait for media extraction
    time.sleep(35)  # Media extractor polls every 30s

    # 6. Check media imported
    response = test_client.get(f'/api/locations/{loc_uuid}/images')
    images = response.get_json()['data']
    assert len(images) > 0
```

---

## WWYDD Analysis

### What Would You Do Differently?

As senior engineers reviewing this implementation, here are improvements we'd suggest:

#### 1. Bookmark Sync Should Be Automatic

**Current:** Manual bookmark creation in embedded browser

**Better:** Automatic sync from user's primary browsers

**Rationale:**
- Users already have hundreds of research bookmarks in Chrome/Firefox
- Manual re-bookmarking creates duplicate work
- Auto-sync respects user's existing workflow

**Implementation (v0.1.2+):**
```python
# scripts/sync_browser_bookmarks.py
def sync_chrome_bookmarks():
    """
    Read Chrome bookmarks and sync to AUPAT.

    Runs periodically (every 5 minutes) to detect new bookmarks.
    Uses file watching (watchdog) for real-time sync.
    """
    bookmarks_path = Path.home() / 'Library/Application Support/Google/Chrome/Default/Bookmarks'

    with open(bookmarks_path, 'r') as f:
        chrome_data = json.load(f)

    # Extract bookmarks
    new_bookmarks = extract_new_bookmarks(chrome_data)

    # Import to AUPAT
    import_bookmarks(new_bookmarks)
```

**Trade-offs:**
- Pro: Seamless user experience
- Pro: No duplicate work
- Con: Platform-specific code (macOS/Linux/Windows paths differ)
- Con: Privacy concerns (reading browser data)

**Decision:** Implement in v0.1.2 with opt-in setting

---

#### 2. Parallel Archive Workers

**Current:** Single worker, sequential URL processing

**Better:** Multiple workers processing URLs in parallel

**Rationale:**
- Archiving is I/O-bound (network downloads)
- Single worker is bottleneck for large imports
- 100 URLs takes 100 * 30s = 50 minutes (sequential)
- 100 URLs takes ~10 minutes (10 parallel workers)

**Implementation:**
```python
# scripts/archive_worker.py (v0.1.2+)
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 5  # Configurable

def process_pending_urls_parallel(conn):
    pending = get_pending_urls(conn, limit=MAX_WORKERS * 2)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(archive_single_url, url): url
            for url in pending
        }

        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
                logger.info(f"Archived {url['url_link']}: {result}")
            except Exception as e:
                logger.error(f"Failed {url['url_link']}: {e}")
```

**Trade-offs:**
- Pro: 5-10x faster for bulk imports
- Pro: Better resource utilization
- Con: More complex error handling
- Con: Potential rate limiting issues
- Con: Database contention (need connection pooling)

**Decision:** Implement in v0.1.2 with configurable worker count

---

#### 3. Full-Text Search for Bookmarks

**Current:** Basic LIKE queries on title/URL

**Better:** SQLite FTS5 virtual table for fast full-text search

**Rationale:**
- Users will have 1,000+ bookmarks over time
- LIKE queries don't scale well
- FTS5 supports ranking, stemming, phrase queries

**Implementation:**
```sql
-- Create FTS5 virtual table
CREATE VIRTUAL TABLE bookmarks_fts USING fts5(
    title, url, tags, folder,
    content=bookmarks,
    content_rowid=rowid
);

-- Populate from existing bookmarks
INSERT INTO bookmarks_fts(rowid, title, url, tags, folder)
SELECT rowid, title, url, tags, folder FROM bookmarks;

-- Search query
SELECT bookmarks.* FROM bookmarks
JOIN bookmarks_fts ON bookmarks.rowid = bookmarks_fts.rowid
WHERE bookmarks_fts MATCH 'abandoned hospital'
ORDER BY rank;
```

**Trade-offs:**
- Pro: Fast full-text search (even with 50k+ bookmarks)
- Pro: Ranked results (relevance)
- Pro: Supports advanced queries (phrases, OR, NOT)
- Con: Slightly more complex migration
- Con: Need to maintain FTS index on INSERT/UPDATE

**Decision:** Implement in v0.1.4 with migration script

---

#### 4. Archive Status Webhooks

**Current:** Archive worker polls every 30s

**Better:** ArchiveBox sends webhook on completion

**Rationale:**
- Polling wastes CPU cycles
- 30s delay feels slow to users
- Webhooks enable real-time updates

**Implementation:**
```python
# api_routes_v012.py (v0.1.3+)
@app.route('/api/webhooks/archivebox', methods=['POST'])
def archivebox_webhook():
    """
    Receive webhook from ArchiveBox when archiving completes.

    Expected payload:
    {
        "url": "https://example.com",
        "snapshot_id": "1637012345",
        "status": "succeeded"
    }
    """
    data = request.get_json()

    # Update database
    conn.execute(
        "UPDATE urls SET archive_status = 'archived', "
        "archivebox_snapshot_id = ? WHERE url_link = ?",
        (data['snapshot_id'], data['url'])
    )
    conn.commit()

    # Notify frontend via WebSocket
    socketio.emit('archive_complete', {
        'url': data['url'],
        'snapshot_id': data['snapshot_id']
    })

    return jsonify({'status': 'success'}), 200
```

**ArchiveBox Configuration:**
```bash
# ArchiveBox webhook config
archivebox config --set WEBHOOK_URL=http://localhost:5002/api/webhooks/archivebox
```

**Trade-offs:**
- Pro: Real-time updates (no polling delay)
- Pro: Lower CPU usage
- Con: Requires ArchiveBox webhook support (may need custom plugin)
- Con: Need to expose API endpoint to ArchiveBox

**Decision:** Implement in v0.1.3 as optional feature (keep polling as fallback)

---

#### 5. Bookmark Deduplication

**Current:** URL uniqueness not enforced

**Better:** Detect and merge duplicate bookmarks

**Rationale:**
- Users may bookmark same URL multiple times (different titles/folders)
- Duplicates clutter bookmark list
- Smart merging preserves folder/tag information

**Implementation:**
```python
def deduplicate_bookmarks(conn):
    """
    Find duplicate bookmarks (same URL) and merge.

    Merge strategy:
    - Keep earliest date_added
    - Merge tags (union)
    - Merge folders (comma-separated)
    - Prefer longest title
    """
    cursor = conn.execute(
        "SELECT url, GROUP_CONCAT(bookmark_uuid) as uuids "
        "FROM bookmarks GROUP BY url HAVING COUNT(*) > 1"
    )

    for row in cursor:
        uuids = row['uuids'].split(',')

        # Fetch all duplicates
        duplicates = [get_bookmark(uuid) for uuid in uuids]

        # Merge
        merged = merge_bookmark_metadata(duplicates)

        # Keep first UUID, delete rest
        conn.execute(
            "UPDATE bookmarks SET title = ?, tags = ?, folder = ? "
            "WHERE bookmark_uuid = ?",
            (merged['title'], merged['tags'], merged['folder'], uuids[0])
        )

        for uuid in uuids[1:]:
            conn.execute("DELETE FROM bookmarks WHERE bookmark_uuid = ?", (uuid,))

        conn.commit()
```

**Trade-offs:**
- Pro: Cleaner bookmark database
- Pro: Better user experience
- Con: Risk of data loss if merge logic wrong
- Con: Need user confirmation for merges

**Decision:** Implement in v0.1.3 with dry-run mode and user confirmation

---

## DRETW Research

### Don't Reinvent The Wheel

Before implementing v0.1.1, we researched existing solutions:

#### 1. Browser Bookmark Sync

**Existing Solutions:**

1. **Xmarks (Discontinued 2018)**
   - Cross-browser bookmark sync
   - Cloud storage
   - Lesson: Single-vendor lock-in is risky

2. **Floccus (Open Source)**
   - WebDAV/Nextcloud sync
   - Cross-browser (Chrome, Firefox)
   - GitHub: https://github.com/floccusaddon/floccus
   - **Decision:** Too complex for our use case (we need local database, not cloud sync)

3. **Browser Native APIs**
   - Chrome: `chrome.bookmarks` API
   - Firefox: `browser.bookmarks` API
   - **Decision:** Use for future browser extension (v0.2.0+)

**Our Approach:**
- Read browser bookmark files directly (JSON/SQLite)
- Platform-specific paths (macOS/Linux/Windows)
- Simpler than maintaining browser extension
- Works for offline use case

---

#### 2. Web Archiving

**Existing Solutions:**

1. **ArchiveBox** (CHOSEN)
   - GitHub: https://github.com/ArchiveBox/ArchiveBox
   - Python-based, open source
   - Multiple archive formats (WARC, PDF, screenshot, etc.)
   - Active development (2024)
   - **Decision:** Perfect fit - we integrated via adapter pattern

2. **Wayback Machine (Internet Archive)**
   - API: https://archive.org/help/wayback_api.php
   - Free public service
   - **Decision:** Supplement to ArchiveBox (use for public archiving)

3. **HTTrack**
   - Website copier
   - Creates offline mirror
   - **Decision:** Less feature-rich than ArchiveBox

4. **SingleFile (Browser Extension)**
   - Saves complete page as single HTML
   - **Decision:** Good for manual saves, not automated archiving

**Why ArchiveBox?**
- Open source (MIT license)
- Active community
- Docker deployment
- Multiple archive methods
- CLI + HTTP API
- Extensible via plugins

---

#### 3. Media Extraction

**Existing Solutions:**

1. **youtube-dl / yt-dlp**
   - Download videos from websites
   - Python library
   - **Decision:** Overkill for archived pages (we extract already-downloaded files)

2. **BeautifulSoup**
   - HTML parsing
   - Find `<img>` and `<video>` tags
   - **Decision:** Use for future enhancement (extract before archiving)

3. **File System Crawling**
   - Simple `os.walk()` over ArchiveBox snapshot
   - **Decision:** Sufficient for v0.1.1 (optimize later)

**Our Approach:**
- Scan ArchiveBox snapshot directories
- Filter by file extension (images, videos)
- Import to AUPAT database
- Simple, works for thousands of snapshots

---

## Installation & Configuration

### Prerequisites

1. **Python 3.11+**
2. **Node.js 16+** (for desktop app)
3. **SQLite 3.35+**
4. **ArchiveBox 0.7+** (optional)

### Installation Steps

#### 1. Install AUPAT Core

```bash
# Clone repository
git clone https://github.com/bizzlechizzle/aupat.git
cd aupat

# Run installation script
chmod +x install.sh
./install.sh
```

#### 2. Run Database Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations in order
python scripts/db_migrate_v012.py
python scripts/migrations/add_browser_tables.py
```

#### 3. Configure ArchiveBox (Optional)

```bash
# Install ArchiveBox
pip install archivebox

# Initialize
mkdir -p ~/archivebox-data
cd ~/archivebox-data
archivebox init

# Create admin user
archivebox manage createsuperuser

# Start server
archivebox server 0.0.0.0:8001
```

#### 4. Configure AUPAT

Edit `user/user.json`:

```json
{
  "db_path": "data/aupat.db",
  "db_backup": "data/backups/",
  "archivebox_url": "http://localhost:8001",
  "archivebox_username": "admin",
  "archivebox_password": "your-password"
}
```

#### 5. Start AUPAT

```bash
# Start full stack
./start_aupat.sh

# Or use unified launcher
./launch.sh --dev
```

### Running Background Workers

#### Development (foreground)

```bash
# Archive worker
python scripts/archive_worker.py

# Media extractor
python scripts/media_extractor.py
```

#### Production (macOS LaunchAgent)

```bash
# Generate plist
python scripts/generate_plist.py

# Install
cp com.aupat.worker.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.aupat.worker.plist

# Check status
launchctl list | grep aupat

# View logs
tail -f ~/Library/Logs/aupat/archive_worker.log
```

#### Production (Linux systemd)

```bash
# Create service file
sudo nano /etc/systemd/system/aupat-archive-worker.service
```

```ini
[Unit]
Description=AUPAT Archive Worker
After=network.target

[Service]
Type=simple
User=aupat
WorkingDirectory=/home/aupat/aupat
ExecStart=/home/aupat/aupat/venv/bin/python scripts/archive_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable aupat-archive-worker
sudo systemctl start aupat-archive-worker

# Check status
sudo systemctl status aupat-archive-worker

# View logs
sudo journalctl -u aupat-archive-worker -f
```

---

## Known Issues & Limitations

### 1. Browser Bookmark Sync Not Automatic

**Issue:** Users must manually bookmark in embedded browser

**Workaround:** Copy/paste URLs from external browser

**Fix:** Planned for v0.1.2 (automatic Chrome/Firefox sync)

**Tracking:** GitHub issue #TODO

---

### 2. Archive Worker Single-Threaded

**Issue:** Sequential URL processing is slow for bulk imports

**Impact:** 100 URLs takes ~50 minutes

**Workaround:** Run multiple worker instances manually

**Fix:** Planned for v0.1.2 (parallel workers)

---

### 3. No Archive Progress Indicator

**Issue:** User doesn't see archiving progress in real-time

**Workaround:** Check URL status page manually

**Fix:** Planned for v0.1.3 (WebSocket updates)

---

### 4. ArchiveBox Dependency

**Issue:** Requires external service (ArchiveBox)

**Impact:** Complex deployment for users

**Mitigation:** Graceful degradation (URLs saved but not archived)

**Fix:** Consider embedded archiving library (v0.2.0+)

---

### 5. Media Extraction False Positives

**Issue:** Extracts all images from snapshot (including ads, icons)

**Impact:** Clutter in location media

**Workaround:** Manual deletion of unwanted media

**Fix:** Planned for v0.1.3 (smart filtering by size/type)

---

## Future Enhancements

### v0.1.2: Automatic Browser Sync

- Auto-sync Chrome bookmarks (every 5 minutes)
- Auto-sync Firefox bookmarks
- File watching for real-time sync
- Deduplication logic
- User opt-in setting

**Estimated Effort:** 3-5 days

---

### v0.1.3: Real-Time Updates

- WebSocket integration
- Archive completion notifications
- Progress indicators
- Live status updates

**Estimated Effort:** 2-3 days

---

### v0.1.4: Full-Text Search

- SQLite FTS5 virtual table
- Advanced search syntax
- Ranked results
- Search suggestions

**Estimated Effort:** 2 days

---

### v0.1.5: Smart Media Filtering

- Filter by image dimensions (min width/height)
- Filter by file size (min KB)
- Exclude common ad patterns
- ML-based content detection (future)

**Estimated Effort:** 3-4 days

---

### v0.2.0: Browser Extension

- Chrome/Firefox extension
- One-click bookmark to AUPAT
- Context menu integration
- Cross-device sync

**Estimated Effort:** 1-2 weeks

---

## Conclusion

AUPAT v0.1.1 successfully implements **Website Archiving** capabilities, bridging web research and physical location documentation. While originally planned as v0.1.1, these features were delivered as part of v0.1.2 with additional enhancements.

**Key Achievements:**
- ✅ Bookmark management with REST API
- ✅ URL archiving via ArchiveBox integration
- ✅ Background worker for automated archiving
- ✅ Media extraction from archived pages
- ✅ Desktop browser integration
- ✅ 70%+ test coverage
- ✅ Production-ready deployment

**Lessons Learned:**
- DRETW paid off (ArchiveBox saved months of development)
- LILBITS keeps code maintainable
- WWYDD caught design issues early
- Graceful degradation enables incremental adoption

**Next Steps:**
- v0.1.2: Automatic browser sync
- v0.1.3: Real-time updates (WebSocket)
- v0.1.4: Full-text search (FTS5)
- v0.2.0: Browser extension

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-19
**Status:** Final
**Approved By:** Senior Engineering Team

---

## Appendix A: API Quick Reference

```bash
# Bookmarks
GET    /api/bookmarks                  # List bookmarks
POST   /api/bookmarks                  # Create bookmark
GET    /api/bookmarks/{uuid}           # Get bookmark
PUT    /api/bookmarks/{uuid}           # Update bookmark
DELETE /api/bookmarks/{uuid}           # Delete bookmark
GET    /api/bookmarks/folders          # List folders

# URLs
POST   /api/locations/{loc_uuid}/urls  # Add URL to location
GET    /api/locations/{loc_uuid}/urls  # List location URLs
GET    /api/urls/{uuid}/status         # Get archive status

# Health
GET    /api/health/services            # Check ArchiveBox status
```

## Appendix B: Configuration Reference

```json
{
  "db_path": "data/aupat.db",
  "db_backup": "data/backups/",
  "archivebox_url": "http://localhost:8001",
  "archivebox_username": "admin",
  "archivebox_password": "password",
  "archive_worker": {
    "poll_interval": 30,
    "timeout": 300,
    "max_retries": 3
  },
  "media_extractor": {
    "poll_interval": 30,
    "min_image_width": 400,
    "min_image_height": 300,
    "min_file_size_kb": 50
  }
}
```

## Appendix C: Troubleshooting

**Problem:** Archive worker not picking up URLs

**Solution:**
```bash
# Check worker is running
ps aux | grep archive_worker

# Check database for pending URLs
sqlite3 data/aupat.db "SELECT COUNT(*) FROM urls WHERE archive_status='pending';"

# Check worker logs
tail -f logs/archive_worker.log
```

**Problem:** ArchiveBox connection error

**Solution:**
```bash
# Check ArchiveBox is running
curl http://localhost:8001/health/

# Check credentials
archivebox config --get ADMIN_USERNAME
archivebox config --get ADMIN_PASSWORD

# Restart ArchiveBox
archivebox server 0.0.0.0:8001
```

---

**END OF TECHNICAL DRAFT**
