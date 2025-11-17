#!/usr/bin/env bash
#
# AUPAT Core API Server Startup Script
# Starts the Flask API server on port 5000
#
# Usage:
#   ./start_server.sh
#
# Environment Variables:
#   DB_PATH - Path to SQLite database (default: ./data/aupat.db)
#   PORT - Server port (default: 5000)

set -e

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set default database path if not specified
export DB_PATH="${DB_PATH:-$SCRIPT_DIR/data/aupat.db}"

# Check if database exists, offer to create it
if [ ! -f "$DB_PATH" ]; then
    echo "WARNING: Database not found at $DB_PATH"
    echo ""
    echo "To initialize the database, run:"
    echo "  python scripts/db_migrate_v012.py"
    echo ""
    read -p "Do you want to create the database now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating database..."
        python3 scripts/db_migrate_v012.py
        echo "Database created successfully!"
    else
        echo "Starting server without database (will fail on first request)"
    fi
fi

# Start server
echo "Starting AUPAT Core API v0.1.2..."
echo "Database: $DB_PATH"
echo "Server: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
