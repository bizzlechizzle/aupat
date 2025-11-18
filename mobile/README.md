# AUPAT Mobile App

Flutter-based mobile application for field GPS capture and offline location cataloging.

## Architecture

```
Mobile App (Flutter)
├── lib/
│   ├── main.dart                  # App entry point
│   ├── models/                    # Data models
│   │   ├── location_model.dart
│   │   ├── sync_item_model.dart
│   │   └── photo_model.dart
│   ├── services/                  # Business logic
│   │   ├── database_service.dart  # Local SQLite operations
│   │   ├── sync_service.dart      # WiFi sync to desktop
│   │   ├── gps_service.dart       # Device GPS capture
│   │   └── photo_service.dart     # Camera integration
│   ├── api/                       # API client
│   │   └── aupat_api_client.dart  # HTTP client for AUPAT Core
│   ├── screens/                   # UI screens
│   │   ├── map_screen.dart        # Offline map with locations
│   │   ├── location_list_screen.dart
│   │   ├── location_detail_screen.dart
│   │   ├── add_location_screen.dart
│   │   └── settings_screen.dart
│   └── widgets/                   # Reusable UI components
│       ├── location_card.dart
│       └── sync_status_indicator.dart
└── test/                          # Unit and widget tests
    ├── models/
    ├── services/
    └── widgets/
```

## Offline Database Schema

Stripped-down version of AUPAT database for offline use:

```sql
-- Local locations (synced subset)
CREATE TABLE locations_mobile (
  loc_uuid TEXT PRIMARY KEY,
  loc_name TEXT,
  lat REAL,
  lon REAL,
  loc_type TEXT,
  street_address TEXT,
  city TEXT,
  state_abbrev TEXT,
  synced INTEGER DEFAULT 1,  -- 0 = pending sync to desktop
  last_modified_at TEXT
);

-- Pending sync queue
CREATE TABLE locations_pending_sync (
  loc_uuid TEXT PRIMARY KEY,
  loc_name TEXT,
  lat REAL,
  lon REAL,
  loc_type TEXT,
  photos TEXT,  -- JSON array of local file paths
  created_at TEXT,
  sync_attempts INTEGER DEFAULT 0
);

-- Sync metadata
CREATE TABLE sync_log (
  sync_id TEXT PRIMARY KEY,
  sync_type TEXT,  -- 'mobile_to_desktop', 'desktop_to_mobile'
  timestamp TEXT,
  items_synced INTEGER,
  conflicts INTEGER,
  status TEXT  -- 'success', 'partial', 'failed'
);
```

## Sync Protocol

### Mobile → Desktop Sync

When WiFi connected and AUPAT API reachable:

1. Gather pending items from `locations_pending_sync`
2. POST /api/sync/mobile with payload:
   ```json
   {
     "device_id": "user-phone-uuid",
     "new_locations": [
       {
         "loc_uuid": "...",
         "loc_name": "...",
         "lat": 42.8142,
         "lon": -73.9396,
         "created_at": "2025-11-18T10:30:00Z",
         "photos": ["file:///path/to/photo1.jpg"]
       }
     ],
     "updated_locations": [],
     "device_timestamp": "2025-11-18T10:35:00Z"
   }
   ```
3. Backend validates, uploads photos to Immich, inserts to database
4. Backend returns sync receipt:
   ```json
   {
     "status": "success",
     "synced_count": 5,
     "conflicts": [],
     "next_sync_after": "2025-11-18T10:36:00Z"
   }
   ```
5. Mobile marks items as synced, removes from pending queue

### Desktop → Mobile Sync

1. GET /api/sync/mobile/pull?since=2025-11-18T00:00:00Z
2. Backend returns new/updated locations created after timestamp
3. Mobile merges into local database:
   - New locations: Insert
   - Updated locations: Overwrite if desktop timestamp > mobile timestamp
   - Conflicts: Flag for user review (future)

### Conflict Resolution Rules

**Simple strategy for v0.1.2:**
- Mobile GPS always wins for new locations created on mobile
- Desktop timestamp wins for updates to existing locations
- User can manually resolve conflicts in desktop app (future)

## Tech Stack

- **Flutter**: 3.16+
- **Dart**: 3.2+
- **sqflite**: SQLite for Flutter
- **geolocator**: GPS location capture
- **flutter_map**: Offline map rendering
- **MBTiles**: Offline map tiles
- **image_picker**: Camera/gallery photo import
- **http**: REST API client
- **workmanager**: Background sync service
- **path_provider**: File system access
- **shared_preferences**: Settings persistence

## Success Metrics

- GPS accuracy: < 10 meter error
- Offline database size: < 10 MB for 1000 locations
- Map tiles for region: < 500 MB
- Near Me search: < 1 second
- Photo upload on WiFi: 100 photos in < 2 minutes
- Sync completes in < 30 seconds
- Works offline for 90%+ of field tasks

## Development Phases

1. **Phase 2**: Flutter project setup, dependencies
2. **Phase 3**: Offline database and data models
3. **Phase 4**: Core UI (location list, map, GPS capture)
4. **Phase 5**: Sync service implementation
5. **Phase 6**: Backend API endpoints (/api/sync/mobile)
6. **Phase 7**: Conflict resolution and sync testing
7. **Phase 8**: Photo capture and camera integration
8. **Phase 9**: Comprehensive testing
9. **Phase 10**: Self-audit and refinement
