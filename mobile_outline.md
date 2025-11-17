# AUPAT Mobile App - Comprehensive Offline Comments Implementation Outline

## Executive Summary

This document outlines the complete mobile application architecture for AUPAT (Abandoned Upstate Project Archive Tool) with a focus on offline-first comments and field data collection. The mobile app enables urban explorers to capture locations, photos, and detailed field notes while offline, then sync to the desktop system when WiFi becomes available.

**Core Philosophy**: Offline-first, sync-second. The mobile app must work 100% without internet connectivity and gracefully sync when connectivity is restored.

**Technology Stack**: Flutter 3.16+, SQLite (sqflite), flutter_map with offline MBTiles, background_fetch for sync

**Key Features**:
- Full offline location catalog with GPS capture
- Hierarchical comment system with rich text and media
- Offline photo capture and management
- Conflict-free sync with desktop AUPAT Core
- Offline map tiles for field navigation

---

## 1. Offline Comments Architecture

### 1.1 Comment Data Model

Comments are the primary field note mechanism for capturing observations, historical research, safety notes, and exploration metadata.

#### Comment Schema (Mobile SQLite)

```sql
CREATE TABLE comments (
  comment_id TEXT PRIMARY KEY,           -- UUID v4
  loc_uuid TEXT NOT NULL,                -- Location this comment belongs to
  parent_comment_id TEXT,                -- For threaded replies (NULL = top-level)

  -- Content
  comment_text TEXT NOT NULL,            -- Markdown-formatted text
  comment_type TEXT DEFAULT 'note',      -- 'note', 'observation', 'safety', 'historical', 'question'

  -- Metadata
  created_at TEXT NOT NULL,              -- ISO 8601 timestamp
  updated_at TEXT,                       -- Last edited timestamp
  author_device_id TEXT,                 -- Device that created this (multi-device sync)

  -- Offline attachments
  has_photos INTEGER DEFAULT 0,          -- Boolean: has attached photos
  has_audio INTEGER DEFAULT 0,           -- Boolean: has voice memo
  photo_count INTEGER DEFAULT 0,

  -- Sync tracking
  synced INTEGER DEFAULT 0,              -- 0 = pending upload, 1 = synced to server
  server_timestamp TEXT,                 -- When synced to server (for conflict detection)
  deleted INTEGER DEFAULT 0,             -- Soft delete flag

  -- GPS context (capture where comment was written)
  gps_lat REAL,
  gps_lon REAL,
  gps_accuracy REAL,

  FOREIGN KEY (loc_uuid) REFERENCES locations_mobile(loc_uuid),
  FOREIGN KEY (parent_comment_id) REFERENCES comments(comment_id)
);

CREATE INDEX idx_comments_location ON comments(loc_uuid) WHERE deleted = 0;
CREATE INDEX idx_comments_parent ON comments(parent_comment_id) WHERE parent_comment_id IS NOT NULL;
CREATE INDEX idx_comments_unsynced ON comments(synced) WHERE synced = 0;
CREATE INDEX idx_comments_created ON comments(created_at DESC);

-- Comment attachments (photos, audio, files)
CREATE TABLE comment_attachments (
  attachment_id TEXT PRIMARY KEY,
  comment_id TEXT NOT NULL,
  attachment_type TEXT,                  -- 'photo', 'audio', 'video'
  local_file_path TEXT NOT NULL,         -- Path on device filesystem
  file_sha256 TEXT,                      -- For deduplication
  file_size_bytes INTEGER,

  -- Server tracking
  uploaded INTEGER DEFAULT 0,            -- 0 = pending, 1 = uploaded to Immich
  immich_asset_id TEXT,                  -- Immich reference after upload

  created_at TEXT NOT NULL,

  FOREIGN KEY (comment_id) REFERENCES comments(comment_id)
);

CREATE INDEX idx_attachments_comment ON comment_attachments(comment_id);
CREATE INDEX idx_attachments_unsynced ON comment_attachments(uploaded) WHERE uploaded = 0;

-- Comment tags for categorization
CREATE TABLE comment_tags (
  tag_id TEXT PRIMARY KEY,
  comment_id TEXT NOT NULL,
  tag_name TEXT NOT NULL,                -- 'asbestos', 'structural_damage', 'graffiti', etc.
  tag_category TEXT,                     -- 'safety', 'feature', 'hazard', 'historical'

  FOREIGN KEY (comment_id) REFERENCES comments(comment_id)
);

CREATE INDEX idx_tags_comment ON comment_tags(comment_id);
CREATE INDEX idx_tags_name ON comment_tags(tag_name);
```

#### Comment Types and Use Cases

| Type | Use Case | Example |
|------|----------|---------|
| **note** | General observations | "Large factory building, 3 stories, brick construction" |
| **observation** | Specific findings | "Found old employee timecards from 1987 in office area" |
| **safety** | Hazards and warnings | "Floor unstable in northwest corner, avoid weight-bearing" |
| **historical** | Research and context | "Built in 1923 by Smith Manufacturing, produced textiles until 1989" |
| **question** | Follow-up items | "Need to research original architect - possible connection to city hall?" |

### 1.2 Comment Threading and Hierarchy

Comments support threaded replies for organizing complex field notes.

**Example Thread Structure**:
```
Location: Abandoned Hospital XYZ
├─ [note] "Main building has 4 floors, west wing collapsed"
│  ├─ [safety] "West wing is completely inaccessible, dangerous"
│  └─ [observation] "Found patient records in basement, dated 1960s"
├─ [historical] "Opened in 1955, closed in 1998 due to bankruptcy"
│  └─ [question] "Why did they leave medical equipment behind?"
└─ [note] "Beautiful art deco tilework in main lobby"
   └─ [photo attachment] lobby_tiles_01.jpg
```

**Threading Rules**:
- Maximum depth: 3 levels (prevents over-nesting on mobile UI)
- Parent comment must exist before replies (enforced by foreign key)
- Deleting parent marks all children as orphaned (UI shows "Reply to deleted comment")

