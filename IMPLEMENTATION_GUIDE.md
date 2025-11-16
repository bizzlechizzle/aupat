# AUPAT Camera Extraction Fix - Implementation Guide

## For Less Experienced Coders

This guide explains what we're fixing, why it's broken, and how to fix it step-by-step.

---

## What Is AUPAT Supposed To Do?

AUPAT is a media archive system that organizes photos and videos by location. The MAIN feature is:

**Extract camera make and model from images/videos, then categorize them**

For example:
- Photo taken with Nikon D850 → category: "camera" (DSLR)
- Photo taken with iPhone 13 → category: "phone"
- Video taken with DJI Mavic → category: "drone"

This is done by:
1. Running `exiftool` on images to get EXIF data (contains Make and Model)
2. Running `ffprobe` on videos to get metadata
3. Looking up the Make in `camera_hardware.json` to determine category
4. Storing results in database

---

## What's Broken?

### The Bug

File: `scripts/db_organize.py`, Line 154

```python
# CURRENT CODE (WRONG):
for category, rules in hardware_rules.items():
```

### Why This Is Wrong

Let's look at what `hardware_rules` contains after loading `camera_hardware.json`:

```json
{
  "version": "0.0.1",
  "last_updated": "2025-11-15",
  "description": "...",
  "categories": {
    "dslr": { "makes": ["Canon", "Nikon", ...] },
    "phone": { "makes": ["Apple", "Samsung", ...] },
    "drone": { "makes": ["DJI", "Autel", ...] }
  },
  "matching_rules": {...},
  "category_priorities": {...}
}
```

When we call `hardware_rules.items()`, we get:
- ("version", "0.0.1")
- ("last_updated", "2025-11-15")
- ("description", "...")
- ("categories", {...all the actual camera data...})
- ("matching_rules", {...})
- ("category_priorities", {...})

So the loop tries to use "version", "last_updated", "description" etc. as categories. This is wrong. We need to iterate over the "categories" key only.

### The Fix

```python
# CORRECT CODE:
for category, rules in hardware_rules.get('categories', {}).items():
```

Now we iterate over:
- ("dslr", {"makes": ["Canon", "Nikon", ...]})
- ("phone", {"makes": ["Apple", "Samsung", ...]})
- ("drone", {"makes": ["DJI", "Autel", ...]})

This is correct.

---

## Step-by-Step Fix Explanation

### Fix #1: Correct the Dictionary Traversal

**Location**: Line 154

**Before**:
```python
def categorize_hardware(make: str, model: str, hardware_rules: dict) -> str:
    if not make or not hardware_rules:
        return 'other'

    make_lower = make.lower()

    # Check each category
    for category, rules in hardware_rules.items():  # <-- WRONG
        if 'makes' in rules:
            for rule_make in rules['makes']:
                if rule_make.lower() in make_lower:
                    return category.lower().replace(' ', '_')

    return 'other'
```

**After**:
```python
def categorize_hardware(make: str, model: str, hardware_rules: dict) -> str:
    if not make or not hardware_rules:
        return 'other'

    make_lower = make.lower()

    # Check each category
    for category, rules in hardware_rules.get('categories', {}).items():  # <-- CORRECT
        if 'makes' in rules:
            for rule_make in rules['makes']:
                if rule_make.lower() in make_lower:
                    return category.lower().replace(' ', '_')

    return 'other'
```

**What changed**: Added `.get('categories', {})` to access the nested categories dict.

**Why `.get()` instead of `[]`**: Safe default - if "categories" key doesn't exist, return empty dict instead of crashing.

---

### Fix #2: Correct the exiftool_hardware Field Type

**Location**: Line 223 (inside `organize_images()`)

According to spec (`logseq/pages/images_table.md` line 21):
```
exiftool_hardware = true/false [starts false]
```

This should be a boolean (0 or 1 in SQLite), not a JSON dump.

**Before**:
```python
cursor.execute(
    """
    UPDATE images
    SET
        exiftool_hardware = ?,
        ...
    """,
    (
        json.dumps(exif),  # <-- WRONG: Storing entire EXIF as JSON
        ...
    )
)
```

