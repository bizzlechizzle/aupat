# Implementation Guide: Fix db_import.py NULL Constraint Bug

## For: Less Experienced Coder
## Priority: P0 Critical
## Estimated Time: 15 minutes
## Complexity: Simple (3 line changes)

---

## What This Guide Does

This guide walks you through fixing a critical bug in the AUPAT import pipeline that prevents any files from being imported. The bug causes a database constraint violation because the code tries to insert NULL values into columns that require data.

By following this guide, you'll:
1. Understand why the bug exists
2. Learn how to fix it correctly
3. Test that the fix works
4. Understand the core logic behind file location tracking

---

## Prerequisites

Before starting, make sure you have:
- [ ] Read TEST_IMPORT_RESULTS.md (understand the bug)
- [ ] Read data/images.json (understand the schema)
- [ ] Basic understanding of SQL NOT NULL constraints
- [ ] Text editor installed (nano, vim, or VS Code)

---

## The Problem (In Simple Terms)

### What's Happening

When you try to import photos into AUPAT, the system crashes with this error:

```
ERROR - Failed to import _DSC1834.NEF: NOT NULL constraint failed: images.img_loc
```

### Why It's Happening

The database has a rule: "Every image MUST have a location (img_loc)". You can't leave it blank.

But the import script (db_import.py) is trying to insert records with img_loc set to `None` (NULL in SQL), which breaks this rule.

Think of it like a form where "Address" is required - you can't submit it blank.

### Why The Code Was Written This Way (The Intent)

The original coder thought:
- During import: files go to staging folder
- During ingest: files move to archive folder
- "I'll set img_loc to NULL during import, then fill it in during ingest"

**BUT**: The database schema says img_loc must NEVER be NULL. The coder misunderstood the design.

### The Correct Design

`img_loc` should ALWAYS point to where the file currently is:
- **During import:** img_loc = staging folder location
- **During ingest:** img_loc = archive folder location (updated)

A *different* field (`img_loco`) stores the original location before import.

---

## The Fix (Step by Step)

### Step 1: Open the File

```bash
cd /home/user/aupat
nano scripts/db_import.py
```

Or use your preferred editor:
```bash
vim scripts/db_import.py
# or
code scripts/db_import.py
```

### Step 2: Find the First Bug (Images)

Press Ctrl+W (nano) or / (vim) and search for:
```
img_loc stays NULL
```

You'll find this code around line 425:

```python
INSERT INTO images (
    img_sha256, img_name, img_loc, loc_uuid,
    img_loco, img_nameo, img_add, img_update, imp_author
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
(
    sha256,
    new_filename,
    None,  # img_loc stays NULL until ingest moves to archive
    loc_uuid,
    str(staging_file),  # img_loco now points to staging location
    orig_name,
    timestamp,
    timestamp,
    imp_author
)
```

### Step 3: Fix the Images Bug

**BEFORE:**
```python
None,  # img_loc stays NULL until ingest moves to archive
```

**AFTER:**
```python
str(staging_file),  # img_loc points to staging until ingest moves to archive
```

**What Changed:**
- `None` → `str(staging_file)`
- Now img_loc points to where the file actually is (in staging)

**Why:** img_loc must always be filled in. It tracks the current file location, which is initially the staging folder.

### Step 4: Find the Second Bug (Videos)

Search for:
```
vid_loc stays NULL
```

You'll find similar code around line 448:

```python
INSERT INTO videos (
    vid_sha256, vid_name, vid_loc, loc_uuid,
    vid_loco, vid_nameo, vid_add, vid_update, imp_author
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
(
    sha256,
    new_filename,
    None,  # vid_loc stays NULL until ingest moves to archive
    loc_uuid,
    str(staging_file),  # vid_loco now points to staging location
    orig_name,
    timestamp,
    timestamp,
    imp_author
)
```

### Step 5: Fix the Videos Bug

**BEFORE:**
```python
None,  # vid_loc stays NULL until ingest moves to archive
```

**AFTER:**
```python
str(staging_file),  # vid_loc points to staging until ingest moves to archive
```

### Step 6: Find the Third Bug (Documents)

Search for:
```
doc_loc stays NULL
```

You'll find similar code around line 471:

```python
INSERT INTO documents (
    doc_sha256, doc_name, doc_loc, doc_ext, loc_uuid,
    doc_loco, doc_nameo, doc_add, doc_update, imp_author
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
(
    sha256,
    new_filename,
    None,  # doc_loc stays NULL until ingest moves to archive
    ext,
    loc_uuid,
    str(staging_file),  # doc_loco now points to staging location
    orig_name,
    timestamp,
    timestamp,
    imp_author
)
```

### Step 7: Fix the Documents Bug

**BEFORE:**
```python
None,  # doc_loc stays NULL until ingest moves to archive
```

**AFTER:**
```python
str(staging_file),  # doc_loc points to staging until ingest moves to archive
```

### Step 8: Save the File

