# AUPAT Critical Fixes - Implementation Guide
## For Less Experienced Developers

**Version**: 2.0
**Date**: 2025-11-16
**Based On**: CLI_AUDIT_FINAL_PLAN.md

---

## INTRODUCTION

This guide provides step-by-step instructions to fix the 3 critical issues (P0) identified in the CLI audit. Each fix is explained in detail with the reasoning behind it.

**What You'll Fix**:
1. Remove all emojis from code (violates NEE principle)
2. Fix disk I/O errors on large imports (transaction batching)
3. Add location type suggestions (better user experience)

**Time Required**: 4-6 hours total

**Prerequisites**:
- Basic Python knowledge
- Text editor (VS Code, Sublime, vim, etc.)
- Terminal access
- Git basics (commit, push)

---

## PART 1: REMOVE ALL EMOJIS (P0) - 30 MINUTES

### Why This Matters

The project specification (claude.md line 46, claudecode.md line 51) states: **"NEE - No Emojis Ever"**

Emojis cause problems:
- Break in some terminals (encoding issues)
- Unprofessional for production code
- Hard to search in logs
- Violates core project principles

### Files Affected

Found emojis in 5 files:
- scripts/db_import.py (docstring)
- scripts/database_cleanup.py
- scripts/normalize.py
- scripts/test_drone_detection.py
- scripts/test_video_metadata.py

### Step-by-Step Instructions

**Step 1: Find all emojis**

```bash
cd /home/user/aupat
grep -rn '[✓⚠]' scripts/
```

This shows every line with checkmark (✓) or warning (⚠) emoji.

**Step 2: Fix scripts/db_import.py**

Open the file:
```bash
nano scripts/db_import.py
# OR
code scripts/db_import.py
```

Find lines 653-660 (the docstring at the top of the file). Change from:
```python
"""
AUPAT Import Script
Imports new locations and associated media via CLI.

This script:
1. Creates backup before import
...

Features:
  ✓ Backup before import
  ✓ Location name collision detection
  ✓ File type detection (images/videos/documents)
  ✓ SHA256 collision checking
  ✓ Hardlink support for same-disk imports
  ✓ Database record creation for all media
  ✓ Versions table tracking
  ✓ Import match count verification
"""
```

To:
```python
"""
AUPAT Import Script
Imports new locations and associated media via CLI.

This script:
1. Creates backup before import
...

Features:
- Backup before import
- Location name collision detection
- File type detection (images/videos/documents)
- SHA256 collision checking
- Hardlink support for same-disk imports
- Database record creation for all media
- Versions table tracking
- Import match count verification
"""
```

**What Changed**: Replaced `✓` with `-` (plain hyphen bullet point)

**Step 3: Fix other files**

Use find-replace in your editor:
- Find: `✓ ` (checkmark + space)
- Replace: `- ` (hyphen + space)

Or use sed command:
```bash
# Backup first
cp scripts/database_cleanup.py scripts/database_cleanup.py.bak

# Replace emojis
sed -i 's/✓ /- /g' scripts/database_cleanup.py
sed -i 's/⚠ /WARNING: /g' scripts/database_cleanup.py

# Repeat for other files
sed -i 's/✓ /- /g' scripts/normalize.py
sed -i 's/⚠ /WARNING: /g' scripts/normalize.py

sed -i 's/✓ /- /g' scripts/test_drone_detection.py
sed -i 's/⚠ /WARNING: /g' scripts/test_drone_detection.py

sed -i 's/✓ /- /g' scripts/test_video_metadata.py
sed -i 's/⚠ /WARNING: /g' scripts/test_video_metadata.py
```

**Step 4: Verify all emojis removed**

```bash
grep -rn '[✓⚠]' scripts/
```

This should return **nothing**. If it still shows files, manually edit those lines.

**Step 5: Test**

```bash
# Make sure scripts still run
python scripts/db_import.py --help
```

If it shows help text without errors, you're good!

---

## PART 2: FIX DISK I/O ERROR ON LARGE IMPORTS (P0) - 4 HOURS

### Why This Matters

The terminal output showed import with 623 files failed with:
```
sqlite3.OperationalError: disk I/O error
```

