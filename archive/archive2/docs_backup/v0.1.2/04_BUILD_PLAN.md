# AUPATOOL v0.1.2 - Step-By-Step Build Plan

## Phase 1: Foundation (2-3 Weeks)

### Goal
Establish Docker infrastructure, enhance database schema, integrate Immich and ArchiveBox with AUPAT Core.

### Exact Deliverables

1. **Docker Compose Infrastructure**
   - Single docker-compose.yml for all services
   - AUPAT Core (Flask)
   - Immich (server + ML + PostgreSQL + Redis)
   - ArchiveBox
   - Volume mappings for persistent data
   - Health checks for all services
   - Restart policies

2. **Database Schema Enhancements**
   - Add GPS fields (lat, lon, gps_source, gps_confidence)
   - Add address fields (street_address, city, state, zip_code, country)
   - Add Immich integration (immich_asset_id in images/videos)
   - Add ArchiveBox integration (archivebox_snapshot_id, archive_status)
   - Add enhanced metadata (dimensions, file sizes, GPS per image/video)
   - Create indexes for performance
   - Alembic migration scripts

3. **AUPAT Core API Enhancements**
   - Immich adapter class (upload, get_thumbnail_url, get_original_url)
   - ArchiveBox adapter class (archive_url, get_status, webhook_handler)
   - Enhanced import pipeline with Immich uploads
   - GPS extraction from EXIF
   - API endpoints for map markers (/api/map/markers)

4. **Import Pipeline Updates**
   - Modify db_import.py to upload photos to Immich
   - Store SHA256 → immich_asset_id mapping
   - Extract GPS from EXIF and update locations table
   - Calculate image dimensions and file sizes

5. **Verification**
   - Import test set of 100 photos
   - Verify photos appear in Immich
   - Verify SHA256 mapping in AUPAT database
   - Test GPS extraction
   - Test API endpoints return correct data

### Lifetime Considerations (BPL)
- Pin all Docker image versions (no :latest tags)
- Document version numbers in docker-compose.yml
- Use Alembic for schema migrations (never manual ALTER TABLE)
- Abstract Immich/ArchiveBox behind adapter interfaces (easy to swap later)

### Dependencies
- Docker 24+ and Docker Compose V2
- Existing AUPAT codebase (Flask app, scripts)
- Test dataset (100-1000 photos for validation)

### Potential Blockers
- Immich PostgreSQL conflicts if PostgreSQL already running on host
  - Mitigation: Use Docker networks, map to non-standard ports
- Disk space for Immich + ArchiveBox
  - Mitigation: Monitor setup, warn if < 100 GB free
- GPU not detected by Immich ML container
  - Mitigation: Test CUDA in container, fall back to CPU if needed

### KISS Simplification Checks
- No Kubernetes (Docker Compose only)
- No separate auth service yet (single-user, localhost)
- No message queue (simple HTTP webhooks)
- No real-time sync (polling/webhooks sufficient)

