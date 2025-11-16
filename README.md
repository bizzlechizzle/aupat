# AUPAT

Abandoned Upstate Project Archive Tool - A bulletproof digital asset management system for organizing location-based media collections with long-term data integrity.

## What It Does

Organizes photos, videos, documents, and URLs by geographic location with hardware-based categorization, metadata extraction, SHA256 deduplication, and comprehensive relationship tracking.

**Input:** Unorganized media files in folders
**Output:** Organized archive with SQLite database tracking everything

## Quick Start

### 1. Initial Setup

```bash
bash setup.sh
```

This creates folder structure, virtual environment, installs dependencies, and configures user.json.

### 2. Edit Configuration

```bash
nano user/user.json
```

Set your database and archive paths. The setup script creates working defaults in `data/` but you can point to external drives.

### 3. Choose Your Workflow

#### Option A: Automated CLI (Recommended)

```bash
source venv/bin/activate
./run_workflow.py --source /path/to/media --backup
```

Runs all steps automatically with progress tracking.

#### Option B: Web Interface

```bash
source venv/bin/activate
./web_interface.py
```

Open browser to http://localhost:5001

#### Option C: Manual Step-by-Step

```bash
source venv/bin/activate
python3 scripts/db_migrate.py      # Create database schema
python3 scripts/db_import.py       # Import location and media
python3 scripts/db_organize.py     # Extract metadata, categorize hardware
python3 scripts/db_folder.py       # Create archive folder structure
python3 scripts/db_ingest.py       # Move files to archive
python3 scripts/db_verify.py       # Verify integrity, cleanup staging
python3 scripts/db_identify.py     # Generate JSON exports
```

## Requirements

### System Requirements

- Python 3.9+
- SQLite 3 with JSON1 extension
- exiftool (image metadata extraction)
- ffprobe (video metadata extraction)

### Install External Tools

macOS:
```bash
brew install exiftool ffmpeg
```

Ubuntu/Debian:
```bash
apt-get install libimage-exiftool-perl ffmpeg
```

### Optional: Advanced Address Normalization

```bash
# macOS
brew install libpostal
pip install postal

# Ubuntu
apt-get install libpostal-dev
pip install postal
```

## How It Works

### Import Pipeline

1. **db_migrate.py** - Creates/updates database schema with foreign key constraints and indexes
2. **db_import.py** - Generates UUID4 for location, calculates SHA256 for files, stores in staging
3. **db_organize.py** - Extracts EXIF (images) and ffprobe (videos) metadata, categorizes by hardware
4. **db_folder.py** - Creates organized folder structure: `{state-type}/{location_name}_{uuid8}/photos|videos|documents`
5. **db_ingest.py** - Moves files with standardized naming: `{uuid8}-img_{sha8}.ext`
6. **db_verify.py** - Verifies SHA256 integrity, deletes staging only after verification passes
7. **db_identify.py** - Exports master JSON file per location with all metadata

### Hardware Categorization

**Photos:**
- original_camera (DSLR: Canon, Nikon, Sony, Fujifilm, etc.)
- original_phone (iPhone, Samsung, Google Pixel, etc.)
- original_drone (DJI, Autel, Parrot, etc.)
- original_go-pro (GoPro action cameras)
- original_film (scanned film)
- original_other (uncategorized)

**Videos:**
- original_camera (DSLR video)
- original_phone (smartphone video)
- original_drone (aerial footage)
- original_go-pro (action video)
- original_dash-cam (dash cam footage)
- original_other (uncategorized, including live videos)

### Data Integrity

- **SHA256 hashing:** Deduplication and integrity verification
- **UUID4 identifiers:** Unique location IDs with collision detection
- **Foreign keys:** Enforced relationships with CASCADE/SET NULL
- **Transaction safety:** All database modifications wrapped in BEGIN/COMMIT/ROLLBACK
- **Automated backups:** Before schema changes and bulk operations
- **Verification before cleanup:** Never delete staging files until archive verified

## CLI Orchestration

The `run_workflow.py` script automates the complete pipeline:

```bash
# Basic usage
./run_workflow.py --source /path/to/media --backup

# Dry run (show what would execute)
./run_workflow.py --source /path/to/media --dry-run

# Interactive mode (prompt before each step)
./run_workflow.py --source /path/to/media --interactive

# Skip specific steps
./run_workflow.py --skip "Import Media" --skip "Export JSON"

# Process existing database without new imports
./run_workflow.py --skip "Import Media"
```

**Options:**
- `--source PATH` - Source directory with media files
- `--backup` - Create database backup after completion
- `--dry-run` - Show execution plan without running
- `--interactive` - Prompt before each step
- `--skip STEP` - Skip specific workflow steps (repeatable)
- `--config PATH` - Custom user.json path
- `--verbose` - Enable verbose logging

## Web Interface

Flask-based web UI with dashboard, location browser, and import form.

```bash
source venv/bin/activate
./web_interface.py
```

