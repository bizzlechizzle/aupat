# AUPAT v0.1.0 Feature Implementation Plan

**Created:** 2025-11-19
**Purpose:** Complete all missing v0.1.0 features following Core Process
**Status:** Step 3 - Making Plan

---

## STEP 1-2: Requirements Analysis

### User Request:
1. Fix all missing v0.1.0 features from spec
2. Get App Icon.png from old GitHub repo
3. Update app icon in desktop app

### Missing v0.1.0 Features:

#### 1. **Locations Dashboard** (Currently: simple table view)
**Spec Requirements:**
- Pinned Locations (top 5)
- Recent Locations (last 5)
- Recently Imported/Updated (last 5)
- States (top 5 by count)
- Types (top 10 by count)
- Quick Links: Favorites, Random, Un-Documented, Historical, To-Do List

**Current State:**
- `desktop/src/renderer/lib/LocationsList.svelte` - Simple table with search
- No dashboard features
- Missing API endpoints for stats

**Gap Analysis:**
- Need API endpoints for statistics
- Need dashboard UI component
- Need bookmark/favorite functionality in database

#### 2. **LocationPage Component** (Currently: LocationPage.svelte exists but incomplete)
**Spec Requirements:**
- Hero image
- Location name
- Sub-locations list
- Edit Button and Import Button
- Details (all input fields)
- User Notes section with title list
- Images gallery
- Videos gallery
- Bookmarks list
- Documents list
- Nerd Stats

**Current State:**
- File exists at `desktop/src/renderer/lib/LocationPage.svelte`
- Needs review and completion

**Gap Analysis:**
- Need to review existing component
- May need notes API endpoints
- Need media gallery components

#### 3. **Browser Component** (Currently: MISSING)
**Spec Requirements:**
- Works like a normal browser
- Saves bookmarks
- Bookmark structure: State > Type > Location

**Current State:**
- Completely missing
- `browser-manager.js` exists in main process but no UI component

**Gap Analysis:**
- Need Electron BrowserView integration
- Need UI component
- Need bookmark sync functionality

#### 4. **App Icon** (Currently: Generic icons)
**Requirements:**
- Get "Abandoned Upstate Icon.png" from old repo
- Update desktop/resources/icons/

**Current State:**
- Generic icons in desktop/resources/icons/
- logo.png exists in desktop/src/renderer/assets/

**Gap Analysis:**
- Need to locate old repo
- Need icon conversion tools (png to icns/ico)

---

## STEP 3: IMPLEMENTATION PLAN

### Phase 1: API Endpoints for Dashboard (LILBITS compliant)

**File:** `scripts/api_v010_stats.py` (NEW - <200 lines)

**Endpoints to create:**
```python
GET /api/stats/pinned - Get pinned locations (top 5)
GET /api/stats/recent - Get recent locations (last 5)
GET /api/stats/updated - Get recently updated (last 5)
GET /api/stats/states - Get top 5 states by count
GET /api/stats/types - Get top 10 types by count
GET /api/stats/counts - Get quick count stats (favorites, undocumented, historical, etc.)
```

**Database Schema Check:**
- Need `favorites` or `pinned` field in locations table
- Need `documented` boolean field
- Need `updated_at` timestamp (already exists)

**Dependencies:**
- scripts/utils.py (get_db_connection)
- Register in scripts/api_routes_v010.py

---

### Phase 2: Locations Dashboard UI

**File:** `desktop/src/renderer/lib/LocationsDashboard.svelte` (NEW)

**Layout Structure:**
```
┌─────────────────────────────────────┐
│ Dashboard Header                     │
├─────────────────────────────────────┤
│ Quick Links Row                      │
│ [Fav] [Random] [Undoc] [Hist] [ToDo]│
├─────────────────────────────────────┤
│ Pinned Locations (Top 5)             │
├─────────────────────────────────────┤
│ Recent Locations  │ Recently Updated │
│ (Last 5)          │ (Last 5)         │
├─────────────────────────────────────┤
│ Top States (5)    │ Top Types (10)   │
├─────────────────────────────────────┤
```

**Components needed:**
- LocationCard.svelte (reusable card for each location)
- StatsCard.svelte (for states/types stats)

**Update:** `desktop/src/renderer/App.svelte`
- Render LocationsDashboard instead of LocationsList

---

### Phase 3: LocationPage Enhancement

**File:** `desktop/src/renderer/lib/LocationPage.svelte` (UPDATE)

**Current Status:** Review needed

