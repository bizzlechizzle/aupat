# AUPATOOL v0.1.2 - Verification & Audit Layer

## Purpose

Systematic verification at each development phase ensures correctness, consistency, reliability, and adherence to KISS, BPL, BPA, and FAANG PE principles.

---

## Phase 1 Verification: Foundation

### What to Verify

**Docker Infrastructure:**
- [ ] `docker-compose up` starts all services without errors
- [ ] All services pass health checks within 60 seconds
- [ ] Services restart automatically after host reboot
- [ ] Docker volumes persist data across restarts
- [ ] Services can communicate (AUPAT Core → Immich, ArchiveBox)

**Database Schema:**
- [ ] All tables created with correct columns and types
- [ ] All indexes created (verify with EXPLAIN QUERY PLAN)
- [ ] Foreign keys enforced (test with invalid references)
- [ ] Unique constraints work (test with duplicate inserts)
- [ ] WAL mode enabled (check with `PRAGMA journal_mode`)

**AUPAT Core API:**
- [ ] API responds to health check: `curl http://localhost:5000/api/health`
- [ ] Immich adapter uploads photo successfully
- [ ] ArchiveBox adapter archives URL successfully
- [ ] Import pipeline extracts GPS from EXIF
- [ ] Map markers endpoint returns JSON array

**Immich Integration:**
- [ ] Upload photo via AUPAT Core → Photo appears in Immich UI
- [ ] Thumbnail generation completes (verify in Immich)
- [ ] CLIP AI tagging runs (verify tags in Immich)
- [ ] Retrieve thumbnail URL works
- [ ] SHA256 → immich_asset_id mapping stored correctly

**ArchiveBox Integration:**
- [ ] Archive URL via AUPAT Core → Archive appears in ArchiveBox UI
- [ ] WARC file created in /data/archivebox/
- [ ] Screenshot captured
- [ ] Webhook fires after archive completes

### How to Ensure Correctness

**Automated Verification Script:**
```bash
#!/bin/bash
# scripts/verify_phase1.sh

set -e

echo "=== Phase 1 Verification ==="

# 1. Check Docker services
echo "Checking Docker services..."
docker-compose ps | grep -q "healthy" || { echo "Services not healthy"; exit 1; }

# 2. Check database schema
echo "Checking database schema..."
sqlite3 /data/aupat.db ".schema locations" | grep -q "lat REAL" || { echo "GPS columns missing"; exit 1; }
sqlite3 /data/aupat.db "PRAGMA integrity_check" | grep -q "ok" || { echo "Database corrupt"; exit 1; }

# 3. Test API endpoints
echo "Testing API endpoints..."
curl -f http://localhost:5000/api/health || { echo "API health check failed"; exit 1; }
curl -f http://localhost:2283/api/server-info/ping || { echo "Immich not reachable"; exit 1; }

# 4. Test import pipeline
echo "Testing import pipeline..."
python3 << 'EOF'
import requests
import json

# Create test location
response = requests.post('http://localhost:5000/api/locations', json={
    'loc_name': 'Test Location',
    'loc_type': 'factory'
})
assert response.status_code == 201
loc_uuid = response.json()['loc_uuid']

# Import test photo
response = requests.post('http://localhost:5000/api/import/images', json={
    'loc_uuid': loc_uuid,
    'file_paths': ['tests/fixtures/test.jpg']
})
assert response.status_code == 200
assert response.json()['imported'] == 1

print("Import pipeline works!")
EOF

echo "✓ Phase 1 verification passed!"
```

**Run After Phase 1:**
```bash
chmod +x scripts/verify_phase1.sh
./scripts/verify_phase1.sh
```

### Metrics to Guarantee Success

- Docker Compose startup time: < 60 seconds
- API health check response time: < 1 second
- Import 100 photos: 100% success rate, < 10 minutes
- Database integrity check: PASS
- No Docker restart loops (check with `docker-compose logs`)

---

## Phase 2 Verification: Desktop MVP

### What to Verify

**Desktop App Launch:**
- [ ] App launches on Mac without errors
- [ ] App launches on Linux without errors
- [ ] App connects to AUPAT Core API
- [ ] Settings page loads and persists changes

**Map View:**
- [ ] Map loads with test dataset (1000 locations) in < 3 seconds
- [ ] Markers cluster correctly at low zoom levels
- [ ] Clicking marker shows location details
- [ ] Sidebar displays location metadata
- [ ] Map pans and zooms smoothly (60 FPS)

