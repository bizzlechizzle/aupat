# AUPAT CLI Audit - Implementation Guide
## For Less Experienced Developers

This guide provides step-by-step instructions to implement the improvements identified in the CLI audit. Each change is explained in detail with the reasoning behind it.

---

## Overview of Changes

Based on the audit, we need to make the following improvements:

1. **Add CLI progress tracking to 4 scripts** (db_import, db_folder, db_ingest, db_verify)
2. **Remove emoji/symbols from code** (replace with text)
3. **Add validation checks to CLI scripts** (disk space, path writability)
4. **Create location update workflow** (new db_update.py script)

**Priority Order:**
- P0 (Critical): Remove emojis (breaks claude.md spec)
- P1 (High): Add progress tracking (user experience)
- P2 (Medium): Add validation checks (safety)
- P3 (Low): Location update workflow (new feature)

---

## PART 1: Remove Emojis and Symbols (P0)

### Why This Matters

The claude.md specification (line 46) states: "NEE - No Emojis Ever"

Emojis and Unicode symbols cause problems:
- Break in some terminals (encoding issues)
- Not professional for production code
- Hard to grep/search in logs
- Inconsistent across different systems

### Files to Modify

Only **db_import.py** uses emojis/symbols. The others are clean.

### Changes Required

**File: scripts/db_import.py**

Find and replace these patterns:

| Line | Current | Replace With | Reason |
|------|---------|--------------|--------|
| 105 | `"✓ Backup completed successfully"` | `"Backup completed successfully"` | Remove checkmark |
| 158 | `logger.warning(f"⚠ Location name already exists: {loc_name}")` | `logger.warning(f"WARNING: Location name already exists: {loc_name}")` | Replace warning symbol |
| 159 | `logger.warning(f"  Existing UUID: {existing_uuid}")` | Keep as-is | No symbol |
| 160 | `logger.warning("⚠ Creating duplicate location (web interface import)")` | `logger.warning("WARNING: Creating duplicate location (web interface import)")` | Replace warning symbol |
| 219 | `logger.warning(f"⚠ Location name already exists: {loc_name}")` | `logger.warning(f"WARNING: Location name already exists: {loc_name}")` | Replace warning symbol |
| 220 | `logger.warning(f"  Existing UUID: {existing_uuid}")` | Keep as-is | No symbol |
| 432 | `logger.info(f"✓ Imported image: {orig_name} -> {new_filename} ({sha8})")` | `logger.info(f"Imported image: {orig_name} -> {new_filename} ({sha8})")` | Remove checkmark |
| 455 | `logger.info(f"✓ Imported video: {orig_name} -> {new_filename} ({sha8})")` | `logger.info(f"Imported video: {orig_name} -> {new_filename} ({sha8})")` | Remove checkmark |
| 479 | `logger.info(f"✓ Imported document: {orig_name} -> {new_filename} ({sha8})")` | `logger.info(f"Imported document: {orig_name} -> {new_filename} ({sha8})")` | Remove checkmark |
| 506 | `logger.info(f"✓ Match count verified: {stats['total']} files imported")` | `logger.info(f"Match count verified: {stats['total']} files imported")` | Remove checkmark |
| 508 | `logger.warning(f"⚠ Match count mismatch: expected {expected_total}, got {stats['total']}")` | `logger.warning(f"WARNING: Match count mismatch: expected {expected_total}, got {stats['total']}")` | Replace warning symbol |
| 551 | `logger.info(f"✓ Created location record: {location_data['loc_name']}")` | `logger.info(f"Created location record: {location_data['loc_name']}")` | Remove checkmark |
| 629 | `logger.info(f"✓ Imported {imported_count} web URL(s)")` | `logger.info(f"Imported {imported_count} web URL(s)")` | Remove checkmark |
| 710 | `logger.warning("⚠ Skipping backup (--skip-backup flag set)")` | `logger.warning("WARNING: Skipping backup (--skip-backup flag set)")` | Replace warning symbol |
| 770 | `logger.warning(f"⚠ Import completed with {stats['errors']} errors")` | `logger.warning(f"WARNING: Import completed with {stats['errors']} errors")` | Replace warning symbol |
| 772 | `logger.info("✓ IMPORT SUCCESSFUL")` | `logger.info("IMPORT SUCCESSFUL")` | Remove checkmark |

### Implementation Steps

