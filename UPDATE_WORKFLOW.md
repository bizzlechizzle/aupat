# How to Update AUPAT After Git Pull

Follow these steps **every time** you pull updates from the repository:

## 1. Stop the Running App
```bash
# Press Ctrl+C in the terminal where ./start_aupat.sh is running
# Make sure BOTH the backend and frontend servers stop
```

## 2. Pull Latest Changes
```bash
git pull origin main
```

## 3. Install Dependencies (IMPORTANT!)
```bash
cd desktop
npm install
cd ..
```
**Why?** New features often require new npm packages. This ensures all dependencies are installed.

## 4. Restart the App
```bash
./start_aupat.sh
```

## 5. Hard Refresh the Electron App
If you still see old content:
- **macOS**: Cmd+Shift+R or Cmd+R
- **Windows/Linux**: Ctrl+Shift+R or Ctrl+R

---

## Quick Command Sequence

```bash
# Stop app (Ctrl+C)
git pull origin main
cd desktop && npm install && cd ..
./start_aupat.sh
```

---

## Common Issues

### "Module not found" or blank white screen
- **Cause**: Missing npm dependencies
- **Fix**: Run `cd desktop && npm install && cd ..`

### Changes not showing up
- **Cause**: Old code cached in memory
- **Fix**: Stop app completely, restart with `./start_aupat.sh`

### "Port already in use"
- **Cause**: Old backend still running
- **Fix**: `pkill -f "python.*app.py"` then restart

---

## What Changes Require npm install?

- ✅ New npm packages added to package.json
- ✅ Package version updates
- ✅ New Svelte components using new libraries
- ❌ Python code changes (backend only)
- ❌ Simple UI tweaks to existing components
