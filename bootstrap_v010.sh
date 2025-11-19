#!/usr/bin/env bash
#
# AUPAT v0.1.0 Bootstrap Script
# ONE script to set up AUPAT from zero to running desktop app
#
# Usage: ./bootstrap_v010.sh
#
# What this does:
# 1. Checks prerequisites (Python, Node, exiftool, ffmpeg)
# 2. Creates Python virtual environment
# 3. Installs Python dependencies
# 4. Creates user configuration
# 5. Creates database with v0.1.0 schema
# 6. Installs desktop dependencies
# 7. Starts AUPAT desktop app
#
# LILBITS: One script = one function (Bootstrap v0.1.0)
# Lines: ~180 (under 200 line limit)
#

set -e  # Exit on any error

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output (NME compliant - no emojis)
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_step() { echo -e "${YELLOW}[STEP]${NC} $1"; }

echo ""
echo "========================================"
echo "  AUPAT v0.1.0 Bootstrap"
echo "========================================"
echo ""

# STEP 1: Check Prerequisites
log_step "Checking prerequisites..."

# Check Python 3.11+
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        log_success "Python $PYTHON_VERSION found"
    else
        log_error "Python 3.11+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    log_error "Python 3 not found - install Python 3.11+ first"
    exit 1
fi

# Check Node 22+
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)

    if [ "$NODE_MAJOR" -ge 22 ]; then
        log_success "Node v$NODE_VERSION found"
    else
        log_error "Node 22+ required, found v$NODE_VERSION"
        exit 1
    fi
else
    log_error "Node.js not found - install Node 22+ first"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    log_error "npm not found - install npm first"
    exit 1
fi
log_success "npm $(npm --version) found"

# Check exiftool
if command -v exiftool &> /dev/null; then
    log_success "exiftool found"
else
    log_error "exiftool not found - install with: brew install exiftool (macOS) or apt-get install libimage-exiftool-perl (Linux)"
    exit 1
fi

# Check ffmpeg/ffprobe
if command -v ffprobe &> /dev/null; then
    log_success "ffmpeg/ffprobe found"
else
    log_error "ffmpeg not found - install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
    exit 1
fi

# STEP 2: Create Python Virtual Environment
log_step "Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    log_info "Creating venv..."
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_info "venv already exists, skipping creation"
fi

# Activate venv
source venv/bin/activate
log_success "Virtual environment activated"

# STEP 3: Install Python Dependencies
log_step "Installing Python dependencies..."

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
log_success "Python packages installed"

# STEP 4: Create User Configuration
log_step "Setting up configuration..."

USER_JSON="$SCRIPT_DIR/user/user.json"
USER_TEMPLATE="$SCRIPT_DIR/user/user.json.template"

if [ ! -f "$USER_JSON" ]; then
    if [ -f "$USER_TEMPLATE" ]; then
        log_info "Creating user.json from template..."

        # Create user.json with correct paths
        cat > "$USER_JSON" <<EOF
{
  "db_name": "aupat.db",
  "db_loc": "$SCRIPT_DIR/data",
  "staging_loc": "$SCRIPT_DIR/staging",
  "archive_loc": "$SCRIPT_DIR/archive",
  "backup_loc": "$SCRIPT_DIR/backups",
  "ingest_loc": "$SCRIPT_DIR/ingest"
}
EOF
        log_success "user.json created"
    else
        log_error "user.json.template not found"
        exit 1
    fi
else
    log_info "user.json already exists, skipping"
fi

# Create necessary directories
mkdir -p "$SCRIPT_DIR/data"
mkdir -p "$SCRIPT_DIR/staging"
mkdir -p "$SCRIPT_DIR/archive"
mkdir -p "$SCRIPT_DIR/backups"
mkdir -p "$SCRIPT_DIR/ingest"
log_success "Directories created"

# STEP 5: Create Database
log_step "Creating database..."

DB_PATH="$SCRIPT_DIR/data/aupat.db"

if [ ! -f "$DB_PATH" ]; then
    log_info "Running database migration (this creates fresh v0.1.0 schema)..."
    python3 scripts/db_migrate_v010.py
    log_success "Database created at $DB_PATH"
else
    log_info "Database already exists at $DB_PATH"
    log_info "If you want fresh database, delete it first: rm $DB_PATH"
fi

# Ensure stats columns exist (for existing databases)
log_info "Ensuring dashboard stats columns exist..."
python3 scripts/db_migrate_add_stats_columns.py
log_success "Stats columns verified"

# STEP 6: Install Desktop Dependencies
log_step "Installing desktop app dependencies..."

cd "$SCRIPT_DIR/desktop"

if [ ! -d "node_modules" ]; then
    log_info "Running npm install (this may take a few minutes)..."
    npm install > /dev/null 2>&1
    log_success "Desktop dependencies installed"
else
    log_info "node_modules already exists, skipping npm install"
fi

cd "$SCRIPT_DIR"

# STEP 7: Success Message
echo ""
echo "========================================"
log_success "Bootstrap complete!"
echo "========================================"
echo ""
log_info "AUPAT v0.1.0 is ready to launch"
log_info "Starting desktop app..."
echo ""

# STEP 8: Start AUPAT
./start_aupat.sh