### 1.3 Offline Comment Editing and Conflict Resolution

#### Editing Behavior
- Edit window: Unlimited for unsynced comments, 24 hours after sync
- Edits create new `updated_at` timestamp
- Original `created_at` preserved for chronological ordering
- Edit history not tracked (KISS principle - desktop can track if needed)

#### Conflict Scenarios and Resolution

**Scenario 1: Same comment edited on mobile and desktop**
- Detection: `updated_at` mismatch during sync
- Resolution: Last-write-wins based on `updated_at` timestamp
- User notification: "Comment was edited elsewhere, your changes were preserved"

**Scenario 2: Comment deleted on desktop, edited on mobile**
- Detection: Server returns 404 on sync
- Resolution: Recreate comment as new (treat as undelete)
- User notification: "This comment was deleted elsewhere, re-creating with your edits"

**Scenario 3: Parent comment deleted, reply added offline**
- Detection: Parent has `deleted = 1` on server
- Resolution: Orphan the reply (set `parent_comment_id = NULL`)
- User notification: "Parent comment was deleted, your reply is now top-level"

### 1.4 Offline Rich Text Editing

#### Markdown Support
Comments use lightweight Markdown for formatting:
- **Bold**, *italic*, ~~strikethrough~~
- Headers: # H1, ## H2, ### H3
- Lists: - bullet or 1. numbered
- Links: [text](url) - for research references
- Code: `inline` or ```multiline```

**Editor Implementation**: flutter_quill or flutter_markdown_editor
- WYSIWYG-style toolbar for mobile
- Markdown preview mode
- Auto-save every 5 seconds to SQLite

#### Voice-to-Text Integration
For hands-free field notes:
- Use device speech recognition (speech_to_text package)
- Start recording → transcribe → append to comment
- Store audio file as attachment for reference
- Background noise filtering (mobile devices handle this)

**Workflow**:
1. User taps microphone icon in comment editor
2. Records voice memo while exploring
3. App transcribes to text, appends to comment
4. Original audio saved as attachment (verify transcription accuracy)

---

## 2. Mobile App Architecture

### 2.1 Flutter Application Structure

```
mobile/
├── lib/
│   ├── main.dart                      # App entry point, routing
│   ├── app_config.dart                # Environment config, API URLs
│   │
│   ├── models/                        # Data models
│   │   ├── location.dart
│   │   ├── comment.dart
│   │   ├── comment_attachment.dart
│   │   ├── sync_state.dart
│   │   └── map_marker.dart
│   │
│   ├── services/                      # Business logic layer
│   │   ├── database/
│   │   │   ├── database_service.dart  # SQLite connection
│   │   │   ├── migrations/            # Schema version migrations
│   │   │   └── dao/                   # Data access objects
│   │   │       ├── location_dao.dart
│   │   │       ├── comment_dao.dart
│   │   │       └── attachment_dao.dart
│   │   │
│   │   ├── sync/
│   │   │   ├── sync_service.dart      # Main sync orchestrator
│   │   │   ├── conflict_resolver.dart
│   │   │   ├── retry_queue.dart       # Failed sync retry logic
│   │   │   └── background_sync.dart   # Background fetch integration
│   │   │
│   │   ├── gps_service.dart           # Location tracking
│   │   ├── camera_service.dart        # Photo capture
│   │   ├── api_client.dart            # AUPAT Core API wrapper
│   │   └── immich_client.dart         # Immich upload API
│   │
│   ├── ui/                            # User interface
│   │   ├── screens/
│   │   │   ├── home_screen.dart       # Location list
│   │   │   ├── map_screen.dart        # Offline map view
│   │   │   ├── location_detail_screen.dart
│   │   │   ├── comment_thread_screen.dart
│   │   │   ├── comment_editor_screen.dart
│   │   │   ├── photo_capture_screen.dart
│   │   │   ├── sync_status_screen.dart
│   │   │   └── settings_screen.dart
│   │   │
│   │   ├── widgets/
│   │   │   ├── comment_card.dart      # Single comment display
│   │   │   ├── comment_tree.dart      # Threaded comment list
│   │   │   ├── markdown_editor.dart   # Rich text editor
│   │   │   ├── attachment_viewer.dart
│   │   │   ├── sync_indicator.dart    # Shows sync status
│   │   │   └── offline_banner.dart    # "No connection" warning
│   │   │
│   │   └── theme/
│   │       ├── app_theme.dart
│   │       └── app_colors.dart
│   │
│   ├── utils/
│   │   ├── uuid_generator.dart
│   │   ├── sha256_calculator.dart
│   │   ├── date_formatter.dart
│   │   └── logger.dart
│   │
│   └── constants/
│       ├── db_constants.dart          # Table/column names
│       ├── sync_constants.dart        # Retry intervals, timeouts
│       └── app_constants.dart
│
├── assets/
│   ├── maps/                          # Offline MBTiles map tiles
│   │   └── upstate_ny.mbtiles         # Pre-downloaded region
│   ├── icons/
│   └── fonts/
│
├── test/                              # Unit tests
├── integration_test/                  # Integration tests
├── pubspec.yaml                       # Dependencies
└── README.md
```

