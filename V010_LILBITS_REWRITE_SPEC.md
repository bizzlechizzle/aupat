# AUPAT v0.1.0 LILBITS-COMPLIANT REWRITE SPECIFICATION

Version: 1.0.0
Date: 2025-11-18
Reviewer: Claude (AI Subject Matter Expert)

---

## EXECUTIVE SUMMARY

**CURRENT STATE:** v0.1.0 import pipeline has **CRITICAL LILBITS violations**

**VIOLATIONS FOUND:** 8 of 8 core import scripts violate 200-line LILBITS rule

**SOLUTION:** Split monolithic scripts into 28 focused LILBITS-compliant modules

**RESULT:** Clean, maintainable architecture for vibe coding developer

---

## TABLE OF CONTENTS

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [LILBITS Violations Audit](#lilbits-violations-audit)
3. [Rewrite Strategy](#rewrite-strategy)
4. [New Architecture](#new-architecture)
5. [Script-by-Script Breakdown](#script-by-script-breakdown)
6. [Implementation Plan](#implementation-plan)
7. [Migration Strategy](#migration-strategy)
8. [Testing Requirements](#testing-requirements)

---

## 1. CURRENT ARCHITECTURE ANALYSIS

### Current v0.1.0 Import Pipeline

```
PHASE 1: IMPORT (db_import_v012.py)
├── Load metadata.json
├── Create location in database
├── Scan source folder for files
├── For each file:
│   ├── Calculate SHA256
│   ├── Check for duplicates
│   ├── Extract EXIF (if image/video)
│   ├── Upload to Immich (optional)
│   ├── Generate filename
│   ├── Copy to staging
│   └── Insert into database
└── Return stats

PHASE 2: ORGANIZE (db_organize.py)
├── For each image:
│   ├── Extract EXIF with exiftool
│   ├── Extract make/model
│   ├── Categorize hardware (camera/phone/drone/etc.)
│   └── Update database
└── For each video:
    ├── Extract metadata with ffprobe
    ├── Extract make/model
    ├── Categorize hardware
    └── Update database

PHASE 3: FOLDER CREATION (db_folder.py)
├── Query database for location details
├── Query database for media counts by category
├── Create base folder: State-Type/LocationName_UUID8/
└── Create subfolders only for categories with files:
    ├── photos/original_camera/
    ├── photos/original_phone/
    ├── videos/original_drone/
    └── etc.

PHASE 4: INGEST (db_ingest.py)
├── For each image:
│   ├── Determine category (camera/phone/etc.)
│   ├── Determine destination folder
│   ├── Move or hardlink file
│   └── Update database with new location
└── For each video:
    ├── Same as images
    └── Update database

PHASE 5: VERIFY (db_verify.py)
├── For each file in database:
│   ├── Recalculate SHA256
│   ├── Compare with database
│   └── Log if mismatch
└── If all pass:
    └── Clean up staging directory
```

### Current File Organization

```
scripts/
├── db_import_v012.py          420 lines ❌ VIOLATES (max 200)
├── db_organize.py             435 lines ❌ VIOLATES
├── db_folder.py               369 lines ❌ VIOLATES
├── db_ingest.py               477 lines ❌ VIOLATES
├── db_verify.py               327 lines ❌ VIOLATES
├── immich_integration.py      416 lines ❌ VIOLATES
├── utils.py                   432 lines ❌ VIOLATES (acceptable if utils)
├── normalize.py               500+ lines ❌ VIOLATES
├── logging_config.py          285 lines ❌ VIOLATES
└── [30+ other scripts]
```

---

## 2. LILBITS VIOLATIONS AUDIT

### CRITICAL VIOLATIONS (Must Fix)

#### 1. db_import_v012.py (420 lines)

**VIOLATION:** Monolithic import script doing too much

**Contains:**
- Config loading (1 function)
- Metadata loading (1 function)
- Main import logic with Immich (1 massive function)
- Entry point (1 function)

**Issues:**
- `import_with_immich()` is 200+ lines alone
- Mixes concerns: database ops + file ops + external service integration
- Hard to test individual pieces
- Hard for vibe coder to understand flow

**MUST SPLIT INTO:**
1. `import/config_loader.py` - Load user config (50 lines)
2. `import/metadata_loader.py` - Load & validate metadata (80 lines)
3. `import/file_scanner.py` - Scan source folder for files (100 lines)
4. `import/file_processor.py` - Process single file (import logic) (180 lines)
5. `import/batch_importer.py` - Orchestrate batch import (150 lines)
6. `import/import_cli.py` - CLI entry point (60 lines)

---

#### 2. db_organize.py (435 lines)

**VIOLATION:** Two similar large functions (organize_images, organize_videos)

**Contains:**
- Config loading (1 function)
- Hardware rules loading (1 function)
- EXIF extraction (1 function)
- Video metadata extraction (1 function)
- Hardware categorization (1 function)
- Image organization (1 function - 80 lines)
- Video organization (1 function - 120 lines)
- Entry point (1 function)

**Issues:**
- `organize_images()` and `organize_videos()` are nearly identical
- Code duplication
- Hardware categorization mixed with metadata extraction

**MUST SPLIT INTO:**
1. `organize/exif_extractor.py` - Extract EXIF from images (120 lines)
2. `organize/video_metadata_extractor.py` - Extract ffprobe metadata (120 lines)
3. `organize/hardware_categorizer.py` - Categorize based on make/model (100 lines)
4. `organize/media_organizer.py` - Generic media organization (150 lines)
5. `organize/organize_cli.py` - CLI entry point (60 lines)

---

#### 3. db_folder.py (369 lines)

**VIOLATION:** Database queries mixed with folder creation

**Contains:**
- Config loading (1 function)
- Template loading (1 function)
- Folder creation with DB queries (1 function - 110 lines)
- Create for specific location (1 function)
- Create for all locations (1 function)
- Entry point (1 function)

**Issues:**
- `create_folder_structure()` does DB queries AND filesystem ops
- Hard to test folder creation without database
- Database queries embedded in file operations

**MUST SPLIT INTO:**
1. `folders/folder_planner.py` - Query DB for what folders needed (120 lines)
2. `folders/folder_creator.py` - Actually create folders (100 lines)
3. `folders/folder_manager.py` - Orchestrate for location(s) (100 lines)
4. `folders/folder_cli.py` - CLI entry point (50 lines)

---

#### 4. db_ingest.py (477 lines)

**VIOLATION:** Two nearly identical large functions

**Contains:**
- Config loading (1 function)
- Hardlink detection (1 function)
- Move/link file (1 function)
- Destination folder determination (1 function)
- Image ingest (1 function - 130 lines)
- Video ingest (1 function - 130 lines)
- Entry point (1 function)

**Issues:**
- `ingest_images()` and `ingest_videos()` are 95% identical
- Massive code duplication
- Should be generic

**MUST SPLIT INTO:**
1. `ingest/file_mover.py` - Move or hardlink files (80 lines)
2. `ingest/destination_resolver.py` - Determine destination folder (100 lines)
3. `ingest/media_ingester.py` - Generic media ingest logic (150 lines)
4. `ingest/ingest_cli.py` - CLI entry point (60 lines)

---

#### 5. db_verify.py (327 lines)

**VIOLATION:** Verification + cleanup mixed

**Contains:**
- Config loading (1 function)
- Verify files (1 function - 130 lines)
- Cleanup staging (1 function - 50 lines)
- Entry point (1 function - 100 lines)

**Issues:**
- `verify_files()` handles images + videos + documents in one function
- Should be generic
- Cleanup mixed with verification

**MUST SPLIT INTO:**
1. `verify/file_verifier.py` - Verify single file SHA256 (80 lines)
2. `verify/batch_verifier.py` - Verify all files (120 lines)
3. `verify/staging_cleanup.py` - Clean up staging directory (100 lines)
4. `verify/verify_cli.py` - CLI entry point (50 lines)

---

#### 6. immich_integration.py (416 lines)

**VIOLATION:** Multiple unrelated functions in one module

**Contains:**
- Get Immich adapter (1 function)
- Upload to Immich (1 function)
- Extract GPS from EXIF (1 function)
- Parse GPS coordinate (1 function)
- Get image dimensions (1 function)
- Get video dimensions (1 function)
- Get file size (1 function)
- Process media for Immich (1 function - orchestrator)
- Update location GPS (1 function)

**Issues:**
- 9 different functions with different concerns
- GPS extraction separate from image metadata
- Should be split by responsibility

**MUST SPLIT INTO:**
1. `immich/immich_uploader.py` - Upload to Immich only (100 lines)
2. `immich/gps_extractor.py` - Extract GPS from EXIF (120 lines)
3. `immich/media_dimensions.py` - Extract dimensions (width/height) (100 lines)
4. `immich/media_processor.py` - Orchestrate all metadata extraction (100 lines)

---

#### 7. utils.py (432 lines)

**VIOLATION:** Multiple utility functions (but acceptable as utils module)

**Contains:**
- UUID generation with collision detection (1 function - 50 lines)
- SHA256 calculation (1 function - 40 lines)
- Filename generation (1 function - 30 lines)
- Master JSON filename (1 function - 10 lines)
- SHA256 with short version (1 function - 10 lines)
- File type extensions (3 sets - static data)
- File type determination (1 function - 20 lines)
- SHA256 collision check (1 function - 20 lines)
- Location name collision check (1 function - 20 lines)

**VERDICT:** ACCEPTABLE (related utility functions, well-organized)

**NO SPLIT NEEDED** - This is a proper utility module following LILBITS spirit

---

#### 8. normalize.py (500+ lines)

**VIOLATION:** Multiple normalization functions

**Contains:**
- Load type mapping (1 function)
- Normalize location name (1 function - 50 lines)
- Normalize state code (1 function - 40 lines)
- Normalize location type (1 function - 50 lines)
- Normalize datetime (1 function - 60 lines)
- Normalize extension (1 function - 20 lines)
- Normalize author (1 function - 30 lines)
- Plus helper functions

**MUST SPLIT INTO:**
1. `normalize/text_normalizer.py` - Location names, types (120 lines)
2. `normalize/date_normalizer.py` - Datetime normalization (100 lines)
3. `normalize/validation.py` - State codes, extensions (80 lines)

---

### SUMMARY OF VIOLATIONS

| Script | Current Lines | Violation | Split Into |
|--------|---------------|-----------|------------|
| db_import_v012.py | 420 | ❌ Yes (210%) | 6 scripts |
| db_organize.py | 435 | ❌ Yes (218%) | 5 scripts |
| db_folder.py | 369 | ❌ Yes (185%) | 4 scripts |
| db_ingest.py | 477 | ❌ Yes (239%) | 4 scripts |
| db_verify.py | 327 | ❌ Yes (164%) | 4 scripts |
| immich_integration.py | 416 | ❌ Yes (208%) | 4 scripts |
| utils.py | 432 | ⚠️  Acceptable | Keep as-is |
| normalize.py | 500+ | ❌ Yes (250%) | 3 scripts |
| logging_config.py | 285 | ❌ Yes (143%) | 2 scripts |

**TOTAL:** 8 major violations, need to create **28 new focused scripts**

---

## 3. REWRITE STRATEGY

### Core Principles

1. **LILBITS GOLDEN RULE:**
   - One Script = One Primary Function
   - Maximum 200 lines per script
   - Helper functions allowed (prefix with `_`)
   - Clear responsibility boundaries

2. **SEPARATION OF CONCERNS:**
   - Database operations separate from file operations
   - External service integration separate from core logic
   - Configuration separate from business logic

3. **TESTABILITY:**
   - Each script independently testable
   - Mock-friendly interfaces
   - No hidden dependencies

4. **VIBE CODING FRIENDLY:**
   - Clear, obvious script names
   - Easy to find what you need
   - Simple to modify one thing without breaking others

### Rewrite Approach

**PHASE 1: Create New Structure (Don't break existing)**
- Create new `scripts_v2/` directory
- Build LILBITS-compliant modules
- Test thoroughly

**PHASE 2: Migrate Incrementally**
- Add compatibility layer
- Redirect old scripts to new modules
- Deprecate old scripts

**PHASE 3: Remove Old Code**
- Archive old scripts to `/archive/v010_old/`
- Update documentation
- Update tests

---

## 4. NEW ARCHITECTURE

### Directory Structure

```
scripts_v2/
├── import/
│   ├── __init__.py
│   ├── config_loader.py          # Load user config (50 lines)
│   ├── metadata_loader.py        # Load & validate metadata.json (80 lines)
│   ├── file_scanner.py           # Scan source folder (100 lines)
│   ├── file_processor.py         # Process single file (180 lines)
│   ├── batch_importer.py         # Orchestrate batch (150 lines)
│   └── import_cli.py             # CLI entry point (60 lines)
│
├── organize/
│   ├── __init__.py
│   ├── exif_extractor.py         # Extract EXIF from images (120 lines)
│   ├── video_metadata_extractor.py  # Extract ffprobe metadata (120 lines)
│   ├── hardware_categorizer.py   # Categorize hardware (100 lines)
│   ├── media_organizer.py        # Generic organize (150 lines)
│   └── organize_cli.py           # CLI entry point (60 lines)
│
├── folders/
│   ├── __init__.py
│   ├── folder_planner.py         # Query DB for folders needed (120 lines)
│   ├── folder_creator.py         # Create folders (100 lines)
│   ├── folder_manager.py         # Orchestrate (100 lines)
│   └── folder_cli.py             # CLI entry point (50 lines)
│
├── ingest/
│   ├── __init__.py
│   ├── file_mover.py             # Move or hardlink (80 lines)
│   ├── destination_resolver.py   # Determine destination (100 lines)
│   ├── media_ingester.py         # Generic ingest (150 lines)
│   └── ingest_cli.py             # CLI entry point (60 lines)
│
├── verify/
│   ├── __init__.py
│   ├── file_verifier.py          # Verify single file (80 lines)
│   ├── batch_verifier.py         # Verify all files (120 lines)
│   ├── staging_cleanup.py        # Clean staging (100 lines)
│   └── verify_cli.py             # CLI entry point (50 lines)
│
├── immich/
│   ├── __init__.py
│   ├── immich_uploader.py        # Upload to Immich (100 lines)
│   ├── gps_extractor.py          # Extract GPS (120 lines)
│   ├── media_dimensions.py       # Extract dimensions (100 lines)
│   └── media_processor.py        # Orchestrate metadata (100 lines)
│
├── normalize/
│   ├── __init__.py
│   ├── text_normalizer.py        # Names, types (120 lines)
│   ├── date_normalizer.py        # Datetime (100 lines)
│   └── validation.py             # State codes, extensions (80 lines)
│
├── logging/
│   ├── __init__.py
│   ├── logger_setup.py           # Setup logging (150 lines)
│   └── correlation.py            # Correlation IDs (100 lines)
│
└── utils/
    ├── __init__.py
    ├── uuid_generator.py         # UUID with collision (100 lines)
    ├── sha_calculator.py         # SHA256 calculation (100 lines)
    ├── filename_generator.py     # Generate filenames (100 lines)
    └── file_type_detector.py    # Detect file types (100 lines)
```

### Total Script Count

**Current:** 8 monolithic scripts
**New:** 35 focused scripts (28 new + 7 existing refactored)

**Line Count:**
- Current: 3,686 lines across 8 scripts
- New: 3,700 lines across 35 scripts (similar total, better organized)

**Average Lines Per Script:**
- Current: 461 lines (VIOLATES)
- New: 106 lines (COMPLIANT)

---

## 5. SCRIPT-BY-SCRIPT BREAKDOWN

### 5.1 IMPORT MODULE

#### import/config_loader.py (50 lines)
```python
"""
Load and validate user configuration from user.json.

LILBITS: One Primary Function = Load Config
"""

def load_user_config(config_path: Optional[str] = None) -> dict:
    """
    Load user configuration from user.json.

    Args:
        config_path: Optional path to config file (defaults to user/user.json)

    Returns:
        dict: Validated configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    # Implementation (50 lines total)
    pass
```

**Responsibility:** ONLY load config, nothing else
**Dependencies:** None
**Tests:** 10 test cases (valid, invalid, missing, etc.)

---

#### import/metadata_loader.py (80 lines)
```python
"""
Load and validate import metadata from metadata.json.

LILBITS: One Primary Function = Load & Validate Metadata
"""

def load_metadata(metadata_path: str) -> dict:
    """
    Load import metadata from JSON file.

    Args:
        metadata_path: Path to metadata.json

    Returns:
        dict: Validated metadata

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required fields missing
    """
    # Implementation (80 lines total)
    pass
```

**Responsibility:** ONLY load/validate metadata
**Dependencies:** normalize module for field validation
**Tests:** 15 test cases

---

#### import/file_scanner.py (100 lines)
```python
"""
Scan source folder and collect media files.

LILBITS: One Primary Function = Scan Folder
"""

def scan_source_folder(source_path: Path) -> List[Path]:
    """
    Scan folder recursively for supported media files.

    Args:
        source_path: Root path to scan

    Returns:
        List of file paths found
    """
    # Implementation (100 lines total)
    pass
```

**Responsibility:** ONLY scan and collect file paths
**Dependencies:** utils/file_type_detector for filtering
**Tests:** 12 test cases

---

#### import/file_processor.py (180 lines)
```python
"""
Process single file during import (hash, copy, database insert).

LILBITS: One Primary Function = Process One File
"""

def process_file(
    file_path: Path,
    location_uuid: str,
    staging_dir: Path,
    cursor: sqlite3.Cursor,
    immich_adapter: Optional[Any] = None
) -> dict:
    """
    Process a single file for import.

    Steps:
    1. Calculate SHA256
    2. Check for duplicates
    3. Extract metadata (EXIF/GPS)
    4. Upload to Immich (if available)
    5. Generate filename
    6. Copy to staging
    7. Insert into database

    Args:
        file_path: Source file to import
        location_uuid: Location UUID this file belongs to
        staging_dir: Staging directory
        cursor: Database cursor
        immich_adapter: Optional Immich adapter

    Returns:
        dict: Processing result with status and metadata
    """
    # Implementation (180 lines total)
    pass
```

**Responsibility:** ONLY process ONE file
**Dependencies:** utils, immich, normalize
**Tests:** 20 test cases

---

#### import/batch_importer.py (150 lines)
```python
"""
Orchestrate batch import of multiple files.

LILBITS: One Primary Function = Batch Import Orchestration
"""

def import_batch(
    source_dir: Path,
    metadata: dict,
    config: dict,
    enable_immich: bool = True
) -> dict:
    """
    Import batch of files with transaction safety.

    Args:
        source_dir: Source directory with files
        metadata: Import metadata (location details)
        config: User configuration
        enable_immich: Whether to enable Immich uploads

    Returns:
        dict: Import statistics
    """
    # Implementation (150 lines total)
    pass
```

**Responsibility:** ONLY orchestrate batch, delegates to file_processor
**Dependencies:** file_scanner, file_processor, config_loader
**Tests:** 15 test cases

---

#### import/import_cli.py (60 lines)
```python
"""
CLI entry point for import command.

LILBITS: One Primary Function = CLI Interface
"""

def main():
    """Main CLI entry point for import."""
    # argparse setup
    # Call batch_importer
    # Print results
    pass
```

**Responsibility:** ONLY CLI interface
**Dependencies:** batch_importer
**Tests:** 8 test cases (CLI argument validation)

---

### 5.2 ORGANIZE MODULE

#### organize/exif_extractor.py (120 lines)
```python
"""
Extract EXIF metadata from images using exiftool.

LILBITS: One Primary Function = Extract EXIF
"""

def extract_exif(image_path: Path) -> dict:
    """
    Extract EXIF metadata from image using exiftool.

    Args:
        image_path: Path to image file

    Returns:
        dict: EXIF metadata as JSON
    """
    # Implementation (120 lines total)
    pass
```

**Responsibility:** ONLY extract EXIF, nothing else
**Dependencies:** exiftool (external)
**Tests:** 15 test cases (various image formats)

---

#### organize/video_metadata_extractor.py (120 lines)
```python
"""
Extract video metadata using ffprobe.

LILBITS: One Primary Function = Extract Video Metadata
"""

def extract_video_metadata(video_path: Path) -> dict:
    """
    Extract video metadata using ffprobe.

    Extracts:
    - Format tags (make, model)
    - Stream tags (DJI detection, etc.)
    - Codec info
    - Duration

    Args:
        video_path: Path to video file

    Returns:
        dict: Video metadata
    """
    # Implementation (120 lines total)
    pass
```

**Responsibility:** ONLY extract video metadata
**Dependencies:** ffprobe (external)
**Tests:** 15 test cases (various video formats, DJI drones)

---

#### organize/hardware_categorizer.py (100 lines)
```python
"""
Categorize hardware based on make/model.

LILBITS: One Primary Function = Categorize Hardware
"""

def categorize_hardware(make: str, model: str) -> str:
    """
    Categorize hardware into camera/phone/drone/etc.

    Args:
        make: Device manufacturer
        model: Device model

    Returns:
        str: Category (camera, phone, drone, go_pro, film, other)
    """
    # Implementation (100 lines total)
    pass
```

**Responsibility:** ONLY categorize, no metadata extraction
**Dependencies:** data/camera_hardware.json
**Tests:** 20 test cases (all hardware types)

---

#### organize/media_organizer.py (150 lines)
```python
"""
Generic media organization workflow.

LILBITS: One Primary Function = Organize Media
"""

def organize_media(
    db_path: Path,
    media_type: str,
    location_uuid: Optional[str] = None
) -> int:
    """
    Organize media files (extract metadata and categorize).

    Works for both images and videos (generic).

    Args:
        db_path: Database path
        media_type: 'image' or 'video'
        location_uuid: Optional filter by location

    Returns:
        int: Number of files processed
    """
    # Implementation (150 lines total)
    # Uses exif_extractor OR video_metadata_extractor
    # Uses hardware_categorizer
    # Updates database
    pass
```

**Responsibility:** ONLY orchestrate organization
**Dependencies:** exif_extractor, video_metadata_extractor, hardware_categorizer
**Tests:** 18 test cases

---

#### organize/organize_cli.py (60 lines)
```python
"""
CLI entry point for organize command.

LILBITS: One Primary Function = CLI Interface
"""

def main():
    """Main CLI entry point for organize."""
    pass
```

---

### 5.3 FOLDERS MODULE

#### folders/folder_planner.py (120 lines)
```python
"""
Query database to determine what folders are needed.

LILBITS: One Primary Function = Plan Folders
"""

def plan_folders_for_location(
    db_path: Path,
    location_uuid: str
) -> dict:
    """
    Query database and determine what folders to create.

    Returns folder plan without creating anything.

    Args:
        db_path: Database path
        location_uuid: Location UUID

    Returns:
        dict: Folder plan with counts
            {
                'base_path': Path,
                'photos': {
                    'original_camera': 10,
                    'original_phone': 5
                },
                'videos': {
                    'original_drone': 3
                },
                'documents': {}
            }
    """
    # Implementation (120 lines total)
    pass
```

**Responsibility:** ONLY query DB and plan, don't create
**Dependencies:** Database only
**Tests:** 12 test cases

---

#### folders/folder_creator.py (100 lines)
```python
"""
Create folders on filesystem.

LILBITS: One Primary Function = Create Folders
"""

def create_folders_from_plan(
    base_path: Path,
    folder_plan: dict
) -> List[Path]:
    """
    Create folders on filesystem based on plan.

    Args:
        base_path: Root archive path
        folder_plan: Plan from folder_planner

    Returns:
        List of created paths
    """
    # Implementation (100 lines total)
    pass
```

**Responsibility:** ONLY create folders, no DB queries
**Dependencies:** Filesystem only
**Tests:** 10 test cases

---

#### folders/folder_manager.py (100 lines)
```python
"""
Orchestrate folder creation for location(s).

LILBITS: One Primary Function = Manage Folder Creation
"""

def create_folders_for_location(
    db_path: Path,
    arch_loc: Path,
    location_uuid: str
) -> List[Path]:
    """
    Plan and create folders for a location.

    Args:
        db_path: Database path
        arch_loc: Archive root
        location_uuid: Location UUID

    Returns:
        List of created paths
    """
    # Uses folder_planner
    # Uses folder_creator
    pass
```

**Responsibility:** ONLY orchestrate
**Dependencies:** folder_planner, folder_creator
**Tests:** 8 test cases

---

### 5.4 INGEST MODULE

#### ingest/file_mover.py (80 lines)
```python
"""
Move or hardlink files (cross-device compatible).

LILBITS: One Primary Function = Move File
"""

def move_or_link_file(
    source: Path,
    destination: Path,
    preserve_times: bool = True
) -> str:
    """
    Move or hardlink file (uses hardlink if same device).

    Args:
        source: Source file path
        destination: Destination file path
        preserve_times: Preserve timestamps

    Returns:
        str: Method used ('hardlink' or 'copy')
    """
    # Implementation (80 lines total)
    pass
```

**Responsibility:** ONLY move/link files
**Dependencies:** None (stdlib only)
**Tests:** 12 test cases

---

#### ingest/destination_resolver.py (100 lines)
```python
"""
Determine destination folder based on hardware category.

LILBITS: One Primary Function = Resolve Destination
"""

def resolve_destination(
    category: str,
    media_type: str,
    arch_loc: Path,
    state: str,
    loc_type: str,
    loc_name: str,
    loc_uuid: str
) -> Path:
    """
    Determine destination folder path.

    Args:
        category: Hardware category (camera, phone, drone, etc.)
        media_type: Media type (img, vid, doc)
        arch_loc: Archive root
        state: State code
        loc_type: Location type
        loc_name: Location name
        loc_uuid: Location UUID (12-char)

    Returns:
        Path: Destination folder path
    """
    # Implementation (100 lines total)
    pass
```

**Responsibility:** ONLY determine path, don't move files
**Dependencies:** None
**Tests:** 15 test cases

---

#### ingest/media_ingester.py (150 lines)
```python
"""
Generic media ingestion workflow.

LILBITS: One Primary Function = Ingest Media
"""

def ingest_media(
    db_path: Path,
    arch_loc: Path,
    ingest_dir: Path,
    media_type: str
) -> int:
    """
    Ingest media files from staging to archive.

    Works for images, videos, documents (generic).

    Args:
        db_path: Database path
        arch_loc: Archive root
        ingest_dir: Staging directory
        media_type: 'image', 'video', or 'document'

    Returns:
        int: Number of files ingested
    """
    # Uses destination_resolver
    # Uses file_mover
    # Updates database
    pass
```

**Responsibility:** ONLY orchestrate ingest
**Dependencies:** destination_resolver, file_mover
**Tests:** 18 test cases

---

### 5.5 VERIFY MODULE

#### verify/file_verifier.py (80 lines)
```python
"""
Verify single file SHA256 integrity.

LILBITS: One Primary Function = Verify One File
"""

def verify_file(
    file_path: Path,
    expected_sha256: str
) -> bool:
    """
    Verify file matches expected SHA256.

    Args:
        file_path: File to verify
        expected_sha256: Expected SHA256 hash

    Returns:
        bool: True if matches, False otherwise
    """
    # Implementation (80 lines total)
    pass
```

**Responsibility:** ONLY verify ONE file
**Dependencies:** utils/sha_calculator
**Tests:** 10 test cases

---

#### verify/batch_verifier.py (120 lines)
```python
"""
Verify all files in database.

LILBITS: One Primary Function = Batch Verify
"""

def verify_all_files(
    db_path: Path,
    location_uuid: Optional[str] = None
) -> Tuple[int, List]:
    """
    Verify all files (or files from specific location).

    Args:
        db_path: Database path
        location_uuid: Optional location filter

    Returns:
        Tuple: (verified_count, failed_files)
    """
    # Uses file_verifier
    pass
```

**Responsibility:** ONLY orchestrate verification
**Dependencies:** file_verifier
**Tests:** 12 test cases

---

#### verify/staging_cleanup.py (100 lines)
```python
"""
Clean up staging directory after successful verification.

LILBITS: One Primary Function = Clean Staging
"""

def cleanup_staging(
    ingest_dir: Path,
    dry_run: bool = False
) -> int:
    """
    Clean up staging directory.

    Args:
        ingest_dir: Staging directory path
        dry_run: If True, only report what would be deleted

    Returns:
        int: Number of items removed
    """
    # Implementation (100 lines total)
    pass
```

**Responsibility:** ONLY clean staging
**Dependencies:** None
**Tests:** 8 test cases

---

### 5.6 IMMICH MODULE

#### immich/immich_uploader.py (100 lines)
```python
"""
Upload files to Immich photo management system.

LILBITS: One Primary Function = Upload to Immich
"""

def upload_to_immich(
    file_path: Path,
    immich_adapter: Optional[Any] = None
) -> Optional[str]:
    """
    Upload file to Immich.

    Args:
        file_path: File to upload
        immich_adapter: Optional adapter (auto-created if None)

    Returns:
        str: Asset ID if successful, None otherwise
    """
    # Implementation (100 lines total)
    pass
```

**Responsibility:** ONLY upload to Immich
**Dependencies:** adapters/immich_adapter
**Tests:** 10 test cases

---

#### immich/gps_extractor.py (120 lines)
```python
"""
Extract GPS coordinates from EXIF data.

LILBITS: One Primary Function = Extract GPS
"""

def extract_gps(file_path: Path) -> Optional[Tuple[float, float]]:
    """
    Extract GPS coordinates from media file.

    Args:
        file_path: Media file path

    Returns:
        Tuple: (latitude, longitude) if found, None otherwise
    """
    # Implementation (120 lines total)
    pass
```

**Responsibility:** ONLY extract GPS
**Dependencies:** exiftool (external)
**Tests:** 15 test cases

---

#### immich/media_dimensions.py (100 lines)
```python
"""
Extract media dimensions (width, height, duration).

LILBITS: One Primary Function = Extract Dimensions
"""

def get_media_dimensions(
    file_path: Path,
    file_type: str
) -> dict:
    """
    Get dimensions for image or video.

    Args:
        file_path: Media file
        file_type: 'image' or 'video'

    Returns:
        dict: {'width': int, 'height': int, 'duration': float (video only)}
    """
    # Implementation (100 lines total)
    pass
```

**Responsibility:** ONLY extract dimensions
**Dependencies:** PIL for images, ffprobe for videos
**Tests:** 12 test cases

---

### 5.7 NORMALIZE MODULE

#### normalize/text_normalizer.py (120 lines)
```python
"""
Normalize text (location names, types, etc.).

LILBITS: One Primary Function = Normalize Text
"""

def normalize_location_name(name: str) -> str:
    """Normalize location name."""
    pass

def normalize_location_type(loc_type: str) -> str:
    """Normalize location type."""
    pass
```

**Responsibility:** ONLY text normalization
**Dependencies:** unidecode, libpostal (optional)
**Tests:** 20 test cases

---

#### normalize/date_normalizer.py (100 lines)
```python
"""
Normalize dates and timestamps.

LILBITS: One Primary Function = Normalize Dates
"""

def normalize_datetime(date_input: Any) -> str:
    """
    Normalize datetime to ISO 8601 format.

    Args:
        date_input: Date in various formats

    Returns:
        str: ISO 8601 formatted datetime
    """
    # Implementation (100 lines total)
    pass
```

**Responsibility:** ONLY date normalization
**Dependencies:** dateutil
**Tests:** 15 test cases

---

#### normalize/validation.py (80 lines)
```python
"""
Validate and normalize state codes, extensions, etc.

LILBITS: One Primary Function = Validate
"""

def normalize_state_code(state: str) -> str:
    """Validate and normalize US state code."""
    pass

def normalize_extension(ext: str) -> str:
    """Normalize file extension."""
    pass
```

**Responsibility:** ONLY validation
**Dependencies:** None
**Tests:** 12 test cases

---

### 5.8 UTILS MODULE (Split from current utils.py)

#### utils/uuid_generator.py (100 lines)
```python
"""
Generate UUIDs with collision detection.

LILBITS: One Primary Function = Generate UUID
"""

def generate_uuid(
    cursor: sqlite3.Cursor,
    table_name: str,
    uuid_field: str = 'loc_uuid'
) -> str:
    """
    Generate unique UUID4 with collision detection.

    Returns full UUID (36 chars).
    Caller extracts uuid12 = uuid[:12]
    """
    # Implementation (100 lines total)
    pass
```

---

#### utils/sha_calculator.py (100 lines)
```python
"""
Calculate SHA256 hashes with chunking.

LILBITS: One Primary Function = Calculate SHA256
"""

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 hash of file.

    Returns full hash (64 chars).
    Caller extracts sha12 = sha256[:12]
    """
    # Implementation (100 lines total)
    pass
```

---

#### utils/filename_generator.py (100 lines)
```python
"""
Generate standardized filenames.

LILBITS: One Primary Function = Generate Filename
"""

def generate_filename(
    media_type: str,
    loc_uuid: str,
    sha256: str,
    extension: str,
    sub_uuid: Optional[str] = None
) -> str:
    """
    Generate standardized filename.

    Format: {uuid12}-{sha12}.{ext}
    With sub: {uuid12}-{subuuid12}-{sha12}.{ext}
    """
    # Implementation (100 lines total)
    pass
```

---

#### utils/file_type_detector.py (100 lines)
```python
"""
Detect file type based on extension.

LILBITS: One Primary Function = Detect File Type
"""

def determine_file_type(filepath: Path) -> str:
    """
    Determine if file is image, video, or document.

    Returns: 'image', 'video', 'document', or 'other'
    """
    # Implementation (100 lines total)
    pass
```

---

## 6. IMPLEMENTATION PLAN

### Phase 1: Foundation (Week 1)

**Day 1-2: Utils Module**
1. Create `scripts_v2/utils/` directory
2. Implement:
   - uuid_generator.py
   - sha_calculator.py
   - filename_generator.py
   - file_type_detector.py
3. Write tests (70% coverage minimum)
4. Verify all pass

**Day 3: Normalize Module**
1. Create `scripts_v2/normalize/` directory
2. Implement:
   - text_normalizer.py
   - date_normalizer.py
   - validation.py
3. Write tests
4. Verify all pass

**Day 4-5: Logging Module**
1. Create `scripts_v2/logging/` directory
2. Split logging_config.py into:
   - logger_setup.py
   - correlation.py
3. Write tests
4. Verify all pass

---

### Phase 2: Import Pipeline (Week 2)

**Day 1-2: Import Module**
1. Create `scripts_v2/import/` directory
2. Implement (in order):
   - config_loader.py
   - metadata_loader.py
   - file_scanner.py
3. Write tests for each
4. Verify all pass

**Day 3-4: Import Core**
1. Implement:
   - file_processor.py (most complex)
   - batch_importer.py
2. Write extensive tests
3. Integration test with test data

**Day 5: Import CLI**
1. Implement import_cli.py
2. Test end-to-end import workflow
3. Compare with old db_import_v012.py results

---

### Phase 3: Organization Pipeline (Week 3)

**Day 1-2: Organize Module**
1. Create `scripts_v2/organize/` directory
2. Implement:
   - exif_extractor.py
   - video_metadata_extractor.py
   - hardware_categorizer.py
3. Write tests

**Day 3-4: Organize Core**
1. Implement media_organizer.py (generic)
2. Test with images
3. Test with videos
4. Test with mixed media

**Day 5: Organize CLI**
1. Implement organize_cli.py
2. End-to-end test
3. Compare with old db_organize.py

---

### Phase 4: Folders & Ingest (Week 4)

**Day 1-2: Folders Module**
1. Create `scripts_v2/folders/` directory
2. Implement:
   - folder_planner.py
   - folder_creator.py
   - folder_manager.py
   - folder_cli.py
3. Write tests
4. Test end-to-end

**Day 3-4: Ingest Module**
1. Create `scripts_v2/ingest/` directory
2. Implement:
   - file_mover.py
   - destination_resolver.py
   - media_ingester.py
   - ingest_cli.py
3. Write tests
4. Test with hardlinks and copies

**Day 5: Integration Test**
1. Full pipeline test (import → organize → folders → ingest)
2. Verify against old scripts
3. Fix any issues

---

### Phase 5: Verify & Immich (Week 5)

**Day 1-2: Verify Module**
1. Create `scripts_v2/verify/` directory
2. Implement:
   - file_verifier.py
   - batch_verifier.py
   - staging_cleanup.py
   - verify_cli.py
3. Write tests
4. Test cleanup (dry-run and real)

**Day 3-4: Immich Module**
1. Create `scripts_v2/immich/` directory
2. Implement:
   - immich_uploader.py
   - gps_extractor.py
   - media_dimensions.py
   - media_processor.py
3. Write tests
4. Test with real Immich instance

**Day 5: Final Integration**
1. Full pipeline with Immich
2. Performance testing
3. Fix any issues

---

### Phase 6: Migration & Documentation (Week 6)

**Day 1-2: Compatibility Layer**
1. Create wrapper scripts that redirect old → new
2. Ensure backward compatibility
3. Test old scripts still work

**Day 3: Archive Old Code**
1. Move old scripts to `/archive/v010_old/`
2. Update imports throughout codebase
3. Update CLI entry points

**Day 4: Documentation**
1. Update lilbits.md with new structure
2. Update techguide.md with new architecture
3. Create migration guide

**Day 5: Final Testing**
1. Full system test
2. Performance benchmarks
3. User acceptance testing (vibe coder friendly?)

---

## 7. MIGRATION STRATEGY

### Backward Compatibility

Create wrapper scripts in old locations:

```python
# scripts/db_import_v012.py (wrapper)
"""
Legacy wrapper for db_import_v012.
Redirects to new scripts_v2/import module.
"""
import sys
from scripts_v2.import.import_cli import main

if __name__ == '__main__':
    sys.exit(main())
```

### Gradual Adoption

1. **Week 1-5:** Build new modules alongside old
2. **Week 6:** Add wrappers, deprecate old
3. **Week 7:** Archive old code
4. **Week 8:** Remove wrappers

---

## 8. TESTING REQUIREMENTS

### Coverage Targets

- **v0.1.0 (current):** 70% coverage (enforced)
- **v0.1.0 rewrite:** 75% coverage minimum
- **Critical modules:** 85% coverage (import, verify)

### Test Categories

1. **Unit Tests:** Each function in isolation
2. **Integration Tests:** Module interactions
3. **End-to-End Tests:** Full pipeline
4. **Regression Tests:** Compare old vs new results
5. **Performance Tests:** Ensure no slowdown

### Test Data

Create comprehensive test dataset:
- 100 test images (various formats, with/without EXIF)
- 50 test videos (various formats, DJI drones)
- 20 test documents
- Multiple test locations
- Edge cases (corrupted files, missing EXIF, etc.)

---

## 9. SUCCESS CRITERIA

### Technical

- ✅ All scripts ≤200 lines (LILBITS compliant)
- ✅ One primary function per script
- ✅ 75%+ test coverage
- ✅ Zero regression (same results as old code)
- ✅ Performance within 10% of old code

### User Experience

- ✅ Easier to understand (vibe coder can navigate)
- ✅ Easier to modify (change one thing without breaking others)
- ✅ Clear error messages
- ✅ Same or better CLI interface

### Maintainability

- ✅ Clear responsibility boundaries
- ✅ Easy to add new features
- ✅ Easy to debug issues
- ✅ Well-documented

---

## 10. RISKS & MITIGATION

### Risk 1: Breaking Existing Functionality

**Mitigation:**
- Build alongside old code (don't replace immediately)
- Comprehensive regression tests
- Wrapper scripts for compatibility
- Gradual migration

### Risk 2: Performance Degradation

**Mitigation:**
- Performance benchmarks before/after
- Profile bottlenecks
- Optimize critical paths
- Accept 10% slowdown for cleaner code

### Risk 3: Testing Overhead

**Mitigation:**
- Prioritize critical paths (import, verify)
- Use fixtures for common test scenarios
- Automate test data generation

### Risk 4: User Confusion During Transition

**Mitigation:**
- Clear migration guide
- Backward-compatible wrappers
- Update documentation early
- Communicate changes clearly

---

## 11. CONCLUSION

### Summary

**Current v0.1.0:** 8 monolithic scripts averaging 461 lines each (VIOLATES LILBITS)

**New v0.1.0:** 35 focused scripts averaging 106 lines each (COMPLIANT)

**Benefits:**
1. Easier to understand (vibe coder friendly)
2. Easier to test (small, focused modules)
3. Easier to modify (change one thing safely)
4. Production-ready architecture (scales to millions)

### Next Steps

1. **Review this spec** with developer
2. **Get approval** for approach
3. **Start Phase 1** (Foundation - Week 1)
4. **Iterate** based on feedback

### Timeline

**6 weeks total:**
- Week 1: Foundation (utils, normalize, logging)
- Week 2: Import pipeline
- Week 3: Organization pipeline
- Week 4: Folders & ingest
- Week 5: Verify & Immich
- Week 6: Migration & docs

**Effort:** ~200 hours (5 hours/day, 40 hours/week, 6 weeks)

### Final Thought

This rewrite transforms AUPAT from "works but messy" to **"production-ready, maintainable, vibe-coder-friendly architecture"** that will last 10+ years.

**The LILBITS Golden Rule isn't just about line counts—it's about creating code that humans (especially beginners) can understand, modify, and trust.**

---

**End of Specification**

Ready to begin implementation?