**Features:**
- Dashboard with statistics and recent imports
- Location browser with pagination
- Import form with preview mode
- Theme toggle (light/dark)
- Responsive mobile design
- Matches abandonedupstate.com aesthetic

## Project Structure

```
aupat/
├── scripts/                    # Core Python scripts
│   ├── db_migrate.py          # Database schema management
│   ├── db_import.py           # Import media to staging
│   ├── db_organize.py         # Metadata extraction and categorization
│   ├── db_folder.py           # Create archive folder structure
│   ├── db_ingest.py           # Move files to archive
│   ├── db_verify.py           # Integrity verification
│   ├── db_identify.py         # JSON export generation
│   ├── database_cleanup.py    # Maintenance and integrity checks
│   ├── backup.py              # Database backups
│   ├── normalize.py           # Text normalization utilities
│   └── utils.py               # Shared utilities
├── data/                       # JSON configuration files
│   ├── locations.json         # Locations table schema
│   ├── images.json            # Images table schema
│   ├── videos.json            # Videos table schema
│   ├── documents.json         # Documents table schema
│   ├── urls.json              # URLs table schema
│   ├── sub-locations.json     # Sub-locations table schema
│   ├── versions.json          # Version tracking schema
│   ├── camera_hardware.json   # Hardware classification rules
│   ├── approved_ext.json      # Special file extension handling
│   ├── ignored_ext.json       # Excluded file extensions
│   ├── live_videos.json       # Live photo matching rules
│   ├── folder.json            # Folder structure template
│   └── name.json              # File naming conventions
├── user/                       # User configuration
│   └── user.json              # Database paths and settings
├── logseq/                     # Original documentation (32+ .md files)
├── claude.md                   # AI collaboration guide
├── claudecode.md               # Development methodology
├── project-overview.md         # Complete technical reference
├── web_interface.py            # Flask web application
├── run_workflow.py             # CLI orchestration script
├── check_import_status.py      # Status checking utility
├── setup.sh                    # Initial setup script
└── requirements.txt            # Python dependencies
```

**Gitignored folders:**
- `venv/` - Python virtual environment
- `backups/` - Database backups
- `logs/` - Application logs
- `data/aupat.db` - SQLite database

## Database Schema

**Tables:**
- **locations** - Main locations (name, state, type, UUID, timestamps)
- **sub_locations** - Sub-locations within main locations (optional)
- **images** - Images with SHA256, hardware flags, metadata JSON
- **videos** - Videos with SHA256, hardware flags, metadata JSON
- **documents** - Documents (.srt, .xml, .pdf, .zip, etc.)
- **urls** - URL references (websites, galleries, articles)
- **versions** - Version tracking for schema and scripts

**Key Features:**
- UUID4 primary keys for locations
- SHA256 unique constraints for deduplication
- Foreign keys with CASCADE/SET NULL
- JSON1 fields for hardware metadata and relationships
- Transaction safety for all modifications

## Engineering Principles

1. **BPA (Best Practices Always):** Industry standards, no compromises
2. **BPL (Bulletproof Longterm):** Code survives years without modification
3. **KISS (Keep It Simple):** Simplicity over cleverness
4. **FAANG PE (FAANG Personal Edition):** Production-grade without enterprise bloat
5. **NEE (No Emojis Ever):** Professional documentation only
6. **Data Integrity Above All:** Fail safely, verify before deleting, backup before destructive operations

## Documentation

- **claude.md** - AI collaboration guide with project context
- **claudecode.md** - Development methodology and 9-step workflow
- **project-overview.md** - Complete technical reference (2000+ lines)
- **logseq/pages/** - Detailed specification files (32+ documents)

## Testing

Test data included in `tempdata/`:
- Middletown State Hospital (NEF photos)
- Water Slide World (DNG photos, MOV videos)

```bash
# Run test import
source venv/bin/activate
./run_workflow.py --source tempdata/testphotos --backup
```

## Troubleshooting

### Database errors
Run migration to create/update schema:
```bash
python3 scripts/db_migrate.py
```

### Missing user.json
Copy and edit template:
```bash
cp user/user.json.template user/user.json
nano user/user.json
```

### Import verification failures
Check logs in `logs/` directory. Staging files preserved for recovery.

### Virtual environment not activated
Always activate before running:
```bash
source venv/bin/activate
```

## Development Status

**Stage 1 (CLI Import Tool):** Complete
**Stage 2 (Web Application):** In Progress
**Stage 3 (Dockerization):** Not Started
**Stage 4 (Mobile App):** Not Started

## Technology Stack

- **Language:** Python 3.9+
- **Database:** SQLite 3 with JSON1 extension
- **Metadata:** exiftool (images), ffprobe (videos)
- **Normalization:** unidecode, libpostal (optional), dateutil
- **Web Framework:** Flask
- **Frontend:** HTML, CSS, vanilla JavaScript

## Version

Version 1.0 - Stage 1 Complete

## License

MIT
