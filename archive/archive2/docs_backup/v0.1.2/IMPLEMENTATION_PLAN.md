# AUPAT v0.1.2 - Implementation Plan

**Date**: 2025-11-17
**Engineer**: Senior FAANG-level Implementation Engineer
**Mode**: DRETW + KISS + BPL + BPA + NME
**Status**: READY TO EXECUTE

---

## OVERVIEW

This plan implements missing features for AUPAT v0.1.2, prioritizing CRITICAL features first (Desktop MVP).

**Execution Model**: Module-by-module, test-verify-commit cycle.

**No redesign**. No new architecture. Phase 1 foundation is DONE. Build on it.

---

## PHASE 2: DESKTOP MVP - IMPLEMENTATION PLAN

### MODULE 1: ELECTRON + SVELTE SCAFFOLD

**Status**: NOT STARTED
**Estimated Time**: 3-4 days
**Dependencies**: None

#### Tasks

**1.1 Project Initialization**

```bash
# Create desktop-app directory
mkdir -p /home/user/aupat/desktop-app
cd /home/user/aupat/desktop-app

# Initialize npm project
npm init -y

# Install Electron
npm install --save-dev electron electron-builder

# Install Svelte + Vite
npm install --save-dev vite @sveltejs/vite-plugin-svelte svelte

# Install development tools
npm install --save-dev concurrently wait-on cross-env

# Install runtime dependencies
npm install axios supercluster leaflet
```

**1.2 Project Structure**

```
desktop-app/
├── package.json
├── vite.config.js
├── electron.vite.config.js
├── src/
│   ├── main/              # Electron main process (Node.js)
│   │   ├── index.js       # Main entry point
│   │   ├── ipc-handlers.js
│   │   └── menu.js
│   ├── preload/           # Preload scripts (sandboxed)
│   │   └── index.js
│   ├── renderer/          # Frontend (Svelte)
│   │   ├── App.svelte     # Root component
│   │   ├── main.js        # Svelte entry
│   │   ├── api/           # API client
│   │   │   └── client.js
│   │   ├── components/    # UI components
│   │   │   ├── Map.svelte
│   │   │   ├── Sidebar.svelte
│   │   │   ├── Gallery.svelte
│   │   │   ├── Import.svelte
│   │   │   └── Settings.svelte
│   │   ├── stores/        # Svelte stores (state)
│   │   │   ├── locations.js
│   │   │   ├── settings.js
│   │   │   └── ui.js
│   │   └── utils/         # Helpers
│   │       ├── format.js
│   │       └── validation.js
│   └── index.html
└── resources/             # Icons, assets
    ├── icon.png
    └── icon.icns
```

**1.3 package.json Scripts**

```json
{
  "name": "aupat-desktop",
  "version": "0.1.2",
  "main": "dist-electron/main/index.js",
  "scripts": {
    "dev": "concurrently \"vite\" \"wait-on http://localhost:5173 && electron .\"",
    "build": "vite build && electron-builder",
    "build:mac": "vite build && electron-builder --mac",
    "build:linux": "vite build && electron-builder --linux"
  },
  "build": {
    "appId": "com.aupat.desktop",
    "productName": "AUPAT",
    "directories": {
      "output": "dist"
    },
    "mac": {
      "target": "dmg",
      "icon": "resources/icon.icns"
    },
    "linux": {
      "target": ["AppImage", "deb"],
      "icon": "resources/icon.png",
      "category": "Utility"
    }
  }
}
```

**1.4 Main Process (src/main/index.js)**

```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers
require('./ipc-handlers');
```

**1.5 Preload Script (src/preload/index.js)**

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),

  // File system operations
  selectFolder: () => ipcRenderer.invoke('select-folder'),

  // Notifications
  showNotification: (title, body) => ipcRenderer.send('show-notification', { title, body })
});
```

**1.6 API Client (src/renderer/api/client.js)**

```javascript
import axios from 'axios';

class AupatAPIClient {
  constructor(baseURL = 'http://localhost:5000') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  // Health checks
  async health() {
    const response = await this.client.get('/api/health');
    return response.data;
  }

  async healthServices() {
    const response = await this.client.get('/api/health/services');
    return response.data;
  }

