#!/usr/bin/env bash
#
# AUPAT Update and Start Script
# Pulls latest changes, installs dependencies, and starts the app
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Updating AUPAT"
echo "========================================="
echo ""

# Pull latest changes
echo "📥 Pulling latest changes from main..."
git pull origin main
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
cd desktop
npm install
cd ..
echo ""

# Start the app
echo "🚀 Starting AUPAT..."
./start_aupat.sh