**Gallery View:**
- [ ] Gallery loads 100 thumbnails in < 2 seconds
- [ ] Thumbnails display correctly (no broken images)
- [ ] Clicking thumbnail opens lightbox
- [ ] Lightbox navigation works (prev/next)
- [ ] Full-resolution image loads on demand

**Import Interface:**
- [ ] Drag-and-drop folder accepted
- [ ] File count displayed before import
- [ ] Progress bar updates during import
- [ ] Results displayed: Imported, duplicates, errors
- [ ] Import completes without crashes

**Location Management:**
- [ ] Create new location form validates inputs
- [ ] Edit location updates database
- [ ] Changes persist after app restart
- [ ] GPS coordinates update on map

### How to Ensure Correctness

**Manual Testing Checklist:**

```markdown
# Desktop App Test Plan

## Launch & Settings
- [ ] Launch app (Mac): No errors in console
- [ ] Launch app (Linux): No errors in console
- [ ] Open Settings, change API URL, save
- [ ] Restart app, verify setting persisted

## Map View
- [ ] Load map with 1000 locations
- [ ] Time to first marker: ____ seconds (target: < 3s)
- [ ] Zoom out: Markers cluster into groups
- [ ] Zoom in: Clusters expand to individual markers
- [ ] Click marker: Sidebar opens within 500ms
- [ ] Sidebar shows: Name, type, address, photo count

## Gallery
- [ ] Open location with 100 photos
- [ ] Gallery load time: ____ seconds (target: < 2s)
- [ ] Scroll gallery: Smooth, no jank
- [ ] Click thumbnail: Lightbox opens
- [ ] Navigate lightbox: Prev/next work
- [ ] Close lightbox: Returns to gallery

## Import
- [ ] Drag folder of 10 photos to import area
- [ ] Select location from dropdown
- [ ] Click "Start Import"
- [ ] Progress bar updates
- [ ] Results show: Imported 10, Duplicates 0, Errors 0
- [ ] Imported photos appear in gallery immediately

## Error Handling
- [ ] Stop AUPAT Core (docker-compose stop aupat-core)
- [ ] App shows error: "API unavailable"
- [ ] Restart AUPAT Core
- [ ] App reconnects automatically
```

**Automated E2E Tests:**
```bash
npm run test:e2e
```

### Metrics to Guarantee Success

- Map load time (1000 locations): < 3 seconds
- Gallery load time (100 thumbnails): < 2 seconds
- Import 100 photos: < 5 minutes, 100% success rate
- Memory usage: < 1 GB with map + gallery open
- Zero crashes during 1-hour stress test

---

## Phase 3 Verification: Hardening + Tests

### What to Verify

**Test Coverage:**
- [ ] AUPAT Core: 80%+ coverage
- [ ] Desktop App: 70%+ coverage
- [ ] All tests pass on Mac and Linux
- [ ] No flaky tests (run suite 10 times)

**Error Handling:**
- [ ] Immich down: Import fails gracefully with error message
- [ ] ArchiveBox down: Archive queued for retry
- [ ] Database corruption: Detected and reported
- [ ] Network timeout: Retries with exponential backoff
- [ ] Disk full: Import stops, error logged

**Backup & Restore:**
- [ ] Daily backup script runs via cron
- [ ] Backup file created in /data/backups/
- [ ] Restore from backup: Database intact
- [ ] Restore from backup: All photos accessible via Immich
- [ ] Restore tested on clean system

**Performance:**
- [ ] 200k locations on map: < 3 seconds
- [ ] Import 1000 photos: < 10 minutes
- [ ] Search query: < 1 second
- [ ] Desktop app runs for 24 hours without memory leaks

**Documentation:**
- [ ] All API endpoints documented (Swagger/OpenAPI)
- [ ] User guide complete (screenshots, workflows)
- [ ] Admin guide complete (installation, troubleshooting)
- [ ] Developer guide complete (architecture, contributing)

### How to Ensure Correctness

**Automated Test Suite:**
```bash
# Run full test suite
pytest tests/ --cov=aupat_core --cov-report=html
npm test
npm run test:e2e

# Check coverage thresholds
pytest tests/ --cov=aupat_core --cov-fail-under=80
```

**Backup Verification:**
```bash
# scripts/verify_backup.sh

# 1. Run backup
./scripts/backup.sh

# 2. Verify backup files exist
test -f /data/backups/aupat_$(date +%Y%m%d).db || exit 1

# 3. Test restore
cp /data/aupat.db /data/aupat.db.original
cp /data/backups/aupat_$(date +%Y%m%d).db /data/aupat.db

# 4. Verify database integrity
sqlite3 /data/aupat.db "PRAGMA integrity_check" | grep -q "ok" || exit 1

# 5. Restore original
mv /data/aupat.db.original /data/aupat.db

echo "✓ Backup verification passed!"
```

