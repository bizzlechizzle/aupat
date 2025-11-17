/**
 * E2E Tests: Settings Configuration
 *
 * Tests settings page functionality:
 * - Loading settings
 * - Updating API URLs
 * - Saving settings
 * - Form validation
 */

import { test, expect } from '@playwright/test';
import { launchElectronApp, closeElectronApp } from './helpers/electron-launcher.js';

test.describe('AUPAT Desktop - Settings', () => {
  let app;
  let window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp({ mockApi: true });
    app = launched.app;
    window = launched.window;

    // Wait for app to be fully loaded
    await window.waitForLoadState('networkidle');

    // Navigate to Settings
    await window.locator('text=Settings').click();
    await expect(window.locator('h2:has-text("Settings")')).toBeVisible();
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should display settings form', async () => {
    // Verify API Configuration section
    await expect(window.locator('text=API Configuration')).toBeVisible();

    // Verify all input fields exist
    await expect(window.locator('#apiUrl')).toBeVisible();
    await expect(window.locator('#immichUrl')).toBeVisible();
    await expect(window.locator('#archiveboxUrl')).toBeVisible();

    // Verify Map Defaults section
    await expect(window.locator('text=Map Defaults')).toBeVisible();
    await expect(window.locator('#mapLat')).toBeVisible();
    await expect(window.locator('#mapLng')).toBeVisible();
    await expect(window.locator('#mapZoom')).toBeVisible();

    // Verify Save button
    await expect(window.locator('button:has-text("Save Settings")')).toBeVisible();
  });

  test('should load default settings', async () => {
    // Verify default API URLs are populated
    const apiUrlInput = window.locator('#apiUrl');
    await expect(apiUrlInput).toHaveValue('http://localhost:5001');

    const immichUrlInput = window.locator('#immichUrl');
    await expect(immichUrlInput).toHaveValue('http://localhost:2283');

    const archiveboxUrlInput = window.locator('#archiveboxUrl');
    await expect(archiveboxUrlInput).toHaveValue('http://localhost:8001');

    // Verify default map center (Albany, NY)
    const mapLatInput = window.locator('#mapLat');
    const latValue = await mapLatInput.inputValue();
    expect(parseFloat(latValue)).toBeCloseTo(42.6526, 2);

    const mapLngInput = window.locator('#mapLng');
    const lngValue = await mapLngInput.inputValue();
    expect(parseFloat(lngValue)).toBeCloseTo(-73.7562, 2);

    // Verify default zoom
    const mapZoomInput = window.locator('#mapZoom');
    await expect(mapZoomInput).toHaveValue('10');
  });

  test('should update API URL setting', async () => {
    // Change AUPAT Core API URL
    const apiUrlInput = window.locator('#apiUrl');
    await apiUrlInput.fill('http://192.168.1.100:5001');

    // Click Save
    await window.locator('button:has-text("Save Settings")').click();

    // Verify success message
    await expect(window.locator('text=Settings saved successfully')).toBeVisible({ timeout: 3000 });

    // Verify value persists
    await expect(apiUrlInput).toHaveValue('http://192.168.1.100:5001');
  });

  test('should update map defaults', async () => {
    // Change map center to NYC
    await window.locator('#mapLat').fill('40.7128');
    await window.locator('#mapLng').fill('-74.0060');
    await window.locator('#mapZoom').fill('12');

    // Click Save
    await window.locator('button:has-text("Save Settings")').click();

    // Verify success message
    await expect(window.locator('text=Settings saved successfully')).toBeVisible({ timeout: 3000 });
  });

  test('should validate URL format', async () => {
    // Try to enter invalid URL
    const apiUrlInput = window.locator('#apiUrl');
    await apiUrlInput.fill('not-a-valid-url');

    // Verify input type is URL (browser validation)
    const inputType = await apiUrlInput.getAttribute('type');
    expect(inputType).toBe('url');
  });

  test('should validate zoom level range', async () => {
    const zoomInput = window.locator('#mapZoom');

    // Verify min/max attributes
    const min = await zoomInput.getAttribute('min');
    const max = await zoomInput.getAttribute('max');
    expect(min).toBe('1');
    expect(max).toBe('18');
  });

  test('should show saving status', async () => {
    // Click Save
    await window.locator('button:has-text("Save Settings")').click();

    // Verify "Saving..." message appears briefly
    // Note: May be too fast to catch, so we allow it to be skipped
    const savingText = window.locator('text=Saving...');
    const isVisible = await savingText.isVisible({ timeout: 500 }).catch(() => false);

    // Either "Saving..." was visible or we went straight to "Settings saved successfully"
    if (!isVisible) {
      await expect(window.locator('text=Settings saved successfully')).toBeVisible({ timeout: 3000 });
    }
  });

  test('should clear success message after delay', async () => {
    // Click Save
    await window.locator('button:has-text("Save Settings")').click();

    // Verify success message appears
    const successMessage = window.locator('text=Settings saved successfully');
    await expect(successMessage).toBeVisible({ timeout: 3000 });

    // Wait for message to disappear (2 second timeout in code)
    await expect(successMessage).not.toBeVisible({ timeout: 5000 });
  });
});
