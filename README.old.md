# AUPAT - Abandoned Upstate Project Archive Tool

Digital asset management for location-based photo/video archives. Organizes media by location and camera hardware. Bulletproof. No BS.

## What It Does

Import photos/videos by location → Extract EXIF/metadata → Categorize by camera hardware → Store in organized archive → Deduplicate via SHA256

That's it.

## Quick Start

```bash
# First time setup
bash setup.sh

# Run web interface (with automatic health checks)
bash start_web.sh

# Or run directly
python web_interface.py

# Open http://localhost:5000 and import
```

**Recommended**: Use `start_web.sh` instead of running `web_interface.py` directly. The startup script runs pre-flight checks to verify all dependencies are installed, preventing blank website errors.

Or run CLI pipeline manually (see Import Pipeline below).

## Requirements

- Python 3
- exiftool (image EXIF)
- ffprobe (video metadata)
- SQLite with JSON1

Install tools:
```bash
# macOS
brew install exiftool ffmpeg

# Linux
apt install libimage-exiftool-perl ffmpeg
```

## Import Pipeline

The full import pipeline runs these scripts in order:

1. **db_migrate.py** - Create/update database schema
2. **db_import.py** - Import location and files to staging
3. **db_organize.py** - Extract metadata, categorize hardware
4. **db_folder.py** - Create archive folder structure
5. **db_ingest.py** - Move files from staging to archive
6. **db_verify.py** - Verify SHA256 integrity, cleanup staging
7. **db_identify.py** - Generate master JSON per location

Web interface runs this automatically. CLI users run each script manually.

## Archive Structure

Files organized by location and hardware:

```
archive/
└── {state}-{type}/                    # e.g., ny-industrial
    └── {location}_{uuid8}/            # e.g., middletown-state-hospital_a1b2c3d4
        ├── photos/
        │   ├── original_camera/       # DSLR photos
        │   ├── original_phone/        # Phone photos
        │   ├── original_drone/        # Drone photos
        │   ├── original_go-pro/       # GoPro photos
        │   ├── original_film/         # Scanned film
        │   └── original_other/        # Uncategorized
        ├── videos/
        │   ├── original_camera/       # DSLR videos
        │   ├── original_phone/        # Phone videos
        │   ├── original_drone/        # Drone videos
        │   ├── original_go-pro/       # GoPro videos
        │   ├── original_dash-cam/     # Dash cam videos
        │   └── original_other/        # Uncategorized + live videos
        └── documents/
            ├── file-extensions/       # .srt, .xml, etc.
            ├── zips/                  # ZIP archives
            ├── pdfs/                  # PDF files
            └── websites/              # URL archives
```

## Hardware Categories

Categories auto-detected from EXIF Make/Model:

- **camera** - Canon, Nikon, Sony, Fujifilm, Olympus, Pentax, Leica, Panasonic, Hasselblad
- **phone** - iPhone, Samsung, Google, OnePlus, etc.
- **drone** - DJI, Autel, Parrot, Skydio, Yuneec
- **go_pro** - GoPro action cameras
- **dash_cam** - Vantrue, BlackVue, Garmin, Nextbase
- **film** - Scanned film (manual flag or metadata)
- **other** - Everything else

Rules in `data/camera_hardware.json`.

## File Naming

Content-addressable naming for deduplication:

```
{loc_uuid8}-{sha8}.ext                    # Images/Videos/Documents
{loc_uuid8}-{sub_uuid8}-{sha8}.ext        # With sub-location
```

- `uuid8` = first 8 chars of location UUID
- `sha8` = first 8 chars of file SHA256

Examples:
- `49184cd2-1a43ad82.dng` (image)
- `49184cd2-ba28beb7.mov` (video)
- `49184cd2-a8f2b3c4-1a43ad82.jpg` (image with sub-location)

Prevents duplicates. Enables integrity verification. No filename collisions.

## Configuration

Edit `user/user.json` (created by setup.sh):

```json
{
  "db_name": "aupat.db",
  "db_loc": "/home/user/aupat/data/aupat.db",
  "db_backup": "/home/user/aupat/data/backups/",
  "db_ingest": "/home/user/aupat/data/ingest/",
  "arch_loc": "/home/user/aupat/data/archive/"
}
```

**CRITICAL**: `db_loc` must point to a FILE (ends with .db), not a directory.

## Project Structure

