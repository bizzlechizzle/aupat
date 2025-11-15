# AUPAT CLI Audit Report
**Date:** 2025-11-15
**Auditor:** Claude
**Scope:** Full audit of db_import.py and web_interface.py against db_import.md specification

---

## Executive Summary

**Status: CRITICAL GAPS IDENTIFIED**

The current implementation of `db_import.py` and `web_interface.py` is **incomplete** compared to the specification in `db_import.md`. While location records are being created, **media files are not being inserted into the database**. The workflow only copies files to staging but does not create database records for images, videos, documents, or URLs.

### Critical Issues
1. ❌ **No media database records created** - Files copied to staging but no database entries
2. ❌ **No file type detection** - Cannot distinguish images from videos from documents
3. ❌ **No backup before import** - Spec requires backup, not implemented
4. ❌ **No collision checking** - SHA256/UUID collisions not detected
5. ❌ **No versions table updates** - Schema version tracking not implemented
6. ❌ **Web interface doesn't match spec** - Missing auto-fill, URL support, film metadata

---

## Detailed Comparison

### Feature Matrix

| Feature | Spec Requirement | db_import.py | web_interface.py | Status |
|---------|-----------------|--------------|------------------|--------|
| **Import Modes** | | | | |
| Mobile web import | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Desktop web import | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Hardlink for same disk | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Scan existing database | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| **Workflow Steps** | | | | |
| Load database config | ✓ Required | ✅ Implemented | ✅ Implemented | **OK** |
| Call backup | ✓ Required | ❌ Not called | ❌ Not called | **MISSING** |
| Generate UUID | ✓ Required | ✅ Implemented | ✅ Implemented | **OK** |
| Create UUID8 folder | ✓ Required | ✅ Implemented | ❌ Not visible | **PARTIAL** |
| Import/copy files | ✓ Required | ✅ Files copied | ❌ Not implemented | **PARTIAL** |
| Determine media types | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Log to database | ✓ Required | ⚠️ Location only | ⚠️ Location only | **INCOMPLETE** |
| Generate SHA256/UUIDs | ✓ Required | ✅ SHA256 only | ❌ Not implemented | **PARTIAL** |
| Update versions table | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Check import match count | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| **Database Operations** | | | | |
| Insert location record | ✓ Required | ✅ Implemented | ❌ Not implemented | **PARTIAL** |
| Insert image records | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Insert video records | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Insert document records | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Insert URL records | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Collision check (SHA256) | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Collision check (UUID) | ✓ Required | ✅ Implemented | ❌ Not implemented | **PARTIAL** |
| Collision check (location name) | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| **Web Interface Features** | | | | |
| Location name input | ✓ Required | ✅ Interactive | ✅ Form field | **OK** |
| Collision check on name | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Auto-fill from database | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Type selection | ✓ Required | ✅ Manual input | ✅ Dropdown | **PARTIAL** |
| Type auto-fill | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Sub-type input | ✓ Required | ✅ Manual input | ✅ Text field | **PARTIAL** |
| Sub-type auto-fill by type | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| State input | ✓ Required | ✅ Manual input | ✅ Text field | **PARTIAL** |
| State auto-fill | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Most popular state default | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Author input | ✓ Required | ✅ Manual input | ✅ Text field | **PARTIAL** |
| Author auto-fill | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Most popular author default | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| **Media Upload** | | | | |
| Images/videos upload | ✓ Required | ✅ Via --source | ❌ Not implemented | **PARTIAL** |
| Documents upload | ✓ Required | ✅ Via --source | ❌ Not implemented | **PARTIAL** |
| Web URLs input | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Film stock metadata | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| SHA256 collision check | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| **Update Existing Location** | | | | |
| Search location | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |
| Add media to existing | ✓ Required | ❌ Not implemented | ❌ Not implemented | **MISSING** |

---

## Critical Missing Functionality

### 1. Media Database Records Not Created
**Problem:** The current `db_import.py` only creates a location record and copies files to staging. It does **not** create database records in the `images`, `videos`, `documents`, or `live_videos` tables.

**Evidence:**
```python
# From db_import.py:254-330
# Only creates location record:
create_location_record(config['db_loc'], location_data)

# Copies files to staging:
import_media_files(args.source, config.get('db_ingest', ''), ...)

# BUT: import_media_files() does NOT insert into media tables!
# It only copies files and calculates SHA256
```

**Impact:**
- Files exist in staging but are invisible to the database
- `db_organize.py` expects media records to exist (line 184, 269)
- Workflow breaks at organize step
- No media can be found, organized, or ingested