  // Map markers
  async getMapMarkers(bounds = null) {
    const params = bounds ? { bounds: JSON.stringify(bounds) } : {};
    const response = await this.client.get('/api/map/markers', { params });
    return response.data;
  }

  // Locations
  async getLocation(uuid) {
    const response = await this.client.get(`/api/locations/${uuid}`);
    return response.data;
  }

  async getLocationImages(uuid, limit = 100, offset = 0) {
    const response = await this.client.get(`/api/locations/${uuid}/images`, {
      params: { limit, offset }
    });
    return response.data;
  }

  async getLocationVideos(uuid, limit = 100, offset = 0) {
    const response = await this.client.get(`/api/locations/${uuid}/videos`, {
      params: { limit, offset }
    });
    return response.data;
  }

  async getLocationArchives(uuid) {
    const response = await this.client.get(`/api/locations/${uuid}/archives`);
    return response.data;
  }

  // Search
  async search(query, filters = {}) {
    const response = await this.client.get('/api/search', {
      params: { q: query, ...filters }
    });
    return response.data;
  }

  // Create/Update/Delete
  async createLocation(data) {
    const response = await this.client.post('/api/locations', data);
    return response.data;
  }

  async updateLocation(uuid, data) {
    const response = await this.client.put(`/api/locations/${uuid}`, data);
    return response.data;
  }

  async deleteLocation(uuid) {
    const response = await this.client.delete(`/api/locations/${uuid}`);
    return response.data;
  }

  // Import
  async importImages(locUuid, filePaths) {
    const response = await this.client.post('/api/import/images', {
      loc_uuid: locUuid,
      file_paths: filePaths
    });
    return response.data;
  }

  // Archive
  async archiveURL(locUuid, url, highResMode = false) {
    const response = await this.client.post(`/api/locations/${locUuid}/archive`, {
      url,
      high_res_mode: highResMode
    });
    return response.data;
  }
}

export default new AupatAPIClient();
```

**1.7 Svelte Store (src/renderer/stores/settings.js)**

```javascript
import { writable } from 'svelte/store';

const defaultSettings = {
  apiUrl: 'http://localhost:5000',
  immichUrl: 'http://localhost:2283',
  archiveboxUrl: 'http://localhost:8001',
  mapCenter: { lat: 42.6526, lon: -73.7562 }, // Albany, NY
  mapZoom: 8,
  autoUploadImmich: true,
  autoExtractGPS: true,
  theme: 'light'
};

function createSettings() {
  const stored = localStorage.getItem('aupat-settings');
  const initial = stored ? JSON.parse(stored) : defaultSettings;

  const { subscribe, set, update } = writable(initial);

  return {
    subscribe,
    set: (value) => {
      localStorage.setItem('aupat-settings', JSON.stringify(value));
      set(value);
    },
    update: (fn) => {
      update((current) => {
        const updated = fn(current);
        localStorage.setItem('aupat-settings', JSON.stringify(updated));
        return updated;
      });
    },
    reset: () => {
      localStorage.setItem('aupat-settings', JSON.stringify(defaultSettings));
      set(defaultSettings);
    }
  };
}

export const settings = createSettings();
```

**1.8 Root Component (src/renderer/App.svelte)**

```svelte
<script>
  import { onMount } from 'svelte';
  import { settings } from './stores/settings.js';
  import api from './api/client.js';
  import Map from './components/Map.svelte';
  import Sidebar from './components/Sidebar.svelte';
  import Import from './components/Import.svelte';
  import Settings from './components/Settings.svelte';

  let currentView = 'map';
  let health = null;
  let error = null;

  onMount(async () => {
    try {
      health = await api.health();
    } catch (e) {
      error = 'Cannot connect to AUPAT Core. Is it running?';
    }
  });

  function switchView(view) {
    currentView = view;
  }
</script>

