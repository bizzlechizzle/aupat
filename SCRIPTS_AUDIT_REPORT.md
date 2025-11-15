# AUPAT Scripts Audit Report
**Date**: 2025-11-15
**Auditor**: Claude Code
**Status**: Pre-Implementation Review

---

## Executive Summary

**Current State**: 0 scripts implemented, 13 scripts documented

**Key Findings**:
1. ✅ **Script organization is logical** - Clear separation between pipeline and utilities
2. ⚠️ **Some wheel reinvention** - Standard operations reimplemented, but justified
3. ❌ **CRITICAL: Database normalization violation** - uuid8/sha8 redundancy must be fixed
4. ✅ **Dependencies are adequate** - All necessary tools available
5. ⚠️ **Potential consolidation opportunities** - Some scripts could be merged

---

## 1. Script Inventory & Purpose Analysis

### Import Pipeline Scripts (8 total)

#### 1.1 db_migrate.py
**Purpose**: Database schema creation and migration management
**Job**:
- Creates SQLite database with JSON1 extension
- Manages schema versions
- Performs migrations

**Reinventing the wheel?** NO
- Standard for any database-backed application
- Alembic/SQLAlchemy could be used, but overkill for SQLite
- Custom implementation justified for simplicity (KISS principle)

**Dependencies**:
- ✅ sqlite3 (built-in)
- ✅ JSON schema files (planned)

---

#### 1.2 db_import.py
**Purpose**: Import locations and media via CLI/web interface
**Job**:
- Generate UUIDs for locations
- Prompt for location details
- Import files to staging
- Generate SHA256 hashes
- Detect duplicates

**Reinventing the wheel?** PARTIAL
- UUID generation: Standard library (✅)
- SHA256 hashing: Standard library (✅)
- File copying: Standard library (✅)
- **Could use**: rsync for file transfers, but Python shutil is fine

**Dependencies**:
- ✅ gen_uuid.py (utility)
- ✅ gen_sha.py (utility)
- ✅ user.json (config)

---

#### 1.3 db_organize.py
**Purpose**: Extract metadata and categorize imported media
**Job**:
- Extract EXIF from images (exiftool)
- Extract metadata from videos (ffprobe)
- Categorize by hardware (DSLR, phone, drone, etc.)
- Match live photos to live videos
- Link documents to media

**Reinventing the wheel?** NO - Unique workflow
- Uses existing tools (exiftool, ffprobe) ✅
- Hardware categorization is custom logic (no existing tool does this)
- Live photo matching is custom (iPhone-specific logic)

**Dependencies**:
- ✅ exiftool (external binary)
- ✅ ffprobe (external binary)
- ✅ camera_hardware.json (classification rules)
- ✅ live_videos.json (matching rules)
- ✅ approved_ext.json, ignored_ext.json

**Potential Issues**:
- ⚠️ exiftool must be installed separately (documented in requirements.txt)
- ⚠️ ffprobe must be installed separately (documented in requirements.txt)

---

#### 1.4 db_folder.py
**Purpose**: Create organized folder structure
**Job**:
- Read folder template from folder.json
- Create state-type directories (e.g., "ny-industrial")
- Create location directories with UUID8
- Create hardware-based subdirectories

**Reinventing the wheel?** NO
- Standard os.makedirs() operations
- Template-driven structure is custom
- Could use cookiecutter, but overkill for simple folder creation

**Dependencies**:
- ✅ folder.json (template)
- ✅ user.json (archive path)
- ✅ os/pathlib (built-in)

---

#### 1.5 db_ingest.py
**Purpose**: Move files from staging to organized archive
**Job**:
- Generate standardized filenames
- Move files (hardlink same disk, copy different disk)
- Update database with new locations
- Preserve timestamps

**Reinventing the wheel?** PARTIAL
- File operations: Standard library (shutil) ✅
- Hardlink detection: Standard approach ✅
- **Could use**: rsync with --link-dest, but Python is fine

**Dependencies**:
- ✅ name.py (filename generation)
- ✅ shutil, os (built-in)
- ✅ Database

