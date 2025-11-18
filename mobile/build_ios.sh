#!/bin/bash
#
# AUPAT Mobile App iOS Build Script
# Builds production-ready IPA for iOS
#
# Prerequisites:
#   - macOS with Xcode 15 or higher
#   - Flutter SDK 3.16.0 or higher
#   - CocoaPods installed
#   - Apple Developer account (for release builds)
#
# Usage:
#   ./build_ios.sh [--clean] [--test] [--release] [--simulator]
#
# Flags:
#   --clean      Clean build artifacts before building
#   --test       Run tests before building
#   --release    Build release IPA (requires signing)
#   --simulator  Build for iOS Simulator (faster, no signing needed)
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
TARGET="device"

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
        --simulator)
            TARGET="simulator"
            shift
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Usage: ./build_ios.sh [--clean] [--test] [--release|--debug] [--simulator]"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AUPAT Mobile App iOS Build Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verify we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}ERROR: iOS builds require macOS${NC}"
    echo "For development:"
    echo "  - Use iOS Simulator on macOS"
    echo "  - Or build Android APK on Linux/Windows"
    exit 1
fi

# Step 1: Verify Flutter installation
echo -e "${YELLOW}[1/8] Verifying Flutter installation...${NC}"
if ! command -v flutter &> /dev/null; then
    echo -e "${RED}ERROR: Flutter not found in PATH${NC}"
    echo "Please install Flutter SDK: https://flutter.dev/docs/get-started/install"
    exit 1
fi

FLUTTER_VERSION=$(flutter --version | head -n 1)
echo "Found: $FLUTTER_VERSION"
echo ""

# Step 2: Verify Xcode installation
echo -e "${YELLOW}[2/8] Verifying Xcode installation...${NC}"
if ! command -v xcodebuild &> /dev/null; then
    echo -e "${RED}ERROR: Xcode not found${NC}"
    echo "Please install Xcode from the App Store"
    exit 1
fi

XCODE_VERSION=$(xcodebuild -version | head -n 1)
echo "Found: $XCODE_VERSION"
echo ""

# Step 3: Clean build artifacts (optional)
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}[3/8] Cleaning build artifacts...${NC}"
    flutter clean
    rm -rf ios/Pods
    rm -rf ios/.symlinks
    rm -rf build/
    echo "Clean complete"
else
    echo -e "${YELLOW}[3/8] Skipping clean (use --clean to enable)${NC}"
fi
echo ""

# Step 4: Install dependencies
echo -e "${YELLOW}[4/8] Installing dependencies...${NC}"
flutter pub get
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install dependencies${NC}"
    exit 1
fi
echo "Dependencies installed"
echo ""

# Step 5: Install CocoaPods dependencies
echo -e "${YELLOW}[5/8] Installing CocoaPods dependencies...${NC}"
cd ios
pod install
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Pod install failed${NC}"
    exit 1
fi
cd ..
echo "CocoaPods dependencies installed"
echo ""

# Step 6: Run code generation
echo -e "${YELLOW}[6/8] Running code generation...${NC}"
flutter pub run build_runner build --delete-conflicting-outputs
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Code generation failed${NC}"
    exit 1
fi
echo "Code generation complete"
echo ""

# Step 7: Run tests (optional)
if [ "$RUN_TESTS" = true ]; then
    echo -e "${YELLOW}[7/8] Running tests...${NC}"
    flutter test
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Tests failed${NC}"
        exit 1
    fi
    echo "All tests passed"
else
    echo -e "${YELLOW}[7/8] Skipping tests (use --test to enable)${NC}"
fi
echo ""

# Step 8: Build IPA or Simulator
echo -e "${YELLOW}[8/8] Building iOS app...${NC}"

if [ "$TARGET" = "simulator" ]; then
    # Build for simulator (no signing needed)
    echo "Building for iOS Simulator..."
    flutter build ios --simulator --$BUILD_TYPE

    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Simulator build failed${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Simulator Build Successful${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "App location: build/ios/iphonesimulator/Runner.app"
    echo ""
    echo "To run on simulator:"
    echo "  1. Open Xcode"
    echo "  2. Select iOS Simulator"
    echo "  3. Run: open -a Simulator"
    echo "  4. Drag build/ios/iphonesimulator/Runner.app to simulator"
    echo ""
    echo "Or use Flutter:"
    echo "  flutter run"
    echo ""

else
    # Build for device (requires signing)
    echo "Building for iOS device..."

    if [ "$BUILD_TYPE" = "release" ]; then
        echo -e "${YELLOW}WARNING: Release build requires code signing${NC}"
        echo "Make sure you have:"
        echo "  1. Apple Developer account"
        echo "  2. Valid provisioning profile"
        echo "  3. Signing configured in Xcode"
        echo ""

        flutter build ios --release
    else
        flutter build ios --debug
    fi

    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: iOS build failed${NC}"
        echo ""
        echo "Common issues:"
        echo "  1. Code signing not configured"
        echo "  2. Provisioning profile missing/expired"
        echo "  3. Bundle ID not registered"
        echo ""
        echo "To fix:"
        echo "  1. Open ios/Runner.xcworkspace in Xcode"
        echo "  2. Select Runner target"
        echo "  3. Go to Signing & Capabilities"
        echo "  4. Select your team and provisioning profile"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Device Build Successful${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "App location: build/ios/iphoneos/Runner.app"
    echo ""
    echo "To create IPA for distribution:"
    echo "  1. Open ios/Runner.xcworkspace in Xcode"
    echo "  2. Product > Archive"
    echo "  3. Distribute App > App Store Connect / Ad Hoc / Enterprise"
    echo ""
    echo "To install on connected device:"
    echo "  1. Connect iPhone via USB"
    echo "  2. Run: flutter install"
    echo ""
fi
