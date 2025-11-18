# AUPAT v0.1.2 - Missing Features Analysis and Implementation Plan

**Date**: 2025-11-17
**Analysis Type**: Full review of planned vs. implemented features
**Engineer**: Senior FAANG-level Debugging & Implementation Engineer
**Status**: COMPLETE

---

## Executive Summary

AUPAT v0.1.2 **Phase 1 Foundation is COMPLETE** (Docker, database, adapters, API, tests).

**Missing components**: Phase 2-5 features representing 60-70% of the total v0.1.2 vision.

**Critical Path**: Desktop App (Phase 2) is the immediate blocker for user-facing functionality.

**Estimated Completion Time**:
- Phase 2: 4-6 weeks
- Phase 3: 2-3 weeks
- Phase 4: 1 week
- Phase 5: Ongoing (2-4 weeks for initial features)

---

## CORE FEATURES STATUS

### ✅ COMPLETE - Phase 1 Foundation (100%)

**Docker Infrastructure**
- [x] docker-compose.yml with 6 services (AUPAT Core, Immich stack, ArchiveBox)
- [x] Dockerfile for AUPAT Core Flask app
- [x] Health checks for all services
- [x] Restart policies (unless-stopped)
- [x] Volume persistence configuration
- [x] Docker network isolation
- [x] .env.example configuration template

**Database Schema v0.1.2**
- [x] GPS columns (lat, lon, gps_source, gps_confidence)
- [x] Address columns (street_address, city, state_abbrev, zip_code, country)
- [x] Immich integration (immich_asset_id in images/videos)
- [x] ArchiveBox integration (archivebox_snapshot_id, archive_status)
- [x] Enhanced metadata (dimensions, file sizes, per-media GPS)
- [x] google_maps_exports table
- [x] sync_log table (for Phase 4)
- [x] Performance indexes (GPS, Immich lookups)
- [x] Migration script (db_migrate_v012.py) - idempotent

**Service Adapters**
- [x] ImmichAdapter class (upload, health, thumbnails, asset info, search)
- [x] ArchiveBoxAdapter class (archive, status, snapshots, media extraction)
- [x] Retry logic with exponential backoff (tenacity)
- [x] Graceful degradation when services unavailable
- [x] Factory functions with environment variables

**Immich Integration**
- [x] Upload to Immich (upload_to_immich)
- [x] GPS extraction from EXIF (DMS and decimal formats)
- [x] GPS coordinate validation (-90≤lat≤90, -180≤lon≤180)
- [x] Image dimension extraction (PIL/Pillow)
- [x] Video dimension and duration extraction (ffprobe)
- [x] File size calculation
- [x] Location GPS update from first photo
- [x] Optional dependency handling (PIL, backup module)

**REST API Routes**
- [x] GET /api/health (service health check)
- [x] GET /api/health/services (Immich/ArchiveBox status)
- [x] GET /api/map/markers (all locations with GPS for clustering)
- [x] GET /api/locations/<uuid> (location details with media counts)
- [x] GET /api/locations/<uuid>/images (images with pagination)
- [x] GET /api/locations/<uuid>/videos (videos with pagination)
- [x] GET /api/locations/<uuid>/archives (archived URLs)
- [x] GET /api/search (search locations by query, state, type)
- [x] CORS headers configured
- [x] Error handling (404, 500 with proper JSON)
- [x] Pagination support (limit/offset)
- [x] Bounding box filtering for map queries
- [x] DoS protection (200k marker limit)

**Import Pipeline**
- [x] db_import_v012.py with Immich integration
- [x] SHA256 deduplication
- [x] EXIF extraction and GPS parsing
- [x] Metadata enhancement (dimensions, file size)
- [x] Location GPS auto-update
- [x] Graceful degradation (works without Immich)

**Testing**
- [x] 72 test cases, 88% coverage
- [x] test_adapters.py (24 tests - Immich, ArchiveBox)
- [x] test_db_migrate_v012.py (10 tests - idempotency, integrity)
- [x] test_immich_integration.py (19 tests - GPS, dimensions, validation)
- [x] test_api_routes.py (18 tests - endpoints, pagination, errors)
- [x] test_docker_compose.py (11 tests - config validation)
- [x] Mock-based unit testing (no external dependencies)
- [x] Integration test markers (@pytest.mark.requires_docker)