### Metrics to Guarantee Success

- Test suite run time: < 10 minutes
- Test coverage: AUPAT Core 80%+, Desktop 70%+
- Backup size: < 500 MB (for 200k images metadata)
- Restore time: < 5 minutes
- Zero critical security vulnerabilities (pip-audit, npm audit)

---

## Phase 4 Verification: Deployment

### What to Verify

**Cloudflare Tunnel:**
- [ ] Tunnel established: `cloudflared tunnel info`
- [ ] DNS records created (aupat.yourdomain.com)
- [ ] Remote access works from mobile device
- [ ] HTTPS certificate valid
- [ ] No unauthorized access (test with wrong device)

**Monitoring:**
- [ ] Docker health checks running
- [ ] Disk usage monitoring script installed (cron)
- [ ] Logs rotating (check /var/log/aupat/)
- [ ] Email alerts configured (test by triggering alert)

**Security:**
- [ ] Firewall rules applied (only Cloudflare tunnel exposed)
- [ ] Docker security scan passes
- [ ] Dependency vulnerability scan passes (Snyk)
- [ ] Secrets in environment variables (not hardcoded)
- [ ] Database file permissions: 600 (owner read/write only)

**Desktop App Packaging:**
- [ ] Mac .dmg installer created
- [ ] Linux .AppImage or .deb created
- [ ] Installer tested on clean Mac system
- [ ] Installer tested on clean Linux system
- [ ] Uninstaller works cleanly

### How to Ensure Correctness

**Cloudflare Tunnel Test:**
```bash
# Test from external network (mobile hotspot)
curl -I https://aupat.yourdomain.com/api/health
# Expect: HTTP 200 OK

# Test unauthorized access
curl -I https://aupat.yourdomain.com -H "CF-Access-Client-Id: invalid"
# Expect: HTTP 403 Forbidden (if Cloudflare Access enabled)
```

**Security Scan:**
```bash
# Docker security scan
docker scan aupat-core:latest

# Python dependencies
pip-audit

# JavaScript dependencies
npm audit --audit-level=high

# Expected: 0 high or critical vulnerabilities
```

**Desktop App Installation Test:**
```bash
# Mac
hdiutil attach aupat-v0.1.2-mac.dmg
cp -R /Volumes/AUPAT/AUPAT.app /Applications/
open /Applications/AUPAT.app
# Verify: App launches without security warnings

# Linux
chmod +x aupat-v0.1.2-linux.AppImage
./aupat-v0.1.2-linux.AppImage
# Verify: App launches, connects to API
```

### Metrics to Guarantee Success

- Cloudflare tunnel uptime: 99.9%+ (monitor for 1 week)
- Remote access latency: < 500ms from anywhere in US
- Security scan: 0 critical vulnerabilities
- Installer size: Mac < 200 MB, Linux < 150 MB
- Clean install success rate: 100% (test on 3 machines)

---

## Phase 5 Verification: Optimization + Automation

### What to Verify

**Web Archiving:**
- [ ] Embedded browser loads pages
- [ ] Archive button triggers ArchiveBox
- [ ] Chrome cookies shared (test with Facebook login)
- [ ] Media extraction works (Instagram carousel)
- [ ] Extracted media uploaded to Immich
- [ ] Webhook updates archive status

**AI Address Extraction:**
- [ ] OCR extracts text from test images (90%+ accuracy)
- [ ] LLM parses addresses from OCR text (90%+ precision)
- [ ] Geocoding converts addresses to GPS (95%+ success rate)
- [ ] Low-confidence results flagged for manual review
- [ ] Batch processing completes without crashes

**Google Maps Export:**
- [ ] KML parser extracts locations
- [ ] Screenshot processor extracts addresses via OCR
- [ ] Import wizard shows preview before import
- [ ] Conflict resolution merges with existing locations
- [ ] Import completes with 90%+ success rate

### How to Ensure Correctness

**Web Archiving Test:**
```bash
# Manual test
1. Open desktop app
2. Navigate to Archive tab
3. Browse to: https://www.instagram.com/p/example/
4. Click "Archive" button
5. Verify: Status changes to "Archiving..."
6. Wait 60 seconds
7. Verify: Status changes to "Archived"
8. Verify: Extracted images appear in location gallery
```

