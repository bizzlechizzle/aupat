/**
 * Electron Launcher for Playwright E2E Tests
 *
 * Provides utilities to launch Electron app with Playwright.
 * Handles app startup, API mocking, and cleanup.
 */

import { _electron as electron } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Launch Electron app for testing
 *
 * @param {object} options - Launch options
 * @param {boolean} options.mockApi - Whether to mock API responses
 * @returns {Promise<{app: ElectronApplication, window: Page}>}
 */
export async function launchElectronApp(options = {}) {
  const { mockApi = true } = options;

  // Path to built Electron app
  const electronPath = path.join(__dirname, '../../../node_modules/.bin/electron');
  const appPath = path.join(__dirname, '../../../dist-electron/main/index.js');

  // Launch Electron
  const app = await electron.launch({
    args: [appPath],
    env: {
      ...process.env,
      NODE_ENV: 'test',
      // Disable hardware acceleration for CI
      ELECTRON_DISABLE_HARDWARE_ACCELERATION: '1',
    },
  });

  // Wait for first window
  const window = await app.firstWindow();

  // Mock API if requested (BEFORE page loads)
  if (mockApi) {
    await setupApiMocks(app, window);
  }

  // Wait for app to be ready
  await window.waitForLoadState('domcontentloaded');

  return { app, window };
}

/**
 * Setup API mocks for testing
 *
 * NOTE: Electron app uses IPC (renderer -> main process) for API calls.
 * We mock IPC handlers directly in the main process using app.evaluate().
 * This is the only reliable way to mock Electron IPC in Playwright tests.
 *
 * @param {ElectronApplication} app - Electron app instance
 * @param {Page} window - Playwright page object
 */
async function setupApiMocks(app, window) {
  // Mock IPC handlers in the main process
  // This runs in the Electron main process context
  await app.evaluate(async () => {
    // Access ipcMain from the require cache (it's already loaded by the main process)
    const { ipcMain } = require('electron');
    // Mock data
    const mockLocations = [
      {
        loc_uuid: 'test-uuid-1',
        loc_name: 'Test Location 1',
        type: 'industrial',
        state: 'NY',
        lat: 42.8142,
        lon: -73.9396
      },
      {
        loc_uuid: 'test-uuid-2',
        loc_name: 'Test Location 2',
        type: 'residential',
        state: 'NY',
        lat: 42.6526,
        lon: -73.7562
      }
    ];

    const mockLocationDetails = {
      'test-uuid-1': {
        loc_uuid: 'test-uuid-1',
        loc_name: 'Test Location 1',
        type: 'industrial',
        state: 'NY',
        lat: 42.8142,
        lon: -73.9396,
        street_address: '123 Test St',
        city: 'Troy',
        zip_code: '12180',
        counts: {
          images: 2,
          videos: 0,
          documents: 0,
          urls: 0
        }
      },
      'test-uuid-2': {
        loc_uuid: 'test-uuid-2',
        loc_name: 'Test Location 2',
        type: 'residential',
        state: 'NY',
        lat: 42.6526,
        lon: -73.7562,
        street_address: '456 Main St',
        city: 'Albany',
        zip_code: '12210',
        counts: {
          images: 0,
          videos: 0,
          documents: 0,
          urls: 0
        }
      }
    };

    const mockImages = [
      {
        img_sha256: 'abc123',
        img_name: 'test-image-1.jpg',
        immich_asset_id: 'immich-123',
        img_width: 6000,
        img_height: 4000,
        img_size_bytes: 15728640,
        gps_lat: 42.8142,
        gps_lon: -73.9396
      },
      {
        img_sha256: 'def456',
        img_name: 'test-image-2.jpg',
        immich_asset_id: 'immich-456',
        img_width: 4000,
        img_height: 3000,
        img_size_bytes: 10485760,
        gps_lat: 42.8142,
        gps_lon: -73.9396
      }
    ];

    // Remove existing handlers (they will fail without API server)
    ipcMain.removeHandler('api:health');
    ipcMain.removeHandler('locations:getAll');
    ipcMain.removeHandler('locations:getById');
    ipcMain.removeHandler('map:getMarkers');
    ipcMain.removeHandler('images:getByLocation');
    ipcMain.removeHandler('import:uploadFile');

    // Register mock handlers
    ipcMain.handle('api:health', async () => ({
      success: true,
      data: {
        status: 'ok',
        version: '0.1.2',
        database: 'connected',
        location_count: 2
      }
    }));

    ipcMain.handle('locations:getAll', async () => ({
      success: true,
      data: mockLocations
    }));

    ipcMain.handle('locations:getById', async (event, id) => ({
      success: true,
      data: mockLocationDetails[id] || null
    }));

    ipcMain.handle('map:getMarkers', async () => ({
      success: true,
      data: mockLocations
    }));

    ipcMain.handle('images:getByLocation', async () => ({
      success: true,
      data: mockImages
    }));

    ipcMain.handle('import:uploadFile', async (event, fileData) => ({
      success: true,
      data: {
        uploaded: true,
        filename: fileData.filename,
        size: fileData.size
      }
    }));
  });

  // Mock Immich thumbnail URLs (these ARE HTTP requests from renderer)
  await window.route('**/api/asset/thumbnail/**', async (route) => {
    // Return a 1x1 transparent PNG
    const transparentPng = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
      'base64'
    );
    await route.fulfill({
      status: 200,
      contentType: 'image/png',
      body: transparentPng
    });
  });
}

/**
 * Close Electron app gracefully
 *
 * @param {ElectronApplication} app - Electron app instance
 */
export async function closeElectronApp(app) {
  await app.close();
}
