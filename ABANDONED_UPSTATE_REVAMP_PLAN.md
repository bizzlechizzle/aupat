# Abandoned Upstate App - Complete Revamp Plan

**Date:** 2025-11-18
**Version:** 0.2.0
**Branch:** claude/fix-startup-script-01Xyebakr4273Rs5mSiyhXFg

---

## Executive Summary

Transform AUPAT from generic archive tool into the **Abandoned Upstate** branded experience - a location-centric digital archive that feels like abandonedupstate.com in desktop form.

### Critical Requirements

1. **Dedicated Location Pages** - Blog-style, full-page experience (WHO/WHAT/WHERE/WHEN/WHY)
2. **KML/KMZ Import** - Must actually work (currently broken)
3. **Abandoned Upstate Branding** - Name, icon, theme, visual identity
4. **Auto-Update** - Mac app updates automatically on git pull
5. **Archive Philosophy** - Accept partial data (city/state without GPS)

---

## Current State Assessment

### ✅ COMPLETED (But User May Not See)

**1. Dedicated Location Pages**
- **Status:** FULLY IMPLEMENTED (commit 6b86cd2)
- **File:** `desktop/src/renderer/lib/LocationPage.svelte` (682 lines)
- **Features:**
  - Hero image section (full-width)
  - Dashboard layout: WHO, WHAT, WHERE, WHEN, WHY sections
  - Rich markdown rendering with clickable hyperlinks
  - Image gallery (3-column grid, lightbox)
  - Archived URLs section
  - Related locations (proximity-based)
  - Print-friendly stylesheet
  - Back button navigation
- **Why User May Not See:** App needs restart after git pull
- **Verification:** Click any map marker → should show full-page view

**2. Abandoned Upstate Theme**
- **Status:** FULLY IMPLEMENTED
- **File:** `desktop/src/renderer/styles/theme.css` (574 lines)
- **Colors:**
  - Cream: #fffbf7 (background)
  - Dark Gray: #474747 (text)
  - Black: #000000 (headings)
  - Brown: #b9975c (accents)
- **Typography:**
  - Roboto Mono (headings - monospace, uppercase, tracked)
  - Lora (body text - serif, readable)
- **Applied To:**
  - Map markers (black/brown instead of blue)
  - Map clusters (brown/gold/rust gradients)
  - Location page typography
  - App header ("Abandoned Upstate" in monospace)

**3. Browser Bookmarks Integration**
- **Status:** JUST ADDED (this session)
- **Files:**
  - `desktop/src/renderer/lib/Bookmarks.svelte` (305 lines)
  - `desktop/src/preload/index.js` (bookmarks API exposed)
  - `scripts/api_routes_bookmarks.py` (562 lines)
  - Database migration: `scripts/migrations/add_browser_tables.py`
- **Features:**
  - Browse bookmarks with search/filter
  - Folder organization
  - Visit count tracking
  - Tags support
  - Delete bookmarks
- **Why User May Not See:** App needs restart + database migration

### ❌ BROKEN (Acknowledged)

**1. KML/KMZ Import**
- **Status:** BROKEN
- **Problem:** Frontend reads KMZ (binary ZIP) as text, corrupts data
- **Root Cause:** `MapImportDialog.svelte:112` uses `selectedFile.text()` for all files
- **Impact:** User uploads Google Maps KML/KMZ export → rejected with "Unsupported file format"
- **Solution Required:** Read KMZ as ArrayBuffer, base64 encode, decode on backend

**2. App Branding**
- **Status:** INCOMPLETE
- **Problems:**
  - App still named "AUPAT Desktop" (should be "Abandoned Upstate")
  - Window title shows "AUPAT"
  - No app icon (should use "Abandoned Upstate.png")
  - package.json still references AUPAT
  - productName needs updating

### ⏳ NOT STARTED

**1. Auto-Update Mechanism**
- **Requirement:** Mac app auto-updates when user does `git pull`
- **Current State:** No auto-update system
- **Needed:**
  - electron-updater integration
  - GitHub releases automation
  - Update notification UI
  - Restart and install flow

