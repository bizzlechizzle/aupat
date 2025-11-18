# Abandoned Upstate

**Digital archive for abandoned and historical locations across Upstate New York**

A desktop application for documenting, organizing, and exploring abandoned places through photos, maps, and rich metadata.

---

## Quick Start

### Prerequisites

- macOS or Linux
- Python 3.8+
- Node.js 16+ and npm
- 4GB+ RAM
- 10GB+ free disk space

### Installation

```bash
# Clone repository
git clone https://github.com/bizzlechizzle/aupat.git
cd aupat

# Run installation script
chmod +x install.sh
./install.sh

# Activate virtual environment
source venv/bin/activate
```

### Starting the App

**NEW: Unified Launch Script** (Recommended)

```bash
# Start development environment (API + Desktop)
./launch.sh --dev

# Or use legacy script
./start_aupat.sh
```

The app will automatically:
- Start the Flask API server on port 5002
- Launch the Electron desktop app
- Open the map interface

**Other launch options:**
```bash
./launch.sh --api      # API server only
./launch.sh --docker   # Full stack with Docker
./launch.sh --status   # Check running services
./launch.sh --stop     # Stop all services
./launch.sh --health   # Run health checks
./launch.sh --help     # Show all options
```

### Database Migrations

**NEW: Migration Orchestrator** (2025-11-18)

After pulling updates that include database changes, use the migration orchestrator:

```bash
# Check migration status
python scripts/migrate.py --status

# List all available migrations
python scripts/migrate.py --list

# Upgrade to latest version
python scripts/migrate.py --upgrade

# Upgrade to specific version
python scripts/migrate.py --upgrade 0.1.4
```

The migration orchestrator:
- Automatically detects which migrations are needed
- Runs migrations in the correct order
- Backs up your database before each migration
- Tracks which migrations have been applied
- Is safe to re-run (idempotent)

### Updating After Git Pull

**Important**: After pulling updates, always run:

```bash
# Quick way (recommended)
./update_and_start.sh

# Manual way
cd desktop && npm install && cd ..
./start_aupat.sh
```

See `UPDATE_WORKFLOW.md` for detailed update instructions.

---

## Features

### Core Features

- **Interactive Map** - Leaflet-based map showing all documented locations
- **Location Pages** - Blog-style dedicated pages for each location with rich content
- **Photo Management** - Import, organize, and view photos with EXIF data extraction
- **Metadata Tracking** - GPS coordinates, addresses, location types, visit dates
- **Import Tools** - CSV, GeoJSON import support (KML/KMZ planned)
- **Search & Filter** - Find locations by name, type, state, city, or author

### Desktop App

Built with Electron + Svelte + Vite for a modern, responsive interface:

- **Map View** - Interactive map with location markers and clustering
- **Locations List** - Sortable, filterable table of all locations
- **Location Pages** - Dedicated view for each location with:
  - Photo galleries with lightbox
  - Rich metadata display
  - Clickable hyperlinks
  - Markdown support for descriptions
  - Navigation between related locations
- **Import** - Drag-and-drop map file import
- **Settings** - Configure API URLs, map defaults, and preferences

### Backend API

Flask-based REST API with SQLite database:

- **Locations API** - CRUD operations for locations
- **Images API** - Photo upload, metadata, thumbnails
- **Map API** - GeoJSON markers with clustering support
- **Search API** - Full-text search across locations
- **Archives API** - Archived URL management (ArchiveBox integration)
- **Bookmarks API** - Browser bookmark integration (backend only, UI pending)

---

## Architecture

### Technology Stack

**Frontend (Desktop App)**
- Electron 28+
- Svelte 4
- Vite 5
- Leaflet (maps)
- Marked (markdown rendering)
- TailwindCSS (styling)

**Backend (API Server)**
- Python 3.8+
- Flask 3.0
- SQLite 3
- PIL/Pillow (image processing)
- ExifTool integration (GPS extraction)

**Optional Integrations**
- Immich (photo management)
- ArchiveBox (web archiving)

### Project Structure

```
aupat/
├── desktop/                    # Electron desktop app
│   ├── src/
│   │   ├── main/              # Electron main process
│   │   ├── renderer/          # Svelte frontend
│   │   │   ├── lib/           # Svelte components
│   │   │   ├── stores/        # State management
│   │   │   ├── styles/        # CSS and themes
│   │   │   └── assets/        # Images, icons
│   │   └── preload/           # IPC bridge
│   └── package.json
├── scripts/                    # Backend Python modules
│   ├── api_routes_v012.py     # Main API routes
│   ├── api_routes_bookmarks.py # Browser bookmarks API
│   ├── immich_integration.py  # Immich adapter
│   ├── archivebox_adapter.py  # ArchiveBox adapter
│   └── migrations/            # Database migrations
├── data/                      # SQLite database
├── tests/                     # Test suite
├── app.py                     # Flask application
├── start_aupat.sh            # Startup script
├── update_and_start.sh       # Update helper
└── README.md                  # This file
```

