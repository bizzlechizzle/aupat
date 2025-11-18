# AUPAT First-Run Setup Wizard

## Overview

A guided setup wizard for the AUPAT desktop application that walks users through initial configuration, eliminating manual configuration pain points and ensuring correct setup.

## Design Principles

- KISS: Keep It Simple Stupid - Clear, linear flow
- BPL: Bulletproof Longterm - Validate all inputs, handle errors gracefully
- BPA: Best Practices Always - Follow platform-specific conventions
- Zero-knowledge assumption: Explain everything clearly

## Wizard Flow

### Step 1: Welcome

```
┌─────────────────────────────────────────────────┐
│  Welcome to AUPAT v0.1.2                       │
│  Abandoned Upstate Photo Archive Tool          │
│                                                 │
│  This wizard will help you set up AUPAT        │
│  in just a few minutes.                        │
│                                                 │
│  Requirements:                                  │
│  ✓ Docker Desktop installed and running        │
│  ✓ At least 10GB free disk space              │
│  ✓ Internet connection (for Docker images)     │
│                                                 │
│         [Check Requirements]  [Exit]            │
└─────────────────────────────────────────────────┘
```

**Actions:**
- Check if Docker is installed and running
- Check available disk space
- Display clear error messages with solutions if checks fail

### Step 2: Data Directory Selection

```
┌─────────────────────────────────────────────────┐
│  Choose Data Directory                          │
│                                                 │
│  Where should AUPAT store your archive?        │
│  This directory will contain:                   │
│  - Database files                               │
│  - Archived web pages (ArchiveBox)             │
│  - Photo library (Immich)                      │
│  - Application logs                             │
│                                                 │
│  Location: [/Users/you/AUPAT-Data] [Browse...] │
│                                                 │
│  Space required: ~10GB                          │
│  Space available: 250GB                         │
│                                                 │
│         [Back]  [Next]                          │
└─────────────────────────────────────────────────┘
```

**Actions:**
- Default to `~/AUPAT-Data`
- Create directory structure:
  ```
  AUPAT-Data/
  ├── database/        # SQLite database
  ├── archivebox/      # Archived web pages
  ├── immich/          # Photo library
  ├── logs/            # Application logs
  └── config/          # Configuration files
  ```
- Validate write permissions
- Check available space

### Step 3: Docker Services Setup

```
┌─────────────────────────────────────────────────┐
│  Docker Services Configuration                  │
│                                                 │
│  AUPAT uses Docker to run services:            │
│                                                 │
│  ☐ AUPAT API (Port 5001)                       │
│     Core application API                        │
│                                                 │
│  ☐ Immich (Port 2283)                          │
│     Photo & video management                    │
│                                                 │
│  ☐ ArchiveBox (Port 8000)                      │
│     Web page archiving                          │
│                                                 │
│  Estimated download: ~2GB                       │
│  Estimated time: 5-10 minutes                   │
│                                                 │
│  [Start Installation] [Advanced Options]        │
└─────────────────────────────────────────────────┘
```

**Actions:**
- Generate `docker-compose.yml` with user's data directory
- Download Docker images with progress indicators
- Start services with health checks
- Display real-time logs during startup
- **Advanced Options:** Allow custom ports if conflicts exist

### Step 4: Database Initialization

```
┌─────────────────────────────────────────────────┐
│  Database Setup                                 │
│                                                 │
│  ✓ Creating database schema...                 │
│  ✓ Running migrations...                       │
│  ✓ Creating indexes...                         │
│  ⏳ Verifying database integrity...             │
│                                                 │
│  This may take a minute...                      │
│                                                 │
│  [View Logs]                                    │
└─────────────────────────────────────────────────┘
```

**Actions:**
- Run `db_migrate_v012.py` automatically
- Create initial database at `{data_dir}/database/aupat.db`
- Validate schema
- Create backup

### Step 5: Service Health Check

```
┌─────────────────────────────────────────────────┐
│  Service Health Check                           │
│                                                 │
│  ✓ AUPAT API        healthy   (port 5001)      │
│  ✓ Immich           healthy   (port 2283)      │
│  ✓ ArchiveBox       healthy   (port 8000)      │
│  ✓ PostgreSQL       healthy                     │
│  ✓ Redis            healthy                     │
│                                                 │
│  All services are running correctly!            │
│                                                 │
│         [Back]  [Next]                          │
└─────────────────────────────────────────────────┘
```

