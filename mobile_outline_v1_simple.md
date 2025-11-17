# AUPAT Mobile App v1.0 - Simplified Offline-First Outline

## Executive Summary

This is the SIMPLIFIED v1.0 mobile app that matches your actual goals: field location capture, offline blog viewing, and WiFi sync. The complex comments system is saved for v2.0.

**Core Goal**: Capture locations in the field with GPS, view research offline, sync to desktop when home.

**Technology Stack**: Flutter 3.16+, SQLite (sqflite), flutter_map with offline MBTiles, camera package

**Timeline**: 6-8 weeks (vs. 10 weeks for the over-engineered version)

---

## 1. Mobile v1.0 Feature Set (MVP)

### 1.1 Add New Location (Offline Capable)

**Workflow**:
```
Field Exploration → Tap "Add Location" → App captures:
  1. GPS coordinates (device location)
  2. Take reference photo (for metadata)
  3. Enter location name
  4. Select location type (factory, hospital, school, etc.)
  5. Optional: Add brief description
→ Save to local SQLite
→ Marked as "Not Synced" (yellow badge)
→ When WiFi available, sync to AUPAT Core
```

**Database Schema (Mobile)**:
```sql
CREATE TABLE locations_mobile (
  loc_uuid TEXT PRIMARY KEY,
  loc_name TEXT NOT NULL,
  loc_type TEXT,
  lat REAL,
  lon REAL,
  gps_accuracy REAL,
  brief_description TEXT,

  reference_photo_path TEXT,      -- Local path to photo
  reference_photo_sha256 TEXT,

  created_at TEXT NOT NULL,
  synced INTEGER DEFAULT 0,       -- 0 = pending, 1 = synced
  server_timestamp TEXT,

  -- For offline viewing
  cached_at TEXT
);

CREATE TABLE pending_uploads (
  upload_id TEXT PRIMARY KEY,
  loc_uuid TEXT NOT NULL,
  file_path TEXT NOT NULL,        -- Photo/video/document path
  file_type TEXT,                 -- 'photo', 'video', 'document'
  file_sha256 TEXT,
  file_size_bytes INTEGER,

  uploaded INTEGER DEFAULT 0,
  immich_asset_id TEXT,           -- Set after upload to Immich

  FOREIGN KEY (loc_uuid) REFERENCES locations_mobile(loc_uuid)
);
```

### 1.2 View Locations (Stripped Blog Post Mode)

**Two Viewing Modes**:

**Mode 1: Stripped Blog Post (Offline, Default)**
- Text-only content
- No images/videos (saves mobile data + storage)
- Shows: Location name, type, description, GPS, key facts
- Cached in local SQLite for offline viewing
- Fast loading, minimal battery usage

**Mode 2: Basic Blog Post (Online, Optional)**
- Full blog post with thumbnails
- Loads from AUPAT Core API
- Shows photos via Immich thumbnail URLs
- Requires WiFi connection
- User can toggle: Settings → "Load full blog posts on WiFi"

**Database Schema**:
```sql
CREATE TABLE blog_posts_cache (
  post_id TEXT PRIMARY KEY,
  loc_uuid TEXT NOT NULL,

  -- Text-only content (for offline)
  title TEXT,
  content_markdown TEXT,          -- Markdown without image embeds
  historical_summary TEXT,
  key_facts TEXT,                 -- JSON array

  published_at TEXT,
  cached_at TEXT,

  -- For online mode
  has_photos INTEGER DEFAULT 0,
  photo_count INTEGER DEFAULT 0,

  FOREIGN KEY (loc_uuid) REFERENCES locations_mobile(loc_uuid)
);
```

### 1.3 Map View (Offline Capable)

**Features**:
- Offline MBTiles (upstate NY region pre-downloaded)
- Show all cached locations as pins
- Cluster markers at low zoom
- Tap marker → Show location name + distance from current position
- "Near Me" button → Zoom to nearby locations (5 mile radius)

**Offline Map Tiles**:
- Source: OpenStreetMap
- Coverage: Upstate NY (bounding box: 42-44°N, 74-78°W)
- Zoom levels: 8-15 (overview to street level)
- File size: ~150 MB
- Bundled with app or downloaded on first launch

### 1.4 Import Mobile Media

**Workflow**:
```
On Location Detail Screen → Tap "Add Photos"
→ Choose: Take Photo | Select from Gallery
→ Photo saved to local storage
→ Calculate SHA256 hash
→ Add to pending_uploads table
→ When WiFi: Upload to Immich, link to location in AUPAT Core
```

