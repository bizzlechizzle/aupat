# AUPAT Quick Start Guide

## Starting the Desktop App

### ONE COMMAND TO RULE THEM ALL

```bash
./start_aupat.sh
```

That's it. This script starts:
- Backend API server on port 5002
- Desktop Electron app with live reload

Press `Ctrl+C` to stop both when you're done.

## What This Script Does

The `start_aupat.sh` script automatically:
- ✅ Activates Python virtual environment
- ✅ Starts the Flask API server on port 5002
- ✅ Starts the Electron desktop app
- ✅ Handles shutdown gracefully when you press Ctrl+C

## Troubleshooting

### "Port 5002 is already in use"

Something is already running on port 5002. Kill it:

```bash
# Kill any processes on port 5002
pkill -f "python.*app.py"

# Or find and kill manually
lsof -ti:5002 | xargs kill

# Then try again
./start_aupat.sh
```

### "Cannot connect to backend" in the app

This means the API server isn't running:

```bash
# Stop everything
pkill -f "python.*app.py"
pkill -f electron

# Start fresh
./start_aupat.sh
```

### Still having issues?

Check the console output when you run `./start_aupat.sh`. You should see:
```
=========================================
AUPAT is running!
=========================================
Backend:  http://localhost:5002
Frontend: Check npm output above
```

## Architecture

```
┌─────────────────┐
│  Desktop App    │  Electron (Svelte) - Port 5173 (dev server)
│                 │  Connects to API at localhost:5002
└────────┬────────┘
         │
         │ HTTP Requests
         │
┌────────▼────────┐
│  API Server     │  Flask - Port 5002
│                 │  REST API
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

1. Run `./start_aupat.sh`
2. Import locations via the desktop app
3. View locations on the map

## Advanced Usage

### Start only the API server in background

If you need to run the API server separately (e.g., for production testing):

```bash
./scripts/advanced/start_api.sh
```

This is NOT needed for normal development. Use `./start_aupat.sh` instead.

### Manual startup (not recommended)

If you want to start components separately:

```bash
# Terminal 1 - Backend
source venv/bin/activate
python3 app.py

# Terminal 2 - Frontend
cd desktop
npm run dev
```

But seriously, just use `./start_aupat.sh` - it's easier.

For full documentation, see the main README.md.