### 2.2 Core Flutter Packages

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter

  # Database
  sqflite: ^2.3.0              # SQLite for Flutter
  path_provider: ^2.1.1        # File system paths

  # Networking
  http: ^1.1.0                 # API client
  dio: ^5.4.0                  # Alternative with upload progress
  connectivity_plus: ^5.0.2    # Network status detection

  # Maps
  flutter_map: ^6.1.0          # Offline map widget
  latlong2: ^0.9.0             # GPS coordinates
  geolocator: ^11.0.0          # Device GPS

  # Comments and Rich Text
  flutter_quill: ^9.0.0        # Rich text editor (Markdown-compatible)
  markdown: ^7.1.1             # Markdown rendering

  # Media
  camera: ^0.10.5              # Photo/video capture
  image_picker: ^1.0.7         # Gallery picker
  record: ^5.0.4               # Audio recording
  speech_to_text: ^6.6.0       # Voice transcription

  # Background Sync
  workmanager: ^0.5.2          # Background tasks
  background_fetch: ^1.2.1     # iOS background fetch

  # Utilities
  uuid: ^4.3.3                 # UUID generation
  crypto: ^3.0.3               # SHA256 hashing
  intl: ^0.19.0                # Date formatting
  shared_preferences: ^2.2.2   # Settings storage

  # State Management
  provider: ^6.1.1             # Simple state management (KISS)

  # Dev Tools
  logger: ^2.0.2               # Structured logging

dev_dependencies:
  flutter_test:
    sdk: flutter
  integration_test:
    sdk: flutter
  mockito: ^5.4.4              # Mocking for tests
  sqflite_common_ffi: ^2.3.2   # SQLite testing on desktop
```

### 2.3 Data Flow Diagrams

#### Creating Offline Comment Flow
```
User taps "Add Comment" on Location Detail Screen
                    │
                    ▼
Comment Editor Screen opens
  - Markdown editor initialized
  - GPS coordinates captured (background)
  - Device ID loaded from storage
                    │
                    ▼
User types field notes, selects type (note/safety/historical)
                    │
                    ▼
User taps camera icon → Photo Capture Screen
  - Take photo or select from gallery
  - Photo saved to local storage
  - attachment_id created, linked to comment
                    │
                    ▼
User taps "Save"
                    │
                    ▼
CommentDAO.insert()
  - Generate UUID for comment_id
  - Insert to comments table with synced=0
  - Insert attachments to comment_attachments table
  - Return to Location Detail Screen
                    │
                    ▼
UI updates: New comment appears in thread
  - Badge shows "Not synced" icon
  - Attachment thumbnails visible
                    │
                    ▼
SyncService detects unsynced comment (background polling)
                    │
                    ▼
When WiFi available: Upload comment to AUPAT Core API
  - POST /api/locations/{loc_uuid}/comments
  - Upload attachments to Immich
  - Mark synced=1, store server_timestamp
                    │
                    ▼
UI updates: "Not synced" badge removed
```

#### Sync Conflict Resolution Flow
```
Mobile: Edit comment "abc123" at 2025-01-15 10:30:00
Desktop: Edit same comment at 2025-01-15 10:32:00
Mobile: Goes online at 2025-01-15 10:35:00
                    │
                    ▼
SyncService.syncComments()
  - Fetch comment "abc123" from server
  - Compare updated_at timestamps
  - Server: 10:32:00 > Mobile: 10:30:00
                    │
                    ▼
ConflictResolver.resolve()
  - Strategy: Last-write-wins (server wins)
  - Option 1: Overwrite mobile version (data loss)
  - Option 2: Create new comment with mobile edits (duplicate)
  - CHOSEN: Option 2 (preserve user work)
                    │
                    ▼
Actions:
  - Update local comment with server version
  - Create new comment "abc124" with mobile edits
  - Add prefix: "[Edited offline] {original text}"
  - Show notification: "Comment was edited elsewhere"
                    │
                    ▼
User reviews notification
  - Can merge manually if needed
  - Can delete duplicate
  - Both versions preserved (BPL principle: never lose data)
```

---

## 3. Offline Map Integration

### 3.1 MBTiles Strategy

**Map Coverage**: Focus on upstate New York region (user's exploration area)
- Zoom levels: 8-16 (region overview to street level)
- Tile count: ~50,000 tiles
- File size: ~300 MB uncompressed, ~150 MB with JPEG compression
- Source: OpenStreetMap via TileMill or offline tile generators

**Tile Generation Workflow**:
```bash
# Using tilemill-export or mbutil
# Define bounding box: upstate NY (approximately)
BBOX="-79.762,42.000,-73.344,44.800"
ZOOM_LEVELS="8-16"

# Generate tiles from OpenStreetMap
tilemill export aupat_upstate_ny --bbox=$BBOX --minzoom=8 --maxzoom=16 --format=mbtiles

# Result: upstate_ny.mbtiles (bundled with app)
```

**Flutter Map Integration**:
```dart
// lib/ui/screens/map_screen.dart
import 'package:flutter_map/flutter_map.dart';
import 'package:mbtiles/mbtiles.dart';

class OfflineMapScreen extends StatefulWidget {
  @override
  _OfflineMapScreenState createState() => _OfflineMapScreenState();
}

class _OfflineMapScreenState extends State<OfflineMapScreen> {
  late MapController _mapController;
  late MBTilesImageProvider _tileProvider;
  List<Marker> _locationMarkers = [];

  @override
  void initState() {
    super.initState();
    _mapController = MapController();
    _loadOfflineMap();
    _loadLocationMarkers();
  }

  Future<void> _loadOfflineMap() async {
    // Load MBTiles from assets
    final mbtilesPath = await _copyAssetToLocal('assets/maps/upstate_ny.mbtiles');
    _tileProvider = MBTilesImageProvider.fromFile(File(mbtilesPath));
  }

