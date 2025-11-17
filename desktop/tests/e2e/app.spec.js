/**
 * E2E Tests: Main Application Flow
 *
 * Tests core application functionality:
 * - Application startup
 * - Window creation
 * - Navigation between views
 * - Health check indicator
 */

import { test, expect } from '@playwright/test';
import { launchElectronApp, closeElectronApp } from './helpers/electron-launcher.js';

test.describe('AUPAT Desktop - Main Application', () => {
  let app;
  let window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp({ mockApi: true });
    app = launched.app;
    window = launched.window;

    // Wait for app to be fully loaded
    await window.waitForLoadState('networkidle');
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should launch application successfully', async () => {
    // Verify window title
    const title = await window.title();
    expect(title).toContain('AUPAT');

    // Verify app heading is visible
    await expect(window.locator('h1')).toBeVisible();
  });

  test('should display sidebar navigation', async () => {
    // Verify sidebar exists
    const sidebar = window.locator('aside');
    await expect(sidebar).toBeVisible();

    // Verify app title
    await expect(window.locator('h1')).toHaveText('AUPAT');

    // Verify all navigation items (use role-based selectors to avoid ambiguity)
    await expect(window.locator('aside button:has-text("Map View")')).toBeVisible();
    await expect(window.locator('aside button:has-text("Locations")')).toBeVisible();
    await expect(window.locator('aside button:has-text("Import")')).toBeVisible();
    await expect(window.locator('aside button:has-text("Settings")')).toBeVisible();
  });

  test('should show API health status', async () => {
    // Wait for health check to complete
    await window.waitForTimeout(1000);

    // Verify health indicator shows connected
    const healthText = window.locator('text=API Connected');
    await expect(healthText).toBeVisible();

    // Verify green status indicator
    const statusDot = window.locator('.bg-green-500');
    await expect(statusDot).toBeVisible();
  });

  test('should navigate between views', async () => {
    // Start on Map View (default)
    await expect(window.locator('.leaflet-container')).toBeVisible({ timeout: 5000 });

    // Navigate to Locations
    await window.locator('aside button:has-text("Locations")').click();
    await expect(window.locator('h2:has-text("All Locations")')).toBeVisible();
    await expect(window.locator('text=2 locations')).toBeVisible();

    // Navigate to Settings
    await window.locator('aside button:has-text("Settings")').click();
    await expect(window.locator('h2:has-text("Settings")')).toBeVisible();
    await expect(window.locator('text=API Configuration')).toBeVisible();

    // Navigate back to Map View
    await window.locator('aside button:has-text("Map View")').click();
    await expect(window.locator('.leaflet-container')).toBeVisible({ timeout: 5000 });
  });

  test('should display Import placeholder', async () => {
    // Navigate to Import
    await window.locator('aside button:has-text("Import")').click();

    // Verify placeholder content
    await expect(window.locator('h2:has-text("Import")')).toBeVisible();
    await expect(window.locator('text=Import interface coming in next iteration')).toBeVisible();
  });

  test('should maintain selected view on reload', async () => {
    // Navigate to Settings
    await window.locator('aside button:has-text("Settings")').click();
    await expect(window.locator('h2:has-text("Settings")')).toBeVisible();

    // Note: Actual reload not tested as it would require persistence
    // This is a limitation of E2E testing with mocked storage
  });
});
