# AUPATOOL v0.1.2 - Testing Strategy

## Testing Philosophy (FAANG PE)

FAANG-grade testing pyramid:

```
              /\
             /  \       E2E Tests (5%)
            /    \      - Full user workflows
           /------\     - Slow but comprehensive
          /        \
         /          \   Integration Tests (15%)
        /            \  - API + Database
       /--------------\ - Service interactions
      /                \
     /                  \ Unit Tests (80%)
    /                    \ - Functions, classes
   /______________________\ - Fast, isolated
```

**Principles:**
- KISS: Simple tests, easy to understand and maintain
- BPA: Follow pytest/Jest best practices
- BPL: Tests prevent regressions for years
- FAANG PE: Automated, comprehensive, fast feedback

---

## Unit Tests

### AUPAT Core (Python/pytest)

**Coverage Target: 80%+ for core business logic**

**Test Structure:**

```python
# tests/unit/test_immich_adapter.py
import pytest
from unittest.mock import Mock, patch
from aupat_core.adapters.immich import ImmichAdapter

class TestImmichAdapter:
    @pytest.fixture
    def adapter(self):
        return ImmichAdapter(api_url="http://localhost:2283", api_key="test")

    def test_upload_success(self, adapter):
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"id": "abc123"}
            asset_id = adapter.upload("/path/to/test.jpg")
            assert asset_id == "abc123"
            mock_post.assert_called_once()

    def test_upload_failure_retries(self, adapter):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = [ConnectionError, ConnectionError, Mock(json=lambda: {"id": "abc123"})]
            asset_id = adapter.upload("/path/to/test.jpg")
            assert asset_id == "abc123"
            assert mock_post.call_count == 3

    def test_get_thumbnail_url(self, adapter):
        url = adapter.get_thumbnail_url("abc123", size="preview")
        assert url == "http://localhost:2283/api/asset/abc123/thumbnail?size=preview"

# tests/unit/test_gps_extraction.py
from aupat_core.utils.exif import extract_gps

def test_extract_gps_valid():
    exif_data = {
        'GPSLatitude': ((42, 1), (48, 1), (51, 100)),
        'GPSLatitudeRef': 'N',
        'GPSLongitude': ((73, 1), (56, 1), (22, 100)),
        'GPSLongitudeRef': 'W'
    }
    lat, lon = extract_gps(exif_data)
    assert abs(lat - 42.8142) < 0.01
    assert abs(lon - (-73.9396)) < 0.01

def test_extract_gps_missing():
    exif_data = {}
    result = extract_gps(exif_data)
    assert result is None

def test_extract_gps_invalid_format():
    exif_data = {'GPSLatitude': 'invalid'}
    result = extract_gps(exif_data)
    assert result is None
```

**Test Categories:**

1. **API Endpoints** (tests/unit/test_api.py)
   - Valid requests return correct responses
   - Invalid requests return 400 errors
   - Authentication (future)
   - Rate limiting (future)

2. **Database Operations** (tests/unit/test_database.py)
   - CRUD operations for locations
   - Foreign key constraints enforced
   - Unique constraints work
   - Indexes improve query performance

3. **Import Pipeline** (tests/unit/test_import.py)
   - SHA256 calculation correct
   - Duplicate detection works
   - EXIF extraction (GPS, timestamps, camera)
   - Immich upload integration

4. **Adapter Interfaces** (tests/unit/test_adapters.py)
   - Immich adapter methods
   - ArchiveBox adapter methods
   - Error handling and retries

5. **Utilities** (tests/unit/test_utils.py)
   - GPS parsing from EXIF
   - Address parsing
   - File validation (image formats, sizes)

**Run Command:**
```bash
pytest tests/unit/ -v --cov=aupat_core --cov-report=html
```

**Success Criteria:**
- All tests pass
- Coverage 80%+
- Run time < 30 seconds

---

### Desktop App (JavaScript/Jest)

**Coverage Target: 70%+ for business logic (not UI components)**

**Test Structure:**