**After**:
```python
cursor.execute(
    """
    UPDATE images
    SET
        exiftool_hardware = ?,
        ...
    """,
    (
        1 if exif else 0,  # <-- CORRECT: Boolean flag
        ...
    )
)
```

**What changed**: Store 1 (true) if exiftool returned data, 0 (false) if it didn't.

**Why**: The field indicates "did we successfully run exiftool?", not "what did exiftool return?"

---

### Fix #3: Clean Up img_hardware Field

**Location**: Line 224

The spec says to store only Make and Model:

```
img_hardware = [json1]
  - camera brand = Make
  - camera model = Model
```

**Before**:
```python
img_hardware = json.dumps({'make': make, 'model': model, 'category': category}),
```

**After**:
```python
img_hardware = json.dumps({'make': make, 'model': model}),
```

**What changed**: Removed `'category': category` from JSON.

**Why**: Category is already stored in separate boolean fields (camera, phone, drone, etc.). Storing it twice is redundant and violates KISS principle.

---

## Understanding the Data Flow

### Step 1: Import
User uploads photos → stored in staging/ingest folder → paths saved to database

### Step 2: Organize (Where We Are)
For each image in database:
1. Read file path from database
2. Run `exiftool -j /path/to/image.jpg`
3. Extract Make and Model from EXIF
4. Look up Make in camera_hardware.json categories
5. Determine category (dslr, phone, drone, etc.)
6. Update database with:
   - img_hardware = {"make": "Nikon", "model": "D850"}
   - exiftool_hardware = 1
   - camera = 1, phone = 0, drone = 0, etc.

### Step 3: Folder Creation
Create organized folders based on categories

### Step 4: Ingest
Move files from staging to final archive location

### Step 5: Verify
Check all files exist and SHA256 matches

---

## Testing the Fix

### Before Fix

```bash
$ python scripts/db_organize.py
# Images processed: 8
# But if you check database:

$ sqlite3 data/aupat.db "SELECT camera, phone, drone FROM images;"
# Result:
# NULL|NULL|NULL
# NULL|NULL|NULL
# NULL|NULL|NULL
# (all NULL - categorization never ran)
```

### After Fix

```bash
$ python scripts/db_organize.py
# Images processed: 8

$ sqlite3 data/aupat.db "SELECT img_name, json_extract(img_hardware, '$.make'), json_extract(img_hardware, '$.model'), camera, phone FROM images;"
# Expected Result:
# afc04f28-img_12345678.nef|NIKON CORPORATION|NIKON D850|1|0
# afc04f28-img_23456789.nef|NIKON CORPORATION|NIKON D850|1|0
# (camera=1 for DSLR, phone=0)
```

---

## Why These Bugs Existed

1. **Nested JSON Structure**: camera_hardware.json has a "categories" wrapper. The code assumed flat structure.

2. **Field Type Confusion**: exiftool_hardware name suggests it stores exiftool output, but spec says it's a boolean flag.

3. **Redundant Data**: Storing category in both img_hardware JSON and separate boolean fields.

---

## Files Changed Summary

```
MODIFIED:
  scripts/db_organize.py
    - Line 154: Fix category iteration
    - Line 223: Fix exiftool_hardware type
    - Line 224: Remove redundant category field
    - Line 298-311: Same fixes for video processing
```

---

## How to Apply These Fixes

### Option 1: Manual Edit

1. Open `scripts/db_organize.py` in editor
2. Find line 154
3. Change `hardware_rules.items()` to `hardware_rules.get('categories', {}).items()`
4. Find line 223
5. Change `json.dumps(exif),` to `1 if exif else 0,`
6. Find line 224
7. Change `json.dumps({'make': make, 'model': model, 'category': category}),` to `json.dumps({'make': make, 'model': model}),`
8. Find line 298 (video section - same bug)
9. Repeat step 5 (change to boolean)
10. Find line 312
11. Repeat step 7 (remove category)
12. Save file

### Option 2: Using Edit Tool

See the actual implementation below.

---

## Verifying the Fix Works

### Test Case: Middletown State Hospital