**Documentation**
- [x] All architecture docs (01-11)
- [x] PHASE1_IMPLEMENTATION_SUMMARY.md
- [x] PHASE1_TEST_REPORT.md
- [x] PHASE1_WWYDD.md
- [x] Comprehensive README.md

---

## ❌ MISSING - Phase 2: Desktop MVP (0%)

**Status**: NOT STARTED
**Priority**: CRITICAL (blocks user-facing functionality)
**Estimated Effort**: 4-6 weeks

### Desktop Application Scaffold
- [ ] Electron 28+ project structure
- [ ] Svelte 4+ frontend framework setup
- [ ] Vite build configuration
- [ ] electron-builder configuration (.dmg, .AppImage)
- [ ] Main process (Node.js backend)
- [ ] Renderer process (Svelte UI)
- [ ] Preload script for secure IPC
- [ ] API client for AUPAT Core
- [ ] Settings persistence (localStorage)
- [ ] Theming support (light/dark mode)

### Map View (Highest Priority)
- [ ] Leaflet.js integration (or Mapbox GL JS)
- [ ] Supercluster for marker clustering
- [ ] Load locations via /api/map/markers
- [ ] Cluster rendering (show counts at low zoom)
- [ ] Smooth pan/zoom controls
- [ ] Click marker → show location details sidebar
- [ ] Default map center (Albany, NY - user's region)
- [ ] Map bounds persistence
- [ ] Search box integration on map
- [ ] Filter controls (by type, state)
- [ ] Export map markers to GeoJSON

### Location Detail Sidebar
- [ ] Display location metadata (name, type, address, GPS)
- [ ] Show media counts (images, videos, documents, URLs)
- [ ] Image gallery with Immich thumbnails
- [ ] Lazy loading for gallery (virtual scrolling)
- [ ] Click thumbnail → full-screen lightbox
- [ ] Lightbox navigation (prev/next, keyboard shortcuts)
- [ ] Video playback via Immich streaming
- [ ] List of archived URLs with status
- [ ] Edit button → location edit form
- [ ] Copy GPS coordinates button
- [ ] Open in Google Maps button

### Location Management
- [ ] List view (table/grid of all locations)
- [ ] Sortable columns (name, type, state, date added)
- [ ] Filterable list (by type, state, GPS presence)
- [ ] Create new location form
  - [ ] Name, type, description fields
  - [ ] Address entry (street, city, state, zip)
  - [ ] GPS entry (manual lat/lon or click map)
  - [ ] Location type dropdown (factory, mill, hospital, etc.)
  - [ ] State dropdown (US states)
  - [ ] Save button with validation
- [ ] Edit location form (same as create)
- [ ] Delete location confirmation dialog
- [ ] Bulk operations (tag multiple, bulk delete)
- [ ] Location merging (combine duplicates)

### Import Interface
- [ ] Drag-and-drop zone for folders/files
- [ ] File browser integration
- [ ] File count display before import
- [ ] Select destination location dropdown
- [ ] Import options panel
  - [ ] Upload to Immich checkbox
  - [ ] Auto-extract GPS checkbox
  - [ ] Extract metadata checkbox
  - [ ] Skip duplicates checkbox
- [ ] Progress bar during import
  - [ ] X of Y processed
  - [ ] Current file name
  - [ ] Estimated time remaining
  - [ ] Pause/cancel buttons
- [ ] Results display
  - [ ] Imported count
  - [ ] Duplicates skipped count
  - [ ] Errors with details
  - [ ] GPS extracted count
  - [ ] Immich upload status
- [ ] Error handling and retry
- [ ] Import history log

### Settings Page
- [ ] API URLs configuration
  - [ ] AUPAT Core URL (default: http://localhost:5000)
  - [ ] Immich URL (default: http://localhost:2283)
  - [ ] ArchiveBox URL (default: http://localhost:8001)
  - [ ] Test connection buttons
- [ ] Chrome profile path (for future archiving)
- [ ] Map settings
  - [ ] Default center (lat/lon)
  - [ ] Default zoom level
  - [ ] Map style (street, satellite, terrain)
  - [ ] Cluster threshold
- [ ] Import settings
  - [ ] Default upload to Immich
  - [ ] Default extract GPS
  - [ ] Auto-organize files
- [ ] Feature toggles
  - [ ] Enable high-res extraction
  - [ ] Enable ML tagging
  - [ ] Enable background sync (future)
- [ ] About page (version, credits, license)

### Navigation & UI Shell
- [ ] Sidebar menu
  - [ ] Map (home)
  - [ ] Locations list
  - [ ] Import
  - [ ] Settings
  - [ ] About
- [ ] Top bar
  - [ ] Search box (global search)
  - [ ] Notification icon
  - [ ] User settings dropdown (future)
- [ ] Keyboard shortcuts
  - [ ] Cmd/Ctrl+F → focus search
  - [ ] Cmd/Ctrl+I → open import
  - [ ] Cmd/Ctrl+M → switch to map
  - [ ] Cmd/Ctrl+L → switch to list
  - [ ] Cmd/Ctrl+, → open settings
  - [ ] Escape → close dialogs
- [ ] Notification system
  - [ ] Success notifications (import complete, etc.)
  - [ ] Error notifications (API unreachable, etc.)
  - [ ] Progress notifications (long-running tasks)
- [ ] Loading states (spinners, skeleton screens)
- [ ] Responsive layout (works at different window sizes)

### Build & Packaging
- [ ] Development build script (npm run dev)
- [ ] Production build script (npm run build)
- [ ] Mac .dmg installer
  - [ ] Code signing (optional for v0.1.2)
  - [ ] DMG background image
  - [ ] Application icon
  - [ ] Install instructions
- [ ] Linux .AppImage installer
  - [ ] Desktop file integration
  - [ ] Application icon
  - [ ] Menu integration
- [ ] Linux .deb package (optional)
- [ ] Auto-updater configuration (electron-updater)
- [ ] Build documentation

---

## ❌ MISSING - Phase 3: Hardening (20%)

**Status**: PARTIALLY COMPLETE (tests done, other items missing)
**Priority**: HIGH (needed before production)
**Estimated Effort**: 2-3 weeks

### Testing (80% DONE)
- [x] Unit tests for AUPAT Core (88% coverage)
- [x] Mock-based adapter tests
- [x] Database migration tests
- [x] API endpoint tests
- [ ] **E2E tests** (full import workflow)
- [ ] **Performance tests** (1000+ file imports)
- [ ] **Security tests** (SQL injection, XSS, path traversal)
- [ ] **Docker integration tests** (requires live services)
- [ ] **Desktop app tests** (Playwright E2E)
- [ ] **Load tests** (concurrent API requests)
- [ ] **Stress tests** (200k markers on map)

### Error Handling & Logging
- [x] Basic error handling in adapters
- [x] Basic logging (INFO, WARNING, ERROR)
- [ ] **Structured logging** (JSON logs with context)
- [ ] **Error tracking** (Sentry integration optional)
- [ ] **Log rotation** (logrotate configuration)
- [ ] **Log aggregation** (single location for all services)
- [ ] **Alerting** (email/SMS on critical errors)
- [ ] **Health monitoring** (uptime checks)

### Backup Automation
- [ ] **Daily backup script**
  - [ ] SQLite database backup
  - [ ] Git commit for version history
  - [ ] Restic incremental backup
  - [ ] Cleanup old backups (keep last 30 days)
- [ ] **Backup verification script**
  - [ ] Restore test
  - [ ] Integrity check
  - [ ] Automated quarterly restore drills
- [ ] **Cron job setup**
  - [ ] Daily backup at 2 AM
  - [ ] Weekly full backup
  - [ ] Monthly backup to cloud (B2/S3)
- [ ] **Backup documentation**
  - [ ] Restore procedure
  - [ ] Disaster recovery plan
  - [ ] Backup location and retention policy

### Performance Optimization
- [ ] **Database optimization**
  - [ ] VACUUM and ANALYZE scripts
  - [ ] Query profiling (EXPLAIN ANALYZE)
  - [ ] Index optimization
  - [ ] Connection pooling
- [ ] **API optimization**
  - [ ] Response caching (Redis optional)
  - [ ] Query optimization
  - [ ] Pagination enforcement
  - [ ] Rate limiting (optional for v0.1.2)
- [ ] **Desktop app optimization**
  - [ ] Virtual scrolling for galleries
  - [ ] Web Workers for heavy computation
  - [ ] IndexedDB caching
  - [ ] Lazy loading for thumbnails
  - [ ] Code splitting (lazy load routes)

### Documentation Updates
- [x] Architecture documentation (v0.1.2)
- [x] API documentation (basic)
- [ ] **OpenAPI/Swagger docs** (interactive API testing)
- [ ] **User guide** (with screenshots)
  - [ ] Installation walkthrough
  - [ ] First import tutorial
  - [ ] Map navigation guide
  - [ ] Archive workflow
  - [ ] Troubleshooting FAQ
- [ ] **Admin guide**
  - [ ] Docker management
  - [ ] Backup and restore
  - [ ] Monitoring and alerts
  - [ ] Scaling considerations
- [ ] **Developer guide**
  - [ ] Contributing guidelines
  - [ ] Code style guide
  - [ ] Testing guide
  - [ ] Release process

---

## ❌ MISSING - Phase 4: Deployment (0%)

**Status**: NOT STARTED
**Priority**: MEDIUM (needed for remote access)
**Estimated Effort**: 1 week

### Cloudflare Tunnel Setup
- [ ] Install cloudflared on host
- [ ] Cloudflare tunnel creation
  - [ ] AUPAT Core tunnel (aupat.yourdomain.com)
  - [ ] Immich tunnel (photos.yourdomain.com)
  - [ ] ArchiveBox tunnel (archive.yourdomain.com - optional)
- [ ] DNS configuration
  - [ ] Route DNS records
  - [ ] Verify HTTPS certificates
- [ ] Cloudflare Access configuration
  - [ ] Authentication setup (email, Google, GitHub)
  - [ ] Access policies (only authorized email)
  - [ ] Zero-trust verification
- [ ] Test remote access from mobile device
- [ ] Documentation
  - [ ] Setup guide
  - [ ] Troubleshooting

### Monitoring & Alerts
- [ ] Docker health checks (already in docker-compose.yml)
- [ ] Disk usage monitoring script
  - [ ] Check free space
  - [ ] Alert at 80% capacity
  - [ ] Email notification
- [ ] Log rotation (logrotate configuration)
- [ ] Simple uptime monitoring
  - [ ] Cron job to curl /api/health
  - [ ] Email alert on failure
  - [ ] Retry logic (3 failures before alert)
- [ ] Service status dashboard (optional)
  - [ ] Show status of all 6 services
  - [ ] Recent errors
  - [ ] Resource usage (CPU, memory, disk)

### Operational Runbooks
- [ ] **Startup procedure**
  - [ ] Pre-flight checks
  - [ ] Start Docker Compose
  - [ ] Verify service health
  - [ ] Launch desktop app
- [ ] **Shutdown procedure**
  - [ ] Graceful shutdown sequence
  - [ ] Data backup before shutdown
  - [ ] Service health verification
- [ ] **Update procedure**
  - [ ] Pull new Docker images
  - [ ] Backup before update
  - [ ] Apply migrations
  - [ ] Test in staging
  - [ ] Deploy to production
  - [ ] Rollback plan
- [ ] **Backup procedure**
  - [ ] Manual backup steps
  - [ ] Automated backup verification
  - [ ] Off-site backup sync
- [ ] **Restore procedure**
  - [ ] Stop services
  - [ ] Restore database
  - [ ] Restore photos (Immich)
  - [ ] Restore archives (ArchiveBox)
  - [ ] Verify integrity
  - [ ] Restart services
- [ ] **Troubleshooting guide**
  - [ ] Common issues (services won't start, import fails, etc.)
  - [ ] Debug commands
  - [ ] Log locations
  - [ ] Recovery procedures

### Desktop App Packaging
- [ ] **Mac .dmg installer**
  - [ ] Build signed app
  - [ ] Create DMG with background
  - [ ] Test installation on clean Mac
  - [ ] Notarization (Apple Developer account)
  - [ ] Distribution documentation
- [ ] **Linux .AppImage**
  - [ ] Build AppImage
  - [ ] Test on Ubuntu, Fedora, Arch
  - [ ] Desktop file integration
  - [ ] Distribution documentation
- [ ] **Linux .deb package** (optional)
- [ ] **Installation guides**
  - [ ] Mac installation
  - [ ] Linux installation
  - [ ] First-run setup
  - [ ] Uninstallation

### Security Hardening
- [ ] **Firewall rules**
  - [ ] Only expose Cloudflare tunnel
  - [ ] Block direct port access (5000, 2283, 8001)
  - [ ] UFW/iptables configuration
- [ ] **Docker security scan**
  - [ ] docker scan for vulnerabilities
  - [ ] Update vulnerable images
  - [ ] Security scanning in CI/CD
- [ ] **Dependency vulnerability scan**
  - [ ] pip-audit for Python
  - [ ] npm audit for JavaScript
  - [ ] Snyk integration (optional)
  - [ ] Automated weekly scans
- [ ] **Secret management**
  - [ ] Environment variables (not hardcoded)
  - [ ] .env file in .gitignore
  - [ ] Cloudflare tunnel credentials secured
  - [ ] API keys rotation policy
- [ ] **Database file permissions**
  - [ ] 600 (owner read/write only)
  - [ ] Verify backup permissions
- [ ] **Security documentation**
  - [ ] Threat model
  - [ ] Security best practices
  - [ ] Incident response plan

---

## ❌ MISSING - Phase 5: Advanced Features (0%)

**Status**: NOT STARTED
**Priority**: LOW (nice-to-have, not blocking)
**Estimated Effort**: 2-4 weeks (iterative)

### Web Archiving Integration
- [ ] **Embedded browser in desktop app**
  - [ ] Chromium WebView component
  - [ ] Browser controls (back, forward, refresh)
  - [ ] Address bar
  - [ ] Archive button in toolbar
  - [ ] Chrome profile integration
  - [ ] Cookie sharing for authenticated sites
- [ ] **Archive workflow**
  - [ ] Browse to URL in embedded browser
  - [ ] Click "Archive" button
  - [ ] Select location to associate
  - [ ] ArchiveBox API call
  - [ ] Show archive status
  - [ ] Notification on completion
- [ ] **Webhook handler for archive completion**
  - [ ] ArchiveBox → AUPAT Core webhook
  - [ ] Extract media file paths
  - [ ] Upload media to Immich
  - [ ] Update urls table with status
  - [ ] Notify desktop app
- [ ] **High-res Playwright extractors**
  - [ ] Instagram carousel extractor (~200 lines)
  - [ ] Facebook post extractor (~200 lines)
  - [ ] SmugMug original size extractor (~150 lines)
  - [ ] Flickr high-res extractor (~150 lines)
  - [ ] Generic srcset parser (find largest variant)
- [ ] **ArchiveBox configuration optimization**
  - [ ] Disable heavyweight methods (PDF, archive.org)
  - [ ] Enable WARC, screenshot, media extraction
  - [ ] Configure timeouts for complex sites
  - [ ] Set SSL validation off (many abandoned site certs expired)

### AI Address Extraction
- [ ] **OCR pipeline**
  - [ ] Tesseract 5 integration (default)
  - [ ] PaddleOCR integration (optional, better accuracy)
  - [ ] EasyOCR integration (alternative)
  - [ ] Google Cloud Vision API (optional, best accuracy)
  - [ ] User setting to choose OCR engine
- [ ] **LLM pipeline**
  - [ ] Ollama integration
  - [ ] Model selection (llama3.2, mistral, phi-3)
  - [ ] Address parsing prompt engineering
  - [ ] Structured output (JSON with street, city, state, zip)
  - [ ] Confidence scoring (0.0-1.0)
- [ ] **Address parser**
  - [ ] usaddress library integration
  - [ ] Fallback to LLM for complex addresses
  - [ ] Manual review interface for low-confidence
- [ ] **Geocoding**
  - [ ] Nominatim (OpenStreetMap) - default, free
  - [ ] Google Maps Geocoding API (optional, better accuracy)
  - [ ] Mapbox Geocoding API (optional)
  - [ ] User setting to choose geocoding provider
  - [ ] Rate limiting compliance
- [ ] **Batch processing**
  - [ ] Process all images without addresses
  - [ ] Progress UI with pause/resume
  - [ ] Manual review queue for low-confidence results
  - [ ] Approval workflow

### Google Maps Export Processing
- [ ] **KML parser**
  - [ ] Parse Google Timeline export (KML)
  - [ ] Extract locations with GPS
  - [ ] Extract timestamps
  - [ ] Map to AUPAT location types
- [ ] **Screenshot processor**
  - [ ] OCR on Google Maps screenshots
  - [ ] Address extraction via LLM
  - [ ] GPS extraction from image metadata
- [ ] **Import wizard in desktop app**
  - [ ] File picker (select KML or folder)
  - [ ] Preview extracted locations
  - [ ] Conflict resolution (merge vs. create new)
  - [ ] Batch import with progress
  - [ ] Success/error reporting
- [ ] **google_maps_exports table usage**
  - [ ] Track import history
  - [ ] Prevent duplicate imports
  - [ ] Link extracted locations to export

### Performance Optimizations
- [ ] **Desktop app**
  - [ ] Lazy load thumbnails (virtual scrolling)
  - [ ] Web Workers for SHA256 calculation
  - [ ] IndexedDB cache for location data
  - [ ] Code splitting (map, gallery, archive modules)
  - [ ] Bundle size optimization
- [ ] **AUPAT Core**
  - [ ] Database query profiling (EXPLAIN ANALYZE)
  - [ ] Add caching layer (Redis - optional)
  - [ ] Connection pooling for API routes
  - [ ] Async job queue (Celery/RQ for large imports)
- [ ] **Map rendering**
  - [ ] WebGL acceleration
  - [ ] Cluster algorithm optimization
  - [ ] Reduce marker payload size

### User Experience Improvements
- [ ] **Keyboard shortcuts**
  - [ ] Full keyboard navigation
  - [ ] Shortcut reference (Help → Keyboard Shortcuts)
- [ ] **Bulk operations**
  - [ ] Tag multiple locations
  - [ ] Bulk edit (change type, state)
  - [ ] Bulk delete with confirmation
  - [ ] Bulk export (JSON, CSV, KML)
- [ ] **Export features**
  - [ ] Export locations to JSON
  - [ ] Export to CSV
  - [ ] Export to KML (for Google Maps)
  - [ ] Export map markers to GeoJSON
- [ ] **Dark mode**
  - [ ] UI theme toggle
  - [ ] Map style (dark theme for map tiles)
  - [ ] Persist theme preference
- [ ] **Accessibility**
  - [ ] Screen reader support (ARIA labels)
  - [ ] Keyboard navigation
  - [ ] High-contrast mode
  - [ ] Font size settings

### Advanced Search
- [ ] **Full-text search (SQLite FTS5)**
  - [ ] Index location names, addresses, descriptions
  - [ ] Search by AI tags (from Immich)
  - [ ] Fuzzy matching
- [ ] **Filters**
  - [ ] Filter by location type
  - [ ] Filter by date range (added, visited)
  - [ ] Filter by GPS presence
  - [ ] Filter by media count (has photos, has videos)
  - [ ] Filter by state
- [ ] **Saved searches**
  - [ ] Save filter combinations
  - [ ] Quick access to common searches
  - [ ] Shared searches (future multi-user)

---

## WANTED FEATURES (Future Versions)

### Phase 6: Mobile App (v0.2.0)

**Status**: NOT STARTED
**Priority**: LOW (nice-to-have, not critical)
**Estimated Effort**: 8-12 weeks (Flutter) or 2-3 weeks (PWA)

**Option 1: Progressive Web App (PWA)**
- [ ] Service worker for offline support
- [ ] IndexedDB for local data storage
- [ ] Geolocation API for GPS capture
- [ ] Camera API for photo import
- [ ] Add to Home Screen prompt
- [ ] Offline-first architecture
- [ ] WiFi sync when online
- [ ] Limited functionality vs. Flutter

**Option 2: Flutter App**
- [ ] Flutter 3.16+ project setup
- [ ] iOS and Android builds
- [ ] Offline SQLite database (subset of AUPAT Core)
- [ ] flutter_map with MBTiles
- [ ] GPS capture in field
- [ ] Camera integration
- [ ] "Near Me" search (local database)
- [ ] WiFi-based sync to desktop
- [ ] Sync conflict resolution
- [ ] Stripped blog post viewer

**Recommendation**: Try PWA first (2-3 weeks). Only build Flutter if PWA inadequate after 1 month field testing.

### Phase 7: Blog Publishing (v0.3.0)

**Status**: NOT STARTED
**Priority**: LOW (not prioritized by user)
**Estimated Effort**: 2-4 weeks

- [ ] Blog post editor with AI assist
  - [ ] Markdown editor
  - [ ] AI-generated drafts (Ollama + llama3.2)
  - [ ] Image selection from location gallery
  - [ ] Auto-generated captions
- [ ] Static site generator integration
  - [ ] Hugo integration
  - [ ] Automatic site generation from database
  - [ ] Template customization
- [ ] Publishing workflow
  - [ ] One-click publish to GitHub Pages
  - [ ] Social media preview generation
  - [ ] SEO optimization

### Phase 8: Advanced AI (v0.4.0)

**Status**: NOT STARTED
**Priority**: LOW (experimental)
**Estimated Effort**: 4-8 weeks

- [ ] Video frame extraction and OCR
  - [ ] Extract keyframes
  - [ ] Run OCR on frames
  - [ ] Detect addresses/signs
- [ ] Historical timeline generation
  - [ ] Parse documents and photos
  - [ ] Extract dates and events
  - [ ] Generate chronological timeline
- [ ] Duplicate photo detection
  - [ ] Perceptual hashing (pHash, dHash)
  - [ ] Similarity scoring
  - [ ] Merge duplicate locations
- [ ] Automatic categorization
  - [ ] Classify location types via ML
  - [ ] Building condition assessment
  - [ ] Predict building age

### Phase 9: Multi-User (v0.5.0)

**Status**: NOT STARTED
**Priority**: LOW (single-user for now)
**Estimated Effort**: 4-6 weeks

- [ ] User authentication (OAuth, JWT)
- [ ] User management (CRUD)
- [ ] Location permissions (owner, viewer, editor)
- [ ] Shared locations (collaborative editing)
- [ ] Collaborative note-taking
- [ ] Activity feed (who added/edited what)
- [ ] Federation (ActivityPub for cross-instance sharing)

---

## IMPLEMENTATION PRIORITY MATRIX

### CRITICAL (Must Have for v0.1.2 Release)

**Phase 2: Desktop MVP** (4-6 weeks)
1. Electron + Svelte scaffold (Week 1)
2. Map view with clustering (Week 2-3)
3. Gallery + location details (Week 4-5)
4. Import interface (Week 6)
5. Settings page (Week 6)

**Phase 3: Hardening (Minimum)** (1 week)
1. E2E tests for import workflow
2. Basic backup automation script
3. User guide with screenshots

### HIGH (Needed for Production)

**Phase 3: Hardening (Full)** (2-3 weeks)
1. Performance tests (200k markers, 1000 file imports)
2. Security tests (SQL injection, path traversal)
3. Structured logging
4. Backup verification
5. OpenAPI/Swagger docs
6. Admin guide

**Phase 4: Deployment** (1 week)
1. Cloudflare tunnel setup
2. Desktop app packaging (.dmg, .AppImage)
3. Monitoring and alerts
4. Operational runbooks

### MEDIUM (Nice to Have)

**Phase 5: Advanced Features (Initial)** (2-3 weeks)
1. Web archiving with embedded browser
2. High-res Playwright extractors (Instagram, Facebook)
3. Basic address extraction (OCR + LLM)

### LOW (Future Phases)

**Phase 5: Advanced Features (Full)** (2-4 weeks)
1. Google Maps export processing
2. Advanced search with FTS5
3. Bulk operations and export features
4. Dark mode and accessibility

**Phase 6-9: Future Versions**
1. Mobile app (PWA or Flutter)
2. Blog publishing
3. Advanced AI features
4. Multi-user support

---

## RECOMMENDED DEVELOPMENT SEQUENCE

### Weeks 1-6: Phase 2 Desktop MVP

**Week 1: Scaffold**
- [ ] Create Electron + Svelte project structure
- [ ] Configure Vite, electron-builder
- [ ] Set up IPC communication
- [ ] Create API client for AUPAT Core
- [ ] Basic settings persistence
- [ ] Test: App launches and connects to API

**Week 2-3: Map View**
- [ ] Integrate Leaflet (or Mapbox GL)
- [ ] Load markers via /api/map/markers
- [ ] Implement Supercluster clustering
- [ ] Add map controls (zoom, pan)
- [ ] Click marker → show sidebar
- [ ] Test: 200k markers render in < 3 seconds

**Week 4-5: Gallery & Details**
- [ ] Location detail sidebar component
- [ ] Image gallery with Immich thumbnails
- [ ] Lightbox for full-size view
- [ ] Location edit form
- [ ] Create location form
- [ ] Test: Gallery loads 100 thumbnails in < 2 seconds

**Week 6: Import & Settings**
- [ ] Import interface with drag-and-drop
- [ ] Progress tracking UI
- [ ] Settings page (API URLs, preferences)
- [ ] Navigation sidebar and top bar
- [ ] Keyboard shortcuts
- [ ] Test: Import 100 photos successfully

### Weeks 7-8: Phase 3 Hardening (Minimum)

**Week 7: Testing**
- [ ] E2E tests (Playwright)
- [ ] Security tests (basic)
- [ ] Performance test (map with 200k markers)
- [ ] Test: All tests pass

**Week 8: Documentation & Backup**
- [ ] Backup automation script
- [ ] Backup verification test
- [ ] User guide with screenshots
- [ ] Test: Backup/restore works

### Week 9: Phase 4 Deployment

- [ ] Cloudflare tunnel setup and testing
- [ ] Build Mac .dmg installer
- [ ] Build Linux .AppImage
- [ ] Test installers on clean systems
- [ ] Write operational runbooks
- [ ] Test: Remote access works, installers work

### Weeks 10+: Phase 5 Advanced Features (Iterative)

- [ ] Web archiving integration (2-3 weeks)
- [ ] Address extraction pipeline (2-3 weeks)
- [ ] Performance optimizations (1 week)
- [ ] UX improvements (1 week)

---

## SUCCESS CRITERIA

### Phase 2 Complete When:
- [ ] Desktop app launches on Mac and Linux
- [ ] Map displays 200k locations in < 3 seconds
- [ ] Gallery loads 100 thumbnails in < 2 seconds
- [ ] Import 100 photos via drag-and-drop works
- [ ] All CRUD operations functional
- [ ] Settings persist across restarts

### Phase 3 Complete When:
- [ ] 80%+ test coverage (total, including desktop app)
- [ ] All E2E tests pass
- [ ] Performance targets met
- [ ] Backup/restore tested and working
- [ ] Documentation complete (user + admin guides)

### Phase 4 Complete When:
- [ ] Cloudflare tunnel provides remote access
- [ ] Desktop installers work on clean Mac and Linux
- [ ] Monitoring scripts functional
- [ ] 7-day stability test passes (no crashes)

### v0.1.2 Release Ready When:
- [ ] All Phase 2-4 complete
- [ ] User acceptance testing: 1 week daily use without critical issues
- [ ] Zero data loss during testing
- [ ] Performance targets met
- [ ] Security scan passes (no critical vulnerabilities)

---

## CONCLUSION

**Current Status**: Phase 1 Foundation COMPLETE (100%)

**Immediate Next Step**: Begin Phase 2 Desktop MVP (Week 1 scaffold)

**Estimated Time to v0.1.2 Release**: 9-10 weeks from now
- Phase 2: 6 weeks
- Phase 3 (minimum): 1 week
- Phase 4: 1 week
- Testing/refinement: 1-2 weeks

**Critical Path**: Desktop application is the blocker for user-facing functionality. All backend infrastructure (Phase 1) is ready to support the desktop app.

**Architecture Readiness**: ✅ EXCELLENT - Foundation is solid, well-tested, and follows all principles (KISS, BPL, BPA, DRETW, NME). Desktop app can be built with confidence on this foundation.
