# Abandoned Upstate App - Comprehensive Revamp Plan

**Version:** 0.2.0 Redesign
**Date:** 2025-11-18
**Session ID:** 01RocQFx3msWXvZ5JwMb7pmw
**Branch:** claude/redesign-abandoned-upstate-app-01RocQFx3msWXvZ5JwMb7pmw

---

## Executive Summary

This revamp transforms AUPAT from a generic archive tool into the **Abandoned Upstate** experience - a location-centric digital archive that feels like a blog-style exploration platform for abandoned locations in Upstate New York.

### Key Principles
- **Archive Mindset**: Work with whatever data we have - precise GPS, city/state only, or just a name
- **Blog-Style Experience**: Each location gets a dedicated "page" with rich content presentation
- **Abandoned Upstate Brand**: Dark, moody, exploration-focused aesthetic from abandonedupstate.com
- **Flexibility Over Constraints**: No predetermined types, no rigid validation that rejects partial data

---

## Critical User Requirements

### 1. Archive Philosophy - "Take What We Can Get"
**Problem**: Current import validation rejects locations without precise GPS coordinates
**User Quote**: *"This is an archive - we take what information we can get sometimes. Knowing the city and state, why can't you add it to the map?"*

**Solution**: Implement geocoding fallback system
- **Full GPS coordinates** → precise marker placement
- **City + State only** → geocode to city center, mark as "approximate location"
- **County + State** → geocode to county center
- **State only** → geocode to state center
- **Name + description but no location** → archive anyway, visual indicator for "no map data yet"

**Visual Indicators**:
- Precise locations: Solid marker
- Approximate locations: Dotted/dashed marker with radius circle
- No location data: Grayed out, searchable, but not mappable

---

### 2. Location Types - No Predetermined Options
**Problem**: Import screens have predetermined type dropdowns
**User Quote**: *"Types should NOT be pre-determined in the location import screen"*

**Solution**: Free-form text entry for location types
- Replace all type dropdowns with text input fields
- Support auto-complete suggestions based on existing types in database
- Allow users to create new types on-the-fly
- Display type statistics/counts in dashboard for organization

---

### 3. KML/KMZ Import - Actually Support It
**Problem**: Despite claims of KML/KMZ support, files are rejected
**User Quote**: *"We still do not have support for .KML no matter how much you insist we do, the file format is rejected by the desktop app"*

**Root Cause Analysis**:
- Frontend: `MapImportDialog.svelte:112` uses `selectedFile.text()` which corrupts binary KMZ data
- Backend: Expects bytes for KML/KMZ but receives corrupted text
- **Fix**: Read KMZ as ArrayBuffer, convert to base64, send to backend, decode on server

**Testing Requirements**:
- Test with actual KML export from Google Maps
- Test with KMZ (zipped KML) files
- Test with nested KMZ structures (multiple KML files inside)
- Validate coordinate extraction (KML uses lon,lat order)

---

### 4. Dedicated Location Pages - Blog-Style Design
**Problem**: Current UI shows locations in a sidebar overlay - not immersive
**User Quote**: *"Locations Each Need A Dedicated 'Page' When you click on it. Dashboard Inspired - break down all technical info who what where when why. Blog Style. Show Images. Clickable hyper links, etc - review my website abandonedupstate.com"*

**Solution**: Full-page location detail view inspired by abandonedupstate.com v0.1.0

**Page Structure** (Blog-Style Layout):
```
┌────────────────────────────────────────────────────────┐
│ [← Back to Map]     ABANDONED UPSTATE                  │
├────────────────────────────────────────────────────────┤
│                                                         │
│              HERO IMAGE (full-width)                    │
│                                                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│   LOCATION NAME (large, impact font)                   │
│   ───────────────────────                              │
│   Type: Industrial • State: NY • Status: Abandoned     │
│                                                         │
│   THE STORY                                            │
│   ──────────                                           │
│   [Rich text description with markdown support]        │
│   [Clickable hyperlinks]                               │
│   [Embedded videos if available]                       │
│                                                         │
│   WHERE                                                │
│   ─────                                                │
│   📍 Address: 123 Main St, Albany, NY 12345           │
│   🗺️ GPS: 42.6526°N, -73.7562°W (precise)            │
│   [Interactive mini-map with marker]                   │
│                                                         │
│   WHEN                                                 │
│   ────                                                 │
│   📅 Built: 1920s                                      │
│   📅 Abandoned: 1985                                   │
│   📅 Last Visited: Nov 18, 2025                        │
│   📅 Added to Archive: Nov 17, 2025                    │
│                                                         │
│   IMAGES (15)                                          │
│   ──────────                                           │
│   [Grid gallery - 3 columns, lazy load]               │
│   [Click to open lightbox with EXIF data]             │
│                                                         │
│   ARCHIVED URLS                                        │
│   ─────────────                                        │
│   🔗 Wikipedia Article (archived Nov 2025)            │
│   🔗 Historical Society Page (archived Oct 2025)      │
│   [+ Add new URL to archive]                           │
│                                                         │
│   RELATED LOCATIONS                                    │
│   ──────────────────                                   │
│   • Other Industrial sites in Albany County            │
│   • Nearby locations within 5 miles                    │
│                                                         │
└────────────────────────────────────────────────────────┘
```

