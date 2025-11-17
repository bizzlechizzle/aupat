# AUPAT Settings Guide

## Configuration Storage

AUPAT Desktop stores settings using electron-store at:
- **macOS**: `~/Library/Application Support/aupat-desktop/config.json`
- **Linux**: `~/.config/aupat-desktop/config.json`
- **Windows**: `%APPDATA%\aupat-desktop\config.json`

## Default Settings

```json
{
  "apiUrl": "http://localhost:5002",
  "immichUrl": "http://localhost:2283",
  "archiveboxUrl": "http://localhost:8001",
  "mapCenter": { "lat": 42.6526, "lng": -73.7562 },
  "mapZoom": 10
}
```

## Troubleshooting

### "Cannot connect to backend" Error

**Cause**: Settings file has outdated API URL from previous version

**Solution 1 - Reset Settings via UI**:
1. Open AUPAT Desktop
2. Click "Settings" tab
3. Update "API URL" to `http://localhost:5002`
4. Click "Save"

**Solution 2 - Delete Settings File**:
```bash
# macOS/Linux
rm ~/Library/Application\ Support/aupat-desktop/config.json

# Restart AUPAT Desktop to regenerate with defaults
```

**Solution 3 - Manual Edit**:
```bash
# macOS
vim ~/Library/Application\ Support/aupat-desktop/config.json

# Update apiUrl to: "http://localhost:5002"
```

### Port Migration History

- **v0.1.0-v0.1.1**: Port 5000
- **v0.1.2+**: Port 5002

If you see connection errors after updating, reset your settings using one of the methods above.

## Verifying Settings

Check your current settings:
```bash
# macOS/Linux
cat ~/Library/Application\ Support/aupat-desktop/config.json | python3 -m json.tool
```

Verify backend is running on correct port:
```bash
curl http://localhost:5002/api/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.2",
  "database": "connected",
  "location_count": <number>
}
```