**Potential Issues**:
- ⚠️ Hardlink logic assumes same filesystem (need to detect cross-filesystem moves)

---

#### 1.6 db_verify.py
**Purpose**: Verify SHA256 integrity and cleanup staging
**Job**:
- Recalculate SHA256 for each moved file
- Compare to database value
- Delete staging files if verification passes
- Preserve staging if verification fails

**Reinventing the wheel?** NO
- Integrity verification is critical for archival
- Standard practice for data migration
- Similar to rsync --checksum, but with database tracking

**Dependencies**:
- ✅ gen_sha.py (SHA256 calculation)
- ✅ Database
- ✅ hashlib (built-in)

---

#### 1.7 db_identify.py
**Purpose**: Generate master JSON export per location
**Job**:
- Query all data for location
- Compile comprehensive JSON structure
- Write to location folder
- Update export timestamp

**Reinventing the wheel?** NO
- Export functionality is unique to this system
- Standard JSON serialization
- Similar to database dump, but location-specific

**Dependencies**:
- ✅ json (built-in)
- ✅ Database

---

#### 1.8 database_cleanup.py
**Purpose**: Database maintenance and integrity checks
**Job**:
- Run PRAGMA integrity_check
- Verify foreign key relationships
- Clean up old backups (retention policy)
- Vacuum database

**Reinventing the wheel?** NO
- Standard database maintenance operations
- Backup retention is custom logic
- Could use cron + SQL scripts, but Python is more maintainable

**Dependencies**:
- ✅ sqlite3 (built-in)
- ✅ user.json (backup paths)

---

### Utility Scripts (5 total)

#### 2.1 backup.py
**Purpose**: Create timestamped database backups
**Job**:
- Generate timestamp
- Copy database using SQLite backup API
- Verify backup created

**Reinventing the wheel?** NO
- Standard practice for database management
- Uses SQLite backup API (correct approach)
- Similar to automated backups, but integrated with import workflow

**Dependencies**:
- ✅ sqlite3 (built-in)
- ✅ user.json (paths)

---

#### 2.2 gen_uuid.py
**Purpose**: Generate unique UUID4 identifiers with collision detection
**Job**:
- Generate UUID4
- Check first 8 chars for uniqueness
- Retry if collision detected

**Reinventing the wheel?** MINIMAL
- UUID generation: uuid.uuid4() (built-in) ✅
- Collision detection: Custom logic (necessary for uuid8 uniqueness)
- Could be a function instead of separate script

**Dependencies**:
- ✅ uuid (built-in)
- ✅ Database (for collision checking)

**Consolidation Opportunity**: Could be merged into a utils.py module

---

#### 2.3 gen_sha.py
**Purpose**: Generate SHA256 hashes for files
**Job**:
- Calculate SHA256 hash
- Read file in chunks (memory efficient)
- Return full SHA256 and SHA8

**Reinventing the wheel?** YES - BUT JUSTIFIED
- hashlib.sha256() is built-in
- Chunked reading is standard pattern
- **Why separate script?** Reusability across import, verify, organize scripts
- **Alternative**: Use `shasum -a 256` command, but Python is more portable

**Dependencies**:
- ✅ hashlib (built-in)

**Consolidation Opportunity**: Could be merged into a utils.py module

---

#### 2.4 name.py
**Purpose**: Generate standardized filenames
**Job**:
- Apply naming template from name.json
- Format: {loc_uuid8}-{media_type}_{sha8}.{ext}
- Handle sub-locations

**Reinventing the wheel?** NO
- Naming convention is custom to this system
- Simple string formatting
- Could be a function, doesn't need to be separate script

**Dependencies**:
- ✅ name.json (naming templates)

**Consolidation Opportunity**: Could be merged into a utils.py module

---

#### 2.5 folder.py
**Purpose**: Create folder structures based on configuration
**Job**:
- Read folder.json template
- Create directory hierarchy
- Verify creation

**Reinventing the wheel?** MINIMAL
- os.makedirs() is built-in
- Template parsing is custom
- Could use cookiecutter or Jinja2, but overkill