**Implementation**:
- Create new `LocationPage.svelte` component
- Add routing: `/location/:uuid`
- Support deep linking (shareable URLs)
- Add print stylesheet for archival purposes
- Support markdown in description field
- Auto-link URLs in text fields

---

### 5. App Rebranding - "Abandoned Upstate"
**Problem**: Current app is branded as "AUPAT Desktop" - too technical
**User Quote**: *"call the app 'Abandoned Upstate' now"*

**Changes Required**:
- **App Name**: "AUPAT" → "Abandoned Upstate"
- **Product Name**: Update in `package.json`
- **Window Title**: Show "Abandoned Upstate - [Location Name]"
- **App ID**: `com.aupat.desktop` → `com.abandonedupstate.app`
- **Menu Bar**: Update all references
- **About Dialog**: Add branding, link to abandonedupstate.com

---

### 6. App Icon Update
**Problem**: Need to use proper app icon
**User Quote**: *"Update the app to use 'App Icon.png'"*

**Current State**:
- Icon file: `/home/user/aupat/Abandoned Upstate.png` (76KB PNG)
- Currently used: `/home/user/aupat/desktop/src/renderer/assets/logo.png` (same file)

**Required Formats** (for electron-builder):
- macOS: `icon.icns` (512x512, 256x256, 128x128, 64x64, 32x32, 16x16)
- Linux: `icon.png` (512x512 recommended)
- Windows: `icon.ico` (if Windows support added later)

**Steps**:
1. Extract logo from `Abandoned Upstate.png`
2. Generate multi-resolution ICNS for macOS
3. Create 512x512 PNG for Linux
4. Update `package.json` build config with icon paths
5. Test packaged app shows correct icon in Dock/taskbar

---

### 7. Mac Auto-Update Mechanism
**Problem**: Users need auto-updates when pulling from git
**User Quote**: *"Make an included Mac app that gets auto updated if needed with we do fresh pulls"*

**Solution**: Electron auto-update with GitHub releases

**Implementation Options**:

**Option A: electron-updater (Recommended)**
- Uses electron-builder's auto-update system
- Checks GitHub releases for new versions
- Downloads and installs `.dmg` or `.zip` updates
- Supports delta updates (smaller downloads)

**Option B: Git-based updates (Development Mode)**
- Check for new commits on branch
- Pull latest changes
- Rebuild Electron app
- Restart app
- **Note**: Only works in dev environment, not packaged apps

**Recommended Approach**: Hybrid
- **Development**: Git-based updates (when running from source)
- **Production**: electron-updater (when running packaged .app)

**Configuration**:
```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "bizzlechizzle",
      "repo": "aupat"
    }
  }
}
```

**Auto-Update Flow**:
1. App checks for updates on startup (configurable interval)
2. If new version available, show notification
3. Download in background
4. Prompt user to restart and install
5. Apply update on restart

---

## Brand Guide

### Colors (Extracted from abandonedupstate.com v0.1.0 + Current Logo)

#### Primary Palette
```css
/* Core Brand Colors */
--au-black: #000000;           /* Background, primary text, logo bg */
--au-white: #FFFFFF;           /* Logo text, highlights, borders */
--au-cream: #fffbf7;           /* Light theme background */
--au-dark-gray: #474747;       /* Dark theme background */
--au-text-dark: #454545;       /* Body text (light theme) */
--au-text-light: #fffbf7;      /* Body text (dark theme) */
```

#### Accent Colors
```css
/* Accent & Highlight */
--au-accent-brown: #b9975c;    /* Earthy, vintage accent */
--au-accent-gold: #d4af37;     /* Highlight, special features */
```

