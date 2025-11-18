#!/bin/bash
#
# Generate App Icons for Abandoned Upstate
#
# This script generates multi-resolution app icons from the source PNG file.
# Requires: electron-icon-builder (installed via npm)
#
# Usage:
#   cd desktop
#   chmod +x generate-icons.sh
#   ./generate-icons.sh
#

set -e

echo "=================================="
echo "Abandoned Upstate Icon Generator"
echo "=================================="
echo ""

# Check if source image exists
SOURCE_IMAGE="../Abandoned Upstate.png"
if [ ! -f "$SOURCE_IMAGE" ]; then
    echo "ERROR: Source image not found: $SOURCE_IMAGE"
    echo "Please ensure 'Abandoned Upstate.png' exists in the project root."
    exit 1
fi

echo "✓ Found source image: $SOURCE_IMAGE"

# Check if electron-icon-builder is installed
if ! npm list electron-icon-builder >/dev/null 2>&1; then
    echo ""
    echo "Installing electron-icon-builder..."
    npm install --save-dev electron-icon-builder
fi

echo "✓ electron-icon-builder is installed"
echo ""

# Create resources directory if it doesn't exist
mkdir -p resources

echo "Generating icons..."
echo ""

# Generate icons for all platforms
npx electron-icon-builder \
    --input="$SOURCE_IMAGE" \
    --output=resources \
    --flatten

echo ""
echo "=================================="
echo "✓ Icon generation complete!"
echo "=================================="
echo ""
echo "Generated files:"
ls -lh resources/icon.* 2>/dev/null || echo "  (no icons generated)"
echo ""
echo "Files created:"
echo "  - resources/icon.icns (macOS)"
echo "  - resources/icon.png (Linux, 512x512)"
echo "  - resources/icon.ico (Windows)"
echo ""
echo "These icons are referenced in package.json build configuration."
echo "Run 'npm run package' to build the app with the new icons."
echo ""