  Future<void> _loadLocationMarkers() async {
    final locations = await LocationDAO().getAllLocations();
    setState(() {
      _locationMarkers = locations.map((loc) => Marker(
        point: LatLng(loc.lat, loc.lon),
        builder: (ctx) => Icon(Icons.location_pin, color: Colors.red),
      )).toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    return FlutterMap(
      mapController: _mapController,
      options: MapOptions(
        center: LatLng(42.8142, -73.9396), // Albany, NY
        zoom: 10.0,
        interactiveFlags: InteractiveFlag.all,
      ),
      children: [
        TileLayer(
          tileProvider: _tileProvider,
          maxZoom: 16.0,
          minZoom: 8.0,
        ),
        MarkerLayer(markers: _locationMarkers),
      ],
    );
  }
}
```

### 3.2 GPS Capture and Location Creation

**Accuracy Requirements**:
- Minimum: 50 meters (acceptable for location pin)
- Target: 10 meters (good GPS signal)
- Timeout: 30 seconds (if GPS poor, allow manual entry)

**GPS Capture Workflow**:
```dart
// lib/services/gps_service.dart
import 'package:geolocator/geolocator.dart';

class GPSService {
  Future<Position?> captureCurrentLocation({int timeoutSeconds = 30}) async {
    // Check permissions
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return null; // User denied
      }
    }

    // Get position with timeout
    try {
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: Duration(seconds: timeoutSeconds),
      );

      // Validate accuracy
      if (position.accuracy > 50.0) {
        // Warn user: GPS accuracy poor
        print('Warning: GPS accuracy ${position.accuracy}m (prefer <50m)');
      }

      return position;
    } catch (e) {
      print('GPS capture failed: $e');
      return null;
    }
  }

  Stream<Position> trackMovement() {
    // For real-time tracking while exploring
    return Geolocator.getPositionStream(
      locationSettings: LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // Update every 10 meters
      ),
    );
  }
}
```

---

## 4. Sync Protocol and API Design

### 4.1 Mobile → Server Sync API

#### Endpoint: POST /api/sync/mobile

**Request Payload**:
```json
{
  "device_id": "mobile-abc123",
  "last_sync_timestamp": "2025-01-15T10:00:00Z",

  "new_locations": [
    {
      "loc_uuid": "loc-def456",
      "loc_name": "Abandoned Factory A",
      "lat": 42.7890,
      "lon": -73.8765,
      "loc_type": "factory",
      "created_at": "2025-01-15T11:30:00Z",
      "offline_created": true
    }
  ],

  "new_comments": [
    {
      "comment_id": "cmt-xyz789",
      "loc_uuid": "loc-def456",
      "parent_comment_id": null,
      "comment_text": "Large brick building, 3 stories, windows broken",
      "comment_type": "note",
      "created_at": "2025-01-15T11:35:00Z",
      "gps_lat": 42.7890,
      "gps_lon": -73.8765,
      "gps_accuracy": 12.5,
      "has_photos": 1,
      "photo_count": 3
    }
  ],

  "updated_comments": [
    {
      "comment_id": "cmt-old123",
      "comment_text": "Updated field notes after second visit",
      "updated_at": "2025-01-15T12:00:00Z",
      "server_timestamp": "2025-01-10T08:00:00Z"  // For conflict detection
    }
  ],

  "deleted_comments": [
    "cmt-delete456"
  ],

  "pending_attachments": [
    {
      "attachment_id": "att-abc001",
      "comment_id": "cmt-xyz789",
      "attachment_type": "photo",
      "file_sha256": "a1b2c3d4...",
      "file_size_bytes": 2048576
    }
  ]
}
```

**Response Payload**:
```json
{
  "sync_id": "sync-2025-01-15-001",
  "server_timestamp": "2025-01-15T12:05:00Z",

  "results": {
    "locations_created": 1,
    "comments_created": 1,
    "comments_updated": 1,
    "comments_deleted": 1,
    "conflicts": []
  },

  "conflicts": [
    {
      "comment_id": "cmt-old123",
      "conflict_type": "updated_on_server",
      "server_version": {
        "comment_text": "Different text from desktop",
        "updated_at": "2025-01-15T11:30:00Z"
      },
      "resolution": "server_wins",  // or "mobile_wins" based on timestamp
      "message": "Comment was edited on desktop, your changes saved as new comment"
    }
  ],

  "upload_urls": [
    {
      "attachment_id": "att-abc001",
      "upload_url": "https://immich.example.com/api/upload?token=xyz",
      "method": "POST"
    }
  ]
}
```

### 4.2 Server → Mobile Sync API

#### Endpoint: GET /api/sync/mobile/changes?since={timestamp}&device_id={id}

**Response Payload**:
```json
{
  "server_timestamp": "2025-01-15T12:05:00Z",

  "new_locations": [
    {
      "loc_uuid": "loc-desktop-001",
      "loc_name": "Abandoned School B",
      "lat": 42.6543,
      "lon": -73.7654,
      "created_at": "2025-01-14T14:00:00Z"
    }
  ],

  "updated_locations": [
    {
      "loc_uuid": "loc-def456",
      "loc_name": "Abandoned Factory A (Updated Name)",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ],

  "new_comments": [
    {
      "comment_id": "cmt-desktop-001",
      "loc_uuid": "loc-def456",
      "comment_text": "Added from desktop app",
      "created_at": "2025-01-15T09:00:00Z",
      "author_device_id": "desktop-main"
    }
  ],

  "deleted_comments": ["cmt-remove789"]
}
```

### 4.3 Attachment Upload Flow

**Two-Phase Upload** (separate from comment sync for large files):

**Phase 1**: Sync comment metadata
- Mobile sends comment with `has_photos=1` but no photo data
- Server acknowledges, returns upload URL

**Phase 2**: Upload attachment to Immich
```dart
// lib/services/sync/attachment_uploader.dart
Future<void> uploadAttachment(CommentAttachment attachment, String uploadUrl) async {
  final file = File(attachment.localFilePath);
  final fileBytes = await file.readAsBytes();

  final dio = Dio();
  final formData = FormData.fromMap({
    'file': MultipartFile.fromBytes(fileBytes, filename: attachment.attachmentId),
    'deviceAssetId': attachment.attachmentId,
    'deviceId': deviceId,
  });

  try {
    final response = await dio.post(
      uploadUrl,
      data: formData,
      onSendProgress: (sent, total) {
        // Update progress UI
        final progress = sent / total;
        print('Upload progress: ${(progress * 100).toFixed(1)}%');
      },
    );

    if (response.statusCode == 201) {
      final immichAssetId = response.data['id'];
      await AttachmentDAO().markUploaded(attachment.attachmentId, immichAssetId);
    }
  } catch (e) {
    // Retry queue handles failures
    await RetryQueue().addFailedUpload(attachment.attachmentId);
  }
}
```

### 4.4 Sync Triggers and Scheduling

**Automatic Sync Conditions**:
1. WiFi connected (not cellular to save data)
2. Battery > 20% OR device charging
3. App in foreground OR background fetch triggered

**Sync Intervals**:
- Foreground: Every 5 minutes if unsynced items exist
- Background: Every 15 minutes (iOS) or 30 minutes (Android)
- Manual: User taps "Sync Now" button

**Background Sync Implementation**:
```dart
// lib/services/sync/background_sync.dart
import 'package:workmanager/workmanager.dart';

void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    final syncService = SyncService();

    // Check if WiFi available
    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity != ConnectivityResult.wifi) {
      return Future.value(false); // Skip sync on cellular
    }

    // Check battery level
    final battery = Battery();
    final batteryLevel = await battery.batteryLevel;
    final batteryState = await battery.batteryState;

    if (batteryLevel < 20 && batteryState != BatteryState.charging) {
      return Future.value(false); // Skip sync on low battery
    }

    // Perform sync
    await syncService.syncAll();

    return Future.value(true);
  });
}

