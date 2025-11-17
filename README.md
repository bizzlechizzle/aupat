# AUPAT v0.1.2

**Abandoned Upstate Project Archive Tool**

Digital asset management system for location-based media archives with Immich photo storage and ArchiveBox web archiving integration.

**Current Version**: v0.1.2 (Microservices Architecture)

---

## What It Does

AUPAT organizes photos, videos, and web content by geographic location with automatic metadata extraction, hardware categorization, and external service integration.

**v0.1.2 Architecture**:
- Docker Compose orchestration (6 services)
- Immich for photo storage and facial recognition
- ArchiveBox for web page archiving
- REST API for desktop/mobile app integration
- GPS coordinate extraction and map visualization
- Bulletproof data integrity with SHA256 deduplication

---

## Quick Start

### Prerequisites

- macOS or Linux
- Docker Desktop (for macOS) or Docker Engine (for Linux)
- 4GB+ RAM recommended
- 10GB+ free disk space

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/aupat.git
cd aupat

# Run install script (macOS or Linux)
chmod +x install.sh
./install.sh

# Activate virtual environment
source venv/bin/activate

# Configure environment (copy and edit .env.example)
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# Run database migration
python scripts/db_migrate_v012.py

# Check service health
curl http://localhost:5000/api/health
```

### First Import

```bash
# Import a location with photos
python scripts/db_import_v012.py

# Check map markers
curl http://localhost:5000/api/map/markers

# View in Immich
open http://localhost:2283
```

---

## Architecture

### Service Stack

| Service | Port | Purpose |
|---------|------|---------|
| AUPAT Core | 5000 | Flask REST API |
| Immich Server | 2283 | Photo storage and ML |
| Immich ML | - | Facial recognition, object detection |
| PostgreSQL | 5432 | Immich database |
| Redis | 6379 | Immich cache |
| ArchiveBox | 8001 | Web archiving |

### Directory Structure

```
aupat/
├── scripts/                # v0.1.2 Python modules
│   ├── adapters/           # Service adapters (Immich, ArchiveBox)
│   ├── db_migrate_v012.py  # Database migration
│   ├── db_import_v012.py   # Import pipeline
│   ├── api_routes_v012.py  # REST API endpoints
│   └── immich_integration.py  # Immich upload + GPS extraction
├── tests/                  # Comprehensive test suite
├── docs/v0.1.2/            # Complete documentation
├── data/                   # JSON configuration files
├── user/                   # User configuration (gitignored)
├── docker-compose.yml      # Service orchestration
├── Dockerfile              # AUPAT Core container
├── requirements.txt        # Python dependencies
└── archive/                # Historical versions (v0.1.0)
```

---

## API Endpoints

### Health Check

```bash
GET /api/health
GET /api/health/services
```

### Map Data

```bash
# Get all locations with GPS coordinates
GET /api/map/markers?limit=1000

# Filter by bounding box
GET /api/map/markers?bounds=minLat,minLon,maxLat,maxLon
```

### Location Details

```bash
# Get location with media counts
GET /api/locations/{loc_uuid}

# Get images for location
GET /api/locations/{loc_uuid}/images?limit=100&offset=0

# Get videos for location
GET /api/locations/{loc_uuid}/videos

# Get archived URLs
GET /api/locations/{loc_uuid}/archives
```

### Search

```bash
# Search locations by name, state, or type
GET /api/search?q=hospital&state=ny&type=hospital&limit=50
```

---

## Features

### Phase 1 (Current)

- **Docker Compose orchestration** - 6-service stack with health checks
- **Immich integration** - Photo upload, GPS extraction, thumbnail URLs
- **ArchiveBox integration** - Web page archiving with media extraction
- **REST API** - 10+ endpoints for desktop app
- **Database migration** - v0.1.2 schema with GPS, addresses, service IDs
- **Comprehensive testing** - 72 test cases with 88% coverage
- **Graceful degradation** - Works even if Immich/ArchiveBox unavailable

### Future Phases

- **Phase 2**: Desktop app with map interface (Electron + React)
- **Phase 3**: Enhanced Dockerization with automated backups
- **Phase 4**: Mobile app with offline mode

---

## Configuration

### Environment Variables (.env)

```bash
# Immich Configuration
IMMICH_URL=http://immich-server:3001
IMMICH_API_KEY=your-api-key-here

# ArchiveBox Configuration
ARCHIVEBOX_URL=http://archivebox:8000
ARCHIVEBOX_USERNAME=admin
ARCHIVEBOX_PASSWORD=your-password-here

