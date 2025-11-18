# AUPATOOL v0.1.2 - High-Level Overview

## The Mission

Build a professional-grade abandoned places digital archive system that serves as a personal historian's workstation. The system must catalog 100-200k photos/videos, extract metadata from multiple sources including Google Maps exports, integrate web archiving, and provide both desktop and mobile interfaces for field work and research.

## Core Philosophy

KISS + FAANG PE + BPL + BPA + DRETW

- Microservices architecture using battle-tested open source tools
- SQLite as authoritative database (simple, reliable, portable)
- Immich handles photo storage/serving/AI tagging (DRETW)
- ArchiveBox handles web archiving (DRETW)
- Custom AUPAT Core orchestrates location-centric organization
- Desktop-first for power user workflows
- Mobile-second for field GPS capture
- No vendor lock-in; all data exportable

## Problems We Are Solving

1. Memory decay: Cannot remember all explored locations
2. Media chaos: 100-200k photos across devices/drives with no organization
3. Research bottleneck: Month-long manual research cycles for blog posts
4. Metadata loss: GPS, timestamps, addresses scattered across sources
5. Web ephemeral: Historical research sites disappear or change
6. Field inefficiency: No offline GPS catalog when exploring
7. Scale failure: Current web interface cannot handle 200k photos efficiently

## Why This Strategy Is Superior

### Over Pure Web App
- Embedded browser for web archiving (impossible in web)
- Native filesystem access for bulk imports (10k+ photos at once)
- Efficient map rendering with 200k clustered markers
- Desktop performance for ML/AI processing on 3090 GPU

### Over Monolithic Desktop App
- Modular: Swap Immich/ArchiveBox if better tools emerge
- Remote access via Cloudflare tunnel (Docker services)
- Mobile app shares same API/database
- Updates don't require full reinstall

### Over Custom Photo Manager
- Immich is production-ready with 200k+ photo scalability
- CLIP AI tagging built-in and GPU-optimized
- Mobile apps already exist (iOS/Android)
- Active development community (BPL consideration)

### Over Manual Web Archiving
- ArchiveBox handles WARC + screenshots + media extraction
- Playwright integration for login-protected sites (Facebook, Instagram)
- Automated extraction pipeline
- Proper WARC preservation standards

## What This Pivot Leaves Behind

### From Old Plan (Stage 1-4 JSON-based system)
- ~~Pure Flask web interface as primary UI~~ (keeping as API only)
- ~~Manual photo organization~~ (Immich handles storage)
- ~~Basic URL tracking~~ (ArchiveBox handles archiving)
- ~~JSON-based exports~~ (adding proper blog publishing)

### Retaining
- SQLite database schema (core locations/relationships)
- All existing Python scripts (db_import.py, db_organize.py, etc.)
- Content-addressed storage philosophy (SHA256 deduplication)
- Git-based version control of database

### Fresh Start
- No migration of existing organized photos
- Clean Immich import pipeline
- Proper GPS extraction from all sources
- Address extraction via AI from images/videos/Google Maps exports

## What Risks Remain

### Technical Risks
1. Immich API stability: Active development may break integrations
   - Mitigation: Pin to stable releases, abstract API calls behind adapter layer

2. ArchiveBox scalability: Thousands of archived URLs
   - Mitigation: Monitor disk usage, implement archive pruning strategy

3. SQLite concurrent writes: Desktop + Mobile editing simultaneously
   - Mitigation: Desktop is authoritative; mobile sync is append-only with conflict resolution

4. GPU dependency: Immich ML requires CUDA (3090)
   - Mitigation: ML is optional; can run on CPU or disable entirely

5. Docker complexity: Multiple services to manage
   - Mitigation: Comprehensive docker-compose.yml with health checks and restart policies

### Operational Risks
1. Data loss: Single SQLite file corruption
   - Mitigation: Automated backups (git commits + rsync), write-ahead logging (WAL)

2. Network dependency: Cloudflare tunnel for remote access
   - Mitigation: Always works locally; remote access is bonus feature

3. Disk space: 200k photos + videos + WARC archives
   - Mitigation: Monitor with alerts, implement tiered storage strategy

4. Maintenance burden: Multiple tools to update
   - Mitigation: Docker Compose updates, automated dependency updates via Renovate

5. Learning curve: Complex system for single user
   - Mitigation: Comprehensive documentation, one-command setup scripts

### Long-Term Risks
1. Immich project abandonment (3-10 years)
   - Mitigation: SHA256-based storage means photos are not locked in; can migrate to alternative

2. ArchiveBox project abandonment
   - Mitigation: WARC is standard format; can process with other tools

3. Electron security vulnerabilities
   - Mitigation: Regular updates, sandboxed architecture, no remote code execution

4. Python 2-to-3 style breaking changes
   - Mitigation: Pin Python version in Docker, comprehensive test suite

5. Database schema evolution complexity
   - Mitigation: Alembic migrations, versioned schema, backward compatibility

## Success Metrics

Version 0.1.2 is successful when:

1. All existing locations imported with GPS coordinates
2. All 100-200k photos imported to Immich with SHA256 linkage
3. Desktop app displays map with all locations (clustered markers)
4. Click location shows all associated photos via Immich thumbnails
5. Web archiving workflow: Browse URL, click Archive, auto-extracts media
6. Google Maps exports processed: Addresses extracted from images via AI
7. System runs stable for 30 days without crashes
8. Docker Compose one-command startup on Linux and Mac
9. Full backup/restore tested successfully
10. Mobile sync architecture designed (implementation in v0.2.x)

## Timeline Expectations

- Phase 1 (Foundation): 2-3 weeks
- Phase 2 (Desktop MVP): 4-6 weeks
- Phase 3 (Hardening): 2-3 weeks
- Phase 4 (Deployment): 1 week
- Phase 5 (Optimization): Ongoing

Total to production-ready system: 10-14 weeks