---

## Implementation Plan

### Phase 1: Fix Critical Issues (Priority 1)

#### Task 1.1: Fix KML/KMZ Import (2 hours)

**Problem:** Binary KMZ files read as text, corrupting data

**Solution:**

**Frontend Changes** (`desktop/src/renderer/lib/MapImportDialog.svelte`):
```javascript
// Around line 112, replace:
// const content = await selectedFile.text();

// With:
let content;
let isBase64 = false;

if (fileFormat === 'kmz') {
  // Read binary KMZ as ArrayBuffer
  const arrayBuffer = await selectedFile.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);
  content = btoa(String.fromCharCode(...bytes));
  isBase64 = true;
} else {
  // KML, CSV, GeoJSON as text
  content = await selectedFile.text();
}

// Update API call to include encoding flag
const response = await window.api.map.importFile({
  content,
  format: fileFormat,
  isBase64,
  mode: importMode,
  description: importDescription
});
```

**Backend Changes** (`scripts/api_maps.py`):
```python
# Add to import endpoint
is_base64 = data.get('is_base64', False)
content = data.get('content')

if is_base64:
    import base64
    content_bytes = base64.b64decode(content)
    # For KMZ, unzip and extract KML
    import zipfile
    import io
    with zipfile.ZipFile(io.BytesIO(content_bytes)) as kmz:
        # Find .kml file inside
        kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
        if not kml_files:
            return jsonify({'error': 'No KML file found in KMZ'}), 400
        content = kmz.read(kml_files[0]).decode('utf-8')
```

**Testing Checklist:**
- [ ] Import Google Maps KML export (text format)
- [ ] Import Google Earth KMZ file (binary format)
- [ ] Import KML with ExtendedData fields
- [ ] Import KMZ with multiple placemarks
- [ ] Verify coordinates parse correctly (KML uses lon,lat order)
- [ ] Verify locations appear on map
- [ ] Test with malformed KML (should show error, not crash)

**Files to Modify:**
- `desktop/src/renderer/lib/MapImportDialog.svelte`
- `scripts/api_maps.py`

---

#### Task 1.2: Update App Branding (1 hour)

**Goal:** Change "AUPAT Desktop" → "Abandoned Upstate" everywhere

**Changes:**

**1. package.json** (`desktop/package.json`):
```json
{
  "name": "abandoned-upstate",
  "productName": "Abandoned Upstate",
  "description": "Digital archive for abandoned locations in Upstate New York",
  "build": {
    "appId": "com.abandonedupstate.app",
    "productName": "Abandoned Upstate",
    "mac": {
      "category": "public.app-category.lifestyle"
    }
  }
}
```

**2. Window Title** (`desktop/src/main/index.js`):
```javascript
// Around line 90
mainWindow = new BrowserWindow({
  title: 'Abandoned Upstate',  // Changed from 'AUPAT'
  width: 1400,
  height: 900,
  // ...
});
```

**3. App Header** (`desktop/src/renderer/App.svelte`):
```svelte
<!-- Line 94 - ALREADY DONE -->
<p class="text-sm text-gray-600 font-medium"
   style="font-family: var(--au-font-mono); text-transform: uppercase; letter-spacing: 0.05em;">
  Abandoned Upstate
</p>
```

**Files to Modify:**
- `desktop/package.json`
- `desktop/src/main/index.js`

**Verification:**
- [ ] Window title bar shows "Abandoned Upstate"
- [ ] App sidebar shows "Abandoned Upstate"
- [ ] About dialog (if exists) shows correct name

---

#### Task 1.3: Add App Icon (1.5 hours)

**Source:** `/home/user/aupat/Abandoned Upstate.png` (76KB, 512x512 PNG)

**Process:**

**Step 1: Install icon builder**
```bash
cd desktop
npm install --save-dev electron-icon-builder
```

**Step 2: Generate multi-resolution icons**
```bash
# From project root
npx electron-icon-builder \
  --input="Abandoned Upstate.png" \
  --output=desktop/resources \
  --flatten
```

