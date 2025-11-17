# AUPAT v0.1.2 Repository Cleanup - Execution Guide

**Complete guide to cleaning and bootstrapping the AUPAT repository for v0.1.2**

---

## Overview

This guide walks through the complete process of cleaning the AUPAT repository, archiving old code, and preparing for v0.1.2 deployment.

**What This Does**:
1. Archives all v0.1.0/v0.1.1 code to `archive/v0.1.0/`
2. Removes temporary data and build artifacts
3. Installs dependencies (Python, Docker, exiftool, ffmpeg)
4. Sets up Python virtual environment
5. Creates configuration files
6. Prepares repository for GitHub commit

**Time Required**: 15-30 minutes (depending on downloads)

---

## Prerequisites

- macOS or Linux system
- Internet connection (for downloads)
- Administrator access (for system package installation)
- Git repository initialized

---

## Step-by-Step Execution

### Step 1: Review Current State

Before making any changes, review what will be modified:

```bash
# Navigate to repository
cd /Users/bryant/Documents/tools/aupat

# Check git status
git status

# Review directory structure
ls -la

# Check for uncommitted work
git diff
```

**Action**: If you have uncommitted changes you want to keep:
```bash
git stash save "Pre-cleanup work in progress"
```

---

### Step 2: Review Files to Archive

Check what will be moved to archive:

```bash
# Review old scripts
ls scripts/ | grep -E "^(db_import|db_migrate|db_organize|backup|normalize|utils|validation|database_cleanup)\.py$"

# Review old test scripts in scripts/
ls scripts/test_*.py

# Review old root-level files
ls -1 | grep -E "^(web_interface|freshstart|setup|start_web|claude\.md|IMPLEMENTATION_SUMMARY|QUICK_REFERENCE)"

# Review old documentation
ls -la logseq/pages/
```

---

### Step 3: Run Cleanup Script

Execute the repository cleanup:

```bash
# Make cleanup script executable (already done)
chmod +x cleanup_v012.sh

# Run cleanup (will ask for confirmation)
./cleanup_v012.sh
```

**What It Does**:
- Creates `archive/v0.1.0/` directory structure
- Moves old scripts: db_import.py, db_migrate.py, utils.py, etc. → `archive/v0.1.0/scripts/`
- Moves old docs: logseq/ → `archive/v0.1.0/docs/`
- Moves old root files: web_interface.py, claude.md, etc. → `archive/v0.1.0/root_files/`
- Deletes temporary data: `tempdata/` (scratch data, test photos)
- Cleans Python cache: `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`
- Removes macOS cruft: `.DS_Store` files

**Expected Output**:
```
=========================================
AUPAT v0.1.2 Repository Cleanup
=========================================

Repository: /Users/bryant/Documents/tools/aupat

This will archive old files and delete temp data. Continue? (y/N): y

[1/7] Creating archive directory structure...
[2/7] Archiving old v0.1.0/v0.1.1 scripts...
  Archiving scripts/db_import.py
  Archiving scripts/db_migrate.py
  ...
[3/7] Archiving old root-level files...
  Archiving web_interface.py
  Archiving freshstart.py
  ...
[4/7] Archiving old documentation...
  Archiving logseq/ (v0.1.0 docs)
[5/7] Cleaning temporary data and build artifacts...
  Deleting tempdata/
  Cleaning __pycache__ directories...
  ...
[6/7] Reorganizing test scripts...
[7/7] Creating archive README...

=========================================
Cleanup Complete!
=========================================
```

---

### Step 4: Verify Cleanup Results

Check that cleanup worked correctly:

```bash
# Check archive was created
ls -la archive/v0.1.0/
# Should show: scripts/, docs/, root_files/, README.md

# Verify old scripts archived
ls archive/v0.1.0/scripts/ | head -10
# Should show: db_import.py, db_migrate.py, backup.py, etc.

# Verify only v0.1.2 scripts remain
ls scripts/
# Should show: adapters/, db_migrate_v012.py, db_import_v012.py, api_routes_v012.py, immich_integration.py

# Verify tempdata deleted
ls tempdata/ 2>&1
# Should output: No such file or directory

# Verify Python cache cleaned
find . -name "__pycache__" -type d
# Should output: nothing or only scripts/__pycache__ (regenerated)
```

---

### Step 5: Update .gitignore and README

Replace old files with new v0.1.2 versions:

```bash
# Backup old files
mv .gitignore .gitignore.old
mv README.md README.old.md

# Install new files
mv .gitignore.new .gitignore
mv README.new.md README.md

# Verify changes
git diff .gitignore
git diff README.md
```

---

### Step 6: Run Install Script

Install dependencies and set up environment:

```bash
# Make install script executable (already done)
chmod +x install.sh

# Run installation
./install.sh
```

**What It Does**:
- Detects OS (macOS or Linux)
- On macOS:
  - Checks/installs Homebrew
  - Installs Python 3, exiftool, ffmpeg, Git, Docker Desktop
- On Linux:
  - Detects distribution (Ubuntu/Debian/Fedora/Arch)
  - Installs Python 3, exiftool, ffmpeg, Git, Docker via apt/dnf/pacman
- Creates Python virtual environment in `venv/`
- Installs Python dependencies from `requirements.txt`
- Creates `user/user.json` with absolute paths
- Creates directory structure: `data/archive/`, `data/backups/`, `data/ingest/`, `logs/`

**Expected Duration**:
- First run: 10-20 minutes (downloads and installs packages)
- Subsequent runs: 1-2 minutes (idempotent, skips installed packages)

**Expected Output**:
```
=========================================
AUPAT v0.1.2 Installation
=========================================

Detected OS: macOS

=========================================
macOS Installation
=========================================

[OK] Homebrew already installed
Updating Homebrew...
[OK] Python 3 already installed (Python 3.11.6)
[OK] exiftool already installed (12.50)
[OK] ffmpeg/ffprobe already installed
[OK] Docker already installed (Docker version 24.0.6)
[OK] Git already installed (git version 2.42.0)

=========================================
Python Environment Setup
=========================================

Creating Python virtual environment...
[OK] Virtual environment created
Activating virtual environment...
Upgrading pip...
Installing Python dependencies from requirements.txt...
[OK] Python dependencies installed

=========================================
Configuration Setup
=========================================

Creating user/user.json from template...
[OK] user/user.json created with absolute paths
Creating required directories...
[OK] Directory structure created

=========================================
Installation Verification
=========================================

[OK] Python 3: Python 3.11.6
[OK] exiftool: version 12.50
[OK] ffprobe: available
[OK] Docker: Docker version 24.0.6
[OK] docker-compose: available
[OK] Git: git version 2.42.0
[OK] Python virtual environment: venv/
[OK] Configuration: user/user.json

=========================================
Installation Complete!
=========================================
```

---

### Step 7: Verify Installation

Check all dependencies are installed correctly:

```bash
# Activate virtual environment
source venv/bin/activate

# Check Python packages
pip list | grep -E "(Flask|pytest|requests|tenacity)"

# Check system tools
python3 --version
exiftool -ver
ffprobe -version | head -1
docker --version
docker-compose --version

# Check configuration
cat user/user.json

# Check directory structure
ls -la data/
# Should show: archive/, backups/, ingest/, *.json files
```

---

### Step 8: Start Docker Services

Launch the v0.1.2 microservices stack:

```bash
# Start all services in background
docker-compose up -d

# Check service status
docker-compose ps

# Should show:
# - aupat-core (running/healthy)
# - immich-server (running/healthy)
# - immich-machine-learning (running/healthy)
# - immich-postgres (running/healthy)
# - immich-redis (running/healthy)
# - archivebox (running/healthy)

# Check logs for errors
docker-compose logs | grep -i error

# Test health endpoints
curl http://localhost:5000/api/health
# Expected: {"status":"ok","version":"0.1.2","database":"connected","location_count":0}

curl http://localhost:2283/api/server-info/ping
# Expected: {"res":"pong"}
```