**AI Extraction Test:**
```python
# tests/integration/test_address_extraction.py
def test_address_extraction_accuracy():
    test_images = [
        ('tests/fixtures/sign1.jpg', '123 Main St, Albany, NY 12203'),
        ('tests/fixtures/sign2.jpg', '456 Factory Rd, Troy, NY 12180'),
        # ... 20 test images with known addresses
    ]

    extractor = AddressExtractor()
    correct = 0
    total = len(test_images)

    for img_path, expected_address in test_images:
        result = extractor.extract_from_image(img_path)
        if result['confidence'] > 0.7:
            extracted = f"{result['street']}, {result['city']}, {result['state']} {result['zip']}"
            if extracted == expected_address:
                correct += 1

    accuracy = correct / total
    assert accuracy >= 0.85, f"Accuracy {accuracy:.2%} below target 85%"
```

### Metrics to Guarantee Success

- Archive success rate: 95%+ (test with 20 URLs)
- Archive time: < 2 minutes per URL (average)
- OCR accuracy: 85%+ on clear text
- Address extraction precision: 90%+ (few false positives)
- Google Maps export: 90%+ locations imported successfully

---

## Cross-Phase Verification: KISS, BPL, BPA, FAANG PE

### KISS Verification

**Checklist:**
- [ ] No Kubernetes (Docker Compose only)
- [ ] No custom message queue (webhooks sufficient)
- [ ] No microservice orchestration (simple REST APIs)
- [ ] No unnecessary abstractions (direct SQL, not ORM)
- [ ] Configuration in single file (docker-compose.yml)

**How to Check:**
- Count files in project: < 100 source files (excluding node_modules)
- Count Docker services: ≤ 10
- Count lines of custom code: < 10,000 (excluding tests, generated code)

### BPL Verification

**Checklist:**
- [ ] All Docker images pinned to specific versions (no :latest)
- [ ] Database migrations use Alembic (versioned, reversible)
- [ ] Adapters abstract external services (easy to swap)
- [ ] Backup and restore procedures documented and tested
- [ ] Security updates have clear update path

**How to Check:**
- Review docker-compose.yml: All images have version tags
- Check Alembic migrations: All up/down functions implemented
- Test: Swap Immich adapter with mock → no code changes needed
- Test: Restore from 1-year-old backup → works without migration

### BPA Verification

**Checklist:**
- [ ] Latest stable Python (3.11+), Node.js (20+)
- [ ] Latest Flask (3.x), Electron (28+), Svelte (4+)
- [ ] Follow official documentation for all tools
- [ ] Use standard project structure (src/, tests/, docs/)
- [ ] Code style: Black (Python), ESLint (JavaScript)

**How to Check:**
- Run `python --version`, `node --version`: Check >= minimum
- Run `pip list`, `npm list`: Check >= minimum versions
- Run `black --check .`, `eslint .`: Zero style violations
- Review project structure: Matches industry standards

### FAANG PE Verification

**Checklist:**
- [ ] Test coverage: 80%+ for core, 70%+ for UI
- [ ] Performance targets met (see Phase 3 metrics)
- [ ] Error handling: Graceful degradation, meaningful messages
- [ ] Monitoring: Health checks, logging, alerts
- [ ] Documentation: Architecture, API, user guide, runbooks

**How to Check:**
- Run coverage report: Check percentages
- Run performance tests: Check all targets met
- Simulate service failures: No crashes, clear error messages
- Review logs: Structured, parseable, helpful for debugging
- Review docs: Complete, up-to-date, understandable by new contributor

---

## DRETW Verification

**For each major component, verify:**

1. **Did we evaluate existing tools?**
   - Immich vs. PhotoPrism vs. Custom: ✓ Chose Immich
   - ArchiveBox vs. Heritrix vs. Custom: ✓ Chose ArchiveBox
   - Electron vs. Tauri vs. Native: ✓ Chose Electron

2. **Did we avoid reinventing?**
   - Photo storage: ✓ Using Immich (not building custom)
   - Web archiving: ✓ Using ArchiveBox (not building custom)
   - OCR: ✓ Using Tesseract/PaddleOCR (not training custom model)
   - Map clustering: ✓ Using Supercluster library

3. **Could we use existing code?**
   - Import pipeline: ✓ Building on existing db_import.py
   - Database schema: ✓ Extending existing schema (not rewriting)
   - EXIF extraction: ✓ Using exiftool library

**How to Check:**
- Review project dependencies: Are we using mature, well-maintained libraries?
- Review custom code: Is any custom code duplicating functionality of known libraries?
- Search GitHub: For each feature, did we search for existing implementations?

---

## Final Audit Before v0.1.2 Release

### Completeness Audit