This creates:
- `desktop/resources/icon.icns` (macOS - contains 16x16 through 1024x1024)
- `desktop/resources/icon.png` (Linux - 512x512)
- `desktop/resources/icons/` (Windows - multiple sizes)

**Step 3: Update package.json**
```json
{
  "build": {
    "mac": {
      "icon": "resources/icon.icns"
    },
    "linux": {
      "icon": "resources/icon.png"
    },
    "win": {
      "icon": "resources/icon.ico"
    }
  }
}
```

**Step 4: Set window icon** (`desktop/src/main/index.js`):
```javascript
import { join } from 'path';
import { app } from 'electron';

const iconPath = join(__dirname, '../../resources/icon.png');

mainWindow = new BrowserWindow({
  icon: iconPath,
  // ...
});
```

**Files Created:**
- `desktop/resources/icon.icns`
- `desktop/resources/icon.png`
- `desktop/resources/icon.ico`

**Files Modified:**
- `desktop/package.json`
- `desktop/src/main/index.js`

**Verification:**
- [ ] macOS Dock shows Abandoned Upstate logo
- [ ] macOS Finder shows icon on .app file
- [ ] Linux app launcher shows icon
- [ ] Window taskbar shows icon

---

### Phase 2: Auto-Update Mechanism (Priority 2)

#### Task 2.1: Implement electron-updater (3 hours)

**Goal:** App checks GitHub releases, downloads updates, prompts user to restart

**Installation:**
```bash
cd desktop
npm install electron-updater
```

**Implementation:**

**1. Create updater module** (`desktop/src/main/updater.js`):
```javascript
import { autoUpdater } from 'electron-updater';
import log from 'electron-log';

export function initAutoUpdater(mainWindow) {
  // Configure logging
  autoUpdater.logger = log;
  autoUpdater.logger.transports.file.level = 'info';

  // Don't auto-download (ask user first)
  autoUpdater.autoDownload = false;

  // Check for updates every 4 hours
  setInterval(() => {
    autoUpdater.checkForUpdates();
  }, 4 * 60 * 60 * 1000);

  // Check on startup (after 10 seconds)
  setTimeout(() => {
    autoUpdater.checkForUpdates();
  }, 10000);

  // Events
  autoUpdater.on('update-available', (info) => {
    log.info('Update available:', info.version);
    mainWindow.webContents.send('update-available', {
      version: info.version,
      releaseDate: info.releaseDate,
      releaseNotes: info.releaseNotes
    });
  });

  autoUpdater.on('update-downloaded', (info) => {
    log.info('Update downloaded:', info.version);
    mainWindow.webContents.send('update-downloaded', {
      version: info.version
    });
  });

  autoUpdater.on('error', (error) => {
    log.error('Update error:', error);
    mainWindow.webContents.send('update-error', {
      message: error.message
    });
  });

  autoUpdater.on('download-progress', (progress) => {
    mainWindow.webContents.send('update-progress', {
      percent: progress.percent,
      transferred: progress.transferred,
      total: progress.total
    });
  });
}

// IPC handlers for update actions
export function registerUpdateHandlers(ipcMain) {
  ipcMain.handle('update:download', () => {
    autoUpdater.downloadUpdate();
    return { success: true };
  });

  ipcMain.handle('update:install', () => {
    autoUpdater.quitAndInstall(false, true);
    return { success: true };
  });

  ipcMain.handle('update:check', () => {
    autoUpdater.checkForUpdates();
    return { success: true };
  });
}
```

**2. Integrate in main process** (`desktop/src/main/index.js`):
```javascript
import { initAutoUpdater, registerUpdateHandlers } from './updater.js';

// After window creation
app.whenReady().then(() => {
  createWindow();
  initAutoUpdater(mainWindow);
  registerUpdateHandlers(ipcMain);
});
```

