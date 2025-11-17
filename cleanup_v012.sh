#!/usr/bin/env bash
#
# AUPAT v0.1.2 Repository Cleanup and Archival Script
#
# This script:
# 1. Creates archive/v0.1.0/ for old code
# 2. Moves v0.1.0/v0.1.1 scripts and docs to archive
# 3. Deletes temporary data and build artifacts
# 4. Reorganizes test scripts
# 5. Cleans Python cache
#
# Principles: KISS, BPL, BPA, DRETW
# Safe to run multiple times (idempotent)
#

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "========================================="
echo "AUPAT v0.1.2 Repository Cleanup"
echo "========================================="
echo ""
echo "Repository: $REPO_ROOT"
echo ""

# Confirm before proceeding
read -p "This will archive old files and delete temp data. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "[1/7] Creating archive directory structure..."
mkdir -p archive/v0.1.0/scripts
mkdir -p archive/v0.1.0/docs
mkdir -p archive/v0.1.0/root_files

echo "[2/7] Archiving old v0.1.0/v0.1.1 scripts..."

# Move old scripts to archive (keep only v0.1.2 scripts in scripts/)
old_scripts=(
    "db_import.py"
    "db_migrate.py"
    "db_organize.py"
    "db_folder.py"
    "db_ingest.py"
    "db_verify.py"
    "db_identify.py"
    "database_cleanup.py"
    "backup.py"
    "normalize.py"
    "utils.py"
    "validation.py"
    "db_migrate_indices.py"
    "test_drone_detection.py"
    "test_video_metadata.py"
    "test_web_interface.py"
)

for script in "${old_scripts[@]}"; do
    if [[ -f "scripts/$script" ]]; then
        echo "  Archiving scripts/$script"
        mv "scripts/$script" "archive/v0.1.0/scripts/"
    fi
done

echo "[3/7] Archiving old root-level files..."

# Move old root files to archive
old_root_files=(
    "web_interface.py"
    "freshstart.py"
    "setup.sh"
    "start_web.sh"
    "claude.md"
    "IMPLEMENTATION_SUMMARY.md"
    "QUICK_REFERENCE.md"
)

for file in "${old_root_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  Archiving $file"
        mv "$file" "archive/v0.1.0/root_files/"
    fi
done

echo "[4/7] Archiving old documentation..."

# Move logseq documentation to archive
if [[ -d "logseq" ]]; then
    echo "  Archiving logseq/ (v0.1.0 docs)"
    mv logseq archive/v0.1.0/docs/
fi

echo "[5/7] Cleaning temporary data and build artifacts..."

# Delete temporary data directories
if [[ -d "tempdata" ]]; then
    echo "  Deleting tempdata/"
    rm -rf tempdata
fi

# Clean Python cache
echo "  Cleaning __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Clean pytest cache
if [[ -d ".pytest_cache" ]]; then
    echo "  Cleaning .pytest_cache/"
    rm -rf .pytest_cache
fi

# Clean mypy cache
if [[ -d ".mypy_cache" ]]; then
    echo "  Cleaning .mypy_cache/"
    rm -rf .mypy_cache
fi

# Clean coverage reports
if [[ -d "htmlcov" ]]; then
    echo "  Cleaning htmlcov/"
    rm -rf htmlcov
fi

if [[ -f ".coverage" ]]; then
    echo "  Removing .coverage"
    rm -f .coverage
fi

# Clean macOS cruft
echo "  Cleaning macOS .DS_Store files..."
find . -name ".DS_Store" -delete 2>/dev/null || true

echo "[6/7] Reorganizing test scripts..."

# Move any test scripts from scripts/ to tests/ (if not already done)
if [[ -f "scripts/test_phase1.py" ]]; then
    echo "  Moving scripts/test_phase1.py to tests/"
    mv scripts/test_phase1.py tests/
fi

echo "[7/7] Creating archive README..."

# Create README in archive to explain contents
cat > archive/v0.1.0/README.md << 'EOF'
# AUPAT v0.1.0/v0.1.1 Archive

This directory contains historical code and documentation from AUPAT v0.1.0 and v0.1.1.

## Archived: November 2025

**Reason for archival**: v0.1.2 introduced a complete architectural change:
- Old: Monolithic web interface with local file processing
- New: Microservices architecture (Docker Compose) with Immich + ArchiveBox integration

## Directory Structure

```
v0.1.0/
├── scripts/           # Old CLI pipeline scripts
├── docs/              # Old Logseq documentation
└── root_files/        # Old root-level utilities and web interface
```

## Old Architecture (v0.1.0/v0.1.1)

- **web_interface.py**: Flask web UI with embedded import pipeline
- **CLI Pipeline**: db_import.py -> db_organize.py -> db_folder.py -> db_ingest.py -> db_verify.py
- **Local Processing**: All metadata extraction and file management done locally
- **No External Services**: Self-contained Python application

## New Architecture (v0.1.2)

- **Docker Compose**: 6-service orchestration (AUPAT Core, Immich, ArchiveBox, PostgreSQL, Redis, ML)
- **Service Adapters**: Immich for photo storage, ArchiveBox for web archiving
- **REST API**: api_routes_v012.py provides endpoints for desktop app
- **Microservices Pattern**: Separation of concerns with external service integration

## Migration Notes

If you need to run old v0.1.0 code:

1. Copy scripts from archive/v0.1.0/scripts/ to a separate directory
2. Install old requirements (no Docker, no Immich/ArchiveBox dependencies)
3. Run setup.sh from archive/v0.1.0/root_files/
4. Use web_interface.py or CLI pipeline as documented in old README

**Not recommended for new deployments. Use v0.1.2 instead.**

## Reference Documentation

Old documentation preserved in archive/v0.1.0/docs/logseq/pages/:
- claude.md - AI collaboration guide
- claudecode.md - Development methodology
- db_*.md - Script specifications
- *_table.md - Database schemas

These docs describe the v0.1.0 architecture and are kept for historical reference only.
EOF

echo ""
echo "========================================="
echo "Cleanup Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  - Old scripts archived to: archive/v0.1.0/scripts/"
echo "  - Old documentation archived to: archive/v0.1.0/docs/"
echo "  - Old root files archived to: archive/v0.1.0/root_files/"
echo "  - Temporary data deleted: tempdata/"
echo "  - Build artifacts cleaned: __pycache__, .pytest_cache, etc."
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Run install script: ./install.sh"
echo "  3. Verify tests pass: pytest -v"
echo "  4. Start services: docker-compose up -d"
echo ""