**No Complex Features**:
- No comments or annotations (that's v2.0)
- Just import and tag to location
- Sync handles the rest

### 1.5 Import URLs (Queue for Desktop)

**Workflow**:
```
User finds interesting article about location while in field
→ Tap "Save URL"
→ Enter URL + optional title
→ Saved to queue_for_desktop table
→ When synced, desktop AUPAT Core receives URL
→ Desktop/Docker runs ArchiveBox to archive
```

**Database Schema**:
```sql
CREATE TABLE urls_queue (
  url_id TEXT PRIMARY KEY,
  loc_uuid TEXT NOT NULL,
  url TEXT NOT NULL,
  url_title TEXT,
  notes TEXT,

  queued_at TEXT,
  synced INTEGER DEFAULT 0,

  FOREIGN KEY (loc_uuid) REFERENCES locations_mobile(loc_uuid)
);
```

### 1.6 Locations Near Me

**Feature**:
- Button on map screen: "Near Me"
- Uses device GPS to find locations within 5 miles
- Sorts by distance
- Works offline (queries local SQLite)
- Shows: Name, type, distance, bearing (N/S/E/W)

**Query**:
```dart
Future<List<Location>> getNearbyLocations(double userLat, double userLon, double radiusMiles) async {
  // Haversine distance calculation in SQL
  // Filter to within radius, sort by distance
  final db = await database;
  return db.rawQuery('''
    SELECT *,
           (6371 * acos(cos(radians(?)) * cos(radians(lat)) *
           cos(radians(lon) - radians(?)) + sin(radians(?)) *
           sin(radians(lat)))) AS distance_km
    FROM locations_mobile
    WHERE distance_km <= ?
    ORDER BY distance_km ASC
    LIMIT 20
  ''', [userLat, userLon, userLat, radiusMiles * 1.60934]);
}
```

---

## 2. Mobile Sync Protocol (Simple Version)

### 2.1 Sync Triggers

**Automatic Sync Conditions**:
- WiFi connected (NOT cellular)
- Battery > 20% OR charging
- App in foreground

**Manual Sync**:
- User taps "Sync Now" button
- Shows progress: "Syncing... 3 of 5 locations uploaded"

**Sync Frequency**:
- Foreground: Every 5 minutes if pending items exist
- Background: Disabled in v1.0 (too complex for MVP)

### 2.2 Sync API Endpoints

#### Upload New Locations
**POST /api/sync/mobile/locations**

Request:
```json
{
  "device_id": "mobile-abc123",
  "new_locations": [
    {
      "loc_uuid": "loc-xyz789",
      "loc_name": "Abandoned Factory A",
      "loc_type": "factory",
      "lat": 42.7890,
      "lon": -73.8765,
      "gps_accuracy": 12.5,
      "brief_description": "Large brick building, 3 stories",
      "created_at": "2025-01-15T14:30:00Z"
    }
  ]
}
```

Response:
```json
{
  "synced": 1,
  "conflicts": 0,
  "server_timestamp": "2025-01-15T14:35:00Z"
}
```

#### Upload Photos
**POST /api/sync/mobile/media**

Two-phase upload:
1. Upload file to Immich (multipart form data)
2. Link immich_asset_id to location in AUPAT Core

#### Download Locations
**GET /api/sync/mobile/locations?since={timestamp}&limit=100**

Response:
```json
{
  "locations": [
    {
      "loc_uuid": "loc-from-desktop",
      "loc_name": "Abandoned School B",
      "lat": 42.6543,
      "lon": -73.7654,
      "created_at": "2025-01-10T12:00:00Z"
    }
  ],
  "blog_posts_stripped": [
    {
      "post_id": "post-001",
      "loc_uuid": "loc-from-desktop",
      "title": "The Story of School B",
      "content_markdown": "Text without images...",
      "photo_count": 25
    }
  ],
  "server_timestamp": "2025-01-15T14:35:00Z"
}
```

### 2.3 Conflict Resolution (Simple)

**Rule: Desktop wins for existing locations, mobile wins for new locations**

Scenarios:
1. **Location created on mobile, doesn't exist on desktop**: Upload, no conflict
2. **Location updated on both mobile and desktop**: Desktop wins, mobile gets overwritten
3. **Location deleted on desktop, edited on mobile**: Desktop wins, mobile deletion synced

**No complex merging - KISS principle**

User sees notification: "1 location was updated on desktop, your changes were overwritten"

---

## 3. Flutter App Structure (Simplified)

```
mobile/
├── lib/
│   ├── main.dart
│   ├── models/
│   │   ├── location.dart
│   │   ├── blog_post.dart
│   │   └── pending_upload.dart
│   │
│   ├── services/
│   │   ├── database_service.dart      # SQLite wrapper
│   │   ├── gps_service.dart           # Device location
│   │   ├── camera_service.dart        # Photo capture
│   │   ├── sync_service.dart          # Sync logic
│   │   └── api_client.dart            # AUPAT Core API
│   │
│   ├── screens/
│   │   ├── home_screen.dart           # Location list
│   │   ├── map_screen.dart            # Offline map
│   │   ├── add_location_screen.dart   # GPS capture form
│   │   ├── location_detail_screen.dart # Blog post viewer
│   │   ├── photo_import_screen.dart   # Camera/gallery
│   │   └── sync_screen.dart           # Manual sync UI
│   │
│   └── widgets/
│       ├── location_card.dart
│       ├── sync_status_badge.dart
│       └── offline_map_widget.dart
│
├── assets/
│   └── maps/
│       └── upstate_ny.mbtiles         # Offline map tiles
│
└── pubspec.yaml
```

### 3.1 Core Packages (Minimal Set)

```yaml
dependencies:
  flutter:
    sdk: flutter

  # Database
  sqflite: ^2.3.0
  path_provider: ^2.1.1

  # Maps
  flutter_map: ^6.1.0
  latlong2: ^0.9.0
  geolocator: ^11.0.0

  # Camera
  camera: ^0.10.5
  image_picker: ^1.0.7

  # Networking
  http: ^1.1.0
  connectivity_plus: ^5.0.2

  # Utilities
  uuid: ^4.3.3
  crypto: ^3.0.3
  shared_preferences: ^2.2.2

  # State
  provider: ^6.1.1              # Simple state management
```

**NO complex packages for v1.0:**
- ❌ flutter_quill (rich text editor - not needed)
- ❌ record (audio recording - not needed)
- ❌ speech_to_text (voice memos - v2.0 feature)
- ❌ workmanager (background sync - too complex for MVP)

---

## 4. Implementation Timeline (Simplified)

### Week 1-2: Database and Core Services
- SQLite schema implementation
- Database service wrapper
- GPS service (location capture)
- Camera service (photo import)
- **Deliverable**: Can create location + take photo, save to local DB

### Week 3-4: UI Screens
- Home screen (location list)
- Add location screen (GPS + form)
- Location detail screen (stripped blog viewer)
- Photo import screen
- **Deliverable**: Full offline app, no sync yet

### Week 4-5: Offline Map
- MBTiles integration with flutter_map
- Location markers on map
- "Near Me" functionality
- **Deliverable**: Offline map navigation works

### Week 6-7: Sync Protocol
- API client implementation
- Sync service (upload/download)
- Sync UI (status, manual trigger)
- **Deliverable**: Full sync to AUPAT Core works

### Week 8: Testing and Polish
- Test on real device in field
- Fix bugs
- Performance optimization
- User acceptance testing
- **Deliverable**: Release candidate

**Total: 8 weeks (2 months)**

---

## 5. What's NOT in v1.0 (Saved for v2.0)

### Comments/Notes System (Your "notes mode")
- Hierarchical threaded comments
- Voice memos
- Rich text annotations
- **Reason**: You listed this under "Long Term Goals v2" - it's a future feature

### Background Sync
- Automatic sync while app closed
- Battery-efficient background fetch
- **Reason**: Too complex for MVP, adds 1-2 weeks

### Offline AI Features
- Image tagging on device
- Address extraction from photos
- **Reason**: Not in your mobile goals list

### Desktop-Like Features
- Web browser for archiving
- Document viewer
- **Reason**: Mobile is for field capture, desktop is for heavy lifting

---

## 6. Your Questions Answered

### "Brain on Docker for now? Desktop?"

**YES - AUPAT Core (the brain) runs in Docker on your desktop/server**

Architecture:
```
┌─────────────────────────────────┐
│ Desktop Machine                 │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Docker Containers           │ │
│ │                             │ │
│ │ - AUPAT Core (Flask+SQLite) │ ← THE BRAIN
│ │ - Immich (Photo Storage)    │ │
│ │ - ArchiveBox (Web Archive)  │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Electron Desktop App        │ ← UI for heavy work
│ │ - Embedded browser          │ │
│ │ - Bulk imports              │ │
│ │ - Map with 200k locations   │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
                ↕
         (WiFi/Cloudflare)
                ↕
┌─────────────────────────────────┐
│ Mobile Phone                    │
│                                 │
│ Flutter App                     │
│ - Offline SQLite (subset)       │
│ - Field GPS capture             │
│ - Photo import                  │
│ - Syncs to AUPAT Core           │
└─────────────────────────────────┘
```

### "web app or app app for both desktop and mobile?"

**NATIVE APPS for both, NOT web apps**

**Desktop**: Electron app (native)
- **Why**: Need embedded Chromium for web archiving
- **Why**: Native filesystem access for bulk imports
- **Why**: Better performance for 200k markers on map

**Mobile**: Flutter app (native) OR try PWA first
- **Why Flutter**: Better offline support, SQLite, camera access
- **Why PWA**: Might be 80% good enough, saves 6 weeks (try this first per WWYDD.md)
- **NOT web app**: Offline requirements + GPS + camera need native or PWA

### "What would you do differently?"

Per WWYDD.md, key recommendations:
1. **Try PWA for mobile FIRST** before building Flutter app
   - Might be adequate for your needs
   - Saves 6-8 weeks if it works
   - Can always build Flutter later if PWA insufficient

2. **Use Mapbox GL JS** instead of Leaflet (better performance)

3. **Add Cloudflare Access** for security (zero-trust auth)

4. **Skip mobile app entirely** (controversial) - just use PWA
   - Your use case might not need native mobile
   - PWA works offline, has GPS, has camera
   - Saves massive development time

5. **Bundle AUPAT Core with Desktop app** in v2.0
   - Simpler deployment (no separate Docker setup)
   - "Just works" experience

---

## 7. Architecture Decision: PWA vs Flutter

### Recommendation: TRY PWA FIRST

**PWA (Progressive Web App) Approach**:

**What it gives you**:
- Works on ALL devices (iOS, Android, tablets, desktop)
- Single codebase (reuse Svelte from desktop)
- No app store approval
- Instant updates
- Offline mode via Service Workers + IndexedDB
- Camera API works in mobile browsers
- Geolocation API works

**What you lose vs native**:
- Background GPS tracking (not needed for your use case)
- App store presence (not important for personal tool)
- Slightly less smooth offline (90% vs 100%)

**Development Time**:
- PWA: 3-4 weeks
- Flutter: 8 weeks

**Recommendation from WWYDD.md**:
> Build PWA in Phase 5 (2-3 weeks). Use for 3 months. Only build Flutter app if PWA truly insufficient.

**My Opinion**: Your mobile goals (GPS capture, photo import, offline viewing) work FINE in PWA. Try it first.

---

## 8. Revised Mobile Roadmap

### Phase 1: Desktop Foundation (Current Phase 1-4)
- Get Docker + Desktop app working
- Import photos, web archiving, map view
- **Mobile not started yet**

### Phase 2: Mobile PWA Prototype (3-4 weeks)
- Build PWA with offline support
- Test GPS capture, photo import, sync
- Use in field for 1 month
- **Decision point**: Is PWA good enough?

### Phase 3A: If PWA sufficient (likely)
- Polish PWA
- Ship it
- **Time saved**: 4-5 weeks

### Phase 3B: If PWA insufficient (unlikely)
- Build Flutter app (8 weeks)
- All features from this outline

### Phase 4: Mobile v2.0 (6+ months later)
- Add "notes mode" (comments system from my original outline)
- Voice memos
- Background sync
- Advanced features

---

## 9. Final Recommendations

### For Mobile v1.0:
1. **Try PWA first** (3-4 weeks, might be all you need)
2. **If PWA doesn't work**, build Flutter app from this simplified outline (8 weeks)
3. **Save comments/notes** for v2.0 (matches your "Long Term Goals v2")

### For Overall Architecture:
1. **AUPAT Core (Docker)** = The brain, authoritative database
2. **Immich (Docker)** = Photo storage ONLY, separate from AUPAT database
3. **Desktop (Electron)** = Heavy lifting UI (archiving, bulk imports, research)
4. **Mobile (PWA or Flutter)** = Field capture (GPS, photos, offline viewing)

### For Database:
- **AUPAT Core SQLite** = Master database for locations, relationships, metadata
- **Immich PostgreSQL** = Photo metadata and AI embeddings ONLY
- **Mobile SQLite** = Offline subset that syncs to AUPAT Core
- **NO** - Immich does NOT handle AUPAT's database!

---

## Summary

**My original mobile outline was correct architecturally but over-engineered for v1.0.**

This simplified outline matches your actual mobile goals:
- ✅ Add location (offline GPS capture)
- ✅ Import mobile media
- ✅ Import URLs (queue for desktop)
- ✅ Edit/update locations
- ✅ Map view (offline)
- ✅ View locations (stripped blog post)
- ✅ Locations near me

**Comments/notes mode saved for v2.0** where it belongs per your long-term goals.

**Try PWA before Flutter** - might save you 4-5 weeks and be perfectly adequate.

**Database is NOT handled by Immich** - AUPAT Core (Docker) is the brain.

Does this simplified approach match your vision better?
