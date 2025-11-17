# AUPAT Large Upload Fix - Quick Reference Card

## One-Command Testing

```bash
# Validation tests (no dependencies)
python scripts/validation.py

# Unit tests (requires pytest)
pytest tests/test_validation.py -v

# E2E tests (requires Flask running)
bash tests/e2e_test.sh
```

---

## One-Command Deployment

```bash
# New installation
bash setup.sh && python scripts/db_migrate.py && python scripts/db_migrate_indices.py

# Existing installation (just add indices)
python scripts/db_migrate_indices.py
```

---

## Key Configuration Changes

| Setting | Location | Old Value | New Value |
|---------|----------|-----------|-----------|
| Upload limit | web_interface.py:75 | 16MB (default) | **10GB** |
| Request timeout | web_interface.py:80 | 30s (default) | **600s (10 min)** |
| Job timeout | web_interface.py:248 | Never | **7200s (2 hours)** |

---

## New Validation Functions

```python
from scripts.validation import (
    validate_location_name,   # "  Test  " → "Test"
    validate_state_code,       # "NY" → "ny"
    validate_file_size,        # Checks < 10GB
    validate_filename,         # Prevents path traversal
    validate_import_form_data  # Validates all fields at once
)

# Example usage
try:
    clean_name = validate_location_name(user_input)
except ValueError as e:
    return error_response(str(e))
```

---

## New Database Indices

Run once to add indices:
```bash
python scripts/db_migrate_indices.py
```

**Indices added**:
- `idx_images_sha256` - Fast duplicate detection
- `idx_videos_sha256` - Fast duplicate detection
- `idx_documents_sha256` - Fast duplicate detection
- `idx_images_loc_uuid` - Fast location queries
- `idx_videos_loc_uuid` - Fast location queries
- `idx_documents_loc_uuid` - Fast location queries
- `idx_images_hardware` - Fast hardware filtering
- `idx_videos_hardware` - Fast hardware filtering
- 2 composite indices for common queries

**Impact**: 10-100x faster queries on large databases

---

## Testing Cheat Sheet

### Before Committing

```bash
# 1. Syntax check
python -m py_compile $(find . -name "*.py")

# 2. Validation tests
python scripts/validation.py

# 3. Unit tests
pytest tests/test_validation.py -v
```

### Before Deploying

```bash
# 1. Start Flask
python web_interface.py &
sleep 3  # Wait for server

# 2. E2E tests
bash tests/e2e_test.sh

# 3. Kill Flask
pkill -f web_interface.py
```

---

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `user.json not found` | Setup not run | `bash setup.sh` |
| `ModuleNotFoundError: validation` | Python path | `export PYTHONPATH="./scripts:$PYTHONPATH"` |
| `Flask server is not running` | Server not started | `python web_interface.py` |
| `jq: command not found` | jq not installed | `sudo apt-get install jq` |
| `File too large: X.XGB (max 10GB)` | File exceeds limit | Split file or increase limit |

---

## File Size Limits

| File Type | Soft Limit | Hard Limit | Reason |
|-----------|------------|------------|--------|
| Images | 100MB | 10GB | RAW photos, TIFFs |
| Videos | 1GB | 10GB | 4K video files |
| Documents | 10MB | 10GB | Large PDFs |
| **Total Request** | - | **10GB** | Flask config |

To change limits, edit `web_interface.py:75`:
```python
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 * 1024  # 20GB
```

---

## Timeout Limits

| Operation | Timeout | Location | Can Change? |
|-----------|---------|----------|-------------|
| Upload request | 10 minutes | web_interface.py:80 | ✅ Yes |
| Import job | 2 hours | web_interface.py:248 | ✅ Yes |
| Database query | 30 seconds | db_import.py:351 | ✅ Yes |

---

## Stale Job Cleanup

**Runs**: Every 1 hour (background thread)
**Action**: Kills jobs running > 2 hours
**Location**: web_interface.py:210-277

