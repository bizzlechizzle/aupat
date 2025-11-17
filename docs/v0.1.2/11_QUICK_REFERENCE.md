# AUPATOOL v0.1.2 - Quick Reference Guide

## One-Page Cheat Sheet

### Start/Stop Services

```bash
# Start
cd ~/Documents/aupat
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# Status
docker compose ps
```

### Common Tasks

| Task | Command |
|------|---------|
| View logs | `docker compose logs -f` |
| Backup database | `./scripts/backup.sh` |
| Check disk usage | `du -sh data/` |
| Import photos | Use desktop app → Import tab |
| View map | Use desktop app → Map tab |
| Archive URL | Use desktop app → Archive tab |
| Check API health | `curl localhost:5000/api/health` |

### File Locations

| What | Where |
|------|-------|
| Database | `data/aupat.db` |
| Photos (Immich) | `data/immich/` |
| Archives | `data/archivebox/` |
| Backups | `data/backups/` |
| Logs | `data/logs/` |
| Config | `.env` |

### Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| AUPAT Core API | http://localhost:5000 | REST API |
| Immich | http://localhost:2283 | Photo manager |
| ArchiveBox | http://localhost:8001 | Web archive |
| Desktop App | Local application | Main UI |

---

## Daily Workflow

### 1. Import Photos

**Via Desktop App:**
1. Open desktop app
2. Click "Import" tab
3. Drag folder of photos
4. Select location from dropdown
5. Click "Start Import"
6. Wait for completion (progress bar shows status)

**Via Command Line:**
```bash
python scripts/db_import.py \
  --location-uuid <UUID> \
  --images-dir /path/to/photos \
  --upload-to-immich
```

### 2. View Locations on Map

**Desktop App:**
1. Click "Map" tab
2. Zoom/pan to explore
3. Clusters expand as you zoom in
4. Click marker → location details sidebar
5. Click photo thumbnail → full-size view

**Filter locations:**
- Search box: Type location name
- Filter dropdown: By type (factory, mill, hospital, etc.)

### 3. Archive Web Page

**Desktop App:**
1. Click "Archive" tab
2. Browse to URL in embedded browser
3. Click "Archive" button
4. Select location to associate with
5. Enable "High-res extraction" if needed
6. Wait for archive completion (notification shows)
7. Extracted media automatically added to location

**Via API:**
```bash
curl -X POST http://localhost:5000/api/locations/<UUID>/archive \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/page"}'
```

### 4. Edit Location

**Desktop App:**
1. Click location on map or in list
2. Click "Edit" button
3. Update fields (name, type, address, GPS)
4. Click "Save"

**Via API:**
```bash
curl -X PUT http://localhost:5000/api/locations/<UUID> \
  -H "Content-Type: application/json" \
  -d '{"loc_name": "Updated Name", "lat": 42.8142, "lon": -73.9396}'
```

### 5. Search Locations

**Desktop App:**
- Type in search box → filters map and list
- Search by: Name, address, type

**Via API:**
```bash
curl "http://localhost:5000/api/search?q=factory"
```

---

## Database Operations

### Query Database Directly

```bash
# Connect to database
sqlite3 data/aupat.db

# List all locations
SELECT loc_uuid, loc_name, loc_type, lat, lon FROM locations LIMIT 10;

# Count photos
SELECT COUNT(*) FROM images;

# Find locations with GPS
SELECT COUNT(*) FROM locations WHERE lat IS NOT NULL;

# Photos per location
SELECT l.loc_name, COUNT(i.img_sha256) as photo_count
FROM locations l
LEFT JOIN images i ON l.loc_uuid = i.loc_uuid
GROUP BY l.loc_uuid
ORDER BY photo_count DESC
LIMIT 10;

# Exit
.exit
```

### Export Data

```bash
# Export locations to JSON
curl http://localhost:5000/api/locations > locations.json

# Export to CSV
sqlite3 -header -csv data/aupat.db "SELECT * FROM locations;" > locations.csv

# Export map markers (for external tools)
curl http://localhost:5000/api/map/markers > markers.json
```

### Backup/Restore

```bash
# Manual backup
cp data/aupat.db data/backups/aupat_$(date +%Y%m%d).db

# Automated backup (runs daily via cron)
./scripts/backup.sh

# Restore from backup
docker compose down
cp data/backups/aupat_20250115.db data/aupat.db
docker compose up -d

# Verify restore
sqlite3 data/aupat.db "PRAGMA integrity_check;"
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# Check port conflicts
lsof -i :5000  # Mac/Linux

# View detailed logs
docker compose logs -f aupat-core

# Restart specific service
docker compose restart immich-server

# Rebuild service
docker compose up -d --build aupat-core
```

