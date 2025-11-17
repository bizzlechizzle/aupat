/**
 * E2E Tests - Import Interface
 *
 * Tests the drag-and-drop file upload interface.
 */

import { test, expect } from '@playwright/test';
import { launchElectronApp, closeElectronApp } from './helpers/electron-launcher.js';

test.describe('Import Interface', () => {
  let app, window;

  test.beforeEach(async () => {
    ({ app, window } = await launchElectronApp());
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should navigate to Import view', async () => {
    await window.locator('aside button:has-text("Import")').click();
    await expect(window.locator('h2:has-text("Import Files")')).toBeVisible();
  });

  test('should show location selector', async () => {
    await window.locator('aside button:has-text("Import")').click();
    const locationSelect = window.locator('#location-select');
    await expect(locationSelect).toBeVisible();
    await expect(locationSelect).toContainText('Choose a location');
  });

  test('should show drag and drop zone', async () => {
    await window.locator('aside button:has-text("Import")').click();
    const dropZone = window.locator('div[role="button"]').filter({ hasText: 'Drag and drop files here' });
    await expect(dropZone).toBeVisible();
  });

  test('should disable upload zone when no location selected', async () => {
    await window.locator('aside button:has-text("Import")').click();
    const dropZone = window.locator('div[role="button"]').filter({ hasText: 'Select a location first' });
    await expect(dropZone).toBeVisible();
  });

  test('should enable upload zone when location selected', async () => {
    await window.locator('aside button:has-text("Import")').click();

    // Select a location
    await window.locator('#location-select').selectOption({ label: /Test Location 1/ });

    // Verify upload zone is enabled
    const dropZone = window.locator('div[role="button"]').filter({ hasText: 'Drag and drop files here' });
    await expect(dropZone).toBeVisible();
  });

  test('should display upload queue after file selection', async () => {
    await window.locator('aside button:has-text("Import")').click();

    // Select a location
    await window.locator('#location-select').selectOption({ label: /Test Location 1/ });

    // Simulate file upload via programmatic API
    await window.evaluate(async () => {
      // Create a mock file
      const mockFile = new File(['test content'], 'test-image.jpg', { type: 'image/jpeg' });

      // Trigger the file input change event
      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;

      // Dispatch change event
      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Wait for upload queue to appear
    await window.waitForSelector('h3:has-text("Upload Queue")');

    // Verify upload queue displays file
    await expect(window.locator('text=test-image.jpg')).toBeVisible();
  });

  test('should show upload progress', async () => {
    await window.locator('aside button:has-text("Import")').click();

    // Select a location
    await window.locator('#location-select').selectOption({ label: /Test Location 1/ });

    // Simulate file upload
    await window.evaluate(async () => {
      const mockFile = new File(['test content'], 'test-image.jpg', { type: 'image/jpeg' });
      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;
      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Wait for upload to complete
    await window.waitForSelector('text=Complete', { timeout: 5000 });

    // Verify success status
    await expect(window.locator('text=Complete')).toBeVisible();
  });

  test('should validate file extensions', async () => {
    await window.locator('aside button:has-text("Import")').click();

    // Select a location
    await window.locator('#location-select').selectOption({ label: /Test Location 1/ });

    // Simulate invalid file upload
    await window.evaluate(async () => {
      const mockFile = new File(['test content'], 'test.invalid', { type: 'application/octet-stream' });
      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;
      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Verify invalid file was skipped (queue should not appear)
    await window.waitForTimeout(500);
    const uploadQueue = window.locator('h3:has-text("Upload Queue")');
    await expect(uploadQueue).not.toBeVisible();
  });

  test('should support multiple file uploads', async () => {
    await window.locator('aside button:has-text("Import")').click();

    // Select a location
    await window.locator('#location-select').selectOption({ label: /Test Location 1/ });

    // Simulate multiple file upload
    await window.evaluate(async () => {
      const mockFile1 = new File(['test content 1'], 'image1.jpg', { type: 'image/jpeg' });
      const mockFile2 = new File(['test content 2'], 'image2.png', { type: 'image/png' });
      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile1);
      dataTransfer.items.add(mockFile2);
      fileInput.files = dataTransfer.files;
      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Verify both files appear in queue
    await expect(window.locator('text=image1.jpg')).toBeVisible();
    await expect(window.locator('text=image2.png')).toBeVisible();
  });

  test('should clear completed uploads', async () => {
    await window.locator('aside button:has-text("Import")').click();

    // Select a location
    await window.locator('#location-select').selectOption({ label: /Test Location 1/ });

    // Simulate file upload
    await window.evaluate(async () => {
      const mockFile = new File(['test content'], 'test-image.jpg', { type: 'image/jpeg' });
      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;
      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Wait for upload to complete
    await window.waitForSelector('text=Complete', { timeout: 5000 });

    // Click "Clear Completed"
    await window.locator('button:has-text("Clear Completed")').click();

    // Verify file is removed from queue
    await expect(window.locator('text=test-image.jpg')).not.toBeVisible();
  });

  test('should show file size in queue', async () => {
    await window.locator('aside button:has-text("Import")').click();

    // Select a location
    await window.locator('#location-select').selectOption({ label: /Test Location 1/ });

    // Simulate file upload with known size
    await window.evaluate(async () => {
      const content = 'x'.repeat(1024); // 1KB
      const mockFile = new File([content], 'test-image.jpg', { type: 'image/jpeg' });
      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(mockFile);
      fileInput.files = dataTransfer.files;
      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    });

    // Verify file size is displayed
    await expect(window.locator('text=/1(\\.|,)\\d+ KB/')).toBeVisible();
  });
});
