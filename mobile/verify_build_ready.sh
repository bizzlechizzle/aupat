#!/bin/bash
#
# AUPAT Mobile Build Readiness Verification Script
# Checks that all requirements are met before building
#
# Usage: ./verify_build_ready.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo "========================================="
echo "  AUPAT Mobile Build Readiness Check"
echo "========================================="
echo ""

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}[OK]${NC} $2"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $2"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}[OK]${NC} $2"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $2"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check command exists
check_command() {
    if command -v "$1" &> /dev/null; then
        VERSION=$($1 --version 2>&1 | head -n 1)
        echo -e "${GREEN}[OK]${NC} $2: $VERSION"
        return 0
    else
        echo -e "${YELLOW}[WARN]${NC} $2"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
}

echo "1. Checking Required Files..."
echo "----------------------------"
check_file "pubspec.yaml" "pubspec.yaml exists"
check_file "lib/main.dart" "main.dart exists"
check_file "android/app/build.gradle" "Android build config exists"
check_file "android/app/src/main/AndroidManifest.xml" "AndroidManifest.xml exists"
echo ""

echo "2. Checking Source Code Structure..."
echo "----------------------------"
check_dir "lib/models" "Models directory exists"
check_dir "lib/screens" "Screens directory exists"
check_dir "lib/services" "Services directory exists"
check_dir "lib/api" "API directory exists"
check_file "lib/models/location_model.dart" "Location model exists"
check_file "lib/services/database_service.dart" "Database service exists"
check_file "lib/services/gps_service.dart" "GPS service exists"
check_file "lib/services/sync_service.dart" "Sync service exists"
check_file "lib/services/camera_service.dart" "Camera service exists"
check_file "lib/api/aupat_api_client.dart" "API client exists"
echo ""

echo "3. Checking Screens..."
echo "----------------------------"
check_file "lib/screens/home_screen.dart" "Home screen exists"
check_file "lib/screens/map_screen.dart" "Map screen exists"
check_file "lib/screens/location_list_screen.dart" "List screen exists"
check_file "lib/screens/add_location_screen.dart" "Add location screen exists"
check_file "lib/screens/settings_screen.dart" "Settings screen exists"
echo ""

echo "4. Checking Tests..."
echo "----------------------------"
check_dir "test" "Test directory exists"
check_file "test/services/database_service_test.dart" "Database tests exist"
echo ""

echo "5. Checking Documentation..."
echo "----------------------------"
check_file "README.md" "README exists"
check_file "DEPLOYMENT.md" "Deployment guide exists"
check_file "IMPLEMENTATION_SUMMARY.md" "Implementation summary exists"
check_file "QUICKSTART.md" "Quick start guide exists"
check_file "WWYDD.md" "Trade-offs documentation exists"
check_file "PRODUCTION_DEPLOYMENT.md" "Production deployment guide exists"
echo ""

echo "6. Checking Build Tools (optional)..."
echo "----------------------------"
check_command "flutter" "Flutter SDK installed"
check_command "dart" "Dart SDK installed"
check_command "java" "Java JDK installed"
check_command "adb" "Android Debug Bridge installed"
echo ""

echo "7. Checking Configuration..."
echo "----------------------------"

# Check pubspec.yaml has required dependencies
if grep -q "sqflite" pubspec.yaml; then
    echo -e "${GREEN}[OK]${NC} sqflite dependency configured"
else
    echo -e "${RED}[FAIL]${NC} sqflite dependency missing"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "geolocator" pubspec.yaml; then
    echo -e "${GREEN}[OK]${NC} geolocator dependency configured"
else
    echo -e "${RED}[FAIL]${NC} geolocator dependency missing"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "image_picker" pubspec.yaml; then
    echo -e "${GREEN}[OK]${NC} image_picker dependency configured"
else
    echo -e "${RED}[FAIL]${NC} image_picker dependency missing"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "flutter_map" pubspec.yaml; then
    echo -e "${GREEN}[OK]${NC} flutter_map dependency configured"
else
    echo -e "${RED}[FAIL]${NC} flutter_map dependency missing"
    ERRORS=$((ERRORS + 1))
fi

# Check version is set
VERSION=$(grep "^version:" pubspec.yaml | cut -d' ' -f2)
if [ -n "$VERSION" ]; then
    echo -e "${GREEN}[OK]${NC} Version configured: $VERSION"
else
    echo -e "${YELLOW}[WARN]${NC} Version not set in pubspec.yaml"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

echo "8. Checking Android Configuration..."
echo "----------------------------"

# Check minimum SDK version
if grep -q "minSdkVersion 21" android/app/build.gradle; then
    echo -e "${GREEN}[OK]${NC} Minimum SDK version configured (21)"
else
    echo -e "${YELLOW}[WARN]${NC} Minimum SDK version may need verification"
    WARNINGS=$((WARNINGS + 1))
fi

# Check target SDK version
if grep -q "targetSdkVersion" android/app/build.gradle; then
    echo -e "${GREEN}[OK]${NC} Target SDK version configured"
else
    echo -e "${YELLOW}[WARN]${NC} Target SDK version not found"
    WARNINGS=$((WARNINGS + 1))
fi

# Check permissions
if grep -q "ACCESS_FINE_LOCATION" android/app/src/main/AndroidManifest.xml; then
    echo -e "${GREEN}[OK]${NC} Location permission configured"
else
    echo -e "${RED}[FAIL]${NC} Location permission missing"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "CAMERA" android/app/src/main/AndroidManifest.xml; then
    echo -e "${GREEN}[OK]${NC} Camera permission configured"
else
    echo -e "${RED}[FAIL]${NC} Camera permission missing"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "INTERNET" android/app/src/main/AndroidManifest.xml; then
    echo -e "${GREEN}[OK]${NC} Internet permission configured"
else
    echo -e "${RED}[FAIL]${NC} Internet permission missing"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Summary
echo "========================================="
echo "  Summary"
echo "========================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}All checks passed! Ready to build.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./build.sh --clean --test --release"
    echo "  2. Install APK on device: adb install build/app/outputs/flutter-apk/app-release.apk"
    echo "  3. Test all functionality"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}Build ready with $WARNINGS warnings${NC}"
    echo "Warnings can usually be ignored for development builds."
    echo ""
    echo "To build anyway:"
    echo "  ./build.sh --release"
    echo ""
    exit 0
else
    echo -e "${RED}Build NOT ready: $ERRORS errors, $WARNINGS warnings${NC}"
    echo ""
    echo "Fix the errors above before building."
    echo ""
    exit 1
fi