### Import Fails

```bash
# Check AUPAT Core logs
docker compose logs -f aupat-core

# Check Immich status
curl http://localhost:2283/api/server-info/ping

# Test file permissions
ls -la /path/to/photos

# Retry import with verbose logging
python scripts/db_import.py --verbose --images-dir /path/to/photos
```

### Slow Performance

```bash
# Check disk space
df -h

# Check Docker resource usage
docker stats

# Optimize database
sqlite3 data/aupat.db "VACUUM; ANALYZE;"

# Clear old Docker images
docker system prune -a

# Restart services
docker compose restart
```

### Database Corruption

```bash
# Check integrity
sqlite3 data/aupat.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
docker compose down
cp data/backups/aupat_<DATE>.db data/aupat.db
docker compose up -d
```

### Immich ML Not Working

```bash
# Check ML service
docker compose logs -f immich-ml

# GPU not detected (use CPU)
# Edit .env: IMMICH_ML_DEVICE=cpu
docker compose up -d --force-recreate immich-ml

# Disable ML entirely
# Immich UI → Settings → Machine Learning → Disable
```

---

## API Quick Reference

### Locations

```bash
# List all
GET /api/locations

# Get one
GET /api/locations/{uuid}

# Create
POST /api/locations
{"loc_name": "Name", "loc_type": "factory", "lat": 42.8, "lon": -73.9}

# Update
PUT /api/locations/{uuid}
{"loc_name": "Updated Name"}

# Delete (soft delete)
DELETE /api/locations/{uuid}
```

### Media

```bash
# List images for location
GET /api/locations/{uuid}/images

# List videos for location
GET /api/locations/{uuid}/videos

# Import images
POST /api/import/images
{"loc_uuid": "...", "file_paths": ["..."]}
```

### Archives

```bash
# List archived URLs for location
GET /api/locations/{uuid}/archives

# Archive new URL
POST /api/locations/{uuid}/archive
{"url": "https://example.com", "high_res_mode": true}

# Check archive status
GET /api/import/status/{job_id}
```

### Map

```bash
# Get all location markers (for map)
GET /api/map/markers
# Returns: [{"loc_uuid": "...", "lat": 42.8, "lon": -73.9, "loc_name": "..."}]

# Get map bounds
GET /api/map/bounds
# Returns: {"min_lat": 40, "max_lat": 45, "min_lon": -75, "max_lon": -70}
```

### Search

```bash
# Search by query
GET /api/search?q=factory

# Find nearby locations
GET /api/search/nearby?lat=42.8142&lon=-73.9396&radius=10
```

---

## Desktop App Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Cmd/Ctrl + F | Focus search |
| Cmd/Ctrl + I | Open import dialog |
| Cmd/Ctrl + M | Switch to map view |
| Cmd/Ctrl + L | Switch to list view |
| Cmd/Ctrl + , | Open settings |
| Escape | Close dialog/sidebar |
| Arrow keys | Navigate map |
| Space | Toggle location details |

---

## Docker Compose Commands

```bash
# View services
docker compose ps

# View logs
docker compose logs -f [service_name]

# Restart service
docker compose restart [service_name]

# Rebuild service
docker compose up -d --build [service_name]

# Update images
docker compose pull
docker compose up -d

# Remove everything (WARNING: Deletes data in volumes)
docker compose down -v

# View resource usage
docker stats
```

---

## Database Maintenance

### Monthly Tasks

```bash
# Run integrity check
sqlite3 data/aupat.db "PRAGMA integrity_check;"

# Optimize database
sqlite3 data/aupat.db "VACUUM; ANALYZE;"

# Check database size
ls -lh data/aupat.db

# Count records
sqlite3 data/aupat.db << EOF
SELECT 'Locations:', COUNT(*) FROM locations;
SELECT 'Images:', COUNT(*) FROM images;
SELECT 'Videos:', COUNT(*) FROM videos;
SELECT 'URLs:', COUNT(*) FROM urls;
EOF
```

### Cleanup Old Data (Optional)

```bash
# Remove deleted locations (soft-deleted, marked for deletion)
sqlite3 data/aupat.db "DELETE FROM locations WHERE deleted_at IS NOT NULL;"

# Remove orphaned images (no location reference)
sqlite3 data/aupat.db "DELETE FROM images WHERE loc_uuid NOT IN (SELECT loc_uuid FROM locations);"

# Archive old logs
gzip data/logs/*.log

# Clean old backups (keep last 30 days)
find data/backups/ -name "aupat_*.db" -mtime +30 -delete
```

---

## Immich Quick Tips

### Access Immich Web UI