This happens because:
1. SQLite has default timeout of 5 seconds
2. Large transactions can exceed this
3. All 623 files imported in single transaction
4. Database gets locked, operation fails

### The Solution: Transaction Batching

Instead of importing all files in one transaction, we'll commit every 100 files.

**Analogy**: Like moving 623 boxes. Instead of carrying all at once (impossible), carry 100 at a time.

### File to Modify: scripts/db_import.py

**Step 1: Increase SQLite timeout**

Find the database connection code (around line 520-530 in the `import_media_files` function).

Look for:
```python
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
```

Change to:
```python
conn = sqlite3.connect(db_path, timeout=30.0)  # Increase from default 5s to 30s
cursor = conn.cursor()
# Enable WAL mode for better concurrency
cursor.execute("PRAGMA journal_mode=WAL")
```

**Why**:
- `timeout=30.0`: Gives 30 seconds for database locks (vs default 5s)
- `PRAGMA journal_mode=WAL`: Write-Ahead Logging = better concurrent access

**Step 2: Add transaction batching**

Find the file processing loop (around line 326-481). It looks like:

```python
try:
    # Begin transaction
    conn.execute("BEGIN TRANSACTION")

    for file_path in files:
        # ... process file ...
        # ... insert into database ...
        stats['total'] += 1
        print(f"PROGRESS: {stats['total']}/{len(files)} files", flush=True)

    # Commit at end
    conn.commit()
```

Change to:
```python
BATCH_SIZE = 100  # Commit every 100 files

try:
    # Begin first transaction
    conn.execute("BEGIN TRANSACTION")

    for i, file_path in enumerate(files, 1):
        # ... process file ...
        # ... insert into database ...
        stats['total'] += 1
        print(f"PROGRESS: {stats['total']}/{len(files)} files", flush=True)

        # Commit every BATCH_SIZE files
        if i % BATCH_SIZE == 0:
            conn.commit()
            logger.info(f"Committed batch {i//BATCH_SIZE} ({i} files processed)")
            conn.execute("BEGIN TRANSACTION")  # Start new transaction

    # Commit remaining files
    conn.commit()
```

**What Changed**:
1. Added `BATCH_SIZE = 100` constant
2. Changed `for file_path in files:` to `for i, file_path in enumerate(files, 1):`
3. Added commit every 100 files: `if i % BATCH_SIZE == 0:`
4. Start new transaction after commit
5. Final commit for remaining files (e.g., if 623 files, commits at 100, 200, 300, 400, 500, 600, then final 23)

**Step 3: Add better error handling**

Wrap the transaction code in try/except:

```python
BATCH_SIZE = 100
batch_start = 0

try:
    conn.execute("BEGIN TRANSACTION")

    for i, file_path in enumerate(files, 1):
        try:
            # ... process file ...
            stats['total'] += 1
            print(f"PROGRESS: {stats['total']}/{len(files)} files", flush=True)

            # Commit every BATCH_SIZE files
            if i % BATCH_SIZE == 0:
                conn.commit()
                logger.info(f"Committed batch {i//BATCH_SIZE} ({i} files processed)")
                batch_start = i
                conn.execute("BEGIN TRANSACTION")

        except sqlite3.Error as db_err:
            logger.error(f"Database error on file {i} ({file_path.name}): {db_err}")
            logger.error(f"Rolling back batch starting at file {batch_start}")
            conn.rollback()
            # Try to continue with next batch
            batch_start = i
            conn.execute("BEGIN TRANSACTION")
            stats['errors'] += 1

        except Exception as e:
            logger.error(f"Failed to import {file_path.name}: {e}")
            stats['errors'] += 1

    # Commit remaining files
    conn.commit()
    logger.info(f"Import completed: {stats['total']} files, {stats['errors']} errors")

except sqlite3.Error as e:
    logger.error(f"Fatal database error: {e}")
    conn.rollback()
    raise

finally:
    conn.close()
```

**What Changed**:
1. Track `batch_start` to know where to rollback to
2. Catch `sqlite3.Error` specifically for database errors
3. Rollback only current batch (not entire import)
4. Continue with next batch after error
5. Final cleanup in `finally` block

**Step 4: Add disk space check before import**

At the start of `import_media_files()` function (around line 279):

