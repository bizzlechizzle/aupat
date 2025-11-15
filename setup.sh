#!/bin/bash
# AUPAT Setup Script
# Creates project structure, virtual environment, and installs dependencies
# Version: 1.0.0
# Last Updated: 2025-11-15

set -e  # Exit on error

echo "========================================="
echo "AUPAT Setup Script"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "$1"
}

# Check if running from correct directory
if [ ! -f "claude.md" ] || [ ! -f "project-overview.md" ]; then
    print_error "Error: Must run setup.sh from the aupat project root directory"
    exit 1
fi

print_success "Running from correct directory"
echo ""

# Step 1: Check Python version
print_info "Step 1: Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        print_success "Python $PYTHON_VERSION found (>= 3.9 required)"
    else
        print_error "Python $PYTHON_VERSION found, but 3.9+ required"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.9 or later"
    exit 1
fi
echo ""

# Step 2: Create folder structure
print_info "Step 2: Creating folder structure..."
mkdir -p scripts
mkdir -p data
mkdir -p user
mkdir -p backups
mkdir -p logs
print_success "Created: scripts/ data/ user/ backups/ logs/"
echo ""

# Step 3: Create virtual environment
print_info "Step 3: Creating Python virtual environment..."
if [ -d "venv" ]; then
    print_warning "venv/ already exists, skipping creation"
else
    python3 -m venv venv
    print_success "Virtual environment created in venv/"
fi
echo ""

# Step 4: Activate virtual environment and upgrade pip
print_info "Step 4: Activating virtual environment and upgrading pip..."
source venv/bin/activate
pip install --upgrade pip --quiet
print_success "Virtual environment activated and pip upgraded"
echo ""

# Step 5: Install Python dependencies
print_info "Step 5: Installing Python dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi
echo ""

# Step 6: Verify Python packages
print_info "Step 6: Verifying Python packages..."
if python3 -c "import unidecode" 2>/dev/null; then
    print_success "unidecode installed"
else
    print_error "unidecode installation failed"
fi
python3 -c "import dateutil; print('  ✓ python-dateutil:', dateutil.__version__)" || print_error "python-dateutil installation failed"
python3 -c "import pytest; print('  ✓ pytest:', pytest.__version__)" || print_error "pytest installation failed"
echo ""

# Check postal (may fail on some systems)
if python3 -c "import postal" 2>/dev/null; then
    print_success "postal (libpostal) installed successfully"
else
    print_warning "postal (libpostal) installation failed or not available"
    print_info "  Note: libpostal requires system library installation first"
    print_info "  macOS: brew install libpostal"
    print_info "  Ubuntu: apt-get install libpostal-dev"
    print_info "  You can continue without it, but location name normalization will be limited"
fi
echo ""

# Step 7: Check for external tools
print_info "Step 7: Checking for external tools..."

# Check for exiftool
if command -v exiftool &> /dev/null; then
    EXIFTOOL_VERSION=$(exiftool -ver 2>&1)
    print_success "exiftool $EXIFTOOL_VERSION found"
else
    print_warning "exiftool not found"
    print_info "  Install: brew install exiftool (macOS) or apt-get install libimage-exiftool-perl (Ubuntu)"
fi

# Check for ffprobe
if command -v ffprobe &> /dev/null; then
    FFPROBE_VERSION=$(ffprobe -version 2>&1 | head -n1 | awk '{print $3}')
    print_success "ffprobe $FFPROBE_VERSION found"
else
    print_warning "ffprobe not found"
    print_info "  Install: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)"
fi
echo ""

# Step 8: Create user.json template
print_info "Step 8: Creating user/user.json template..."
if [ -f "user/user.json" ]; then
    print_warning "user/user.json already exists, skipping creation"
else
    cat > user/user.json << 'EOF'
{
  "db_name": "aupat.db",
  "db_loc": "/absolute/path/to/database/aupat.db",
  "db_backup": "/absolute/path/to/backups/",
  "db_ingest": "/absolute/path/to/ingest/staging/",
  "arch_loc": "/absolute/path/to/archive/"
}
EOF
    print_success "Created user/user.json template"
    print_warning "IMPORTANT: Edit user/user.json with your actual paths before running scripts"
fi
echo ""

# Step 9: Make scripts executable
print_info "Step 9: Making scripts executable..."
if [ -d "scripts" ] && [ "$(ls -A scripts/*.py 2>/dev/null)" ]; then
    chmod +x scripts/*.py
    print_success "All Python scripts are now executable"
else
    print_warning "No Python scripts found in scripts/ directory"
fi
echo ""

# Step 10: Verify scripts can be imported
print_info "Step 10: Verifying script modules..."
cd scripts 2>/dev/null && {
    if python3 -c "import utils" 2>/dev/null; then
        print_success "utils.py imports successfully"
    else
        print_warning "utils.py import failed (may not exist yet)"
    fi

    if python3 -c "import normalize" 2>/dev/null; then
        print_success "normalize.py imports successfully"
    else
        print_warning "normalize.py import failed (may not exist yet)"
    fi
    cd ..
}
echo ""

# Step 11: Verify .gitignore
print_info "Step 11: Verifying .gitignore..."
if grep -q "^venv/" .gitignore 2>/dev/null && \
   grep -q "^backups/" .gitignore 2>/dev/null && \
   grep -q "^logs/" .gitignore 2>/dev/null; then
    print_success ".gitignore already configured"
else
    print_warning ".gitignore may need updates (venv/, backups/, logs/)"
fi
echo ""

# Summary
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
print_info "Next steps:"
print_info "  1. Edit user/user.json with your actual paths (REQUIRED)"
print_info "  2. Install external tools if not found:"
if ! command -v exiftool &> /dev/null; then
    print_info "     - exiftool: brew install exiftool (macOS) or apt-get install libimage-exiftool-perl"
fi
if ! command -v ffprobe &> /dev/null; then
    print_info "     - ffprobe: brew install ffmpeg (macOS) or apt-get install ffmpeg"
fi
if ! python3 -c "import postal" 2>/dev/null; then
    print_info "  3. Optional: Install libpostal for advanced address normalization"
    print_info "     - macOS: brew install libpostal && pip install postal"
    print_info "     - Ubuntu: apt-get install libpostal-dev && pip install postal"
fi
print_info "  4. Initialize database: python3 scripts/db_migrate.py"
print_info "  5. Start importing media: python3 scripts/db_import.py --source /path/to/media"
echo ""
print_success "Virtual environment is ready in venv/"
print_info "  Activate: source venv/bin/activate"
print_info "  Deactivate: deactivate"
echo ""
print_info "For full workflow, run these scripts in order:"
print_info "  1. db_migrate.py   - Create database schema"
print_info "  2. db_import.py    - Import location and media"
print_info "  3. db_organize.py  - Extract metadata and categorize"
print_info "  4. db_folder.py    - Create archive folder structure"
print_info "  5. db_ingest.py    - Move files to archive"
print_info "  6. db_verify.py    - Verify integrity and cleanup staging"
print_info "  7. db_identify.py  - Generate JSON exports"
echo ""