```bash
# Open in browser
open http://localhost:2283  # Mac
xdg-open http://localhost:2283  # Linux

# Login with credentials created during setup
```

### Common Immich Tasks

**View all photos:**
- Immich UI → Photos

**Search by AI tags:**
- Immich UI → Search → Type tag (e.g., "building", "abandoned")

**Create album:**
- Immich UI → Albums → Create Album → Add photos

**Download original:**
- Click photo → ... menu → Download

**Share photo:**
- Click photo → Share → Generate link

---

## ArchiveBox Quick Tips

### Access ArchiveBox Web UI

```bash
# Open in browser
open http://localhost:8001  # Mac
xdg-open http://localhost:8001  # Linux

# Login with superuser credentials
```

### Common ArchiveBox Tasks

**Add URL manually:**
- ArchiveBox UI → Add → Enter URL → Submit

**View archive:**
- ArchiveBox UI → Snapshots → Click URL

**Re-archive (update):**
- Click URL → Re-archive button

**Export archive:**
- Settings → Export → Download as ZIP

**Search archived pages:**
- Search box → Enter keywords

---

## Performance Tuning

### For Large Datasets (100k+ photos)

```bash
# Increase Docker resources
# Docker Desktop → Settings → Resources
# RAM: 8 GB minimum, 16 GB recommended
# CPU: 4+ cores

# Optimize SQLite
sqlite3 data/aupat.db << EOF
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=MEMORY;
EOF

# Increase Immich ML workers (if GPU available)
# Edit docker-compose.yml:
# immich-ml:
#   environment:
#     - MACHINE_LEARNING_WORKERS=4

# Restart services
docker compose up -d
```

### For Slow Map Loading

```bash
# Check marker count
curl http://localhost:5000/api/map/markers | jq length

# If > 100k markers, increase clustering zoom threshold
# Desktop app → Settings → Map → Min Cluster Zoom: 8
```

---

## Security Best Practices

### Local-Only Access

```bash
# Ensure .env has:
AUPAT_HOST=127.0.0.1  # Localhost only
IMMICH_HOST=127.0.0.1
ARCHIVEBOX_HOST=127.0.0.1

# Firewall: Block external access to ports
sudo ufw deny 5000  # Linux
# Mac: System Preferences → Security → Firewall
```

### Remote Access (Cloudflare Tunnel)

```bash
# Enable Cloudflare Access (authentication)
# Cloudflare Dashboard → Zero Trust → Access → Applications
# Add application: aupat.yourdomain.com
# Policy: Allow email = your@email.com

# Never expose ports directly to internet
# Always use Cloudflare tunnel + Access
```

### Regular Updates

```bash
# Update Docker images monthly
docker compose pull
docker compose up -d

# Update dependencies
pip install --upgrade -r requirements.txt
cd desktop-app && npm update
```

---

## Emergency Recovery

### Complete System Failure

```bash
# 1. Stop services
docker compose down

# 2. Restore database from backup
cp data/backups/aupat_LATEST.db data/aupat.db

# 3. Check integrity
sqlite3 data/aupat.db "PRAGMA integrity_check;"

# 4. Restart services
docker compose up -d

# 5. Verify
curl http://localhost:5000/api/health
```

### Data Loss Prevention

```bash
# Set up automated off-site backups (Restic + B2)
restic init --repo b2:bucket-name:aupat-backups

# Daily backup script with Restic
#!/bin/bash
restic backup data/ --repo b2:bucket-name:aupat-backups
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune

# Add to crontab
0 3 * * * /home/user/aupat/scripts/backup_restic.sh
```

---

## Getting Help

### Documentation

- Architecture: `docs/v0.1.2/02_ARCHITECTURE.md`
- Installation: `docs/v0.1.2/10_INSTALLATION.md`
- Testing: `docs/v0.1.2/05_TESTING.md`

### Logs

```bash
# AUPAT Core
docker compose logs -f aupat-core

# Immich
docker compose logs -f immich-server immich-ml

# ArchiveBox
docker compose logs -f archivebox

# Desktop app (dev mode)
cd desktop-app && npm run dev
# Check terminal output and DevTools console (Cmd/Ctrl+Shift+I)
```

### Community

- GitHub Issues: https://github.com/bizzlechizzle/aupat/issues
- Immich Discord: https://discord.gg/immich
- ArchiveBox Docs: https://github.com/ArchiveBox/ArchiveBox

---

## Version Info

AUPATOOL v0.1.2
- AUPAT Core: Python 3.11+, Flask 3.x, SQLite
- Desktop App: Electron 28+, Svelte 4+
- Immich: v1.91+
- ArchiveBox: v0.7+
- Docker Compose: v2.20+

Last updated: 2025-01-17
