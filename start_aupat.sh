#!/usr/bin/env bash
#
# AUPAT Full Stack Startup Script
# Starts both the backend Flask server and frontend development server
#
# Usage:
#   ./start_aupat.sh
#

set -e

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Starting AUPAT Full Stack"
echo "========================================="
echo ""

# Check if port 5002 is in use
if lsof -Pi :5002 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "ERROR: Port 5002 is already in use!"
    echo ""
    echo "Please stop the service using port 5002 or change the port in:"
    echo "  - app.py (line 73)"
    echo "  - desktop/src/main/index.js (line 27)"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

# Set default database path
export DB_PATH="${DB_PATH:-$SCRIPT_DIR/data/aupat.db}"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "WARNING: Database not found at $DB_PATH"
    echo "Please run: python scripts/db_migrate_v012.py"
    echo ""
fi

# Start backend server in background
echo "Starting backend server..."
echo "Backend: http://localhost:5002"
python3 app.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
echo ""

# Give the backend a moment to start
sleep 2

# Start frontend dev server
echo "Starting frontend dev server..."
cd "$SCRIPT_DIR/desktop"
npm run dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
echo ""

echo "========================================="
echo "AUPAT is running!"
echo "========================================="
echo "Backend:  http://localhost:5002"
echo "Frontend: Check npm output above"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "Servers stopped."
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup INT TERM

# Wait for both processes
wait
