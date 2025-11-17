# AUPAT v0.1.2 Repository Cleanup Verification Checklist

This checklist verifies that the repository cleanup and bootstrap process completed successfully.

---

## Pre-Cleanup Checklist

Before running cleanup:

- [ ] Backup any uncommitted work: `git stash` or commit changes
- [ ] Verify git status: `git status` (note any important untracked files)
- [ ] Review tempdata/ for any important files before deletion
- [ ] Confirm you have backups of user/user.json (if it contains custom paths)

---

## Cleanup Execution

Run the cleanup script:

```bash
# Make executable
chmod +x cleanup_v012.sh

# Run cleanup (will ask for confirmation)
./cleanup_v012.sh
```

Expected output:
- Creates `archive/v0.1.0/` directory structure
- Moves old scripts to `archive/v0.1.0/scripts/`
- Moves old docs to `archive/v0.1.0/docs/`
- Moves old root files to `archive/v0.1.0/root_files/`
- Deletes `tempdata/` directory
- Cleans `__pycache__`, `.pytest_cache`, `.mypy_cache`
- Removes `.DS_Store` files

---

## Post-Cleanup Verification

### 1. Directory Structure

Verify clean directory layout:

```bash
# Check root directories
ls -la

# Should see:
# - archive/          (new, contains v0.1.0)
# - docs/             (contains only v0.1.2/)
# - scripts/          (contains only v0.1.2 scripts)
# - tests/            (all tests consolidated)
# - data/             (JSON configs)
# - user/             (config template + user.json)
# - docker-compose.yml, Dockerfile, docker-start.sh
# - install.sh, cleanup_v012.sh
# - requirements.txt, pytest.ini
# - .gitignore, .dockerignore, .env.example
# - README.md

# Should NOT see:
# - tempdata/
# - logseq/
# - web_interface.py, freshstart.py, setup.sh, start_web.sh
# - claude.md, IMPLEMENTATION_SUMMARY.md, QUICK_REFERENCE.md (at root)
```

### 2. Archive Verification

Verify old files were archived correctly:

```bash
# Check archive structure
ls -la archive/v0.1.0/

# Should contain:
# - scripts/          (old db_import.py, db_migrate.py, etc.)
# - docs/             (old logseq/ directory)
# - root_files/       (old web_interface.py, claude.md, etc.)
# - README.md         (explains archive contents)

# Verify old scripts are archived
ls archive/v0.1.0/scripts/

# Should see:
# - db_import.py, db_migrate.py, db_organize.py, db_folder.py
# - db_ingest.py, db_verify.py, db_identify.py
# - database_cleanup.py, backup.py, normalize.py, utils.py
# - test_drone_detection.py, test_video_metadata.py, test_web_interface.py
```

### 3. Scripts Directory

Verify only v0.1.2 scripts remain:

```bash
# Check scripts directory
ls -la scripts/

# Should contain ONLY:
# - adapters/ (directory with immich_adapter.py, archivebox_adapter.py)
# - db_migrate_v012.py
# - db_import_v012.py
# - api_routes_v012.py
# - immich_integration.py
# - __pycache__/ (will be regenerated, safe to ignore)

# Should NOT contain:
# - db_import.py (archived)
# - db_migrate.py (archived)
# - test_*.py files (should be in tests/)
```

### 4. Tests Directory

Verify all tests are consolidated:

```bash
# Check tests directory
ls -la tests/

# Should contain:
# - test_db_migrate_v012.py
# - test_adapters.py
# - test_immich_integration.py
# - test_api_routes.py
# - test_docker_compose.py
# - test_validation.py
# - e2e_test.sh
# - README.md
```

### 5. Docs Directory

Verify only v0.1.2 docs remain:

```bash
# Check docs structure
ls -la docs/

# Should contain:
# - v0.1.2/ (directory only)

# Should NOT contain:
# - v0.1.0/ or v0.1.1/ directories
# - Any root-level markdown files in docs/

# Check v0.1.2 docs
ls docs/v0.1.2/

# Should contain all v0.1.2 documentation files
```

### 6. Temporary Data Removal

Verify temporary data was deleted:

```bash
# These should NOT exist:
ls tempdata/           # Should error: No such file or directory
ls __pycache__/        # Should not exist at root (may exist in scripts/, that's ok)
ls .pytest_cache/      # Should not exist
ls .mypy_cache/        # Should not exist
ls htmlcov/            # Should not exist
find . -name "*.pyc"   # Should return nothing
find . -name ".DS_Store"  # Should return nothing
```

---

## Installation Script Verification

### 1. Install Script Execution

Run the install script:

```bash
# Make executable
chmod +x install.sh

# Run installation
./install.sh
```

Expected steps:
- Detects OS (macOS or Linux)
- Checks/installs Homebrew (macOS)
- Installs Python 3
- Installs exiftool
- Installs ffmpeg/ffprobe
- Checks Docker availability
- Creates Python virtual environment
- Installs Python dependencies
- Creates user/user.json from template
- Creates data directories
- Prints verification summary

### 2. Verify Dependencies

Check all tools are installed:

```bash
# Python
python3 --version
# Should output: Python 3.x.x

# exiftool
exiftool -ver
# Should output: version number (e.g., 12.50)

# ffprobe
ffprobe -version
# Should output: ffmpeg version info

# Docker
docker --version
# Should output: Docker version x.x.x

# docker-compose
docker-compose --version
# Or: docker compose version
# Should output: version info

# Git
git --version
# Should output: git version x.x.x
```

### 3. Verify Virtual Environment

Check Python virtual environment:

```bash
# Activate venv
source venv/bin/activate

# Check Python is from venv
which python
# Should output: /path/to/aupat/venv/bin/python

# Check installed packages
pip list

# Should include:
# - Flask
# - pytest
# - pytest-mock
# - requests
# - requests-mock
# - tenacity
# - Pillow (optional)
# - Other requirements.txt packages
```

### 4. Verify Configuration

Check user configuration:

```bash
# Check user.json was created
cat user/user.json

# Should contain:
# - Absolute paths to database, backups, ingest, archive
# - No placeholder paths like "/absolute/path"

# Verify directories were created
ls -la data/
# Should see: archive/, backups/, ingest/ (empty directories)

ls -la logs/
# Should exist (may be empty)
```

---

## Git Status Verification

### 1. Check Untracked Files

```bash
git status
```