**Dependencies**:
- ✅ folder.json (template)
- ✅ os/pathlib (built-in)

**Consolidation Opportunity**: Overlap with db_folder.py - consider merging

---

## 2. Reinventing the Wheel Analysis

### Summary Table

| Script | Wheel Reinvention? | Justification | Existing Alternatives |
|--------|-------------------|---------------|----------------------|
| db_migrate.py | ❌ NO | Standard for DB apps | Alembic (overkill) |
| db_import.py | ⚠️ PARTIAL | Uses stdlib, custom workflow | None for this use case |
| db_organize.py | ❌ NO | Unique categorization | None |
| db_folder.py | ❌ NO | Custom folder structure | None |
| db_ingest.py | ⚠️ PARTIAL | Standard file ops | rsync (less flexible) |
| db_verify.py | ❌ NO | Critical for integrity | None with DB tracking |
| db_identify.py | ❌ NO | Custom export format | None |
| database_cleanup.py | ❌ NO | Standard maintenance | Cron + SQL (less maintainable) |
| backup.py | ❌ NO | Standard practice | Cron + cp (less safe) |
| gen_uuid.py | ⚠️ MINIMAL | Adds collision detection | uuid module alone |
| gen_sha.py | ✅ YES | But reusable across scripts | shasum command |
| name.py | ❌ NO | Custom naming scheme | None |
| folder.py | ⚠️ MINIMAL | Template-driven | os.makedirs alone |

### Overall Assessment

**Are we reinventing the wheel?**

**NO** - for the most part. The project is:
- Using standard libraries where appropriate
- Leveraging existing tools (exiftool, ffprobe)
- Implementing custom business logic that no existing tool provides

**Key differentiators from existing photo/media management tools**:
1. **Location-based organization** (not date/event-based like Lightroom, digiKam)
2. **Hardware categorization** (DSLR vs phone vs drone) - unique
3. **SHA256 deduplication + integrity verification** - rare in photo tools
4. **Document-media relationships** - unique
5. **Live photo pairing** - specific to this workflow
6. **Bulletproof verification workflow** - not found in consumer tools

**Existing tools in this space**:
- **Adobe Lightroom** - Proprietary, subscription, date-based organization
- **digiKam** - Free, but GUI-heavy, date-based
- **PhotoPrism** - Web-based, opinionated structure, no hardware categorization
- **ExifTool** - Metadata extraction only, no organization
- **Beets** - Music library organizer (similar approach but for music)
- **Plex/Emby** - Media consumption, not archival

**None of these tools provide**:
- Geographic + hardware-based organization
- SQLite database with comprehensive relationships
- SHA256 integrity tracking with verification workflow
- Flexible folder structure based on templates

**Conclusion**: The combination of requirements is **unique enough to justify** a custom tool. Not pointless reinvention.

---

## 3. Database Normalization Review

### CRITICAL ISSUE IDENTIFIED

**Problem**: Schema violates 2NF/3NF normalization by storing redundant computed values.

**Violation Details**:

All tables store BOTH:
- Full identifier (loc_uuid, img_sha256, etc.)
- First 8 characters (loc_uuid8, img_sha8, etc.)

**Example**:
```sql
CREATE TABLE locations (
    loc_uuid TEXT PRIMARY KEY,      -- Full UUID
    loc_uuid8 TEXT UNIQUE NOT NULL  -- First 8 chars - REDUNDANT!
    ...
);
```

**Why this is wrong**:
1. **Violates normalization** - uuid8 is functionally dependent on loc_uuid
2. **Data redundancy** - Every record stores duplicate information
3. **Maintenance burden** - Risk of uuid/uuid8 getting out of sync
4. **Storage waste** - Unnecessary column storage

**Correct approach**:
```sql
-- Store only full UUID
CREATE TABLE locations (
    loc_uuid TEXT PRIMARY KEY,
    -- loc_uuid8 REMOVED
    ...
);

-- Compute uuid8 when needed
SELECT SUBSTR(loc_uuid, 1, 8) AS loc_uuid8 FROM locations;
```