**Actions:**
- Call `/api/health` endpoint
- Call `/api/health/services` endpoint
- Display service statuses with colored indicators
- Offer troubleshooting if any service fails
- **Auto-retry:** Retry failed health checks 3 times

### Step 6: Optional: Import First Location

```
┌─────────────────────────────────────────────────┐
│  Add Your First Location (Optional)             │
│                                                 │
│  Would you like to add a location now?         │
│                                                 │
│  Location Name: [________________________]      │
│  Type:          [City ▾]                        │
│  State:         [NY ▾]                          │
│  GPS:           Lat [____] Lon [____] [Auto]   │
│                                                 │
│  You can add locations later from the main      │
│  interface.                                     │
│                                                 │
│         [Skip]  [Add Location]                  │
└─────────────────────────────────────────────────┘
```

**Actions:**
- Call POST `/api/locations` if user adds location
- Validate inputs
- Show success confirmation
- **Auto GPS:** Use IP geolocation as hint (optional)

### Step 7: Complete

```
┌─────────────────────────────────────────────────┐
│  Setup Complete!                                │
│                                                 │
│  AUPAT is ready to use.                        │
│                                                 │
│  Your data is stored at:                        │
│  /Users/you/AUPAT-Data                         │
│                                                 │
│  Services are running at:                       │
│  • AUPAT:      http://localhost:5001           │
│  • Immich:     http://localhost:2283           │
│  • ArchiveBox: http://localhost:8000           │
│                                                 │
│  Next steps:                                    │
│  1. Add locations from the main screen         │
│  2. Import photos and videos                    │
│  3. Archive web URLs                            │
│                                                 │
│         [Open AUPAT]  [View Documentation]      │
└─────────────────────────────────────────────────┘
```

**Actions:**
- Save configuration to `user/user.json`
- Mark setup as complete (create `.setup_complete` flag)
- Launch main application window

## Error Handling

### Docker Not Running

```
┌─────────────────────────────────────────────────┐
│  ⚠ Docker Desktop Not Running                   │
│                                                 │
│  AUPAT requires Docker Desktop to run.         │
│                                                 │
│  Please:                                        │
│  1. Open Docker Desktop                         │
│  2. Wait for it to fully start                  │
│  3. Click "Retry" below                         │
│                                                 │
│  Don't have Docker?                             │
│  Download from: https://docker.com/get-started  │
│                                                 │
│         [Retry]  [Exit]                         │
└─────────────────────────────────────────────────┘
```

### Port Conflict

```
┌─────────────────────────────────────────────────┐
│  ⚠ Port Conflict Detected                       │
│                                                 │
│  Port 5001 is already in use by another app.   │
│                                                 │
│  Options:                                       │
│  • Stop the other application using port 5001   │
│  • Use a different port for AUPAT              │
│                                                 │
│  Custom port: [5002]                            │
│                                                 │
│         [Use Custom Port]  [Retry]  [Cancel]    │
└─────────────────────────────────────────────────┘
```

### Insufficient Disk Space

```
┌─────────────────────────────────────────────────┐
│  ⚠ Insufficient Disk Space                      │
│                                                 │
│  AUPAT requires at least 10GB of free space.   │
│  Available: 3.2GB                               │
│                                                 │
│  Please:                                        │
│  • Free up disk space                           │
│  • Choose a different data directory            │
│                                                 │
│         [Choose Different Location]  [Exit]     │
└─────────────────────────────────────────────────┘
```

### Service Startup Failure

```
┌─────────────────────────────────────────────────┐
│  ⚠ Service Failed to Start                      │
│                                                 │
│  Immich service failed health check.           │
│                                                 │
│  Common causes:                                 │
│  • Port 2283 already in use                     │
│  • Docker out of memory                         │
│  • Network connectivity issues                  │
│                                                 │
│  [View Logs]  [Retry]  [Advanced Troubleshoot]  │
└─────────────────────────────────────────────────┘
```

## Technical Implementation

### Configuration File Generation

The wizard generates `user/user.json`:

```json
{
  "db_name": "aupat.db",
  "db_loc": "/Users/you/AUPAT-Data/database/aupat.db",
  "db_backup": "/Users/you/AUPAT-Data/database/backups/",
  "db_ingest": "/Users/you/AUPAT-Data/database/ingest/",
  "arch_loc": "/Users/you/AUPAT-Data/archive/",
  "services": {
    "aupat_port": 5001,
    "immich_port": 2283,
    "archivebox_port": 8000
  },
  "setup_completed": true,
  "setup_version": "0.1.2",
  "setup_date": "2025-11-17T20:30:00Z"
}
```

