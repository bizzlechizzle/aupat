#!/usr/bin/env bash
#
# AUPAT v0.1.0 Smart Startup Script
# Starts both the backend Flask server and frontend development server
# with intelligent first-run detection and health checks
#
# Usage:
#   ./start_aupat.sh              # Normal startup with health checks
#   ./start_aupat.sh --skip-health # Skip health checks (advanced)
#
# LILBITS: One script = one function (smart startup)
# Lines: <200 (LILBITS compliant)
#

set -e

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
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo ""
echo "========================================="
echo "  AUPAT v0.1.0 Startup"
echo "========================================="
echo ""

# Check if port 5002 is in use
if lsof -Pi :5002 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    log_error "Port 5002 is already in use!"
    echo ""
    echo "Options:"
    echo "  1. Stop the service using port 5002"
    echo "  2. Change port in app.py and desktop/src/main/index.js"
    echo ""
    exit 1
fi

# Activate virtual environment
log_info "Activating virtual environment..."
if [ ! -d "venv" ]; then
    log_error "Virtual environment not found!"
    log_info "Run: python3 -m venv venv"
    log_info "Or run: ./bootstrap_v010.sh for complete setup"
    exit 1
fi

source "$SCRIPT_DIR/venv/bin/activate"
log_success "Virtual environment activated"

# Set PYTHONPATH so scripts can import from scripts/ module
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
log_info "PYTHONPATH set to $SCRIPT_DIR"

# Set default database path
export DB_PATH="${DB_PATH:-$SCRIPT_DIR/data/aupat.db}"

# Run health checks (unless skipped)
if [ "$1" != "--skip-health" ]; then
    echo ""
    log_info "Running health checks..."
    echo ""

    if python3 scripts/health_check_simple.py; then
        echo ""
        log_success "Health checks passed"
    else
        echo ""
        log_warn "Health checks failed - see issues above"
        echo ""
        echo "Common fixes:"
        echo "  - Missing database? Run: python scripts/db_migrate_v010.py"
        echo "  - Missing desktop deps? Run: cd desktop && npm install"
        echo "  - Or run full bootstrap: ./bootstrap_v010.sh"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Startup cancelled"
            exit 1
        fi
    fi
fi

# Start backend server in background
echo ""
log_info "Starting backend server..."
log_info "Backend will run on: http://localhost:5002"
python3 app.py &
BACKEND_PID=$!
log_success "Backend PID: $BACKEND_PID"

# Give the backend a moment to start
sleep 2

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    log_error "Backend failed to start!"
    log_info "Check logs above for error details"
    exit 1
fi

# Start frontend dev server
echo ""
log_info "Starting frontend dev server..."
cd "$SCRIPT_DIR/desktop"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    log_warn "Desktop dependencies not installed!"
    log_info "Installing npm packages (this may take a few minutes)..."
    npm install
    log_success "Desktop dependencies installed"
fi

npm run dev &
FRONTEND_PID=$!
log_success "Frontend PID: $FRONTEND_PID"

cd "$SCRIPT_DIR"

echo ""
echo "========================================="
log_success "AUPAT v0.1.0 is running!"
echo "========================================="
echo ""
echo "Backend:  http://localhost:5002"
echo "Frontend: Electron window should open automatically"
echo "API Docs: http://localhost:5002/api/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    log_info "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true

    # Wait a moment for graceful shutdown
    sleep 1

    # Force kill if still running
    kill -9 $BACKEND_PID 2>/dev/null || true
    kill -9 $FRONTEND_PID 2>/dev/null || true

    log_success "Servers stopped"
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup INT TERM

# Wait for both processes
wait