**Required Fix:**
Add database insertion logic to `import_media_files()` function:
```python
# Determine file type based on extension
file_type = determine_file_type(ext)  # NEW FUNCTION NEEDED

if file_type == 'image':
    cursor.execute("INSERT INTO images (img_sha256, img_name, img_loc, ...) VALUES (...)")
elif file_type == 'video':
    cursor.execute("INSERT INTO videos (vid_sha256, vid_name, vid_loc, ...) VALUES (...)")
elif file_type == 'document':
    cursor.execute("INSERT INTO documents (doc_sha256, doc_name, doc_loc, ...) VALUES (...)")
```

### 2. No File Type Detection
**Problem:** No function exists to classify files as images, videos, or documents based on file extension.

**Evidence:**
- No `IMAGE_EXTENSIONS`, `VIDEO_EXTENSIONS`, `DOCUMENT_EXTENSIONS` constants defined
- No `determine_file_type()` function in utils.py or normalize.py
- Files are copied with no categorization

**Impact:**
- Cannot determine which database table to use (images/videos/documents)
- All files treated identically
- No way to separate media types

**Required Fix:**
Create file type detection in `utils.py`:
```python
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.heic', '.raw', '.dng', ...}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', ...}
DOCUMENT_EXTENSIONS = {'.pdf', '.srt', '.xml', ...}

def determine_file_type(extension: str) -> str:
    ext = extension.lower()
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    elif ext in VIDEO_EXTENSIONS:
        return 'video'
    elif ext in DOCUMENT_EXTENSIONS:
        return 'document'
    else:
        return 'other'
```

### 3. No Backup Before Import
**Problem:** Specification requires calling `backup.py` before import, but this is not implemented.

**Evidence:**
```markdown
# From db_import.md:12
- call [[backup]]
```

**Current:** No backup call in `db_import.py`

**Impact:**
- No recovery if import fails
- No snapshot before database modification
- Violates spec safety requirement

**Required Fix:**
```python
# In db_import.py main():
logger.info("Creating backup before import...")
backup_result = subprocess.run([sys.executable, 'scripts/backup.py', '--config', args.config])
if backup_result.returncode != 0:
    logger.error("Backup failed - aborting import")
    return 1
```

### 4. No Collision Checking
**Problem:** SHA256 hash collisions are not detected during import. Files with duplicate hashes should be rejected.

**Evidence:**
- `import_media_files()` calculates SHA256 but doesn't check if it exists in database
- No query like `SELECT img_sha256 FROM images WHERE img_sha256 = ?`

**Impact:**
- Duplicate files imported multiple times
- Storage waste
- Database integrity issues

**Required Fix:**
```python
# Check for existing SHA256 before inserting
cursor.execute("SELECT img_sha256 FROM images WHERE img_sha256 = ?", (sha256,))
if cursor.fetchone():
    logger.warning(f"Duplicate file detected: {file_path.name} ({sha8})")
    stats['duplicates'] += 1
    continue  # Skip this file
```

### 5. No Versions Table Updates
**Problem:** Specification requires updating the `versions` table to track schema and import versions, but this is not implemented.

**Evidence:**
```markdown
# From db_import.md:21
- update versions table
```

**Current:** No code in `db_import.py` that touches `versions` table

**Impact:**
- No tracking of when imports occurred
- No schema version tracking
- Cannot audit import history

**Required Fix:**
```python
# After successful import
cursor.execute(
    "INSERT INTO versions (version_type, version_number, description, date_applied) VALUES (?, ?, ?, ?)",
    ('import', '1.0.0', f'Imported location {loc_uuid}', normalize_datetime(None))
)
```

### 6. Web Interface Incomplete
**Problem:** The web interface doesn't support many spec features.

**Missing from web_interface.py:**
- ❌ Auto-fill suggestions based on existing database data
- ❌ Most popular state/author defaults
- ❌ File upload handling (only directory path input)
- ❌ Web URL input
- ❌ Film stock metadata
- ❌ Update existing location mode
- ❌ Location name collision warnings

**Impact:**
- Poor user experience
- Manual typing required for repeated values
- No way to add URLs
- No film photography support

### 7. No Hardlink Support
**Problem:** Specification says desktop imports should use hardlinks if on same disk, but only copy is implemented.

**Evidence:**
```markdown
# From db_import.md:16-17
- if desktop web import
  - if images are on same disk/system hardlink images, if not files images into ingest folder
```

**Current:** `shutil.copy2()` always used (line 192 of db_import.py)

**Impact:**
- Storage waste for large media libraries
- Slower imports
- Unnecessary I/O

**Required Fix:**
```python
# Check if same filesystem
if source_path.stat().st_dev == loc_staging.stat().st_dev:
    # Same disk - use hardlink
    os.link(file_path, staging_file)
    logger.info(f"Hardlinked: {file_path.name}")
else:
    # Different disk - copy
    shutil.copy2(file_path, staging_file)
    logger.info(f"Copied: {file_path.name}")
```

