#!/bin/bash
#
# AUPAT Unified Launch Script
# Version: 1.0.0
#
# This script consolidates all startup methods into a single unified launcher.
# Supports development, API-only, Docker, and status check modes.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/venv"
PID_FILE="${PROJECT_ROOT}/.aupat.pid"
API_PID_FILE="${PROJECT_ROOT}/api_server.pid"
LOG_FILE="${PROJECT_ROOT}/aupat.log"
DB_PATH="${DB_PATH:-${PROJECT_ROOT}/data/aupat.db}"
API_PORT="${PORT:-5002}"

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  AUPAT - Abandoned Upstate Archive Tracker${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

show_help() {
    print_header
    cat << EOF
Usage: ./launch.sh [MODE] [OPTIONS]

MODES:
  --dev, -d          Start full stack (API + Desktop) for development
                     - Flask API on port ${API_PORT}
                     - Electron desktop app with hot reload

  --api, -a          Start API server only (no desktop app)
                     - Flask API on port ${API_PORT}
                     - Suitable for headless deployments

  --docker           Start full stack with Docker Compose
                     - AUPAT Core, Immich, ArchiveBox, PostgreSQL, Redis
                     - See docker-compose.yml for details

  --status, -s       Show status of running services
                     - Check if API is running
                     - Check health endpoints
                     - Show PIDs and ports

  --stop             Stop all running AUPAT services
                     - Gracefully shutdown API and desktop app
                     - Remove PID files

  --health, -h       Run comprehensive health check
                     - Database connectivity
                     - File system access
                     - External tools (exiftool, ffmpeg)
                     - External services (Immich, ArchiveBox)

  --help             Show this help message

OPTIONS:
  --port PORT        Override API port (default: 5002)
  --db PATH          Override database path

EXAMPLES:
  ./launch.sh --dev              # Start development environment
  ./launch.sh --api              # Start API server only
  ./launch.sh --docker           # Start with Docker Compose
  ./launch.sh --status           # Check what's running
  ./launch.sh --stop             # Stop everything
  ./launch.sh --health           # Run health checks
  ./launch.sh --api --port 5000  # Start API on custom port

ENVIRONMENT VARIABLES:
  DB_PATH            Database location (default: data/aupat.db)
  PORT               API server port (default: 5002)
  FLASK_ENV          Flask environment (development/production)

For more information, see:
  - README.md (quick start)
  - techguide.md (technical details)
  - lilbits.md (script documentation)
  - claude.md (development rules)

EOF
}

check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.8+"
        return 1
    fi
    print_success "Python 3 found: $(python3 --version)"

    # Check virtual environment
    if [ ! -d "${VENV_PATH}" ]; then
        print_warning "Virtual environment not found. Run ./install.sh first"
        return 1
    fi
    print_success "Virtual environment found"

    # Check database
    if [ ! -f "${DB_PATH}" ]; then
        print_warning "Database not found at ${DB_PATH}"
        print_info "Will create database on first run"
    else
        print_success "Database found at ${DB_PATH}"
    fi

    return 0
}

check_port() {
    local port=$1
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port in use
    else
        return 1  # Port available
    fi
}

get_pid_from_port() {
    local port=$1
    lsof -Pi :${port} -sTCP:LISTEN -t 2>/dev/null || echo ""
}

