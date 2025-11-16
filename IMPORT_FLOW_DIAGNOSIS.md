# AUPAT Import Flow - Complete Diagnosis

## Issue Summary

User reports: "Images are not being imported into the database" and "archive folder is blank"

## Root Cause Analysis

### Critical Understanding: The Import Pipeline Has Multiple Stages

The AUPAT import process is **NOT a single step**. It's a multi-stage pipeline:

```
1. db_import.py    → Import to STAGING/INGEST folder + create DB records
2. db_organize.py  → Extract metadata (EXIF, hardware detection)
3. db_folder.py    → Create organized folder structure in archive
4. db_ingest.py    → MOVE files from staging to ARCHIVE
5. db_verify.py    → Verify integrity and cleanup staging
6. db_identify.py  → Generate JSON exports
```

**The web interface currently only runs step 1 (db_import.py)**

This means:
- Files ARE imported to the staging/ingest directory
- Files ARE added to the database
- Files are NOT yet in the archive (requires steps 3-4)
- Metadata is NOT yet extracted (requires step 2)

## What Actually Happens During Web Import

### Step-by-Step Breakdown

1. **User uploads files** (e.g., 15x NEF files)
   - Files saved to temporary directory: `/tmp/aupat_import_XXXXX/`
   - metadata.json created in same directory

2. **Database migration runs**
   - Ensures schema is up-to-date
   - Creates/updates all tables

3. **db_import.py is called** via subprocess:
   ```bash
   python scripts/db_import.py \
     --source /tmp/aupat_import_XXXXX/ \
     --config user/user.json \
     --metadata /tmp/aupat_import_XXXXX/metadata.json \
     --skip-backup
   ```

4. **db_import.py processes files**:
   - Reads metadata from metadata.json
   - Creates location record in `locations` table
   - For each file in source directory:
     - Calculate SHA256 hash
     - Check for duplicates (SHA256 collision)
     - Determine file type (image/video/document)
     - Generate standardized filename: `{loc_uuid8}-{media_type}_{sha8}.ext`
     - Copy or hardlink file to staging: `{db_ingest}/{loc_uuid8}/`
     - Insert record into appropriate table (images/videos/documents)
   - Updates versions table
   - Commits transaction

5. **Temporary directory cleaned up**
   - Original uploads deleted
   - Only staged files remain in `{db_ingest}/{loc_uuid8}/`

## Expected Results After Web Import

### Database

Location record exists:
```sql
SELECT * FROM locations WHERE loc_name = 'St. Peter & Paul Catholic Church';
```

Image records exist:
```sql
SELECT img_name, img_loc FROM images WHERE loc_uuid = '{uuid}';
```

### File System

Files in staging/ingest:
```
{db_ingest}/
  {loc_uuid8}/
    {loc_uuid8}-img_{sha8}.nef
    {loc_uuid8}-img_{sha8}.nef
    ...
```

Files NOT yet in archive:
```
{arch_loc}/
  (empty - nothing moved yet)
```

## Diagnostic Steps

### 1. Run the diagnostic script

```bash
python check_import_status.py
```

This will show:
- Number of locations in database
- Number of images/videos/documents in database
- Files in staging/ingest folder
- Files in archive folder (should be empty after import)
- Clear diagnosis and next steps

### 2. Check the database directly

```bash
sqlite3 {db_loc} "SELECT COUNT(*) FROM locations;"
sqlite3 {db_loc} "SELECT COUNT(*) FROM images;"
sqlite3 {db_loc} "SELECT COUNT(*) FROM videos;"
```

### 3. Check staging folder

```bash
ls -la {db_ingest}/
```

Should see UUID8 folders with imported files.

### 4. Check import logs

Look for these log patterns:

**Successful import**:
```
INFO - ✓ Imported image: DSC8845.NEF -> {uuid8}-img_{sha8}.nef ({sha8})
INFO - ✓ Imported image: DSC8855.NEF -> {uuid8}-img_{sha8}.nef ({sha8})
...
INFO - ✓ Match count verified: 15 files imported
INFO - ✓ IMPORT SUCCESSFUL
```

**Failed import** (no files processed):
```
INFO - Found 0 files to process
```
OR
```
INFO - Skipped: 15 files (unknown type)
```

**Silent failure**:
- Import completes in < 1 second
- No file processing logs
- "Import completed successfully" but no files in database

## Common Failure Modes

### 1. Files Not Recognized

**Symptom**: All files skipped, `stats['skipped']` = 15

**Cause**: File extensions not in IMAGE_EXTENSIONS/VIDEO_EXTENSIONS/DOCUMENT_EXTENSIONS

