# AUPAT v2 - API Migration Guide

Guide for updating Svelte components from Flask HTTP API to IPC API.

## Overview

**Old (Flask):** Svelte → HTTP fetch → Flask (port 5002) → SQLite
**New (v2):** Svelte → IPC → Electron Main → SQLite (direct)

**Benefits:**
- No Flask startup issues
- 6x faster database access
- Works 100% offline
- Simpler architecture

---

## Quick Reference

### Old Flask API
```javascript
// locations.js (old)
const response = await fetch('http://127.0.0.1:5002/api/locations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name, state, type })
});
const result = await response.json();
```

### New IPC API
```javascript
// locations.js (new)
const result = await window.api.location.create({ name, state, type });
```

---

## API Changes

### Locations

#### Create Location
```javascript
// OLD (Flask)
const response = await fetch('http://127.0.0.1:5002/api/locations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Buffalo Psychiatric Center',
    state: 'NY',
    type: 'Hospital',
    gps: '42.8864, -78.8784'
  })
});
const data = await response.json();

// NEW (IPC)
const result = await window.api.location.create({
  name: 'Buffalo Psychiatric Center',
  state: 'NY',
  type: 'Hospital',
  gps: '42.8864, -78.8784'
});

// Response format: {success: boolean, data?: Object, error?: string}
if (result.success) {
  const location = result.data;  // {loc_uuid, loc_short, loc_name}
}
```

#### Get Location
```javascript
// OLD
const response = await fetch(`http://127.0.0.1:5002/api/locations/${locUuid}`);
const location = await response.json();

// NEW
const result = await window.api.location.get(locUuid);
if (result.success) {
  const location = result.data;
}
```

#### Get All Locations
```javascript
// OLD
const response = await fetch('http://127.0.0.1:5002/api/locations');
const locations = await response.json();

// NEW
const result = await window.api.location.getAll();
if (result.success) {
  const locations = result.data;
}

// With pagination
const result = await window.api.location.getAll({
  limit: 10,
  offset: 0,
  orderBy: 'updated_at DESC'
});
```

#### Search Locations (Autocomplete)
```javascript
// OLD
const response = await fetch(
  `http://127.0.0.1:5002/api/locations/search?q=${searchTerm}`
);
const matches = await response.json();

// NEW
const result = await window.api.location.search(searchTerm, 10);
if (result.success) {
  const matches = result.data;
}
```

#### Update Location
```javascript
// OLD
const response = await fetch(`http://127.0.0.1:5002/api/locations/${locUuid}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ status: 'Demolished' })
});

// NEW
const result = await window.api.location.update(locUuid, {
  status: 'Demolished'
});
```

#### Delete Location
```javascript
// OLD
const response = await fetch(
  `http://127.0.0.1:5002/api/locations/${locUuid}`,
  { method: 'DELETE' }
);

// NEW
const result = await window.api.location.delete(locUuid);
```

---

### Import

#### Import Single File
```javascript
// OLD
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('loc_uuid', locUuid);
formData.append('state', 'ny');
formData.append('type', 'hospital');

const response = await fetch('http://127.0.0.1:5002/api/import', {
  method: 'POST',
  body: formData
});
const result = await response.json();

// NEW
const result = await window.api.import.file(
  filePath,  // Full file path (from file picker)
  {
    locUuid: location.loc_uuid,
    locShort: location.loc_short,
    state: 'ny',
    type: 'hospital'
  },
  {
    deleteSource: false  // Optional
  }
);

// Response: {success, fileUuid, mediaType, fileName, verified, error?}
```

#### Import Multiple Files (Batch)
```javascript
// NEW (no Flask equivalent)
const filePaths = ['/path/to/photo1.jpg', '/path/to/photo2.jpg'];

const result = await window.api.import.batch(
  filePaths,
  locationData,
  { deleteSource: false }
);

// Response: {success, data: {total, imported, failed, errors}}
```

#### Import Progress Updates
```javascript
// NEW
// Listen for progress
window.api.import.onProgress((data) => {
  console.log(`${data.current} / ${data.total}`);
  progressBar.value = (data.current / data.total) * 100;
});