start_dev_mode() {
    print_header
    print_info "Starting AUPAT in development mode..."
    echo ""

    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi

    # Check if API already running
    if check_port ${API_PORT}; then
        local pid=$(get_pid_from_port ${API_PORT})
        print_error "Port ${API_PORT} already in use by process ${pid}"
        print_info "Run './launch.sh --stop' to stop existing services"
        exit 1
    fi

    # Activate virtual environment
    source "${VENV_PATH}/bin/activate"

    # Export environment variables
    export DB_PATH="${DB_PATH}"
    export FLASK_ENV=development

    print_info "Starting Flask API on port ${API_PORT}..."

    # Start Flask in background
    cd "${PROJECT_ROOT}"
    python app.py > "${LOG_FILE}" 2>&1 &
    API_PID=$!
    echo ${API_PID} > "${API_PID_FILE}"

    # Wait for API to start
    print_info "Waiting for API to start..."
    for i in {1..10}; do
        if curl -s http://localhost:${API_PORT}/api/health > /dev/null 2>&1; then
            print_success "API started successfully (PID: ${API_PID})"
            break
        fi
        if [ $i -eq 10 ]; then
            print_error "API failed to start. Check ${LOG_FILE} for errors"
            kill ${API_PID} 2>/dev/null || true
            rm -f "${API_PID_FILE}"
            exit 1
        fi
        sleep 1
    done

    # Start desktop app
    print_info "Starting Electron desktop app..."
    cd "${PROJECT_ROOT}/desktop"

    if [ ! -d "node_modules" ]; then
        print_warning "Desktop dependencies not installed. Installing..."
        npm install
    fi

    npm run dev &
    DESKTOP_PID=$!

    # Store PIDs
    echo "${API_PID},${DESKTOP_PID}" > "${PID_FILE}"

    echo ""
    print_success "AUPAT started successfully!"
    echo ""
    print_info "API: http://localhost:${API_PORT}"
    print_info "Desktop app will open automatically"
    print_info "Logs: ${LOG_FILE}"
    echo ""
    print_info "Press Ctrl+C to stop all services"
    echo ""

    # Wait for user interrupt
    trap "stop_services; exit 0" INT TERM

    # Keep script running
    wait
}

start_api_mode() {
    print_header
    print_info "Starting AUPAT API server..."
    echo ""

    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi

    # Check if API already running
    if check_port ${API_PORT}; then
        local pid=$(get_pid_from_port ${API_PORT})
        print_error "Port ${API_PORT} already in use by process ${pid}"
        print_info "Run './launch.sh --stop' to stop existing services"
        exit 1
    fi

    # Activate virtual environment
    source "${VENV_PATH}/bin/activate"

    # Export environment variables
    export DB_PATH="${DB_PATH}"
    export FLASK_ENV="${FLASK_ENV:-production}"

    print_info "Starting Flask API on port ${API_PORT}..."

    # Start Flask
    cd "${PROJECT_ROOT}"
    python app.py
}

start_docker_mode() {
    print_header
    print_info "Starting AUPAT with Docker Compose..."
    echo ""

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first"
        exit 1
    fi

    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose not found. Please install docker-compose first"
        exit 1
    fi

    # Use existing docker-start.sh if available
    if [ -f "${PROJECT_ROOT}/docker-start.sh" ]; then
        print_info "Using existing docker-start.sh..."
        exec "${PROJECT_ROOT}/docker-start.sh"
    else
        # Basic docker-compose up
        cd "${PROJECT_ROOT}"
        docker-compose up -d

        print_success "Docker services started"
        print_info "API: http://localhost:5001"
        print_info "Immich: http://localhost:2283"
        print_info "ArchiveBox: http://localhost:8001"
    fi
}

