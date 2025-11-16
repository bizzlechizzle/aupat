# AUPAT Web Interface - Quick Start Guide

## Getting Started in 3 Steps

### Step 1: Activate Virtual Environment
The Flask web interface requires the virtual environment to be activated:

```bash
cd /home/user/aupat
source venv/bin/activate
```

**Important**: Always activate the venv before running the web interface!

### Step 2: Verify Setup
Ensure all dependencies are installed and configured:

```bash
# Check Flask is available
python3 -c "import flask; print(f'Flask {flask.__version__} is installed')"

# Verify database exists (create if needed)
python3 scripts/db_migrate.py

# Check user configuration
cat user/user.json
```

### Step 3: Launch Web Interface
Start the Flask development server:

```bash
./web_interface.py
# Or: python3 web_interface.py
```

The interface will be available at: **http://localhost:5001**

## New Design Features

The web interface has been completely redesigned to match your abandonedupstate website:

### Pages
- **Dashboard** (`/`) - Statistics, recent imports, system status
- **Locations** (`/locations`) - Browse all locations with pagination
- **Archives** (`/archives`) - View archived media (coming soon)
- **Import** (`/import`) - Import new locations and media

### Design System
- **Colors**: Cream (#fffbf7), Dark Gray (#454545), Warm Brown (#b9975c)
- **Typography**: Roboto Mono (headings), Lora (body text)
- **Theme Toggle**: Switch between light/dark modes (saved to localStorage)
- **Responsive**: Mobile-friendly card-based layout

## Using the Import Form

1. Navigate to **Import** page
2. Enter source directory path (e.g., `/path/to/photos/LocationName`)
3. Check "Preview Only" to test without importing
4. Click "Start Import" to process

The form will:
- Validate the source directory exists
- Show progress during import
- Display results and any errors
- Update database with new location and media

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
**Solution**: Activate the virtual environment first
```bash
source venv/bin/activate
```

### "Database not found"
**Solution**: Run the migration script
```bash
python3 scripts/db_migrate.py
```

### "user.json not configured"
**Solution**: Copy and edit the template
```bash
cp user/user.json.template user/user.json
# Edit user.json with your actual paths
```

### Port 5001 already in use
**Solution**: Kill the existing process or use a different port
```bash
# Find and kill existing process
lsof -ti:5001 | xargs kill -9

# Or run on different port
python3 web_interface.py --port 5002
```

## Command-Line Workflow Alternative

If you prefer command-line tools, use the orchestration script:

```bash
# Activate venv
source venv/bin/activate

# Run complete workflow
./run_workflow.py /path/to/source/folder

# Or run with options
./run_workflow.py /path/to/source \
  --skip-steps folder,ingest \
  --backup \
  --interactive
```

See `WORKFLOW_TOOLS.md` for full orchestration documentation.

## Recent Fixes (2025-11-16)

### P0 Critical Fixes
- ✅ Fixed versions table schema mismatch in `db_import.py`
- ✅ Redesigned web interface to match abandonedupstate aesthetic
- ✅ Added Dashboard, Locations, and Archives pages
- ✅ Implemented theme toggle with localStorage persistence

### What Changed
1. **db_import.py** - Fixed INSERT statement to use correct columns (modules, version, ver_updated)
2. **web_interface.py** - Complete rewrite with:
   - Exact color scheme from abandonedupstate-nextjs
   - Professional card-based layout
   - Statistics dashboard
   - Location browser with pagination
   - Theme toggle (light/dark)
   - Responsive mobile design

## Next Steps

1. **Test the web interface**: Follow Steps 1-3 above
2. **Import your first location**: Use the Import page
3. **Review the audit report**: See `CLI_AUDIT_REPORT.md` for implementation status
4. **Report issues**: Check the GitHub repository for bug tracking

## Documentation

- `README.md` - Project overview and architecture
- `WORKFLOW_TOOLS.md` - Orchestration script and web interface details
- `CLI_AUDIT_REPORT.md` - Comprehensive audit of CLI implementation
- `claude.md` - Troubleshooting methodology and best practices

---

**Ready to start?** Run: `source venv/bin/activate && ./web_interface.py`