Expected output:
- **New files** (untracked):
  - `archive/` (entire directory)
  - `install.sh`
  - `.gitignore.new` (if you haven't replaced .gitignore yet)
  - `README.new.md` (if you haven't replaced README.md yet)
  - `cleanup_v012.sh`
  - `VERIFICATION_CHECKLIST.md`

- **Deleted files**:
  - `web_interface.py`
  - `freshstart.py`
  - `setup.sh`
  - `start_web.sh`
  - `claude.md` (root level)
  - `IMPLEMENTATION_SUMMARY.md`
  - `QUICK_REFERENCE.md`
  - `scripts/db_import.py`
  - `scripts/db_migrate.py`
  - ... (other old scripts)
  - `logseq/` (entire directory)

- **Modified files**:
  - (None expected if cleanup script worked correctly)

### 2. Replace .gitignore and README.md

```bash
# Replace .gitignore
mv .gitignore .gitignore.old
mv .gitignore.new .gitignore

# Replace README.md
mv README.md README.old.md
mv README.new.md README.md

# Verify
git diff .gitignore
git diff README.md
```

### 3. Check Gitignored Files

Verify user data is properly ignored:

```bash
# These should be ignored (not in git status):
git status user/user.json
# Should output: nothing (file is ignored)

git status data/*.db
# Should output: nothing (ignored)

git status venv/
# Should output: nothing (ignored)

git status logs/
# Should output: nothing (ignored)

# Check .gitignore is working
cat .gitignore | grep "user/user.json"
# Should find the pattern
```

### 4. Review Changes Before Commit

```bash
# Review all changes
git status

# Check diff for modified files
git diff

# Check deleted files
git ls-files --deleted

# Check new files
git ls-files --others --exclude-standard
```

---

## Docker Services Verification

### 1. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# All services should be "healthy" or "running"
```

### 2. Health Checks

```bash
# AUPAT Core health
curl http://localhost:5000/api/health

# Expected response:
# {"status":"ok","version":"0.1.2","database":"connected","location_count":0}

# Immich health
curl http://localhost:2283/api/server-info/ping

# Expected response:
# {"res":"pong"}

# Service health check
curl http://localhost:5000/api/health/services

# Expected response:
# {"status":"ok|degraded","services":{"immich":"healthy|unhealthy","archivebox":"healthy|unhealthy"}}
```

### 3. Check Logs

```bash
# Check AUPAT Core logs
docker-compose logs aupat-core

# Check Immich logs
docker-compose logs immich-server

# Check for errors
docker-compose logs | grep -i error
# Should be minimal/none
```

---

## Test Suite Verification

### 1. Run All Tests

```bash
# Activate venv
source venv/bin/activate

# Run test suite
pytest -v

# Expected:
# - All tests should pass
# - ~72 test cases
# - Coverage ~88%
```

### 2. Run Specific Test Categories

```bash
# Unit tests only
pytest -v -m unit

# Integration tests
pytest -v -m integration

# Docker tests (requires docker-compose up)
pytest -v -m requires_docker

# Specific test file
pytest tests/test_adapters.py -v
```

### 3. Coverage Report

```bash
# Generate coverage report
pytest --cov=scripts --cov-report=term-missing

# Check coverage is above 70%
# Expected: ~88% for Phase 1 scope
```

---

## Final Checklist

- [ ] Archive directory created with v0.1.0 contents
- [ ] Old scripts removed from scripts/ and archived
- [ ] Old docs removed and archived
- [ ] Temporary data (tempdata/) deleted
- [ ] Python cache (__pycache__, .pytest_cache) cleaned
- [ ] install.sh executable and runs successfully
- [ ] Virtual environment created and dependencies installed
- [ ] user/user.json created with absolute paths
- [ ] Data directories created (data/archive, data/backups, data/ingest)
- [ ] .gitignore updated and working correctly
- [ ] README.md updated for v0.1.2
- [ ] git status shows expected changes
- [ ] Docker services start and health checks pass
- [ ] Test suite passes (pytest -v)
- [ ] No unintended files tracked by git
- [ ] No sensitive data (user.json, .db files) tracked by git

---

## Ready for Commit

If all checks pass, the repository is ready for git commit:

```bash
# Add all changes
git add .

# Review staged changes
git status

# Commit
git commit -m "v0.1.2: Repository cleanup and microservices architecture

- Archived v0.1.0 code to archive/v0.1.0/
- Removed temporary data and build artifacts
- Consolidated v0.1.2 microservices architecture
- Added bulletproof install.sh for macOS and Linux
- Updated .gitignore for Docker + Python + macOS
- Rewrote README.md for v0.1.2
- Comprehensive test suite (72 tests, 88% coverage)
- Docker Compose stack (AUPAT Core + Immich + ArchiveBox)
- REST API with 10+ endpoints
- Service adapters with retry logic and graceful degradation

Principles: KISS, BPL, BPA, DRETW, NME"

# Push to GitHub
git push origin main
```

---

## Rollback Procedure

If cleanup failed or you need to rollback:

```bash
# Restore from git (if you committed before cleanup)
git reset --hard HEAD~1

# Or restore individual files
git restore <file>

# Restore from archive
cp -r archive/v0.1.0/scripts/* scripts/
cp -r archive/v0.1.0/docs/logseq .
cp archive/v0.1.0/root_files/* .

# Clean up failed cleanup attempt
rm -rf archive/
```

---

## Post-Deployment Checklist

After pushing to GitHub:

- [ ] README renders correctly on GitHub
- [ ] .gitignore properly excludes sensitive files
- [ ] archive/ directory is visible and browsable
- [ ] docs/v0.1.2/ documentation is accessible
- [ ] No user.json or .db files visible on GitHub
- [ ] Install instructions in README work for fresh clones
- [ ] CI/CD workflows pass (if configured)

---

## Support

If verification fails:

1. Check logs: `docker-compose logs`
2. Review git status: `git status`
3. Check install script output
4. Verify all dependencies installed
5. See docs/v0.1.2/README.md for troubleshooting

For issues, see archive/v0.1.0/README.md to compare with old architecture.