# Database Configuration
DB_PATH=/app/data/aupat.db
```

### User Configuration (user/user.json)

```json
{
  "db_name": "aupat.db",
  "db_loc": "/path/to/aupat/data/aupat.db",
  "db_backup": "/path/to/aupat/data/backups/",
  "db_ingest": "/path/to/aupat/data/ingest/",
  "arch_loc": "/path/to/aupat/data/archive/"
}
```

**Note**: Created automatically by `install.sh` with absolute paths.

---

## Database Schema (v0.1.2)

### Enhanced Tables

**locations**
- Added: `lat`, `lon`, `gps_source`, `gps_confidence`
- Added: `street_address`, `city`, `state_abbrev`, `zip_code`, `country`, `address_source`

**images**
- Added: `immich_asset_id` (unique)
- Added: `img_width`, `img_height`, `img_size_bytes`
- Added: `gps_lat`, `gps_lon` (per-image GPS)

**videos**
- Added: `immich_asset_id` (unique)
- Added: `vid_width`, `vid_height`, `vid_duration_sec`, `vid_size_bytes`
- Added: `gps_lat`, `gps_lon` (per-video GPS)

**urls**
- Added: `archivebox_snapshot_id`
- Added: `archive_status`, `archive_date`, `media_extracted`

### New Tables

**google_maps_exports** - Track Google Maps imports
**sync_log** - Mobile sync tracking (Phase 4)

---

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=scripts --cov-report=term-missing

# Run specific test file
pytest tests/test_adapters.py -v

# Run Docker integration tests (requires docker-compose up)
pytest -v -m requires_docker
```

### Code Quality

```bash
# Type checking (if mypy installed)
mypy scripts/

# Linting (if ruff installed)
ruff check scripts/

# Format code (if black installed)
black scripts/ tests/
```

### Database Migration

```bash
# Run v0.1.2 migration
python scripts/db_migrate_v012.py

# Migration creates backup automatically
# Idempotent: safe to run multiple times
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# Check service logs
docker-compose logs aupat-core
docker-compose logs immich-server

# Restart services
docker-compose restart

# Full rebuild
docker-compose down
docker-compose up -d --build
```

### Health Check Fails

```bash
# Check if services are up
curl http://localhost:5000/api/health
curl http://localhost:2283/api/server-info/ping

# Check service logs
docker-compose logs -f aupat-core
```

### Import Fails

```bash
# Check Immich is healthy
curl http://localhost:2283/api/server-info/ping

# Check database exists
ls -la data/aupat.db

# Run migration
python scripts/db_migrate_v012.py

# Check logs
tail -f logs/aupat.log
```

### GPS Extraction Fails

```bash
# Verify exiftool installed
exiftool -ver

# Check if image has GPS data
exiftool -GPSLatitude -GPSLongitude /path/to/image.jpg

# Manual test
python -c "from scripts.immich_integration import extract_gps_from_exif; print(extract_gps_from_exif('/path/to/image.jpg'))"
```

---

## Documentation

Full technical documentation in `docs/v0.1.2/`:

- **01_OVERVIEW.md** - Project overview and goals
- **02_ARCHITECTURE.md** - System architecture and design
- **03_MODULES.md** - Module specifications
- **04_BUILD_PLAN.md** - Implementation plan
- **05_TESTING.md** - Testing strategy
- **PHASE1_TEST_REPORT.md** - Comprehensive test results
- **PHASE1_WWYDD.md** - Improvement recommendations

---

## Archived Versions

Previous versions have been archived for reference:

- **archive/v0.1.0/** - Original CLI pipeline and web interface
  - Monolithic Flask app with local processing
  - No external service integration
  - See `archive/v0.1.0/README.md` for details

**Not recommended for new deployments. Use v0.1.2 instead.**

---

## Engineering Principles

This project follows strict engineering principles:

- **KISS** - Keep It Simple, Stupid (no over-engineering)
- **BPL** - Bulletproof Long-term (3-10+ year reliability)
- **BPA** - Best Practices Always (industry standards)
- **DRETW** - Don't Reinvent The Wheel (use proven libraries)
- **NME** - No Emojis Ever (professional documentation)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow engineering principles (KISS, BPL, BPA)
4. Write tests for new code
5. Ensure all tests pass (`pytest -v`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## License

See LICENSE file.

---

## Credits

**Built with**: Python, Docker, Flask, Immich, ArchiveBox, SQLite, PostgreSQL, Redis

**Principles**: KISS, BPL, BPA, DRETW, NME

**Version**: v0.1.2 (Phase 1 Foundation)

**Last Updated**: November 2025
