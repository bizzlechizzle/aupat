#!/bin/bash
# AUPAT Web Interface Startup Script
# Performs health checks before starting the web interface

set -e

echo "============================================================"
echo "AUPAT Web Interface Startup"
echo "============================================================"
echo ""

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed or not in PATH"
    exit 1
fi

# Check if pip3 is available
if ! command -v pip3 &> /dev/null; then
    echo "WARNING: pip3 is not installed. You may need to install dependencies manually."
fi

# Run health check tests
echo "Running pre-flight checks..."
echo ""

if python3 scripts/test_web_interface.py; then
    echo ""
    echo "Pre-flight checks passed! Starting web interface..."
    echo ""

    # Start the web interface
    exec python3 web_interface.py "$@"
else
    echo ""
    echo "============================================================"
    echo "ERROR: Pre-flight checks failed!"
    echo "============================================================"
    echo ""
    echo "The web interface cannot start due to missing dependencies."
    echo ""
    echo "To fix this issue, run:"
    echo "  pip3 install -r requirements.txt"
    echo ""
    echo "Or run the setup script:"
    echo "  ./setup.sh"
    echo ""
    exit 1
fi
