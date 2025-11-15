# AUPAT Workflow Tools

This document describes the orchestration and web interface tools for AUPAT.

## Orchestration Script: `run_workflow.py`

A Python script that automates the complete AUPAT workflow by running all scripts in the correct sequence.

### Features

- **Automated Execution**: Runs all workflow steps in correct order
- **Error Handling**: Stops on critical failures, continues on optional failures
- **Progress Tracking**: Shows real-time progress and step completion
- **Flexible Control**: Skip steps, run interactively, or dry-run mode
- **Optional Backup**: Run database backup after successful completion

### Workflow Steps

The orchestration script runs these steps in order:

1. **Database Migration** (`db_migrate.py`) - Create/update database schema
2. **Import Media** (`db_import.py`) - Import new location and media files [OPTIONAL]
3. **Organize Metadata** (`db_organize.py`) - Extract metadata and categorize
4. **Create Folder Structure** (`db_folder.py`) - Generate archive folder structure
5. **Ingest Files** (`db_ingest.py`) - Move files to archive
6. **Verify Archive** (`db_verify.py`) - Verify integrity and cleanup staging
7. **Export JSON** (`db_identify.py`) - Generate JSON exports
8. **Backup** (`backup.py`) - Create database backup [OPTIONAL]

### Usage

#### Basic Usage

```bash
# Run complete workflow (no new imports, just process existing data)
./run_workflow.py

# Run complete workflow with new media import
./run_workflow.py --source /path/to/media/directory

# Run with backup at the end
./run_workflow.py --source /path/to/media --backup
```

#### Interactive Mode

```bash
# Prompt before executing each step
./run_workflow.py --interactive --source /path/to/media
```

#### Dry Run

```bash
# Show what would be executed without actually running
./run_workflow.py --dry-run --source /path/to/media
```

#### Skip Steps

```bash
# Skip specific steps (e.g., skip import and export)
./run_workflow.py --skip "Import Media" --skip "Export JSON"

# Skip just the import step
./run_workflow.py --skip "Import Media"
```

#### Custom Configuration

```bash
# Use custom config file
./run_workflow.py --config /path/to/custom/user.json --source /media

# Use custom scripts directory
./run_workflow.py --scripts-dir /path/to/scripts --source /media
```

### Command Line Options

```
--config PATH           Path to user.json config file (default: user/user.json)
--source PATH           Source directory containing media files to import
--scripts-dir PATH      Path to scripts directory (default: scripts)
--skip STEP_NAME        Skip a specific workflow step (can be used multiple times)
--backup                Run database backup after successful completion
--dry-run               Show what would be executed without actually running
--interactive           Prompt before executing each step
-v, --verbose           Enable verbose logging
```

### Examples

```bash
# Example 1: Complete workflow for new location
./run_workflow.py --source /Volumes/Photos/AbandonedFactory --backup

# Example 2: Process existing data without new imports
./run_workflow.py --skip "Import Media"

# Example 3: Interactive mode for step-by-step control
./run_workflow.py --interactive --source /media/new-location

# Example 4: Dry run to preview execution
./run_workflow.py --dry-run --source /media/test

# Example 5: Custom config and skip export
./run_workflow.py --config custom.json --skip "Export JSON" --source /media
```

---

## Web Interface: `web_interface.py`

A Flask-based web interface for managing AUPAT imports and workflows through a browser.

### Features

- **Web-based Import**: Import media through a simple web form
- **Dashboard**: View database statistics (locations, files, etc.)
- **Workflow Execution**: Run complete workflow from browser
- **Real-time Logs**: View live activity logs during execution
- **Progress Tracking**: See current status and running operations

### Starting the Web Interface

```bash
# Start web interface (default: http://127.0.0.1:5000)
./web_interface.py

# Custom host and port
./web_interface.py --host 0.0.0.0 --port 8080

# Debug mode (auto-reload on code changes)
./web_interface.py --debug
```

### Accessing the Interface

1. Start the server:
   ```bash
   ./web_interface.py
   ```

2. Open your browser to: **http://127.0.0.1:5000**

3. You'll see the dashboard with:
   - Database statistics (locations, files, etc.)
   - Quick action buttons
   - System status

### Web Interface Pages

#### Home Dashboard (`/`)
- View database statistics
- Quick access to all functions
- Current system status
- Navigation to other pages

#### Import Media (`/import`)
- Web form for importing new media
- Fields:
  - Auto-generated UUID
  - Location name (required)
  - Alternative names (optional)
  - State (required, 2-letter code)
  - Location type (required)
  - Sub type (optional)
  - Source directory (required)
  - Author (optional)
- Click "Import Media" to start import process
- Redirects to logs page to view progress

#### View Logs (`/logs`)
- Real-time activity logs
- Auto-refreshes every 5 seconds
- Shows last 100 log entries
- Displays timestamps and messages

#### Database Migration (`/migrate`)
- Initialize or update database schema
- Click to run migration
- View progress in logs

#### Run Workflow (`/workflow`)
- Execute complete AUPAT workflow
- Click to start workflow
- View progress in logs

### Command Line Options

```
--host HOST     Host to bind to (default: 127.0.0.1)
--port PORT     Port to bind to (default: 5000)
--debug         Run in debug mode with auto-reload
```

### Examples

