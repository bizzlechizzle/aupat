# AUPAT Project Overview

## Executive Summary

**Project Name**: AUPAT (Abandoned Upstate Project Archive Tool)

**Purpose**: Bulletproof digital asset management system for organizing, cataloging, and archiving location-based media collections with emphasis on long-term data integrity.

**Current Status**: Planning phase - comprehensive documentation complete, no implementation started.

**Implementation Stage**: Stage 1 - CLI Import Tool (not yet begun)

**Technology Stack**: Python 3, SQLite (JSON1), exiftool, ffprobe

**Core Function**: Import photos, videos, documents, and URLs organized by geographic location with automatic metadata extraction, hardware categorization, deduplication via SHA256, and comprehensive relationship tracking.

---

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [Folder Structure](#folder-structure)
3. [Python Scripts](#python-scripts)
4. [JSON Configuration Files](#json-configuration-files)
5. [Database Design](#database-design)
6. [Data Integrity Features](#data-integrity-features)
7. [Organizational Features](#organizational-features)
8. [Import Pipeline Workflow](#import-pipeline-workflow)
9. [Technology Stack](#technology-stack)
10. [Implementation Roadmap](#implementation-roadmap)

---

## Project Architecture

### Design Philosophy

AUPAT follows bulletproof engineering principles:
- **BPA**: Best practices always (industry standards, proven patterns)
- **BPL**: Bulletproof long-term (code survives years without modification)
- **KISS**: Keep it simple (simplicity over cleverness)
- **FAANG PE**: Production-grade quality for personal/small business use
- **Transaction Safety**: All database operations wrapped in transactions
- **Data Integrity**: SHA256 verification, automated backups, foreign key enforcement

### Staged Development Plan

**Stage 1: CLI Import Tool** (Current Focus)
- Command-line interface for importing media
- Database schema creation and migration
- Metadata extraction and categorization
- File organization and archiving
- Verification and integrity checking
- Status: Documentation complete, implementation not started

**Stage 2: Web Application**
- Web interface for import operations
- Mobile-responsive design
- Location autocomplete
- Batch upload capabilities
- Real-time progress tracking
- Status: Not started

**Stage 3: Dockerization**
- Containerized web application
- Data persistence with volumes
- Automated backups
- Easy deployment
- Status: Not started

**Stage 4: Mobile Application**
- Native mobile app for field import
- Connects to Docker backend
- Offline mode with sync
- GPS integration
- Status: Not started

### Core Workflows

**Import Pipeline** (executed in sequence):
1. db_migrate.py - Create/update database schema
2. db_import.py - Import location and media to staging area
3. db_organize.py - Extract metadata, categorize by hardware
4. db_folder.py - Create organized folder structure
5. db_ingest.py - Move files from staging to archive
6. db_verify.py - Verify SHA256 integrity, cleanup staging
7. db_identify.py - Generate master JSON export per location
8. database_cleanup.py - Maintenance and integrity checks

**Utility Operations**:
- backup.py - Create timestamped database backups
- gen_uuid.py - Generate unique UUID4 identifiers
- gen_sha.py - Generate SHA256 hashes for files
- name.py - Generate standardized file names
- folder.py - Create folder structures

---

## Folder Structure

### Intended Project Structure

```
/Users/bryant/Documents/tools/aupat/
├── scripts/                    # All Python scripts
│   ├── db_migrate.py          # Database schema management
│   ├── db_import.py           # Import media via CLI/web
│   ├── db_organize.py         # Metadata extraction/categorization
│   ├── db_folder.py           # Create folder structure
│   ├── db_ingest.py           # Move files to archive
│   ├── db_verify.py           # Integrity verification
│   ├── db_identify.py         # Generate JSON exports
│   ├── database_cleanup.py    # Maintenance tasks
│   ├── backup.py              # Database backups
│   ├── gen_uuid.py            # UUID generation
│   ├── gen_sha.py             # SHA256 hashing
│   ├── name.py                # File naming
│   ├── folder.py              # Folder creation
│   └── aupat_webapp.py        # Web app (Stage 2)
├── data/                       # All JSON configuration files
│   ├── locations.json         # Locations table schema
│   ├── sub-locations.json     # Sub-locations table schema
│   ├── images.json            # Images table schema
│   ├── videos.json            # Videos table schema
│   ├── documents.json         # Documents table schema
│   ├── urls.json              # URLs table schema
│   ├── versions.json          # Version tracking schema
│   ├── camera_hardware.json   # Hardware classification
│   ├── approved_ext.json      # Special file extensions
│   ├── ignored_ext.json       # Excluded file extensions
│   ├── host_domains.json      # URL domain normalization
│   ├── live_videos.json       # Live photo matching rules
│   ├── folder.json            # Folder structure template
│   └── name.json              # File naming conventions
├── user/                       # User configuration
│   └── user.json              # Database paths and settings
├── venv/                       # Python virtual environment (gitignored)
├── backups/                    # Database backups (gitignored)
├── logs/                       # Application logs (gitignored)
├── logseq/                     # Comprehensive documentation
│   └── pages/                 # All .md specification files
├── claude.md                   # AI collaboration guide
├── claudecode.md               # Development methodology
├── project-overview.md         # This file
├── .gitignore                  # Git exclusions
└── README.md                   # Project README (not yet created)
```

### Current Actual Structure

```
/Users/bryant/Documents/tools/aupat/
├── .git/
├── .gitignore
├── claude.md
├── claudecode.md
├── project-overview.md
└── logseq/
    └── pages/                  # 32+ .md documentation files
```

**Status**: Gap between intended and actual is 100%. Only documentation exists. No scripts/, data/, or user/ folders created yet.

### Archive Folder Structure

Media files are organized in the archive location (specified in user.json) using this structure:

```
{arch_loc}/
└── {state-type}/                      # e.g., "ny-industrial" or "vt-residential"
    └── {location-name}_{loc_uuid8}/   # e.g., "abandoned-factory_a1b2c3d4"
        ├── photos/
        │   ├── original_camera/       # DSLR photos
        │   ├── original_phone/        # Phone photos
        │   ├── original_drone/        # Drone photos
        │   ├── original_go-pro/       # GoPro photos
        │   ├── original_film/         # Scanned film photos
        │   └── original_other/        # Uncategorized photos
        ├── videos/
        │   ├── original_camera/       # DSLR videos
        │   ├── original_phone/        # Phone videos
        │   ├── original_drone/        # Drone videos
        │   ├── original_go-pro/       # GoPro videos
        │   ├── original_dash-cam/     # Dash cam videos
        │   └── original_other/        # Uncategorized videos (incl. live videos)
        └── documents/
            ├── file-extensions/       # Organized by extension (.srt, .xml, etc.)
            ├── zips/                  # ZIP archives
            ├── pdfs/                  # PDF documents
            └── websites/              # URL screenshots/exports
                └── {domain}_{url_uuid8}/
```

---

## Python Scripts

All scripts documented, none implemented yet. Implementation status: 0%.

### Core Import Pipeline Scripts

#### 1. db_migrate.py
**Purpose**: Database schema creation and migration management

**Operations**:
- Creates SQLite database with JSON1 extension
- Creates all tables (locations, sub-locations, images, videos, documents, urls, versions)
- Manages schema version tracking
- Performs schema updates/migrations
- Enforces PRAGMA foreign_keys = ON

**Dependencies**:
- user.json (database paths)
- All table schema JSON files (data/*.json)

**Input**: JSON schema definitions
**Output**: SQLite database with current schema
**Specification**: logseq/pages/db_migrate.py.md

---

#### 2. db_import.py
**Purpose**: Import new locations and associated media via CLI or web interface

**Modes**:
1. Mobile web import (simplified interface)
2. Desktop web import (full interface)
3. Scan existing database (recover from ingest folder)

**Operations**:
- Generate UUID4 for location (verify first 8 chars unique)
- Prompt for location details (name, aka, state, type, sub-type, address)
- Import media files to staging ingest folder
- Generate SHA256 hashes for all files
- Store metadata in database
- Detect collisions (duplicate SHA256)
- Create initial database entries

**Features**:
- Auto-complete for location names, types, states
- Author tracking (imp_author field)
- Timestamp tracking (loc_add, loc_update)
- Collision detection and reporting

**Dependencies**:
- gen_uuid.py (UUID generation)
- gen_sha.py (SHA256 hashing)
- user.json (database and ingest paths)

**Input**: Location data + media files
**Output**: Database entries + files in ingest staging
**Specification**: logseq/pages/db_import.py.md

---

#### 3. db_organize.py
**Purpose**: Extract metadata and categorize imported media

**Operations**:

**For Images**:
1. Extract EXIF metadata using exiftool
2. Identify hardware from EXIF Make/Model fields
3. Categorize as: DSLR, Phone, Drone, GoPro, Film, Other
4. Store hardware info in img_hardware (JSON1 field)
5. Set hardware flags (original, camera, phone, drone, go_pro, film, other)
6. Match live photos to live videos by filename/location

**For Videos**:
1. Extract metadata using ffprobe
2. Identify hardware from Make/Model tags
3. Categorize as: Camera, Phone, Drone, GoPro, Dash Cam, Other
4. Store hardware info in vid_hardware (JSON1 field)
5. Set hardware flags (original, camera, drone, phone, go_pro, dash_cam, other)
6. Match to live photos if applicable

**For Documents**:
1. Extract file extension
2. Process approved extensions (from approved_ext.json)
3. Match .srt/.xml files to images/videos by name
4. Set relationships (docs_img field for images, vid_docs/img_docs for videos)

**For URLs**:
1. Parse domain from URL
2. Normalize domain using host_domains.json rules
3. Generate url_uuid for tracking

**Hardware Detection Rules**:
- DSLR: Canon, Nikon, Sony, Fujifilm, Olympus, Pentax, Leica, Panasonic, Hasselblad
- Drone: DJI, Autel, Parrot, Skydio, Yuneec
- Phone: iPhone, Samsung, Google, OnePlus, Huawei, Xiaomi, etc.
- GoPro: GoPro models
- Dash Cam: Vantrue, BlackVue, Garmin, Nextbase, etc.
- Film: Marked manually or via metadata

**Dependencies**:
- exiftool (external binary)
- ffprobe (external binary)
- camera_hardware.json (hardware classification)
- live_videos.json (live photo matching rules)
- approved_ext.json (special extension handling)
- ignored_ext.json (excluded extensions)
- host_domains.json (URL domain normalization)

**Input**: Database entries with files in ingest staging
**Output**: Updated database with metadata and categorization
**Specification**: logseq/pages/db_organize.py.md

---

#### 4. db_folder.py
**Purpose**: Create organized folder structure for location

**Operations**:
1. Read folder structure from folder.json
2. Create state-type directory (e.g., "ny-industrial")
3. Create location directory: {location-name}_{loc_uuid8}
4. Create subdirectories:
   - photos/original_camera, original_phone, original_drone, original_go-pro, original_film, original_other
   - videos/original_camera, original_phone, original_drone, original_go-pro, original_dash-cam, original_other
   - documents/file-extensions, zips, pdfs
   - documents/websites/{domain}_{url_uuid8} (for each URL)
5. Verify all directories created successfully

**Dependencies**:
- folder.json (folder structure template)
- user.json (archive location path)

**Input**: Location data from database
**Output**: Created folder structure in archive location
**Specification**: logseq/pages/db_folder.py.md

---

#### 5. db_ingest.py
**Purpose**: Move files from staging to organized archive structure

**Operations**:

**File Movement Strategy**:
- Same disk: Use hardlinks (preserves original, saves space)
- Different disk: Copy files (slower but necessary)
- Always preserve original timestamps

**For Images**:
1. Generate standardized filename using name.py:
   - Format: `{loc_uuid8}-img_{sha8}.{ext}` or `{loc_uuid8}-{sub_uuid8}-img_{sha8}.{ext}`
2. Determine destination based on hardware category
3. Move/hardlink to appropriate photos/original_* folder
4. Update img_loc, img_name in database
5. Verify file exists at destination

**For Videos**:
1. Generate standardized filename using name.py:
   - Format: `{loc_uuid8}-vid_{sha8}.{ext}` or `{loc_uuid8}-{sub_uuid8}-vid_{sha8}.{ext}`
2. Determine destination based on hardware category
3. Special case: Live videos go to videos/original_other
4. Move/hardlink to appropriate videos/original_* folder
5. Update vid_loc, vid_name in database
6. Verify file exists at destination

**For Documents**:
1. Generate standardized filename using name.py:
   - Format: `{loc_uuid8}-doc_{sha8}.{ext}` or `{loc_uuid8}-{sub_uuid8}-doc_{sha8}.{ext}`
2. Move to documents/file-extensions/{ext}/ or documents/zips/ or documents/pdfs/
3. Update doc_loc, doc_name in database
4. Verify file exists at destination

**For URLs**:
- Store URL in database with domain and url_uuid
- Create placeholder in documents/websites/{domain}_{url_uuid8}/
- Future: Screenshot or archive page content

**Dependencies**:
- name.py (file naming)
- user.json (paths)
- Database (location and file metadata)

**Input**: Files in ingest staging + database metadata
**Output**: Files in organized archive + updated database locations
**Specification**: logseq/pages/db_ingest.py.md

---

#### 6. db_verify.py
**Purpose**: Verify successful import and cleanup staging

**Operations**:
1. For each file moved to archive:
   - Calculate SHA256 of file at new location
   - Compare to SHA256 stored in database
   - Verify match (integrity check)
2. If all files verified successfully:
   - Delete original files from ingest staging folder
   - Delete empty staging folder
3. If any verification fails:
   - Log error with details
   - Do NOT delete staging files
   - Report failure to user
4. Update verification timestamp in database

**Safety Rules**:
- NEVER delete source files until verification passes
- If verification fails, preserve staging for manual recovery
- Log all verification results
- Atomic operation: either all files verified and deleted, or none

**Dependencies**:
- gen_sha.py (SHA256 verification)
- user.json (paths)
- Database (file locations and SHA256 values)

**Input**: Files in archive + original staging files
**Output**: Verified archive, cleaned staging, updated database
**Specification**: logseq/pages/db_verify.py.md

---

#### 7. db_identify.py
**Purpose**: Generate master JSON export file for each location

**Operations**:
1. For each location in database:
2. Query all related data:
   - Location details (name, state, type, etc.)
   - All sub-locations
   - All images with metadata and relationships
   - All videos with metadata and relationships
   - All documents with relationships
   - All URLs
3. Compile into comprehensive JSON structure
4. Write to file: `{loc_uuid8}_master.json`
5. Store in location's archive folder
6. Update json_update timestamp in database

**JSON Structure**:
```json
{
  "location": {
    "loc_name": "...",
    "loc_uuid": "...",
    ...
  },
  "sub_locations": [...],
  "images": [...],
  "videos": [...],
  "documents": [...],
  "urls": [...],
  "metadata": {
    "export_date": "...",
    "total_images": 123,
    "total_videos": 45,
    ...
  }
}
```

**Dependencies**:
- Database (all tables)
- user.json (export location)

**Input**: Location data from database
**Output**: Master JSON export file per location
**Specification**: logseq/pages/db_identify.py.md

---

#### 8. database_cleanup.py
**Purpose**: Database maintenance and integrity checks

**Operations**:
1. Run PRAGMA integrity_check on database
2. Verify all foreign key relationships
3. Check for orphaned records (files without locations, etc.)
4. Clean up old backups:
   - Keep first backup of each day
   - Keep last backup of each day
   - Delete intermediate backups
5. Vacuum database to reclaim space
6. Update statistics
7. Generate maintenance report

**Backup Retention Policy**:
- Keep all backups from last 7 days
- For older: keep first and last backup of each day only
- Never delete backups less than 24 hours old

**Dependencies**:
- user.json (database and backup paths)
- Database

**Input**: Database and backup folder
**Output**: Maintained database, cleaned backups, maintenance report
**Specification**: logseq/pages/database_cleanup.py.md (referred to as "database cleanup" in docs)

---

### Utility Scripts

#### 9. backup.py
**Purpose**: Create timestamped database backups

**Operations**:
1. Generate timestamp: YYYY-MM-DD_HH-MM-SS
2. Create backup filename: `{db_name}-{timestamp}.db`
3. Copy database to backup folder using SQLite backup API
4. Verify backup is newer than previous backup (size/modified time)
5. Log backup creation
6. Return backup path

**Safety**:
- Use SQLite backup API (not file copy) to ensure consistency
- Verify backup completed successfully before confirming
- Never overwrite existing backups

**Dependencies**:
- user.json (database and backup paths)

**Input**: Current database
**Output**: Timestamped backup file
**Specification**: logseq/pages/backup.py.md

---

#### 10. gen_uuid.py
**Purpose**: Generate unique UUID4 identifiers

**Operations**:
1. Generate UUID4 using Python uuid module
2. Extract first 8 characters (uuid8)
3. Query database to check if uuid8 already exists in relevant table
4. If collision detected, generate new UUID and retry
5. Return full UUID and uuid8
6. Log any collisions (should be extremely rare)

**Usage**:
- Location IDs (loc_uuid, loc_uuid8)
- Sub-location IDs (sub_uuid, sub_uuid8)
- URL IDs (url_uuid)

**Collision Handling**:
- Probability of collision with 8 hex chars: ~1 in 4 billion
- If collision occurs, regenerate (don't increment)
- Log collision for monitoring

**Dependencies**:
- Database (to check for collisions)

**Input**: Table name and field to check
**Output**: UUID (full) and UUID8 (first 8 chars)
**Specification**: logseq/pages/gen_uuid.py.md

---

#### 11. gen_sha.py
**Purpose**: Generate SHA256 hashes for files

**Operations**:
1. Open file in binary read mode
2. Read file in chunks (e.g., 65536 bytes) for memory efficiency
3. Update SHA256 hash with each chunk
4. Return full SHA256 hash (64 hex chars)
5. Also return SHA8 (first 8 chars) for compact references

**Usage**:
- Image file hashing (img_sha256, img_sha8)
- Video file hashing (vid_sha256, vid_sha8)
- Document file hashing (doc_sha, doc_sha8)
- Deduplication (detect identical files)
- Integrity verification (compare before/after move)

**Performance**:
- Chunk-based reading for large files (doesn't load entire file in memory)
- Efficient for files of any size

**Dependencies**: None (uses Python hashlib standard library)

**Input**: File path
**Output**: SHA256 (full 64 chars) and SHA8 (first 8 chars)
**Specification**: logseq/pages/gen_sha.py.md

---

#### 12. name.py
**Purpose**: Generate standardized file names

**Operations**:

**File Naming Patterns** (from name.json):

**Images**:
- Without sub-location: `{loc_uuid8}-img_{sha8}.{ext}`
- With sub-location: `{loc_uuid8}-{sub_uuid8}-img_{sha8}.{ext}`
- Example: `a1b2c3d4-img_e5f6g7h8.jpg`
- Example with sub: `a1b2c3d4-i9j0k1l2-img_e5f6g7h8.jpg`

**Videos**:
- Without sub-location: `{loc_uuid8}-vid_{sha8}.{ext}`
- With sub-location: `{loc_uuid8}-{sub_uuid8}-vid_{sha8}.{ext}`
- Example: `a1b2c3d4-vid_e5f6g7h8.mp4`

**Documents**:
- Without sub-location: `{loc_uuid8}-doc_{sha8}.{ext}`
- With sub-location: `{loc_uuid8}-{sub_uuid8}-doc_{sha8}.{ext}`
- Example: `a1b2c3d4-doc_e5f6g7h8.pdf`

**Function Signature**:
```python
def generate_filename(
    media_type: str,      # "image", "video", "document"
    loc_uuid8: str,       # First 8 chars of location UUID
    sha8: str,            # First 8 chars of SHA256
    extension: str,       # File extension (e.g., "jpg")
    sub_uuid8: str = None # Optional: first 8 chars of sub-location UUID
) -> str:
    """Generate standardized filename."""
```

**Dependencies**:
- name.json (naming patterns)

**Input**: Media type, UUIDs, SHA, extension
**Output**: Standardized filename string
**Specification**: logseq/pages/name.py.md

---

#### 13. folder.py
**Purpose**: Create folder structures based on configuration

**Operations**:
1. Read folder structure definition from folder.json
2. Parse template with variables: {state}, {type}, {location_name}, {loc_uuid8}, etc.
3. Create all directories in hierarchy
4. Set appropriate permissions
5. Verify all directories created successfully
6. Return list of created directories

**Folder Categories** (from folder.json):

**Photos**:
- original_camera (DSLR)
- original_phone
- original_drone
- original_go-pro
- original_film
- original_other

**Videos**:
- original_camera (DSLR)
- original_phone
- original_drone
- original_go-pro
- original_dash-cam
- original_other

**Documents**:
- file-extensions (subfolders per extension)
- zips
- pdfs
- websites (subfolders per URL)

**Dependencies**:
- folder.json (folder structure template)

**Input**: Location data, folder template
**Output**: Created directory structure
**Specification**: logseq/pages/folder.py.md (referred to as "folder script" in docs)

---

### Future Scripts

#### 14. aupat_webapp.py (Stage 2)
**Purpose**: Web application for import and management

**Planned Features**:
- Web-based import interface
- Location autocomplete
- Batch upload
- Progress tracking
- Database browsing
- Search functionality

**Status**: Not started (Stage 2 development)
**Specification**: logseq/pages/web_interface.md (basic outline only)

---

## JSON Configuration Files

All JSON files documented, none created yet. Implementation status: 0%.

### Database Schema Definitions

#### 1. locations.json
**Purpose**: Main locations table schema

**Table Name**: locations

**Key Fields**:
- `loc_name` (TEXT, NOT NULL) - Location name (normalized: unidecode, titlecase, libpostal)
- `aka_name` (TEXT) - Alternate/known-as name
- `state` (TEXT, NOT NULL) - US state abbreviation (lowercase)
- `type` (TEXT, NOT NULL) - Location type (e.g., industrial, residential, commercial)
- `sub_type` (TEXT) - Sub-type (e.g., factory, warehouse)
- `loc_uuid` (TEXT, PRIMARY KEY) - UUID4 for location
- `loc_uuid8` (TEXT, UNIQUE, NOT NULL) - First 8 chars of UUID (for compact reference)
- `org_loc` (TEXT) - Original staging location
- `loc_loc` (TEXT) - Current archive location
- `loc_add` (TEXT) - Date/time added (ISO 8601)
- `loc_update` (TEXT) - Date/time last updated (ISO 8601)
- `imp_author` (TEXT) - Author who imported
- `json_update` (TEXT) - Date/time JSON export last generated

**Normalization Rules**:
- loc_name: unidecode → titlecase → libpostal (address parsing)
- state: lowercase, validated against US state list
- type/sub_type: lowercase, validated against approved list

**Indexes**:
- PRIMARY KEY on loc_uuid
- UNIQUE on loc_uuid8
- INDEX on (state, type) for common queries

**Specification**: logseq/pages/locations.json.md

---

#### 2. sub-locations.json
**Purpose**: Sub-locations within main locations

**Table Name**: sub-locations (or sub_locations)

**Key Fields**:
- `sub_name` (TEXT, NOT NULL) - Sub-location name
- `sub_uuid` (TEXT, PRIMARY KEY) - UUID4 for sub-location
- `sub_uuid8` (TEXT, UNIQUE, NOT NULL) - First 8 chars of UUID
- `loc_uuid` (TEXT, FOREIGN KEY → locations.loc_uuid) - Parent location
- `loc_uuid8` (TEXT, NOT NULL) - Parent location UUID8 (for reference)
- `org_loc` (TEXT) - Original location
- `loc_loc` (TEXT) - Current location
- `loc_add` (TEXT) - Date/time added
- `loc_update` (TEXT) - Date/time updated
- `imp_author` (TEXT) - Import author

**Foreign Keys**:
- loc_uuid REFERENCES locations(loc_uuid) ON DELETE CASCADE

**Use Cases**:
- Large locations with distinct areas (e.g., Building A, Building B)
- Different sections of same property

**Specification**: logseq/pages/sub-locations.json.md

---

#### 3. images.json
**Purpose**: Images table schema

**Table Name**: images

**Key Fields**:

**Identity**:
- `img_name` (TEXT, NOT NULL) - Current filename
- `img_loc` (TEXT, NOT NULL) - Current file path
- `img_sha256` (TEXT, UNIQUE, NOT NULL) - Full SHA256 hash (64 chars)
- `img_sha8` (TEXT, NOT NULL) - First 8 chars of SHA256

**Hardware Categorization** (boolean flags):
- `original` (INTEGER) - Original unprocessed file
- `camera` (INTEGER) - DSLR camera
- `phone` (INTEGER) - Smartphone
- `drone` (INTEGER) - Drone camera
- `go_pro` (INTEGER) - GoPro action camera
- `film` (INTEGER) - Scanned film
- `other` (INTEGER) - Uncategorized

**Metadata** (JSON1 fields):
- `exiftool_hardware` (TEXT) - Raw EXIF data from exiftool
- `img_hardware` (TEXT, JSON1) - Parsed hardware info: {make, model, category}

**Relationships**:
- `loc_uuid` (TEXT, FOREIGN KEY → locations.loc_uuid) - Parent location
- `sub_uuid` (TEXT, FOREIGN KEY → sub-locations.sub_uuid, nullable) - Parent sub-location
- `img_docs` (TEXT, JSON1) - Related document SHA256s (array)
- `img_vids` (TEXT, JSON1) - Related video SHA256s (array, for live photos)

**Tracking**:
- `img_loco` (TEXT) - Original location before import
- `img_nameo` (TEXT) - Original filename
- `img_add` (TEXT) - Date/time added
- `img_update` (TEXT) - Date/time updated
- `imp_author` (TEXT) - Import author

**Hardware Detection**:
- Uses EXIF Make and Model fields
- Matched against camera_hardware.json rules
- DSLR: Canon, Nikon, Sony, Fujifilm, Olympus, Pentax, Leica, Panasonic, Hasselblad
- Drone: DJI, Autel, Parrot, Skydio, Yuneec
- Phone: iPhone, Samsung, Google, OnePlus, Huawei, Xiaomi, etc.
- GoPro: GoPro models
- Film: Manual designation or specific metadata

**Foreign Keys**:
- loc_uuid REFERENCES locations(loc_uuid) ON DELETE CASCADE
- sub_uuid REFERENCES sub-locations(sub_uuid) ON DELETE SET NULL

**Specification**: logseq/pages/images.json.md

---

#### 4. videos.json
**Purpose**: Videos table schema

**Table Name**: videos

**Key Fields**:

**Identity**:
- `vid_name` (TEXT, NOT NULL) - Current filename
- `vid_loc` (TEXT, NOT NULL) - Current file path
- `vid_sha256` (TEXT, UNIQUE, NOT NULL) - Full SHA256 hash
- `vid_sha8` (TEXT, NOT NULL) - First 8 chars of SHA256

**Hardware Categorization** (boolean flags):
- `original` (INTEGER) - Original unprocessed file
- `camera` (INTEGER) - DSLR/camera video
- `drone` (INTEGER) - Drone video
- `phone` (INTEGER) - Smartphone video
- `go_pro` (INTEGER) - GoPro video
- `dash_cam` (INTEGER) - Dash cam video
- `other` (INTEGER) - Uncategorized (includes live videos)

**Metadata** (JSON1 fields):
- `ffmpeg_hardware` (TEXT) - Raw metadata from ffprobe
- `vid_hardware` (TEXT, JSON1) - Parsed hardware info: {make, model, category}

**Relationships**:
- `loc_uuid` (TEXT, FOREIGN KEY → locations.loc_uuid) - Parent location
- `sub_uuid` (TEXT, FOREIGN KEY → sub-locations.sub_uuid, nullable) - Parent sub-location
- `vid_docs` (TEXT, JSON1) - Related document SHA256s (array)
- `vid_imgs` (TEXT, JSON1) - Related image SHA256s (array, for live videos)

**Tracking**:
- `img_loc_o` (TEXT) - Original location (typo in schema? should be vid_loc_o)
- `img_name_o` (TEXT) - Original filename (typo in schema? should be vid_name_o)
- `img_add` (TEXT) - Date/time added (typo? should be vid_add)
- `img_update` (TEXT) - Date/time updated (typo? should be vid_update)
- `imp_author` (TEXT) - Import author

**Hardware Detection**:
- Uses ffprobe to extract Make and Model tags
- Matched against camera_hardware.json rules
- Live videos detected by matching to images via live_videos.json rules

**Foreign Keys**:
- loc_uuid REFERENCES locations(loc_uuid) ON DELETE CASCADE
- sub_uuid REFERENCES sub-locations(sub_uuid) ON DELETE SET NULL

**Note**: Schema has field name inconsistencies (img_* instead of vid_*) - should be corrected during implementation.

**Specification**: logseq/pages/videos.json.md

---

#### 5. documents.json
**Purpose**: Documents table schema

**Table Name**: documents

**Key Fields**:

**Identity**:
- `doc_name` (TEXT, NOT NULL) - Current filename
- `doc_loc` (TEXT, NOT NULL) - Current file path
- `doc_ext` (TEXT, NOT NULL) - File extension
- `doc_sha` (TEXT, UNIQUE, NOT NULL) - Full SHA256 hash
- `doc_sha8` (TEXT, NOT NULL) - First 8 chars of SHA256

**Relationships**:
- `loc_uuid` (TEXT, FOREIGN KEY → locations.loc_uuid) - Parent location
- `sub_uuid` (TEXT, FOREIGN KEY → sub-locations.sub_uuid, nullable) - Parent sub-location
- `docs_img` (TEXT, JSON1) - Related image SHA256s (array)

**Tracking**:
- `doc_loco` (TEXT) - Original location
- `doc_nameo` (TEXT) - Original filename
- `doc_add` (TEXT) - Date/time added
- `doc_update` (TEXT) - Date/time updated
- `imp_author` (TEXT) - Import author

**Document Types**:
- .srt files - Subtitle files (match to videos by filename)
- .xml files - Metadata files (match to images/videos by filename)
- .pdf files - PDF documents
- .zip files - Archive files
- Other extensions as specified in approved_ext.json

**Foreign Keys**:
- loc_uuid REFERENCES locations(loc_uuid) ON DELETE CASCADE
- sub_uuid REFERENCES sub-locations(sub_uuid) ON DELETE SET NULL

**Specification**: logseq/pages/documents.json.md

---

#### 6. urls.json
**Purpose**: URLs table schema

**Table Name**: urls

**Key Fields**:

**Identity**:
- `url` (TEXT, NOT NULL) - Full URL
- `domain` (TEXT, NOT NULL) - Normalized domain
- `url_uuid` (TEXT, PRIMARY KEY) - UUID4 for URL
- `url_uuid8` (TEXT, NOT NULL) - First 8 chars of UUID
- `url_loc` (TEXT) - Storage location for archived content

**Relationships**:
- `loc_uuid` (TEXT, FOREIGN KEY → locations.loc_uuid) - Parent location
- `sub_uuid` (TEXT, FOREIGN KEY → sub-locations.sub_uuid, nullable) - Parent sub-location

**Tracking**:
- `url_add` (TEXT) - Date/time added
- `url_update` (TEXT) - Date/time updated
- `imp_author` (TEXT) - Import author

**Domain Normalization**:
- Uses host_domains.json rules
- Handles complex hosting (SmugMug, Blogspot, WordPress, GitHub Pages, etc.)
- Extracts canonical domain for organization

**Use Cases**:
- Website references for locations
- Online photo galleries
- Blog posts
- News articles
- Social media posts

**Foreign Keys**:
- loc_uuid REFERENCES locations(loc_uuid) ON DELETE CASCADE
- sub_uuid REFERENCES sub-locations(sub_uuid) ON DELETE SET NULL

**Specification**: logseq/pages/urls.json.md

---

#### 7. versions.json
**Purpose**: Version tracking table schema

**Table Name**: versions

**Key Fields**:
- `modules` (TEXT, PRIMARY KEY) - Module/component name
- `version` (TEXT, NOT NULL) - Version number (semantic versioning)
- `ver_updated` (TEXT, NOT NULL) - Date/time version updated

**Tracked Components**:
- Database schema version
- Each Python script version
- Each JSON configuration file version
- Application version

**Use Cases**:
- Schema migration tracking
- Compatibility checking
- Rollback support
- Change history

**Example Entries**:
```
modules          | version | ver_updated
-----------------|---------|-----------------
database_schema  | 1.0.0   | 2025-01-15T10:30:00Z
db_migrate       | 1.0.0   | 2025-01-15T10:30:00Z
locations.json   | 1.0.0   | 2025-01-15T10:30:00Z
```

**Specification**: logseq/pages/versions.json.md

---

### Configuration Reference Files

#### 8. camera_hardware.json
**Purpose**: Hardware classification rules

**Structure**:
```json
{
  "DSLR": {
    "makes": ["Canon", "Nikon", "Sony", "Fujifilm", "Olympus", "Pentax", "Leica", "Panasonic", "Hasselblad"],
    "models": ["EOS", "D850", "A7", ...]
  },
  "Drone": {
    "makes": ["DJI", "Autel", "Parrot", "Skydio", "Yuneec"],
    "models": ["Mavic", "Phantom", "Mini", "Air", ...]
  },
  "Phone": {
    "makes": ["Apple", "Samsung", "Google", "OnePlus", "Huawei", "Xiaomi", ...],
    "models": ["iPhone", "Galaxy", "Pixel", ...]
  },
  "GoPro": {
    "makes": ["GoPro"],
    "models": ["HERO", ...]
  },
  "DashCam": {
    "makes": ["Vantrue", "BlackVue", "Garmin", "Nextbase", ...],
    "models": [...]
  }
}
```

**Matching Logic**:
1. Extract Make and Model from EXIF (images) or ffprobe (videos)
2. Check Make against each category's makes list (case-insensitive contains)
3. If make matches, check model against models list
4. Assign to first matching category
5. If no match, assign to "Other"

**Specification**: logseq/pages/camera_hardware.json.md

---

#### 9. approved_ext.json
**Purpose**: Special handling rules for file extensions

**Structure**:
```json
{
  ".srt": {
    "type": "subtitle",
    "match_to": "video",
    "match_method": "filename",
    "description": "Subtitle files - match to videos by name"
  },
  ".xml": {
    "type": "metadata",
    "match_to": ["image", "video"],
    "match_method": "filename",
    "description": "Metadata files - match to images/videos by name"
  },
  ...
}
```

**Use Cases**:
- .srt files → Match to videos by filename
- .xml files → Match to images or videos by filename
- Sidecar files → Associate with main media files

**Specification**: logseq/pages/approved_ext.json.md

---

#### 10. ignored_ext.json
**Purpose**: File extensions to exclude from import

**Structure**:
```json
{
  ".lrf": {
    "condition": "filename contains 'DJI'",
    "reason": "DJI LRF files (drone log files not needed)"
  },
  ".thm": {
    "reason": "Thumbnail files (redundant)"
  },
  ...
}
```

**Use Cases**:
- Exclude cache files
- Exclude system files
- Exclude temporary files
- Exclude redundant sidecar files

**Specification**: logseq/pages/ignored_ext.json.md

---

#### 11. host_domains.json
**Purpose**: Domain normalization for URL cleaning

**Structure**:
```json
{
  "SmugMug": {
    "pattern": "*.smugmug.com",
    "extract": "subdomain",
    "example": "username.smugmug.com → username"
  },
  "Blogspot": {
    "pattern": "*.blogspot.com",
    "extract": "subdomain",
    "example": "myblog.blogspot.com → myblog"
  },
  "WordPress": {
    "pattern": "*.wordpress.com",
    "extract": "subdomain"
  },
  "GitHub Pages": {
    "pattern": "*.github.io",
    "extract": "subdomain"
  },
  ...
}
```

**Use Cases**:
- Normalize complex hosting platforms
- Extract meaningful identifiers
- Organize URLs by provider

**Specification**: logseq/pages/host_domains.json.md

---

#### 12. live_videos.json
**Purpose**: Rules for matching live photos to live videos

**Matching Logic**:
1. Compare img_loco (original image location) with vid_loco (original video location)
2. Compare img_nameo (original image name) with vid_nameo (original video name)
3. If location matches and names are similar (e.g., IMG_1234.JPG vs IMG_1234.MOV):
   - Mark as live photo/video pair
   - Add image SHA256 to video's vid_imgs field
   - Add video SHA256 to image's img_vids field
   - Categorize video as "other" (live videos go to original_other folder)

**iPhone Live Photo Pattern**:
- Photo: IMG_1234.HEIC
- Video: IMG_1234.MOV
- Same prefix, different extensions

**Structure**:
```json
{
  "patterns": [
    {
      "photo_pattern": "IMG_*.HEIC",
      "video_pattern": "IMG_*.MOV",
      "match_method": "prefix"
    },
    ...
  ]
}
```

**Specification**: logseq/pages/live_videos.json.md

---

#### 13. folder.json
**Purpose**: Folder structure template

**Structure**:
```json
{
  "archive_root": "{arch_loc}",
  "location_structure": {
    "state_type": "{state}-{type}",
    "location": "{location_name}_{loc_uuid8}",
    "subdirectories": {
      "photos": [
        "original_camera",
        "original_phone",
        "original_drone",
        "original_go-pro",
        "original_film",
        "original_other"
      ],
      "videos": [
        "original_camera",
        "original_phone",
        "original_drone",
        "original_go-pro",
        "original_dash-cam",
        "original_other"
      ],
      "documents": [
        "file-extensions",
        "zips",
        "pdfs",
        "websites"
      ]
    }
  }
}
```

**Template Variables**:
- {arch_loc} - Archive root from user.json
- {state} - State abbreviation (lowercase)
- {type} - Location type
- {location_name} - Location name (normalized)
- {loc_uuid8} - First 8 chars of location UUID

**Specification**: logseq/pages/folder.json.md

---

#### 14. name.json
**Purpose**: File naming conventions

**Structure**:
```json
{
  "image": {
    "without_sub": "{loc_uuid8}-img_{sha8}.{ext}",
    "with_sub": "{loc_uuid8}-{sub_uuid8}-img_{sha8}.{ext}"
  },
  "video": {
    "without_sub": "{loc_uuid8}-vid_{sha8}.{ext}",
    "with_sub": "{loc_uuid8}-{sub_uuid8}-vid_{sha8}.{ext}"
  },
  "document": {
    "without_sub": "{loc_uuid8}-doc_{sha8}.{ext}",
    "with_sub": "{loc_uuid8}-{sub_uuid8}-doc_{sha8}.{ext}"
  }
}
```

**Variables**:
- {loc_uuid8} - First 8 chars of location UUID
- {sub_uuid8} - First 8 chars of sub-location UUID (if applicable)
- {sha8} - First 8 chars of file SHA256
- {ext} - File extension (lowercase)

**Examples**:
- Image without sub: `a1b2c3d4-img_e5f6g7h8.jpg`
- Image with sub: `a1b2c3d4-i9j0k1l2-img_e5f6g7h8.jpg`
- Video: `a1b2c3d4-vid_e5f6g7h8.mp4`
- Document: `a1b2c3d4-doc_e5f6g7h8.pdf`

**Specification**: logseq/pages/name.json.md

---

### User Configuration

#### 15. user.json
**Purpose**: User configuration and database paths

**Location**: user/user.json

**Structure**:
```json
{
  "db_name": "aupat.db",
  "db_loc": "/path/to/database/aupat.db",
  "db_backup": "/path/to/backups/",
  "db_ingest": "/path/to/ingest/staging/",
  "arch_loc": "/path/to/archive/"
}
```

**Fields**:
- `db_name` - Database filename
- `db_loc` - Full path to database file
- `db_backup` - Directory for database backups
- `db_ingest` - Staging directory for incoming files
- `arch_loc` - Root directory for organized archive

**Example**:
```json
{
  "db_name": "aupat.db",
  "db_loc": "/Users/bryant/Documents/aupat_database/aupat.db",
  "db_backup": "/Users/bryant/Documents/aupat_database/backups/",
  "db_ingest": "/Users/bryant/Documents/aupat_database/ingest/",
  "arch_loc": "/Volumes/Archive/AUPAT/"
}
```

**Specification**: logseq/pages/user.json.md

---

## Database Design

### Database Technology

**Engine**: SQLite 3
**Extensions**: JSON1 (for JSON column support)
**Connection Settings**:
- PRAGMA foreign_keys = ON (always enforce foreign keys)
- PRAGMA journal_mode = WAL (write-ahead logging for concurrency)
- Transaction isolation level: SERIALIZABLE

### Schema Overview

**Tables**:
1. locations - Main locations
2. sub_locations - Sub-locations within locations
3. images - Image files
4. videos - Video files
5. documents - Document files
6. urls - URL references
7. versions - Version tracking

**Relationships**:
- locations → sub_locations (one-to-many)
- locations → images (one-to-many)
- locations → videos (one-to-many)
- locations → documents (one-to-many)
- locations → urls (one-to-many)
- sub_locations → images (one-to-many, nullable)
- sub_locations → videos (one-to-many, nullable)
- sub_locations → documents (one-to-many, nullable)
- sub_locations → urls (one-to-many, nullable)
- images ↔ videos (many-to-many via JSON1 fields, for live photos)
- images ↔ documents (many-to-many via JSON1 fields)
- videos ↔ documents (many-to-many via JSON1 fields)

### Foreign Key Constraints

**Cascade Behavior**:
- ON DELETE CASCADE: Deleting location deletes all related media
- ON DELETE SET NULL: Deleting sub-location sets sub_uuid to NULL in media

**Foreign Keys**:
```sql
-- sub_locations
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE

-- images
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL

-- videos
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL

-- documents
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL

-- urls
FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
```

### Indexes

**Primary Indexes** (for lookups):
- locations: loc_uuid (PRIMARY KEY), loc_uuid8 (UNIQUE)
- sub_locations: sub_uuid (PRIMARY KEY), sub_uuid8 (UNIQUE)
- images: img_sha256 (UNIQUE)
- videos: vid_sha256 (UNIQUE)
- documents: doc_sha (UNIQUE)
- urls: url_uuid (PRIMARY KEY)
- versions: modules (PRIMARY KEY)

**Composite Indexes** (for common queries):
- locations: (state, type) - for browsing by geography/type
- images: (loc_uuid, camera) - for filtering by location and hardware
- videos: (loc_uuid, drone) - for filtering by location and hardware

**JSON1 Indexes** (for JSON field queries):
- Consider creating indexes on frequently queried JSON paths

### JSON1 Usage

**JSON Fields**:
- images.img_hardware - Structured hardware metadata: {make, model, category}
- videos.vid_hardware - Structured hardware metadata: {make, model, category}
- images.img_docs - Array of related document SHA256s
- images.img_vids - Array of related video SHA256s (live photos)
- videos.vid_docs - Array of related document SHA256s
- videos.vid_imgs - Array of related image SHA256s (live videos)

**Query Examples**:
```sql
-- Query images by camera make
SELECT * FROM images
WHERE json_extract(img_hardware, '$.make') = 'Canon';

-- Query images with live videos
SELECT * FROM images
WHERE json_array_length(img_vids) > 0;

-- Query videos related to specific image
SELECT * FROM videos
WHERE EXISTS (
  SELECT 1 FROM json_each(vid_imgs)
  WHERE value = 'abc123...'  -- image SHA256
);
```

### Data Integrity Rules

**Uniqueness Constraints**:
- loc_uuid, loc_uuid8 must be unique across locations
- sub_uuid, sub_uuid8 must be unique across sub_locations
- img_sha256 must be unique across images (deduplication)
- vid_sha256 must be unique across videos (deduplication)
- doc_sha must be unique across documents (deduplication)

**NOT NULL Constraints**:
- All UUID fields (loc_uuid, loc_uuid8, sub_uuid, sub_uuid8, url_uuid)
- All SHA256 fields (img_sha256, vid_sha256, doc_sha)
- All file location fields (img_loc, vid_loc, doc_loc)
- All filename fields (img_name, vid_name, doc_name)
- All core identification fields (loc_name, state, type, etc.)

**Check Constraints** (to be implemented):
- State must be valid US state abbreviation
- Type must be from approved type list
- Extension must match filename
- SHA256 must be 64 hex characters
- UUID must be valid UUID4 format

### Transaction Safety

**All Modifications Must**:
1. Begin with BEGIN TRANSACTION
2. Perform operations
3. Verify success
4. COMMIT if successful, ROLLBACK if failed
5. Log transaction outcome

**Example Transaction**:
```python
try:
    conn.execute("BEGIN TRANSACTION")

    # Perform operations
    conn.execute("INSERT INTO locations (...) VALUES (...)")
    conn.execute("INSERT INTO images (...) VALUES (...)")

    # Verify
    if verify_operations():
        conn.execute("COMMIT")
        log.info("Transaction committed successfully")
    else:
        conn.execute("ROLLBACK")
        log.error("Verification failed, transaction rolled back")

except Exception as e:
    conn.execute("ROLLBACK")
    log.error(f"Transaction failed: {e}")
    raise
```

---

## Data Integrity Features

### SHA256 Hashing

**Purpose**: File deduplication and integrity verification

**Implementation**:
- Every file (image, video, document) gets SHA256 hash on import
- Hash stored in database (full 64 chars + first 8 chars for compact reference)
- Unique constraint on SHA256 fields prevents duplicate imports
- Hash verified after file move to ensure integrity

**Benefits**:
- Detect duplicate files across imports
- Verify file integrity after copy/move operations
- Detect file corruption
- Enable deduplication (don't store same file twice)

### UUID4 Generation

**Purpose**: Unique identifiers for locations and sub-locations

**Implementation**:
- UUID4 (random) for all location and sub-location IDs
- Full UUID stored for uniqueness
- First 8 characters (uuid8) stored for compact reference
- Collision detection on uuid8 (regenerate if collision)

**Benefits**:
- Globally unique identifiers
- No sequential IDs (security)
- Compact 8-char reference for filenames and folders
- Mergeable databases (UUIDs won't conflict)

### Collision Detection

**Types of Collisions**:

**SHA256 Collision** (during import):
- Same file imported twice → skip duplicate
- Different file with same SHA256 → extremely unlikely (1 in 2^256)
- If detected: alert user, log incident, reject import

**UUID8 Collision** (during generation):
- Probability: ~1 in 4 billion (2^32)
- If detected: regenerate UUID, try again
- Log collision for monitoring

**Handling**:
```python
# SHA256 collision check
existing = db.execute("SELECT * FROM images WHERE img_sha256 = ?", (sha256,))
if existing:
    if same_filename_and_location:
        log.info("Duplicate file detected, skipping")
        return "SKIP"
    else:
        log.warning("SHA256 collision with different file - investigate!")
        return "COLLISION"

# UUID8 collision check
while True:
    uuid8 = generate_uuid8()
    existing = db.execute("SELECT * FROM locations WHERE loc_uuid8 = ?", (uuid8,))
    if not existing:
        break
    log.warning(f"UUID8 collision: {uuid8}, regenerating")
```

### Automated Backups

**When Backups Are Created**:
- Before schema migrations (db_migrate.py)
- Before bulk imports (db_import.py with many files)
- Before cleanup operations (database_cleanup.py)
- On user request (backup.py)
- Scheduled (daily via cron/systemd timer)

**Backup Process**:
1. Generate timestamp: YYYY-MM-DD_HH-MM-SS
2. Create backup filename: `{db_name}-{timestamp}.db`
3. Use SQLite backup API (ensures consistency)
4. Verify backup created successfully
5. Verify backup is newer than previous
6. Log backup creation

**Retention Policy**:
- Keep all backups from last 7 days
- For older backups: keep first and last of each day
- Never delete backups less than 24 hours old

### Verification Workflows

**Post-Import Verification** (db_verify.py):
1. For each imported file:
   - Calculate SHA256 at new archive location
   - Compare to SHA256 in database
   - Verify match
2. If all match: delete staging files, mark verified
3. If any fail: preserve staging, alert user, log error

**Database Integrity Check** (database_cleanup.py):
1. Run `PRAGMA integrity_check`
2. Verify all foreign key relationships
3. Check for orphaned records
4. Verify file paths exist
5. Generate integrity report

**On-Demand Verification**:
- User can trigger full verification of archive
- Recalculate SHA256 for all files
- Compare to database
- Report any mismatches

---

## Organizational Features

### Geographic Organization

**Structure**: `{state-type}/{location-name}_{loc_uuid8}/`

**Examples**:
- `ny-industrial/abandoned-factory_a1b2c3d4/`
- `vt-residential/old-farmhouse_e5f6g7h8/`
- `pa-commercial/shopping-mall_i9j0k1l2/`

**Benefits**:
- Easy browsing by state
- Type categorization (industrial, residential, commercial, etc.)
- Unique location names (UUID8 prevents conflicts)

### Hardware-Based Categorization

**Images** (photos folder):
- `original_camera/` - DSLR photos (Canon, Nikon, Sony, etc.)
- `original_phone/` - Smartphone photos
- `original_drone/` - Drone aerial photos
- `original_go-pro/` - GoPro action camera photos
- `original_film/` - Scanned film photos
- `original_other/` - Uncategorized

**Videos** (videos folder):
- `original_camera/` - DSLR videos
- `original_phone/` - Smartphone videos
- `original_drone/` - Drone aerial videos
- `original_go-pro/` - GoPro action videos
- `original_dash-cam/` - Dash cam videos
- `original_other/` - Uncategorized (includes live videos)

**Benefits**:
- Quick filtering by source hardware
- Identify photo/video quality level
- Track equipment usage
- Organize by capture method

### Live Photo Pairing

**Detection**:
- Compare original filenames and locations
- Match iPhone Live Photos (IMG_1234.HEIC + IMG_1234.MOV)
- Match similar patterns from other devices

**Relationship Tracking**:
- Image gets video SHA256 in img_vids field
- Video gets image SHA256 in vid_imgs field
- Bidirectional reference

**Storage**:
- Photo: stored in appropriate hardware folder
- Video: stored in videos/original_other/ (special case)

**Benefits**:
- Preserve live photo functionality
- Maintain photo/video relationship
- Query for live photos easily

### Document-Media Relationships

**Relationship Types**:

**.srt (subtitle) files**:
- Match to videos by original filename
- Store video SHA256 in docs_img field (typo in schema)
- Store document SHA256 in vid_docs field

**.xml (metadata) files**:
- Match to images or videos by original filename
- Store media SHA256 in docs_img field
- Store document SHA256 in img_docs or vid_docs field

**Benefits**:
- Preserve media metadata
- Maintain subtitle associations
- Query for media with documents

### URL Domain Normalization

**Complex Hosting Platforms**:

**SmugMug**: `username.smugmug.com` → `username`
**Blogspot**: `myblog.blogspot.com` → `myblog`
**WordPress**: `mysite.wordpress.com` → `mysite`
**GitHub Pages**: `username.github.io` → `username`

**Storage**:
- Normalized domain stored in database
- Full URL preserved
- Organized in `documents/websites/{domain}_{url_uuid8}/`

**Benefits**:
- Group URLs by platform
- Extract meaningful identifiers
- Organized folder structure

### Film Stock Tracking

**Designation**:
- Manual flag during import (film=1)
- Metadata detection (if EXIF contains film stock info)

**Storage**:
- Separate folder: photos/original_film/
- Preserves film scan organization

**Use Cases**:
- Track analog photography
- Organize scanned negatives
- Differentiate from digital photos

### Metadata Preservation

**Image Metadata** (via exiftool):
- EXIF data (camera settings, GPS, timestamps)
- IPTC data (keywords, copyright)
- XMP data (editing metadata)
- Raw EXIF stored in exiftool_hardware field
- Parsed hardware info in img_hardware JSON field

**Video Metadata** (via ffprobe):
- Container format
- Codec information
- Frame rate, resolution
- Duration
- GPS tracks (if available)
- Raw metadata stored in ffmpeg_hardware field
- Parsed hardware info in vid_hardware JSON field

**Original File Information**:
- Original location (img_loco, vid_loco, doc_loco)
- Original filename (img_nameo, vid_nameo, doc_nameo)
- Import timestamp (img_add, vid_add, doc_add)
- Import author (imp_author)

**Benefits**:
- Full audit trail
- Recover original file organization
- Track who imported what
- Preserve all camera metadata

---

## Import Pipeline Workflow

### End-to-End Import Process

**1. Pre-Import Setup**
```
User prepares:
- Location information (name, state, type)
- Media files in temporary folder
```

**2. Database Migration** (db_migrate.py)
```
- Check current database schema version
- Apply any pending migrations
- Update versions table
- Backup database before changes
```

**3. Import to Staging** (db_import.py)
```
- Generate loc_uuid, loc_uuid8 for location
- Verify uuid8 uniqueness
- Create location entry in database
- For each media file:
  - Calculate SHA256
  - Check for duplicates
  - Copy to ingest staging folder
  - Create preliminary database entry
- Log import summary
```

**4. Organize and Categorize** (db_organize.py)
```
For each image:
- Run exiftool to extract metadata
- Parse Make/Model from EXIF
- Match against camera_hardware.json
- Set hardware category flags
- Store metadata in img_hardware (JSON)
- Match to live videos if applicable
- Match to related documents (.xml, etc.)

For each video:
- Run ffprobe to extract metadata
- Parse Make/Model from metadata
- Match against camera_hardware.json
- Set hardware category flags
- Store metadata in vid_hardware (JSON)
- Match to live photos if applicable
- Match to related documents (.srt, etc.)

For each document:
- Extract file extension
- Check approved_ext.json for special handling
- Match to related images/videos if applicable

For each URL:
- Parse domain
- Normalize using host_domains.json
- Generate url_uuid
```

**5. Create Folder Structure** (db_folder.py)
```
- Read folder template from folder.json
- Create state-type directory
- Create location directory: {name}_{loc_uuid8}
- Create photos subdirectories (original_camera, original_phone, etc.)
- Create videos subdirectories (original_camera, original_phone, etc.)
- Create documents subdirectories (file-extensions, zips, pdfs, websites)
- Verify all directories created
```

**6. Ingest Files** (db_ingest.py)
```
For each image:
- Generate standardized filename: {loc_uuid8}-img_{sha8}.{ext}
- Determine destination folder based on hardware category
- Hardlink (same disk) or copy (different disk) to destination
- Update img_loc, img_name in database
- Verify file exists at destination

For each video:
- Generate standardized filename: {loc_uuid8}-vid_{sha8}.{ext}
- Determine destination folder (live videos → original_other)
- Hardlink or copy to destination
- Update vid_loc, vid_name in database
- Verify file exists at destination

For each document:
- Generate standardized filename: {loc_uuid8}-doc_{sha8}.{ext}
- Copy to appropriate documents subfolder
- Update doc_loc, doc_name in database
- Verify file exists at destination
```

**7. Verify Integrity** (db_verify.py)
```
For each file moved:
- Calculate SHA256 at new location
- Compare to database SHA256
- Log verification result

If all verified:
- Delete original files from ingest staging
- Delete empty staging folder
- Mark import as verified in database

If any fail:
- Preserve staging files
- Log errors with details
- Alert user
- Do NOT delete staging
```

**8. Generate JSON Export** (db_identify.py)
```
- Query all data for location from database
- Compile into comprehensive JSON structure
- Write to {loc_uuid8}_master.json
- Store in location's archive folder
- Update json_update timestamp in database
```

**9. Cleanup and Maintenance** (database_cleanup.py)
```
- Run database integrity check
- Verify foreign key relationships
- Check for orphaned records
- Clean up old backups (retention policy)
- Vacuum database
- Generate maintenance report
```

### Import Workflow Diagram

```
┌─────────────────────┐
│ User: Prepare files │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  db_migrate.py      │ ← Create/update schema
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  db_import.py       │ ← Import to staging, generate UUIDs/SHA256
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  db_organize.py     │ ← Extract metadata, categorize hardware
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  db_folder.py       │ ← Create organized folder structure
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  db_ingest.py       │ ← Move files to archive
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  db_verify.py       │ ← Verify integrity, cleanup staging
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  db_identify.py     │ ← Generate JSON export
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│database_cleanup.py  │ ← Maintenance and cleanup
└──────────┬──────────┘
           │
           v
     ┌─────────┐
     │ Complete │
     └─────────┘
```

---

## Technology Stack

### Core Technologies

**Language**: Python 3.9+
- Reason: Excellent file handling, rich ecosystem, readable syntax
- Libraries: sqlite3, pathlib, json, hashlib, uuid

**Database**: SQLite 3
- Reason: Serverless, single file, perfect for local archive
- Extension: JSON1 (for JSON field support)
- Configuration: Foreign keys ON, WAL mode

**Metadata Extraction**:
- **exiftool** (external binary) - Industry standard for EXIF extraction
- **ffprobe** (part of ffmpeg) - Video metadata extraction

**Text Normalization**:
- **unidecode** - Convert Unicode to ASCII
- **libpostal** - Address parsing and normalization
- **dateutil** - Date parsing

### Python Dependencies

**Standard Library**:
- sqlite3 - Database operations
- pathlib - Path handling
- json - JSON parsing/generation
- hashlib - SHA256 hashing
- uuid - UUID generation
- logging - Application logging
- argparse - CLI argument parsing
- datetime - Timestamp handling
- shutil - File operations

**Third-Party** (to be installed):
- unidecode - Unicode normalization
- python-dateutil - Date parsing
- postal (libpostal Python bindings) - Address parsing

### External Tools

**exiftool**:
- Installation: `brew install exiftool` (macOS) or package manager
- Purpose: Extract EXIF metadata from images
- Usage: `exiftool -j image.jpg` (JSON output)

**ffprobe**:
- Installation: `brew install ffmpeg` (macOS) or package manager
- Purpose: Extract metadata from videos
- Usage: `ffprobe -v quiet -print_format json -show_format video.mp4`

### Development Tools

**Version Control**: Git
**Code Quality**:
- pylint - Linting
- mypy - Type checking
- black - Code formatting (optional)

**Testing**:
- pytest - Testing framework
- pytest-cov - Coverage reporting

### Environment Setup

**Virtual Environment**:
```bash
cd /Users/bryant/Documents/tools/aupat
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install --upgrade pip
pip install unidecode python-dateutil postal pytest pytest-cov
```

**External Tools** (macOS):
```bash
brew install exiftool ffmpeg
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Setup**:
- [ ] Create folder structure (scripts/, data/, user/, backups/, logs/)
- [ ] Set up Python virtual environment
- [ ] Install dependencies
- [ ] Create user.json configuration file

**Utility Scripts**:
- [ ] Implement gen_uuid.py
- [ ] Implement gen_sha.py
- [ ] Implement backup.py
- [ ] Implement name.py
- [ ] Implement folder.py
- [ ] Write tests for utilities

**Configuration Files**:
- [ ] Create all JSON schema files in data/
- [ ] Validate JSON syntax
- [ ] Document any schema adjustments

### Phase 2: Database (Week 3)

**Schema**:
- [ ] Implement db_migrate.py
- [ ] Create initial schema (all tables)
- [ ] Implement foreign key constraints
- [ ] Create indexes
- [ ] Test schema creation
- [ ] Test migrations

**Testing**:
- [ ] Write schema tests
- [ ] Test foreign key cascades
- [ ] Test transaction rollback
- [ ] Verify PRAGMA settings

### Phase 3: Import Pipeline (Week 4-6)

**Import**:
- [ ] Implement db_import.py (basic import)
- [ ] Test UUID generation and collision detection
- [ ] Test SHA256 generation and duplicate detection
- [ ] Test database entry creation

**Organization**:
- [ ] Implement db_organize.py
- [ ] Integrate exiftool for image metadata
- [ ] Integrate ffprobe for video metadata
- [ ] Implement hardware categorization
- [ ] Implement live photo detection
- [ ] Test metadata extraction

**Folder Creation**:
- [ ] Implement db_folder.py
- [ ] Test folder structure creation
- [ ] Test with various location types

**Ingestion**:
- [ ] Implement db_ingest.py
- [ ] Test hardlinking (same disk)
- [ ] Test copying (different disk)
- [ ] Test file naming
- [ ] Test database updates

**Verification**:
- [ ] Implement db_verify.py
- [ ] Test SHA256 verification
- [ ] Test staging cleanup
- [ ] Test error handling (verification failures)

**Export**:
- [ ] Implement db_identify.py
- [ ] Test JSON export generation
- [ ] Validate JSON output

**Maintenance**:
- [ ] Implement database_cleanup.py
- [ ] Test integrity checks
- [ ] Test backup cleanup
- [ ] Test vacuum operations

### Phase 4: Testing & Documentation (Week 7)

**Testing**:
- [ ] Write comprehensive unit tests
- [ ] Write integration tests
- [ ] Write end-to-end tests
- [ ] Test error paths
- [ ] Test edge cases
- [ ] Achieve >80% code coverage

**Documentation**:
- [ ] Write user guide
- [ ] Write developer guide
- [ ] Document troubleshooting procedures
- [ ] Create example workflows
- [ ] Update README.md

### Phase 5: Refinement (Week 8)

**Code Quality**:
- [ ] Run pylint on all scripts
- [ ] Run mypy type checking
- [ ] Fix all linting issues
- [ ] Add missing type hints
- [ ] Add missing docstrings
- [ ] Review and refactor

**Performance**:
- [ ] Profile import pipeline
- [ ] Optimize slow operations
- [ ] Test with large datasets
- [ ] Verify memory usage

**Security**:
- [ ] Audit for SQL injection
- [ ] Audit for path traversal
- [ ] Audit input validation
- [ ] Test with malicious input

### Phase 6: Stage 1 Completion (Week 9)

**Final Testing**:
- [ ] Full end-to-end import test
- [ ] Test with real data
- [ ] Verify all features work
- [ ] Verify data integrity

**Release**:
- [ ] Create version 1.0.0 tag
- [ ] Write release notes
- [ ] Archive Stage 1 documentation
- [ ] Begin Stage 2 planning

### Future Stages

**Stage 2: Web Application** (Months 3-4)
- Web interface design
- Backend API development
- Frontend implementation
- Testing and deployment

**Stage 3: Dockerization** (Month 5)
- Dockerfile creation
- Docker Compose setup
- Data persistence
- Testing and deployment

**Stage 4: Mobile Application** (Months 6-8)
- Mobile app design
- Native app development
- Backend integration
- Testing and deployment

---

## Current Implementation Status

### Summary

**Overall Status**: PLANNING PHASE - 0% Implemented

**Documentation**: 100% Complete
- All scripts documented: 13/13
- All JSON files documented: 15/15
- Methodology defined: claudecode.md complete
- Architecture documented: This file complete

**Implementation**: 0% Complete
- Python scripts: 0/13 implemented
- JSON files: 0/15 created
- Database: Not created
- Tests: 0 written
- Folder structure: Not created

### Next Immediate Steps

1. **Create folder structure**: scripts/, data/, user/, backups/, logs/
2. **Set up environment**: Python venv, install dependencies
3. **Create user.json**: Configure database paths
4. **Create JSON schema files**: All 15 files in data/
5. **Implement utilities first**: gen_uuid.py, gen_sha.py, backup.py, name.py, folder.py
6. **Implement database**: db_migrate.py to create schema
7. **Follow roadmap**: Complete Phase 1, then Phase 2, etc.

---

## Conclusion

AUPAT is a comprehensively planned, bulletproof digital asset management system designed for long-term reliability and data integrity. The project has complete documentation covering all aspects of design, implementation, and operation. The next step is to begin implementation following the bulletproof 9-step workflow defined in claudecode.md.

**Key Strengths**:
- Thorough planning and documentation
- Strong engineering principles (BPA, BPL, KISS, FAANG PE)
- Data integrity focus (SHA256, UUID, foreign keys, transactions)
- Clear architecture and workflows
- Comprehensive error handling and verification

**Ready for Implementation**: All specifications are complete and ready for development to begin.

---

**Last Updated**: 2025-01-15
**Version**: 1.0
**Status**: Planning Phase Complete, Ready for Implementation