show_status() {
    print_header
    print_info "Checking AUPAT service status..."
    echo ""

    # Check API
    if check_port ${API_PORT}; then
        local pid=$(get_pid_from_port ${API_PORT})
        print_success "API running on port ${API_PORT} (PID: ${pid})"

        # Check health endpoint
        if curl -s http://localhost:${API_PORT}/api/health > /dev/null 2>&1; then
            print_success "API health check passed"

            # Show version info
            local health=$(curl -s http://localhost:${API_PORT}/api/health)
            echo "  ${health}"
        else
            print_warning "API health check failed"
        fi
    else
        print_warning "API not running on port ${API_PORT}"
    fi

    echo ""

    # Check PID files
    if [ -f "${PID_FILE}" ]; then
        print_info "PID file found: ${PID_FILE}"
        cat "${PID_FILE}"
    fi

    if [ -f "${API_PID_FILE}" ]; then
        print_info "API PID file found: ${API_PID_FILE}"
        cat "${API_PID_FILE}"
    fi

    echo ""

    # Check Docker services
    if command -v docker &> /dev/null; then
        if docker ps | grep -q aupat; then
            print_success "Docker services running:"
            docker ps | grep aupat
        else
            print_info "No Docker services running"
        fi
    fi
}

stop_services() {
    print_header
    print_info "Stopping AUPAT services..."
    echo ""

    # Stop from PID file
    if [ -f "${PID_FILE}" ]; then
        local pids=$(cat "${PID_FILE}")
        IFS=',' read -ra PID_ARRAY <<< "$pids"
        for pid in "${PID_ARRAY[@]}"; do
            if ps -p $pid > /dev/null 2>&1; then
                print_info "Stopping process ${pid}..."
                kill $pid 2>/dev/null || true
                sleep 1
                if ps -p $pid > /dev/null 2>&1; then
                    kill -9 $pid 2>/dev/null || true
                fi
                print_success "Process ${pid} stopped"
            fi
        done
        rm -f "${PID_FILE}"
    fi

    # Stop from API PID file
    if [ -f "${API_PID_FILE}" ]; then
        local api_pid=$(cat "${API_PID_FILE}")
        if ps -p $api_pid > /dev/null 2>&1; then
            print_info "Stopping API (PID: ${api_pid})..."
            kill $api_pid 2>/dev/null || true
            sleep 1
            if ps -p $api_pid > /dev/null 2>&1; then
                kill -9 $api_pid 2>/dev/null || true
            fi
            print_success "API stopped"
        fi
        rm -f "${API_PID_FILE}"
    fi

    # Stop any process using API port
    if check_port ${API_PORT}; then
        local pid=$(get_pid_from_port ${API_PORT})
        if [ -n "$pid" ]; then
            print_info "Stopping process on port ${API_PORT} (PID: ${pid})..."
            kill $pid 2>/dev/null || true
            sleep 1
            print_success "Port ${API_PORT} freed"
        fi
    fi

    # pkill as last resort
    pkill -f "python.*app.py" 2>/dev/null || true
    pkill -f "electron.*aupat" 2>/dev/null || true

    echo ""
    print_success "All services stopped"
}

run_health_check() {
    print_header
    print_info "Running comprehensive health check..."
    echo ""

    # Activate virtual environment
    if [ -d "${VENV_PATH}" ]; then
        source "${VENV_PATH}/bin/activate"
    fi

    # Check if health_check.py exists
    if [ -f "${PROJECT_ROOT}/scripts/health_check.py" ]; then
        python "${PROJECT_ROOT}/scripts/health_check.py"
    else
        print_warning "scripts/health_check.py not found"
        print_info "Running basic health checks..."

        # Basic checks
        echo ""
        print_info "Database check..."
        if [ -f "${DB_PATH}" ]; then
            print_success "Database found at ${DB_PATH}"
        else
            print_error "Database not found at ${DB_PATH}"
        fi

        echo ""
        print_info "External tools check..."
        if command -v exiftool &> /dev/null; then
            print_success "exiftool found: $(exiftool -ver)"
        else
            print_warning "exiftool not found (required for EXIF extraction)"
        fi

        if command -v ffmpeg &> /dev/null; then
            print_success "ffmpeg found: $(ffmpeg -version | head -n1)"
        else
            print_warning "ffmpeg not found (required for video metadata)"
        fi

        echo ""
        print_info "API health check..."
        if check_port ${API_PORT}; then
            if curl -s http://localhost:${API_PORT}/api/health > /dev/null 2>&1; then
                print_success "API health check passed"
            else
                print_error "API health check failed"
            fi
        else
            print_warning "API not running"
        fi
    fi
}

# Main script
main() {
    # Parse arguments
    MODE=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev|-d)
                MODE="dev"
                shift
                ;;
            --api|-a)
                MODE="api"
                shift
                ;;
            --docker)
                MODE="docker"
                shift
                ;;
            --status|-s)
                MODE="status"
                shift
                ;;
            --stop)
                MODE="stop"
                shift
                ;;
            --health|-h)
                MODE="health"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            --port)
                API_PORT="$2"
                shift 2
                ;;
            --db)
                DB_PATH="$2"
                shift 2
                ;;
            *)
                print_error "Unknown option: $1"
                echo ""
                show_help
                exit 1
                ;;
        esac
    done

    # If no mode specified, show help
    if [ -z "$MODE" ]; then
        show_help
        exit 0
    fi

    # Execute mode
    case $MODE in
        dev)
            start_dev_mode
            ;;
        api)
            start_api_mode
            ;;
        docker)
            start_docker_mode
            ;;
        status)
            show_status
            ;;
        stop)
            stop_services
            ;;
        health)
            run_health_check
            ;;
        *)
            print_error "Invalid mode: $MODE"
            exit 1
            ;;
    esac
}

# Run main
main "$@"
