#!/bin/bash
#
# AUPAT Mobile App Build Script
# Builds production-ready APK for Android
#
# Prerequisites:
#   - Flutter SDK 3.16.0 or higher
#   - Android SDK with API level 33
#   - Java JDK 17 or higher
#
# Usage:
#   ./build.sh [--clean] [--test] [--release]
#
# Flags:
#   --clean    Clean build artifacts before building
#   --test     Run tests before building
#   --release  Build release APK (default)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Parse arguments
CLEAN=false
RUN_TESTS=false
BUILD_TYPE="release"

for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN=true
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --release)
            BUILD_TYPE="release"
            shift
            ;;
        --debug)
            BUILD_TYPE="debug"
            shift
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Usage: ./build.sh [--clean] [--test] [--release|--debug]"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AUPAT Mobile App Build Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Verify Flutter installation
echo -e "${YELLOW}[1/7] Verifying Flutter installation...${NC}"
if ! command -v flutter &> /dev/null; then
    echo -e "${RED}ERROR: Flutter not found in PATH${NC}"
    echo "Please install Flutter SDK: https://flutter.dev/docs/get-started/install"
    exit 1
fi

FLUTTER_VERSION=$(flutter --version | head -n 1)
echo "Found: $FLUTTER_VERSION"
echo ""

# Step 2: Clean build artifacts (optional)
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}[2/7] Cleaning build artifacts...${NC}"
    flutter clean
    rm -rf build/
    echo "Clean complete"
else
    echo -e "${YELLOW}[2/7] Skipping clean (use --clean to enable)${NC}"
fi
echo ""

# Step 3: Install dependencies
echo -e "${YELLOW}[3/7] Installing dependencies...${NC}"
flutter pub get
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install dependencies${NC}"
    exit 1
fi
echo "Dependencies installed"
echo ""

# Step 4: Run code generation
echo -e "${YELLOW}[4/7] Running code generation...${NC}"
flutter pub run build_runner build --delete-conflicting-outputs
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Code generation failed${NC}"
    exit 1
fi
echo "Code generation complete"
echo ""

# Step 5: Run tests (optional)
if [ "$RUN_TESTS" = true ]; then
    echo -e "${YELLOW}[5/7] Running tests...${NC}"
    flutter test
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Tests failed${NC}"
        exit 1
    fi
    echo "All tests passed"
else
    echo -e "${YELLOW}[5/7] Skipping tests (use --test to enable)${NC}"
fi
echo ""

# Step 6: Analyze code
echo -e "${YELLOW}[6/7] Analyzing code...${NC}"
flutter analyze
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}WARNING: Code analysis found issues${NC}"
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Step 7: Build APK
echo -e "${YELLOW}[7/7] Building $BUILD_TYPE APK...${NC}"
if [ "$BUILD_TYPE" = "release" ]; then
    flutter build apk --release
else
    flutter build apk --debug
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Build failed${NC}"
    exit 1
fi
echo ""

# Success summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Build Successful${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "APK Location:"
if [ "$BUILD_TYPE" = "release" ]; then
    APK_PATH="build/app/outputs/flutter-apk/app-release.apk"
else
    APK_PATH="build/app/outputs/flutter-apk/app-debug.apk"
fi

if [ -f "$APK_PATH" ]; then
    APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
    echo "  $APK_PATH"
    echo "  Size: $APK_SIZE"
    echo ""

    # Calculate SHA256 for verification
    if command -v sha256sum &> /dev/null; then
        SHA256=$(sha256sum "$APK_PATH" | cut -d' ' -f1)
        echo "SHA256: $SHA256"
        echo ""
    fi

    echo "Next steps:"
    echo "  1. Install on device: adb install $APK_PATH"
    echo "  2. Test on device"
    echo "  3. Upload to Play Store (if signed)"
else
    echo -e "${RED}WARNING: APK not found at expected location${NC}"
fi
echo ""