This folder has 8 NEF files (Nikon RAW) in `tempdata/testphotos/Middletown State Hospital/`.

These should:
- Extract Make: "NIKON CORPORATION" (or "Nikon")
- Extract Model: "NIKON D850" (or similar)
- Categorize as: camera=1 (DSLR)

### Full Test Sequence

```bash
# 1. Setup
bash setup.sh

# 2. Create database
python scripts/db_migrate.py

# 3. Import test data (via web interface or CLI)
# Upload tempdata/testphotos/Middletown State Hospital/

# 4. Run organize (this is what we fixed)
python scripts/db_organize.py

# 5. Verify results
sqlite3 data/aupat.db << EOF
SELECT
  img_name,
  json_extract(img_hardware, '\$.make') as make,
  json_extract(img_hardware, '\$.model') as model,
  camera,
  phone,
  drone
FROM images
LIMIT 5;
EOF
```

### Expected Output

```
afc04f28-img_12345678.nef|NIKON CORPORATION|NIKON D850|1|0|0
afc04f28-img_23456789.nef|NIKON CORPORATION|NIKON D850|1|0|0
...
```

All Nikon images should show:
- make: NIKON CORPORATION (or Nikon)
- model: actual camera model
- camera: 1
- phone: 0
- drone: 0

---

## Common Questions

### Q: Why does camera_hardware.json have nested structure?

A: It's organized by sections for maintainability. The "categories" key contains actual camera data. Other keys like "matching_rules" and "category_priorities" provide metadata about how to use the categories.

### Q: Why store category in multiple places?

A: Different use cases:
- Boolean fields (camera, phone, drone) → Fast filtering in SQL: `SELECT * FROM images WHERE camera=1`
- img_hardware JSON → Preserves original Make/Model for display/export

The bug was ALSO storing category in img_hardware, which is redundant.

### Q: What if exiftool fails to extract Make/Model?

A: Then:
- make = "" (empty string)
- model = "" (empty string)
- category = "other" (fallback)
- exiftool_hardware = 0 (false - extraction failed)

The system still works, just categorizes as "other".

### Q: What about videos?

A: Same bug exists in `organize_videos()` function (line 298-334). Same fixes apply:
- Fix category iteration
- Fix ffmpeg_hardware to boolean
- Remove category from vid_hardware

---

## Success Criteria

After applying these fixes:

1. **Images are categorized**: camera=1 for DSLRs, phone=1 for phones, etc.
2. **Make/Model extracted**: img_hardware contains {"make": "...", "model": "..."}
3. **Flags set correctly**: exiftool_hardware = 1 when extraction succeeds
4. **No crashes**: Code handles missing/malformed data gracefully

This is the ONLY thing AUPAT needs to do per the original spec. Everything else (folder creation, ingestion, verification) depends on this working.

---

## Additional Context

### Why This Fix Is Critical

From the user's perspective:
- "This program is a complete mess"
- "Why aren't we identifying images camera and model?"
- "Per the spec this is the ONLY thing we are looking for"

This fix addresses the core complaint. Without correct camera categorization:
- Can't organize by camera type
- Can't filter DSLR vs phone photos
- Can't generate reports by hardware
- The entire system's value proposition is broken

### Alignment with Spec

From `logseq/pages/db_organize.md`:
```
images run
  - exiftool -Make -Model
  - log img_hardware = [json1]
    - camera brand = Make
    - camera model = Model
```

Our fix ensures this happens correctly.

From `logseq/pages/camera_hardware.md`:
```
true/false camera_hardware
  - camera: true if dslr [for all images/video]
  - phone: true if phone [for all images/video]
  - drone: true if drone [for all images/video]
  - gopro: true if gopro [for all images/video]
  - other: true if not any of the above
```

Our fix ensures these boolean flags are set correctly based on the Make field.

---

## Next Steps After Fix

1. Apply the 3 line changes to db_organize.py
2. Create user/user.json from template
3. Run setup.sh to initialize database
4. Import test data (Middletown State Hospital)
5. Run db_organize.py
6. Verify categorization worked
7. Clean up obsolete documentation files
8. Update .gitignore
9. Write clean README.md

Then the system will work as originally designed.