void registerBackgroundSync() {
  Workmanager().initialize(callbackDispatcher, isInDebugMode: false);

  Workmanager().registerPeriodicTask(
    "mobile-sync-task",
    "syncToDesktop",
    frequency: Duration(minutes: 30),
    constraints: Constraints(
      networkType: NetworkType.unmetered,  // WiFi only
      requiresBatteryNotLow: true,
    ),
  );
}
```

---

## 5. UI/UX Design for Offline Comments

### 5.1 Location Detail Screen with Comments

```
┌─────────────────────────────────────┐
│ ← Back          Location Detail    ⋮│
├─────────────────────────────────────┤
│                                     │
│  📍 Abandoned Factory A             │
│  Factory • Albany, NY               │
│  42.7890, -73.8765                  │
│                                     │
│  [Photos (12)]  [Comments (8)]  [Map]│ ← Tabs
├─────────────────────────────────────┤
│ 🗨 Comments                    [+ Add]│
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ 📝 Note • 2 hours ago      [⋮]  │ │
│ │ Large brick building, 3 stories │ │
│ │ Windows broken, roof intact     │ │
│ │ 📷 3 photos attached            │ │
│ │   └─ 💬 Reply                   │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ ⚠️ Safety • 1 day ago      [⋮]  │ │
│ │ Floor unstable in NW corner     │ │
│ │ Avoid weight-bearing            │ │
│ │   └─ 💬 1 reply                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 📚 Historical • 3 days ago [⋮]  │ │
│ │ Built 1923 by Smith Mfg         │ │
│ │ Produced textiles until 1989    │ │
│ └─────────────────────────────────┘ │
│                                     │
│                [Load More (5)]      │
└─────────────────────────────────────┘
```

### 5.2 Comment Editor Screen

```
┌─────────────────────────────────────┐
│ ✕ Cancel      New Comment      Save │
├─────────────────────────────────────┤
│ Comment Type                        │
│ [📝 Note ▼]                         │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Write your field notes...       │ │
│ │                                 │ │
│ │ [User types here]               │ │
│ │                                 │ │
│ │                                 │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [B] [I] [H] [•] [1] [🔗] [```]     │ ← Markdown toolbar
│                                     │
│ Attachments                         │
│ ┌───────┐ ┌───────┐ ┌───────┐     │
│ │ 📷    │ │ 📷    │ │   +   │     │ ← Photo thumbnails
│ │ Photo │ │ Photo │ │  Add  │     │
│ └───────┘ └───────┘ └───────┘     │
│                                     │
│ [🎤 Voice Note] [📷 Camera]  [📍 GPS]│
│                                     │
│ GPS: 42.7890, -73.8765 (12m acc.)  │
│ ⚠️ Not synced - will upload on WiFi │
└─────────────────────────────────────┘
```

### 5.3 Sync Status Indicators

**Visual Indicators**:
- 🔄 Gray sync icon: Not synced (offline mode)
- ✅ Green checkmark: Synced successfully
- ⚠️ Yellow warning: Sync conflict, review needed
- ❌ Red X: Sync failed, will retry
- 📡 Animated pulse: Syncing in progress

**Status Banner** (top of app):
```
┌─────────────────────────────────────┐
│ 📡 Syncing... (3 of 5 comments)     │ ← Active sync
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🔄 Offline • 8 items pending sync   │ ← No connection
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ✅ Synced • All changes uploaded    │ ← Up to date
└─────────────────────────────────────┘
```

---

## 6. Implementation Modules and Build Plan

### 6.1 Module Breakdown

#### Module 1: Database and Offline Storage (Week 1-2)
**Deliverables**:
- SQLite schema implementation
- Migration system (versioned schema updates)
- DAOs for locations, comments, attachments
- Unit tests for database operations

**Success Criteria**:
- Create 1000 test comments in < 5 seconds
- Query threaded comments in < 100ms
- Database size < 10 MB for 1000 locations + 5000 comments

#### Module 2: Comment UI and Editor (Week 3-4)
**Deliverables**:
- Comment list widget (threaded display)
- Comment editor with Markdown toolbar
- Voice-to-text integration
- Photo attachment workflow
- Tag selection UI

**Success Criteria**:
- Editor auto-saves every 5 seconds
- Voice transcription accuracy > 80%
- Photo attach time < 2 seconds

#### Module 3: GPS and Location Capture (Week 2-3, parallel with Module 1)
**Deliverables**:
- GPS service wrapper
- Location creation form
- GPS accuracy validation
- Manual GPS entry fallback

**Success Criteria**:
- GPS capture in < 10 seconds
- Accuracy < 20 meters in good signal
- Graceful degradation in poor signal

#### Module 4: Offline Map Integration (Week 4-5)
**Deliverables**:
- MBTiles integration
- Location marker rendering
- Map navigation (pan, zoom)
- "Near Me" search radius

**Success Criteria**:
- Map loads in < 2 seconds
- Smooth rendering of 1000 markers
- Offline tiles work without network

#### Module 5: Sync Protocol Implementation (Week 6-7)
**Deliverables**:
- API client for AUPAT Core
- Upload/download sync logic
- Conflict resolution algorithms
- Retry queue for failed syncs
- Background sync service

**Success Criteria**:
- Sync 100 comments in < 30 seconds on WiFi
- Zero data loss during conflict resolution
- Background sync triggers every 30 minutes

#### Module 6: Testing and Polish (Week 8-9)
**Deliverables**:
- Unit tests (80% coverage)
- Integration tests (critical paths)
- Performance profiling
- Bug fixes and refinements
- User acceptance testing

**Success Criteria**:
- All tests pass
- No critical bugs
- App runs for 8 hours without crash
- Memory usage < 200 MB

### 6.2 Implementation Timeline

```
Week 1-2:   Module 1 (Database)
Week 2-3:   Module 3 (GPS) - parallel
Week 3-4:   Module 2 (Comments UI)
Week 4-5:   Module 4 (Maps)
Week 6-7:   Module 5 (Sync)
Week 8-9:   Module 6 (Testing)
Week 10:    Release candidate, final testing
```

**Total Duration**: 10 weeks (2.5 months)

---

## 7. WWYDD (What Would You Do Differently)

### 7.1 Alternative Architectures Considered

**1. Firebase Firestore for Sync Instead of Custom API**
- **Pros**: Built-in offline sync, real-time updates, conflict resolution
- **Cons**: Vendor lock-in, monthly costs, less control over data
- **Verdict**: Custom API preferred for BPL (no vendor dependency)

**2. CRDTs (Conflict-Free Replicated Data Types) for Comments**
- **Pros**: Automatic conflict resolution, no central server needed
- **Cons**: Complex implementation, larger payload sizes, debugging harder
- **Verdict**: Last-write-wins is simpler, adequate for single-user mobile

**3. GraphQL Instead of REST for Sync API**
- **Pros**: Single endpoint, fetch only needed fields, typed schema
- **Cons**: More complex than REST, overkill for simple sync
- **Verdict**: REST is KISS, adequate for our needs

**4. React Native Instead of Flutter**
- **Pros**: JavaScript ecosystem, web dev familiarity
- **Cons**: Slower performance, worse offline support, more dependencies
- **Verdict**: Flutter is better for offline-first, native performance

### 7.2 Future Enhancements (Beyond v1.0)

**1. Collaborative Comments** (Multi-user mode)
- Multiple users exploring same location
- Real-time comment updates via WebSockets
- User attribution and permissions

**2. Comment Search and Filtering**
- Full-text search in comment text
- Filter by type, date range, author, tags
- Saved search queries

**3. Export Comments to PDF Report**
- Generate field report from location comments
- Include photos, map, timeline
- Email or share PDF

**4. Voice Memos as First-Class Comments**
- Record voice note → auto-transcribe → create comment
- Playback voice memo in app
- Attach voice to existing comment

**5. Offline AI Image Tagging**
- On-device ML model (TensorFlow Lite)
- Auto-tag photos: "asbestos", "graffiti", "structural_damage"
- Suggest comment tags based on photos

**6. Comment Templates**
- Pre-defined comment structures (safety checklist, historical research)
- Quick-fill common observations
- User-customizable templates

### 7.3 Potential Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Sync conflicts lose user data | High | Medium | Implement "duplicate on conflict" strategy |
| GPS accuracy poor indoors | Medium | High | Allow manual GPS entry, warn user |
| MBTiles file too large for app bundle | Medium | Low | Generate smaller region, lower max zoom |
| Background sync drains battery | Medium | Medium | WiFi-only, battery checks, user control |
| Voice transcription inaccurate | Low | Medium | Keep audio file, allow manual correction |
| SQLite database corruption | High | Low | WAL mode, auto-backups, integrity checks |

---

## 8. Security and Privacy Considerations

### 8.1 Data Security

**Local Database Encryption** (Optional for sensitive locations):
```dart
// lib/services/database/encrypted_database.dart
import 'package:sqflite_sqlcipher/sqflite.dart';

Future<Database> openEncryptedDatabase(String password) async {
  final dbPath = await getDatabasesPath();
  return await openDatabase(
    join(dbPath, 'aupat_mobile.db'),
    password: password,  // SQLCipher encryption
    version: 1,
  );
}
```

**Considerations**:
- Encryption adds 10-20% performance overhead
- User must remember password (no cloud recovery)
- Useful for locations with sensitive information (private property, safety concerns)

**API Authentication**:
- Mobile API key stored in secure storage (flutter_secure_storage)
- HTTPS-only communication with desktop
- Certificate pinning for Cloudflare tunnel

### 8.2 Privacy Design

**Minimal Data Collection**:
- No analytics or telemetry by default
- GPS only captured when user explicitly adds location
- Photos stay on device until manual sync

**User Control**:
- Settings toggle: "Auto-sync on WiFi" (default: ON)
- Settings toggle: "Include GPS in comments" (default: ON)
- Clear option: "Delete all unsynced data" (for abandoning exploration session)

---

## 9. Testing Strategy

### 9.1 Unit Tests

```dart
// test/services/comment_dao_test.dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('CommentDAO', () {
    late Database testDb;
    late CommentDAO dao;

    setUp(() async {
      testDb = await openTestDatabase();
      dao = CommentDAO(testDb);
    });

    test('Insert comment with attachments', () async {
      final comment = Comment(
        commentId: 'test-001',
        locUuid: 'loc-001',
        commentText: 'Test comment',
        commentType: 'note',
        createdAt: DateTime.now().toIso8601String(),
      );

      await dao.insert(comment);

      final retrieved = await dao.getById('test-001');
      expect(retrieved.commentText, 'Test comment');
    });

    test('Get threaded comments', () async {
      // Insert parent and child comments
      await dao.insert(Comment(commentId: 'parent', locUuid: 'loc-001', ...));
      await dao.insert(Comment(commentId: 'child', parentCommentId: 'parent', ...));

      final thread = await dao.getThreadedComments('loc-001');
      expect(thread.length, 1); // One top-level
      expect(thread[0].replies.length, 1); // One reply
    });
  });
}
```

### 9.2 Integration Tests

```dart
// integration_test/offline_comment_flow_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Create comment offline, sync when online', (tester) async {
    // 1. Launch app
    await tester.pumpWidget(MyApp());
    await tester.pumpAndSettle();

    // 2. Navigate to location
    await tester.tap(find.text('Abandoned Factory A'));
    await tester.pumpAndSettle();

    // 3. Open comment editor
    await tester.tap(find.byIcon(Icons.add_comment));
    await tester.pumpAndSettle();

    // 4. Write comment
    await tester.enterText(find.byType(TextField), 'Integration test comment');

    // 5. Save (offline)
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    // 6. Verify "not synced" indicator
    expect(find.byIcon(Icons.sync_disabled), findsOneWidget);

    // 7. Trigger sync (simulate WiFi)
    await tester.tap(find.text('Sync Now'));
    await tester.pumpAndSettle();

    // 8. Verify "synced" indicator
    expect(find.byIcon(Icons.check_circle), findsOneWidget);
  });
}
```

### 9.3 Performance Benchmarks

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Insert 1000 comments | < 5 seconds | SQLite batch insert |
| Query threaded comments (100 items) | < 100ms | DAO query time |
| Render comment list (100 items) | < 500ms | Widget build time |
| Sync 100 comments to server | < 30 seconds | Network round-trip |
| Upload 10 photos (2MB each) | < 60 seconds | Immich upload API |
| Map load with 1000 markers | < 2 seconds | flutter_map render |

---

## 10. Documentation Deliverables

### 10.1 User Guide

**Topics**:
- Getting Started: First location, first comment
- Writing field notes: Markdown basics, voice memos
- Attaching photos and organizing with tags
- Understanding sync status and conflict resolution
- Offline map navigation and GPS capture
- Settings and customization

### 10.2 Developer Guide

**Topics**:
- Setting up development environment
- Database schema and migrations
- Adding new comment types
- Extending sync protocol
- Testing strategies
- Building and releasing

### 10.3 API Documentation

**Endpoints**:
- POST /api/sync/mobile - Full sync request/response
- GET /api/sync/mobile/changes - Pull changes from server
- POST /api/locations/{uuid}/comments - Create comment
- PUT /api/comments/{id} - Update comment
- DELETE /api/comments/{id} - Delete comment

---

## 11. Success Metrics and KPIs

### 11.1 Technical Metrics

- **Sync Success Rate**: > 99% (with retry queue)
- **Offline Availability**: 100% (all core features work offline)
- **Data Loss Rate**: 0% (conflicts preserve data)
- **App Crash Rate**: < 0.1% of sessions
- **Battery Drain**: < 5% per hour of active use

### 11.2 User Experience Metrics

- **Time to Add Comment**: < 30 seconds (capture → write → save)
- **GPS Capture Time**: < 10 seconds in good signal
- **Photo Attach Time**: < 2 seconds per photo
- **Sync Wait Time**: < 60 seconds for typical session (20 comments)

### 11.3 Acceptance Criteria for Release

- [ ] All 6 modules complete and tested
- [ ] 80% unit test coverage
- [ ] All integration tests pass
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] User acceptance testing by 3+ field testers
- [ ] Zero critical bugs
- [ ] Battery usage validated on iOS and Android
- [ ] Sync works on poor WiFi (< 1 Mbps)

