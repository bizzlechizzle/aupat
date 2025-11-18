/**
 * E2E Tests: Map Import File Formats
 *
 * Tests map import functionality with different file formats.
 * Specifically verifies fix for:
 * - KML/KMZ file format support (commit 909a1fc)
 */

import { test, expect } from '@playwright/test';
import { launchElectronApp, closeElectronApp } from './helpers/electron-launcher.js';

test.describe('Map Import File Formats', () => {
  let app, window;

  test.beforeEach(async () => {
    ({ app, window } = await launchElectronApp({ mockApi: true }));
    await window.waitForLoadState('networkidle');

    // Navigate to Settings
    await window.locator('aside button:has-text("Settings")').click();
    await expect(window.locator('h2:has-text("Settings")')).toBeVisible();

    // Click Import Map button (assuming it's in Settings)
    await window.locator('button:has-text("Import Map")').click();
    await expect(window.locator('text=Import Map')).toBeVisible({ timeout: 3000 });
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  /**
   * FIX VERIFICATION: KML file format acceptance (commit 909a1fc)
   * Tests that .kml files are accepted by the import dialog
   */
  test('should accept KML files for import', async () => {
    // Create mock KML file
    await window.evaluate(async () => {
      const kmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Test Locations</name>
    <Placemark>
      <name>Test Location</name>
      <Point>
        <coordinates>-73.7562,42.6526,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>`;

      const mockFile = new File([kmlContent], 'test-locations.kml', {
        type: 'application/vnd.google-earth.kml+xml'
      });

      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;

      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Verify file was accepted (no error message)
    await window.waitForTimeout(500);
    const errorMessage = window.locator('text=Unsupported file format');
    await expect(errorMessage).not.toBeVisible();

    // Verify file appears in preview or processing started
    await expect(window.locator('text=test-locations.kml')).toBeVisible({ timeout: 2000 });
  });

  /**
   * FIX VERIFICATION: KMZ file format acceptance (commit 909a1fc)
   * Tests that .kmz files are accepted by the import dialog
   */
  test('should accept KMZ files for import', async () => {
    // Create mock KMZ file (compressed KML)
    await window.evaluate(async () => {
      // KMZ is a ZIP file containing KML, so we create a mock
      const mockFile = new File(['mock kmz content'], 'test-locations.kmz', {
        type: 'application/vnd.google-earth.kmz'
      });

      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;

      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Verify file was accepted (no error message)
    await window.waitForTimeout(500);
    const errorMessage = window.locator('text=Unsupported file format');
    await expect(errorMessage).not.toBeVisible();

    // Verify file appears in preview
    await expect(window.locator('text=test-locations.kmz')).toBeVisible({ timeout: 2000 });
  });

  /**
   * Tests that CSV files are still accepted (regression test)
   */
  test('should accept CSV files for import', async () => {
    await window.evaluate(async () => {
      const csvContent = `name,state,type,lat,lon
Test Location,NY,abandoned,42.6526,-73.7562`;

      const mockFile = new File([csvContent], 'locations.csv', {
        type: 'text/csv'
      });

      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;

      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Verify file was accepted
    await window.waitForTimeout(500);
    const errorMessage = window.locator('text=Unsupported file format');
    await expect(errorMessage).not.toBeVisible();

    await expect(window.locator('text=locations.csv')).toBeVisible({ timeout: 2000 });
  });

  /**
   * Tests that GeoJSON files are still accepted (regression test)
   */
  test('should accept GeoJSON files for import', async () => {
    await window.evaluate(async () => {
      const geojsonContent = JSON.stringify({
        type: 'FeatureCollection',
        features: [{
          type: 'Feature',
          properties: {
            name: 'Test Location',
            state: 'NY',
            type: 'abandoned'
          },
          geometry: {
            type: 'Point',
            coordinates: [-73.7562, 42.6526]
          }
        }]
      });

      const mockFile = new File([geojsonContent], 'locations.geojson', {
        type: 'application/geo+json'
      });

      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;

      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Verify file was accepted
    await window.waitForTimeout(500);
    const errorMessage = window.locator('text=Unsupported file format');
    await expect(errorMessage).not.toBeVisible();

    await expect(window.locator('text=locations.geojson')).toBeVisible({ timeout: 2000 });
  });

  /**
   * Tests that .json extension works for GeoJSON
   */
  test('should accept .json files for GeoJSON import', async () => {
    await window.evaluate(async () => {
      const geojsonContent = JSON.stringify({
        type: 'FeatureCollection',
        features: []
      });

      const mockFile = new File([geojsonContent], 'locations.json', {
        type: 'application/json'
      });

      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;

      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Verify file was accepted
    await window.waitForTimeout(500);
    const errorMessage = window.locator('text=Unsupported file format');
    await expect(errorMessage).not.toBeVisible();

    await expect(window.locator('text=locations.json')).toBeVisible({ timeout: 2000 });
  });

  /**
   * Tests that unsupported formats are rejected
   */
  test('should reject unsupported file formats', async () => {
    await window.evaluate(async () => {
      const mockFile = new File(['invalid content'], 'document.pdf', {
        type: 'application/pdf'
      });

      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;

      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Verify error message appears
    await expect(window.locator('text=Unsupported file format')).toBeVisible({ timeout: 2000 });

    // Verify error lists all supported formats
    await expect(window.locator('text=.csv, .geojson, .kml, or .kmz')).toBeVisible();
  });

  /**
   * Tests that help text shows all supported formats
   */
  test('should display help text with all supported formats', async () => {
    // Verify help text mentions all formats
    const helpText = window.locator('text=/Supports.*CSV.*GeoJSON.*KML.*KMZ/i');
    await expect(helpText).toBeVisible();
  });
});
