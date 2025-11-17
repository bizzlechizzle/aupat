# AUPAT Desktop - Test Suite

Comprehensive testing for the AUPAT Desktop application following FAANG PE principles.

## Test Structure

```
tests/
├── unit/               # Unit tests (Fast, isolated)
│   └── api-client.test.js
├── e2e/                # End-to-end tests (Full user workflows)
│   ├── app.spec.js
│   ├── settings.spec.js
│   ├── map.spec.js
│   ├── photos.spec.js
│   └── helpers/
│       └── electron-launcher.js
└── README.md
```

## Test Pyramid

Following industry-standard test pyramid:
- Unit Tests: 80% (fast, isolated function/module tests)
- Integration Tests: 15% (service-to-service interactions)
- E2E Tests: 5% (full user workflows)

## Prerequisites

### Install Dependencies

```bash
cd desktop
npm install
```

This installs:
- Vitest: Unit testing framework
- Playwright: E2E testing framework
- Coverage tools: Code coverage reporting

### Build Application

E2E tests require a built application:

```bash
npm run build
```

This creates `dist-electron/` with the compiled Electron app.

## Running Tests

### Unit Tests

```bash
# Run all unit tests
npm test

# Watch mode (re-run on file changes)
npm run test:watch

# With coverage report
npm run test:coverage
```

**Unit test files**: `tests/unit/**/*.test.js`

**Coverage target**: 80%+ for core business logic

### E2E Tests

```bash
# Run all E2E tests (headless)
npm run test:e2e

# Run with visible browser (debugging)
npm run test:e2e:headed

# Debug mode (step through tests)
npm run test:e2e:debug
```

**E2E test files**: `tests/e2e/**/*.spec.js`

**Note**: E2E tests launch the full Electron application, so they are slower than unit tests.

### All Tests

```bash
# Run unit + E2E tests
npm run test:all
```

## Test Files

### Unit Tests

**api-client.test.js**: Tests for HTTP client retry logic
- Network error retries with exponential backoff
- Timeout error handling
- HTTP error classification (4xx vs 5xx)
- Response format handling

Coverage: 19 tests

### E2E Tests

**app.spec.js**: Main application flow
- Application startup
- Window creation
- Sidebar navigation
- View routing
- Health status indicator

**settings.spec.js**: Settings configuration
- Settings form display
- Loading default settings
- Updating API URLs
- Updating map defaults
- Form validation
- Save status feedback

**map.spec.js**: Map view and location markers
- Map initialization
- Location marker loading
- Marker clustering
- Location detail sidebar
- Locations list view

**photos.spec.js**: Photo gallery and Immich integration
- Loading photos for a location
- Displaying Immich thumbnails
- Full-screen lightbox
- Image metadata display
- Keyboard navigation (Escape to close)

## Test Configuration

### Vitest (Unit Tests)

Configuration: `vitest.config.js`

Key settings:
- Environment: Node.js
- Coverage provider: v8
- Test files: `tests/**/*.test.js`

### Playwright (E2E Tests)

Configuration: `playwright.config.js`

Key settings:
- Test directory: `tests/e2e/`
- Workers: 1 (Electron apps can't run in parallel)
- Timeout: 60s per test
- Screenshots: On failure only
- Trace: On first retry (for debugging)

## Debugging Tests

### Unit Tests

```bash
# Run specific test file
npm test tests/unit/api-client.test.js

# Run tests matching pattern
npm test -- --grep "retry"

# Show detailed output
npm test -- --reporter=verbose
```

### E2E Tests

```bash
# Run specific test file
npm run test:e2e tests/e2e/app.spec.js

# Run tests matching pattern
npm run test:e2e -- --grep "navigation"

# Debug mode (step through tests)
npm run test:e2e:debug
```

### Common Issues

**Issue**: E2E tests fail with "Electron not found"
**Solution**: Run `npm run build` to compile the Electron app first

**Issue**: E2E tests timeout
**Solution**: Increase timeout in `playwright.config.js` or use `--timeout=90000`

**Issue**: Unit tests fail with "fetch is not defined"
**Solution**: Update to Node.js 18+ which includes native fetch

**Issue**: Tests pass locally but fail in CI
**Solution**: Ensure CI runs `npm run build` before E2E tests

## Known Issues

### E2E Test IPC Mocking Limitation

**Status**: Known architectural limitation

**Issue**: E2E tests fail with `ReferenceError: require is not defined` when attempting to mock IPC handlers in Playwright's `app.evaluate()` context.

**Root cause**: Playwright's `app.evaluate()` runs in a restricted security context without access to Node.js `require()` or `import`. This prevents dynamic mocking of Electron's IPC handlers during test execution.

**Impact**: E2E tests cannot properly mock API responses via IPC, causing tests to fail when the AUPAT Core API is unavailable.

**Workarounds** (future solutions):

1. **Environment-based mocking** (recommended):
   - Modify `src/main/index.js` to check `process.env.NODE_ENV === 'test'`
   - Return mock data directly from IPC handlers in test mode
   - No Playwright mocking needed

2. **Mock HTTP server**:
   - Launch mock AUPAT Core API server during tests
   - Tests hit real IPC → real HTTP → mock server
   - Requires additional infrastructure

3. **Integration tests with real API**:
   - Replace E2E tests with integration tests
   - Require AUPAT Core API running during tests
   - Removes mocking complexity, adds dependency

**Current status**: Unit tests provide core coverage (16/18 passing). E2E tests blocked pending implementation of workaround #1.

**Reference**: See `tests/e2e/helpers/electron-launcher.js` for attempted mocking strategy.

## Test Data

### Unit Tests

Unit tests use mocks and fixtures:
- Mock fetch responses with Vitest's `vi.fn()`
- Mock timers for retry backoff testing
- No external dependencies

### E2E Tests

E2E tests use API route mocking:
- Mock responses defined in `helpers/electron-launcher.js`
- Deterministic test data (2 locations, 2 images)
- No dependency on live AUPAT Core API

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd desktop && npm install
      - run: cd desktop && npm run build
      - run: cd desktop && npm run test:all
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: test-results
          path: desktop/test-results/
```

## Performance Benchmarks

**Unit tests**: ~3-5 seconds (19 tests)
**E2E tests**: ~60-120 seconds (depends on test count)
**Total**: ~2 minutes for full suite

## Future Improvements

**Component Tests** (Svelte Testing Library):
- Test individual Svelte components in isolation
- Test component props, events, slots
- Test component state changes

**Visual Regression Tests** (Percy/Chromatic):
- Screenshot comparison for UI changes
- Detect unintended visual regressions
- Track visual history over time

**Performance Tests**:
- Test map loading with 200k markers
- Test photo gallery with 1000+ images
- Memory leak detection (24-hour run)

**Accessibility Tests** (axe-core):
- Automated accessibility checks
- WCAG 2.1 compliance
- Keyboard navigation tests

## Best Practices

1. **Keep tests fast**: Unit tests should run in seconds, not minutes
2. **Keep tests isolated**: Each test should be independent and idempotent
3. **Keep tests deterministic**: No random data, no external API calls
4. **Keep tests simple**: Easy to understand, easy to maintain
5. **Test behavior, not implementation**: Test what the code does, not how it does it

## Documentation References

- Testing strategy: `/docs/v0.1.2/05_TESTING.md`
- Verification procedures: `/docs/v0.1.2/06_VERIFICATION.md`
- Phase 3 build plan: `/docs/v0.1.2/04_BUILD_PLAN.md`

## Support

For issues or questions:
1. Check test output and error messages
2. Review this README
3. Check test configuration files
4. Review official Vitest/Playwright documentation