```
aupat/
├── scripts/              # Python pipeline scripts
│   ├── db_import.py      # Import to staging
│   ├── db_organize.py    # Metadata extraction
│   ├── db_folder.py      # Create folders
│   ├── db_ingest.py      # Move to archive (FIXED!)
│   └── db_verify.py      # Integrity check
├── data/                 # Database + JSON configs
│   ├── aupat.db          # SQLite database
│   ├── camera_hardware.json
│   ├── folder.json       # Archive structure template
│   └── *.json            # Other configs
├── user/                 # User config (gitignored)
│   └── user.json         # Paths configuration
├── logseq/pages/         # Complete technical specs
├── tempdata/testphotos/  # Test data
├── web_interface.py      # Flask web UI
└── freshstart.py         # Testing utility
```

## Database Schema

- **locations** - Location info (name, state, type, UUID)
- **images** - Images with EXIF + hardware categorization + film flag
- **videos** - Videos with metadata + hardware categorization
- **documents** - Documents and sidecar files
- **urls** - Web URLs for locations
- **versions** - Schema version tracking

**Film photography**: `film` field is in images table (per-image property), NOT locations table.

Full specs in `logseq/pages/`.

## Troubleshooting

### "user.json not found"
```bash
bash setup.sh
```

### "Database path is a directory"
Fix `user/user.json` - `db_loc` must end with `/aupat.db` (FILE), not just directory.

### Camera categorization fails
```bash
# Install exiftool
brew install exiftool          # macOS
apt install libimage-exiftool-perl  # Linux

# Verify
exiftool -ver
```

### Video metadata fails
```bash
# Install ffmpeg/ffprobe
brew install ffmpeg            # macOS
apt install ffmpeg             # Linux

# Verify
ffprobe -version
```

### Pipeline creates empty folders
Fixed. Folders only created when media of that type exists. No more empty `photos/original_camera/` if no DSLR images, no `videos/` if no videos, etc.

### Blank archive folders after import
Run the FULL pipeline:
```bash
python scripts/db_import.py     # Import to staging
python scripts/db_organize.py   # Categorize
python scripts/db_folder.py     # Create folders
python scripts/db_ingest.py     # Move files (THIS WAS BROKEN, NOW FIXED)
python scripts/db_verify.py     # Verify + cleanup
```

Or use web interface which runs everything.

## Testing

### Web Interface Health Check

Test web interface dependencies and functionality:
```bash
python scripts/test_web_interface.py
```

This checks:
- Flask and all Python dependencies are installed
- web_interface.py has valid syntax
- Server can start and serve HTML correctly
- Website returns actual content (not blank pages)

Run this after any changes to catch issues before deployment.

### Data Import Testing

Test data in `tempdata/testphotos/`:
- Middletown State Hospital - 8 Nikon .NEF files
- Water Slide World - 29 .DNG photos + 2 .MOV videos + 1 .JPG edit

Run freshstart test:
```bash
python freshstart.py
```

## Data Integrity

Bulletproof principles:
- SHA256 deduplication (no duplicate imports)
- Transaction-safe database ops (ACID compliance)
- Staging before ingest (reversible)
- Verification before cleanup (integrity check)
- Automated backups (before schema changes)
- Foreign key enforcement (referential integrity)

## Documentation

Full technical specs in `logseq/pages/`:
- `claude.md` - AI collaboration guide
- `claudecode.md` - Development methodology
- `db_*.md` - Script specifications
- `*_table.md` - Database schemas
- `camera_hardware.md` - Hardware detection rules
- `folder.md` - Archive structure template

## Development Status

**Stage 1**: CLI + Web import tool (ACTIVE)
- Import pipeline: COMPLETE
- Web interface: FUNCTIONAL
- Hardware categorization: WORKING
- Archive organization: WORKING (recently fixed)

**Future Stages**:
- Stage 2: Enhanced web UI
- Stage 3: Docker deployment
- Stage 4: Mobile app + Docker backend

## Known Issues

NONE currently. All critical issues resolved:
- ✓ Pipeline fixed - files move to archive correctly
- ✓ Blank website issue - fixed with automated dependency checking
- ✓ Added health checks to prevent deployment failures

## License

See LICENSE file.

---

**Built with**: Python, SQLite, exiftool, ffprobe
**Principles**: KISS, bulletproof longterm, best practices always