**3. Add to preload script** (`desktop/src/preload/index.js`):
```javascript
contextBridge.exposeInMainWorld('api', {
  // ... existing APIs

  /**
   * Auto-update API
   */
  updates: {
    check: () => ipcRenderer.invoke('update:check'),
    download: () => ipcRenderer.invoke('update:download'),
    install: () => ipcRenderer.invoke('update:install'),
    onAvailable: (callback) => ipcRenderer.on('update-available', (_, data) => callback(data)),
    onDownloaded: (callback) => ipcRenderer.on('update-downloaded', (_, data) => callback(data)),
    onProgress: (callback) => ipcRenderer.on('update-progress', (_, data) => callback(data)),
    onError: (callback) => ipcRenderer.on('update-error', (_, data) => callback(data))
  }
});
```

**4. Create update notification UI** (`desktop/src/renderer/lib/UpdateNotification.svelte`):
```svelte
<script>
  import { onMount, onDestroy } from 'svelte';

  let updateAvailable = false;
  let updateDownloaded = false;
  let updateVersion = '';
  let downloadProgress = 0;
  let downloading = false;

  onMount(() => {
    window.api.updates.onAvailable((data) => {
      updateAvailable = true;
      updateVersion = data.version;
    });

    window.api.updates.onDownloaded((data) => {
      updateDownloaded = true;
      downloading = false;
    });

    window.api.updates.onProgress((data) => {
      downloadProgress = Math.round(data.percent);
    });
  });

  async function downloadUpdate() {
    downloading = true;
    await window.api.updates.download();
  }

  async function installUpdate() {
    await window.api.updates.install();
  }
</script>

{#if updateAvailable && !updateDownloaded && !downloading}
  <div class="update-banner bg-blue-600 text-white px-4 py-3 flex items-center justify-between">
    <div>
      <strong>Update available:</strong> Version {updateVersion}
    </div>
    <button
      on:click={downloadUpdate}
      class="bg-white text-blue-600 px-4 py-1 rounded hover:bg-gray-100"
    >
      Download Update
    </button>
  </div>
{/if}

{#if downloading}
  <div class="update-banner bg-blue-600 text-white px-4 py-3">
    <div class="flex items-center gap-3">
      <div class="flex-1">
        <div class="text-sm">Downloading update...</div>
        <div class="bg-white/20 rounded-full h-2 mt-1">
          <div
            class="bg-white rounded-full h-2 transition-all"
            style="width: {downloadProgress}%"
          />
        </div>
      </div>
      <div class="text-sm">{downloadProgress}%</div>
    </div>
  </div>
{/if}

{#if updateDownloaded}
  <div class="update-banner bg-green-600 text-white px-4 py-3 flex items-center justify-between">
    <div>
      <strong>Update ready!</strong> Restart to install version {updateVersion}
    </div>
    <button
      on:click={installUpdate}
      class="bg-white text-green-600 px-4 py-1 rounded hover:bg-gray-100"
    >
      Restart Now
    </button>
  </div>
{/if}

<style>
  .update-banner {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    animation: slideDown 0.3s ease;
  }

  @keyframes slideDown {
    from {
      transform: translateY(-100%);
    }
    to {
      transform: translateY(0);
    }
  }
</style>
```

**5. Add to App.svelte** (`desktop/src/renderer/App.svelte`):
```svelte
<script>
  import UpdateNotification from './lib/UpdateNotification.svelte';
  // ... other imports
</script>

<ErrorBoundary on:error={handleError}>
  <UpdateNotification />
  <div class="flex h-screen bg-gray-50">
    <!-- Rest of app -->
  </div>
</ErrorBoundary>
```

**6. Configure GitHub releases** (`desktop/package.json`):
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

**Files Created:**
- `desktop/src/main/updater.js`
- `desktop/src/renderer/lib/UpdateNotification.svelte`

**Files Modified:**
- `desktop/src/main/index.js`
- `desktop/src/preload/index.js`
- `desktop/src/renderer/App.svelte`
- `desktop/package.json`

**Testing:**
- [ ] Create GitHub release with built .dmg
- [ ] Launch app, verify update check (logs show "Checking for updates")
- [ ] Publish new release, verify notification appears
- [ ] Click "Download Update", verify progress bar
- [ ] Click "Restart Now", verify app restarts with new version