**Enhancement Checklist:**
- [ ] Hero image (first image or placeholder)
- [ ] Sub-locations list with links
- [ ] Edit button (opens LocationForm)
- [ ] Import button (opens Import with location pre-selected)
- [ ] Details section (all location fields)
- [ ] Notes section (create/edit/list)
- [ ] Images gallery (grid with lightbox)
- [ ] Videos gallery (grid with player)
- [ ] Bookmarks list
- [ ] Documents list
- [ ] Nerd Stats (file counts, dates, etc.)

**New Components:**
- ImageGallery.svelte
- VideoGallery.svelte
- DocumentsList.svelte
- NerdStats.svelte

**API Endpoints needed:**
```
GET /api/notes?loc_uuid=<uuid> - List notes for location
POST /api/notes - Create note
PUT /api/notes/<note_id> - Update note
DELETE /api/notes/<note_id> - Delete note
```

**Database Schema:**
- Notes table already exists (check scripts/db_migrate_v010.py)

---

### Phase 4: Browser Component

**Files to create:**
1. `desktop/src/renderer/lib/Browser.svelte` (Main UI)
2. `desktop/src/renderer/lib/BrowserToolbar.svelte` (URL bar, nav buttons)
3. `desktop/src/renderer/lib/BookmarkBar.svelte` (Saved bookmarks)

**Electron Integration:**
- Use `<webview>` tag in Electron (sandboxed browser)
- IPC handlers in main/index.js for:
  - browser:navigate
  - browser:back
  - browser:forward
  - browser:bookmark

**BrowserView vs WebView:**
- WebView = easier integration with Svelte
- BrowserView = better performance but harder integration
- **Decision:** Use `<webview>` tag for v0.1.0 (simpler)

**Bookmark Structure:**
```javascript
{
  bookmark_uuid: "abc123",
  url: "https://example.com",
  title: "Example Site",
  state: "ny",         // Organizational hierarchy
  type: "industrial",
  loc_uuid: "xyz789",  // Optional - link to location
  folder: null,        // For future folder support
  created_at: "2024-..."
}
```

**API Endpoints:**
- Already exist in `/api/bookmarks` (api_routes_bookmarks.py)

---

### Phase 5: App Icon Update

**Steps:**
1. **Locate old repo:**
   - Check `/home/user/aupat/archive/abandonedupstate`
   - If missing, ask user for icon file or GitHub URL

2. **Convert icon formats:**
   - Source: PNG (preferably 1024x1024)
   - macOS: .icns (multiple sizes)
   - Windows: .ico (multiple sizes)
   - Linux: .png (512x512)

3. **Tools needed:**
   ```bash
   # macOS .icns creation
   iconutil -c icns icon.iconset/

   # Windows .ico creation
   convert icon.png -define icon:auto-resize=256,128,96,64,48,32,16 icon.ico

   # Or use electron-icon-builder
   npm install -g electron-icon-builder
   electron-icon-builder --input=./icon.png --output=./resources/icons/
   ```

4. **Files to update:**
   - `desktop/resources/icons/icon.icns` (macOS)
   - `desktop/resources/icons/icon.ico` (Windows)
   - `desktop/resources/icons/icon.png` (Linux/source)
   - `desktop/src/renderer/assets/logo.png` (in-app logo)

5. **electron-builder config:**
   - Check `desktop/package.json` build.icon path

---

## STEP 4: PLAN AUDIT

### LILBITS Compliance Check:
✅ api_v010_stats.py - One function (statistics endpoints) <200 lines
✅ Each new component - Single responsibility
✅ Browser split into 3 components - Complexity management

### BPA (Best Practices Always):
✅ Use existing patterns from codebase
✅ Follow Svelte conventions
✅ Use Tailwind classes for styling
✅ Maintain v0.1.0 compatibility (no v0.1.2+ features)

### KISS Principle:
✅ Dashboard: Simple card layout
✅ Browser: Use `<webview>` not complex BrowserView
✅ Icons: Use existing tools (electron-icon-builder)

### BPL (Bulletproof Long-Term):
✅ Stats API designed for scaling (pagination ready)
✅ Components reusable
✅ Database queries optimized with indexes

### DRETW (Don't Re-Invent The Wheel):
✅ Use Leaflet's existing components
✅ Use Electron's built-in `<webview>`
✅ Use electron-icon-builder for icon conversion

---

## STEP 5: IMPLEMENTATION GUIDE (For New Coder)

### Order of Implementation:

