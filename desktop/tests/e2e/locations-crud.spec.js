/**
 * E2E Tests: Location CRUD Operations
 *
 * Tests location creation, editing, updating, and deletion.
 * Specifically verifies fixes for:
 * - Keyboard input in edit forms (issue #61)
 * - Location row clicking to view details
 * - Location updates persisting to database
 */

import { test, expect } from '@playwright/test';
import { launchElectronApp, closeElectronApp } from './helpers/electron-launcher.js';

test.describe('Location CRUD Operations', () => {
  let app, window;

  test.beforeEach(async () => {
    ({ app, window } = await launchElectronApp({ mockApi: true }));
    await window.waitForLoadState('networkidle');

    // Navigate to Locations view
    await window.locator('aside button:has-text("Locations")').click();
    await expect(window.locator('h2:has-text("All Locations")')).toBeVisible();
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  /**
   * FIX VERIFICATION: Location row clicking (commit 32141de)
   * Tests that clicking a location row opens the detail sidebar
   */
  test('should open location detail sidebar when row clicked', async () => {
    // Wait for locations to load
    await window.waitForSelector('tbody tr', { timeout: 5000 });

    // Click first location row
    await window.locator('tbody tr').first().click();

    // Verify LocationDetail sidebar appears
    await expect(window.locator('text=Location Details')).toBeVisible({ timeout: 3000 });

    // Verify sidebar shows location data
    await expect(window.locator('.absolute.top-0.right-0')).toBeVisible();
  });

  /**
   * FIX VERIFICATION: Edit and Delete buttons don't trigger row click
   * Tests stopPropagation on action buttons
   */
  test('should not open sidebar when Edit button clicked', async () => {
    // Wait for locations to load
    await window.waitForSelector('tbody tr', { timeout: 5000 });

    // Click Edit button (should not trigger row click)
    await window.locator('tbody tr').first().locator('button:has-text("Edit")').click();

    // Verify edit form modal opens (not detail sidebar)
    await expect(window.locator('text=Edit Location')).toBeVisible({ timeout: 3000 });

    // Verify detail sidebar does NOT appear
    await expect(window.locator('text=Location Details')).not.toBeVisible();
  });

  /**
   * FIX VERIFICATION: Keyboard input in location edit form (commit 2ac8aa8)
   * Tests that typing works in input fields after fixing global keydown handler
   */
  test('should allow typing in location edit form', async () => {
    // Wait for locations to load
    await window.waitForSelector('tbody tr', { timeout: 5000 });

    // Open edit form
    await window.locator('tbody tr').first().locator('button:has-text("Edit")').click();
    await expect(window.locator('text=Edit Location')).toBeVisible({ timeout: 3000 });

    // Get the location name input
    const nameInput = window.locator('input[type="text"]').first();

    // Clear existing value
    await nameInput.clear();

    // CRITICAL TEST: Type new value
    await nameInput.fill('Updated Location Name');

    // Verify text appears in input
    await expect(nameInput).toHaveValue('Updated Location Name');
  });

  /**
   * FIX VERIFICATION: Autofocus on location name field
   * Tests that name input receives focus when modal opens
   */
  test('should autofocus on location name field when edit form opens', async () => {
    // Wait for locations to load
    await window.waitForSelector('tbody tr', { timeout: 5000 });

    // Open edit form
    await window.locator('tbody tr').first().locator('button:has-text("Edit")').click();
    await expect(window.locator('text=Edit Location')).toBeVisible({ timeout: 3000 });

    // Wait for autofocus to apply
    await window.waitForTimeout(200);

    // Get the name input
    const nameInput = window.locator('input[type="text"]').first();

    // Verify it has focus
    const isFocused = await nameInput.evaluate(el => el === document.activeElement);
    expect(isFocused).toBe(true);
  });

  /**
   * FIX VERIFICATION: Escape key closes modal without triggering when typing
   * Tests improved Escape key handling
   */
  test('should not close modal when Escape pressed in input field', async () => {
    // Wait for locations to load
    await window.waitForSelector('tbody tr', { timeout: 5000 });

    // Open edit form
    await window.locator('tbody tr').first().locator('button:has-text("Edit")').click();
    await expect(window.locator('text=Edit Location')).toBeVisible({ timeout: 3000 });

    // Focus on input field
    const nameInput = window.locator('input[type="text"]').first();
    await nameInput.focus();

    // Press Escape while in input
    await nameInput.press('Escape');

    // Modal should remain open (Escape while typing shouldn't close)
    await expect(window.locator('text=Edit Location')).toBeVisible();
  });

  /**
   * FIX VERIFICATION: Escape key closes modal when not in input
   * Tests that Escape works from modal background
   */
  test('should close modal when Escape pressed on modal overlay', async () => {
    // Wait for locations to load
    await window.waitForSelector('tbody tr', { timeout: 5000 });

    // Open edit form
    await window.locator('tbody tr').first().locator('button:has-text("Edit")').click();
    await expect(window.locator('text=Edit Location')).toBeVisible({ timeout: 3000 });

    // Press Escape
    await window.keyboard.press('Escape');

    // Modal should close
    await expect(window.locator('text=Edit Location')).not.toBeVisible({ timeout: 1000 });
  });

  /**
   * FIX VERIFICATION: Location update persists to database
   * End-to-end test of update flow
   */
  test('should save location updates and persist changes', async () => {
    // Wait for locations to load
    await window.waitForSelector('tbody tr', { timeout: 5000 });

    // Open edit form
    await window.locator('tbody tr').first().locator('button:has-text("Edit")').click();
    await expect(window.locator('text=Edit Location')).toBeVisible({ timeout: 3000 });

    // Update location name
    const nameInput = window.locator('input[type="text"]').first();
    await nameInput.clear();
    await nameInput.fill('E2E Test Updated Name');

    // Update state
    const stateInput = window.locator('input[placeholder="State code (e.g., NY)"]');
    await stateInput.clear();
    await stateInput.fill('VT');

    // Click Save button
    await window.locator('button:has-text("Save")').click();

    // Verify modal closes
    await expect(window.locator('text=Edit Location')).not.toBeVisible({ timeout: 3000 });

    // Verify updated values appear in table
    await expect(window.locator('tbody tr').first()).toContainText('E2E Test Updated Name');
    await expect(window.locator('tbody tr').first()).toContainText('VT');
  });

  /**
   * Tests location creation flow
   */
  test('should create new location with keyboard input', async () => {
    // Click Add Location button
    await window.locator('button:has-text("Add Location")').click();
    await expect(window.locator('text=Create Location')).toBeVisible({ timeout: 3000 });

    // Fill in required fields using keyboard
    await window.locator('input[placeholder="Location name"]').fill('E2E Test New Location');
    await window.locator('input[placeholder="State code (e.g., NY)"]').fill('MA');
    await window.locator('select').first().selectOption('abandoned');

    // Click Create button
    await window.locator('button:has-text("Create")').click();

    // Verify modal closes
    await expect(window.locator('text=Create Location')).not.toBeVisible({ timeout: 3000 });

    // Verify new location appears in table
    await expect(window.locator('text=E2E Test New Location')).toBeVisible();
  });

  /**
   * Tests location deletion
   */
  test('should delete location after confirmation', async () => {
    // Wait for locations to load
    await window.waitForSelector('tbody tr', { timeout: 5000 });

    // Get first location name for verification
    const firstRow = window.locator('tbody tr').first();
    const locationName = await firstRow.locator('td').first().innerText();

    // Set up dialog handler to accept confirmation
    window.on('dialog', dialog => dialog.accept());

    // Click Delete button
    await firstRow.locator('button:has-text("Delete")').click();

    // Verify location removed from table
    await expect(window.locator(`text=${locationName}`)).not.toBeVisible({ timeout: 3000 });
  });

  /**
   * Tests location detail sidebar close button
   */
  test('should close location detail sidebar when X clicked', async () => {
    // Wait for locations to load
    await window.waitForSelector('tbody tr', { timeout: 5000 });

    // Click location row to open detail
    await window.locator('tbody tr').first().click();
    await expect(window.locator('text=Location Details')).toBeVisible({ timeout: 3000 });

    // Click close button
    await window.locator('.absolute.top-0.right-0 button').first().click();

    // Verify sidebar closes
    await expect(window.locator('text=Location Details')).not.toBeVisible({ timeout: 1000 });
  });
});