### DRETW Checks
- Use official Immich Docker images (don't build custom)
- Use official ArchiveBox Docker images
- Use Alembic for migrations (standard Python tool)
- Follow Immich API docs exactly (don't guess endpoints)

---

## Phase 2: Desktop MVP (4-6 Weeks)

### Goal
Build Electron desktop app with map view, gallery view, location management, and basic import interface.

### Exact Deliverables

1. **Electron Application Scaffold**
   - Electron 28+ with Svelte 4+ frontend
   - Main process (Node.js): API client, filesystem access
   - Renderer process (Svelte): UI components
   - Preload script for secure IPC
   - Build configuration (electron-builder for Mac/Linux)

2. **Map View**
   - Leaflet.js integration
   - Supercluster for marker clustering
   - Load all locations via /api/map/markers
   - Cluster rendering (show counts at low zoom)
   - Click marker → show location details sidebar
   - Default to Albany, NY region (user's area)

3. **Location Detail View**
   - Sidebar displays when marker clicked
   - Show location metadata (name, type, address, GPS)
   - Gallery of photos (Immich thumbnails via /api/asset/{id}/thumbnail)
   - Click thumbnail → full-screen lightbox (Immich original)
   - List of archived URLs
   - Edit button → location edit form

4. **Location Management**
   - List view (alternative to map): All locations in table
   - Create new location form
   - Edit location form (update name, type, address, GPS)
   - Manual GPS entry (click map to set coordinates)
   - Delete location (soft delete, future)

5. **Import Interface**
   - Drag-and-drop folder of photos
   - Select destination location (dropdown)
   - Show import progress (X of Y processed)
   - Display results: Imported, duplicates, errors
   - Option: Auto-extract GPS from photos

6. **Settings Page**
   - API URLs (AUPAT, Immich, ArchiveBox)
   - Chrome profile path (for future archiving)
   - Map default center and zoom
   - Enable/disable features

7. **Basic Navigation**
   - Sidebar menu: Map, Locations, Import, Settings
   - Top bar: Search (future), notifications

### Lifetime Considerations (BPL)
- Abstract map library behind interface (easy to swap Leaflet for Mapbox later)
- Use SvelteKit routing (stable, standard)
- Modular components (easy to refactor)
- Settings in localStorage (simple, adequate for desktop)

### Dependencies
- Phase 1 complete (Docker services running)
- Node.js 20+ LTS
- Electron build tools (electron-builder)
- Test dataset imported in Phase 1

### Potential Blockers
- Supercluster performance with 200k markers
  - Mitigation: Test with full dataset, optimize zoom levels
- Immich thumbnail API rate limiting
  - Mitigation: Implement client-side caching, lazy loading
- Electron app size (150+ MB)
  - Mitigation: Expected for Electron, acceptable for desktop app

### KISS Simplification Checks
- No custom styling library (use Tailwind CSS)
- No complex state management (Svelte stores sufficient)
- No unnecessary animations (fast > flashy)
- No premature optimization (profile before optimizing)

### DRETW Checks
- Use Supercluster library (don't write custom clustering)
- Use PhotoSwipe or similar for lightbox (don't build custom)
- Use Svelte components from community (buttons, forms, etc.)
- Follow Electron security best practices guide

---

## Phase 3: Hardening + Tests (2-3 Weeks)

### Goal
Comprehensive testing, error handling, backup automation, and documentation.

### Exact Deliverables

1. **AUPAT Core Tests**
   - Unit tests for API endpoints (pytest)
   - Test Immich adapter (mock API responses)
   - Test ArchiveBox adapter
   - Test import pipeline with sample data
   - Test GPS extraction
   - Test database queries (search, filter, map markers)
   - Coverage target: 80%+

2. **Desktop App Tests**
   - Unit tests for API client (Jest)
   - Component tests for UI (Svelte Testing Library)
   - Integration tests: Map loading, location detail, import
   - E2E tests with Playwright (full user workflows)
   - Test on both Mac and Linux

3. **Error Handling**
   - AUPAT Core: Graceful handling of Immich/ArchiveBox downtime
   - Desktop app: Show meaningful error messages
   - Import pipeline: Handle corrupt files, network errors
   - Database: Catch constraint violations, rollback transactions
   - Logging: Structured logs to /data/logs/

4. **Backup Automation**
   - Daily SQLite backup script (rsync to /data/backups/)
   - Git commit of database after imports (version history)
   - Weekly Immich photo backup (rsync to external drive)
   - Backup verification (restore test quarterly)
   - Document restore procedure

5. **Performance Testing**
   - Load test: 200k locations on map
   - Import test: 1000 photos
   - Database query test: Search with 100k records
   - Memory leak test: Desktop app runs for 24 hours
   - Identify and fix bottlenecks

6. **Documentation**
   - Architecture diagrams (Mermaid)
   - API documentation (Swagger/OpenAPI)
   - User guide for desktop app
   - Admin guide (Docker, backups, troubleshooting)
   - Developer guide (contributing, testing)

### Lifetime Considerations (BPL)
- Automated tests prevent regressions during future updates
- Backup procedures tested and documented (disaster recovery)
- Performance baselines established (detect degradation)
- Documentation enables future contributors

### Dependencies
- Phase 2 complete (desktop app functional)
- Test datasets (small, medium, large)
- External backup drive for testing restore

### Potential Blockers
- Tests uncover major bugs
  - Mitigation: Budget time to fix issues found
- Performance targets not met
  - Mitigation: Profile, optimize, or adjust targets
- Backup space insufficient
  - Mitigation: Warn early, implement pruning strategy

### KISS Simplification Checks
- Use pytest (standard Python testing)
- Use Jest (standard JavaScript testing)
- Don't over-engineer backup (rsync + git is sufficient)
- Don't build custom monitoring (Docker health checks sufficient for now)

### DRETW Checks
- Use pytest-cov for coverage reports
- Use Playwright for E2E (industry standard)
- Use rclone for backups if need cloud sync (don't build custom)
- Follow 12-factor app principles (logs, config, backups)

---

## Phase 4: Full Deployment (1 Week)

### Goal
Production-ready deployment with Cloudflare tunnel, monitoring, and operational procedures.

### Exact Deliverables

1. **Cloudflare Tunnel Setup**
   - Install cloudflared on host
   - Create tunnel for AUPAT Core (aupat.yourdomain.com)
   - Create tunnel for Immich (photos.yourdomain.com)
   - Optional: Tunnel for ArchiveBox (archive.yourdomain.com)
   - Test remote access from mobile device
   - Document setup procedure

2. **Monitoring & Alerts**
   - Docker health checks for all services
   - Disk usage monitoring script (alert at 80%)
   - Log rotation (logrotate)
   - Simple uptime monitoring (cron + curl)
   - Email alerts for critical issues (optional)

3. **Operational Runbooks**
   - Startup procedure (docker-compose up)
   - Shutdown procedure (graceful stop)
   - Update procedure (pull new images, test, deploy)
   - Backup procedure (manual and automated)
   - Restore procedure (from backup)
   - Troubleshooting guide (common issues)

4. **Security Hardening**
   - Firewall rules (only expose Cloudflare tunnel)
   - Docker security scan (docker scan)
   - Dependency vulnerability scan (Snyk or similar)
   - Secret management (environment variables, not hardcoded)
   - Document security model

5. **Desktop App Packaging**
   - Build Mac .dmg installer
   - Build Linux .AppImage or .deb
   - Sign binaries (Mac: codesign, Linux: GPG)
   - Test installation on clean systems
   - Document install procedure

### Lifetime Considerations (BPL)
- Cloudflare tunnel is stable, long-term solution
- Monitoring catches issues before user notices
- Runbooks enable fast recovery from failures
- Security hardening prevents common attacks

### Dependencies
- Phase 3 complete (tested, stable)
- Cloudflare account with domain
- Code signing certificates (Mac)

### Potential Blockers
- Cloudflare tunnel configuration issues
  - Mitigation: Follow official Cloudflare docs, test early
- Code signing requires Apple Developer account ($99/year)
  - Mitigation: Can skip for personal use, add later for distribution

### KISS Simplification Checks
- No complex monitoring (Prometheus/Grafana overkill)
- No automated deployment (single-user, manual is fine)
- No CI/CD pipeline yet (add in future for multi-user version)

### DRETW Checks
- Use cloudflared official tool (don't build custom tunnel)
- Use logrotate (standard Linux tool)
- Use electron-builder for packaging (standard Electron tool)
- Follow Cloudflare tunnel best practices guide

---

## Phase 5: Optimization + Automation (Ongoing)

### Goal
Continuous improvements, advanced features, and user experience enhancements.

### Exact Deliverables

1. **Web Archiving Integration**
   - Embedded browser in desktop app (Chromium WebView)
   - Archive button in browser toolbar
   - Chrome profile integration (share cookies for login)
   - ArchiveBox API calls from desktop app
   - Webhook handler for archive completion
   - Auto-import extracted media to Immich
   - High-res Playwright extractors for Instagram, Facebook, SmugMug

2. **Address Extraction (AI)**
   - OCR pipeline (Tesseract or PaddleOCR)
   - LLM pipeline (Ollama + llama3.2)
   - Address parser (OCR → LLM → structured data)
   - Geocoding (Nominatim or Google Maps API)
   - Batch processing for existing images
   - Manual review interface for low-confidence extractions

3. **Google Maps Export Processing**
   - KML parser for Google Timeline exports
   - Screenshot processor (extract addresses via OCR)
   - Import wizard in desktop app
   - Preview extracted locations before import
   - Conflict resolution (merge with existing locations)

4. **Performance Optimizations**
   - Desktop app: Lazy load thumbnails (virtual scrolling)
   - Desktop app: Web Workers for SHA256 calculation
   - Desktop app: IndexedDB cache for location data
   - AUPAT Core: Database query optimization (EXPLAIN ANALYZE)
   - AUPAT Core: Add caching layer (Redis, optional)

5. **User Experience Improvements**
   - Keyboard shortcuts (Cmd+F for search, etc.)
   - Bulk operations (tag multiple locations, bulk edit)
   - Export features (JSON, CSV, KML)
   - Dark mode (UI theme)
   - Accessibility (screen reader support, ARIA labels)

6. **Advanced Search**
   - Full-text search (FTS5 in SQLite)
   - Filter by location type, date range, GPS bounds
   - Search by AI tags (from Immich)
   - Saved searches (bookmarks)

7. **Mobile App Foundation (If Time)**
   - Flutter project scaffold
   - Design offline database schema
   - Prototype map view with MBTiles
   - Prototype location list
   - Test GPS capture
   - Design sync protocol

### Lifetime Considerations (BPL)
- Modular features can be added/removed without breaking core
- Optimization baselines established in Phase 3 (measure improvements)
- Future mobile app uses same API (consistent architecture)

### Dependencies
- Phases 1-4 complete (stable foundation)
- AI services set up (Ollama, OCR)
- Test data for address extraction

### Potential Blockers
- Embedded browser security issues
  - Mitigation: Sandbox, Content Security Policy
- OCR accuracy insufficient
  - Mitigation: Test multiple OCR engines, allow manual entry
- Performance optimization yields minimal gains
  - Mitigation: Measure first, optimize only if needed

### KISS Simplification Checks
- Don't optimize prematurely (Phase 3 profiling guides Phase 5 work)
- Don't add features user doesn't need (focus on address extraction)
- Don't over-engineer AI (simple OCR + LLM sufficient)

### DRETW Checks
- Use existing Playwright scripts for web scraping (search GitHub)
- Use existing KML parser libraries (don't write custom)
- Use Nominatim for free geocoding (or Geocodio for better accuracy)
- Study existing address parsing libraries (usaddress, libpostal)

---

## Phase-by-Phase Summary Table

| Phase | Duration | Focus                    | Key Deliverables                          | Success Criteria                          |
|-------|----------|--------------------------|-------------------------------------------|-------------------------------------------|
| 1     | 2-3 wks  | Foundation               | Docker, Database, API integrations        | Import 100 photos to Immich successfully  |
| 2     | 4-6 wks  | Desktop MVP              | Electron app, Map, Gallery, Import        | View 200k locations on map in <3s         |
| 3     | 2-3 wks  | Hardening + Tests        | Test suite, Error handling, Backups       | 80% test coverage, backup/restore works   |
| 4     | 1 wk     | Deployment               | Cloudflare tunnel, Monitoring, Runbooks   | Remote access works, packaged installers  |
| 5     | Ongoing  | Optimization + Automation| Web archiving, AI extraction, Improvements| Archive 1 URL with media extraction       |

---

## Critical Path Dependencies

```
Phase 1 (Foundation)
    ↓
Phase 2 (Desktop MVP)
    ↓
Phase 3 (Hardening) ← Can start testing earlier parts of Phase 2
    ↓
Phase 4 (Deployment)
    ↓
Phase 5 (Optimization) ← Some features can start during Phase 3
```

**Parallelization Opportunities:**
- Phase 2 + 3: Start writing tests while building features
- Phase 3 + 4: Set up Cloudflare tunnel during testing phase
- Phase 5: AI extraction can be developed independently of web archiving

---

## Risk Mitigation Timeline

**Week 1-2 (Phase 1 Start):**
- Test GPU passthrough to Docker (Immich ML)
- Verify disk space adequate (100+ GB free)
- Test Immich upload/retrieval with sample photos

**Week 3-4 (Phase 1 Complete):**
- Validate entire import pipeline end-to-end
- Checkpoint: Can import 1000 photos? If no, fix before Phase 2

**Week 5-8 (Phase 2 Midpoint):**
- Test map performance with full dataset (200k locations)
- If slow, optimize before building more features

**Week 9-10 (Phase 2 Complete):**
- User acceptance testing (you use the app daily for 1 week)
- Fix critical UX issues before Phase 3

**Week 11-13 (Phase 3):**
- Load testing uncovers performance issues
- Fix before deployment

**Week 14 (Phase 4):**
- Final validation: Restore from backup, test disaster recovery
- Only deploy if restore works perfectly

---

## Rollback Plan

If critical issues arise mid-phase:

**Phase 1:** Rollback to existing system (pure Flask web interface)
**Phase 2:** Keep using Phase 1 API via web browser until desktop app stable
**Phase 3:** If tests fail badly, delay Phase 4 until fixed
**Phase 4:** If deployment fails, continue using localhost only (not critical)
**Phase 5:** Features are additive; can disable without breaking core

---

## Definition of Done (Each Phase)

**Phase 1:**
- [ ] All Docker services start with `docker-compose up`
- [ ] Health checks pass for all services
- [ ] Import 100 photos, verify in Immich and AUPAT database
- [ ] GPS extracted from EXIF, locations have coordinates
- [ ] API returns map markers correctly

**Phase 2:**
- [ ] Desktop app launches on Mac and Linux
- [ ] Map loads with 200k locations in <3 seconds
- [ ] Click location, see photos from Immich
- [ ] Import 100 photos via drag-and-drop
- [ ] Edit location details, changes persist

**Phase 3:**
- [ ] Test suite runs, 80%+ coverage
- [ ] All tests pass
- [ ] Backup script runs, restore tested
- [ ] Documentation complete (API, user guide, admin guide)
- [ ] Performance targets met (see Phase 3 deliverables)

**Phase 4:**
- [ ] Cloudflare tunnel accessible from remote device
- [ ] Desktop app installer works on clean Mac and Linux
- [ ] Monitoring alerts working (test by filling disk to 80%)
- [ ] Runbooks tested (startup, shutdown, restore)

**Phase 5:**
- [ ] Archive 1 URL with media extraction successfully
- [ ] Extract addresses from 10 test images with >80% accuracy
- [ ] Process Google Maps export with >90% success rate
- [ ] User reports workflow improvements (actual use case testing)

---

## Long-Term Roadmap (Beyond v0.1.2)

**v0.2.0: Mobile App**
- Flutter app for iOS and Android
- Offline location catalog
- GPS capture in field
- Photo import via mobile camera
- WiFi sync to desktop

**v0.3.0: Publishing & Sharing**
- Blog post editor with AI assist
- Static site generator integration (Hugo)
- One-click publish to GitHub Pages
- Social media preview generation

**v0.4.0: Advanced AI**
- Video frame extraction and OCR
- Historical timeline generation from documents
- Duplicate photo detection (perceptual hashing)
- Automatic categorization of location types

**v0.5.0: Multi-User (Optional)**
- User authentication (OAuth)
- Location sharing and permissions
- Collaborative note-taking
- Federation (ActivityPub for sharing across instances)

Each version builds on the previous, maintaining BPL principles and backward compatibility.