#### UI State Colors
```css
/* Status Indicators */
--au-success: #5a7f5c;         /* Muted green (archive success) */
--au-warning: #b9975c;         /* Brown/gold (approximate GPS) */
--au-error: #8b4c4c;           /* Muted red (error states) */
--au-info: #5c7f99;            /* Muted blue (info) */
```

#### Map-Specific Colors
```css
/* Map Markers & Clusters */
--au-marker-precise: #000000;      /* Precise GPS coordinates */
--au-marker-approximate: #b9975c;  /* City/state only */
--au-marker-none: #cccccc;         /* No location data */
--au-cluster-bg: rgba(185, 151, 92, 0.8);  /* Cluster background */
--au-cluster-text: #FFFFFF;        /* Cluster count text */
```

### Typography

#### Font Families
```css
/* Headings - Bold, Impact */
--au-font-heading: 'Impact', 'Arial Black', 'Roboto Condensed', sans-serif;
/* Logo uses: Impact, bold italic, condensed, uppercase */

/* Body - Serif, Readable */
--au-font-body: 'Lora', 'Georgia', 'Times New Roman', serif;

/* Monospace - Technical Data */
--au-font-mono: 'Roboto Mono', 'Courier New', monospace;
```

#### Type Scale
```css
--au-text-xs: 0.75rem;    /* 12px - captions, metadata */
--au-text-sm: 0.875rem;   /* 14px - small body text */
--au-text-base: 1rem;     /* 16px - body text */
--au-text-lg: 1.125rem;   /* 18px - large body */
--au-text-xl: 1.25rem;    /* 20px - subheadings */
--au-text-2xl: 1.5rem;    /* 24px - section headers */
--au-text-3xl: 1.875rem;  /* 30px - page titles */
--au-text-4xl: 2.25rem;   /* 36px - hero text */
```

### UI Components

#### Buttons
```css
/* Primary Action (Archive, Import, Save) */
.btn-primary {
  background: var(--au-black);
  color: var(--au-white);
  border: 2px solid var(--au-black);
  font-family: var(--au-font-heading);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 12px 24px;
  font-weight: bold;
}

.btn-primary:hover {
  background: var(--au-accent-brown);
  border-color: var(--au-accent-brown);
}

/* Secondary Action (Cancel, Back) */
.btn-secondary {
  background: transparent;
  color: var(--au-black);
  border: 2px solid var(--au-black);
  font-family: var(--au-font-heading);
  text-transform: uppercase;
}

.btn-secondary:hover {
  background: var(--au-black);
  color: var(--au-white);
}
```

#### Map Markers

**Precise Location Marker**:
```
  ▲
 ███   Black triangle (NY state silhouette simplified)
  █
```

**Approximate Location Marker**:
```
  ⊙    Circle with dot, brown/gold color
 ╱ ╲   Dashed radius circle showing uncertainty
```

**No Location Marker**:
```
  ?    Gray question mark, grayed out appearance
```

### Layout Grid
- **Desktop**: 12-column grid, max-width 1200px
- **Tablet**: 8-column grid, max-width 768px
- **Mobile**: 4-column grid, full-width

### Spacing Scale
```css
--au-space-1: 0.25rem;  /* 4px */
--au-space-2: 0.5rem;   /* 8px */
--au-space-3: 0.75rem;  /* 12px */
--au-space-4: 1rem;     /* 16px */
--au-space-6: 1.5rem;   /* 24px */
--au-space-8: 2rem;     /* 32px */
--au-space-12: 3rem;    /* 48px */
--au-space-16: 4rem;    /* 64px */
```

### Dark Mode Support
**Toggle**: Available in settings, persists to electron-store
**Default**: System preference detection

**Dark Theme Overrides**:
```css
[data-theme="dark"] {
  --au-bg-primary: var(--au-dark-gray);
  --au-text-primary: var(--au-text-light);
  --au-bg-secondary: #2a2a2a;
  --au-border: #666666;
}
```

---

## Technical Implementation Plan

### Phase 1: Core Fixes (Critical Path)

#### 1.1 Fix KML/KMZ Import
**Files to Modify**:
- `desktop/src/renderer/lib/MapImportDialog.svelte`
- `scripts/api_maps.py`