---

### Phase 3: Polish & Verification (Priority 3)

#### Task 3.1: Test Location Pages Are Visible (30 minutes)

**Problem:** User may have LocationPage.svelte but hasn't restarted app

**Steps:**
1. Run `./update_and_start.sh` (installs deps, starts app)
2. Click any map marker
3. Verify full-page location view appears
4. Check for:
   - Hero image (or placeholder)
   - WHO/WHAT/WHERE/WHEN/WHY sections
   - Markdown rendering with hyperlinks
   - Image gallery
   - Back button

**If Not Working:**
- Check console for errors
- Verify `currentView === 'location-page'` state
- Verify `LocationPage` imported in App.svelte (line 12)
- Verify navigation handler exists (line 58-61)

---

#### Task 3.2: Run Database Migration (15 minutes)

**Problem:** Bookmarks feature added but database schema not updated

**Steps:**
```bash
cd /home/user/aupat

# Run migration
python3 scripts/migrations/add_browser_tables.py --db-path data/aupat.db

# Verify tables created
sqlite3 data/aupat.db ".tables"
# Should see: bookmarks

# Verify columns
sqlite3 data/aupat.db ".schema bookmarks"
# Should see: bookmark_uuid, loc_uuid, url, title, etc.
```

**If Database Doesn't Exist:**
```bash
# Create database first
python3 scripts/db_migrate_v012.py --db-path data/aupat.db

# Then run bookmarks migration
python3 scripts/migrations/add_browser_tables.py --db-path data/aupat.db
```

---

#### Task 3.3: Verify Bookmarks UI Works (15 minutes)

**Steps:**
1. Restart desktop app
2. Click "Bookmarks" in sidebar
3. Should see empty bookmarks view with filters
4. Test adding bookmark (if create UI exists)
5. Test search/filter
6. Test folder dropdown

**If Not Working:**
- Check API server running on port 5002
- Check `/api/bookmarks` endpoint responds
- Check IPC handlers in main/index.js (lines 645-733)
- Check preload exposes bookmarks API (lines 75-82)

---

#### Task 3.4: Build Mac App (1 hour)

**Goal:** Create distributable .dmg file

**Prerequisites:**
```bash
cd desktop
npm install  # Ensure all dependencies installed
```

**Build Command:**
```bash
npm run package:mac
```

This creates:
- `desktop/dist-builder/Abandoned Upstate-0.1.2.dmg`
- `desktop/dist-builder/Abandoned Upstate-0.1.2-mac.zip`

**Testing:**
1. Eject any mounted DMG
2. Double-click .dmg file
3. Drag "Abandoned Upstate" to Applications
4. Launch from Applications
5. Verify:
   - Icon appears in Dock
   - Window title is "Abandoned Upstate"
   - App header shows "Abandoned Upstate"
   - Map loads
   - Location pages work
   - Settings persist

**Troubleshooting:**
- If build fails: Check `desktop/dist-builder/builder-debug.yml` for errors
- If icon missing: Verify `resources/icon.icns` exists
- If app crashes: Check Console.app for crash logs

---

## Brand Guide: Abandoned Upstate

### Visual Identity

**Logo:**
- File: `/home/user/aupat/Abandoned Upstate.png`
- Format: PNG, 512x512px (transparent background optional)
- Usage: App icon, splash screen, about dialog

**Color Palette:**

```css
/* Primary Colors */
--au-cream: #fffbf7;        /* Background, light areas */
--au-dark-gray: #474747;    /* Primary text */
--au-black: #000000;        /* Headings, emphasis */
--au-brown: #b9975c;        /* Accents, links, highlights */

/* Secondary Colors */
--au-rust: #8b4513;         /* Dark accents */
--au-gold: #d4af37;         /* Highlights, hover states */
--au-charcoal: #2b2b2b;     /* Dark backgrounds */

/* Semantic Colors */
--au-error: #dc2626;        /* Errors, warnings */
--au-success: #16a34a;      /* Success states */
--au-info: #2563eb;         /* Informational */
```

**Typography:**