### Docker Compose Generation

Generate `docker-compose.yml` with user-specific paths:

```yaml
services:
  aupat-core:
    volumes:
      - /Users/you/AUPAT-Data/database:/data
      - /Users/you/AUPAT-Data/logs:/app/logs
    ports:
      - "${AUPAT_PORT:-5001}:5000"

  immich-server:
    volumes:
      - /Users/you/AUPAT-Data/immich:/data/immich
    ports:
      - "${IMMICH_PORT:-2283}:2283"

  archivebox:
    volumes:
      - /Users/you/AUPAT-Data/archivebox:/data
    ports:
      - "${ARCHIVEBOX_PORT:-8000}:8000"
```

### Health Check API

Wizard calls these endpoints to verify setup:

```
GET /api/health
Response: {"status": "healthy"}

GET /api/health/services
Response: {
  "database": "healthy",
  "immich": "healthy",
  "archivebox": "healthy"
}
```

### Setup State Management

Track wizard progress in case of interruption:

```json
{
  "setup_state": {
    "current_step": 3,
    "data_directory": "/Users/you/AUPAT-Data",
    "docker_images_downloaded": true,
    "database_initialized": false,
    "services_started": false
  }
}
```

## Platform-Specific Considerations

### macOS
- Request permissions for data directory (Finder access)
- Use native file picker dialogs
- Check for Docker Desktop for Mac specifically
- Offer to add AUPAT to Login Items

### Windows
- Request admin elevation for Docker operations
- Use Windows file explorer dialogs
- Check for Docker Desktop for Windows
- Offer to create desktop shortcut

### Linux
- Check for Docker Engine or Docker Desktop
- Verify user in `docker` group
- Use GTK/Qt file dialogs
- Offer to create `.desktop` file

## User Experience Enhancements

### Progress Indicators
- Show download progress for Docker images
- Display real-time service startup logs
- Animate health check indicators

### Help & Documentation
- Context-sensitive help on every screen
- "Learn More" links to documentation
- Troubleshooting section accessible from anywhere

### Skip Options
- Allow skipping optional steps
- Save partial configuration
- Resume setup later from main menu

### Accessibility
- Keyboard navigation (Tab, Enter, Escape)
- Screen reader compatible
- High contrast mode support
- Clear error messages with actionable steps

## Testing Requirements

### Unit Tests
- Validate each step independently
- Mock Docker API responses
- Test error handling paths
- Verify configuration generation

### Integration Tests
- Full wizard flow end-to-end
- Docker service startup/health checks
- Database migration execution
- Configuration file creation

### User Testing
- Test with non-technical users
- Measure time to complete setup
- Identify confusing steps
- Gather feedback on error messages

## Future Enhancements

### Phase 2
- Import existing ArchiveBox/Immich instances
- Migrate data from other tools
- Backup/restore wizard
- Multi-user setup

### Phase 3
- Cloud deployment option (AWS, Azure, GCP)
- NAS/remote storage configuration
- Advanced networking (reverse proxy, SSL)

### Phase 4
- Mobile app pairing
- Remote access setup
- Collaboration features

## Implementation Priority

### v0.1.3 (Next Release)
- Step 1: Welcome & Requirements Check
- Step 2: Data Directory Selection
- Step 3: Docker Services Setup
- Step 4: Database Initialization
- Step 5: Service Health Check
- Step 7: Complete

### v0.1.4
- Step 6: Optional First Location
- Advanced troubleshooting
- Setup state persistence

### v0.1.5
- Platform-specific polish
- Accessibility improvements
- Advanced configuration options

## Success Metrics

- 95%+ successful first-run completions
- Average setup time under 10 minutes
- Zero manual configuration file editing required
- Clear, actionable error messages for all failure modes
- User satisfaction score of 4.5+/5

## Related Files

- `scripts/db_migrate_v012.py` - Database initialization
- `docker-compose.yml` - Service configuration
- `user/user.json` - User configuration
- `scripts/api_routes_v012.py` - Health check endpoints

## References

- Docker Desktop: https://www.docker.com/products/docker-desktop
- Immich: https://immich.app
- ArchiveBox: https://archivebox.io
- AUPAT Documentation: /docs/