**In Python**:
```python
loc_uuid8 = loc_uuid[:8]  # Compute on-the-fly
```

### Dependencies for Database Normalization

**Required capabilities**:
1. ✅ **SUBSTR() function** - Built into SQLite
2. ✅ **String slicing in Python** - Built into Python
3. ✅ **Foreign key enforcement** - Built into SQLite (PRAGMA foreign_keys = ON)
4. ✅ **JSON1 extension** - Built into SQLite 3.9+
5. ✅ **Transaction support** - Built into SQLite

**Dependency status**:

| Requirement | Available? | Source | Notes |
|------------|-----------|--------|-------|
| SUBSTR() function | ✅ YES | SQLite built-in | For computing uuid8/sha8 |
| Foreign key support | ✅ YES | SQLite built-in | Need PRAGMA foreign_keys = ON |
| JSON1 extension | ✅ YES | SQLite 3.9+ | For img_hardware, vid_hardware fields |
| Transaction support | ✅ YES | SQLite built-in | For atomic operations |
| Python sqlite3 | ✅ YES | Python standard library | Database operations |
| unidecode | ✅ YES | requirements.txt | Text normalization |
| python-dateutil | ✅ YES | requirements.txt | Date parsing |
| libpostal | ⚠️ OPTIONAL | External install | Address parsing (not critical) |

**Missing dependencies**: NONE for core normalization

**Optional dependencies**:
- libpostal - Address parsing and normalization (OPTIONAL, documented as such)

### Other Normalization Considerations

**JSON1 fields for many-to-many relationships**:
- `img_docs` (array of document SHA256s)
- `img_vids` (array of video SHA256s for live photos)
- `vid_imgs` (array of image SHA256s for live videos)
- `vid_docs` (array of document SHA256s)

**Is this normalized?**
- ⚠️ **Technically not fully normalized** (violates 1NF by storing arrays)
- ✅ **Acceptable for SQLite** - JSON1 extension provides querying capabilities
- ✅ **Pragmatic choice** - Alternative is junction tables (more complex)
- ✅ **Common pattern** in modern SQLite applications

**Recommendation**: Keep JSON1 fields for many-to-many relationships. They're:
- Easier to query with json_each()
- Simpler to maintain
- Standard practice in SQLite with JSON1

**Schema field name inconsistencies**:
- videos table uses `img_loc_o`, `img_name_o`, `img_add`, `img_update` instead of `vid_*`
- ❌ **BUG** - Should be corrected to `vid_loc_o`, `vid_name_o`, `vid_add`, `vid_update`

---

## 4. Script Consolidation Opportunities

### Potential Merges

#### Option 1: Create utils.py module
**Merge**:
- gen_uuid.py → utils.generate_uuid()
- gen_sha.py → utils.calculate_sha256()
- name.py → utils.generate_filename()

**Benefits**:
- Reduce script count: 13 → 10
- Single import for utilities
- Easier to test (one test file)

