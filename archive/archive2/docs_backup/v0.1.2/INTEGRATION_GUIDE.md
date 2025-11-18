# AUPATOOL v0.1.2 Integration Guide

## Overview

This guide explains how to integrate v0.1.2 enhancements into the existing AUPAT system.

## Phase 1 Integration Steps

### Step 1: Database Schema Migration

Run the v0.1.2 database migration to add new columns and tables:

```bash
# Backup database first (automated in migration script)
python scripts/db_migrate_v012.py

# Or specify custom config
python scripts/db_migrate_v012.py --config /path/to/user.json
```

This adds:
- GPS coordinates (lat, lon) to locations table
- Address fields to locations table
- immich_asset_id to images and videos tables
- Enhanced metadata columns (dimensions, file sizes)
- ArchiveBox integration columns to urls table
- New tables: google_maps_exports, sync_log
- Performance indexes for map queries

### Step 2: Install New Dependencies

Update Python dependencies:

```bash
# Activate virtual environment
source venv/bin/activate

# Install new requirements
pip install -r requirements.txt
```

New dependencies:
- `requests` - HTTP client for Immich/ArchiveBox APIs
- `tenacity` - Retry logic for API calls
- `Pillow` - Image dimension extraction

### Step 3: Docker Compose Setup

Start all services using Docker Compose:

```bash
# First time setup
./docker-start.sh

# Or manually
docker-compose up -d
```

This starts:
- AUPAT Core (Flask API) on port 5000
- Immich (photo storage) on port 2283
- ArchiveBox (web archiving) on port 8001
- PostgreSQL (Immich database)
- Redis (Immich cache)

Verify services are healthy:

```bash
docker-compose ps
docker-compose logs -f
```

### Step 4: Integrate API Routes into web_interface.py

Add the new API routes to the existing Flask app:

```python
# In web_interface.py, add this import at the top:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from api_routes_v012 import register_api_routes

# After creating the Flask app, add this:
app = Flask(__name__)

# Configure database path
app.config['DB_PATH'] = '/path/to/aupat.db'  # Or load from user.json

# Register v0.1.2 API routes
register_api_routes(app)

# ... rest of existing app code
```

Example full integration:

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from flask import Flask, render_template

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

# Import v0.1.2 API routes
from api_routes_v012 import register_api_routes

# Create Flask app
app = Flask(__name__)

# Load user config
config_path = Path(__file__).parent / 'user' / 'user.json'
with open(config_path) as f:
    config = json.load(f)

# Configure app
app.config['DB_PATH'] = config['db_loc']

# Register v0.1.2 API routes
register_api_routes(app)

# ... existing routes ...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Step 5: Use Enhanced Import Pipeline

Use the new import script with Immich integration:

```bash
# Standard import with Immich
python scripts/db_import_v012.py \
    --source /path/to/photos \
    --metadata metadata.json

# Import without Immich (fallback)
python scripts/db_import_v012.py \
    --source /path/to/photos \
    --metadata metadata.json \
    --no-immich
```

The enhanced import automatically:
- Uploads photos/videos to Immich
- Extracts GPS coordinates from EXIF
- Calculates image/video dimensions
- Stores file sizes
- Updates location GPS from first photo with coordinates

### Step 6: Verify Integration

Test the new API endpoints:

```bash
# Health check
curl http://localhost:5000/api/health

# Service health
curl http://localhost:5000/api/health/services

# Map markers (all locations with GPS)
curl http://localhost:5000/api/map/markers

# Location details
curl http://localhost:5000/api/locations/{loc_uuid}

# Location images with Immich asset IDs
curl http://localhost:5000/api/locations/{loc_uuid}/images
```

Expected responses:

```json
// /api/health
{
  "status": "ok",
  "version": "0.1.2",
  "database": "connected",
  "location_count": 42
}

// /api/health/services
{
  "status": "ok",
  "services": {
    "immich": "healthy",
    "archivebox": "healthy"
  }
}

// /api/map/markers
[
  {
    "loc_uuid": "a1b2c3d4...",
    "loc_name": "Abandoned Factory",
    "lat": 42.8142,
    "lon": -73.9396,
    "type": "industrial",
    "state": "ny"
  },
  ...
]

// /api/locations/{uuid}/images
[
  {
    "img_sha256": "abc123...",
    "img_name": "a1b2c3d4-abc12345.jpg",
    "immich_asset_id": "xyz789...",
    "img_width": 6000,
    "img_height": 4000,
    "img_size_bytes": 15728640,
    "gps_lat": 42.8142,
    "gps_lon": -73.9396,
    "camera": 1,
    "phone": 0,
    "drone": 0
  },
  ...
]
```

## Troubleshooting

### Database Migration Issues

**Error: "Database not found"**
- Solution: Run `python scripts/db_migrate.py` first to create initial schema

**Error: "Column already exists"**
- Solution: Migration is idempotent, safe to re-run. It will skip existing columns.

### Docker Issues

**Error: "Port already in use"**
- Solution: Change ports in docker-compose.yml or stop conflicting services

**Error: "Immich service unhealthy"**
- Solution: Check logs with `docker-compose logs immich-server`
- Verify PostgreSQL is running: `docker-compose ps immich-postgres`
- Wait 1-2 minutes for ML service to download models on first start

**Error: "Cannot connect to Docker daemon"**
- Solution: Start Docker Desktop or run `sudo systemctl start docker`

### Import Issues

**Warning: "Immich service unavailable"**
- This is expected if Immich not running
- Import continues without Immich integration
- immich_asset_id fields will be NULL
- Can upload to Immich later using separate script

**Error: "exiftool not found"**
- Solution: Install exiftool
  - macOS: `brew install exiftool`
  - Ubuntu: `apt install libimage-exiftool-perl`

**Error: "ffprobe not found"**
- Solution: Install ffmpeg
  - macOS: `brew install ffmpeg`
  - Ubuntu: `apt install ffmpeg`

### API Issues

**Error: "CORS policy blocking request"**
- Solution: API routes include CORS headers by default
- Verify `Access-Control-Allow-Origin: *` in response headers
- For production, restrict to specific origins in api_routes_v012.py

**Error: 404 on /api/* endpoints**
- Solution: Verify `register_api_routes(app)` was called in web_interface.py
- Check Flask logs for registration messages

## Backward Compatibility

All v0.1.2 enhancements are backward compatible:

- **Database**: New columns added with ALTER TABLE (non-destructive)
- **Import Scripts**: Original db_import.py still works
- **API**: New endpoints added, existing routes unchanged
- **Optional Features**: Immich/ArchiveBox integration is optional

You can:
1. Run v0.1.2 migration and continue using old import scripts
2. Use new import script with `--no-immich` flag
3. Mix old and new workflows

## Next Steps

After completing Phase 1 integration:

1. **Test import pipeline**: Import 100 photos to verify Immich integration
2. **Verify map data**: Check that locations have GPS coordinates
3. **Desktop app development**: Use API endpoints to build Electron app (Phase 2)

See `04_BUILD_PLAN.md` for full Phase 2-5 roadmap.

## Support

- Documentation: `/docs/v0.1.2/`
- Logs: `docker-compose logs -f`
- Health check: `curl http://localhost:5000/api/health/services`