```javascript
// tests/unit/api-client.test.js
import { describe, it, expect, vi } from 'vitest';
import ApiClient from '../src/lib/api-client';

describe('ApiClient', () => {
  it('fetches locations successfully', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([{ loc_uuid: '123', loc_name: 'Test' }])
      })
    );

    const client = new ApiClient('http://localhost:5000');
    const locations = await client.getLocations();

    expect(locations).toHaveLength(1);
    expect(locations[0].loc_name).toBe('Test');
  });

  it('handles network errors gracefully', async () => {
    global.fetch = vi.fn(() => Promise.reject(new Error('Network error')));

    const client = new ApiClient('http://localhost:5000');
    await expect(client.getLocations()).rejects.toThrow('Network error');
  });
});

// tests/unit/marker-clustering.test.js
import { clusterMarkers } from '../src/lib/map-utils';

describe('clusterMarkers', () => {
  it('clusters nearby markers', () => {
    const markers = [
      { lat: 42.8142, lon: -73.9396 },
      { lat: 42.8143, lon: -73.9397 },  // Very close to first
      { lat: 43.0, lon: -74.0 }          // Far away
    ];

    const clusters = clusterMarkers(markers, zoom: 10);
    expect(clusters).toHaveLength(2);  // Two clusters: one with 2 markers, one with 1
  });
});
```

**Test Categories:**

1. **API Client** (tests/unit/api-client.test.js)
   - HTTP requests to AUPAT Core
   - Error handling (network, 404, 500)
   - Response parsing

2. **Map Utilities** (tests/unit/map-utils.test.js)
   - Marker clustering logic
   - Bounds calculation
   - Coordinate validation

3. **Data Transformations** (tests/unit/transformers.test.js)
   - Convert API responses to UI models
   - Format dates, addresses
   - Calculate derived fields

4. **IPC Handlers** (tests/unit/ipc.test.js)
   - Main process message handling
   - Filesystem operations
   - Settings persistence

**Run Command:**
```bash
npm test -- --coverage
```

**Success Criteria:**
- All tests pass
- Coverage 70%+
- Run time < 20 seconds

---

## Integration Tests

### AUPAT Core Integration (Python/pytest)

**Test full API workflows with real database (test database, not production)**

**Test Structure:**

```python
# tests/integration/test_import_pipeline.py
import pytest
from aupat_core import create_app
from aupat_core.database import get_db

@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'DATABASE': ':memory:'})
    with app.app_context():
        init_db()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_import_photos_end_to_end(client, tmp_path):
    # 1. Create test photos
    test_image = tmp_path / "test.jpg"
    create_test_image(test_image, gps=(42.8142, -73.9396))

    # 2. Create location
    response = client.post('/api/locations', json={
        'loc_name': 'Test Location',
        'loc_type': 'factory'
    })
    assert response.status_code == 201
    loc_uuid = response.json['loc_uuid']

    # 3. Import photo
    with patch('aupat_core.adapters.immich.ImmichAdapter.upload') as mock_upload:
        mock_upload.return_value = 'immich-asset-123'
        response = client.post(f'/api/import/images', json={
            'loc_uuid': loc_uuid,
            'file_paths': [str(test_image)]
        })

    assert response.status_code == 200
    assert response.json['imported'] == 1

    # 4. Verify in database
    db = get_db()
    images = db.execute('SELECT * FROM images WHERE loc_uuid = ?', (loc_uuid,)).fetchall()
    assert len(images) == 1
    assert images[0]['immich_asset_id'] == 'immich-asset-123'

    # 5. Verify GPS extracted to location
    location = db.execute('SELECT * FROM locations WHERE loc_uuid = ?', (loc_uuid,)).fetchone()
    assert abs(location['lat'] - 42.8142) < 0.01
    assert abs(location['lon'] - (-73.9396)) < 0.01

def test_archive_url_workflow(client):
    # Create location
    loc_uuid = create_test_location(client)

    # Archive URL (mock ArchiveBox)
    with patch('aupat_core.adapters.archivebox.ArchiveBoxAdapter.archive_url') as mock_archive:
        mock_archive.return_value = 'snapshot-123'
        response = client.post(f'/api/locations/{loc_uuid}/archive', json={
            'url': 'https://example.com/abandoned-factory'
        })

    assert response.status_code == 202  # Accepted (async)

    # Simulate webhook callback (archive complete)
    response = client.post('/api/webhooks/archivebox', json={
        'snapshot_id': 'snapshot-123',
        'status': 'archived',
        'extracted_media': ['/path/to/extracted1.jpg', '/path/to/extracted2.jpg']
    })

    assert response.status_code == 200

    # Verify URL in database
    db = get_db()
    urls = db.execute('SELECT * FROM urls WHERE loc_uuid = ?', (loc_uuid,)).fetchall()
    assert len(urls) == 1
    assert urls[0]['archive_status'] == 'archived'
    assert urls[0]['media_extracted'] == 2
```