---

## 12. Appendix: Code Examples

### 12.1 Complete Comment Model

```dart
// lib/models/comment.dart
class Comment {
  final String commentId;
  final String locUuid;
  final String? parentCommentId;

  final String commentText;
  final String commentType;

  final String createdAt;
  final String? updatedAt;
  final String? authorDeviceId;

  final bool hasPhotos;
  final bool hasAudio;
  final int photoCount;

  final bool synced;
  final String? serverTimestamp;
  final bool deleted;

  final double? gpsLat;
  final double? gpsLon;
  final double? gpsAccuracy;

  // Transient (not stored in DB)
  List<Comment> replies = [];
  List<CommentAttachment> attachments = [];

  Comment({
    required this.commentId,
    required this.locUuid,
    this.parentCommentId,
    required this.commentText,
    this.commentType = 'note',
    required this.createdAt,
    this.updatedAt,
    this.authorDeviceId,
    this.hasPhotos = false,
    this.hasAudio = false,
    this.photoCount = 0,
    this.synced = false,
    this.serverTimestamp,
    this.deleted = false,
    this.gpsLat,
    this.gpsLon,
    this.gpsAccuracy,
  });

  Map<String, dynamic> toMap() {
    return {
      'comment_id': commentId,
      'loc_uuid': locUuid,
      'parent_comment_id': parentCommentId,
      'comment_text': commentText,
      'comment_type': commentType,
      'created_at': createdAt,
      'updated_at': updatedAt,
      'author_device_id': authorDeviceId,
      'has_photos': hasPhotos ? 1 : 0,
      'has_audio': hasAudio ? 1 : 0,
      'photo_count': photoCount,
      'synced': synced ? 1 : 0,
      'server_timestamp': serverTimestamp,
      'deleted': deleted ? 1 : 0,
      'gps_lat': gpsLat,
      'gps_lon': gpsLon,
      'gps_accuracy': gpsAccuracy,
    };
  }

  factory Comment.fromMap(Map<String, dynamic> map) {
    return Comment(
      commentId: map['comment_id'],
      locUuid: map['loc_uuid'],
      parentCommentId: map['parent_comment_id'],
      commentText: map['comment_text'],
      commentType: map['comment_type'],
      createdAt: map['created_at'],
      updatedAt: map['updated_at'],
      authorDeviceId: map['author_device_id'],
      hasPhotos: map['has_photos'] == 1,
      hasAudio: map['has_audio'] == 1,
      photoCount: map['photo_count'],
      synced: map['synced'] == 1,
      serverTimestamp: map['server_timestamp'],
      deleted: map['deleted'] == 1,
      gpsLat: map['gps_lat'],
      gpsLon: map['gps_lon'],
      gpsAccuracy: map['gps_accuracy'],
    );
  }
}
```

