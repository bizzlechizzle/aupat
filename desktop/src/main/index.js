/**
 * AUPAT Desktop - Main Process
 *
 * Electron main process entry point.
 * Handles window creation, IPC communication, and system-level operations.
 *
 * Security:
 * - contextIsolation: true
 * - nodeIntegration: false
 * - sandbox: true
 * - All IPC communication via preload script
 */

import { app, BrowserWindow, ipcMain, shell } from 'electron';
import { join } from 'path';
import log from 'electron-log';
import Store from 'electron-store';
import { createAPIClient } from './api-client.js';

// Configure logging
log.transports.file.level = 'info';
log.info('AUPAT Desktop starting...');

// Initialize settings store
const store = new Store({
  defaults: {
    apiUrl: 'http://localhost:5001',
    immichUrl: 'http://localhost:2283',
    archiveboxUrl: 'http://localhost:8001',
    mapCenter: { lat: 42.6526, lng: -73.7562 }, // Albany, NY
    mapZoom: 10
  }
});

// Initialize API client
const api = createAPIClient(store.get('apiUrl'));

let mainWindow;

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.on('ready-to-show', () => {
    mainWindow.show();
    log.info('Main window ready');
  });

  mainWindow.webContents.setWindowOpenHandler((details) => {
    // Open external links in default browser
    shell.openExternal(details.url);
    return { action: 'deny' };
  });

  // Load the remote URL for development or the local html file for production
  if (!app.isPackaged && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL']);
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'));
  }
}

// IPC Handlers

/**
 * Input validation helpers
 */
function validateRequired(value, name) {
  if (value === null || value === undefined || value === '') {
    throw new Error(`${name} is required`);
  }
}

function validateString(value, name) {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`${name} must be a non-empty string`);
  }
}

function validateNumber(value, name, options = {}) {
  if (typeof value !== 'number' || isNaN(value)) {
    throw new Error(`${name} must be a number`);
  }
  if (options.min !== undefined && value < options.min) {
    throw new Error(`${name} must be >= ${options.min}`);
  }
  if (options.max !== undefined && value > options.max) {
    throw new Error(`${name} must be <= ${options.max}`);
  }
}

/**
 * Sanitize error message for renderer
 */
function sanitizeError(error) {
  // Only send error message, not stack trace or internal details
  if (typeof error === 'string') {
    return error;
  }
  return error.message || 'An unknown error occurred';
}

/**
 * Settings handlers
 */
ipcMain.handle('settings:get', async () => {
  try {
    log.info('Getting all settings');
    const settings = store.store;
    return { success: true, data: settings };
  } catch (error) {
    log.error('Failed to get settings:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('settings:set', async (event, key, value) => {
  try {
    validateRequired(key, 'key');
    validateString(key, 'key');
    validateRequired(value, 'value');

    log.info(`Setting ${key} = ${JSON.stringify(value)}`);
    store.set(key, value);

    // Update API client if apiUrl changed
    if (key === 'apiUrl') {
      api.setBaseUrl(value);
    }

    return { success: true, data: true };
  } catch (error) {
    log.error(`Failed to set ${key}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * Locations API handlers
 */
ipcMain.handle('locations:getAll', async () => {
  try {
    log.info('Fetching all locations');
    const locations = await api.get('/api/locations');
    return { success: true, data: locations };
  } catch (error) {
    log.error('Failed to fetch locations:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('locations:getById', async (event, id) => {
  try {
    validateRequired(id, 'id');
    validateString(id, 'id');

    log.info(`Fetching location ${id}`);
    const location = await api.get(`/api/locations/${id}`);
    return { success: true, data: location };
  } catch (error) {
    log.error(`Failed to fetch location ${id}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('locations:create', async (event, locationData) => {
  try {
    validateRequired(locationData, 'locationData');

    log.info('Creating new location');
    const location = await api.post('/api/locations', locationData);
    return { success: true, data: location };
  } catch (error) {
    log.error('Failed to create location:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('locations:update', async (event, id, locationData) => {
  try {
    validateRequired(id, 'id');
    validateString(id, 'id');
    validateRequired(locationData, 'locationData');

    log.info(`Updating location ${id}`);
    const location = await api.put(`/api/locations/${id}`, locationData);
    return { success: true, data: location };
  } catch (error) {
    log.error(`Failed to update location ${id}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('locations:delete', async (event, id) => {
  try {
    validateRequired(id, 'id');
    validateString(id, 'id');

    log.info(`Deleting location ${id}`);
    await api.delete(`/api/locations/${id}`);
    return { success: true };
  } catch (error) {
    log.error(`Failed to delete location ${id}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * Map markers API handler
 */
ipcMain.handle('map:getMarkers', async () => {
  try {
    log.info('Fetching map markers');
    const markers = await api.get('/api/map/markers');
    return { success: true, data: markers };
  } catch (error) {
    log.error('Failed to fetch map markers:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * Images API handlers
 */
ipcMain.handle('images:getByLocation', async (event, locUuid, limit = 100, offset = 0) => {
  try {
    validateRequired(locUuid, 'locUuid');
    validateString(locUuid, 'locUuid');
    validateNumber(limit, 'limit', { min: 1, max: 1000 });
    validateNumber(offset, 'offset', { min: 0 });

    log.info(`Fetching images for location ${locUuid} (limit=${limit}, offset=${offset})`);
    const images = await api.get(`/api/locations/${locUuid}/images?limit=${limit}&offset=${offset}`);
    return { success: true, data: images };
  } catch (error) {
    log.error(`Failed to fetch images for location ${locUuid}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('images:getThumbnailUrl', async (event, assetId) => {
  try {
    validateRequired(assetId, 'assetId');
    validateString(assetId, 'assetId');

    const immichUrl = store.get('immichUrl');
    if (!immichUrl) {
      throw new Error('Immich URL not configured in settings');
    }

    return `${immichUrl}/api/asset/thumbnail/${assetId}?size=preview`;
  } catch (error) {
    log.error(`Failed to generate thumbnail URL for ${assetId}:`, error);
    throw error; // Re-throw to maintain contract (returns string or throws)
  }
});

ipcMain.handle('images:getOriginalUrl', async (event, assetId) => {
  try {
    validateRequired(assetId, 'assetId');
    validateString(assetId, 'assetId');

    const immichUrl = store.get('immichUrl');
    if (!immichUrl) {
      throw new Error('Immich URL not configured in settings');
    }

    return `${immichUrl}/api/asset/file/${assetId}`;
  } catch (error) {
    log.error(`Failed to generate original URL for ${assetId}:`, error);
    throw error; // Re-throw to maintain contract (returns string or throws)
  }
});

/**
 * Health check handler
 */
ipcMain.handle('api:health', async () => {
  try {
    const health = await api.get('/api/health');
    return { success: true, data: health };
  } catch (error) {
    log.error('Health check failed:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

// App lifecycle

app.whenReady().then(() => {
  // Set app user model id for Windows
  app.setAppUserModelId('com.aupat.desktop');

  createWindow();

  app.on('activate', function () {
    // On macOS re-create window when dock icon is clicked
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