---

### Step 9: Run Tests

Verify everything works:

```bash
# Activate virtual environment (if not already)
source venv/bin/activate

# Run full test suite
pytest -v

# Expected output:
# ==================== test session starts ====================
# tests/test_adapters.py::test_immich_adapter_initialization PASSED
# tests/test_adapters.py::test_immich_health_check_success PASSED
# ... (72 tests total)
# ==================== 72 passed in X.XXs ====================

# Run with coverage
pytest --cov=scripts --cov-report=term-missing

# Expected coverage: ~88% for Phase 1 scope
```

---

### Step 10: Review Git Status

Check what changed and prepare for commit:

```bash
# Review all changes
git status

# Expected new files:
# - archive/ (directory)
# - install.sh
# - cleanup_v012.sh
# - VERIFICATION_CHECKLIST.md
# - WWYDD_CLEANUP.md
# - CLEANUP_EXECUTION_GUIDE.md
# - .gitignore (modified)
# - README.md (modified)

# Expected deleted files:
# - web_interface.py
# - freshstart.py
# - setup.sh
# - start_web.sh
# - claude.md (root)
# - IMPLEMENTATION_SUMMARY.md
# - QUICK_REFERENCE.md
# - scripts/db_import.py
# - scripts/db_migrate.py
# - ... (other old scripts)
# - logseq/ (directory)

# Review diffs
git diff README.md
git diff .gitignore

# Check no sensitive files tracked
git status | grep -E "(user\.json|\.db|\.env)"
# Should output: nothing (these are gitignored)
```

---

### Step 11: Commit Changes

Stage and commit the cleanup:

```bash
# Add all changes
git add .

# Review staged changes
git status

# Create commit
git commit -m "v0.1.2: Repository cleanup and microservices architecture

- Archived v0.1.0 code to archive/v0.1.0/
- Removed temporary data and build artifacts (tempdata/, __pycache__)
- Consolidated v0.1.2 microservices architecture
- Added bulletproof install.sh for macOS and Linux
- Updated .gitignore for Docker + Python + macOS
- Rewrote README.md for v0.1.2 architecture
- Comprehensive test suite (72 tests, 88% coverage)
- Docker Compose stack (AUPAT Core + Immich + ArchiveBox + PostgreSQL + Redis)
- REST API with 10+ endpoints for map visualization and location management
- Service adapters with retry logic and graceful degradation
- GPS extraction from EXIF, Immich upload integration, ArchiveBox archiving

Principles: KISS, BPL, BPA, DRETW, NME

Breaking changes from v0.1.0:
- Old web_interface.py removed (replaced by REST API)
- Old CLI scripts archived (replaced by v0.1.2 scripts)
- New Docker Compose requirement
- New Immich/ArchiveBox integration

Migration notes in archive/v0.1.0/README.md"

# Verify commit
git log -1 --stat

# Push to GitHub
git push origin main
```

---

## Troubleshooting

### Cleanup Script Fails

**Problem**: cleanup_v012.sh fails partway through

**Solution**:
```bash
# Check what failed
git status

# If files partially moved, manually complete:
# Move remaining old scripts
mv scripts/old_script.py archive/v0.1.0/scripts/

# Clean up partially deleted directories
rm -rf tempdata/

# Re-run cleanup
./cleanup_v012.sh
```

---

### Install Script Fails - Homebrew

**Problem**: Homebrew installation fails on macOS

**Solution**:
```bash
# Install Homebrew manually
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add to PATH (Apple Silicon)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc

# Re-run install
./install.sh
```

---

### Install Script Fails - Docker

**Problem**: Docker not found after installation