**Day 1: API Foundation**
1. Create `scripts/api_v010_stats.py`
2. Add database fields (favorites, pinned, documented)
3. Register routes in `api_routes_v010.py`
4. Test with curl/Postman

**Day 2: Dashboard UI**
1. Create `LocationsDashboard.svelte`
2. Create `LocationCard.svelte`
3. Create `StatsCard.svelte`
4. Wire up API calls
5. Replace LocationsList in App.svelte

**Day 3: LocationPage Enhancement**
1. Review existing LocationPage.svelte
2. Add missing sections one by one
3. Create ImageGallery.svelte
4. Create VideoGallery.svelte
5. Test with real data

**Day 4: Browser Component**
1. Create Browser.svelte with `<webview>` tag
2. Create BrowserToolbar.svelte
3. Add IPC handlers in main/index.js
4. Wire up bookmark saving
5. Add to App.svelte navigation

**Day 5: App Icon**
1. Locate icon PNG
2. Install electron-icon-builder
3. Generate all icon formats
4. Update package.json if needed
5. Test build

**Day 6: Testing & Polish**
1. Manual testing all features
2. Fix bugs
3. Update documentation
4. Commit and push

---

## STEP 6-7: TECHNICAL GUIDE

### Database Schema Updates

**Add to locations table:**
```sql
ALTER TABLE locations ADD COLUMN pinned INTEGER DEFAULT 0;
ALTER TABLE locations ADD COLUMN documented INTEGER DEFAULT 0;
ALTER TABLE locations ADD COLUMN favorite INTEGER DEFAULT 0;

CREATE INDEX idx_locations_pinned ON locations(pinned DESC);
CREATE INDEX idx_locations_documented ON locations(documented);
CREATE INDEX idx_locations_favorite ON locations(favorite);
```

**Notes table** (verify exists):
```sql
-- Should already exist from db_migrate_v010.py
SELECT name FROM sqlite_master WHERE type='table' AND name='notes';
```

### API Examples

**Stats Endpoint Response:**
```json
{
  "success": true,
  "data": {
    "pinned": [
      {"loc_uuid": "abc", "loc_name": "Old Mill", "state": "ny", "type": "industrial"},
      ...
    ],
    "recent": [...],
    "updated": [...],
    "states": [
      {"state": "ny", "count": 150},
      {"state": "pa", "count": 87},
      ...
    ],
    "types": [
      {"type": "industrial", "count": 234},
      ...
    ],
    "counts": {
      "total": 500,
      "favorites": 12,
      "undocumented": 45,
      "historical": 23,
      "with_notes": 67
    }
  }
}
```

### Component Architecture

**LocationsDashboard.svelte:**
```svelte
<script>
  import { onMount } from 'svelte';
  import LocationCard from './LocationCard.svelte';
  import StatsCard from './StatsCard.svelte';

  let stats = {
    pinned: [],
    recent: [],
    updated: [],
    states: [],
    types: [],
    counts: {}
  };

  onMount(async () => {
    const response = await window.api.stats.getAll();
    if (response.success) {
      stats = response.data;
    }
  });
</script>

<div class="dashboard p-8">
  <!-- Quick Links -->
  <div class="quick-links mb-6">
    <button on:click={() => filterFavorites()}>Favorites ({stats.counts.favorites})</button>
    <!-- More buttons -->
  </div>

  <!-- Pinned -->
  <section class="mb-8">
    <h2>Pinned Locations</h2>
    <div class="grid grid-cols-5 gap-4">
      {#each stats.pinned as location}
        <LocationCard {location} />
      {/each}
    </div>
  </section>

  <!-- States and Types in 2 columns -->
  <div class="grid grid-cols-2 gap-8">
    <StatsCard title="Top States" items={stats.states} />
    <StatsCard title="Top Types" items={stats.types} />
  </div>
</div>
```

**Browser.svelte:**
```svelte
<script>
  let currentUrl = 'https://www.abandonedupstate.com';
  let canGoBack = false;
  let canGoForward = false;

  function navigate() {
    const webview = document.querySelector('webview');
    webview.loadURL(currentUrl);
  }

  function saveBookmark() {
    const webview = document.querySelector('webview');
    window.api.bookmarks.create({
      url: webview.getURL(),
      title: webview.getTitle()
    });
  }
</script>

<div class="browser h-full flex flex-col">
  <BrowserToolbar
    bind:url={currentUrl}
    {canGoBack}
    {canGoForward}
    on:navigate={navigate}
    on:bookmark={saveBookmark}
  />

  <webview
    src={currentUrl}
    class="flex-1"
    allowpopups
  />
</div>
```