1. Open scripts/db_import.py in your editor
2. Use find-replace (Ctrl+H or Cmd+H):
   - Find: `"✓ ` → Replace with: `"`
   - Find: `"⚠ ` → Replace with: `"WARNING: `
3. Save file
4. Test import to verify no encoding errors

### Testing

```bash
# Run a test import
python scripts/db_import.py --source tempdata/testphotos/middletown --skip-backup -v

# Check logs for clean output (no weird symbols)
```

---

## PART 2: Add CLI Progress Tracking (P1)

### Why This Matters

When running scripts from the command line, users see nothing for potentially minutes. Progress tracking provides:
- Feedback that script is working (not frozen)
- Estimated completion time
- Early detection if script is stuck
- Better user experience

### How Progress Tracking Works

Look at **db_organize.py** (lines 192, 241, 278, 357) - it already does this correctly:

```python
print(f"PROGRESS: {processed_count}/{len(images)} images", flush=True)
```

**Key points:**
- Uses `print()` not `logger` (logger goes to logs, print goes to stdout)
- Format: `PROGRESS: current/total description`
- `flush=True` forces immediate output (don't wait for buffer)
- Web interface parses this format to update progress bar

### Scripts to Modify

1. db_import.py - Add progress during file import
2. db_folder.py - Add progress during folder creation
3. db_ingest.py - Add progress during file movement
4. db_verify.py - Add progress during verification

### Implementation: db_import.py

**Location:** `scripts/db_import.py`, function `import_media_files` (lines 279-513)

**Current code (line 326):**
```python
logger.info(f"Found {len(files)} files to process")
```

**Add after line 326:**
```python
logger.info(f"Found {len(files)} files to process")
print(f"PROGRESS: 0/{len(files)} files", flush=True)  # ADD THIS LINE
```

**Current code (line 481, inside the for loop):**
```python
stats['total'] += 1
```

**Add after line 481:**
```python
stats['total'] += 1
print(f"PROGRESS: {stats['total']}/{len(files)} files", flush=True)  # ADD THIS LINE
```

**Why this works:**
- Prints progress before loop starts (0/total)
- Prints progress after each file (current/total)
- Web interface sees "PROGRESS: X/Y files" and updates bar

### Implementation: db_folder.py

**Location:** `scripts/db_folder.py`, function `create_folders_for_all_locations` (lines 260-302)

**Current code (line 284):**
```python
logger.info(f"Found {len(locations)} locations to process")
```

**Add after line 284:**
```python
logger.info(f"Found {len(locations)} locations to process")
print(f"PROGRESS: 0/{len(locations)} locations", flush=True)  # ADD THIS LINE
```

**Current code (line 286, inside for loop):**
```python
for loc_uuid, loc_name, state, loc_type in locations:
    logger.info(f"Processing location: {loc_name} ({loc_uuid[:8]})")
```

**Add counter and progress tracking:**
```python
processed = 0  # ADD THIS LINE BEFORE LOOP
for loc_uuid, loc_name, state, loc_type in locations:
    logger.info(f"Processing location: {loc_name} ({loc_uuid[:8]})")

    try:
        created_paths = create_folder_structure(
            arch_loc, loc_name, loc_uuid, state, loc_type
        )
        results[loc_uuid] = created_paths
        processed += 1  # ADD THIS LINE
        print(f"PROGRESS: {processed}/{len(locations)} locations", flush=True)  # ADD THIS LINE

    except Exception as e:
        logger.error(f"Failed to create folders for {loc_name}: {e}")
        results[loc_uuid] = None
```

### Implementation: db_ingest.py

**Location:** `scripts/db_ingest.py`, function `ingest_images` (lines 152-272)

**Current code (line 193):**
```python
logger.info(f"Found {len(images)} images to ingest")
```

**Add after line 193:**
```python
logger.info(f"Found {len(images)} images to ingest")
print(f"PROGRESS: 0/{len(images)} images", flush=True)  # ADD THIS LINE
```

**Current code (line 260, after successful ingest):**
```python
ingested_count += 1
logger.debug(f"Ingested ({method}): {filename}")
```

**Add after line 260:**
```python
ingested_count += 1
print(f"PROGRESS: {ingested_count}/{len(images)} images", flush=True)  # ADD THIS LINE
logger.debug(f"Ingested ({method}): {filename}")
```

**Repeat for videos:**

**Location:** `scripts/db_ingest.py`, function `ingest_videos` (lines 275-395)

**Current code (line 316):**
```python
logger.info(f"Found {len(videos)} videos to ingest")
```

**Add after line 316:**
```python
logger.info(f"Found {len(videos)} videos to ingest")
print(f"PROGRESS: 0/{len(videos)} videos", flush=True)  # ADD THIS LINE
```

**Current code (line 383, after successful ingest):**
```python
ingested_count += 1
logger.debug(f"Ingested ({method}): {filename}")
```

**Add after line 383:**
```python
ingested_count += 1
print(f"PROGRESS: {ingested_count}/{len(videos)} videos", flush=True)  # ADD THIS LINE
logger.debug(f"Ingested ({method}): {filename}")
```

### Implementation: db_verify.py

**Location:** `scripts/db_verify.py`, function `verify_files` (lines 51-150)

This one is trickier because it processes 3 types (images, videos, documents) in sequence.

**Strategy:** Track total count and current count across all types.

**Current code (lines 69-77):**
```python
# Verify images
logger.info("Verifying images...")
if location_uuid:
    cursor.execute(
        "SELECT img_sha256, img_loc, img_name FROM images WHERE loc_uuid = ?",
        (location_uuid,)
    )
else:
    cursor.execute("SELECT img_sha256, img_loc, img_name FROM images")
```

**Replace with:**
```python
# Get counts first for progress tracking
if location_uuid:
    cursor.execute("SELECT COUNT(*) FROM images WHERE loc_uuid = ?", (location_uuid,))
    img_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM videos WHERE loc_uuid = ?", (location_uuid,))
    vid_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM documents WHERE loc_uuid = ?", (location_uuid,))
    doc_count = cursor.fetchone()[0]
else:
    cursor.execute("SELECT COUNT(*) FROM images")
    img_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM videos")
    vid_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]

total_files = img_count + vid_count + doc_count
progress_count = 0

logger.info(f"Verifying {total_files} total files ({img_count} images, {vid_count} videos, {doc_count} documents)")
print(f"PROGRESS: 0/{total_files} files", flush=True)

# Verify images
logger.info("Verifying images...")
if location_uuid:
    cursor.execute(
        "SELECT img_sha256, img_loc, img_name FROM images WHERE loc_uuid = ?",
        (location_uuid,)
    )
else:
    cursor.execute("SELECT img_sha256, img_loc, img_name FROM images")
```

**Then inside the image verification loop (after line 86):**
```python
if sha256_file == sha256_db:
    verified_count += 1
    progress_count += 1  # ADD THIS LINE
    print(f"PROGRESS: {progress_count}/{total_files} files", flush=True)  # ADD THIS LINE
```

**Repeat for videos loop (after line 112) and documents loop (after line 138):**
```python
if sha256_file == sha256_db:
    verified_count += 1
    progress_count += 1  # ADD THIS LINE
    print(f"PROGRESS: {progress_count}/{total_files} files", flush=True)  # ADD THIS LINE
```

### Testing Progress Tracking

```bash
# Test each script individually
python scripts/db_import.py --source tempdata/testphotos/middletown --skip-backup
# Watch for: PROGRESS: 1/8 files, PROGRESS: 2/8 files, etc.

python scripts/db_organize.py
# Watch for: PROGRESS: 1/32 images, PROGRESS: 1/2 videos

python scripts/db_folder.py
# Watch for: PROGRESS: 1/1 locations

python scripts/db_ingest.py
# Watch for: PROGRESS: 1/32 images, PROGRESS: 1/2 videos

python scripts/db_verify.py
# Watch for: PROGRESS: 1/34 files (combined count)
```

---

## PART 3: Add Validation Checks (P2)

### Why This Matters

The web interface has excellent pre-flight checks (web_interface.py:253-314):
- Disk space validation
- Path writability checks
- Database schema verification
- Configuration validation

CLI scripts should have the same safety checks to prevent:
- Running out of disk space mid-import (corruption risk)
- Writing to read-only paths (permission errors)
- Missing database tables (crashes)

### Create Shared Validation Module

**Create new file: scripts/validation.py**

```python
#!/usr/bin/env python3
"""
AUPAT Validation Checks
Shared validation functions for all scripts.

Version: 1.0.0
"""

import logging
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


def check_disk_space(path: str, required_gb: float = 1.0) -> Tuple[bool, str]:
    """
    Check if enough disk space is available.

    Args:
        path: Path to check
        required_gb: Required free space in GB

    Returns:
        tuple: (is_ok, message)
    """
    try:
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024**3)

        if free_gb < required_gb:
            return False, f"Insufficient disk space: {free_gb:.2f}GB free, {required_gb}GB required"

        return True, f"Disk space OK: {free_gb:.2f}GB free"

    except Exception as e:
        logger.error(f"Failed to check disk space for {path}: {e}")
        return False, f"Could not check disk space: {e}"


def check_path_writable(path: str) -> Tuple[bool, str]:
    """
    Check if a path is writable by attempting to create a test file.

    Args:
        path: Path to check

    Returns:
        tuple: (is_writable, message)
    """
    test_path = Path(path)

    # If it's a file path, check parent directory
    if not test_path.exists() or test_path.is_file():
        test_dir = test_path.parent
    else:
        test_dir = test_path

    # Try to create directory if it doesn't exist
    try:
        test_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return False, f"Cannot create directory {test_dir}: {e}"

    # Try to write a test file
    test_file = test_dir / f'.aupat_write_test_{os.getpid()}'
    try:
        test_file.write_text('test')
        test_file.unlink()
        return True, f"Path is writable: {test_dir}"
    except Exception as e:
        return False, f"Path not writable {test_dir}: {e}"


def check_database_schema(db_path: str) -> Tuple[bool, list]:
    """
    Verify that required database tables exist.

    Args:
        db_path: Path to database file

    Returns:
        tuple: (is_valid, list_of_missing_tables)
    """
    required_tables = ['locations', 'images', 'videos', 'documents', 'versions']

    if not Path(db_path).exists():
        return False, required_tables  # All tables missing

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        conn.close()

        # Check which tables are missing
        missing = [t for t in required_tables if t not in existing_tables]

        return len(missing) == 0, missing

    except Exception as e:
        logger.error(f"Failed to check database schema: {e}")
        return False, required_tables


def run_preflight_checks(config: dict, required_disk_gb: float = 5.0) -> Tuple[bool, list]:
    """
    Run all preflight checks before starting import.

    Args:
        config: User configuration dict
        required_disk_gb: Required free disk space in GB

    Returns:
        tuple: (all_passed, list_of_errors)
    """
    errors = []

    # Check disk space
    if 'db_ingest' in config:
        disk_ok, disk_msg = check_disk_space(config['db_ingest'], required_disk_gb)
        if not disk_ok:
            errors.append(disk_msg)
        else:
            logger.info(disk_msg)

    # Check path writability
    for path_key in ['db_ingest', 'db_backup', 'arch_loc']:
        if path_key in config:
            writable, write_msg = check_path_writable(config[path_key])
            if not writable:
                errors.append(write_msg)
            else:
                logger.debug(write_msg)

    # Check database schema (only if database exists)
    if 'db_loc' in config and Path(config['db_loc']).exists():
        schema_ok, missing_tables = check_database_schema(config['db_loc'])
        if not schema_ok:
            errors.append(f"Database missing tables: {', '.join(missing_tables)}")

    return len(errors) == 0, errors
```

### Add Validation to CLI Scripts

**File: scripts/db_import.py**

**Add import (after line 54):**
```python
from normalize import (
    normalize_location_name,
    normalize_state_code,
    normalize_location_type,
    normalize_sub_type,
    normalize_datetime,
    normalize_extension,
    normalize_author
)
from validation import run_preflight_checks  # ADD THIS LINE
```

**Add check in main() function (after line 697):**
```python
config = load_user_config(config_path)

# Run preflight checks
logger.info("Running preflight checks...")
checks_passed, check_errors = run_preflight_checks(config, required_disk_gb=5.0)
if not checks_passed:
    logger.error("Preflight checks failed:")
    for error in check_errors:
        logger.error(f"  - {error}")
    logger.error("Fix errors and try again")
    return 1

logger.info("=" * 60)
```

**Repeat for:**
- scripts/db_organize.py (add validation before processing)
- scripts/db_folder.py (add validation before creating folders)
- scripts/db_ingest.py (add validation before moving files)
- scripts/db_verify.py (add validation before verification)

### Testing Validation

```bash
# Test disk space check - should pass
python scripts/db_import.py --source tempdata/testphotos/middletown --skip-backup

# Test with invalid path (create bad config)
# Edit user/user.json temporarily to point db_ingest to /invalid/path
python scripts/db_import.py --source tempdata/testphotos/middletown
# Should error: "Path not writable /invalid/path"
```

---

## PART 4: Create Location Update Workflow (P3)

### Why This Matters

Current system can only create NEW locations. Users need ability to add more media to existing locations without creating duplicates.

**Use case:**
1. User imports "Abandoned Factory" with 100 photos (March 2024)
2. User visits same location again (November 2024)
3. User has 50 new photos to add
4. Should add to existing location, not create duplicate

### Design: db_update.py Script

**Create new file: scripts/db_update.py**

```python
#!/usr/bin/env python3
"""
AUPAT Update Script
Add media to existing locations.

This script:
1. Finds existing location by UUID or name
2. Imports new media files to staging
3. Links files to existing location UUID
4. Runs organize → folder → ingest → verify pipeline

Version: 1.0.0
Last Updated: 2025-11-16
"""

import argparse
import json
import logging
import sqlite3
import subprocess
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import generate_uuid, calculate_sha256, generate_filename, determine_file_type, check_sha256_collision
from normalize import normalize_extension, normalize_datetime, normalize_author
from validation import run_preflight_checks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_user_config(config_path: str = None) -> dict:
    """Load user configuration from user.json."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"user.json not found at {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)


def find_location(db_path: str, search_term: str) -> dict:
    """
    Find location by UUID or name.

    Args:
        db_path: Path to database
        search_term: Location UUID (full or uuid8) or location name

    Returns:
        dict: Location data or None
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Try UUID search first (exact or prefix match)
        cursor.execute(
            """
            SELECT loc_uuid, loc_name, aka_name, state, type, sub_type
            FROM locations
            WHERE loc_uuid = ? OR loc_uuid LIKE ?
            """,
            (search_term, f"{search_term}%")
        )

        result = cursor.fetchone()

        # If not found, try name search
        if not result:
            cursor.execute(
                """
                SELECT loc_uuid, loc_name, aka_name, state, type, sub_type
                FROM locations
                WHERE loc_name LIKE ? OR aka_name LIKE ?
                """,
                (f"%{search_term}%", f"%{search_term}%")
            )
            result = cursor.fetchone()

        if result:
            return {
                'loc_uuid': result[0],
                'loc_name': result[1],
                'aka_name': result[2],
                'state': result[3],
                'type': result[4],
                'sub_type': result[5]
            }

        return None

    finally:
        conn.close()


def list_locations(db_path: str) -> list:
    """List all locations in database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                loc_uuid,
                loc_name,
                state,
                type,
                (SELECT COUNT(*) FROM images WHERE loc_uuid = locations.loc_uuid) as img_count,
                (SELECT COUNT(*) FROM videos WHERE loc_uuid = locations.loc_uuid) as vid_count
            FROM locations
            ORDER BY loc_name
            """
        )

        return [
            {
                'uuid': row[0],
                'uuid8': row[0][:8],
                'name': row[1],
                'state': row[2],
                'type': row[3],
                'images': row[4],
                'videos': row[5]
            }
            for row in cursor.fetchall()
        ]

    finally:
        conn.close()


def add_media_to_location(
    source_dir: str,
    staging_dir: str,
    db_path: str,
    location: dict,
    imp_author: str
) -> dict:
    """
    Add new media files to existing location.

    Args:
        source_dir: Source directory with new media
        staging_dir: Staging/ingest directory
        db_path: Path to database
        location: Location dict from find_location()
        imp_author: Author name

    Returns:
        dict: Statistics
    """
    source_path = Path(source_dir)
    staging_path = Path(staging_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    # Create staging directory using existing location UUID
    loc_uuid = location['loc_uuid']
    loc_staging = staging_path / loc_uuid[:8]
    loc_staging.mkdir(parents=True, exist_ok=True)

    logger.info(f"Adding media to: {location['loc_name']} ({loc_uuid[:8]})")
    logger.info(f"Source: {source_dir}")
    logger.info(f"Staging: {loc_staging}")

    # Collect all files
    files = list(source_path.rglob('*'))
    files = [f for f in files if f.is_file()]

    logger.info(f"Found {len(files)} files to process")
    print(f"PROGRESS: 0/{len(files)} files", flush=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {
        'total': 0,
        'images': 0,
        'videos': 0,
        'documents': 0,
        'duplicates': 0,
        'errors': 0,
        'skipped': 0,
        'hardlinked': 0,
        'copied': 0
    }

    timestamp = normalize_datetime(None)

    # Check if same filesystem for hardlinking
    try:
        same_filesystem = source_path.stat().st_dev == loc_staging.stat().st_dev
        if same_filesystem:
            logger.info("Source and staging on same filesystem - will use hardlinks")
        else:
            logger.info("Source and staging on different filesystems - will copy files")
    except Exception:
        same_filesystem = False
        logger.warning("Could not determine filesystem - defaulting to copy")

    try:
        for file_path in files:
            try:
                # Determine file type
                ext = normalize_extension(file_path.suffix)
                file_type = determine_file_type(ext)

                if file_type == 'other':
                    logger.debug(f"Skipping unknown file type: {file_path.name}")
                    stats['skipped'] += 1
                    continue

                # Calculate SHA256
                sha256 = calculate_sha256(str(file_path))
                sha8 = sha256[:8]

                # Check for collision
                if check_sha256_collision(cursor, sha256, file_type):
                    logger.warning(f"Duplicate {file_type} detected (SHA256 exists): {file_path.name} ({sha8})")
                    stats['duplicates'] += 1
                    continue

                # Generate filename
                media_type = 'img' if file_type == 'image' else 'vid' if file_type == 'video' else 'doc'
                new_filename = generate_filename(media_type, loc_uuid, sha256, ext)

                # Target file in staging
                staging_file = loc_staging / new_filename

                # Copy or hardlink file
                if same_filesystem:
                    try:
                        import os
                        os.link(file_path, staging_file)
                        stats['hardlinked'] += 1
                        logger.debug(f"Hardlinked: {file_path.name} -> {new_filename}")
                    except OSError as e:
                        import shutil
                        logger.warning(f"Hardlink failed, falling back to copy: {e}")
                        shutil.copy2(file_path, staging_file)
                        stats['copied'] += 1
                else:
                    import shutil
                    shutil.copy2(file_path, staging_file)
                    stats['copied'] += 1

                # Store original location
                orig_location = str(file_path.parent)
                orig_name = file_path.name

                # Insert into appropriate table
                if file_type == 'image':
                    cursor.execute(
                        """
                        INSERT INTO images (
                            img_sha256, img_name, img_loc, loc_uuid,
                            img_loco, img_nameo, img_add, img_update, imp_author
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sha256,
                            new_filename,
                            str(staging_file),
                            loc_uuid,
                            orig_location,
                            orig_name,
                            timestamp,
                            timestamp,
                            imp_author
                        )
                    )
                    stats['images'] += 1
                    logger.info(f"Imported image: {orig_name} -> {new_filename} ({sha8})")

                elif file_type == 'video':
                    cursor.execute(
                        """
                        INSERT INTO videos (
                            vid_sha256, vid_name, vid_loc, loc_uuid,
                            vid_loco, vid_nameo, vid_add, vid_update, imp_author
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sha256,
                            new_filename,
                            str(staging_file),
                            loc_uuid,
                            orig_location,
                            orig_name,
                            timestamp,
                            timestamp,
                            imp_author
                        )
                    )
                    stats['videos'] += 1
                    logger.info(f"Imported video: {orig_name} -> {new_filename} ({sha8})")

                elif file_type == 'document':
                    cursor.execute(
                        """
                        INSERT INTO documents (
                            doc_sha256, doc_name, doc_loc, doc_ext, loc_uuid,
                            doc_loco, doc_nameo, doc_add, doc_update, imp_author
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sha256,
                            new_filename,
                            str(staging_file),
                            ext,
                            loc_uuid,
                            orig_location,
                            orig_name,
                            timestamp,
                            timestamp,
                            imp_author
                        )
                    )
                    stats['documents'] += 1
                    logger.info(f"Imported document: {orig_name} -> {new_filename} ({sha8})")

                stats['total'] += 1
                print(f"PROGRESS: {stats['total']}/{len(files)} files", flush=True)

            except Exception as e:
                logger.error(f"Failed to import {file_path.name}: {e}")
                stats['errors'] += 1

        # Update versions table
        cursor.execute(
            """
            INSERT OR REPLACE INTO versions (modules, version, ver_updated)
            VALUES (?, ?, ?)
            """,
            (
                f'update_{loc_uuid[:8]}',
                '1.0.0',
                timestamp
            )
        )

        conn.commit()

        logger.info(f"\nAdded {stats['total']} files to location")

    finally:
        conn.close()

    return stats


def main():
    """Main update workflow."""
    parser = argparse.ArgumentParser(
        description='Add media to existing AUPAT location',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all locations
  python db_update.py --list

  # Add media to location by UUID
  python db_update.py --location a1b2c3d4 --source /new/photos

  # Add media to location by name
  python db_update.py --location "Abandoned Factory" --source /new/photos
        """
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to user.json config file'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all locations in database'
    )
    parser.add_argument(
        '--location',
        type=str,
        help='Location UUID or name to update'
    )
    parser.add_argument(
        '--source',
        type=str,
        help='Source directory containing new media files'
    )
    parser.add_argument(
        '--author',
        type=str,
        help='Your name/username for tracking (optional)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config_path = args.config or str(Path(__file__).parent.parent / 'user' / 'user.json')
        config = load_user_config(config_path)

        # Run preflight checks
        logger.info("Running preflight checks...")
        checks_passed, check_errors = run_preflight_checks(config, required_disk_gb=2.0)
        if not checks_passed:
            logger.error("Preflight checks failed:")
            for error in check_errors:
                logger.error(f"  - {error}")
            return 1

        # List mode
        if args.list:
            logger.info("=" * 60)
            logger.info("All Locations in Database")
            logger.info("=" * 60)

            locations = list_locations(config['db_loc'])

            if not locations:
                logger.info("No locations found in database")
                return 0

            for loc in locations:
                logger.info(f"{loc['uuid8']} - {loc['name']}")
                logger.info(f"  State: {loc['state']}, Type: {loc['type']}")
                logger.info(f"  Media: {loc['images']} images, {loc['videos']} videos")
                logger.info("")

            logger.info(f"Total: {len(locations)} locations")
            return 0

        # Update mode - require both location and source
        if not args.location:
            logger.error("ERROR: --location required (or use --list to see all locations)")
            return 1

        if not args.source:
            logger.error("ERROR: --source required")
            return 1

        # Find location
        logger.info(f"Searching for location: {args.location}")
        location = find_location(config['db_loc'], args.location)

        if not location:
            logger.error(f"Location not found: {args.location}")
            logger.info("\nUse --list to see all locations, or search by:")
            logger.info("  - Full UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)")
            logger.info("  - UUID8 (first 8 characters)")
            logger.info("  - Location name (partial match allowed)")
            return 1

        logger.info(f"Found location: {location['loc_name']} ({location['loc_uuid'][:8]})")

        # Confirm update
        response = input(f"\nAdd new media to '{location['loc_name']}'? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            logger.info("Update cancelled by user")
            return 0

        logger.info("=" * 60)
        logger.info("AUPAT Update - Add Media to Existing Location")
        logger.info("=" * 60)

        # Add media to location
        author = normalize_author(args.author) if args.author else 'unknown'
        stats = add_media_to_location(
            args.source,
            config['db_ingest'],
            config['db_loc'],
            location,
            author
        )

        # Run organize → folder → ingest → verify pipeline
        logger.info("\nRunning pipeline...")

        # Organize (extract metadata)
        logger.info("1/4: Extracting metadata...")
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / 'db_organize.py'), '--config', config_path],
            check=True
        )

        # Folder (create any new folders needed)
        logger.info("2/4: Creating folders...")
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / 'db_folder.py'), '--config', config_path, '--location', location['loc_uuid']],
            check=True
        )

        # Ingest (move to archive)
        logger.info("3/4: Moving files to archive...")
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / 'db_ingest.py'), '--config', config_path],
            check=True
        )

        # Verify (check integrity)
        logger.info("4/4: Verifying integrity...")
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / 'db_verify.py'), '--config', config_path, '--location', location['loc_uuid']],
            check=True
        )

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Update Summary")
        logger.info("=" * 60)
        logger.info(f"Location: {location['loc_name']}")
        logger.info(f"UUID: {location['loc_uuid']}")
        logger.info(f"")
        logger.info(f"New media added: {stats['total']}")
        logger.info(f"  - Images: {stats['images']}")
        logger.info(f"  - Videos: {stats['videos']}")
        logger.info(f"  - Documents: {stats['documents']}")
        logger.info(f"")
        logger.info(f"Duplicates skipped: {stats['duplicates']}")
        logger.info(f"Unknown types skipped: {stats['skipped']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info("=" * 60)

        if stats['errors'] > 0:
            logger.warning(f"WARNING: Update completed with {stats['errors']} errors")
        else:
            logger.info("UPDATE SUCCESSFUL")

        return 0 if stats['errors'] == 0 else 1

    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

### Using db_update.py

**List all locations:**
```bash
python scripts/db_update.py --list
```

**Add new media to location (by UUID8):**
```bash
python scripts/db_update.py --location a1b2c3d4 --source /new/photos --author "YourName"
```

**Add new media to location (by name):**
```bash
python scripts/db_update.py --location "Abandoned Factory" --source /new/photos
```

### Testing db_update.py

```bash
# First, import a location normally
python scripts/db_import.py --source tempdata/testphotos/middletown --skip-backup

# List locations to get UUID
python scripts/db_update.py --list
# Output: a1b2c3d4 - Middletown State Hospital

# Add more media to that location
# (Copy some test files to a new directory first)
mkdir tempdata/newmedia
cp tempdata/testphotos/waterslideworld/*.DNG tempdata/newmedia/

python scripts/db_update.py --location a1b2c3d4 --source tempdata/newmedia

# Verify files were added (check database or archive)
```

---

## SUMMARY & NEXT STEPS

### What We've Covered

1. **P0 - Remove Emojis**: Simple find-replace in db_import.py
2. **P1 - Add Progress Tracking**: Add print() statements to 4 scripts
3. **P2 - Add Validation**: Create validation.py module, add checks to all scripts
4. **P3 - Location Updates**: Create new db_update.py script

### Testing Checklist

- [ ] Emoji removal: Run db_import.py, check logs for clean output
- [ ] Progress tracking: Run all scripts, verify PROGRESS: X/Y messages appear
- [ ] Validation: Run with bad config paths, verify preflight checks catch errors
- [ ] Location updates: Import location, then add more media with db_update.py

### Priority Implementation Order

**Do First (Critical):**
1. Remove emojis from db_import.py (5 minutes)
2. Add progress to db_organize.py (already done - verify it works)
3. Add progress to db_import.py (10 minutes)

**Do Second (High Value):**
4. Add progress to db_ingest.py (15 minutes)
5. Add progress to db_verify.py (20 minutes)
6. Add progress to db_folder.py (10 minutes)

**Do Third (Safety):**
7. Create validation.py (30 minutes)
8. Add validation to all scripts (20 minutes each = 100 minutes total)

**Do Last (New Feature):**
9. Create db_update.py (60 minutes)
10. Test location update workflow (30 minutes)

**Total estimated time: 5-6 hours**

### Getting Help

**If you get stuck:**

1. Check error messages carefully - they usually tell you what's wrong
2. Use verbose logging: add `-v` flag to any script
3. Check the logs in logs/ directory
4. Verify your config: `cat user/user.json`
5. Test with small datasets first (tempdata/testphotos)

**Common issues:**

- "File not found": Check paths in user.json are absolute, not relative
- "Permission denied": Run `chmod +x scripts/*.py` or use `python scripts/scriptname.py`
- "Import error": Make sure you're in the aupat/ directory when running scripts
- "Database locked": Close any other programs accessing the database

---

## APPENDIX: Quick Reference

### Progress Tracking Pattern

```python
# At start of processing
logger.info(f"Found {len(items)} items to process")
print(f"PROGRESS: 0/{len(items)} items", flush=True)

# Inside loop
for i, item in enumerate(items):
    # ... process item ...
    print(f"PROGRESS: {i+1}/{len(items)} items", flush=True)
```

### Validation Pattern

```python
from validation import run_preflight_checks

# In main() function, after loading config
checks_passed, check_errors = run_preflight_checks(config, required_disk_gb=5.0)
if not checks_passed:
    logger.error("Preflight checks failed:")
    for error in check_errors:
        logger.error(f"  - {error}")
    return 1
```

### Emoji Replacement Patterns

```python
# Before:
logger.info(f"✓ Task completed")
logger.warning(f"⚠ Warning message")

# After:
logger.info(f"Task completed")
logger.warning(f"WARNING: Warning message")
```

---

## END OF IMPLEMENTATION GUIDE

This guide provides everything needed to implement all audit recommendations.

Follow the priority order, test each change, commit working code frequently.

Good luck!
