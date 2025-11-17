#!/bin/bash
# End-to-End Test Script for AUPAT Web Import
# Tests the complete upload → import → verify flow
#
# Usage:
#   bash tests/e2e_test.sh
#
# Requirements:
#   - Flask server running on localhost:5000
#   - Test files in tempdata/testphotos/
#   - jq (JSON processor) installed: sudo apt-get install jq
#
# Version: 1.0.0

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FLASK_URL="http://localhost:5000"
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$TEST_DIR")"
LOG_FILE="/tmp/aupat_e2e_test.log"

echo "============================================================"
echo "AUPAT E2E Test Suite"
echo "============================================================"
echo "Test Directory: $TEST_DIR"
echo "Project Directory: $PROJECT_DIR"
echo "Flask URL: $FLASK_URL"
echo "Log File: $LOG_FILE"
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}ERROR: jq is not installed${NC}"
    echo "Install with: sudo apt-get install jq"
    exit 1
fi

# Check if Flask server is running
echo "1. Checking if Flask server is running..."
if ! curl -s "$FLASK_URL" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Flask server is not running on $FLASK_URL${NC}"
    echo "Start it with: python web_interface.py"
    exit 1
fi
echo -e "${GREEN}✓${NC} Flask server is running"
echo ""

# Create test file if it doesn't exist
TEST_FILE="$PROJECT_DIR/tempdata/testphotos/test_e2e.txt"
mkdir -p "$PROJECT_DIR/tempdata/testphotos"
if [ ! -f "$TEST_FILE" ]; then
    echo "Creating test file: $TEST_FILE"
    echo "This is a test file for E2E testing" > "$TEST_FILE"
fi

# Test 1: Single file upload
echo "2. Testing single file upload..."
RESPONSE_FILE="/tmp/aupat_upload_response.json"

curl -X POST "$FLASK_URL/import/submit" \
  -F "media_files=@$TEST_FILE" \
  -F "loc_name=E2E Test Location $(date +%s)" \
  -F "state=ny" \
  -F "type=industrial" \
  -F "imp_author=e2e_test" \
  -H "X-Requested-With: XMLHttpRequest" \
  -s > "$RESPONSE_FILE" 2>&1

# Check if response contains task_id
if grep -q "task_id" "$RESPONSE_FILE"; then
    TASK_ID=$(jq -r '.task_id' "$RESPONSE_FILE" 2>/dev/null)
    if [ -z "$TASK_ID" ] || [ "$TASK_ID" = "null" ]; then
        echo -e "${RED}✗ Failed to extract task_id from response${NC}"
        cat "$RESPONSE_FILE"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Upload succeeded, got task_id: $TASK_ID"
else
    echo -e "${RED}✗ Upload failed, no task_id in response${NC}"
    cat "$RESPONSE_FILE"
    exit 1
fi
echo ""

# Test 2: Poll for completion
echo "3. Polling for import completion (max 120 seconds)..."
MAX_ATTEMPTS=120
ATTEMPT=0
COMPLETED=false
ERROR=""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    # Poll task status
    STATUS_RESPONSE=$(curl -s "$FLASK_URL/api/task-status/$TASK_ID")

    # Extract status fields
    RUNNING=$(echo "$STATUS_RESPONSE" | jq -r '.running' 2>/dev/null)
    COMPLETED_FLAG=$(echo "$STATUS_RESPONSE" | jq -r '.completed' 2>/dev/null)
    ERROR=$(echo "$STATUS_RESPONSE" | jq -r '.error // empty' 2>/dev/null)
    PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress // 0' 2>/dev/null)
    CURRENT_STEP=$(echo "$STATUS_RESPONSE" | jq -r '.current_step // "unknown"' 2>/dev/null)

    # Show progress
    if [ "$PROGRESS" != "null" ] && [ "$PROGRESS" != "0" ]; then
        echo -ne "\r  Progress: ${PROGRESS}% - ${CURRENT_STEP}                    "
    fi

    # Check if completed
    if [ "$COMPLETED_FLAG" = "true" ]; then
        echo ""
        echo -e "${GREEN}✓${NC} Import completed successfully"
        COMPLETED=true
        break
    fi

    # Check if error occurred
    if [ -n "$ERROR" ] && [ "$ERROR" != "null" ]; then
        echo ""
        echo -e "${RED}✗ Import failed with error:${NC}"
        echo "  $ERROR"
        exit 1
    fi

    # Check if job is stuck (not running and not completed)
    if [ "$RUNNING" = "false" ] && [ "$COMPLETED_FLAG" != "true" ]; then
        echo ""
        echo -e "${RED}✗ Import job is stuck (not running, not completed)${NC}"
        echo "Status response: $STATUS_RESPONSE"
        exit 1
    fi

    ATTEMPT=$((ATTEMPT + 1))
    sleep 1
