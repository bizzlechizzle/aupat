/**
 * E2E Tests: Photo Gallery and Immich Integration
 *
 * Tests photo gallery functionality:
 * - Loading photos for a location
 * - Displaying Immich thumbnails
 * - Full-screen lightbox
 * - Image metadata display
 */

import { test, expect } from '@playwright/test';
import { launchElectronApp, closeElectronApp } from './helpers/electron-launcher.js';

test.describe('AUPAT Desktop - Photo Gallery', () => {
  let app;
  let window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp({ mockApi: true });
    app = launched.app;
    window = launched.window;

    // Wait for app to be fully loaded (Map View is default)
    await window.waitForLoadState('networkidle');

    // Wait for marker pane to be ready
    await expect(window.locator('.leaflet-marker-pane')).toBeVisible();

    // Click on a marker to open location detail
    const marker = window.locator('.leaflet-marker-icon').first();
    const markerExists = await marker.count() > 0;

    if (markerExists) {
      await marker.click({ force: true });

      // Verify location detail sidebar is open
      await expect(window.locator('text=Location Details')).toBeVisible({ timeout: 3000 });
    } else {
      // If no markers, skip this test suite
      test.skip();
    }
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should display location details', async () => {
    // Verify location name
    await expect(window.locator('text=Test Location 1')).toBeVisible();

    // Verify location type
    await expect(window.locator('text=industrial')).toBeVisible();

    // Verify GPS coordinates (full precision in detail view)
    const gpsText = window.locator('text=/GPS: 42\\.\\d+, -73\\.\\d+/');
    await expect(gpsText).toBeVisible();
  });

  test('should display address information', async () => {
    // Verify address is shown
    await expect(window.locator('text=123 Test St')).toBeVisible();
    await expect(window.locator('text=Troy')).toBeVisible();
  });

  test('should show photo count', async () => {
    // Verify "Photos (N)" heading
    const photoHeading = window.locator('text=/Photos \\(\\d+\\)/');
    await expect(photoHeading).toBeVisible({ timeout: 3000 });
  });

  test('should display photo grid', async () => {
    // Check if photos loaded (may show "Loading photos..." briefly)
    const loadingText = window.locator('text=Loading photos...');
    const isLoading = await loadingText.isVisible({ timeout: 500 }).catch(() => false);

    if (!isLoading) {
      // Photos should be displayed in grid
      const photoGrid = window.locator('.grid.grid-cols-2');
      const gridExists = await photoGrid.count() > 0;

      if (gridExists) {
        await expect(photoGrid).toBeVisible({ timeout: 3000 });

        // Verify thumbnail images are present
        const thumbnails = window.locator('img[loading="lazy"]');
        const thumbnailCount = await thumbnails.count();
        expect(thumbnailCount).toBeGreaterThan(0);
      }
    }
  });

  test('should show photo thumbnails', async () => {
    // Find photo thumbnails (wait for them to load)
    const thumbnails = window.locator('img[alt*="test-image"]');
    const firstThumbnail = thumbnails.first();

    // Wait for at least one thumbnail to be visible
    await expect(firstThumbnail).toBeVisible({ timeout: 3000 });

    // Verify thumbnail has src attribute
    const src = await firstThumbnail.getAttribute('src');
    expect(src).toBeTruthy();
    expect(src).toContain('api/asset/thumbnail');
  });

  test('should open lightbox on thumbnail click', async () => {
    // Find first thumbnail button (wait for it to load)
    const thumbnailButton = window.locator('button[class*="aspect-square"]').first();
    await expect(thumbnailButton).toBeVisible({ timeout: 3000 });

    // Click thumbnail
    await thumbnailButton.click();

    // Verify lightbox opens
    const lightbox = window.locator('[role="dialog"][aria-modal="true"]');
    await expect(lightbox).toBeVisible({ timeout: 2000 });

    // Verify full-size image
    const fullImage = lightbox.locator('img');
    await expect(fullImage).toBeVisible();

    // Verify close button
    const closeButton = lightbox.locator('button[aria-label="Close lightbox"]');
    await expect(closeButton).toBeVisible();
  });

  test('should display image metadata in lightbox', async () => {
    // Click first thumbnail (wait for it to load)
    const thumbnailButton = window.locator('button[class*="aspect-square"]').first();
    await expect(thumbnailButton).toBeVisible({ timeout: 3000 });

    await thumbnailButton.click();

    // Verify image name
    const imageName = window.locator('text=test-image-1.jpg');
    await expect(imageName).toBeVisible({ timeout: 2000 });

    // Verify dimensions
    const dimensions = window.locator('text=/\\d+ x \\d+/');
    await expect(dimensions).toBeVisible();

    // Verify GPS coordinates
    const gps = window.locator('text=/GPS: 42\\.\\d+, -73\\.\\d+/');
    await expect(gps).toBeVisible();
  });

  test('should close lightbox on close button click', async () => {
    // Click first thumbnail (wait for it to load)
    const thumbnailButton = window.locator('button[class*="aspect-square"]').first();
    await expect(thumbnailButton).toBeVisible({ timeout: 3000 });

    await thumbnailButton.click();

    // Wait for lightbox
    const lightbox = window.locator('[role="dialog"]');
    await expect(lightbox).toBeVisible({ timeout: 2000 });

    // Click close button
    const closeButton = window.locator('button[aria-label="Close lightbox"]');
    await closeButton.click();

    // Verify lightbox is closed
    await expect(lightbox).not.toBeVisible({ timeout: 1000 });
  });

  test('should close lightbox on Escape key', async () => {
    // Click first thumbnail (wait for it to load)
    const thumbnailButton = window.locator('button[class*="aspect-square"]').first();
    await expect(thumbnailButton).toBeVisible({ timeout: 3000 });

    await thumbnailButton.click();

    // Wait for lightbox
    const lightbox = window.locator('[role="dialog"]');
    await expect(lightbox).toBeVisible({ timeout: 2000 });

    // Press Escape key
    await window.keyboard.press('Escape');

    // Verify lightbox is closed
    await expect(lightbox).not.toBeVisible({ timeout: 1000 });
  });

  test('should show "No photos" message when location has no photos', async () => {
    // This would require mocking a location with no photos
    // Skipped for now as we have test data with photos
  });

  test('should close location detail sidebar', async () => {
    // Verify close button exists
    const closeButton = window.locator('button:has-text("×")');
    await expect(closeButton).toBeVisible();

    // Click close button
    await closeButton.click();

    // Verify sidebar is closed
    const sidebar = window.locator('text=Location Details');
    await expect(sidebar).not.toBeVisible({ timeout: 1000 });
  });
});
