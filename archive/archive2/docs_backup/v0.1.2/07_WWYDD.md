# AUPATOOL v0.1.2 - What Would You Do Differently (WWYDD)

## Honest Critical Evaluation

This document provides brutally honest assessment of architectural decisions, potential improvements, and trade-offs to reconsider.

---

## Architecture: Microservices vs. Monolith

### Decision Made
Microservices: AUPAT Core + Immich + ArchiveBox as separate Docker services

### What I Would Change
**Consider a hybrid approach with tighter integration**

The current microservices architecture is clean but may be over-engineered for single-user use case.

**Alternative Approach:**
- Keep Immich and ArchiveBox as separate services (they're complex, maintain separation)
- BUT: Bundle desktop app with embedded AUPAT Core Flask server
- Desktop app launches Flask server as subprocess on startup
- Eliminates need for user to manage Docker separately
- Simpler deployment: Install desktop app, done

**Why It Matters:**
- Current approach: User must install Docker, run docker-compose, THEN launch desktop app
- Hybrid approach: User installs desktop app, everything works (Docker only for Immich/ArchiveBox)
- Reduces barrier to entry
- Better "just works" experience

**Trade-offs:**
- Hybrid: Less modular (desktop app + API coupled)
- Microservices: More flexible but more complex setup
- For single-user personal tool, simplicity > modularity

**Recommendation:**
- **v0.1.2**: Stick with microservices (cleaner for development)
- **v0.2.0**: Consider bundling API with desktop app for simplified deployment

---

## Database: SQLite vs. PostgreSQL

### Decision Made
SQLite for AUPAT Core metadata

### What I Would Change
**Nothing - SQLite is correct choice**

But add one enhancement: Write-Ahead Logging (WAL) mode + connection pooling.

**Why It Matters:**
- SQLite with WAL handles concurrent reads during writes
- Connection pooling prevents "database locked" errors
- Still single file, but more robust

**Implementation:**
```python
# aupat_core/database.py
def get_db():
    db = sqlite3.connect('data/aupat.db', check_same_thread=False)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=NORMAL')  # Faster writes, still safe
    db.execute('PRAGMA cache_size=10000')   # 10MB cache
    db.execute('PRAGMA foreign_keys=ON')
    return db
```

**Why NOT PostgreSQL:**
- PostgreSQL requires server process (violates KISS)
- Immich already runs PostgreSQL (don't duplicate)
- SQLite can handle 200k locations easily
- SQLite is more portable (single file backup)

**Recommendation:** Keep SQLite, add WAL optimizations

---

## Desktop App: Electron vs. Tauri

### Decision Made
Electron (Chromium + Node.js)

### What I Would Change
**Seriously consider Tauri for v0.2.0**

Electron is the safe choice, but Tauri has compelling advantages:

**Tauri Advantages:**
- Bundle size: 15 MB (Tauri) vs. 150 MB (Electron)
- Memory usage: 50% less than Electron
- Security: Rust-based, sandboxed by default
- Uses system webview (WebKit on Mac, WebView2 on Windows, WebKitGTK on Linux)

**Electron Advantages:**
- Embedded Chromium (consistent browser across platforms)
- Larger ecosystem (more plugins, more examples)
- Easier debugging (Chrome DevTools)

**Why It Matters:**
- For web archiving, having embedded Chromium is valuable (consistent rendering)
- But for main UI, system webview is adequate
- Could use Electron for archiving tab, Tauri for rest (complex)

**Trade-offs:**
- Tauri: Smaller, faster, BUT web archiving harder (no embedded Chromium)
- Electron: Larger, slower, BUT web archiving easier

**Recommendation:**
- **v0.1.2**: Electron (we need embedded browser for archiving)
- **v0.2.0**: Reconsider if web archiving moves to separate tool

**Compromise Approach:**
- Desktop app in Tauri (main UI)
- Separate archiving tool in Electron (or use headless Chromium directly)
- Best of both worlds: Lightweight main app + powerful archiving

---

## Map Library: Leaflet vs. Mapbox GL

### Decision Made
Leaflet (free, open source)

### What I Would Change
**Use Mapbox GL JS from the start**

Leaflet is good, but Mapbox GL is better for 200k markers:

**Mapbox GL Advantages:**
- Vector tiles (smaller download, smoother zoom)
- WebGL rendering (hardware accelerated, faster)
- Better clustering performance
- More modern API

**Leaflet Advantages:**
- Completely free (no API limits)
- Simpler API
- Smaller bundle
- Raster tiles work offline easily

**Why It Matters:**
- With 200k locations, rendering performance is critical
- Mapbox GL handles this better
- Free tier: 50k loads/month (adequate for single user)
- Can download vector tiles for offline use

**Recommendation:**
- Start with Mapbox GL JS (free tier)
- If you exceed free tier (unlikely), fall back to Leaflet
- Abstract map library behind interface (easy to swap)

**Implementation:**
```javascript
// lib/map-adapter.js
class MapAdapter {
  constructor(container, options) {
    // Use Mapbox GL if API key available, else Leaflet
    if (import.meta.env.VITE_MAPBOX_TOKEN) {
      this.map = new mapboxgl.Map({...});
    } else {
      this.map = L.map(container, {...});
    }
  }

  addMarkers(markers) {
    // Adapter translates to specific map library API
  }
}
```

This approach lets user choose: Free (Leaflet) or Performance (Mapbox).

---

## AI Services: Local vs. Cloud

### Decision Made
Local AI (Ollama, Tesseract, PaddleOCR)

### What I Would Change
**Hybrid approach with cloud fallback**

Local AI is great for privacy and cost, but cloud APIs are better at some tasks.

**Hybrid Strategy:**
1. **Default: Local models** (Ollama, Tesseract)
   - Address extraction from images
   - Basic text summarization
   - OCR on documents

2. **Optional: Cloud APIs** (OpenAI, Anthropic) via user API key
   - Complex historical research (Claude Sonnet 4.5 is excellent)
   - High-accuracy OCR (Google Cloud Vision)
   - Image analysis (GPT-4 Vision)

3. **User Controls:**
   - Settings: "Use cloud AI for: [ ] OCR [ ] Summarization [ ] Research"
   - Cost tracking: Show estimated costs based on usage
   - Fallback: If API call fails or budget exceeded, use local model

**Why It Matters:**
- Local models are 80-90% as good for basic tasks
- Cloud models are 99% accurate for complex tasks
- Let user choose based on their priorities (privacy vs. accuracy)

**Implementation:**
```python
# ai_services/providers.py
class AIProvider:
    def extract_address(self, image_path: str) -> dict:
        pass

class LocalProvider(AIProvider):
    def extract_address(self, image_path: str) -> dict:
        # Tesseract + Ollama
        pass

class CloudProvider(AIProvider):
    def extract_address(self, image_path: str) -> dict:
        # Google Cloud Vision + OpenAI
        pass

class HybridProvider(AIProvider):
    def __init__(self, local: LocalProvider, cloud: CloudProvider, user_settings: dict):
        self.local = local
        self.cloud = cloud
        self.settings = user_settings

    def extract_address(self, image_path: str) -> dict:
        # Try local first
        result = self.local.extract_address(image_path)

        # If low confidence and cloud enabled, use cloud
        if result['confidence'] < 0.7 and self.settings['allow_cloud_ocr']:
            result = self.cloud.extract_address(image_path)

        return result
```

**Recommendation:** Implement hybrid AI from the start. Give user choice.

---

## Mobile App: Flutter vs. PWA

### Decision Made
Flutter (native iOS/Android apps)

### What I Would Change
**Try PWA first, then Flutter if limitations hit**

Flutter is powerful but requires significant development effort. PWA might be adequate:

**PWA Advantages:**
- Reuse desktop app code (Svelte components)
- No app store approval process
- Instant updates (no reinstall)
- Works on all platforms (iOS, Android, desktop)

**PWA Limitations:**
- GPS background access limited (iOS especially)
- Offline storage limits (varies by browser)
- No app store presence (harder to discover)
- Camera access more limited

**Flutter Advantages:**
- Full native access (GPS, camera, filesystem)
- Better offline support (full SQLite)
- App store distribution
- Better performance

**Recommendation:**
- **Phase 4.5**: Build PWA prototype (1-2 weeks)
- Test GPS capture, offline functionality, photo import
- If PWA limitations acceptable: Ship PWA, save months of Flutter development
- If PWA insufficient: Build Flutter app as planned

**Why It Matters:**
- PWA could get you 80% there in 20% of the time
- Mobile app is future phase, so less urgency
- KISS principle: Try simpler approach first

---

## Web Archiving: ArchiveBox vs. Custom

### Decision Made
ArchiveBox (DRETW)

### What I Would Change
**Nothing - ArchiveBox is correct choice**

But add one enhancement: **Prioritize extraction over preservation**

ArchiveBox defaults to comprehensive preservation (WARC, PDF, screenshot, HTML, etc.).
For your use case, media extraction is more important than perfect preservation.

**Optimized ArchiveBox Config:**
```python
# archivebox-config.py
# Disable heavyweight preservation methods
SAVE_ARCHIVE_DOT_ORG = False  # Don't submit to Internet Archive
SAVE_PDF = False              # Skip PDF generation (slow)
SAVE_SCREENSHOT = True        # Keep screenshots (useful reference)
SAVE_DOM = False              # Skip DOM snapshot
SAVE_WARC = True              # Keep WARC (standard format)
SAVE_MEDIA = True             # CRITICAL: Extract images/videos

# Focus on extraction
MEDIA_TIMEOUT = 300           # Allow 5 minutes for complex sites
CHECK_SSL_VALIDITY = False    # Many abandoned place sites have expired certs
```

**Custom Extractors Priority:**
1. Instagram (high-res carousel)
2. Facebook (login-protected posts)
3. SmugMug (original size downloads)
4. Flickr (high-res variants)
5. Generic: Find largest srcset variant

**Recommendation:** Configure ArchiveBox for extraction-first workflow

---

## Backup Strategy: Git vs. rsync

### Decision Made
Git commits for version history + rsync for full backups

### What I Would Change
**Add ZFS snapshots or Restic for incremental backups**

Git + rsync works, but lacks:
- Point-in-time recovery (can only restore to commit times)
- Incremental backups (rsync is full copy each time)
- Deduplication (Immich photos are duplicated in backups)

**Better Approach: Restic**

Restic is a modern backup tool with:
- Incremental backups (only changed data)
- Deduplication (same photo stored once)
- Encryption (backup security)
- Cloud backends (B2, S3, etc.)
- Easy restore to any point in time

**Implementation:**
```bash
# scripts/backup_restic.sh
#!/bin/bash

# Initialize Restic repository (once)
restic init --repo /mnt/backup/aupat

# Daily backup
restic backup /data/aupat.db /data/immich /data/archivebox --repo /mnt/backup/aupat

# Automatic retention policy
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --repo /mnt/backup/aupat

# Restore (if needed)
restic restore latest --target /data/restore --repo /mnt/backup/aupat
```

**Why It Matters:**
- Restic backups are smaller (deduplication)
- Restore to any point in time (not just git commit times)
- Works with cloud storage (off-site backups)

**Recommendation:** Add Restic in Phase 4, keep git for database schema version control

---

## Import Pipeline: Synchronous vs. Asynchronous

### Decision Made
Synchronous import (blocks until complete)

### What I Would Change
**Add asynchronous job queue for large imports**

Current approach: User clicks "Import" → blocks desktop app until complete (could be 10 minutes for 1000 photos)

**Better Approach: Celery or RQ job queue**

```python
# aupat_core/tasks.py
from celery import Celery

celery = Celery('aupat', broker='redis://localhost:6379')

@celery.task
def import_images_task(loc_uuid, file_paths):
    for path in file_paths:
        # ... import logic
        # Update progress: task.update_state(state='PROGRESS', meta={'current': i, 'total': len(file_paths)})

# API endpoint:
@app.route('/api/import/images', methods=['POST'])
def import_images():
    task = import_images_task.delay(loc_uuid, file_paths)
    return {'task_id': task.id}, 202  # Accepted

# Desktop app polls for progress:
GET /api/import/status/{task_id}
→ {'state': 'PROGRESS', 'current': 500, 'total': 1000}
```

**Why It Matters:**
- Desktop app doesn't freeze during large imports
- User can continue working (browse map, view locations)
- Progress updates in real-time
- Can cancel long-running imports

**Trade-offs:**
- Adds Redis dependency (violates KISS slightly)
- More complex architecture
- But significantly better UX for large imports

**Recommendation:**
- **v0.1.2**: Synchronous (simpler to build)
- **v0.1.3**: Add Celery for large imports (> 100 photos)

---

## Testing: Unit Tests vs. Property-Based Tests

### Decision Made
Traditional unit tests (pytest, Jest)

### What I Would Add
**Property-based testing with Hypothesis**

Property-based testing generates random inputs to find edge cases you didn't think of.

**Example:**
```python
from hypothesis import given
from hypothesis.strategies import floats

@given(lat=floats(min_value=-90, max_value=90), lon=floats(min_value=-180, max_value=180))
def test_gps_parsing_never_crashes(lat, lon):
    # This test runs 100 times with random GPS coordinates
    result = parse_gps({'lat': lat, 'lon': lon})
    assert isinstance(result, tuple) or result is None  # Never crashes, always returns valid type
```

Hypothesis would find edge cases like:
- GPS coordinate exactly 0.0 (might be missing data)
- GPS at extreme values (90, -180)
- NaN or infinity values

**Why It Matters:**
- Finds bugs traditional tests miss
- Especially valuable for parsing untrusted input (EXIF, user input, OCR)

**Recommendation:** Add Hypothesis tests for:
- GPS parsing
- Address extraction
- EXIF parsing
- File validation

---

## Security: No Auth vs. Cloudflare Access

### Decision Made
No authentication in v0.1.2 (single-user, localhost or Cloudflare tunnel)

### What I Would Add Immediately
**Cloudflare Access for zero-trust remote access**

Current plan: Cloudflare tunnel exposes services to internet.
Risk: If tunnel URL leaks, anyone can access your AUPAT instance.

**Better: Cloudflare Access**

Cloudflare Access adds authentication layer:
- Login via Google, GitHub, or email
- Only authorized users can access tunnel URLs
- Zero-trust: Verify on every request

**Setup:**
```bash
# Enable Cloudflare Access
cloudflared access login

# Add authentication to tunnel
# cloudflare dashboard → Zero Trust → Access → Applications
# Create application: aupat.yourdomain.com
# Add policy: Allow email = your@email.com
```

Now, accessing https://aupat.yourdomain.com requires login.

**Why It Matters:**
- Prevents unauthorized access if URL leaks
- No code changes needed (Cloudflare handles auth)
- Free tier: 50 users (way more than needed)

**Recommendation:** Set up Cloudflare Access in Phase 4 deployment

---

## Final Recommendations Summary

### High Priority Changes

1. **Add Mapbox GL JS** (instead of Leaflet)
   - Better performance for 200k markers
   - Fallback to Leaflet if free tier exceeded

2. **Add Cloudflare Access** (instead of no auth)
   - Security improvement with zero code changes
   - Prevents unauthorized access to remote instance

3. **Configure ArchiveBox for extraction priority**
   - Disable heavyweight preservation features
   - Focus on media extraction (your use case)

4. **Add Restic for backups** (supplement git/rsync)
   - Incremental backups, deduplication, point-in-time recovery

5. **Optimize SQLite with WAL mode**
   - Better concurrent access
   - Faster writes

### Medium Priority Improvements (v0.1.3+)

6. **Add async job queue** (Celery/RQ)
   - Better UX for large imports
   - Non-blocking desktop app

7. **Hybrid AI provider** (local + cloud)
   - Give user choice between privacy and accuracy

8. **Property-based testing** (Hypothesis)
   - Find edge cases in parsing logic

### Low Priority (v0.2.0+)

9. **Bundle AUPAT Core with desktop app**
   - Simpler deployment (no separate Docker for API)

10. **Consider Tauri for main UI** (keep Electron for archiving)
    - Smaller bundle, better performance

11. **Try PWA before Flutter**
    - Might be adequate, saves months of development

---

## What NOT to Change

### Keep These Decisions:

1. **SQLite (not PostgreSQL)**: Simpler, portable, adequate for scale
2. **Docker Compose (not Kubernetes)**: KISS, single-user doesn't need orchestration
3. **Immich (not custom photo manager)**: DRETW, saves 6-12 months development
4. **ArchiveBox (not custom archiving)**: DRETW, mature solution
5. **Microservices (vs. monolith)**: Cleaner separation, easier to maintain
6. **Flask (not FastAPI)**: Async not needed for single-user, Flask is simpler

These decisions are sound and align with KISS, BPL, BPA, DRETW principles.

---

## Controversial Opinion: Skip Mobile App Entirely

**Radical suggestion:** Don't build mobile app at all. Here's why:

**Alternative: Progressive Web App + Cloudflare Access**
- Access AUPAT from mobile browser via https://aupat.yourdomain.com
- PWA provides offline mode (service workers, IndexedDB)
- Camera API works in mobile browsers (photo import)
- Geolocation API works (GPS capture)
- No app store approval needed
- Zero native code to maintain

**What you lose:**
- Background GPS tracking (not critical for use case)
- App store presence (not important for personal tool)
- Absolute best offline experience (PWA offline is 90% there)

**What you gain:**
- Save 8-12 weeks of Flutter development
- Single codebase for desktop + mobile
- Instant updates (no app store releases)
- Works on all platforms (iOS, Android, even tablets)

**Recommendation:**
- Build PWA in Phase 5 (2-3 weeks)
- Use for 3 months
- Only build Flutter app if PWA truly insufficient

**Why It Matters:**
- Mobile app is 30%+ of total project effort
- If PWA is 90% as good, huge time savings
- Focus effort on features that matter more (AI extraction, archiving)

This is the most KISS approach to mobile.