```css
/* Headings - Roboto Mono */
--au-font-heading: 'Roboto Mono', monospace;
/* Usage: All caps, tracked (letter-spacing: 0.05em) */
/* Sizes: h1: 2rem, h2: 1.5rem, h3: 1.25rem */

/* Body - Lora */
--au-font-body: 'Lora', serif;
/* Usage: Paragraphs, descriptions, long-form content */
/* Sizes: body: 1rem (16px), small: 0.875rem (14px) */

/* Monospace - Roboto Mono */
--au-font-mono: 'Roboto Mono', monospace;
/* Usage: Code, metadata, technical details */
```

**Font Loading:**
```html
<!-- In index.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,700;1,400&family=Roboto+Mono:wght@400;700&display=swap" rel="stylesheet">
```

### Component Styles

**Buttons:**
```css
.au-button {
  background: var(--au-black);
  color: var(--au-cream);
  font-family: var(--au-font-mono);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0; /* Sharp corners */
  transition: background 0.2s;
}

.au-button:hover {
  background: var(--au-brown);
}

.au-button-secondary {
  background: transparent;
  color: var(--au-black);
  border: 2px solid var(--au-black);
}

.au-button-secondary:hover {
  background: var(--au-black);
  color: var(--au-cream);
}
```

**Cards:**
```css
.au-card {
  background: var(--au-cream);
  border: 1px solid #e5e5e5;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.au-card-dark {
  background: var(--au-charcoal);
  color: var(--au-cream);
  border-color: var(--au-brown);
}
```

**Section Headers:**
```css
.au-section-header {
  font-family: var(--au-font-heading);
  font-size: 1.25rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--au-black);
  border-bottom: 3px solid var(--au-brown);
  padding-bottom: 0.5rem;
  margin-bottom: 1.5rem;
}
```

**Map Markers:**
```css
/* Precise location */
.au-marker-precise {
  background: var(--au-black);
  border: 2px solid var(--au-brown);
  border-radius: 50% 50% 50% 0;
  width: 24px;
  height: 24px;
  transform: rotate(-45deg);
}

/* Approximate location (geocoded) */
.au-marker-approximate {
  background: transparent;
  border: 2px dashed var(--au-brown);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  opacity: 0.7;
}

/* Cluster */
.au-cluster {
  background: linear-gradient(135deg, var(--au-brown), var(--au-rust));
  color: white;
  border-radius: 50%;
  font-family: var(--au-font-mono);
  font-weight: bold;
}
```

### Layout Patterns

**Location Page Layout:**
```
┌─────────────────────────────────────────┐
│ [← Back]     ABANDONED UPSTATE          │ ← Header (fixed)
├─────────────────────────────────────────┤
│                                         │
│         HERO IMAGE (full-width)         │ ← 16:9 aspect ratio
│                                         │
├─────────────────────────────────────────┤
│  LOCATION NAME                          │ ← h1, Roboto Mono
│  ────────────                           │
│  Type • State • Status                  │ ← Metadata line
│                                         │
│  THE STORY                              │ ← Section headers
│  ─────────                              │   (uppercase, tracked)
│  [Rich text with markdown]              │
│                                         │
│  WHO / WHAT / WHERE / WHEN / WHY        │ ← Dashboard grid
│  ┌──────┬──────┬──────┬──────┬──────┐ │   (5 columns)
│  │      │      │      │      │      │ │
│  └──────┴──────┴──────┴──────┴──────┘ │
│                                         │
│  IMAGES                                 │
│  ──────                                 │
│  ┌──────┬──────┬──────┐               │ ← 3-column grid
│  │      │      │      │               │
│  └──────┴──────┴──────┘               │
│                                         │
│  ARCHIVED URLS                          │
│  ─────────────                          │
│  • url1.com                             │
│  • url2.com                             │
│                                         │
│  RELATED LOCATIONS                      │
│  ─────────────────                      │
│  [Nearby sites within 10km]             │
└─────────────────────────────────────────┘
```