**Test Scenarios:**

1. **Import Pipeline**
   - Import photos with GPS → GPS extracted to location
   - Import duplicate photos → Deduplication works
   - Import with Immich down → Graceful failure

2. **Archive Workflow**
   - Archive URL → ArchiveBox called
   - Webhook callback → Media uploaded to Immich
   - Archive with ArchiveBox down → Status remains pending

3. **Map Queries**
   - 200k locations → Returns in < 2 seconds
   - Filter by bounds → Only locations in bounds returned
   - Search query → Full-text search works

4. **Database Integrity**
   - Delete location → Cascades to images, videos, URLs
   - Foreign key violations caught
   - Unique constraint violations caught

**Run Command:**
```bash
pytest tests/integration/ -v --tb=short
```

**Success Criteria:**
- All tests pass
- Test database cleaned up after each test
- Run time < 2 minutes

---

### Desktop App Integration (Playwright)

**Test desktop app with mocked backend**

**Test Structure:**

```javascript
// tests/integration/desktop-app.spec.js
import { test, expect } from '@playwright/test';
import { _electron as electron } from 'playwright';

test.describe('Desktop App Integration', () => {
  let electronApp;
  let window;

  test.beforeAll(async () => {
    electronApp = await electron.launch({ args: ['.'] });
    window = await electronApp.firstWindow();
  });

  test.afterAll(async () => {
    await electronApp.close();
  });

  test('launches and shows map view', async () => {
    await expect(window).toHaveTitle('AUPAT');
    await expect(window.locator('#map')).toBeVisible();
  });

  test('loads locations on map', async () => {
    // Mock API response
    await window.route('**/api/map/markers', route => {
      route.fulfill({
        json: [
          { loc_uuid: '1', lat: 42.8142, lon: -73.9396, loc_name: 'Factory A' },
          { loc_uuid: '2', lat: 42.9, lon: -74.0, loc_name: 'Mill B' }
        ]
      });
    });

    await window.reload();
    await window.waitForSelector('.leaflet-marker-icon');
    const markers = await window.locator('.leaflet-marker-icon').count();
    expect(markers).toBeGreaterThan(0);
  });

  test('clicks marker and shows location details', async () => {
    // Click first marker
    await window.locator('.leaflet-marker-icon').first().click();

    // Sidebar appears
    await expect(window.locator('#location-details')).toBeVisible();
    await expect(window.locator('h2')).toContainText('Factory A');
  });

  test('imports photos via drag-and-drop', async () => {
    await window.locator('#import-button').click();

    // Simulate drag-and-drop (Electron file input)
    const fileInput = await window.locator('input[type="file"]');
    await fileInput.setInputFiles([
      'tests/fixtures/test1.jpg',
      'tests/fixtures/test2.jpg'
    ]);

    // Select location
    await window.locator('#location-select').selectOption('1');

    // Start import
    await window.locator('#import-start-button').click();

    // Wait for completion
    await expect(window.locator('.import-complete')).toBeVisible({ timeout: 30000 });
    await expect(window.locator('.import-stats')).toContainText('Imported: 2');
  });
});
```

**Test Scenarios:**

1. **App Lifecycle**
   - Launch app → Loads without errors
   - Close app → Saves settings
   - Restart app → Restores previous state

2. **Map Interaction**
   - Load 1000 markers → Clusters render
   - Zoom in → Clusters expand
   - Click marker → Details shown

3. **Gallery View**
   - Load location with 100 photos → Thumbnails load
   - Click thumbnail → Lightbox opens
   - Navigate lightbox → Previous/next work

4. **Import Flow**
   - Drag folder → Shows file count
   - Select location → Import starts
   - Shows progress → Completes successfully

**Run Command:**
```bash
npm run test:integration
```

**Success Criteria:**
- All tests pass
- Tests run on Mac and Linux
- Run time < 5 minutes

---

## Stress Tests

### Database Performance