**Fix**: Add extensions to utils.py or convert files to supported format

**Verify**: NEF is already supported (line 254 in utils.py)

### 2. Silent Subprocess Failure

**Symptom**: Import completes instantly, no logs, return code 0

**Possible causes**:
- Exception in db_import.py caught and suppressed
- Early return without error
- stdout/stderr not being captured correctly

**Fix**: Run db_import.py directly to see full output:
```bash
python scripts/db_import.py \
  --source /path/to/test/files \
  --config user/user.json \
  --metadata /path/to/metadata.json \
  -v
```

### 3. Database Schema Missing

**Symptom**: "no such table: images" error

**Cause**: Migration didn't run or failed

**Fix**: Run db_migrate.py manually

### 4. Path Configuration Issues

**Symptom**: "unable to open database" or "directory does not exist"

**Cause**: Invalid paths in user/user.json

**Fix**: Verify all paths in user.json:
```json
{
  "db_loc": "/absolute/path/to/database/aupat.db",  // FILE path
  "db_ingest": "/absolute/path/to/ingest/",          // DIRECTORY path
  "arch_loc": "/absolute/path/to/archive/"           // DIRECTORY path
}
```

### 5. Permission Issues

**Symptom**: "Permission denied" errors

**Cause**: Web server doesn't have write access

**Fix**: Ensure all paths are writable by the process running web_interface.py

## Next Steps After Successful Import

Once files are confirmed in database and staging:

### 1. Extract Metadata

```bash
python scripts/db_organize.py --config user/user.json
```

This will:
- Run exiftool on images to extract EXIF
- Run ffprobe on videos to extract metadata
- Detect camera hardware (DSLR/Phone/Drone/GoPro/Film)
- Detect video hardware (Camera/Phone/Drone/GoPro/Dashcam)
- Match live photos (image/video pairs)
- Update hardware flags in database

### 2. Create Archive Structure

```bash
python scripts/db_folder.py --config user/user.json
```

This will:
- Create folder structure in archive:
  ```
  {arch_loc}/
    {state}-{type}/
      {location_name}_{uuid8}/
        photos/
          original_camera/
          original_phone/
          original_drone/
          ...
        videos/
          original_camera/
          ...
        documents/
          ...
  ```

### 3. Move Files to Archive

```bash
python scripts/db_ingest.py --config user/user.json
```

This will:
- Move files from staging to archive
- Organize by hardware type
- Update `loc_loc` paths in database
- Preserve file integrity (verify SHA256)

### 4. Verify and Cleanup

```bash
python scripts/db_verify.py --config user/user.json
```

This will:
- Verify SHA256 of all files in archive
- Verify database records match files
- Clean up staging directory
- Report any integrity issues

## Web Interface Enhancement Needed

The web interface should be enhanced to:

1. **Show import pipeline status**
   - Step 1/6: Importing files to staging
   - Step 2/6: Extracting metadata
   - Step 3/6: Creating folder structure
   - Step 4/6: Moving to archive
   - Step 5/6: Verifying integrity
   - Step 6/6: Generating exports

2. **Run full pipeline automatically**
   - Currently only runs db_import.py
   - Should run all 6 steps sequentially
   - Update progress bar for each step

3. **Better error reporting**
   - Capture and display full subprocess output
   - Show which files failed and why
   - Display validation errors clearly

4. **Import summary**
   - Show final file locations in archive
   - Display metadata extracted
   - Link to location detail page

## Testing Checklist

To verify import is working correctly:

- [ ] Run check_import_status.py - shows files in database
- [ ] Check staging folder - has UUID8 folders with files
- [ ] Query database - location and images records exist
- [ ] File count matches - uploaded 15 files, database has 15 records
- [ ] File paths are correct - img_loc points to staging folder
- [ ] SHA256 hashes calculated - not null in database
- [ ] Filenames standardized - match pattern `{uuid8}-img_{sha8}.ext`
- [ ] Duplicate detection works - upload same file twice, only imports once
- [ ] Web interface shows location in /locations page
- [ ] Location detail page shows all files
- [ ] Archive folder empty until db_ingest.py runs
- [ ] After db_ingest.py, files moved to archive with proper organization

## Conclusion

The most likely scenario is:

**Import IS working correctly** - files are in database and staging folder, but user expects them to be in archive folder immediately. The archive requires running the additional pipeline steps (db_organize, db_folder, db_ingest).

To confirm:
1. Run `python check_import_status.py`
2. Check if files exist in staging/ingest folder
3. Check if database has location and image records

If files are in staging and database, the solution is to complete the pipeline. If not, there's a deeper issue with the import process itself.
