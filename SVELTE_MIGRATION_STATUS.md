# Svelte Component Migration Status

## Overview
Migration of Svelte UI components from old desktop preload API to desktop-v2 IPC API per MIGRATION_GUIDE.md.

## Completed Migrations

### 1. Locations API Updates
**Changed: `window.api.locations.*` → `window.api.location.*`**

- ✅ `locations.getById(id)` → `location.get(uuid)`
  - LocationsDashboard.svelte (line 247)
  - Import.svelte (line 138)
  - LocationPage.svelte (line 70)

- ✅ `locations.getAll()` → `location.getAll()`
  - LocationPage.svelte (line 143)

### 2. Stats API Updates
**Changed: `window.api.stats.getDashboard()` → `window.api.stats.dashboard()`**

- ✅ LocationsDashboard.svelte (line 46)

## Migrations Requiring Complex Refactoring

### 1. Import API (NOT MIGRATED - Needs Refactoring)
The import API signature changed significantly:

**Old API:**
```javascript
window.api.import.uploadFile({
  locationId, filename, category, size, data, sub_location
})

window.api.import.bulkImport({
  locationId, sourcePath, author
})
```

**New API (desktop-v2):**
```javascript
window.api.import.file(filePath, locationData, options)
window.api.import.batch(filePaths, locationData, options)
```

**Files Affected:**
- Import.svelte (line 412) - uploadFile needs refactoring
- LocationPage.svelte (line 337) - bulkImport needs refactoring

**Required Changes:**
- Change from base64 data upload to file path references
- Restructure locationData object format
- Update options parameter structure

### 2. Settings/Config API (NOT MIGRATED - Data Structure Changed)
**Old API:**
```javascript
window.api.config.get()          // Returns: {db_path, staging_path, archive_path, backup_path}
window.api.config.update(data)
window.api.dialog.selectDirectory()
```

**New API (desktop-v2):**
```javascript
window.api.settings.getAll()     // Returns: {dbPath, archiveRoot, deleteAfterImport, importAuthor, mapCenter, mapZoom}
window.api.settings.update(updates)
window.api.settings.chooseFolder(title)
```

**Files Affected:**
- Settings.svelte (lines 42, 86, 100)

**Required Changes:**
- Update data structure mapping (db_path → dbPath, archive_path → archiveRoot, etc.)
- Remove/refactor fields not in new API (staging_path, backup_path)
- Update chooseFolder calls with title parameter

### 3. Autocomplete API (NOT MIGRATED - No Equivalent in v2)
**Old API:**
```javascript
window.api.locations.autocomplete(field, options)  // Field-specific autocomplete
```

**New API (desktop-v2):**
```javascript
window.api.location.search(searchTerm, limit)      // General search only
```

**Files Affected:**
- LocationForm.svelte (lines 180-183, 210)

**Required Changes:**
- Either implement field-specific autocomplete in desktop-v2 backend, OR
- Refactor components to use general search instead of field-specific autocomplete

## Non-Migrated APIs (Not in desktop-v2 yet)
These APIs are still using old desktop preload and cannot be migrated yet:

- `window.api.bookmarks.*` - Bookmarks functionality
- `window.api.images.*` - Image gallery functionality
- `window.api.videos.*` - Video gallery functionality
- `window.api.urls.*` - Web archive functionality
- `window.api.notes.*` - Notes functionality
- `window.api.map.*` - Map markers functionality
- `window.api.updates.*` - Auto-update functionality
- `window.api.dialog.*` - Dialog utilities (partially replaced by settings.chooseFolder)

## Next Steps

### Phase 1: Backend API Implementation
Before components can be fully migrated, desktop-v2 needs:
1. Field-specific autocomplete API for location fields
2. Remaining API modules (bookmarks, images, videos, urls, notes, map, updates)

### Phase 2: Component Refactoring
Once backend APIs are available:
1. Refactor Import.svelte to use file paths instead of base64 uploads
2. Refactor Settings.svelte to use new settings data structure
3. Refactor LocationForm.svelte autocomplete to use new search API
4. Migrate remaining components as backend APIs become available

### Phase 3: Testing
1. Copy desktop-v2 preload and handlers to desktop/src/
2. Test all updated components with desktop-v2 backend
3. Verify data flow and error handling
4. Performance testing with large datasets

## Summary
- **Completed:** 5 simple API method renames (locations, stats)
- **Pending:** 3 complex refactorings (import, settings, autocomplete)
- **Blocked:** 8 API modules not yet in desktop-v2 backend

The simple method renames have been completed and are ready for testing once the desktop-v2 backend is integrated into the desktop application.