---

## STEP 8: IMPLEMENTATION CHECKLIST

### Phase 1: API (scripts/api_v010_stats.py)
- [ ] Create file
- [ ] Add stats endpoints
- [ ] Register in api_routes_v010.py
- [ ] Test endpoints

### Phase 2: Database
- [ ] Add pinned column
- [ ] Add documented column
- [ ] Add favorite column
- [ ] Create indexes
- [ ] Migrate existing data

### Phase 3: Dashboard
- [ ] Create LocationsDashboard.svelte
- [ ] Create LocationCard.svelte
- [ ] Create StatsCard.svelte
- [ ] Add IPC handlers for stats
- [ ] Update App.svelte
- [ ] Test

### Phase 4: LocationPage
- [ ] Review existing file
- [ ] Add missing sections
- [ ] Create ImageGallery.svelte
- [ ] Create VideoGallery.svelte
- [ ] Create DocumentsList.svelte
- [ ] Create NerdStats.svelte
- [ ] Test

### Phase 5: Browser
- [ ] Create Browser.svelte
- [ ] Create BrowserToolbar.svelte
- [ ] Create BookmarkBar.svelte
- [ ] Add IPC handlers
- [ ] Add to navigation
- [ ] Test bookmark saving

### Phase 6: App Icon
- [ ] Locate Abandoned Upstate Icon.png
- [ ] Install electron-icon-builder
- [ ] Generate .icns for macOS
- [ ] Generate .ico for Windows
- [ ] Update logo.png
- [ ] Test build

---

## STEP 9: TESTING PLAN

### Manual Testing Checklist:

**Dashboard:**
- [ ] Shows pinned locations correctly
- [ ] Shows recent locations (newest first)
- [ ] Shows updated locations (newest first)
- [ ] Shows top 5 states with counts
- [ ] Shows top 10 types with counts
- [ ] Quick links filter correctly
- [ ] Cards clickable, navigate to LocationPage

**LocationPage:**
- [ ] Hero image displays
- [ ] Sub-locations list shows
- [ ] Edit button opens LocationForm
- [ ] Import button opens Import view
- [ ] All details display
- [ ] Notes can be created/edited/deleted
- [ ] Images gallery works
- [ ] Videos gallery works
- [ ] Bookmarks list shows
- [ ] Documents list shows
- [ ] Nerd stats calculate correctly

**Browser:**
- [ ] URL bar works
- [ ] Back/forward buttons work
- [ ] Page loads correctly
- [ ] Bookmark button saves
- [ ] Bookmarks appear in list
- [ ] Can navigate to bookmarked sites

**App Icon:**
- [ ] Icon shows in macOS dock
- [ ] Icon shows in Windows taskbar
- [ ] Icon shows in app title bar
- [ ] Build includes correct icons

---

## STEP 10: DOCUMENTATION UPDATES

### Files to update:

**techguide.md:**
- Desktop UI architecture (add dashboard, browser)
- Component hierarchy
- IPC handlers list

**lilbits.md:**
- Add api_v010_stats.py
- Add new Svelte components
- Add browser integration

**README.md:**
- Update feature list
- Update screenshots (after implementation)

---

## PRIORITIES & ESTIMATES

### High Priority (MVP blockers):
1. **Locations Dashboard** - 6 hours (API + UI)
2. **LocationPage Enhancement** - 4 hours
3. **App Icon** - 1 hour

### Medium Priority (Complete v0.1.0):
4. **Browser Component** - 6 hours

### Low Priority (Nice to have):
- Polish and bug fixes

**Total Estimate:** 17 hours of focused work

---

## RISKS & MITIGATIONS

### Risk 1: Icon file not found
**Mitigation:** Ask user for file or use placeholder, can update later

### Risk 2: WebView doesn't work in Electron
**Mitigation:** Test early, fall back to external browser if needed

### Risk 3: Stats queries slow with large dataset
**Mitigation:** Add LIMIT clauses, create indexes, test with sample data

### Risk 4: Time constraint
**Mitigation:** Prioritize dashboard and LocationPage, browser can be v0.1.1

---

## SUCCESS CRITERIA

✅ Dashboard shows all 6 sections from spec
✅ LocationPage has all 11 elements from spec
✅ Browser component functional (even if basic)
✅ App icon updated from Abandoned Upstate branding
✅ All features work without errors
✅ Code follows LILBITS principle
✅ Documentation updated
✅ Committed and pushed to Git

---

**End of Plan - Ready for Implementation**