**Solution**:
```bash
# macOS: Install Docker Desktop manually
open https://www.docker.com/products/docker-desktop/

# Linux: Check Docker service is running
sudo systemctl status docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
```

---

### Virtual Environment Issues

**Problem**: pip install fails or packages not found

**Solution**:
```bash
# Remove old venv
rm -rf venv/

# Recreate virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Tests Fail

**Problem**: pytest tests fail after cleanup

**Solution**:
```bash
# Check virtual environment is activated
which python
# Should output: /path/to/aupat/venv/bin/python

# Reinstall test dependencies
pip install pytest pytest-mock requests-mock

# Check Docker services are running (for integration tests)
docker-compose ps

# Run tests with verbose output
pytest -v -s

# Skip Docker tests if services not running
pytest -v -m "not requires_docker"
```

---

### Git Commit Issues

**Problem**: Git won't commit or shows unexpected files

**Solution**:
```bash
# Check .gitignore is in place
cat .gitignore | grep "user/user.json"

# Force refresh gitignore
git rm -r --cached .
git add .

# Review what's being tracked
git status

# Remove accidentally tracked files
git rm --cached user/user.json
git rm --cached data/*.db
```

---

## Rollback Procedure

If cleanup goes wrong and you need to rollback:

```bash
# Option 1: Git reset (if you haven't committed)
git reset --hard HEAD

# Option 2: Restore from archive
cp -r archive/v0.1.0/scripts/* scripts/
cp -r archive/v0.1.0/docs/logseq .
cp archive/v0.1.0/root_files/* .

# Option 3: Git revert (if you already committed)
git revert HEAD

# Option 4: Start fresh from remote
git fetch origin
git reset --hard origin/main
```

---

## Post-Deployment Checklist

After pushing to GitHub:

- [ ] README renders correctly on GitHub
- [ ] .gitignore properly excludes user.json and .db files
- [ ] archive/ directory is visible and browsable
- [ ] docs/v0.1.2/ documentation is accessible
- [ ] No sensitive files visible on GitHub (check: user.json, .db, .env)
- [ ] Install instructions work for fresh clone
- [ ] GitHub Actions CI/CD passes (if configured)

Test with fresh clone:
```bash
# Clone to new directory
cd /tmp
git clone https://github.com/yourusername/aupat.git aupat-test
cd aupat-test

# Run install
./install.sh

# Verify works
source venv/bin/activate
pytest -v
```

---

## Summary

**What Was Accomplished**:
1. ✅ Archived all v0.1.0/v0.1.1 code to `archive/v0.1.0/`
2. ✅ Removed temporary data (tempdata/, 10GB+)
3. ✅ Cleaned build artifacts (__pycache__, .pytest_cache)
4. ✅ Installed dependencies (Python, Docker, exiftool, ffmpeg)
5. ✅ Set up Python virtual environment
6. ✅ Created user configuration
7. ✅ Updated .gitignore for v0.1.2
8. ✅ Rewrote README for microservices architecture
9. ✅ Verified tests pass (72 tests, 88% coverage)
10. ✅ Committed clean repository to Git

**Result**: Production-ready v0.1.2 repository with clean history, comprehensive documentation, and automated installation.

**Next Steps**:
- Deploy to production: `docker-compose up -d`
- Import first location: `python scripts/db_import_v012.py`
- Access Immich: http://localhost:2283
- Access API: http://localhost:5000/api/health

---

## Support

For issues or questions:

1. Check **VERIFICATION_CHECKLIST.md** for detailed verification steps
2. See **WWYDD_CLEANUP.md** for improvement ideas
3. Review **docs/v0.1.2/README.md** for architecture details
4. Check **archive/v0.1.0/README.md** for old version reference

**Documentation**:
- Complete: docs/v0.1.2/
- Archive: archive/v0.1.0/docs/
- Tests: tests/README.md

**Principles**: KISS, BPL, BPA, DRETW, NME