**Changes**:
```javascript
// MapImportDialog.svelte - Update file reading
async function parseFile() {
  if (!selectedFile) return;

  let content;

  // Read KMZ as binary, others as text
  if (fileFormat === 'kmz') {
    const arrayBuffer = await selectedFile.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);
    // Convert to base64 for JSON transport
    content = btoa(String.fromCharCode(...bytes));
  } else if (fileFormat === 'kml') {
    // KML is XML text, but backend needs encoding info
    content = await selectedFile.text();
  } else {
    // CSV, GeoJSON as text
    content = await selectedFile.text();
  }

  // Send to backend with encoding flag
  const response = await fetch(`${apiUrl}/api/maps/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: fileName,
      format: fileFormat,
      content: content,
      is_base64: fileFormat === 'kmz'  // Flag for binary data
    })
  });
}
```

```python
# api_maps.py - Update parsing endpoint
@api_maps.route('/parse', methods=['POST'])
def parse_map_file():
    data = request.get_json()
    content = data.get('content', '')
    file_format = data.get('format', '').lower()
    is_base64 = data.get('is_base64', False)

    # Decode base64 for binary formats
    if is_base64:
        import base64
        content_bytes = base64.b64decode(content)
    elif file_format == 'kml':
        content_bytes = content.encode('utf-8')
    else:
        content_bytes = content  # CSV, GeoJSON stay as text

    if file_format == 'kml':
        locations, errors = parse_kml_map(content_bytes, is_kmz=False)
    elif file_format == 'kmz':
        locations, errors = parse_kml_map(content_bytes, is_kmz=True)
```

**Testing**:
- [ ] Import Google Maps KML export
- [ ] Import Google Earth KMZ file
- [ ] Import KML with extended data
- [ ] Import KMZ with multiple placemarks
- [ ] Verify coordinates are correct (KML uses lon,lat order)

---

#### 1.2 Remove Predetermined Location Types
**Files to Modify**:
- `desktop/src/renderer/lib/LocationForm.svelte`
- `desktop/src/renderer/lib/MapImportDialog.svelte`
- Database: No schema change needed (type is already TEXT)

**Changes**:
```svelte
<!-- LocationForm.svelte - Replace dropdown with text input -->
<div class="form-group">
  <label for="type">Type</label>
  <input
    id="type"
    type="text"
    bind:value={formData.type}
    placeholder="e.g., industrial, residential, commercial"
    list="type-suggestions"
  />
  <!-- Datalist for autocomplete from existing types -->
  <datalist id="type-suggestions">
    {#each existingTypes as type}
      <option value={type} />
    {/each}
  </datalist>
</div>
```

**Backend Support**:
```python
# Add endpoint to get unique types for autocomplete
@api_routes.route('/api/types', methods=['GET'])
def get_location_types():
    """Get all unique location types with counts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT type, COUNT(*) as count
        FROM locations
        WHERE type IS NOT NULL AND type != ''
        GROUP BY type
        ORDER BY count DESC
    """)

    types = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
    conn.close()

    return jsonify({'types': types}), 200
```

---

#### 1.3 Implement Geocoding Fallback
**New Dependency**: Add geocoding service

**Options**:
- **Nominatim** (OpenStreetMap) - Free, no API key, rate-limited
- **Google Geocoding API** - Paid, accurate, requires API key
- **Mapbox Geocoding** - Generous free tier, requires API key

**Recommendation**: Nominatim for now (free, privacy-focused)

**New File**: `scripts/geocoding.py`
```python
import requests
import time
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "AbandonedUpstate/0.2.0"

def geocode_location(
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: str = "United States"
) -> Tuple[Optional[float], Optional[float], str]:
    """
    Geocode a location from city/state to lat/lon.

    Args:
        city: City name
        state: State abbreviation or name
        country: Country name (default: United States)

    Returns:
        Tuple of (lat, lon, confidence_level)
        confidence_level: 'city', 'county', 'state', 'none'
    """
    if not city and not state:
        return None, None, 'none'

    # Build query string
    query_parts = []
    if city:
        query_parts.append(city)
    if state:
        query_parts.append(state)
    query_parts.append(country)

    query = ", ".join(query_parts)

    try:
        # Respect Nominatim usage policy: 1 request per second
        time.sleep(1)

        response = requests.get(
            NOMINATIM_URL,
            params={
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            },
            headers={'User-Agent': USER_AGENT},
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"Geocoding failed: HTTP {response.status_code}")
            return None, None, 'none'

        results = response.json()

        if not results:
            logger.warning(f"No geocoding results for: {query}")
            return None, None, 'none'

        result = results[0]
        lat = float(result['lat'])
        lon = float(result['lon'])

        # Determine confidence based on result type
        place_type = result.get('type', '')
        if place_type in ['city', 'town', 'village']:
            confidence = 'city'
        elif place_type in ['county', 'state_district']:
            confidence = 'county'
        elif place_type == 'state':
            confidence = 'state'
        else:
            confidence = 'approximate'

        logger.info(f"Geocoded '{query}' to ({lat}, {lon}) with confidence: {confidence}")
        return lat, lon, confidence

    except Exception as e:
        logger.error(f"Geocoding error for '{query}': {e}")
        return None, None, 'none'