---

## API Reference

### Base URL

```
http://localhost:5002/api
```

### Interactive API Documentation

**NEW: Swagger/OpenAPI Documentation** (v0.1.6)

Explore and test the API interactively using the built-in Swagger UI:

```
http://localhost:5002/api/docs
```

Features:
- Interactive API explorer with "Try it out" functionality
- Complete endpoint documentation with parameters and responses
- OpenAPI 2.0 specification available at `/api/apispec.json`
- Organized by tags (health, locations, map, search, media, etc.)

### Health Check

```bash
GET /api/health
```

### Locations

```bash
# List all locations
GET /api/locations

# Get specific location
GET /api/locations/{uuid}

# Create location
POST /api/locations

# Update location
PUT /api/locations/{uuid}

# Delete location
DELETE /api/locations/{uuid}
```

### Images

```bash
# Get images for location
GET /api/locations/{uuid}/images?limit=50&offset=0

# Upload image
POST /api/locations/{uuid}/import

# Get image file
GET /api/images/{uuid}/file
```

### Map Data

```bash
# Get map markers (GeoJSON)
GET /api/map/markers?limit=1000
```

### Search

```bash
# Search locations
GET /api/search?q=hospital&state=ny&type=abandoned
```

### Autocomplete

```bash
# Get autocomplete suggestions
GET /api/locations/autocomplete/type
GET /api/locations/autocomplete/state
GET /api/locations/autocomplete/city
GET /api/locations/autocomplete/sub_type?type=industrial
```

---

## Database Schema

### Core Tables

**locations** - Main location records
- `loc_uuid` - Unique identifier
- `loc_name` - Location name
- `aka_name` - Alternate names
- `type` - Location type (industrial, commercial, residential, etc.)
- `sub_type` - Subcategory
- `state`, `city`, `street_address`, `zip_code` - Address
- `lat`, `lon` - GPS coordinates
- `gps_source` - How coordinates were obtained
- `imp_author` - Who added the location
- `loc_add`, `loc_update` - Timestamps

**images** - Photo metadata
- `img_uuid` - Unique identifier
- `loc_uuid` - Associated location
- `img_fn` - Original filename
- `img_loc` - File path
- `img_sha256` - Content hash (deduplication)
- `img_width`, `img_height`, `img_size_bytes` - Dimensions
- `gps_lat`, `gps_lon` - Per-image GPS
- `immich_asset_id` - Immich integration

**urls** - Archived web pages
- `url_uuid` - Unique identifier
- `loc_uuid` - Associated location
- `url_title` - Page title
- `url_link` - URL
- `archivebox_snapshot_id` - ArchiveBox integration

**bookmarks** - Browser bookmarks (backend only)
- Integration with Chrome/Firefox/Safari bookmarks
- Auto-associate bookmarks with locations

---

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest -v

# Run with coverage
pytest --cov=scripts --cov-report=term-missing

# Run specific test file
pytest tests/test_api_routes.py -v
```

### Frontend Development

```bash
cd desktop

# Install dependencies
npm install

# Run dev server (hot reload)
npm run dev

# Build for production
npm run build

# Type checking
npm run typecheck

# Linting
npm run lint
```

### Backend Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run Flask in debug mode
FLASK_ENV=development python app.py

# Run database migration
python scripts/db_migrate_v012.py

# Run import script
python scripts/db_import_v012.py
```

### Type Checking

**NEW: Python Type Hints** (v0.1.6)

High-priority modules now have comprehensive type hints for better IDE support and code quality:

```bash
# Install mypy (optional)
pip install mypy

# Run type checking on all modules
mypy scripts/ app.py

# Run type checking on specific module
mypy scripts/utils.py
```

**Fully Typed Modules:**
- `scripts/utils.py` - UUID generation, SHA256 hashing, filename generation
- `scripts/normalize.py` - Text and data normalization functions
- `scripts/adapters/immich_adapter.py` - Immich photo storage adapter
- `scripts/adapters/archivebox_adapter.py` - ArchiveBox web archiving adapter

Configuration in `mypy.ini` with strict checking enabled for fully-typed modules.

---

## Configuration

### Database Location

Default: `data/aupat.db`

Override with environment variable:
```bash
export DB_PATH=/custom/path/aupat.db
```