---

## What Actually Works

### ✅ Implemented Features

1. **UUID Generation** - Properly generates UUIDs with collision detection
2. **Location Record Creation** - Creates database records in `locations` table
3. **SHA256 Hashing** - Correctly calculates file hashes
4. **File Copying to Staging** - Files are copied to UUID8 subfolder
5. **Normalization Functions** - Location name, state, type normalization working
6. **Interactive CLI Input** - Prompts for location details
7. **Basic Web Dashboard** - Shows database statistics
8. **Configuration Loading** - user.json properly loaded

### ⚠️ Partially Implemented

1. **Import Workflow** - Copies files but doesn't create media records
2. **Web Interface** - Basic form exists but missing most features
3. **Collision Detection** - UUID checked, but SHA256 not checked

---

## Comparison to db_organize.py

**Important:** `db_organize.py` assumes media records already exist!

```python
# From db_organize.py:183-186
cursor.execute(
    "SELECT img_sha256, img_loc, img_loco FROM images WHERE camera IS NULL"
)
images = cursor.fetchall()
```

This query will return **zero results** because `db_import.py` never inserted any image records!

**The workflow is broken between import and organize steps.**

---

## Recommended Implementation Priority

### P0 - Critical (Workflow Blockers)
1. **Add file type detection** - `determine_file_type()` function in utils.py
2. **Insert media database records** - Modify `import_media_files()` to INSERT into images/videos/documents tables
3. **Add SHA256 collision checking** - Query before insert to detect duplicates
4. **Call backup before import** - Integrate backup.py into import workflow

### P1 - High Priority (Spec Compliance)
5. **Update versions table** - Track import operations
6. **Add match count verification** - Verify all files were processed
7. **Implement hardlink support** - Use hardlinks for same-disk imports
8. **Add location name collision check** - Warn if location already exists

### P2 - Medium Priority (User Experience)
9. **Web interface auto-fill** - Query database for suggestions
10. **Web interface file upload** - Accept file uploads, not just directory paths
11. **Default most popular values** - State, author defaults from database
12. **Update existing location mode** - Add media to existing locations

### P3 - Nice to Have
13. **Web URL support** - Input and store URLs in urls table
14. **Film stock metadata** - Special handling for film photography
15. **Mobile vs desktop detection** - Different behavior for mobile/desktop
16. **Progress bars** - Visual feedback during long imports

---

## Code Changes Required

### 1. Add to `scripts/utils.py`

```python
# File type detection
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.heic', '.heif', '.webp', '.raw', '.cr2', '.nef', '.dng',
    '.arw', '.orf', '.rw2', '.pef', '.srw'
}

VIDEO_EXTENSIONS = {
    '.mp4', '.mov', '.avi', '.mkv', '.m4v', '.mpg', '.mpeg',
    '.wmv', '.flv', '.webm', '.3gp', '.mts', '.m2ts'
}

DOCUMENT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.rtf',
    '.srt', '.xml', '.json'
}

def determine_file_type(extension: str) -> str:
    """Determine file type based on extension."""
    ext = extension.lower().lstrip('.')
    ext_with_dot = f'.{ext}'

    if ext_with_dot in IMAGE_EXTENSIONS:
        return 'image'
    elif ext_with_dot in VIDEO_EXTENSIONS:
        return 'video'
    elif ext_with_dot in DOCUMENT_EXTENSIONS:
        return 'document'
    else:
        return 'other'

def check_sha256_collision(cursor, sha256: str, table: str) -> bool:
    """Check if SHA256 already exists in specified table."""
    sha_field = f"{table[:-1]}_sha256"  # images -> img_sha256
    cursor.execute(f"SELECT {sha_field} FROM {table} WHERE {sha_field} = ?", (sha256,))
    return cursor.fetchone() is not None
```

### 2. Modify `scripts/db_import.py`