```

**Database Schema Update**:
```sql
-- Add GPS confidence field if not exists
ALTER TABLE locations ADD COLUMN gps_confidence TEXT;
-- Values: 'precise' (user-provided GPS), 'city', 'county', 'state', 'approximate', 'none'
```

**Integration in Import**:
```python
# In map_import.py - import_locations_to_db()

# After parsing location, before insert
if not location.get('lat') or not location.get('lon'):
    # Attempt geocoding
    from scripts.geocoding import geocode_location

    city = location.get('city')
    state = location.get('state')

    if city or state:
        lat, lon, confidence = geocode_location(city=city, state=state)
        if lat and lon:
            location['lat'] = lat
            location['lon'] = lon
            location['gps_source'] = 'geocoded'
            location['gps_confidence'] = confidence
```

**Map Display**:
- Add marker styling based on `gps_confidence`
- Show radius circle for approximate locations
- Add tooltip: "Approximate location (geocoded from city/state)"

---

### Phase 2: UI/UX Transformation

#### 2.1 Create Dedicated Location Page Component
**New File**: `desktop/src/renderer/lib/LocationPage.svelte`

**Routing**:
- Update `App.svelte` to support page navigation
- Add state management for current view: 'map', 'locations', 'location-detail', 'import', 'settings'
- Pass location UUID to LocationPage component

**Features**:
- Hero image (first image from location, or default placeholder)
- Full-width layout (not sidebar)
- Markdown rendering for description
- Interactive mini-map showing location context
- Image gallery with lightbox
- Related locations section
- Print-friendly layout
- Back button to return to map/list view

**Sample Implementation** (key sections):
```svelte
<script>
  import { onMount } from 'svelte';
  import { marked } from 'marked'; // Add marked.js for markdown

  export let locationUuid;

  let location = null;
  let images = [];
  let videos = [];
  let archives = [];
  let relatedLocations = [];

  onMount(async () => {
    // Fetch location details
    location = await window.api.locations.getById(locationUuid);
    images = await window.api.images.getByLocation(locationUuid);
    videos = await window.api.videos.getByLocation(locationUuid);
    archives = await window.api.urls.getByLocation(locationUuid);
    relatedLocations = await window.api.locations.getNearby(
      location.lat,
      location.lon,
      10000 // 10km radius
    );
  });

  function goBack() {
    // Emit event to parent to return to map
    dispatch('close');
  }
</script>

