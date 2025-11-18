#!/usr/bin/env bash
#
# AUPAT API Server Startup Script
#
# This script checks if the AUPAT API server is running and starts it if needed.
# It ensures the database exists and all dependencies are installed.
#
# Usage:
#   ./start_api.sh        # Start server if not running
#   ./start_api.sh --force # Kill existing server and restart
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
API_PORT=5002
DB_PATH="${SCRIPT_DIR}/data/aupat.db"
LOG_FILE="${SCRIPT_DIR}/api_server.log"
PID_FILE="${SCRIPT_DIR}/api_server.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if server is running
is_server_running() {
    # Check if responding to health check
    if curl -s -f "http://localhost:${API_PORT}/api/health" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Get PID of running server
get_server_pid() {
    pgrep -f "python3.*app.py" | head -1
}

# Kill existing server
kill_server() {
    local pid=$(get_server_pid)
    if [ -n "$pid" ]; then
        log_info "Stopping server (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 2

        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            log_warning "Force killing server..."
            kill -9 "$pid" 2>/dev/null || true
        fi
    fi
    rm -f "$PID_FILE"
}

# Check and install dependencies
check_dependencies() {
    log_info "Checking Python dependencies..."

    if ! python3 -c "import flask" 2>/dev/null; then
        log_warning "Flask not installed, installing dependencies..."
        pip3 install --break-system-packages -r requirements.txt || {
            log_error "Failed to install dependencies"
            exit 1
        }
    fi

    log_success "Dependencies OK"
}

# Check and initialize database
check_database() {
    log_info "Checking database..."

    # Check if user.json exists
    if [ ! -f "user/user.json" ]; then
        log_warning "user.json not found, creating from template..."
        cat > user/user.json <<EOF
{
  "db_name": "aupat.db",
  "db_loc": "${DB_PATH}",
  "db_backup": "${SCRIPT_DIR}/backups/",
  "db_ingest": "${SCRIPT_DIR}/ingest/",
  "arch_loc": "${SCRIPT_DIR}/archive/"
}
EOF
        log_success "Created user.json"
    fi

    # Check if database exists
    if [ ! -f "$DB_PATH" ]; then
        log_warning "Database not found, creating..."
        python3 scripts/db_migrate_v012.py || {
            log_error "Failed to create database"
            exit 1
        }
        log_success "Database created"
    else
        log_success "Database OK"
    fi
}

# Start the server
start_server() {
    log_info "Starting AUPAT API server on port ${API_PORT}..."

    export DB_PATH="${DB_PATH}"

    # Start server in background
    nohup python3 app.py > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"

    # Wait for server to start
    log_info "Waiting for server to start..."
    for i in {1..10}; do
        sleep 1
        if is_server_running; then
            log_success "API server started successfully (PID: $pid)"
            log_info "API URL: http://localhost:${API_PORT}"
            log_info "Log file: ${LOG_FILE}"
            return 0
        fi
    done

    log_error "Server failed to start within 10 seconds"
    log_info "Check log file: ${LOG_FILE}"
    cat "$LOG_FILE"
    exit 1
}

# Show status
show_status() {
    if is_server_running; then
        local pid=$(get_server_pid)
        log_success "API server is running (PID: $pid)"
        log_info "Health check: http://localhost:${API_PORT}/api/health"

        # Show health info
        echo ""
        echo "Health Status:"
        curl -s "http://localhost:${API_PORT}/api/health" | python3 -m json.tool || true
        return 0
    else
        log_warning "API server is not running"
        return 1
    fi
}

# Main script
main() {
    echo "======================================"
    echo "  AUPAT API Server Startup Script"
    echo "======================================"
    echo ""

    # Handle --force flag
    if [ "$1" == "--force" ]; then
        kill_server
    fi

    # Handle --status flag
    if [ "$1" == "--status" ]; then
        show_status
        exit $?
    fi

    # Check if already running
    if is_server_running; then
        log_success "API server is already running"
        show_status
        exit 0
    fi

    # Check dependencies
    check_dependencies

    # Check database
    check_database

    # Start server
    start_server

    echo ""
    echo "======================================"
    log_success "AUPAT API Server Ready"
    echo "======================================"
}

# Run main function
main "$@"