<main>
  {#if error}
    <div class="error-banner">{error}</div>
  {/if}

  <nav class="sidebar-nav">
    <button on:click={() => switchView('map')} class:active={currentView === 'map'}>
      Map
    </button>
    <button on:click={() => switchView('import')} class:active={currentView === 'import'}>
      Import
    </button>
    <button on:click={() => switchView('settings')} class:active={currentView === 'settings'}>
      Settings
    </button>
  </nav>

  <div class="content">
    {#if currentView === 'map'}
      <Map />
      <Sidebar />
    {:else if currentView === 'import'}
      <Import />
    {:else if currentView === 'settings'}
      <Settings />
    {/if}
  </div>
</main>

<style>
  main {
    display: flex;
    height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  .sidebar-nav {
    width: 200px;
    background: #2c3e50;
    color: white;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .sidebar-nav button {
    padding: 10px;
    background: #34495e;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-align: left;
  }

  .sidebar-nav button.active {
    background: #3498db;
  }

  .sidebar-nav button:hover {
    background: #3498db;
  }

  .content {
    flex: 1;
    display: flex;
    position: relative;
  }

  .error-banner {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: #e74c3c;
    color: white;
    padding: 10px;
    text-align: center;
    z-index: 9999;
  }
</style>
```

**Testing**:
```bash
cd desktop-app
npm run dev
# App should launch with basic navigation
```

---

### MODULE 2: MAP VIEW WITH CLUSTERING

**Status**: NOT STARTED
**Estimated Time**: 5-7 days
**Dependencies**: Module 1 (scaffold)

#### Tasks

**2.1 Install Map Libraries**

```bash
npm install leaflet supercluster
npm install --save-dev @types/leaflet
```

**2.2 Map Component (src/renderer/components/Map.svelte)**

```svelte
<script>
  import { onMount } from 'svelte';
  import L from 'leaflet';
  import Supercluster from 'supercluster';
  import api from '../api/client.js';
  import { selectedLocation } from '../stores/locations.js';
  import 'leaflet/dist/leaflet.css';

  let mapContainer;
  let map;
  let markers = [];
  let clusters = new Supercluster({
    radius: 60,
    maxZoom: 16
  });
  let clusterLayer;

  onMount(async () => {
    // Initialize map
    map = L.map(mapContainer).setView([42.6526, -73.7562], 8);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(map);

    // Load markers
    await loadMarkers();

    // Update clusters on zoom/pan
    map.on('moveend', updateClusters);
    map.on('zoomend', updateClusters);
  });

  async function loadMarkers() {
    try {
      markers = await api.getMapMarkers();

      // Convert to GeoJSON for Supercluster
      const points = markers.map(m => ({
        type: 'Feature',
        properties: { ...m },
        geometry: {
          type: 'Point',
          coordinates: [m.lon, m.lat]
        }
      }));

      clusters.load(points);
      updateClusters();
    } catch (error) {
      console.error('Failed to load markers:', error);
    }
  }

  function updateClusters() {
    if (!map) return;

    // Remove existing markers
    if (clusterLayer) {
      map.removeLayer(clusterLayer);
    }

    const bounds = map.getBounds();
    const bbox = [
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth()
    ];
    const zoom = map.getZoom();

    // Get clusters in current view
    const clustersInView = clusters.getClusters(bbox, zoom);

    clusterLayer = L.layerGroup();

    clustersInView.forEach(feature => {
      const [lon, lat] = feature.geometry.coordinates;
      const props = feature.properties;

      if (props.cluster) {
        // Render cluster marker
        const count = props.point_count;
        const marker = L.marker([lat, lon], {
          icon: L.divIcon({
            html: `<div class="cluster-marker">${count}</div>`,
            className: 'cluster-icon',
            iconSize: [40, 40]
          })
        });

        marker.on('click', () => {
          const expansionZoom = clusters.getClusterExpansionZoom(props.cluster_id);
          map.setView([lat, lon], expansionZoom);
        });

        marker.addTo(clusterLayer);
      } else {
        // Render single location marker
        const marker = L.marker([lat, lon], {
          icon: L.divIcon({
            html: '<div class="location-marker"></div>',
            className: 'location-icon',
            iconSize: [20, 20]
          })
        });

        marker.on('click', () => {
          selectedLocation.set(props);
        });

        marker.addTo(clusterLayer);
      }
    });

    clusterLayer.addTo(map);
  }
</script>

<div bind:this={mapContainer} class="map-container"></div>

<style>
  .map-container {
    width: 100%;
    height: 100%;
  }

  :global(.cluster-marker) {
    background: #3498db;
    color: white;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    border: 2px solid white;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  }

  :global(.location-marker) {
    background: #e74c3c;
    border-radius: 50%;
    width: 12px;
    height: 12px;
    border: 2px solid white;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  }
</style>
```

**2.3 Location Store (src/renderer/stores/locations.js)**

```javascript
import { writable } from 'svelte/store';

export const selectedLocation = writable(null);
export const locations = writable([]);
export const searchQuery = writable('');
```

**Testing**:
- Load map with 200k markers
- Verify clustering works at different zoom levels
- Click cluster → should zoom to expansion level
- Click marker → should set selectedLocation store
- Performance target: Render 200k markers in < 3 seconds

---

### MODULE 3: LOCATION DETAILS SIDEBAR

**Status**: NOT STARTED
**Estimated Time**: 3-4 days
**Dependencies**: Module 2 (map)

**3.1 Sidebar Component (src/renderer/components/Sidebar.svelte)**

```svelte
<script>
  import { selectedLocation } from '../stores/locations.js';
  import Gallery from './Gallery.svelte';
  import api from '../api/client.js';
  import { onMount } from 'svelte';

  let location = null;
  let images = [];
  let videos = [];
  let archives = [];
  let loading = false;

  selectedLocation.subscribe(async (loc) => {
    if (!loc) {
      location = null;
      return;
    }

    loading = true;
    try {
      // Load full location details
      location = await api.getLocation(loc.loc_uuid);
      images = await api.getLocationImages(loc.loc_uuid, 100, 0);
      videos = await api.getLocationVideos(loc.loc_uuid, 100, 0);
      archives = await api.getLocationArchives(loc.loc_uuid);
    } catch (error) {
      console.error('Failed to load location:', error);
    } finally {
      loading = false;
    }
  });

  function close() {
    selectedLocation.set(null);
  }
</script>

{#if location}
  <aside class="sidebar">
    <header>
      <h2>{location.loc_name}</h2>
      <button on:click={close}>✕</button>
    </header>

    {#if loading}
      <div class="loading">Loading...</div>
    {:else}
      <section class="details">
        <div class="metadata">
          <div><strong>Type:</strong> {location.loc_type}</div>
          <div><strong>State:</strong> {location.loc_state}</div>
          {#if location.street_address}
            <div><strong>Address:</strong> {location.street_address}, {location.city}, {location.state_abbrev} {location.zip_code}</div>
          {/if}
          {#if location.lat && location.lon}
            <div><strong>GPS:</strong> {location.lat.toFixed(6)}, {location.lon.toFixed(6)}</div>
          {/if}
        </div>

        <div class="counts">
          <span>{images.length} images</span>
          <span>{videos.length} videos</span>
          <span>{archives.length} archived URLs</span>
        </div>
      </section>

      <section class="gallery-section">
        <h3>Gallery</h3>
        <Gallery {images} {videos} />
      </section>

      <section class="archives-section">
        <h3>Archived URLs</h3>
        <ul>
          {#each archives as archive}
            <li>
              <a href={archive.url} target="_blank">{archive.url}</a>
              <span class="status">{archive.archive_status}</span>
            </li>
          {/each}
        </ul>
      </section>
    {/if}
  </aside>
{/if}

<style>
  .sidebar {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 400px;
    background: white;
    box-shadow: -2px 0 8px rgba(0,0,0,0.1);
    overflow-y: auto;
    z-index: 1000;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #e0e0e0;
  }

  header h2 {
    margin: 0;
    font-size: 18px;
  }

  header button {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #999;
  }

  header button:hover {
    color: #333;
  }

  section {
    padding: 20px;
    border-bottom: 1px solid #e0e0e0;
  }

  .metadata div {
    margin-bottom: 10px;
  }

  .counts {
    display: flex;
    gap: 15px;
    margin-top: 15px;
    color: #666;
  }

  .archives-section ul {
    list-style: none;
    padding: 0;
  }

  .archives-section li {
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
  }

  .status {
    color: #999;
    font-size: 12px;
  }

  .loading {
    padding: 20px;
    text-align: center;
    color: #999;
  }
</style>
```

**3.2 Gallery Component (src/renderer/components/Gallery.svelte)**

```svelte
<script>
  import { settings } from '../stores/settings.js';

  export let images = [];
  export let videos = [];

  let immichUrl;
  settings.subscribe(s => {
    immichUrl = s.immichUrl;
  });

  function getThumbnailUrl(assetId) {
    if (!assetId) return '/placeholder.png';
    return `${immichUrl}/api/asset/thumbnail/${assetId}?size=preview`;
  }

  function getOriginalUrl(assetId) {
    if (!assetId) return '#';
    return `${immichUrl}/api/asset/file/${assetId}`;
  }

  function openLightbox(assetId) {
    // TODO: Implement lightbox in next iteration
    window.open(getOriginalUrl(assetId), '_blank');
  }
</script>

<div class="gallery">
  {#each images as img}
    <div class="thumbnail" on:click={() => openLightbox(img.immich_asset_id)}>
      <img src={getThumbnailUrl(img.immich_asset_id)} alt={img.img_orig_filename} />
    </div>
  {/each}
  {#each videos as vid}
    <div class="thumbnail video" on:click={() => openLightbox(vid.immich_asset_id)}>
      <img src={getThumbnailUrl(vid.immich_asset_id)} alt={vid.vid_orig_filename} />
      <div class="play-icon">▶</div>
    </div>
  {/each}
</div>

<style>
  .gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }

  .thumbnail {
    aspect-ratio: 1;
    overflow: hidden;
    border-radius: 4px;
    cursor: pointer;
    position: relative;
  }

  .thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .thumbnail:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }

  .thumbnail.video .play-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0,0,0,0.6);
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
  }
</style>
```

**Testing**:
- Click marker on map → sidebar opens with location details
- Gallery displays Immich thumbnails
- Click thumbnail → opens full-size image in new tab
- Performance target: Load 100 thumbnails in < 2 seconds

---

### MODULE 4: IMPORT INTERFACE

**Status**: NOT STARTED
**Estimated Time**: 3-4 days
**Dependencies**: Module 1 (scaffold)

**4.1 Import Component (src/renderer/components/Import.svelte)**

```svelte
<script>
  import { onMount } from 'svelte';
  import api from '../api/client.js';
  import { locations } from '../stores/locations.js';

  let allLocations = [];
  let selectedLocation = null;
  let files = [];
  let importing = false;
  let progress = { current: 0, total: 0 };
  let results = null;

  onMount(async () => {
    allLocations = await api.search('', { limit: 1000 });
  });

  function handleDrop(event) {
    event.preventDefault();
    const items = event.dataTransfer.items;

    for (let item of items) {
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry();
        if (entry.isDirectory) {
          readDirectory(entry);
        } else {
          files = [...files, entry.file()];
        }
      }
    }
  }

  async function readDirectory(dirEntry) {
    const reader = dirEntry.createReader();
    reader.readEntries(async (entries) => {
      for (let entry of entries) {
        if (entry.isFile) {
          const file = await getFile(entry);
          if (isImageOrVideo(file.name)) {
            files = [...files, file];
          }
        } else if (entry.isDirectory) {
          await readDirectory(entry);
        }
      }
    });
  }

  function getFile(fileEntry) {
    return new Promise((resolve) => {
      fileEntry.file(resolve);
    });
  }

  function isImageOrVideo(filename) {
    const ext = filename.toLowerCase().split('.').pop();
    return ['jpg', 'jpeg', 'png', 'heic', 'mp4', 'mov', 'avi'].includes(ext);
  }

  function handleDragOver(event) {
    event.preventDefault();
  }

  async function startImport() {
    if (!selectedLocation || files.length === 0) return;

    importing = true;
    progress = { current: 0, total: files.length };

    const filePaths = files.map(f => f.path);

    try {
      // Call API to import files
      const result = await api.importImages(selectedLocation.loc_uuid, filePaths);

      results = {
        imported: result.imported_count,
        duplicates: result.duplicates_skipped,
        errors: result.errors || [],
        gps_extracted: result.gps_extracted_count
      };
    } catch (error) {
      results = {
        error: error.message
      };
    } finally {
      importing = false;
    }
  }

  function reset() {
    files = [];
    results = null;
    progress = { current: 0, total: 0 };
  }
</script>

<div class="import-container">
  <h1>Import Photos and Videos</h1>

  <div class="location-select">
    <label for="location">Select Destination Location:</label>
    <select id="location" bind:value={selectedLocation}>
      <option value={null}>-- Select Location --</option>
      {#each allLocations as loc}
        <option value={loc}>{loc.loc_name} ({loc.loc_state})</option>
      {/each}
    </select>
  </div>

  <div
    class="drop-zone"
    on:drop={handleDrop}
    on:dragover={handleDragOver}
  >
    {#if files.length === 0}
      <p>Drag and drop folder or files here</p>
    {:else}
      <p>{files.length} files selected</p>
      <button on:click={reset}>Clear</button>
    {/if}
  </div>

  {#if files.length > 0 && selectedLocation && !importing}
    <button class="import-btn" on:click={startImport}>
      Import {files.length} files to {selectedLocation.loc_name}
    </button>
  {/if}

  {#if importing}
    <div class="progress">
      <div class="progress-bar" style="width: {(progress.current / progress.total) * 100}%"></div>
      <span>{progress.current} / {progress.total}</span>
    </div>
  {/if}

  {#if results}
    <div class="results">
      {#if results.error}
        <div class="error">Error: {results.error}</div>
      {:else}
        <div class="success">
          <p>Import complete!</p>
          <ul>
            <li>Imported: {results.imported}</li>
            <li>Duplicates skipped: {results.duplicates}</li>
            <li>GPS extracted: {results.gps_extracted}</li>
            {#if results.errors.length > 0}
              <li class="error">Errors: {results.errors.length}</li>
            {/if}
          </ul>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .import-container {
    padding: 40px;
    max-width: 800px;
    margin: 0 auto;
  }

  h1 {
    margin-bottom: 30px;
  }

  .location-select {
    margin-bottom: 30px;
  }

  .location-select label {
    display: block;
    margin-bottom: 10px;
    font-weight: bold;
  }

  .location-select select {
    width: 100%;
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  .drop-zone {
    border: 2px dashed #3498db;
    border-radius: 8px;
    padding: 60px;
    text-align: center;
    background: #f8f9fa;
    margin-bottom: 30px;
  }

  .drop-zone p {
    color: #666;
    font-size: 18px;
  }

  .import-btn {
    width: 100%;
    padding: 15px;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
  }

  .import-btn:hover {
    background: #2980b9;
  }

  .progress {
    margin-top: 30px;
    position: relative;
    height: 40px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: #3498db;
    transition: width 0.3s;
  }

  .progress span {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-weight: bold;
  }

  .results {
    margin-top: 30px;
    padding: 20px;
    border-radius: 4px;
  }

  .results.success {
    background: #d4edda;
    border: 1px solid #c3e6cb;
  }

  .results.error {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
  }

  .results ul {
    margin-top: 10px;
  }
</style>
```

**Testing**:
- Drag folder → files list populates
- Select location → import button enabled
- Click import → progress bar shows status
- Verify files uploaded to AUPAT Core and Immich
- Check results display

---

### MODULE 5: SETTINGS PAGE

**Status**: NOT STARTED
**Estimated Time**: 2 days
**Dependencies**: Module 1 (scaffold)

**5.1 Settings Component (src/renderer/components/Settings.svelte)**

```svelte
<script>
  import { settings } from '../stores/settings.js';
  import api from '../api/client.js';

  let settingsData = {};
  let saved = false;

  settings.subscribe(s => {
    settingsData = { ...s };
  });

  async function testConnection(service) {
    try {
      if (service === 'aupat') {
        const health = await api.health();
        alert(`AUPAT Core: ${health.status}`);
      } else if (service === 'immich') {
        const response = await fetch(`${settingsData.immichUrl}/api/server-info/ping`);
        const data = await response.json();
        alert(`Immich: ${data.res}`);
      } else if (service === 'archivebox') {
        const response = await fetch(`${settingsData.archiveboxUrl}/health`);
        const data = await response.json();
        alert(`ArchiveBox: ${data.status}`);
      }
    } catch (error) {
      alert(`Connection failed: ${error.message}`);
    }
  }

  function save() {
    settings.set(settingsData);
    saved = true;
    setTimeout(() => saved = false, 3000);
  }

  function reset() {
    if (confirm('Reset all settings to defaults?')) {
      settings.reset();
      settingsData = {};
      settings.subscribe(s => settingsData = { ...s })();
    }
  }
</script>

<div class="settings-container">
  <h1>Settings</h1>

  <section>
    <h2>API Connections</h2>

    <div class="field">
      <label>AUPAT Core URL</label>
      <input type="text" bind:value={settingsData.apiUrl} />
      <button on:click={() => testConnection('aupat')}>Test Connection</button>
    </div>

    <div class="field">
      <label>Immich URL</label>
      <input type="text" bind:value={settingsData.immichUrl} />
      <button on:click={() => testConnection('immich')}>Test Connection</button>
    </div>

    <div class="field">
      <label>ArchiveBox URL</label>
      <input type="text" bind:value={settingsData.archiveboxUrl} />
      <button on:click={() => testConnection('archivebox')}>Test Connection</button>
    </div>
  </section>

  <section>
    <h2>Map Settings</h2>

    <div class="field">
      <label>Default Center Latitude</label>
      <input type="number" step="0.0001" bind:value={settingsData.mapCenter.lat} />
    </div>

    <div class="field">
      <label>Default Center Longitude</label>
      <input type="number" step="0.0001" bind:value={settingsData.mapCenter.lon} />
    </div>

    <div class="field">
      <label>Default Zoom Level (1-18)</label>
      <input type="number" min="1" max="18" bind:value={settingsData.mapZoom} />
    </div>
  </section>

  <section>
    <h2>Import Settings</h2>

    <div class="field checkbox">
      <label>
        <input type="checkbox" bind:checked={settingsData.autoUploadImmich} />
        Auto-upload to Immich
      </label>
    </div>

    <div class="field checkbox">
      <label>
        <input type="checkbox" bind:checked={settingsData.autoExtractGPS} />
        Auto-extract GPS from EXIF
      </label>
    </div>
  </section>

  <section>
    <h2>Appearance</h2>

    <div class="field">
      <label>Theme</label>
      <select bind:value={settingsData.theme}>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </div>
  </section>

  <div class="actions">
    <button class="save-btn" on:click={save}>Save Settings</button>
    <button class="reset-btn" on:click={reset}>Reset to Defaults</button>
    {#if saved}
      <span class="saved-indicator">✓ Saved</span>
    {/if}
  </div>
</div>

<style>
  .settings-container {
    padding: 40px;
    max-width: 800px;
    margin: 0 auto;
  }

  h1 {
    margin-bottom: 30px;
  }

  section {
    margin-bottom: 40px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
  }

  h2 {
    font-size: 18px;
    margin-bottom: 20px;
  }

  .field {
    margin-bottom: 20px;
  }

  .field label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
  }

  .field input[type="text"],
  .field input[type="number"],
  .field select {
    width: 100%;
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  .field button {
    margin-top: 10px;
    padding: 8px 16px;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .field.checkbox label {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .actions {
    display: flex;
    gap: 15px;
    align-items: center;
  }

  .save-btn {
    padding: 12px 24px;
    background: #27ae60;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
  }

  .save-btn:hover {
    background: #229954;
  }

  .reset-btn {
    padding: 12px 24px;
    background: #95a5a6;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
  }

  .reset-btn:hover {
    background: #7f8c8d;
  }

  .saved-indicator {
    color: #27ae60;
    font-weight: bold;
  }
</style>
```

**Testing**:
- Change settings → click save → verify localStorage updated
- Test connection buttons → verify API reachability
- Reset to defaults → verify all values reset
- Settings persist across app restarts

---

## PHASE 3: ESSENTIAL HARDENING

### MODULE 6: E2E TESTS

**6.1 Install Playwright**

```bash
cd desktop-app
npm install --save-dev @playwright/test
npx playwright install
```

**6.2 E2E Test (tests/e2e/import.spec.js)**

```javascript
const { test, expect } = require('@playwright/test');

test('full import workflow', async ({ page }) => {
  // Launch app
  await page.goto('http://localhost:5173');

  // Navigate to import
  await page.click('text=Import');

  // Select location
  await page.selectOption('select#location', { index: 1 });

  // Simulate file drop (mock)
  await page.evaluate(() => {
    window.mockFiles = [
      { path: '/test/photo1.jpg', name: 'photo1.jpg' },
      { path: '/test/photo2.jpg', name: 'photo2.jpg' }
    ];
  });

  // Start import
  await page.click('text=Import');

  // Wait for completion
  await page.waitForSelector('.results', { timeout: 30000 });

  // Verify results
  const resultsText = await page.textContent('.results');
  expect(resultsText).toContain('Import complete');
  expect(resultsText).toContain('Imported: 2');
});
```

**Testing**: Run `npx playwright test`

---

### MODULE 7: BACKUP AUTOMATION

**7.1 Backup Script (scripts/backup_v012.sh)**

```bash
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/user/aupat/data/backups"
DB_PATH="/home/user/aupat/data/aupat.db"

echo "Starting backup: $DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup SQLite database
cp "$DB_PATH" "$BACKUP_DIR/aupat_${DATE}.db"

# Git commit
cd /home/user/aupat
git add data/aupat.db
git commit -m "Backup: $DATE" || echo "No changes to commit"

# Restic backup (if configured)
if command -v restic &> /dev/null; then
    echo "Running Restic backup..."
    restic backup data/ --repo "$BACKUP_DIR/restic-repo" || echo "Restic backup failed"
fi

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "aupat_*.db" -mtime +30 -delete

echo "Backup complete: $DATE"
```

**7.2 Cron Job Setup**

```bash
crontab -e

# Add line (daily at 2 AM):
0 2 * * * /home/user/aupat/scripts/backup_v012.sh >> /home/user/aupat/data/logs/backup.log 2>&1
```

---

## PHASE 4: DEPLOYMENT

### MODULE 8: DESKTOP APP PACKAGING

**8.1 Mac .dmg Build**

```bash
cd desktop-app
npm run build:mac
# Output: desktop-app/dist/AUPAT-0.1.2.dmg
```

**8.2 Linux .AppImage Build**

```bash
cd desktop-app
npm run build:linux
# Output: desktop-app/dist/AUPAT-0.1.2.AppImage
```

**8.3 Installation Testing**

Test installers on clean Mac and Linux systems.

---

### MODULE 9: CLOUDFLARE TUNNEL

**9.1 Install cloudflared**

```bash
# Mac
brew install cloudflare/cloudflare/cloudflared

# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

**9.2 Setup Tunnel**

```bash
# Login
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create aupat

# Configure (copy tunnel ID from output)
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << EOF
tunnel: <TUNNEL_ID>
credentials-file: ~/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: aupat.yourdomain.com
    service: http://localhost:5000
  - hostname: photos.yourdomain.com
    service: http://localhost:2283
  - service: http_status:404
EOF

# Route DNS
cloudflared tunnel route dns aupat aupat.yourdomain.com
cloudflared tunnel route dns aupat photos.yourdomain.com

# Run tunnel
cloudflared tunnel run aupat

# Install as service
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

**Testing**: Access https://aupat.yourdomain.com/api/health from mobile device

---

## EXECUTION CHECKLIST

### Week 1-2: Desktop Scaffold + Map
- [ ] Module 1: Electron + Svelte scaffold (3-4 days)
- [ ] Module 2: Map view with clustering (5-7 days)
- [ ] Test: App launches, map loads 200k markers

### Week 3-4: Sidebar + Import
- [ ] Module 3: Location details sidebar (3-4 days)
- [ ] Module 4: Import interface (3-4 days)
- [ ] Test: Gallery displays, import works

### Week 5: Settings + Polish
- [ ] Module 5: Settings page (2 days)
- [ ] Polish UI, fix bugs (3 days)
- [ ] Test: End-to-end user workflow

### Week 6-7: Hardening
- [ ] Module 6: E2E tests (2 days)
- [ ] Module 7: Backup automation (1 day)
- [ ] Security tests (2 days)
- [ ] Documentation (2 days)

### Week 8: Deployment
- [ ] Module 8: Desktop app packaging (2 days)
- [ ] Module 9: Cloudflare tunnel (1 day)
- [ ] Operational runbooks (1 day)
- [ ] Final testing (1 day)

---

## CONCLUSION

**Total Estimated Time**: 8 weeks to v0.1.2 release

**Next Action**: Begin Module 1 (Electron + Svelte scaffold)

**Success Metric**: Desktop app displays map, allows import, and works end-to-end

This plan follows KISS, BPL, BPA, DRETW, NME strictly. No reinvention. Build on Phase 1 foundation. Ship v0.1.2.