```python
# tests/stress/test_database_performance.py
import pytest
import time
from aupat_core.database import get_db

def test_map_query_with_200k_locations(benchmark_db):
    """Test that map query returns 200k locations in < 2 seconds"""
    db = get_db()

    start = time.time()
    results = db.execute('SELECT loc_uuid, lat, lon, loc_name FROM locations WHERE lat IS NOT NULL').fetchall()
    elapsed = time.time() - start

    assert len(results) >= 200000
    assert elapsed < 2.0, f"Query took {elapsed:.2f}s, expected < 2.0s"

def test_search_query_performance(benchmark_db):
    """Test full-text search returns in < 1 second"""
    db = get_db()

    start = time.time()
    results = db.execute("SELECT * FROM locations WHERE loc_name LIKE '%factory%' LIMIT 100").fetchall()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Search took {elapsed:.2f}s, expected < 1.0s"

def test_insert_1000_images(benchmark_db):
    """Test bulk insert performance"""
    db = get_db()
    loc_uuid = 'test-location-uuid'

    images = [(f'sha256-{i}', loc_uuid, f'immich-{i}') for i in range(1000)]

    start = time.time()
    db.executemany('INSERT INTO images (img_sha256, loc_uuid, immich_asset_id) VALUES (?, ?, ?)', images)
    db.commit()
    elapsed = time.time() - start

    assert elapsed < 5.0, f"Insert took {elapsed:.2f}s, expected < 5.0s"
```

### Desktop App Performance

```javascript
// tests/stress/map-performance.spec.js
import { test, expect } from '@playwright/test';

test('map loads 200k markers with clustering', async ({ page }) => {
  // Generate 200k mock locations
  const locations = Array.from({ length: 200000 }, (_, i) => ({
    loc_uuid: `uuid-${i}`,
    lat: 42.5 + Math.random() * 2,
    lon: -74.0 + Math.random() * 2,
    loc_name: `Location ${i}`
  }));

  await page.route('**/api/map/markers', route => {
    route.fulfill({ json: locations });
  });

  const startTime = Date.now();
  await page.goto('http://localhost:5173');
  await page.waitForSelector('.leaflet-marker-icon');
  const loadTime = Date.now() - startTime;

  expect(loadTime).toBeLessThan(3000);  // Load in < 3 seconds

  // Check clusters rendered
  const clusterCount = await page.locator('.leaflet-marker-icon').count();
  expect(clusterCount).toBeGreaterThan(0);
  expect(clusterCount).toBeLessThan(10000);  // Should be clustered, not all 200k rendered
});

test('gallery loads 100 thumbnails efficiently', async ({ page }) => {
  const images = Array.from({ length: 100 }, (_, i) => ({
    img_sha256: `sha256-${i}`,
    immich_asset_id: `asset-${i}`
  }));

  await page.route('**/api/locations/*/images', route => {
    route.fulfill({ json: images });
  });

  const startTime = Date.now();
  await page.goto('http://localhost:5173/location/test-uuid');
  await page.waitForSelector('.thumbnail', { state: 'visible' });
  const loadTime = Date.now() - startTime;

  expect(loadTime).toBeLessThan(2000);  // Load in < 2 seconds

  const thumbnailCount = await page.locator('.thumbnail').count();
  expect(thumbnailCount).toBe(100);
});
```

**Run Command:**
```bash
pytest tests/stress/ -v --benchmark
npm run test:stress
```

**Success Criteria:**
- All performance targets met (defined in Phase 1 deliverables)
- No memory leaks detected
- CPU usage reasonable (< 50% average)

---

## Failure Injection

### Test Service Failures

```python
# tests/failure/test_service_failures.py
import pytest
from aupat_core import create_app

def test_immich_down_during_import(client, monkeypatch):
    """Import should fail gracefully when Immich is down"""
    def mock_upload_failure(*args, **kwargs):
        raise ConnectionError("Immich unreachable")

    monkeypatch.setattr('aupat_core.adapters.immich.ImmichAdapter.upload', mock_upload_failure)

    response = client.post('/api/import/images', json={
        'loc_uuid': 'test-uuid',
        'file_paths': ['/path/to/test.jpg']
    })

    assert response.status_code == 503  # Service Unavailable
    assert 'Immich' in response.json['error']

def test_archivebox_down_during_archive(client, monkeypatch):
    """Archive should queue for retry when ArchiveBox is down"""
    def mock_archive_failure(*args, **kwargs):
        raise ConnectionError("ArchiveBox unreachable")

    monkeypatch.setattr('aupat_core.adapters.archivebox.ArchiveBoxAdapter.archive_url', mock_archive_failure)

    response = client.post('/api/locations/test-uuid/archive', json={
        'url': 'https://example.com'
    })

    # Should accept but mark as pending
    assert response.status_code == 202
    assert response.json['status'] == 'pending'

def test_database_corruption(tmp_path):
    """App should detect and report database corruption"""
    db_path = tmp_path / "test.db"

    # Create corrupt database (truncated file)
    with open(db_path, 'wb') as f:
        f.write(b'corrupted')

    with pytest.raises(DatabaseError) as exc:
        app = create_app({'DATABASE': str(db_path)})

    assert 'corrupt' in str(exc.value).lower()
```