```bash
# Example 1: Start on default port
./web_interface.py

# Example 2: Make accessible from network
./web_interface.py --host 0.0.0.0 --port 8080

# Example 3: Development mode with debug
./web_interface.py --debug

# Example 4: Custom port
./web_interface.py --port 3000
```

### Security Notes

- The web interface is intended for **local use only** by default
- Default binding to `127.0.0.1` prevents external access
- To allow network access, use `--host 0.0.0.0` (use with caution)
- No authentication is implemented - do not expose to public internet
- Consider using SSH tunneling for remote access

### Using the Import Form

1. Navigate to **Import Media** from home page
2. Note the auto-generated UUID (you don't need to change this)
3. Fill in the required fields:
   - **Location Name**: Name of the abandoned location
   - **State**: Two-letter state code (e.g., NY, PA)
   - **Location Type**: Select from dropdown
   - **Source Directory**: Absolute path to media files
4. Optional fields:
   - **Also Known As**: Alternative names
   - **Sub Type**: Specific building type
   - **Author**: Person importing the media
5. Click **Import Media**
6. View progress on the Logs page

---

## Installation

### Install Dependencies

```bash
# Install Flask for web interface
pip install Flask

# Or install all requirements (includes Flask)
pip install -r requirements.txt
```

### Make Scripts Executable

```bash
chmod +x run_workflow.py
chmod +x web_interface.py
```

---

## Workflow Comparison

### Command Line (run_workflow.py)
**Best for:**
- Automated workflows
- Scripting/cron jobs
- Power users
- Batch processing
- CI/CD integration

**Pros:**
- Fast execution
- Scriptable
- Full control
- No browser needed

**Cons:**
- Command line only
- Less visual feedback

### Web Interface (web_interface.py)
**Best for:**
- One-off imports
- Visual feedback
- Less technical users
- Remote management (via SSH tunnel)
- Monitoring progress

**Pros:**
- User-friendly
- Visual dashboard
- Real-time logs
- Easy navigation

**Cons:**
- Requires browser
- Requires server running

---

## Troubleshooting

### run_workflow.py Issues

**Problem**: Script fails immediately
- Check that `user/user.json` exists and is valid JSON
- Verify all paths in config file are correct
- Run with `--verbose` for more details

**Problem**: Import step fails
- Ensure `--source` directory exists
- Check directory contains valid media files
- Verify file permissions

**Problem**: Step times out
- Default timeout is 1 hour per step
- Check logs for stuck processes
- May need to run steps individually

### web_interface.py Issues

**Problem**: Can't access web interface
- Check that Flask is installed: `pip install Flask`
- Verify port is not in use
- Try different port with `--port`

**Problem**: Import doesn't start
- Check source directory path is absolute
- Verify directory exists
- Check logs page for errors

**Problem**: Page not found errors
- Ensure server is running
- Check URL is correct: `http://127.0.0.1:5000`
- Try restarting the server

**Problem**: Scripts not running
- Verify scripts directory exists
- Check scripts are executable
- Ensure config file is valid

---

## Tips

### For run_workflow.py

1. **Use dry-run first**: Test with `--dry-run` to see execution plan
2. **Interactive for testing**: Use `--interactive` when testing new workflows
3. **Skip completed steps**: Use `--skip` to avoid re-running steps
4. **Always backup**: Add `--backup` for important workflows
5. **Check config first**: Verify `user/user.json` before running

### For web_interface.py

1. **Keep logs open**: Open logs page in separate tab during imports
2. **Refresh for updates**: Logs auto-refresh every 5 seconds
3. **Check dashboard first**: View stats before importing
4. **Use absolute paths**: Always use full paths for source directories
5. **One operation at a time**: Wait for current operation to finish

### General Best Practices

1. **Test with small datasets**: Verify workflow with small test imports first
2. **Monitor disk space**: Ensure sufficient space for staging and archive
3. **Backup database**: Regular backups before major operations
4. **Check logs**: Always review logs after workflow completion
5. **Verify results**: Use `db_verify.py` output to confirm success

---

## Integration Examples

### Cron Job (Automated Daily Import)

```bash
# Add to crontab: Import from specific directory daily at 2 AM
0 2 * * * cd /path/to/aupat && ./run_workflow.py --source /daily/media --backup
```

### Shell Script Wrapper

```bash
#!/bin/bash
# import_and_archive.sh

SOURCE_DIR="$1"

if [ -z "$SOURCE_DIR" ]; then
    echo "Usage: $0 /path/to/source"
    exit 1
fi

cd /path/to/aupat
./run_workflow.py --source "$SOURCE_DIR" --backup --verbose

if [ $? -eq 0 ]; then
    echo "Import successful!"
else
    echo "Import failed - check logs"
    exit 1
fi
```

### Remote Access via SSH Tunnel

```bash
# On remote server
./web_interface.py --host 127.0.0.1 --port 5000

# On local machine (create tunnel)
ssh -L 8080:127.0.0.1:5000 user@remote-server

# Access in browser: http://localhost:8080
```

---

## Summary

Both tools provide complementary ways to manage the AUPAT workflow:

- **`run_workflow.py`**: Command-line orchestration for automation and power users
- **`web_interface.py`**: Web-based interface for visual management and ease of use

Choose the tool that best fits your workflow, or use both as needed!