**Spacing Scale:**
```css
--au-space-xs: 0.25rem;   /* 4px */
--au-space-sm: 0.5rem;    /* 8px */
--au-space-md: 1rem;      /* 16px */
--au-space-lg: 1.5rem;    /* 24px */
--au-space-xl: 2rem;      /* 32px */
--au-space-2xl: 3rem;     /* 48px */
--au-space-3xl: 4rem;     /* 64px */
```

### Voice & Tone

**Headlines:** Direct, factual, no hype
- "Abandoned Textile Mill, Troy NY"
- "Former Erie Canal Lock #7"

**Body Text:** Informative, respectful, curious
- "This industrial complex operated from 1892 to 1974..."
- "Local historians believe the structure dates to..."

**Metadata:** Technical, precise, monospace
- GPS: 42.7284°N, 73.6918°W
- Built: 1892 • Closed: 1974
- Status: Partially Demolished

**Avoid:**
- Sensationalism ("CREEPY ABANDONED PLACE!!!")
- Urban explorer slang ("sick spot bro")
- Disrespect to history or people affected

### UI States

**Loading:**
```svelte
<div class="au-loading">
  <div class="au-spinner"></div>
  <p class="au-loading-text">Loading locations...</p>
</div>
```

**Empty State:**
```svelte
<div class="au-empty">
  <p class="au-empty-heading">No locations yet</p>
  <p class="au-empty-text">Import your first location to get started</p>
  <button class="au-button">Import Locations</button>
</div>
```

**Error:**
```svelte
<div class="au-error">
  <p class="au-error-heading">Failed to load location</p>
  <p class="au-error-text">{error.message}</p>
  <button class="au-button-secondary">Try Again</button>
</div>
```

### Accessibility

**Contrast Ratios:**
- Black text on cream: 15.8:1 (AAA)
- Brown on cream: 4.6:1 (AA)
- White on brown: 6.2:1 (AA)

**Focus States:**
```css
*:focus {
  outline: 2px solid var(--au-brown);
  outline-offset: 2px;
}
```

**Screen Reader Labels:**
```svelte
<button aria-label="Navigate back to map">
  ← Back
</button>

<img src={url} alt={`Photo of ${locationName}`} />
```

---

## Testing Plan

### Manual Testing Checklist

**KML/KMZ Import:**
- [ ] Import KML file from Google Maps export
- [ ] Import KMZ file (zipped KML)
- [ ] Verify coordinates extract correctly
- [ ] Verify locations appear on map
- [ ] Test with malformed KML (should error gracefully)

**Location Pages:**
- [ ] Click map marker → opens dedicated page
- [ ] Hero image displays (or placeholder)
- [ ] Markdown renders with hyperlinks
- [ ] WHO/WHAT/WHERE/WHEN/WHY sections populated
- [ ] Image gallery displays
- [ ] Click image → lightbox opens
- [ ] Back button returns to map

**Branding:**
- [ ] Window title shows "Abandoned Upstate"
- [ ] App icon shows in Dock/taskbar
- [ ] Sidebar header shows "Abandoned Upstate"
- [ ] Map markers are black/brown (not blue)
- [ ] Typography uses Roboto Mono + Lora
- [ ] Colors match brand palette

**Bookmarks:**
- [ ] Navigate to Bookmarks view
- [ ] Search for bookmark
- [ ] Filter by folder
- [ ] Sort by date/visits/title
- [ ] Open bookmark URL
- [ ] Delete bookmark

**Auto-Update:**
- [ ] Update notification appears (test mode)
- [ ] Download progress shows
- [ ] Install prompts restart
- [ ] App updates successfully

### Automated Testing

**Unit Tests:**
```bash
cd desktop
npm test
# All tests should pass
```

**E2E Tests:**
```bash
cd desktop
npm run test:e2e
# Playwright tests should pass
```

---

## Deployment Checklist

### Pre-Release

- [ ] All manual tests pass
- [ ] All automated tests pass
- [ ] KML/KMZ import verified
- [ ] Location pages verified
- [ ] Branding updated (name, icon)
- [ ] Auto-update configured
- [ ] Database migration tested
- [ ] README updated with new name

