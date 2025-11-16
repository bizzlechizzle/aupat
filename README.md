# AUPAT - Abandoned Upstate Project Archive Tool

Location-based media archive system. Organizes photos/videos by location and camera hardware.

## What It Does

1. Import media by location (name, type, state)
2. Extract camera make/model from EXIF/metadata
3. Categorize by hardware (DSLR, phone, drone, GoPro, dash cam)
4. Store in organized archive with deduplication
5. Generate location exports as JSON

## Quick Start

```bash
# Setup
bash setup.sh

# Run web interface
python web_interface.py

# Navigate to http://localhost:5000
# Import media, system handles the rest
```

## Requirements

- Python 3
- exiftool (for image metadata)
- ffmpeg/ffprobe (for video metadata)
- SQLite with JSON1

## Project Structure

```
aupat/
├── scripts/           # Python pipeline scripts
├── data/              # JSON configs + database
├── user/              # User config (gitignored)
├── logseq/pages/      # Complete documentation
├── claude.md          # AI collaboration guide
└── web_interface.py   # Web UI
```

## Import Pipeline

1. `db_migrate.py` - Create database schema
2. `db_import.py` - Import location and media
3. `db_organize.py` - Extract metadata and categorize
4. `db_folder.py` - Create folder structure
5. `db_ingest.py` - Move files to archive
6. `db_verify.py` - Verify integrity
7. `db_identify.py` - Generate JSON exports

Web interface runs this automatically.

## Camera Categories

- **DSLR**: Canon, Nikon, Sony, Fujifilm, Panasonic, Olympus, Leica, etc.
- **Phone**: iPhone, Samsung, Google Pixel, etc.
- **Drone**: DJI, Autel, Parrot
- **GoPro**: GoPro action cameras
- **Dash Cam**: Vantrue, BlackVue, Garmin, etc.
- **Other**: Unknown or uncategorized

Categories defined in `data/camera_hardware.json`.

## Configuration

Edit `user/user.json` (created by setup.sh):

```json
{
  "db_name": "aupat.db",
  "db_loc": "/path/to/database/aupat.db",
  "db_backup": "/path/to/backups/",
  "db_ingest": "/path/to/ingest/",
  "arch_loc": "/path/to/archive/"
}
```

## Database Schema

- **locations** - Location info (name, type, state, GPS)
- **images** - Image files with EXIF and categorization
- **videos** - Video files with metadata and categorization
- **documents** - Documents and other files
- **urls** - Web URLs related to locations

Full schema in `logseq/pages/`.

## File Naming

Archives use content-addressable naming:

- Images: `loc_uuid8-img_sha8.ext`
- Videos: `loc_uuid8-vid_sha8.ext`
- Documents: `loc_uuid8-doc_sha8.ext`

With sub-locations: `loc_uuid8-sub_uuid8-{img|vid|doc}_sha8.ext`

- `uuid8` = first 8 chars of location UUID
- `sha8` = first 8 chars of file SHA256

## Documentation

Complete specifications in `logseq/pages/`:

- **claude.md** - AI collaboration guide
- **claudecode.md** - Development methodology
- **db_*.md** - Script specifications
- **{table}_table.md** - Database schemas
- **camera_hardware.md** - Hardware categorization rules

## Development

Follows KISS and bulletproof longterm principles:

- Transaction-safe database operations
- SHA256 deduplication
- Staging before final ingest
- Verification before cleanup
- No destructive operations without backup

See `claude.md` for complete development guidelines.

## Troubleshooting

**Import fails with "user.json not found"**:
```bash
bash setup.sh
```

**Camera categorization not working**:
Check exiftool is installed:
```bash
brew install exiftool  # macOS
apt install libimage-exiftool-perl  # Linux
```

**Video metadata extraction fails**:
Check ffmpeg is installed:
```bash
brew install ffmpeg  # macOS
apt install ffmpeg  # Linux
```

**Database errors**:
```bash
# Check database exists
ls -la data/aupat.db

# Recreate schema
python scripts/db_migrate.py
```

## Testing

Test data in `tempdata/testphotos/`:
- Middletown State Hospital (8 Nikon NEF files)
- Water Slide World (DNG files + videos)

Use for pipeline testing.

## License

See LICENSE file.

## Status

Stage 1 (CLI/Web Import Tool) - Active development

Future stages:
- Stage 2: Enhanced web interface
- Stage 3: Docker deployment
- Stage 4: Mobile app with Docker backend
