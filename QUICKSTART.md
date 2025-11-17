# AUPAT Quickstart Guide

## First-Time Setup

### 1. Start the API Server

```bash
# Option A: Using startup script (recommended)
./start_server.sh

# Option B: Manual start
python3 app.py
```

The server will start on **http://localhost:5000**

### 2. Initialize the Database (First Run Only)

If you see a "Database not found" warning, initialize it:

```bash
python3 scripts/db_migrate_v012.py
```

### 3. Start the Desktop App

```bash
cd desktop
npm install    # First time only
npm run dev    # Development mode
# OR
npm run build  # Production build
npm start      # Run production build
```

## Configuration

### Environment Variables

- `DB_PATH` - Database file location (default: `/app/data/aupat.db`)
- `PORT` - API server port (default: 5000)

### Desktop App Settings

Access via Settings menu in the desktop app:

- **API URL**: http://localhost:5000 (default)
- **Immich URL**: http://localhost:2283 (if using Immich)
- **ArchiveBox URL**: http://localhost:8001 (if using ArchiveBox)

## Troubleshooting

### "Cannot connect to backend"

1. Verify API server is running: `curl http://localhost:5000/api/health`
2. Check desktop app settings use port **5000** (not 5001)
3. Check firewall isn't blocking port 5000

### "Database not found"

Run: `python3 scripts/db_migrate_v012.py`

### Custom States/Types

AUPAT allows custom location states and types based on your folder structure.
You'll see info-level logs for non-standard values, but they are fully supported.

**Examples:**
- State: `ny`, `ca`, `tx` (standard) or `custom-region` (custom)
- Type: `industrial`, `residential` (standard) or `secret-lab` (custom)

## Next Steps

- See `docs/v0.1.2/10_INSTALLATION.md` for detailed setup
- See `docs/v0.1.2/11_QUICK_REFERENCE.md` for API documentation
- See `tests/test_troubleshoot_backend_connection.py` for regression tests