### API Settings

Configure in the desktop app Settings page:
- AUPAT Core API URL (default: `http://localhost:5002`)
- Immich API URL
- ArchiveBox API URL
- Map defaults (center coordinates, zoom level)

### Optional: Immich Integration

For advanced photo management:

```bash
# Set Immich URL and API key
IMMICH_URL=http://localhost:2283
IMMICH_API_KEY=your-api-key-here
```

Features:
- Automatic photo upload to Immich
- GPS coordinate extraction from EXIF
- Thumbnail generation
- Duplicate detection

### Optional: ArchiveBox Integration

For web page archiving:

```bash
# Set ArchiveBox URL and credentials
ARCHIVEBOX_URL=http://localhost:8000
ARCHIVEBOX_USERNAME=admin
ARCHIVEBOX_PASSWORD=your-password
```

---

## Branding

**Visual Identity**: Inspired by the original [abandonedupstate.com](https://abandonedupstate.com) aesthetic

- **Colors**: Cream background, dark gray text, warm brown accents
- **Typography**: Roboto Mono (headings), Lora (body text)
- **Design**: Moody, exploration-focused, information-rich
- **Theme**: Available in `desktop/src/renderer/styles/theme.css`

See `BRANDING_PLAN.md` for complete brand guidelines.

---

## Roadmap

### Current (v0.1.2)
- ✅ Desktop app with map interface
- ✅ Location pages with blog-style layout
- ✅ Photo import and management
- ✅ CSV/GeoJSON map import
- ✅ REST API with autocomplete
- ✅ Browser bookmarks backend

### Planned Features
- 🔲 KML/KMZ import support
- 🔲 Browser bookmarks UI
- 🔲 Advanced search filters
- 🔲 Location relationship mapping
- 🔲 Visit history tracking
- 🔲 Export to various formats
- 🔲 Mobile companion app

See `IMPLEMENTATION_STATUS.md` for detailed status.

---

## Troubleshooting

### Port Already in Use

```bash
# Kill existing Flask process
pkill -f "python.*app.py"

# Then restart
./start_aupat.sh
```

### Blank White Screen

**Cause**: Missing npm dependencies after git pull

**Fix**:
```bash
cd desktop && npm install && cd ..
./start_aupat.sh
```

### Database Errors

```bash
# Run migration
python scripts/db_migrate_v012.py

# Check database exists
ls -la data/aupat.db

# If corrupted, restore from backup
cp data/backups/aupat_backup_*.db data/aupat.db
```

### Import Fails

```bash
# Check logs
tail -f logs/aupat.log

# Verify file permissions
ls -la data/ingest/

# Test API health
curl http://localhost:5002/api/health
```

### Map Not Loading

1. Check browser console (View > Developer > Developer Tools)
2. Verify API is running: `curl http://localhost:5002/api/health`
3. Check map markers endpoint: `curl http://localhost:5002/api/map/markers`
4. Restart app: Ctrl+C then `./start_aupat.sh`

---

## Documentation

### Core Documentation (Start Here)
- **`README.md`** - This file - project overview and quick start
- **`claude.md`** - Development rules and 10-step process (READ THIS FIRST for development)
- **`techguide.md`** - Complete technical reference and architecture
- **`lilbits.md`** - All scripts documented with examples
- **`todo.md`** - Current tasks, gaps, and roadmap

### Additional Documentation
- `QUICKSTART.md` - Quick reference guide
- `UPDATE_WORKFLOW.md` - How to update after git pull
- `BRANDING_PLAN.md` - Visual identity and design system
- `IMPLEMENTATION_STATUS.md` - Feature status tracker
- `REVAMP_PLAN.md` - UI redesign specifications
- `BROWSER_INTEGRATION_WWYDD.md` - Browser bookmarks integration

### Technical Documentation
- `docs/dependency_map.md` - Complete file dependency analysis
- `CODEBASE_AUDIT_COMPLETE.md` - Comprehensive codebase audit
- `docs/PRODUCTION_DEPLOYMENT.md` - Production deployment guide with security, SSL, monitoring
- `docs/v0.1.2/` - Versioned documentation (18 files)

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Write or update tests
5. Ensure tests pass: `pytest -v`
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Open a Pull Request

---

## License

See LICENSE file.

---

## Credits

**Project**: Abandoned Upstate Photo & Archive Tracker (AUPAT)

**Built With**:
- Electron, Svelte, Vite, Leaflet
- Python, Flask, SQLite
- Marked, TailwindCSS

**Inspired By**: [abandonedupstate.com](https://abandonedupstate.com)

**Version**: v0.1.2

**Last Updated**: November 2024