**To disable** (not recommended):
Comment out lines 4189-4191 in web_interface.py

**To change timeout**:
Edit line 248: `if age_hours > 2:` → `if age_hours > 4:`

---

## Validation Rules

### Location Name
- Length: 2-200 characters
- Allowed: Letters, numbers, spaces, punctuation
- Forbidden: `/`, `\`, null bytes

### State Code
- Length: Exactly 2 letters
- Output: Lowercase (NY → ny)

### File Size
- Max: 10GB per file
- Check: Before processing (no memory load)

### Filename
- Max: 255 characters
- Forbidden: Path separators (`/`, `\`)
- Check: Path traversal attempts

---

## Quick Debugging

```bash
# Check Flask is running
curl http://localhost:5000

# Check database exists
ls -lh data/aupat.db

# Check temp directories
ls /tmp/aupat_import_*

# Check logs
tail -50 logs/aupat.log

# Check disk space
df -h

# Check active imports
curl http://localhost:5000/api/task-status | python -m json.tool
```

---

## Performance Tips

1. **Database vacuum** (monthly):
   ```bash
   sqlite3 data/aupat.db "VACUUM;"
   ```

2. **Temp cleanup** (if orphaned):
   ```bash
   find /tmp -name "aupat_import_*" -mtime +1 -exec rm -rf {} \;
   ```

3. **Check index usage**:
   ```sql
   sqlite3 data/aupat.db
   EXPLAIN QUERY PLAN SELECT * FROM images WHERE img_sha256 = 'abc123';
   ```

---

## Rollback Plan

If something breaks:

```bash
# 1. Revert to previous commit
git revert ba8eb43

# 2. Remove indices (optional - they don't hurt)
sqlite3 data/aupat.db "DROP INDEX IF EXISTS idx_images_sha256;"
# ...repeat for other indices

# 3. Restart Flask
pkill -f web_interface.py
git checkout main
python web_interface.py
```

**Note**: Indices are backward compatible and don't change data, so you can leave them.

---

## Code Locations

```
📁 scripts/
├── db_migrate_indices.py    ← Run once to add indices
├── validation.py             ← Import for validation functions
└── ...other scripts

📁 tests/
├── test_validation.py        ← Unit tests (pytest)
├── e2e_test.sh              ← E2E tests (bash)
└── README.md                ← Testing documentation

📁 web_interface.py
├── Line 75: Upload limit config
├── Line 80: Timeout config
├── Line 210: Stale job cleanup function
└── Line 4189: Thread startup
```

---

## Integration with Existing Code

### Using Validation in Routes

```python
from scripts.validation import validate_import_form_data

@app.route('/import/submit', methods=['POST'])
def import_submit():
    try:
        # Validate all form data at once
        data = validate_import_form_data(request.form)
        # data is now clean and safe to use
    except ValueError as e:
        flash(f'Validation error: {e}', 'error')
        return redirect(url_for('import_form'))
```

### Checking File Size Before Upload

```python
from scripts.validation import validate_file_size

for file in request.files.getlist('media_files'):
    try:
        size = validate_file_size(file, max_size_gb=10.0)
        logger.info(f"File size OK: {size / 1024 / 1024:.1f}MB")
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('import_form'))
```

---

## Environment Variables (Optional)

```bash
# Increase limits via environment
export AUPAT_MAX_UPLOAD_GB=20
export AUPAT_REQUEST_TIMEOUT_MIN=15

# In web_interface.py, replace hardcoded values with:
import os
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('AUPAT_MAX_UPLOAD_GB', 10)) * 1024**3
WSGIRequestHandler.timeout = int(os.getenv('AUPAT_REQUEST_TIMEOUT_MIN', 10)) * 60
```

---

**Last Updated**: 2025-11-17
**Version**: Phase 2 & 3 Complete
**Status**: ✅ Ready for Testing