**In nano:**
- Press Ctrl+O (WriteOut)
- Press Enter to confirm
- Press Ctrl+X to exit

**In vim:**
- Press Esc
- Type `:wq` and press Enter

**In VS Code:**
- Press Ctrl+S (or Cmd+S on Mac)

---

## Understanding the Core Logic

### File Location Tracking (The Key Concept)

AUPAT tracks THREE location values for each file:

1. **Original location** (`img_loco`): Where the file was before import
   - Example: `/Users/bryant/Desktop/Photos/IMG_1234.JPG`
   - Set once during import, never changes
   - Can be NULL (if unknown)

2. **Current location** (`img_loc`): Where the file is RIGHT NOW
   - During import: `/home/user/aupat/data/ingest/573c02b2/IMG_1234.JPG`
   - After ingest: `/archive/ny-institutional/Middletown_573c02b2/photos/original_camera/573c02b2-img_a1b2c3d4.NEF`
   - Updated as file moves through pipeline
   - MUST NEVER be NULL (always points to current location)

3. **Archive location** (not a separate field, but the final value of `img_loc`)
   - The permanent home after import completes

### Data Flow Example

**Step 1: User has photo**
```
Location: /home/user/Photos/Vacation/IMG_1234.JPG
Database: (not in database yet)
```

**Step 2: Import runs (db_import.py)**
```
File copied/hardlinked to: /home/user/aupat/data/ingest/573c02b2/IMG_1234.JPG
Database record created:
  - img_loco = "/home/user/Photos/Vacation"  (original)
  - img_nameo = "IMG_1234.JPG"              (original name)
  - img_loc = "/home/user/aupat/data/ingest/573c02b2/IMG_1234.JPG"  (current - in staging)
  - img_name = "IMG_1234.JPG"               (current name, not renamed yet)
```

**Step 3: Organize runs (db_organize.py)**
```
File location unchanged (still in staging)
Database updated with metadata:
  - img_hardware = {"make": "Nikon", "model": "D850", "category": "DSLR"}
  - camera = 1  (boolean flag set)
```

**Step 4: Folder creation runs (db_folder.py)**
```
Creates: /archive/ny-institutional/Middletown_573c02b2/photos/original_camera/
File still in staging (not moved yet)
```

**Step 5: Ingest runs (db_ingest.py)**
```
File moved to: /archive/ny-institutional/Middletown_573c02b2/photos/original_camera/573c02b2-img_a1b2c3d4.NEF
Database updated:
  - img_loc = "/archive/ny-institutional/Middletown_573c02b2/photos/original_camera/573c02b2-img_a1b2c3d4.NEF"
  - img_name = "573c02b2-img_a1b2c3d4.NEF"
```

**Step 6: Verify runs (db_verify.py)**
```
Calculates SHA256 of file at img_loc
Compares to img_sha256 in database
If match: deletes staging folder
If mismatch: ERROR, keeps staging for recovery
```

### Why This Design Works

**Data Integrity:**
- img_loc always points to real file
- Can find file at any stage of pipeline
- If import fails, img_loc points to staging for recovery
- If ingest fails, img_loc points to staging, file not lost

**Audit Trail:**
- img_loco preserves original location
- Can trace file back to source
- Can re-import if needed

**Transaction Safety:**
- File exists in database? Then file exists on disk (at img_loc)
- No orphaned database records
- No orphaned files

---

## Testing the Fix

### Step 1: Clean Up Previous Test

```bash
cd /home/user/aupat

# Remove failed test data
rm -rf data/ingest/*
rm test_metadata.json

# Reset database (optional - start fresh)
rm data/aupat.db
source venv/bin/activate
python3 scripts/db_migrate.py
```

### Step 2: Create Test Metadata

```bash
cat > test_metadata.json << 'EOF'
{
  "loc_name": "Middletown State Hospital",
  "aka_name": "Middletown Psychiatric Center",
  "state": "ny",
  "type": "institutional",
  "sub_type": "healthcare",
  "address": "Middletown NY"
}
EOF
```

### Step 3: Run Test Import

```bash
source venv/bin/activate
python3 scripts/db_import.py --source "tempdata/testphotos/Middletown State Hospital" --metadata test_metadata.json
```

### Step 4: Check for Success

**Expected Output:**
```
============================================================
Import Summary
============================================================
Location: Middletown State Hospital
UUID: [some UUID]

Files processed: 9
Files imported: 8
  - Images: 8
  - Videos: 0
  - Documents: 0

Duplicates skipped: 0
Unknown types skipped: 0
Errors: 0

Transfer method:
  - Hardlinked: 8
  - Copied: 0
============================================================
✓ Import completed successfully
```

**Key Success Indicators:**
- "Errors: 0" (not "Errors: 8")
- "Files imported: 8" (not "Files imported: 0")
- "✓ Import completed successfully" (not "⚠ Import completed with errors")

### Step 5: Verify Database