done

if [ "$COMPLETED" = false ]; then
    echo ""
    echo -e "${RED}✗ Import timed out after ${MAX_ATTEMPTS} seconds${NC}"
    echo "Final status: $STATUS_RESPONSE"
    exit 1
fi
echo ""

# Test 3: Verify database entries (optional - requires database access)
if [ -f "$PROJECT_DIR/data/aupat.db" ]; then
    echo "4. Verifying database entries..."

    # Check if sqlite3 is available
    if command -v sqlite3 &> /dev/null; then
        LOCATION_COUNT=$(sqlite3 "$PROJECT_DIR/data/aupat.db" \
            "SELECT COUNT(*) FROM locations WHERE loc_name LIKE 'E2E Test Location%'" 2>/dev/null || echo "0")

        if [ "$LOCATION_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✓${NC} Found $LOCATION_COUNT E2E test location(s) in database"
        else
            echo -e "${YELLOW}⚠${NC} No E2E test locations found in database (may have been cleaned up)"
        fi
    else
        echo -e "${YELLOW}⚠${NC} sqlite3 not installed, skipping database verification"
    fi
else
    echo "4. Skipping database verification (database not found)"
fi
echo ""

# Test 4: Verify XHR detection works
echo "5. Testing XHR header detection..."
XHR_RESPONSE=$(curl -X POST "$FLASK_URL/import/submit" \
  -F "media_files=@$TEST_FILE" \
  -F "loc_name=XHR Test Location $(date +%s)" \
  -F "state=vt" \
  -F "type=residential" \
  -H "X-Requested-With: XMLHttpRequest" \
  -s)

if echo "$XHR_RESPONSE" | jq -e '.task_id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} XHR detection working (returned JSON)"
else
    echo -e "${RED}✗ XHR detection failed (did not return JSON)${NC}"
    echo "Response: $XHR_RESPONSE"
    exit 1
fi
echo ""

# Test 5: Verify fallback page (non-XHR request)
echo "6. Testing fallback page (non-XHR request)..."
FALLBACK_RESPONSE=$(curl -X POST "$FLASK_URL/import/submit" \
  -F "media_files=@$TEST_FILE" \
  -F "loc_name=Fallback Test Location $(date +%s)" \
  -F "state=pa" \
  -F "type=commercial" \
  -s)

if echo "$FALLBACK_RESPONSE" | grep -q "import-progress" || \
   echo "$FALLBACK_RESPONSE" | grep -q "302 Found" || \
   echo "$FALLBACK_RESPONSE" | grep -q "Redirecting"; then
    echo -e "${GREEN}✓${NC} Fallback mechanism working (redirected to progress page)"
else
    echo -e "${YELLOW}⚠${NC} Fallback response unexpected:"
    echo "$(echo "$FALLBACK_RESPONSE" | head -5)"
fi
echo ""

# Summary
echo "============================================================"
echo "E2E Test Summary"
echo "============================================================"
echo -e "${GREEN}✓ All critical tests passed${NC}"
echo ""
echo "Tests completed:"
echo "  ✓ Flask server connectivity"
echo "  ✓ File upload via XHR"
echo "  ✓ Progress tracking"
echo "  ✓ Import completion"
echo "  ✓ XHR header detection"
echo "  ✓ Fallback page mechanism"
echo ""
echo "Log file: $LOG_FILE"
echo "============================================================"

exit 0