### Build

```bash
# Install dependencies
cd desktop
npm install

# Build for macOS
npm run package:mac

# Verify build artifacts
ls -lh dist-builder/
# Should see: Abandoned Upstate-0.2.0.dmg
```

### Release

1. Tag version in git:
```bash
git tag -a v0.2.0 -m "Abandoned Upstate rebrand + KML/KMZ fix + Auto-update"
git push origin v0.2.0
```

2. Create GitHub release:
   - Go to https://github.com/bizzlechizzle/aupat/releases/new
   - Tag: v0.2.0
   - Title: "Abandoned Upstate v0.2.0"
   - Upload `Abandoned Upstate-0.2.0.dmg`
   - Release notes:
```markdown
## Abandoned Upstate v0.2.0

### Rebranding
- App renamed from "AUPAT Desktop" to "Abandoned Upstate"
- New app icon using Abandoned Upstate logo
- Updated visual theme (black, brown, cream color palette)

### New Features
- **KML/KMZ Import Now Works**: Import Google Maps and Google Earth files
- **Auto-Update**: App checks for updates automatically
- **Browser Bookmarks**: Manage research URLs with folder organization

### Improvements
- Dedicated location pages (blog-style layout)
- WHO/WHAT/WHERE/WHEN/WHY dashboard sections
- Markdown support with clickable hyperlinks
- Image gallery with lightbox

### Bug Fixes
- Fixed KMZ import (binary file corruption)
- Fixed map marker clustering colors
- Fixed API connection status indicator
```

3. Verify auto-update works:
   - Install v0.1.2 (old version)
   - Launch app
   - Wait for update notification
   - Download and install v0.2.0
   - Verify update succeeds

---

## Timeline

### Day 1 (4 hours)
- Fix KML/KMZ import (2 hours)
- Update app branding (1 hour)
- Add app icon (1 hour)

### Day 2 (4 hours)
- Implement auto-update (3 hours)
- Test all features (1 hour)

### Day 3 (2 hours)
- Build Mac app (1 hour)
- Create GitHub release (1 hour)

**Total: 10 hours over 3 days**

---

## Success Criteria

**Must Have:**
- [x] Location pages work (already implemented)
- [ ] KML/KMZ import works (needs fix)
- [ ] App named "Abandoned Upstate" (needs update)
- [ ] App icon uses Abandoned Upstate.png (needs update)
- [ ] Auto-update mechanism works (needs implementation)

**Should Have:**
- [ ] Bookmarks feature accessible (database migration needed)
- [ ] Brand guide documented (this document)
- [ ] Mac .dmg builds successfully
- [ ] All tests pass

**Could Have:**
- [ ] Linux AppImage build
- [ ] Windows installer
- [ ] Automated GitHub Actions build

---

## Risk Assessment

**Low Risk:**
- App branding (simple text changes)
- App icon (straightforward process)
- Location pages (already working)

**Medium Risk:**
- KML/KMZ import fix (requires binary handling)
- Auto-update (complex but well-documented)
- Mac app build (depends on environment)

**High Risk:**
- Database migration (could fail if database corrupt)
- Auto-update testing (requires real GitHub release)
- Compatibility (macOS version requirements)

**Mitigation:**
- Test on clean macOS VM before release
- Keep rollback plan (previous .dmg available)
- Document known issues in release notes

---

## Appendix: Quick Reference

### Start Dev Environment
```bash
cd /home/user/aupat
./update_and_start.sh
```

### Build for macOS
```bash
cd desktop
npm run package:mac
```

### Run Tests
```bash
cd desktop
npm test                # Unit tests
npm run test:e2e       # E2E tests
```

### Create Database
```bash
python3 scripts/db_migrate_v012.py --db-path data/aupat.db
python3 scripts/migrations/add_browser_tables.py --db-path data/aupat.db
```

### Check API Health
```bash
curl http://localhost:5002/api/health
```

---

**Document Version:** 1.0
**Status:** READY FOR IMPLEMENTATION
**Next Step:** Fix KML/KMZ import (Task 1.1)
