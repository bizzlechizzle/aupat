# AUPAT Testing Guide

This directory contains comprehensive tests for the AUPAT import engine.

## Test Categories

### Unit Tests (`test_validation.py`)
Tests individual validation functions in isolation.

**Run with**:
```bash
cd /home/user/aupat
pytest tests/test_validation.py -v
```

**Coverage**:
- Location name validation
- State code validation
- Location type validation
- File size validation
- Filename validation
- Author name validation
- URL validation
- Complete form data validation

**Expected output**: All tests should pass

---

### End-to-End Tests (`e2e_test.sh`)
Tests complete upload → import → verification flow through web interface.

**Prerequisites**:
1. Flask server must be running:
   ```bash
   python web_interface.py
   ```

2. jq must be installed:
   ```bash
   sudo apt-get install jq  # Ubuntu/Debian
   brew install jq           # macOS
   ```

**Run with**:
```bash
bash tests/e2e_test.sh
```

**Tests performed**:
1. Flask server connectivity
2. Single file upload via XHR
3. Progress tracking and polling
4. Import completion detection
5. XHR header detection
6. Fallback page mechanism (non-XHR)

**Expected output**: All tests pass with green checkmarks

---

## Installing Test Dependencies

```bash
cd /home/user/aupat

# Install pytest and coverage tools
pip install pytest pytest-cov

# For E2E tests
sudo apt-get install jq  # Ubuntu/Debian
```

---

## Running All Tests

### Quick Test (Unit Tests Only)
```bash
pytest tests/test_validation.py -v
```

### Full Test Suite (Unit + E2E)
```bash
# Terminal 1: Start Flask server
python web_interface.py

# Terminal 2: Run tests
pytest tests/test_validation.py -v && bash tests/e2e_test.sh
```

---

## Test Coverage

To see code coverage:

```bash
pytest tests/test_validation.py --cov=scripts/validation --cov-report=html
```

Open `htmlcov/index.html` in browser to see detailed coverage report.

**Target**: 80%+ coverage for validation module

---

## Interpreting Test Results

### Unit Tests

**PASS** - All green:
```
tests/test_validation.py::TestLocationNameValidation::test_valid_location_names PASSED
tests/test_validation.py::TestLocationNameValidation::test_empty_location_name PASSED
...
=== 30 passed in 0.25s ===
```

**FAIL** - Red with error details:
```
tests/test_validation.py::TestLocationNameValidation::test_valid_location_names FAILED
E   AssertionError: ...
```

### E2E Tests

**PASS** - All green checkmarks:
```
============================================================
E2E Test Summary
============================================================
✓ All critical tests passed
```

**FAIL** - Red X with error message:
```
✗ Upload failed, no task_id in response
{"error": "..."}
```

---

## Troubleshooting

### Unit Tests Fail

**Problem**: `ModuleNotFoundError: No module named 'validation'`

**Solution**: Make sure scripts directory is in Python path:
```bash
export PYTHONPATH="/home/user/aupat/scripts:$PYTHONPATH"
pytest tests/test_validation.py -v
```

---

### E2E Tests Fail

**Problem**: `ERROR: Flask server is not running`

**Solution**: Start Flask in another terminal:
```bash
python web_interface.py
```

**Problem**: `ERROR: jq is not installed`

**Solution**: Install jq:
```bash
sudo apt-get install jq
```

**Problem**: `✗ Upload failed, no task_id in response`

**Solution**: Check Flask logs for errors:
```bash
tail -50 logs/aupat.log
```

---

## Adding New Tests

### Unit Test Template

```python
# tests/test_mymodule.py
import pytest
from scripts.mymodule import my_function

class TestMyFunction:
    """Test my_function behavior."""

    def test_valid_input(self):
        """Valid input should work."""
        result = my_function("valid input")
        assert result == "expected output"

    def test_invalid_input(self):
        """Invalid input should raise error."""
        with pytest.raises(ValueError, match="error message"):
            my_function("invalid input")
```

### E2E Test Template

```bash
# tests/my_e2e_test.sh
#!/bin/bash
set -e

echo "Testing my feature..."

# Make API request
curl -X POST http://localhost:5000/my-endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}' \
  -s > /tmp/response.json

# Verify response
if grep -q "success" /tmp/response.json; then
    echo "✓ Test passed"
else
    echo "✗ Test failed"
    exit 1
fi
```

---

## Continuous Integration (Future)

When ready to add CI/CD:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt pytest
      - run: pytest tests/test_validation.py -v
```

---

## Test Maintenance

**When to update tests**:
- Adding new validation rules → Update `test_validation.py`
- Changing API endpoints → Update `e2e_test.sh`
- Adding new features → Add corresponding tests

**Test hygiene**:
- Tests should be fast (< 1 second per test)
- Tests should be independent (can run in any order)
- Tests should clean up after themselves (no leftover files/data)

---

## Questions?

See main documentation in `../claude.md` or check logs in `../logs/aupat.log`.
