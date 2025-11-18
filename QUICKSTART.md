# AUPAT Quick Start Guide

## Starting the API Server

### Automatic Startup (Recommended)

Use the included startup script that handles health checks and dependencies:

```bash
./start_api.sh
```

This script will:
- ✅ Check if the API server is already running
- ✅ Install Python dependencies if needed
- ✅ Create database if it doesn't exist
- ✅ Start the API server on port 5002
- ✅ Verify the server started successfully

### Additional Commands

```bash
# Check server status
./start_api.sh --status

# Force restart the server
./start_api.sh --force
```

### Manual Startup

If you prefer to start manually:

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Create user.json (if not exists)
cp user/user.json.template user/user.json
# Edit user/user.json with your paths

# 3. Initialize database (if not exists)
python3 scripts/db_migrate_v012.py

# 4. Start API server
export DB_PATH=/home/user/aupat/data/aupat.db
python3 app.py
```

## Starting the Desktop App

```bash
cd desktop
npm install
npm run dev
```

The desktop app will automatically connect to `http://localhost:5002`.

## Health Check

Verify the API server is running:

```bash
curl http://localhost:5002/api/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.2",
  "database": "connected",
  "location_count": 0
}
```

## Troubleshooting

### "Cannot connect to backend" Error

This error occurs when:
1. API server is not running → Run `./start_api.sh`
2. Wrong port in desktop app settings → Desktop app defaults to port 5002 (correct)
3. Database not initialized → Script handles this automatically

### Check Logs

```bash
# API server logs
tail -f api_server.log

# Desktop app logs (when running)
# Check the console in the Electron DevTools
```

## Why the Startup Script?

Previously, users had to:
- Manually check if the server was running
- Remember to create user.json
- Manually initialize the database
- Export environment variables

The `start_api.sh` script automates all of this with health checks built in.

## Architecture

```
┌─────────────────┐
│  Desktop App    │  Electron (Svelte)
│  Port: N/A      │  Connects to API
└────────┬────────┘
         │
         │ HTTP Requests
         │
┌────────▼────────┐
│  API Server     │  Flask
│  Port: 5002     │  REST API
└────────┬────────┘
         │
         │ SQLite
         │
┌────────▼────────┐
│  Database       │  SQLite
│  aupat.db       │  Location data
└─────────────────┘
```

## Next Steps

1. Start the API server: `./start_api.sh`
2. Start the desktop app: `cd desktop && npm run dev`
3. Import locations via the desktop app
4. View locations on the map

For full documentation, see the main README.md.