<article class="location-page">
  <header class="hero">
    {#if images.length > 0}
      <img src={images[0].url} alt={location.loc_name} />
    {:else}
      <div class="hero-placeholder">
        <span class="icon-abandoned">🏚️</span>
      </div>
    {/if}

    <button class="back-btn" on:click={goBack}>
      ← Back to Map
    </button>
  </header>

  <main class="content">
    <h1 class="location-title">{location.loc_name}</h1>

    <div class="metadata">
      <span class="type">{location.type || 'Unknown Type'}</span>
      <span class="state">{location.state}</span>
      <span class="gps-confidence">
        {location.gps_confidence === 'precise' ? '📍 Precise GPS' : '⊙ Approximate GPS'}
      </span>
    </div>

    {#if location.notes}
      <section class="story">
        <h2>The Story</h2>
        <div class="prose">
          {@html marked(location.notes)}
        </div>
      </section>
    {/if}

    <!-- WHERE, WHEN, IMAGES, ARCHIVED URLS sections... -->
  </main>
</article>
```

---

#### 2.2 Apply Abandoned Upstate Branding
**Files to Modify**:
- `desktop/src/renderer/styles/app.css` - Add CSS variables
- All `.svelte` components - Update class names, styles
- `desktop/src/renderer/App.svelte` - Update header, sidebar

**New CSS Variables File**: `desktop/src/renderer/styles/theme.css`
```css
:root {
  /* Colors */
  --au-black: #000000;
  --au-white: #FFFFFF;
  --au-cream: #fffbf7;
  --au-dark-gray: #474747;
  --au-text-dark: #454545;
  --au-text-light: #fffbf7;
  --au-accent-brown: #b9975c;
  --au-accent-gold: #d4af37;

  /* Typography */
  --au-font-heading: 'Impact', 'Arial Black', sans-serif;
  --au-font-body: 'Lora', Georgia, serif;
  --au-font-mono: 'Roboto Mono', monospace;

  /* Spacing */
  --au-space-1: 0.25rem;
  --au-space-2: 0.5rem;
  --au-space-3: 0.75rem;
  --au-space-4: 1rem;
  --au-space-6: 1.5rem;
  --au-space-8: 2rem;
  --au-space-12: 3rem;
  --au-space-16: 4rem;
}

[data-theme="dark"] {
  --au-bg-primary: var(--au-dark-gray);
  --au-text-primary: var(--au-text-light);
}

body {
  font-family: var(--au-font-body);
  background: var(--au-cream);
  color: var(--au-text-dark);
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--au-font-heading);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

**Update App Header**:
```svelte
<!-- App.svelte -->
<header class="app-header">
  <img src="./assets/logo.png" alt="Abandoned Upstate" class="logo" />
  <h1 class="app-title">ABANDONED UPSTATE</h1>
</header>
```

---

#### 2.3 Update App Metadata & Icon
**Files to Modify**:
- `desktop/package.json`
- `desktop/src/main/index.js`

**package.json Updates**:
```json
{
  "name": "abandoned-upstate",
  "productName": "Abandoned Upstate",
  "description": "Digital archive for abandoned locations in Upstate New York",
  "version": "0.2.0",
  "build": {
    "appId": "com.abandonedupstate.app",
    "productName": "Abandoned Upstate",
    "mac": {
      "category": "public.app-category.lifestyle",
      "icon": "resources/icon.icns"
    },
    "linux": {
      "icon": "resources/icon.png",
      "category": "Graphics"
    }
  }
}
```

**Generate App Icons**:
```bash
# Install icon generation tool
npm install --save-dev electron-icon-builder

# Generate from PNG
npx electron-icon-builder --input="Abandoned Upstate.png" --output=resources --flatten
```

**Window Title**:
```javascript
// desktop/src/main/index.js
mainWindow = new BrowserWindow({
  title: 'Abandoned Upstate',
  width: 1200,
  height: 800,
  // ... other options
});

// Update title when location is viewed
ipcMain.handle('update-window-title', (event, locationName) => {
  mainWindow.setTitle(`Abandoned Upstate - ${locationName}`);
});
```

---

#### 2.4 Implement Auto-Update Mechanism
**Dependencies**:
```bash
npm install electron-updater
```

**New File**: `desktop/src/main/updater.js`
```javascript
import { autoUpdater } from 'electron-updater';
import { BrowserWindow } from 'electron';
import log from 'electron-log';

let updateCheckInterval = null;

export function initAutoUpdater(mainWindow) {
  // Configure logging
  autoUpdater.logger = log;
  autoUpdater.logger.transports.file.level = 'info';

  // Check for updates every 4 hours
  updateCheckInterval = setInterval(() => {
    checkForUpdates(mainWindow);
  }, 4 * 60 * 60 * 1000);

  // Check on startup (after 10 seconds)
  setTimeout(() => {
    checkForUpdates(mainWindow);
  }, 10000);

  // Event handlers
  autoUpdater.on('update-available', (info) => {
    log.info('Update available:', info);
    mainWindow.webContents.send('update-available', info);
  });

  autoUpdater.on('update-downloaded', (info) => {
    log.info('Update downloaded:', info);
    mainWindow.webContents.send('update-downloaded', info);
  });

  autoUpdater.on('error', (err) => {
    log.error('Update error:', err);
    mainWindow.webContents.send('update-error', err.message);
  });
}

function checkForUpdates(mainWindow) {
  if (!mainWindow || mainWindow.isDestroyed()) return;

  log.info('Checking for updates...');
  autoUpdater.checkForUpdates().catch(err => {
    log.error('Failed to check for updates:', err);
  });
}

export function quitAndInstall() {
  autoUpdater.quitAndInstall();
}

export function cleanup() {
  if (updateCheckInterval) {
    clearInterval(updateCheckInterval);
  }
}
```

**Frontend Notification Component**: `desktop/src/renderer/lib/UpdateNotification.svelte`
```svelte
<script>
  import { onMount } from 'svelte';

  let updateAvailable = false;
  let updateReady = false;
  let updateInfo = null;

  onMount(() => {
    // Listen for update events from main process
    window.api.onUpdateAvailable((info) => {
      updateAvailable = true;
      updateInfo = info;
    });

    window.api.onUpdateDownloaded((info) => {
      updateReady = true;
      updateInfo = info;
    });
  });

  function installUpdate() {
    window.api.installUpdate();
  }
</script>

{#if updateReady}
  <div class="update-banner ready">
    <p>
      🎉 Update {updateInfo.version} is ready to install!
    </p>
    <button on:click={installUpdate}>Restart & Install</button>
  </div>
{:else if updateAvailable}
  <div class="update-banner downloading">
    <p>
      📥 Downloading update {updateInfo.version}...
    </p>
  </div>
{/if}
```

---

### Phase 3: Testing & Validation

#### 3.1 Manual Testing Checklist
- [ ] KML import from Google Maps export
- [ ] KMZ import with multiple placemarks
- [ ] CSV import with partial data (city/state only, no GPS)
- [ ] Location with city/state gets geocoded to approximate coordinates
- [ ] Map shows different marker styles for precise vs approximate
- [ ] Location type is free-form text input (not dropdown)
- [ ] Location detail page renders with hero image
- [ ] Markdown renders in location description
- [ ] Clickable hyperlinks work in description
- [ ] Related locations show nearby sites
- [ ] App icon displays correctly in macOS Dock
- [ ] App title is "Abandoned Upstate"
- [ ] Window title updates when viewing location
- [ ] Auto-update check runs on startup
- [ ] Update notification appears when new version available

#### 3.2 Automated Tests
**New Test File**: `desktop/tests/kml-import.spec.js`
```javascript
import { test, expect } from '@playwright/test';

test('should import KML file with placemarks', async ({ page }) => {
  await page.goto('/');

  // Click import button
  await page.click('[data-testid="import-map"]');

  // Upload KML file
  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles('./fixtures/test-map.kml');

  // Verify file detected as KML
  await expect(page.locator('text=/Format:.*KML/i')).toBeVisible();

  // Click Next
  await page.click('button:has-text("Next")');

  // Verify preview shows locations
  await expect(page.locator('text=/Valid Locations/i')).toBeVisible();
  await expect(page.locator('.stat-value')).toHaveText(/\d+/);

  // Import
  await page.click('button:has-text("Import")');

  // Verify success
  await expect(page.locator('text=/Import Complete/i')).toBeVisible();
});
```

---

### Phase 4: Documentation & Deployment

#### 4.1 Update Documentation
**Files to Update**:
- `README.md` - Update app name, features list
- `01_OVERVIEW.md` - Update project description
- Add `CHANGELOG.md` - Document v0.2.0 changes

#### 4.2 Create GitHub Release
```bash
# Tag release
git tag -a v0.2.0 -m "Abandoned Upstate v0.2.0 - Location Pages & Brand Revamp"
git push origin v0.2.0

# Build packages
cd desktop
npm run package

# Create GitHub release with DMG and AppImage
gh release create v0.2.0 \
  dist-builder/*.dmg \
  dist-builder/*.AppImage \
  --title "Abandoned Upstate v0.2.0" \
  --notes "See CHANGELOG.md for details"
```

#### 4.3 Deployment Checklist
- [ ] Version bumped to 0.2.0 in package.json
- [ ] App icon updated and tested
- [ ] Auto-updater configured with correct GitHub repo
- [ ] Mac DMG tested on clean macOS system
- [ ] Linux AppImage tested on Ubuntu/Debian
- [ ] Documentation updated
- [ ] GitHub release created
- [ ] Previous users can auto-update from v0.1.2

---

## Success Metrics

### User Experience
- [ ] User can import KML/KMZ files without errors
- [ ] User can add location with only city/state, no GPS required
- [ ] Location page feels like a blog post, not a database record
- [ ] App branding matches abandonedupstate.com aesthetic
- [ ] Updates install seamlessly without manual re-download

### Technical
- [ ] KML import success rate: 100% for valid files
- [ ] Geocoding fallback success rate: >90% for US city/state combos
- [ ] Page load time for location detail: <500ms
- [ ] Auto-update check completes in <2 seconds
- [ ] App package size: <100MB (DMG), <150MB (AppImage)

---

## Risk Assessment & Mitigation

### Risk 1: Geocoding Rate Limits (Nominatim)
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Implement 1-second delay between requests (Nominatim policy)
- Cache geocoding results in database
- Add fallback to manual GPS entry if geocoding fails
- Consider paid geocoding service (Mapbox) for production

### Risk 2: KMZ Binary Encoding Issues
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Thoroughly test with Google Maps/Earth exports
- Add detailed error logging for decode failures
- Provide clear error messages to user with file format hints

### Risk 3: Auto-Update Breaking Changes
**Probability**: Low
**Impact**: High
**Mitigation**:
- Semantic versioning (0.2.x = compatible, 0.3.0 = breaking)
- Test updates on isolated systems before release
- Provide rollback instructions in documentation
- Add update notes in release changelog

### Risk 4: Branding Font Loading
**Probability**: Low
**Impact**: Low
**Mitigation**:
- Include web-safe fallback fonts (Impact → Arial Black → sans-serif)
- Embed font files in app resources if needed
- Test on systems without Impact font installed

---

## Timeline Estimate

### Phase 1: Core Fixes (4-6 hours)
- KML/KMZ binary handling: 2 hours
- Remove predetermined types: 1 hour
- Geocoding fallback: 2-3 hours
- Testing: 1 hour

### Phase 2: UI/UX Transformation (6-8 hours)
- Location page component: 3-4 hours
- Branding (CSS, colors, fonts): 2 hours
- App metadata & icon: 1 hour
- Auto-update integration: 2 hours
- Testing: 1 hour

### Phase 3: Testing & Validation (2-3 hours)
- Manual testing: 1-2 hours
- Automated tests: 1 hour

### Phase 4: Documentation & Deployment (1-2 hours)
- Update docs: 30 min
- Create release: 30 min
- Deployment testing: 30-60 min

**Total Estimated Time**: 13-19 hours

---

## Appendix

### A. Database Schema Changes

```sql
-- Add gps_confidence column to locations table
ALTER TABLE locations ADD COLUMN gps_confidence TEXT DEFAULT 'none';

-- Update existing records with GPS to 'precise'
UPDATE locations
SET gps_confidence = 'precise'
WHERE lat IS NOT NULL AND lon IS NOT NULL AND gps_source = 'manual';

-- Create index for type autocomplete
CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(type);
```

### B. API Endpoint Additions

```
GET  /api/types                     # Get unique location types with counts
POST /api/geocode                   # Geocode city/state to lat/lon
GET  /api/locations/:id/nearby      # Get nearby locations (within radius)
```

### C. Environment Variables

```bash
# Optional: Mapbox API key for geocoding (if switching from Nominatim)
MAPBOX_API_KEY=your_key_here

# Auto-update configuration
GH_TOKEN=your_github_token  # For electron-builder publish
```

### D. Build Commands Reference

```bash
# Development
npm run dev                  # Start dev server with hot reload

# Testing
npm run test                 # Unit tests
npm run test:e2e            # End-to-end tests
npm run test:all            # All tests

# Build
npm run build               # Build Electron app
npm run package             # Package for all platforms
npm run package:mac         # Package macOS only
npm run package:linux       # Package Linux only

# Release
npm version 0.2.0           # Bump version
git push --tags             # Push tags to trigger release
```

---

## Conclusion

This revamp transforms AUPAT from a technical archive tool into the **Abandoned Upstate** experience - a blog-style platform for exploring forgotten places. By addressing the core user requirements (KML support, partial data handling, free-form types, rich location pages) and applying the Abandoned Upstate brand identity, we create a tool that feels purposeful and aligned with its mission.

The implementation follows FAANG engineering principles:
- **KISS**: Fix root causes simply (binary encoding, geocoding fallback)
- **BPL**: Build for long-term maintainability (CSS variables, component architecture)
- **BPA**: Solve actual user problems, not theoretical ones
- **NME**: No unnecessary complexity (use Nominatim free tier first, upgrade if needed)

**Next Steps**: Complete Phase 1 (Core Fixes), validate with user testing, then proceed to Phase 2 (UI/UX Transformation).

---

**Document Version**: 1.0
**Last Updated**: 2025-11-18
**Status**: Ready for Implementation
