# Where to Change Settings in AUPAT

## API Server Settings

### Port Configuration
**File**: `app.py`
**Line**: 73
**Current**: `app.run(host='0.0.0.0', port=5000, debug=False)`

To change port:
```python
app.run(host='0.0.0.0', port=YOUR_PORT, debug=False)
```

**Also update**: `desktop/src/main/index.js` line 27 to match

### Database Path
**File**: `app.py`
**Line**: 31
**Current**: `app.config['DB_PATH'] = os.environ.get('DB_PATH', '/app/data/aupat.db')`

Set via environment variable:
```bash
export DB_PATH=/your/custom/path/aupat.db
python3 app.py
```

---

## Desktop App Settings

### Default Connection Settings
**File**: `desktop/src/main/index.js`
**Lines**: 25-32

```javascript
const store = new Store({
  defaults: {
    apiUrl: 'http://localhost:5000',      // AUPAT API
    immichUrl: 'http://localhost:2283',   // Immich photo server
    archiveboxUrl: 'http://localhost:8001', // ArchiveBox
    mapCenter: { lat: 42.6526, lng: -73.7562 }, // Default map center
    mapZoom: 10  // Default zoom level
  }
});
```

**Note**: Users can override these in Settings menu within the app.
Desktop settings are stored in Electron's user data directory.

---

## State and Type Configuration

### Custom States
**File**: `scripts/normalize.py`
**Line**: 54-62 (Reference list only - not enforced)

Custom states are **fully supported**. The `VALID_US_STATES` list is for reference only.

### Custom Location Types
**File**: `scripts/normalize.py`
**Line**: 64-70 (Reference list only - not enforced)

Custom types are **fully supported**. The `VALID_LOCATION_TYPES` list is for reference only.

### Type Mappings (Auto-Correction)
**File**: `data/location_type_mapping.json`

Add custom mappings to auto-correct common variations:
```json
{
  "mappings": {
    "your-custom-type": "canonical-type",
    "hospital": "healthcare",
    ...
  }
}
```

---

## Map Configuration

### Default Map Center
**File**: `desktop/src/main/index.js`
**Line**: 29
**Current**: Albany, NY `{ lat: 42.6526, lng: -73.7562 }`

Change to your region:
```javascript
mapCenter: { lat: YOUR_LAT, lng: YOUR_LNG },
```

### Map Tile Provider
**File**: `desktop/src/renderer/lib/Map.svelte`
**Line**: 43-47

Change OpenStreetMap tiles:
```javascript
L.tileLayer('https://your-tile-server/{z}/{x}/{y}.png', {
  attribution: 'Your attribution',
  maxZoom: 19
}).addTo(map);
```

---

## Runtime Settings (In-App)

Desktop app provides Settings menu for runtime configuration:
- API URL (server endpoint)
- Immich URL (photo server endpoint)
- ArchiveBox URL (archive server endpoint)
- Map center and zoom preferences

**Access**: Click "Settings" in the desktop app sidebar

**Storage**: Settings are persisted via Electron Store in:
- macOS: `~/Library/Application Support/aupat-desktop/config.json`
- Linux: `~/.config/aupat-desktop/config.json`
- Windows: `%APPDATA%\aupat-desktop\config.json`

---

## Quick Reference Table

| Setting | File | Line | Can Change At Runtime? |
|---------|------|------|----------------------|
| API Port | app.py | 73 | No (restart required) |
| Database Path | app.py | 31 | No (restart required) |
| Desktop API URL | index.js | 27 | Yes (Settings menu) |
| Desktop Immich URL | index.js | 28 | Yes (Settings menu) |
| Desktop ArchiveBox URL | index.js | 29 | Yes (Settings menu) |
| Map Center | index.js | 30 | Yes (Settings menu) |
| Map Zoom | index.js | 31 | Yes (Settings menu) |
| Custom States | normalize.py | 54-62 | N/A (always allowed) |
| Custom Types | normalize.py | 64-70 | N/A (always allowed) |
| Type Mappings | location_type_mapping.json | - | No (restart required) |

---

## Environment Variables

All environment variables (highest priority):

```bash
# Database location
export DB_PATH=/path/to/aupat.db

# Server port (optional, defaults to 5000)
export PORT=5000
```

---

## Recommended Workflow

1. **Initial Setup**: Edit default configs in source files
2. **Development**: Use environment variables for overrides
3. **Production**: Set via desktop app Settings menu for user preferences
4. **Custom States/Types**: Just use them! No configuration needed.