**Drawbacks**:
- Less granular (can't run gen_sha.py standalone easily)
- All-or-nothing import

**Recommendation**: ✅ **DO THIS** - These are small utility functions

---

#### Option 2: Merge folder.py into db_folder.py
**Current**:
- folder.py - Generic folder creation from template
- db_folder.py - Create folders for specific location

**Issue**: Significant overlap

**Recommendation**: ✅ **MERGE** - db_folder.py can handle both

**Result**: 10 → 9 scripts

---

#### Option 3: Merge db_identify.py into db_verify.py
**Current**:
- db_verify.py - Verify integrity after move
- db_identify.py - Generate JSON export

**Reasoning**: Both run at end of import workflow

**Recommendation**: ❌ **DO NOT MERGE** - Different purposes:
- Verification is critical safety check
- JSON export is informational
- Should remain separate for clarity

---

### Recommended Script Structure

**After consolidation**:

**Core Pipeline** (7 scripts):
1. db_migrate.py - Schema management
2. db_import.py - Import to staging
3. db_organize.py - Metadata extraction
4. db_folder.py - Folder creation (merged with folder.py)
5. db_ingest.py - Move to archive
6. db_verify.py - Integrity verification
7. db_identify.py - JSON export

**Maintenance** (1 script):
8. database_cleanup.py - Cleanup and maintenance

**Utilities** (2 files):
9. backup.py - Database backups (keep separate - important standalone operation)
10. utils.py - UUID, SHA256, naming functions (merged from gen_uuid.py, gen_sha.py, name.py)

**Web Application** (future):
11. aupat_webapp.py - Stage 2

**Total**: 10 scripts (down from 13)

---

## 5. Dependency Audit

### Python Standard Library (Built-in)

✅ All required, no installation needed:
- sqlite3 - Database operations
- pathlib - Path handling
- json - JSON parsing
- hashlib - SHA256 hashing
- uuid - UUID generation
- logging - Application logging
- argparse - CLI arguments
- datetime - Timestamps
- shutil - File operations
- os - OS operations

---

### Python Third-Party Packages

From requirements.txt:

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| unidecode | >=1.3.6 | Unicode → ASCII | ✅ Required |
| python-dateutil | >=2.8.2 | Date parsing | ✅ Required |
| pytest | >=7.4.0 | Testing | ✅ Required (dev) |
| pytest-cov | >=4.1.0 | Coverage | ✅ Required (dev) |
| postal | >=1.1.10 | Address parsing | ⚠️ Optional |

**Missing critical dependencies**: NONE

**Optional dependencies**:
- postal (libpostal) - Address parsing
  - Requires system library installation first
  - Documented as optional in requirements.txt
  - Can function without it (fallback to unidecode + titlecase)

---

### External Binary Tools

| Tool | Purpose | Required? | Installation |
|------|---------|-----------|--------------|
| exiftool | Image EXIF extraction | ✅ YES | brew install exiftool |
| ffprobe | Video metadata | ✅ YES | brew install ffmpeg |

**Status**:
- ✅ Documented in requirements.txt
- ✅ Check included in setup.sh
- ⚠️ Must be installed manually (can't be pip installed)

---

### Configuration Files (JSON)

All 13 JSON files documented but **not yet created**:

**Schema Definitions**:
1. ✅ locations.json
2. ✅ sub-locations.json
3. ✅ images.json
4. ✅ videos.json
5. ✅ documents.json
6. ✅ urls.json
7. ✅ versions.json

**Reference Data**:
8. ✅ camera_hardware.json
9. ✅ approved_ext.json
10. ✅ ignored_ext.json
11. ✅ live_videos.json

**Templates**:
12. ✅ folder.json
13. ✅ name.json

**User Config**:
14. ✅ user.json (template exists)

**Status**: All documented, none created yet (0% implementation)

---

## 6. Critical Issues & Recommendations

### CRITICAL - Must Fix Before Implementation

#### Issue #1: Database Normalization Violation
**Severity**: CRITICAL
**Impact**: Data redundancy, maintenance burden, violates BPA principle

**Problem**: Storing both full identifiers and 8-char prefixes as separate columns

**Fix**:
1. Remove all uuid8/sha8 columns from schema
2. Compute with SUBSTR() in SQL or [:8] in Python
3. Update all documentation

**Files to update**:
- All table schema files (logseq/pages/*_table.md)
- project-overview.md
- db_migrate.py implementation (when written)

**Effort**: LOW (documentation changes only, no code exists yet)
**Priority**: 1 - Fix before writing any scripts

---

#### Issue #2: Videos Table Field Name Inconsistencies
**Severity**: HIGH
**Impact**: Bugs, confusion, violates BPA

**Problem**: videos.json uses `img_*` instead of `vid_*` for some fields

**Incorrect**:
- `img_loc_o` → should be `vid_loc_o`
- `img_name_o` → should be `vid_name_o`
- `img_add` → should be `vid_add`
- `img_update` → should be `vid_update`

**Fix**: Update videos.json schema documentation

**Effort**: TRIVIAL
**Priority**: 1 - Fix before implementation

---

### HIGH - Should Address

#### Issue #3: Missing JSON Configuration Files
**Severity**: HIGH
**Impact**: Scripts cannot run without these

**Status**: 0/13 JSON files created (documented but not implemented)

**Action**: Create all JSON configuration files in data/ directory

**Priority**: 2 - Create before script implementation

---

#### Issue #4: Hardlink vs Copy Logic
**Severity**: MEDIUM
**Impact**: Performance and disk usage

**Current plan**: Auto-detect same vs different disk for hardlink vs copy

**Recommendation**: ✅ Good approach, ensure robust detection:
```python
import os
src_stat = os.stat(src_path)
dst_stat = os.stat(os.path.dirname(dst_path))
same_device = (src_stat.st_dev == dst_stat.st_dev)
```

**Priority**: 3 - Handle during db_ingest.py implementation

---

### MEDIUM - Consider

#### Issue #5: Script Consolidation
**Severity**: LOW
**Impact**: Code organization, maintainability

**Recommendation**: Consolidate utilities into utils.py module

**Benefits**:
- Fewer files (13 → 10)
- Easier testing
- Single import

**Priority**: 4 - Optional, but recommended

---

#### Issue #6: libpostal Dependency
**Severity**: LOW
**Impact**: Address parsing quality

**Current**: Optional dependency, may not be available on all systems

**Recommendation**: ✅ Keep as optional, document fallback behavior:
- If available: Use libpostal for address parsing
- If not: Use unidecode + titlecase

**Priority**: 5 - Document fallback behavior

---

## 7. Final Recommendations

### Immediate Actions (Before Implementation)

1. **FIX DATABASE SCHEMA** (Priority 1)
   - Remove all uuid8/sha8 columns from documentation
   - Update all table schema files
   - Update project-overview.md
   - Document computation approach (SUBSTR, [:8])

2. **FIX VIDEOS TABLE FIELD NAMES** (Priority 1)
   - Correct img_* → vid_* in videos.json documentation
   - Update all references

3. **CREATE JSON CONFIGURATION FILES** (Priority 2)
   - Create all 13 JSON files in data/ directory
   - Validate JSON syntax
   - Populate with documented schemas

4. **CONSOLIDATE UTILITIES** (Priority 4, Optional)
   - Merge gen_uuid.py, gen_sha.py, name.py → utils.py
   - Merge folder.py → db_folder.py
   - Reduce script count: 13 → 10

### Implementation Order

**Phase 1**: Utilities and Foundation
1. Create utils.py (UUID, SHA256, naming functions)
2. Create backup.py
3. Test utilities

**Phase 2**: Database
4. Create db_migrate.py (with corrected schema)
5. Test schema creation
6. Test migrations

**Phase 3**: Import Pipeline
7. Create db_import.py
8. Create db_organize.py
9. Create db_folder.py
10. Create db_ingest.py
11. Create db_verify.py
12. Create db_identify.py
13. Create database_cleanup.py
14. Test end-to-end workflow

**Phase 4**: Web Interface (Stage 2)
15. Create aupat_webapp.py

---

## 8. Conclusion

### Summary

**Scripts**: Well-organized, logical separation, minimal wheel reinvention
**Dependencies**: All necessary dependencies available and documented
**Database Normalization**: ❌ CRITICAL ISSUE - must remove uuid8/sha8 redundancy
**Consolidation**: ✅ Recommended - merge utilities into utils.py

### Overall Assessment

**Strengths**:
- Comprehensive documentation
- Clear workflow
- Bulletproof principles (BPA, BPL, KISS)
- Unique combination of features not found in existing tools

**Weaknesses**:
- Database normalization violation (fixable before implementation)
- Field name inconsistencies in videos table (fixable)
- No code implemented yet (0%)

**Verdict**:
✅ **APPROVED FOR IMPLEMENTATION** after fixing critical issues

**Action Items**:
1. Fix database schema normalization (remove uuid8/sha8)
2. Fix videos table field names
3. Create JSON configuration files
4. Consolidate utilities (optional but recommended)
5. Begin implementation following roadmap

---

**Report Status**: COMPLETE
**Next Steps**: Fix critical issues, then begin Phase 1 implementation