// Start import
await window.api.import.batch(filePaths, locationData);

// Clean up listener
window.api.import.removeProgressListener();
```

---

### Settings

#### Get Settings
```javascript
// OLD
const response = await fetch('http://127.0.0.1:5002/api/settings');
const settings = await response.json();

// NEW
const result = await window.api.settings.getAll();
if (result.success) {
  const settings = result.data;
  // {dbPath, archiveRoot, deleteAfterImport, importAuthor, mapCenter, mapZoom}
}
```

#### Update Settings
```javascript
// OLD
const response = await fetch('http://127.0.0.1:5002/api/settings', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ deleteAfterImport: true })
});

// NEW
const result = await window.api.settings.update({
  deleteAfterImport: true
});
```

#### Choose Folder (Native Dialog)
```javascript
// NEW (no Flask equivalent - used native file picker)
const result = await window.api.settings.chooseFolder('Choose Archive Folder');
if (result.success && !result.canceled) {
  const folderPath = result.data;
  // Update settings with new path
  await window.api.settings.update({ archiveRoot: folderPath });
}
```

---

### Statistics

#### Dashboard Stats
```javascript
// OLD
const response = await fetch('http://127.0.0.1:5002/api/stats/dashboard');
const stats = await response.json();

// NEW
const result = await window.api.stats.dashboard();
if (result.success) {
  const stats = result.data;
  // {locations, images, videos, documents, maps, states, types}
}
```

#### By State
```javascript
// NEW
const result = await window.api.stats.byState();
// Returns: [{state: 'ny', count: 10}, {state: 'ca', count: 5}, ...]
```

#### By Type
```javascript
// NEW
const result = await window.api.stats.byType();
// Returns: [{type: 'hospital', count: 15}, {type: 'industrial', count: 8}, ...]
```

---

## Error Handling

### Old (Flask)
```javascript
try {
  const response = await fetch('http://127.0.0.1:5002/api/locations');

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data = await response.json();
} catch (error) {
  console.error('API error:', error);
}
```

### New (IPC)
```javascript
const result = await window.api.location.getAll();

if (!result.success) {
  console.error('Error:', result.error);
  // Show user-friendly error message
  showError(result.error);
} else {
  const locations = result.data;
  // Use data
}
```

---

## Common Patterns

### Loading State
```javascript
let loading = false;
let locations = [];

async function loadLocations() {
  loading = true;
  const result = await window.api.location.getAll();
  loading = false;

  if (result.success) {
    locations = result.data;
  } else {
    console.error('Failed to load:', result.error);
  }
}
```

### Form Submission
```javascript
async function handleSubmit() {
  const result = await window.api.location.create({
    name: formData.name,
    state: formData.state,
    type: formData.type,
    gps: formData.gps
  });

  if (result.success) {
    // Success - navigate to location page
    goto(`/locations/${result.data.loc_uuid}`);
  } else {
    // Show error
    errorMessage = result.error;
  }
}
```

---

## Migration Checklist

For each Svelte component:

- [ ] Remove `fetch()` calls to `http://127.0.0.1:5002`
- [ ] Replace with `window.api.*` calls
- [ ] Update error handling (check `result.success`)
- [ ] Update response handling (use `result.data`)
- [ ] Test functionality
- [ ] Remove Flask dependency checks

---

## Testing

After migration, verify:

1. **Locations work:**
   - Create location
   - View location list
   - Search locations
   - Update location
   - Delete location

2. **Import works:**
   - Import single file
   - Import multiple files
   - Progress updates display
   - Files appear in archive

3. **Settings work:**
   - View settings
   - Update settings
   - Folder picker works

4. **Stats work:**
   - Dashboard shows correct counts
   - State/type breakdowns work

---

## Need Help?

Check the working examples in:
- `test-example.js` - Backend usage
- `src/preload/index.js` - Available API methods
- `src/main/ipc-handlers.js` - Handler implementation