```bash
sqlite3 data/aupat.db "SELECT img_name, img_loc, img_loco FROM images LIMIT 3;"
```

**Expected Output:**
```
_DSC1828.NEF|/home/user/aupat/data/ingest/[UUID]/Original - Photo/_DSC1828.NEF|tempdata/testphotos/Middletown State Hospital/Original - Photo
_DSC1831.NEF|/home/user/aupat/data/ingest/[UUID]/Original - Photo/_DSC1831.NEF|tempdata/testphotos/Middletown State Hospital/Original - Photo
_DSC1834.NEF|/home/user/aupat/data/ingest/[UUID]/Original - Photo/_DSC1834.NEF|tempdata/testphotos/Middletown State Hospital/Original - Photo
```

**Check:**
- img_loc is NOT NULL (second column has a path)
- img_loc points to staging (contains `/data/ingest/`)
- img_loco has original path (contains `/tempdata/testphotos/`)

### Step 6: Test Complete Workflow

```bash
./run_workflow.py --source "tempdata/testphotos/Middletown State Hospital" --backup
```

**Expected:** All 7 steps complete successfully with no errors

---

## Common Mistakes to Avoid

### Mistake 1: Only Fixing One of the Three Bugs

**Wrong:**
```python
# Only fixed images, forgot videos and documents
```

**Right:**
```python
# Fixed all three: images (line 425), videos (line 448), documents (line 471)
```

### Mistake 2: Using staging_file Instead of str(staging_file)

**Wrong:**
```python
staging_file,  # This is a Path object, not a string
```

**Right:**
```python
str(staging_file),  # Convert Path to string for database
```

**Why:** SQLite TEXT columns need strings, not Path objects. Path objects will cause type errors.

### Mistake 3: Confusing img_loc with img_loco

**Wrong:**
```python
str(file_path),  # This is the ORIGINAL path, not staging
```

**Right:**
```python
str(staging_file),  # This is the CURRENT path in staging
```

**Why:**
- img_loc = CURRENT location (where file is NOW)
- img_loco = ORIGINAL location (where file WAS)

### Mistake 4: Not Testing After Changes

**Wrong:**
```
Make changes → Commit to git → Done
```

**Right:**
```
Make changes → Test import → Verify database → Commit to git
```

**Why:** Code might have syntax errors, logic errors, or other bugs. Always test before committing.

---

## Verification Checklist

Before marking this task complete:

- [ ] All three bugs fixed (images, videos, documents)
- [ ] Used `str(staging_file)` not `None`
- [ ] Comments updated to reflect new behavior
- [ ] File saved
- [ ] Test import runs without errors
- [ ] Database query shows img_loc is not NULL
- [ ] Complete workflow runs successfully
- [ ] Changes committed to git with clear message

---

## Expected Results After Fix

### Before Fix
```
Files processed: 9
Files imported: 0
Errors: 8
⚠ Import completed with 8 errors
```

### After Fix
```
Files processed: 9
Files imported: 8
Errors: 0
✓ Import completed successfully
```

### Database Before Fix
```
sqlite3: Error: NOT NULL constraint failed: images.img_loc
```

### Database After Fix
```
img_name           img_loc                                                          img_loco
_DSC1828.NEF       /home/user/aupat/data/ingest/573c02b2/Original - Photo/_DSC...  tempdata/testphotos/...
_DSC1831.NEF       /home/user/aupat/data/ingest/573c02b2/Original - Photo/_DSC...  tempdata/testphotos/...
```

---

## What You Learned

By completing this fix, you now understand:

1. **Database Constraints:** NOT NULL means the field MUST have a value
2. **File Location Tracking:** Difference between current location (img_loc) and original location (img_loco)
3. **Data Integrity:** Why fields should track actual file locations at all times
4. **Testing:** How to verify database operations with SQL queries
5. **Code Comments:** Why inline comments should match actual behavior

---

## Next Steps

After this fix is complete and tested:

1. Run full workflow test with Water Slide World data (includes videos)
2. Document successful import in final test report
3. Commit changes to git
4. Update TEST_IMPORT_RESULTS.md with success
5. Mark bug as RESOLVED in project tracker

---

## Questions?

If you get stuck:

1. Re-read the "Core Logic" section (page 2)
2. Check TEST_IMPORT_RESULTS.md for the exact error
3. Compare your changes with the BEFORE/AFTER examples
4. Verify you fixed all three locations (not just one)
5. Check that you used `str(staging_file)` not `staging_file`

If still stuck, check:
- data/images.json (schema definition)
- project-overview.md page 1676 (import pipeline explanation)
- claude.md (troubleshooting workflow)

---

## Summary

**What:** Fix NULL constraint violation in db_import.py
**Where:** Lines 425, 448, 471
**Change:** `None` → `str(staging_file)`
**Why:** img_loc/vid_loc/doc_loc must always point to current file location
**Test:** Import succeeds with 0 errors, 8 files imported

**Simple:** 3 lines changed, bug fixed, import works.