```python
def import_media_files(source_dir: str, staging_dir: str, db_path: str, loc_uuid: str, imp_author: str) -> dict:
    """Import media files and create database records."""

    # ... existing setup code ...

    for file_path in files:
        try:
            sha256 = calculate_sha256(str(file_path))
            ext = normalize_extension(file_path.suffix)
            file_type = determine_file_type(ext)  # NEW

            # Skip unknown file types
            if file_type == 'other':
                logger.warning(f"Unknown file type, skipping: {file_path.name}")
                stats['errors'] += 1
                continue

            # Check for collision
            if file_type == 'image':
                table = 'images'
                sha_field = 'img_sha256'
            elif file_type == 'video':
                table = 'videos'
                sha_field = 'vid_sha256'
            elif file_type == 'document':
                table = 'documents'
                sha_field = 'doc_sha256'

            # Collision check
            cursor.execute(f"SELECT {sha_field} FROM {table} WHERE {sha_field} = ?", (sha256,))
            if cursor.fetchone():
                logger.warning(f"Duplicate detected: {file_path.name}")
                stats['duplicates'] += 1
                continue

            # Copy or hardlink file
            staging_file = loc_staging / file_path.name
            if source_path.stat().st_dev == loc_staging.stat().st_dev:
                os.link(file_path, staging_file)
            else:
                shutil.copy2(file_path, staging_file)

            # Generate standardized filename
            new_filename = generate_filename(
                media_type='img' if file_type == 'image' else 'vid' if file_type == 'video' else 'doc',
                loc_uuid=loc_uuid,
                sha256=sha256,
                extension=ext
            )

            # Insert into appropriate table
            timestamp = normalize_datetime(None)

            if file_type == 'image':
                cursor.execute(
                    """
                    INSERT INTO images (
                        img_sha256, img_name, img_loc, loc_uuid,
                        img_loco, img_nameo, img_add, imp_author
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sha256, new_filename, str(staging_file), loc_uuid,
                     str(file_path.parent), file_path.name, timestamp, imp_author)
                )
                stats['images'] += 1

            elif file_type == 'video':
                cursor.execute(
                    """
                    INSERT INTO videos (
                        vid_sha256, vid_name, vid_loc, loc_uuid,
                        vid_loco, vid_nameo, vid_add, imp_author
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sha256, new_filename, str(staging_file), loc_uuid,
                     str(file_path.parent), file_path.name, timestamp, imp_author)
                )
                stats['videos'] += 1

            elif file_type == 'document':
                cursor.execute(
                    """
                    INSERT INTO documents (
                        doc_sha256, doc_name, doc_loc, doc_ext, loc_uuid,
                        doc_loco, doc_nameo, doc_add, imp_author
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sha256, new_filename, str(staging_file), ext, loc_uuid,
                     str(file_path.parent), file_path.name, timestamp, imp_author)
                )
                stats['documents'] += 1

            stats['total'] += 1
            logger.info(f"Imported {file_type}: {file_path.name}")

        except Exception as e:
            logger.error(f"Failed to import {file_path.name}: {e}")
            stats['errors'] += 1

    # Update versions table
    cursor.execute(
        """
        INSERT INTO versions (version_type, version_number, description, date_applied)
        VALUES (?, ?, ?, ?)
        """,
        ('import', '1.0.0', f'Import for location {loc_uuid[:8]}', timestamp)
    )

    conn.commit()
    return stats
```

### 3. Add Backup to Import Workflow

```python
# In db_import.py main(), before import:
def main():
    # ... existing code ...

    # Create backup before import
    logger.info("Creating database backup...")
    backup_script = Path(__file__).parent / 'backup.py'
    backup_result = subprocess.run(
        [sys.executable, str(backup_script), '--config', args.config or 'user/user.json'],
        capture_output=True
    )

    if backup_result.returncode != 0:
        logger.error("Backup failed - aborting import for safety")
        logger.error(backup_result.stderr.decode())
        return 1

    logger.info("Backup completed successfully")

    # ... continue with import ...
```

---

## Testing Checklist

After implementing fixes, test the following:

### Import Workflow Tests
- [ ] Import location with mixed media (images, videos, documents)
- [ ] Verify all files get database records
- [ ] Check file type detection is correct
- [ ] Verify SHA256 collision detection works
- [ ] Confirm backup is created before import
- [ ] Verify versions table is updated
- [ ] Check hardlinks used when on same disk
- [ ] Verify copies used when on different disk

### Database Integrity Tests
- [ ] Confirm no duplicate SHA256 hashes
- [ ] Verify foreign key constraints work
- [ ] Check all timestamps are ISO 8601
- [ ] Confirm location collision warnings

### Web Interface Tests
- [ ] Test location import form
- [ ] Verify normalization works on form input
- [ ] Check dashboard shows correct statistics
- [ ] Test workflow execution from web

### Integration Tests
- [ ] Run complete workflow: import → organize → folder → ingest
- [ ] Verify db_organize finds all media records
- [ ] Check db_folder creates correct structure
- [ ] Confirm db_ingest moves files properly

---

## Summary

**The current implementation is incomplete.** While the foundation is solid (UUID generation, normalization, basic import), the critical piece—creating database records for media files—is missing. This breaks the entire workflow.

**Immediate Action Required:**
1. Implement file type detection
2. Add database insertion for images/videos/documents
3. Add collision checking
4. Integrate backup call

**Estimated Effort:**
- P0 fixes: 4-6 hours
- P1 fixes: 2-3 hours
- P2 fixes: 4-5 hours
- P3 fixes: 3-4 hours

**Total: ~15-20 hours of development work**

Once P0 fixes are complete, the workflow will be functional and users can successfully import media into AUPAT.