### Desktop App Failure Handling

```javascript
// tests/failure/app-resilience.spec.js
import { test, expect } from '@playwright/test';

test('shows error when API is unreachable', async ({ page }) => {
  await page.route('**/api/**', route => route.abort());

  await page.goto('http://localhost:5173');

  await expect(page.locator('.error-message')).toBeVisible();
  await expect(page.locator('.error-message')).toContainText('API unreachable');
});

test('handles malformed API responses', async ({ page }) => {
  await page.route('**/api/map/markers', route => {
    route.fulfill({ body: 'not json' });
  });

  await page.goto('http://localhost:5173');

  await expect(page.locator('.error-message')).toContainText('Failed to load map');
});

test('recovers from thumbnail load failures', async ({ page }) => {
  let failCount = 0;
  await page.route('**/api/asset/*/thumbnail', route => {
    if (failCount++ < 5) {
      route.abort();  // Fail first 5 requests
    } else {
      route.continue();  // Succeed after retries
    }
  });

  await page.goto('http://localhost:5173/location/test-uuid');

  // Should show placeholders for failed thumbnails
  await expect(page.locator('.thumbnail-placeholder')).toHaveCount(5);
  // Successful thumbnails should load
  await expect(page.locator('.thumbnail img')).toHaveCount(95);
});
```

**Run Command:**
```bash
pytest tests/failure/ -v
npm run test:failure
```

**Success Criteria:**
- No crashes or hangs
- Meaningful error messages shown to user
- App recovers gracefully when services restore

---

## Data Integrity Validation

### Database Consistency Checks

```python
# tests/integrity/test_database_integrity.py
def test_no_orphaned_images(db):
    """All images must reference valid locations"""
    orphans = db.execute("""
        SELECT img_sha256 FROM images
        WHERE loc_uuid NOT IN (SELECT loc_uuid FROM locations)
    """).fetchall()
    assert len(orphans) == 0, f"Found {len(orphans)} orphaned images"

def test_no_orphaned_urls(db):
    """All URLs must reference valid locations"""
    orphans = db.execute("""
        SELECT url_uuid FROM urls
        WHERE loc_uuid NOT IN (SELECT loc_uuid FROM locations)
    """).fetchall()
    assert len(orphans) == 0

def test_sha256_integrity(db):
    """Verify all images have valid SHA256 hashes"""
    images = db.execute("SELECT img_sha256, img_loc FROM images").fetchall()

    for img in images:
        if os.path.exists(img['img_loc']):
            actual_sha256 = calculate_sha256(img['img_loc'])
            assert img['img_sha256'] == actual_sha256, f"SHA256 mismatch for {img['img_loc']}"

def test_gps_coordinates_valid(db):
    """All GPS coordinates must be within valid ranges"""
    invalid = db.execute("""
        SELECT loc_uuid, lat, lon FROM locations
        WHERE lat IS NOT NULL
        AND (lat < -90 OR lat > 90 OR lon < -180 OR lon > 180)
    """).fetchall()
    assert len(invalid) == 0, f"Found {len(invalid)} locations with invalid GPS"

def test_immich_references_exist(db):
    """All immich_asset_ids should be reachable via Immich API"""
    images = db.execute("SELECT immich_asset_id FROM images WHERE immich_asset_id IS NOT NULL LIMIT 100").fetchall()

    immich_client = ImmichAdapter()
    for img in images:
        response = immich_client.get_asset_info(img['immich_asset_id'])
        assert response is not None, f"Immich asset {img['immich_asset_id']} not found"
```

**Run Command:**
```bash
pytest tests/integrity/ -v
```

**Success Criteria:**
- Zero integrity violations
- All foreign keys valid
- All SHA256 hashes match files

---

## Load Testing

### Concurrent User Simulation (Future Multi-User)