### 12.2 Complete Sync Service

```dart
// lib/services/sync/sync_service.dart
class SyncService {
  final ApiClient apiClient;
  final CommentDAO commentDAO;
  final AttachmentDAO attachmentDAO;
  final LocationDAO locationDAO;

  SyncService({
    required this.apiClient,
    required this.commentDAO,
    required this.attachmentDAO,
    required this.locationDAO,
  });

  Future<SyncResult> syncAll() async {
    try {
      // 1. Gather unsynced data
      final unsyncedComments = await commentDAO.getUnsyncedComments();
      final unsyncedLocations = await locationDAO.getUnsyncedLocations();
      final unsyncedAttachments = await attachmentDAO.getUnsyncedAttachments();

      // 2. Upload to server
      final syncRequest = SyncRequest(
        deviceId: await getDeviceId(),
        lastSyncTimestamp: await getLastSyncTimestamp(),
        newLocations: unsyncedLocations,
        newComments: unsyncedComments,
        pendingAttachments: unsyncedAttachments,
      );

      final syncResponse = await apiClient.post('/api/sync/mobile', syncRequest.toJson());

      // 3. Handle conflicts
      for (var conflict in syncResponse.conflicts) {
        await ConflictResolver().resolve(conflict);
      }

      // 4. Mark items as synced
      for (var comment in unsyncedComments) {
        await commentDAO.markSynced(comment.commentId, syncResponse.serverTimestamp);
      }

      // 5. Upload attachments
      for (var uploadUrl in syncResponse.uploadUrls) {
        await uploadAttachment(uploadUrl.attachmentId, uploadUrl.url);
      }

      // 6. Download changes from server
      await downloadServerChanges(syncResponse.serverTimestamp);

      // 7. Save sync timestamp
      await saveLastSyncTimestamp(syncResponse.serverTimestamp);

      return SyncResult.success(syncResponse);

    } catch (e) {
      print('Sync failed: $e');
      return SyncResult.failure(e.toString());
    }
  }

  Future<void> downloadServerChanges(String since) async {
    final changes = await apiClient.get('/api/sync/mobile/changes?since=$since');

    // Insert new locations, comments from server
    for (var location in changes.newLocations) {
      await locationDAO.insert(location, fromServer: true);
    }

    for (var comment in changes.newComments) {
      await commentDAO.insert(comment, fromServer: true);
    }

    // Handle deletions
    for (var deletedCommentId in changes.deletedComments) {
      await commentDAO.markDeleted(deletedCommentId);
    }
  }

  Future<void> uploadAttachment(String attachmentId, String url) async {
    final attachment = await attachmentDAO.getById(attachmentId);
    // ... (upload implementation from section 4.3)
  }
}
```

