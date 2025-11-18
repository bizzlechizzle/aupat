/**
 * Unit Tests: API URL Configuration
 *
 * Tests to prevent hardcoded API URLs and ensure proper settings propagation.
 * These tests verify the fix for "Cannot read properties of undefined (reading 'locations')" error
 * caused by hardcoded port 5000 in MapImportDialog.
 *
 * Run: npm test -- api-url-configuration.test.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');

describe('API URL Configuration', () => {
  const rendererPath = path.join(__dirname, '../../src/renderer');

  /**
   * Test 1: No hardcoded localhost:5000 URLs in renderer code
   *
   * Ensures no component has hardcoded the legacy port 5000
   */
  it('should not contain hardcoded localhost:5000 URLs in renderer code', () => {
    const files = getAllFiles(rendererPath, ['.js', '.svelte']);
    const violations = [];

    files.forEach(file => {
      const content = fs.readFileSync(file, 'utf8');
      const lines = content.split('\n');

      lines.forEach((line, index) => {
        // Skip comments
        if (line.trim().startsWith('//') || line.trim().startsWith('*')) {
          return;
        }

        if (line.includes('localhost:5000') && !line.includes('test') && !line.includes('example')) {
          violations.push({
            file: path.relative(rendererPath, file),
            line: index + 1,
            content: line.trim()
          });
        }
      });
    });

    if (violations.length > 0) {
      const message = 'Found hardcoded localhost:5000 URLs:\n' +
        violations.map(v => `  ${v.file}:${v.line} - ${v.content}`).join('\n');
      assert.fail(message);
    }

    assert.ok(true, 'No hardcoded localhost:5000 URLs found');
  });

  /**
   * Test 2: No hardcoded localhost:5001 URLs in renderer code
   *
   * Ensures no component has hardcoded the intermediate port 5001
   */
  it('should not contain hardcoded localhost:5001 URLs in renderer code', () => {
    const files = getAllFiles(rendererPath, ['.js', '.svelte']);
    const violations = [];

    files.forEach(file => {
      const content = fs.readFileSync(file, 'utf8');
      const lines = content.split('\n');

      lines.forEach((line, index) => {
        // Skip comments and placeholders
        if (line.trim().startsWith('//') ||
            line.trim().startsWith('*') ||
            line.includes('placeholder=')) {
          return;
        }

        if (line.includes('localhost:5001') && !line.includes('test') && !line.includes('example')) {
          violations.push({
            file: path.relative(rendererPath, file),
            line: index + 1,
            content: line.trim()
          });
        }
      });
    });

    if (violations.length > 0) {
      const message = 'Found hardcoded localhost:5001 URLs:\n' +
        violations.map(v => `  ${v.file}:${v.line} - ${v.content}`).join('\n');
      assert.fail(message);
    }

    assert.ok(true, 'No hardcoded localhost:5001 URLs found');
  });

  /**
   * Test 3: Settings store has correct default port
   *
   * Verifies settings.js uses port 5002 as default
   */
  it('should have correct default port (5002) in settings store', () => {
    const settingsPath = path.join(rendererPath, 'stores/settings.js');
    const content = fs.readFileSync(settingsPath, 'utf8');

    assert.ok(
      content.includes("apiUrl: 'http://localhost:5002'"),
      'Settings store should have default apiUrl with port 5002'
    );

    assert.ok(
      !content.includes("apiUrl: 'http://localhost:5000'") &&
      !content.includes("apiUrl: 'http://localhost:5001'"),
      'Settings store should not have legacy ports 5000 or 5001'
    );
  });

  /**
   * Test 4: MapImportDialog uses dynamic API URL
   *
   * Ensures MapImportDialog imports settings store and uses dynamic URL
   */
  it('should use settings store in MapImportDialog', () => {
    const dialogPath = path.join(rendererPath, 'lib/MapImportDialog.svelte');
    const content = fs.readFileSync(dialogPath, 'utf8');

    // Should import settings store
    assert.ok(
      content.includes("import { settings } from '../stores/settings.js'") ||
      content.includes('import { settings } from "../stores/settings.js"'),
      'MapImportDialog should import settings store'
    );

    // Should load settings on mount
    assert.ok(
      content.includes('settings.load()'),
      'MapImportDialog should load settings'
    );

    // Should subscribe to settings
    assert.ok(
      content.includes('settings.subscribe'),
      'MapImportDialog should subscribe to settings'
    );

    // Should use dynamic apiUrl variable
    assert.ok(
      content.includes('${apiUrl}'),
      'MapImportDialog should use template literal with apiUrl variable'
    );

    // Should NOT have hardcoded localhost:5000
    const lines = content.split('\n');
    lines.forEach((line, index) => {
      if (line.trim().startsWith('//') || line.trim().startsWith('*')) {
        return;
      }
      assert.ok(
        !line.includes('localhost:5000'),
        `Line ${index + 1} should not contain hardcoded localhost:5000: ${line.trim()}`
      );
    });
  });

  /**
   * Test 5: Settings placeholder shows correct port
   *
   * Ensures Settings UI displays port 5002 as example
   */
  it('should have correct placeholder (5002) in Settings UI', () => {
    const settingsUIPath = path.join(rendererPath, 'lib/Settings.svelte');
    const content = fs.readFileSync(settingsUIPath, 'utf8');

    assert.ok(
      content.includes('placeholder="http://localhost:5002"'),
      'Settings UI should show port 5002 in placeholder'
    );
  });

  /**
   * Test 6: All fetch() calls use variables not hardcoded URLs
   *
   * Ensures fetch() calls use configuration, not hardcoded strings
   */
  it('should use variable URLs in fetch() calls', () => {
    const files = getAllFiles(rendererPath, ['.js', '.svelte']);
    const violations = [];

    files.forEach(file => {
      const content = fs.readFileSync(file, 'utf8');
      const lines = content.split('\n');

      lines.forEach((line, index) => {
        if (line.includes('fetch(') &&
            (line.includes('http://localhost:5000') || line.includes('http://localhost:5001'))) {
          violations.push({
            file: path.relative(rendererPath, file),
            line: index + 1,
            content: line.trim()
          });
        }
      });
    });

    if (violations.length > 0) {
      const message = 'Found fetch() calls with hardcoded URLs:\n' +
        violations.map(v => `  ${v.file}:${v.line} - ${v.content}`).join('\n');
      assert.fail(message);
    }

    assert.ok(true, 'All fetch() calls use variable URLs');
  });

  /**
   * Test 7: Regression - MapImportDialog error scenario
   *
   * Simulates the original bug scenario where hardcoded URLs cause errors
   */
  it('should prevent MapImportDialog connection errors from hardcoded URLs', () => {
    const dialogPath = path.join(rendererPath, 'lib/MapImportDialog.svelte');
    const content = fs.readFileSync(dialogPath, 'utf8');

    // Verify all three critical fetch endpoints use dynamic URL
    const endpoints = [
      '/api/maps/parse',
      '/api/maps/check-duplicates',
      '/api/maps/import'
    ];

    endpoints.forEach(endpoint => {
      // Should use template literal with apiUrl
      const pattern = new RegExp(`\\\${apiUrl}${endpoint.replace(/\//g, '\\/')}`);
      assert.ok(
        pattern.test(content),
        `Endpoint ${endpoint} should use \${apiUrl} template literal`
      );

      // Should NOT use hardcoded localhost:5000
      const hardcodedPattern = new RegExp(`http://localhost:5000${endpoint.replace(/\//g, '\\/')}`);
      assert.ok(
        !hardcodedPattern.test(content),
        `Endpoint ${endpoint} should NOT use hardcoded localhost:5000`
      );
    });
  });

  /**
   * Test 8: Configuration consistency
   *
   * Ensures all default configurations use the same port
   */
  it('should have consistent port configuration across all defaults', () => {
    const settingsPath = path.join(rendererPath, 'stores/settings.js');
    const mainIndexPath = path.join(__dirname, '../../src/main/index.js');

    const settingsContent = fs.readFileSync(settingsPath, 'utf8');
    const mainContent = fs.readFileSync(mainIndexPath, 'utf8');

    // Extract port from settings store default
    const settingsMatch = settingsContent.match(/apiUrl:\s*'http:\/\/localhost:(\d+)'/);
    assert.ok(settingsMatch, 'Should find apiUrl in settings store');
    const settingsPort = settingsMatch[1];

    // Extract port from main process default
    const mainMatch = mainContent.match(/apiUrl:\s*'http:\/\/localhost:(\d+)'/);
    assert.ok(mainMatch, 'Should find apiUrl in main process');
    const mainPort = mainMatch[1];

    assert.strictEqual(
      settingsPort,
      mainPort,
      `Settings store port (${settingsPort}) should match main process port (${mainPort})`
    );

    assert.strictEqual(
      settingsPort,
      '5002',
      'Default port should be 5002'
    );
  });
});

/**
 * Helper: Recursively get all files with specific extensions
 */
function getAllFiles(dir, extensions, fileList = []) {
  if (!fs.existsSync(dir)) {
    return fileList;
  }

  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      // Skip node_modules and test directories
      if (!file.startsWith('.') && file !== 'node_modules' && file !== 'tests') {
        getAllFiles(filePath, extensions, fileList);
      }
    } else {
      const ext = path.extname(file);
      if (extensions.includes(ext)) {
        fileList.push(filePath);
      }
    }
  });

  return fileList;
}