```python
# tests/load/test_concurrent_requests.py
import asyncio
import aiohttp

async def test_concurrent_map_requests():
    """Simulate 100 concurrent map requests"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_map_markers(session) for _ in range(100)]
        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

    assert all(r.status == 200 for r in results)
    assert elapsed < 10.0, f"100 concurrent requests took {elapsed:.2f}s"

async def fetch_map_markers(session):
    async with session.get('http://localhost:5000/api/map/markers') as response:
        return response
```

**Run Command:**
```bash
pytest tests/load/ -v
```

**Success Criteria (Single-User System):**
- Handle 100 concurrent requests without errors
- Response times degrade gracefully under load

---

## Long-Term Bit-Rot Prevention

### Automated Quarterly Checks

```python
# tests/maintenance/test_bit_rot.py
def test_database_file_not_corrupt(db_path):
    """SQLite integrity check"""
    conn = sqlite3.connect(db_path)
    result = conn.execute("PRAGMA integrity_check").fetchone()
    assert result[0] == 'ok', f"Database corruption detected: {result[0]}"

def test_photo_files_match_database(db):
    """Verify files exist for all database entries"""
    images = db.execute("SELECT img_sha256, img_loc FROM images").fetchall()

    missing = []
    for img in images:
        if not os.path.exists(img['img_loc']):
            missing.append(img['img_loc'])

    assert len(missing) == 0, f"Missing {len(missing)} image files"

def test_dependencies_have_security_updates():
    """Check for known vulnerabilities in dependencies"""
    # Python
    subprocess.run(['pip-audit'], check=True)

    # JavaScript
    subprocess.run(['npm audit --audit-level=high'], shell=True, check=True)
```

**Scheduled Execution:**
```bash
# Cron job: Run every 3 months
0 0 1 */3 * cd /path/to/aupat && pytest tests/maintenance/ --tb=short && mail -s "AUPAT Maintenance Report" user@example.com < report.txt
```

---

## Tools & Frameworks (BPA Compliance)

### Python Testing
- **pytest 7.4+**: Industry standard, plugin ecosystem
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking/patching
- **Faker**: Generate test data
- **factory-boy**: Test fixtures
- **pytest-benchmark**: Performance testing

### JavaScript Testing
- **Vitest**: Fast, modern Jest alternative for Vite/Svelte
- **Playwright**: E2E testing for Electron
- **@testing-library/svelte**: Component testing
- **jest-fetch-mock**: Mock API calls

### Tools
- **coverage.py**: Python coverage reports
- **c8**: JavaScript coverage reports
- **Locust**: Load testing (if needed for multi-user)
- **pip-audit**: Python security scanning
- **npm audit**: JavaScript security scanning

---

## Continuous Testing Strategy

### Pre-Commit Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
set -e

echo "Running unit tests..."
pytest tests/unit/ -q
npm test -- --run

echo "Running linters..."
black --check aupat_core/
eslint desktop-app/src/

echo "Checking types..."
mypy aupat_core/
npm run type-check

echo "All checks passed!"
```

### Daily Automated Runs (GitHub Actions or Cron)
```yaml
# .github/workflows/daily-tests.yml
name: Daily Test Suite
on:
  schedule:
    - cron: '0 6 * * *'  # 6 AM daily

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run full test suite
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Definition of Success (Testing Phase)

Phase 3 is complete when:

- [ ] Unit test coverage: 80%+ for AUPAT Core, 70%+ for Desktop App
- [ ] All integration tests pass
- [ ] Performance targets met (map, gallery, import)
- [ ] Stress tests pass (200k locations, 100 thumbnails)
- [ ] Failure injection tests show graceful degradation
- [ ] Data integrity checks pass (zero violations)
- [ ] Security scans pass (no high/critical vulnerabilities)
- [ ] Tests run successfully on Mac and Linux
- [ ] Test documentation complete (how to run, what each test does)
- [ ] CI/CD pipeline configured (optional but recommended)

---

## Long-Term Test Maintenance (BPL)

**Annual Review:**
- Update test data to reflect current dataset size
- Review performance targets (adjust if hardware upgraded)
- Update dependency versions (pytest, Playwright, etc.)
- Review and prune obsolete tests

**When Adding Features:**
- Write tests first (TDD) or immediately after
- Maintain coverage thresholds
- Update integration tests for new workflows

**When Bugs Found:**
- Write regression test that reproduces bug
- Fix bug
- Verify test now passes
- Keep test to prevent regression