**Core Features:**
- [ ] Import photos to Immich: WORKING
- [ ] Extract GPS from EXIF: WORKING
- [ ] Map view with 200k locations: WORKING
- [ ] Gallery view with thumbnails: WORKING
- [ ] Location management (CRUD): WORKING
- [ ] Web archiving (basic): WORKING
- [ ] AI address extraction: WORKING
- [ ] Google Maps export processing: WORKING

**Documentation:**
- [ ] README.md: Installation, usage, troubleshooting
- [ ] API documentation: All endpoints documented
- [ ] User guide: Screenshots, workflows
- [ ] Admin guide: Docker, backups, monitoring
- [ ] Architecture docs: This document set

**Testing:**
- [ ] Unit tests: 80%+ coverage
- [ ] Integration tests: All pass
- [ ] E2E tests: All pass
- [ ] Performance tests: Targets met
- [ ] Security scans: Zero critical issues

**Deployment:**
- [ ] Docker Compose: One-command startup
- [ ] Cloudflare tunnel: Remote access works
- [ ] Desktop installers: Mac and Linux
- [ ] Backup scripts: Automated, tested
- [ ] Monitoring: Health checks, alerts

### Quality Audit

**Code Quality:**
- [ ] No hardcoded secrets (API keys, passwords)
- [ ] No TODOs or FIXMEs in main branch
- [ ] All functions have docstrings
- [ ] All complex logic has comments
- [ ] Consistent code style (Black, ESLint)

**User Experience:**
- [ ] No confusing error messages
- [ ] All buttons have clear labels
- [ ] Loading states displayed (spinners)
- [ ] Success/failure feedback shown
- [ ] Keyboard shortcuts documented

**Reliability:**
- [ ] No known crashes
- [ ] No data loss scenarios
- [ ] Graceful degradation when services down
- [ ] Auto-recovery where possible
- [ ] Clear logs for debugging

### Release Checklist

- [ ] All verification scripts pass
- [ ] All tests pass on Mac and Linux
- [ ] Performance benchmarks met
- [ ] Security scans clear
- [ ] Documentation complete and reviewed
- [ ] Backup/restore tested
- [ ] User acceptance testing: 1 week of daily use without critical issues
- [ ] Tag release in Git: `git tag v0.1.2`
- [ ] Build release packages (Mac .dmg, Linux .AppImage)
- [ ] Update CHANGELOG.md
- [ ] Deploy to production (your personal instance)
- [ ] Monitor for 7 days: No critical issues

---

## Ongoing Verification (Post-Release)

### Monthly Health Check

```bash
# scripts/monthly_health_check.sh

echo "=== AUPAT Monthly Health Check ==="

# 1. Check services
docker-compose ps | grep -q "healthy" || echo "⚠ Services unhealthy"

# 2. Check disk space
df -h /data | awk 'NR==2 {print $5}' | grep -q '^[0-7][0-9]%' || echo "⚠ Disk > 80%"

# 3. Check database integrity
sqlite3 /data/aupat.db "PRAGMA integrity_check" | grep -q "ok" || echo "⚠ Database corrupt"

# 4. Check backup freshness
find /data/backups -name "aupat_*.db" -mtime -7 -print | grep -q . || echo "⚠ No recent backups"

# 5. Check for security updates
pip list --outdated | grep -q "Flask\|requests" && echo "⚠ Security updates available"
npm outdated | grep -q "electron\|svelte" && echo "⚠ Security updates available"

# 6. Test basic functionality
curl -f http://localhost:5000/api/health || echo "⚠ API health check failed"

echo "=== Health check complete ==="
```

**Schedule via cron:**
```bash
0 9 1 * * /path/to/scripts/monthly_health_check.sh | mail -s "AUPAT Health Report" user@example.com
```

### Quarterly Deep Audit

- Run full test suite
- Review logs for warnings/errors
- Check database size growth (project trends)
- Review disk usage (prune old archives if needed)
- Update dependencies (patch versions only)
- Review documentation for accuracy
- Test disaster recovery (restore from backup)

---

## Success Metrics Summary

| Phase | Key Metric | Target |
|-------|------------|--------|
| 1 | Import 100 photos | < 10 min, 100% success |
| 2 | Map load (200k locations) | < 3 seconds |
| 2 | Gallery load (100 thumbnails) | < 2 seconds |
| 3 | Test coverage | 80%+ core, 70%+ UI |
| 3 | Backup/restore | < 5 minutes |
| 4 | Cloudflare tunnel uptime | 99.9%+ |
| 4 | Security vulnerabilities | 0 critical |
| 5 | Archive success rate | 95%+ |
| 5 | OCR accuracy | 85%+ |

All metrics must be met before declaring phase complete.