---

## 13. Summary and Next Steps

### 13.1 Project Summary

This mobile app outline provides a comprehensive, offline-first field data collection system for AUPAT. The hierarchical comment system with rich media attachments enables detailed field documentation while exploring abandoned locations. The conflict-free sync protocol ensures data integrity across desktop and mobile platforms.

**Key Innovations**:
- Offline-first architecture (works 100% without internet)
- Hierarchical threaded comments with media attachments
- Voice-to-text field notes for hands-free documentation
- Conflict resolution that never loses user data
- MBTiles offline maps for navigation in remote areas

**Engineering Principles Applied**:
- **KISS**: Simple SQLite database, standard REST API, no over-engineering
- **BPL**: Flutter and SQLite are stable for 10+ years, no vendor lock-in
- **BPA**: Industry-standard sync patterns, proven conflict resolution
- **DRETW**: Use flutter_map, sqflite, standard packages - no custom wheels
- **NME**: Professional documentation throughout

### 13.2 Implementation Roadmap

**Phase 1: Foundation** (Weeks 1-3)
- Set up Flutter project structure
- Implement database schema and DAOs
- GPS service and location capture
- Basic UI scaffolding

**Phase 2: Core Features** (Weeks 4-6)
- Comment editor with Markdown support
- Photo attachment workflow
- Offline map with MBTiles
- Comment threading and display

**Phase 3: Sync** (Weeks 7-8)
- API client implementation
- Sync protocol with conflict resolution
- Background sync service
- Retry queue for failures

**Phase 4: Polish** (Weeks 9-10)
- Testing (unit, integration, performance)
- Bug fixes and optimizations
- User acceptance testing
- Documentation

**Total Timeline**: 10 weeks from start to release candidate

### 13.3 Next Actions

1. **Review and Approval**: Stakeholder review of this outline
2. **Prototype**: Build minimal viable prototype (1-2 weeks)
3. **Validation**: Test sync protocol with AUPAT Core API
4. **Full Implementation**: Follow Module 1-6 build plan
5. **Field Testing**: Real-world testing at abandoned locations
6. **Release**: v1.0 release to iOS TestFlight and Android Play Store

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Author**: AUPAT Development Team
**Status**: Ready for Implementation