```python
def import_media_files(
    source_dir: str,
    staging_dir: str,
    db_path: str,
    location_data: dict,
    imp_author: str
) -> dict:
    """Import media files to staging and create database entries."""

    # ADD THIS: Check disk space before starting
    import shutil
    source_path = Path(source_dir)

    # Estimate space needed (rough: sum of file sizes * 2 for safety)
    total_size = sum(f.stat().st_size for f in source_path.rglob('*') if f.is_file())
    total_size_gb = total_size / (1024**3)
    required_gb = total_size_gb * 2  # 2x for safety (staging + archive)

    # Check available space
    stat = shutil.disk_usage(staging_dir)
    free_gb = stat.free / (1024**3)

    if free_gb < required_gb:
        raise RuntimeError(
            f"Insufficient disk space: {free_gb:.2f}GB free, "
            f"{required_gb:.2f}GB required for safe import. "
            f"Free up space and try again."
        )

    logger.info(f"Disk space check: {free_gb:.2f}GB free, {required_gb:.2f}GB required")

    # Rest of function...
```

**What Changed**:
1. Calculate total size of source files
2. Estimate required space (2x for safety)
3. Check free space before starting
4. Raise error with helpful message if insufficient space

### Testing Part 2

**Test 1: Small dataset** (make sure we didn't break anything)
```bash
python scripts/db_import.py --source tempdata/testphotos/middletown --skip-backup -v
```

Watch for:
- No errors
- Files import successfully
- See "Committed batch" messages if >100 files

**Test 2: Large dataset** (the one that failed before)
```bash
# Use the 623-file dataset that failed before
python scripts/db_import.py --source /path/to/623files --skip-backup -v
```

Watch for:
- "Committed batch 1 (100 files processed)"
- "Committed batch 2 (200 files processed)"
- ... up to batch 6
- "Import completed: 623 files, 0 errors"
- **No disk I/O error!**

**Test 3: Low disk space**
```bash
# Temporarily use a small disk or fill up disk to test error message
# Should see: "Insufficient disk space: X GB free, Y GB required"
```

---

## PART 3: ADD LOCATION TYPE SUGGESTIONS (P0) - 2 HOURS

### Why This Matters

Users entering intuitive but invalid types:
- 'medical' → system should suggest 'healthcare'
- 'hospital' → system should suggest 'healthcare'
- 'businesses' → system should suggest 'commercial'
- 'entertainment' → system should suggest 'recreational'

Currently: Warning logged, user not informed, confusing experience

### The Solution: Type Mapping + Auto-Suggestion

**Step 1: Create type mapping file**

Create new file: `data/location_type_mapping.json`

```bash
nano data/location_type_mapping.json
```

Add this content:
```json
{
  "mappings": {
    "medical": "healthcare",
    "hospital": "healthcare",
    "clinic": "healthcare",
    "doctor": "healthcare",
    "nursing-home": "healthcare",
    "asylum": "healthcare",

    "business": "commercial",
    "businesses": "commercial",
    "retail": "commercial",
    "store": "commercial",
    "shop": "commercial",
    "mall": "commercial",
    "office": "commercial",

    "entertainment": "recreational",
    "amusement": "recreational",
    "park": "recreational",
    "theater": "recreational",
    "cinema": "recreational",
    "pool": "recreational",
    "waterpark": "recreational",

    "faith": "religious",
    "church": "religious",
    "temple": "religious",
    "mosque": "religious",
    "synagogue": "religious",
    "chapel": "religious",
    "cathedral": "religious",

    "school": "educational",
    "college": "educational",
    "university": "educational",
    "academy": "educational",
    "institute": "educational",

    "factory": "industrial",
    "warehouse": "industrial",
    "plant": "industrial",
    "mill": "industrial",
    "foundry": "industrial",

    "farm": "agricultural",
    "ranch": "agricultural",
    "barn": "agricultural",
    "silo": "agricultural",

    "house": "residential",
    "home": "residential",
    "apartment": "residential",
    "condo": "residential",
    "mansion": "residential",

    "base": "military",
    "fort": "military",
    "barracks": "military",
    "armory": "military",

    "prison": "institutional",
    "jail": "institutional",
    "courthouse": "institutional",
    "government": "institutional",
    "city-hall": "institutional",

    "road": "infrastructure",
    "bridge": "infrastructure",
    "tunnel": "infrastructure",
    "dam": "infrastructure",
    "power-plant": "infrastructure",

    "train": "transportation",
    "station": "transportation",
    "depot": "transportation",
    "airport": "transportation",
    "terminal": "transportation"
  },

  "valid_types": [
    "industrial",
    "residential",
    "commercial",
    "institutional",
    "agricultural",
    "recreational",
    "infrastructure",
    "military",
    "religious",
    "educational",
    "healthcare",
    "transportation",
    "mixed-use",
    "other"
  ]
}
```

**What This Does**: Maps common user inputs to valid types

**Step 2: Update scripts/normalize.py**

Add function to load and use the mapping:

```python
# At top of file, after imports
import json
from pathlib import Path

# Load type mapping
def load_type_mapping() -> dict:
    """Load location type mapping from JSON."""
    mapping_path = Path(__file__).parent.parent / 'data' / 'location_type_mapping.json'

    if not mapping_path.exists():
        logger.warning("location_type_mapping.json not found - suggestions disabled")
        return {'mappings': {}, 'valid_types': list(VALID_LOCATION_TYPES)}

    with open(mapping_path, 'r') as f:
        return json.load(f)

# Load once at module level
TYPE_MAPPING_DATA = load_type_mapping()
TYPE_MAPPINGS = TYPE_MAPPING_DATA.get('mappings', {})
```

**Step 3: Update normalize_location_type function**

Find the `normalize_location_type()` function (around line 230-259).

Change from:
```python
def normalize_location_type(location_type: str) -> str:
    """Normalize location type."""
    if not location_type or not location_type.strip():
        return 'other'

    # Convert Unicode to ASCII
    if HAS_UNIDECODE:
        normalized = unidecode(location_type)
    else:
        normalized = location_type

    # Clean and lowercase
    normalized = normalized.strip().lower()

    # Replace spaces with hyphens
    normalized = normalized.replace(' ', '-')

    # Validate (warn if unknown, but allow it)
    if normalized not in VALID_LOCATION_TYPES:
        logger.warning(
            f"Unknown location type: '{normalized}'. "
            f"Valid types: {sorted(VALID_LOCATION_TYPES)}"
        )

    return normalized
```

To:
```python
def normalize_location_type(location_type: str, auto_correct: bool = True) -> str:
    """
    Normalize location type with auto-correction.

    Args:
        location_type: Raw location type from user
        auto_correct: If True, auto-correct using type mappings

    Returns:
        str: Normalized type (auto-corrected if mapping exists)
    """
    if not location_type or not location_type.strip():
        return 'other'

    # Convert Unicode to ASCII
    if HAS_UNIDECODE:
        normalized = unidecode(location_type)
    else:
        normalized = location_type

    # Clean and lowercase
    normalized = normalized.strip().lower()

    # Replace spaces with hyphens
    normalized = normalized.replace(' ', '-')

    # Check if it's already valid
    if normalized in VALID_LOCATION_TYPES:
        return normalized

    # Try to auto-correct using mapping
    if auto_correct and normalized in TYPE_MAPPINGS:
        suggested = TYPE_MAPPINGS[normalized]
        logger.info(
            f"Location type '{normalized}' auto-corrected to '{suggested}'"
        )
        return suggested

    # Unknown type - warn but allow
    logger.warning(
        f"Unknown location type: '{normalized}'. "
        f"Valid types: {sorted(VALID_LOCATION_TYPES)}. "
        f"Using '{normalized}' as-is."
    )

    return normalized
```

**What Changed**:
1. Added `auto_correct` parameter (default True)
2. Return early if already valid
3. Check mapping and auto-correct with INFO log
4. Improved warning message
5. Return user's input if no mapping (allows custom types)

**Step 4: Update web interface**

Edit `web_interface.py` to show type dropdown with suggestions.

Find the import form (search for "location type" in template around line 1500+).

Change from:
```html
<input type="text" name="type" required>
```

To:
```html
<input type="text"
       name="type"
       list="location-types"
       placeholder="Start typing to see suggestions..."
       required>
<datalist id="location-types">
  <option value="healthcare">Healthcare (hospitals, clinics)</option>
  <option value="commercial">Commercial (businesses, retail)</option>
  <option value="recreational">Recreational (parks, entertainment)</option>
  <option value="religious">Religious (churches, temples)</option>
  <option value="educational">Educational (schools, universities)</option>
  <option value="industrial">Industrial (factories, warehouses)</option>
  <option value="residential">Residential (houses, apartments)</option>
  <option value="agricultural">Agricultural (farms, ranches)</option>
  <option value="institutional">Institutional (prisons, government)</option>
  <option value="infrastructure">Infrastructure (bridges, roads)</option>
  <option value="transportation">Transportation (stations, airports)</option>
  <option value="military">Military (bases, forts)</option>
  <option value="mixed-use">Mixed Use</option>
  <option value="other">Other</option>
</datalist>
```

**What This Does**: Shows dropdown with suggestions as user types (HTML5 datalist)

### Testing Part 3

**Test 1: Auto-correction in CLI**
```bash
# Test with invalid type that has mapping
python -c "
from scripts.normalize import normalize_location_type
print(normalize_location_type('hospital'))  # Should print: healthcare
print(normalize_location_type('businesses'))  # Should print: commercial
print(normalize_location_type('entertainment'))  # Should print: recreational
"
```

Expected output:
```
healthcare
commercial
recreational
```

**Test 2: Web interface dropdown**
```bash
python web_interface.py
# Open http://localhost:5000
# Go to Import page
# Click on "Type" field
# Start typing "hosp" - should see "healthcare (hospitals, clinics)" suggestion
```

**Test 3: Full import with auto-correction**
```bash
# Import with invalid type
# Create test location with type "hospital"
# Check database - should be stored as "healthcare"

sqlite3 tempdata/database/abandonedupstate.db "SELECT loc_name, type FROM locations WHERE type = 'healthcare';"
```

---

## SUMMARY

### What You Fixed

1. **Emojis Removed**:
   - All ✓ and ⚠ replaced with plain text
   - 5 files cleaned up
   - NEE principle now compliant

2. **Disk I/O Errors Fixed**:
   - Transaction batching (commit every 100 files)
   - Increased timeout (5s → 30s)
   - WAL mode enabled
   - Disk space pre-flight check
   - Better error handling

3. **Location Type UX Improved**:
   - Auto-correction for common types
   - Helpful suggestions in web UI
   - Clear logging of corrections
   - 40+ type mappings

### Time Spent

- Part 1 (Emojis): 30 minutes
- Part 2 (Disk I/O): 4 hours
- Part 3 (Type Suggestions): 2 hours
- **Total**: 6.5 hours

### Testing Checklist

- [ ] No emojis found: `grep -rn '[✓⚠]' scripts/` returns nothing
- [ ] Small import works: 8 files import successfully
- [ ] Large import works: 623 files import successfully
- [ ] Batch commits logged: See "Committed batch X" messages
- [ ] Type auto-correction works: 'hospital' → 'healthcare'
- [ ] Web dropdown works: Shows suggestions when typing
- [ ] Disk space check works: Error if insufficient space

### Next Steps

After completing these fixes:

1. Commit your changes:
```bash
git add -A
git commit -m "Fix P0 critical issues: Remove emojis, add transaction batching, improve type validation"
git push -u origin claude/fix-import-page-01NEuSBBETd3QEq6bjmWy5R5
```

2. Test with real data (623-file import)

3. Move on to P1 fixes (verification cross-contamination, validation module)

---

## GETTING HELP

If you get stuck:

1. **Error messages**: Read them carefully - they tell you what's wrong
2. **Verbose logging**: Add `-v` flag to any script for more details
3. **Check logs**: Look in logs/ directory for detailed error info
4. **Test in isolation**: If part fails, test just that function
5. **Compare with examples**: Look at existing code patterns

Common issues:

- **"File not found"**: Check paths are absolute, not relative
- **"Permission denied"**: Check file permissions, run with `python scripts/X.py`
- **"Import error"**: Make sure you're in /home/user/aupat directory
- **"Database locked"**: Close other programs accessing database
- **Syntax error**: Check indentation (Python is picky about spaces/tabs)

---

**Good luck! You're fixing critical issues in a production-quality system.**
