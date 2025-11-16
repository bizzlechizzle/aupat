# AUPAT FIX PLAN - Back to LOGSEQ Specifications

## CRITICAL ISSUES TO FIX

### 1. is_film BELONGS IN IMAGES TABLE, NOT LOCATIONS ❌
**Current State**: is_film, film_stock, film_format in locations table
**LOGSEQ Spec**: images_table.md line 20 - `film = true/false [starts null]`
**Why Wrong**: Film is a per-image property (some images in a shoot are film, others digital)
**Fix Required**:
- REMOVE is_film, film_stock, film_format from locations table schema
- REMOVE from locations table migration
- ADD film field to images table (INTEGER, defaults to NULL)
- REMOVE film fields from web interface location import form
- Film data should be detected/set during metadata extraction, not import

### 2. File Naming ✅ ALREADY CORRECT
**Current State**: Files named `loc_uuid8-sha8.ext` (e.g., `c5cb8d46-c9029253.jpg`)
**LOGSEQ Spec**: name_json.md lines 5-6 - `"loc_uuid8"-"img_sha8".image extension`
**Status**: ✅ Naming is correct - no "img_" or "vid_" prefixes
**No changes needed**

### 3. Video Metadata Extraction - Needs Verification
**LOGSEQ Spec**: db_organize.md lines 21-27
```
ffprobe -v quiet -show_entries format_tags=make,Make,model,Model
```
**Check**: Does db_organize.py properly extract DJI from video metadata?
**Hardware Detection**: camera_hardware.md line 19 - DJI is a drone manufacturer

### 4. Web Interface Styling
**Issue**: Header background and text colors don't match site design
**Fix Required**:
- Header background should match dark theme
- "Abandoned Upstate" text should be dark gray (#454545) in light mode

---

## ADDITIONAL CLEANUP TASKS

### 5. Remove Old/Duplicate .md Files
**Safe to Delete**:
- Root-level .md files that are duplicates of logseq/pages/ files
- Any outdated documentation not referenced in claude.md

**Keep**:
- logseq/pages/*.md - ALL original specifications
- claude.md - Main AI collaboration guide
- claudecode.md - Development methodology
- project-overview.md - If it's comprehensive and current

### 6. Create Proper README.md
**Tone**: Direct, no-bullshit, professional
**Content**:
- What AUPAT does in 2-3 sentences
- Quick start instructions
- Folder structure
- How to run imports
- No marketing fluff

### 7. Update .gitignore
**Add**:
- user/user.json (contains absolute paths)
- *.db, *.sqlite (database files)
- backups/ (backup directory)
- logs/ (log files)
- .DS_Store (macOS)
- __pycache__/ (Python cache)
- *.pyc (Python compiled)
- venv/ (virtual environment)

---

## IMPLEMENTATION PRIORITY

### PHASE 1: Critical Schema Fixes (DO FIRST)
1. Revert is_film from locations table
2. Add film to images table
3. Update db_migrate.py migration logic
4. Remove film fields from web interface

### PHASE 2: Metadata & Styling
5. Verify/fix video metadata extraction
6. Fix web interface header styling

### PHASE 3: Documentation & Cleanup
7. Create README.md
8. Update .gitignore
9. Remove duplicate .md files

### PHASE 4: Testing
10. Run full test import with real media files
11. Verify all metadata extraction works
12. Verify folder creation only creates needed folders
13. Verify import errors stay visible

---

## DETAILED FIX SPECIFICATIONS

### Fix #1: Database Schema Corrections

**File**: scripts/db_migrate.py

**REMOVE from locations table** (lines 54-56):
```python
is_film INTEGER DEFAULT 0,
film_stock TEXT,
film_format TEXT,
```

**REMOVE from migrations** (lines 246-249):
```python
{
    'table': 'locations',
    'columns': [
        ('is_film', 'INTEGER DEFAULT 0'),
        ('film_stock', 'TEXT'),
        ('film_format', 'TEXT')
    ]
}
```

**ADD to images table** (after line 82, before img_hardware):
```python
film INTEGER,
```

**ADD to migrations**:
```python
{
    'table': 'images',
    'columns': [
        ('film', 'INTEGER')
    ]
}
```

### Fix #2: Web Interface Changes

**File**: web_interface.py

**REMOVE** film fields from import form (search for "is_film", "film_stock", "film_format")
**REMOVE** from metadata.json creation
**REMOVE** from import_location_from_metadata() function

### Fix #3: Header Styling

**File**: web_interface.py (in BASE_TEMPLATE)

Find header styles and update to match site colors:
- Background: dark gray (#474747)
- Text: cream (#fffbf7)
- "Abandoned Upstate" text color: Keep cream in dark mode

---

## TEST DATA REQUIREMENTS

For comprehensive testing, need:
- [ ] DJI drone video (.mov with DJI metadata)
- [ ] DSLR images (.jpg, .raw)
- [ ] Phone images
- [ ] Film scans (if available)
- [ ] Documents (.pdf, .srt, .json)

---

## SUCCESS CRITERIA

- [ ] Database schema has NO film fields in locations table
- [ ] Database schema HAS film field in images table
- [ ] Import form does NOT ask for film information
- [ ] Video metadata extraction identifies DJI as drone
- [ ] Web interface header matches site design
- [ ] All tests pass with correct metadata
- [ ] Folders only created when media exists
- [ ] Failed imports stay visible for 30 minutes

---

## LOGSEQ SPECIFICATION COMPLIANCE CHECKLIST

- [ ] Naming follows name_json.md: `loc_uuid8-sha8.ext`
- [ ] Images table follows images_table.md exactly
- [ ] Videos table follows videos.md exactly
- [ ] Metadata extraction follows db_organize.md commands
- [ ] Hardware detection uses camera_hardware.json makes/models
- [ ] Folder structure follows folder_json.md
- [ ] Film field is in images table per images_table.md line 20

---

## NOTES

- File naming is ALREADY CORRECT - verified in test import
- Folder creation is ALREADY FIXED - only creates needed folders
- Import visibility is ALREADY FIXED - failed imports stay 30 min
- **Main issue**: is_film was added to wrong table (locations instead of images)
