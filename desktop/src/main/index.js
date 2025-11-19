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

import { app, BrowserWindow, ipcMain, shell, dialog } from 'electron';
import { join } from 'path';
import log from 'electron-log';
import Store from 'electron-store';
import { createAPIClient } from './api-client.js';
import { BrowserManager } from './browser-manager.js';
import { initAutoUpdater, registerUpdateHandlers } from './updater.js';

// Configure logging
log.transports.file.level = 'info';
log.info('Abandoned Upstate starting...');

// Initialize settings store
const store = new Store({
  defaults: {
    apiUrl: 'http://127.0.0.1:5002',
    immichUrl: 'http://127.0.0.1:2283',
    archiveboxUrl: 'http://127.0.0.1:8001',
    mapCenter: { lat: 42.6526, lng: -73.7562 }, // Albany, NY
    mapZoom: 10
  }
});

// Migrate settings from old AUPAT Desktop to Abandoned Upstate (v0.2.0)
try {
  const oldStore = new Store({ name: 'aupat-desktop' });
  if (oldStore.size > 0 && store.size <= Object.keys(store.defaults).length) {
    log.info('Migrating settings from AUPAT Desktop to Abandoned Upstate...');
    // Copy all old settings to new store
    for (const [key, value] of Object.entries(oldStore.store)) {
      if (!store.has(key)) {
        store.set(key, value);
      }
    }
    log.info('Settings migration complete');
  }
} catch (error) {
  log.warn('Settings migration skipped:', error.message);
}

// Migrate settings from old ports to current version (v0.1.2+)
// Fixes: "Cannot read properties of undefined (reading 'locations')" error
// when stored config has outdated port from previous versions
const currentApiUrl = store.get('apiUrl');
const CURRENT_API_PORT = '5002'; // v0.1.2+ uses port 5002
const LEGACY_PORTS = ['5000', '5001']; // v0.1.0-v0.1.1 used these ports

if (currentApiUrl && currentApiUrl.includes('localhost')) {
  const urlMatch = currentApiUrl.match(/localhost:(\d+)/);
  if (urlMatch) {
    const storedPort = urlMatch[1];
    if (LEGACY_PORTS.includes(storedPort)) {
      const migratedUrl = `http://127.0.0.1:${CURRENT_API_PORT}`;
      log.info(`Auto-migrating API URL: port ${storedPort} → ${CURRENT_API_PORT}`);
      store.set('apiUrl', migratedUrl);
    }
  }
}

// Migrate localhost to 127.0.0.1 to fix IPv6 connection issues
// Node.js fetch() resolves localhost to IPv6 (::1) first, but Flask only listens on IPv4
['apiUrl', 'immichUrl', 'archiveboxUrl'].forEach(key => {
  const url = store.get(key);
  if (url && url.includes('localhost')) {
    const migratedUrl = url.replace('localhost', '127.0.0.1');
    log.info(`Migrating ${key}: localhost → 127.0.0.1`);
    store.set(key, migratedUrl);
  }
});

// Initialize API client
const api = createAPIClient(store.get('apiUrl'));

let mainWindow;
let browserManager;

/**
 * Clear application cache on startup to prevent stale cached code issues
 * Especially important after port migrations or code updates
 */
async function clearAppCache() {
  const { session } = require('electron');
  try {
    await session.defaultSession.clearCache();
    log.info('Cleared application cache on startup');
  } catch (error) {
    log.warn('Failed to clear cache on startup:', error);
  }
}

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    title: 'Abandoned Upstate',
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
    const response = await api.get('/api/locations?limit=1000');
    // API now returns paginated response: { locations, total, limit, offset }
    const locations = response.locations || response;
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
    log.info(`[IPC] Update request received for location ${id}`);
    log.debug(`[IPC] Update data:`, JSON.stringify(locationData, null, 2));

    validateRequired(id, 'id');
    validateString(id, 'id');
    validateRequired(locationData, 'locationData');

    log.info(`[IPC] Validation passed, sending PUT request to API`);
    const location = await api.put(`/api/locations/${id}`, locationData);
    log.info(`[IPC] Update successful for location ${id}`);
    log.debug(`[IPC] Updated location data:`, JSON.stringify(location, null, 2));

    return { success: true, data: location };
  } catch (error) {
    log.error(`[IPC] Failed to update location ${id}:`, error.message);
    log.error(`[IPC] Error stack:`, error.stack);
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

ipcMain.handle('locations:autocomplete', async (event, field, options = {}) => {
  try {
    validateRequired(field, 'field');
    validateString(field, 'field');

    const params = new URLSearchParams();
    if (options.type) params.append('type', options.type);
    if (options.limit) params.append('limit', options.limit.toString());

    const queryString = params.toString();
    const url = `/api/locations/autocomplete/${field}${queryString ? '?' + queryString : ''}`;

    log.info(`Fetching autocomplete for ${field}`);
    const results = await api.get(url);
    return { success: true, data: results };
  } catch (error) {
    log.error(`Failed to fetch autocomplete for ${field}:`, error);
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
 * Import API handlers
 */
ipcMain.handle('import:uploadFile', async (event, fileData) => {
  try {
    validateRequired(fileData, 'fileData');
    validateRequired(fileData.locationId, 'locationId');
    validateString(fileData.locationId, 'locationId');
    validateRequired(fileData.filename, 'filename');
    validateString(fileData.filename, 'filename');
    validateRequired(fileData.category, 'category');
    validateString(fileData.category, 'category');
    validateRequired(fileData.size, 'size');
    validateNumber(fileData.size, 'size', { min: 1, max: 104857600 }); // Max 100MB
    validateRequired(fileData.data, 'data');
    validateString(fileData.data, 'data');

    log.info(`Uploading file ${fileData.filename} (${fileData.size} bytes) to location ${fileData.locationId}`);

    // Prepare payload with optional sublocation
    const payload = {
      filename: fileData.filename,
      category: fileData.category,
      size: fileData.size,
      data: fileData.data
    };

    // Add sublocation if provided
    if (fileData.sub_location) {
      payload.sub_location = fileData.sub_location;
      log.info(`Including sublocation: ${fileData.sub_location.name}`);
    }

    // Send file to AUPAT Core API
    const response = await api.post(`/api/locations/${fileData.locationId}/import`, payload);

    log.info(`Successfully uploaded ${fileData.filename}`);
    return { success: true, data: response };
  } catch (error) {
    log.error(`Failed to upload file:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * Directory picker handler
 */
ipcMain.handle('dialog:selectDirectory', async () => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
      title: 'Select Source Directory for Import'
    });

    if (result.canceled) {
      return { success: false, canceled: true };
    }

    const selectedPath = result.filePaths[0];
    log.info(`Directory selected: ${selectedPath}`);
    return { success: true, path: selectedPath };
  } catch (error) {
    log.error('Failed to show directory picker:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * Bulk import handler
 */
ipcMain.handle('import:bulkImport', async (event, data) => {
  try {
    validateRequired(data, 'data');
    validateRequired(data.locationId, 'locationId');
    validateString(data.locationId, 'locationId');
    validateRequired(data.sourcePath, 'sourcePath');
    validateString(data.sourcePath, 'sourcePath');

    log.info(`Starting bulk import for location ${data.locationId} from ${data.sourcePath}`);

    // Call the bulk import API endpoint
    const response = await api.post(`/api/locations/${data.locationId}/import/bulk`, {
      source_path: data.sourcePath,
      author: data.author || 'desktop-app'
    });

    log.info(`Bulk import completed for location ${data.locationId}. Batch ID: ${response.batch_id}`);
    return { success: true, data: response };
  } catch (error) {
    log.error(`Bulk import failed:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * Import batch status handler
 */
ipcMain.handle('import:getBatchStatus', async (event, batchId) => {
  try {
    validateRequired(batchId, 'batchId');
    validateString(batchId, 'batchId');

    log.info(`Fetching batch status for ${batchId}`);
    const status = await api.get(`/api/import/batches/${batchId}`);
    return { success: true, data: status };
  } catch (error) {
    log.error(`Failed to fetch batch status:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * Import batch logs handler
 */
ipcMain.handle('import:getBatchLogs', async (event, batchId, filters = {}) => {
  try {
    validateRequired(batchId, 'batchId');
    validateString(batchId, 'batchId');

    const params = new URLSearchParams();
    if (filters.stage) params.append('stage', filters.stage);
    if (filters.status) params.append('status', filters.status);

    const queryString = params.toString();
    const url = `/api/import/batches/${batchId}/logs${queryString ? '?' + queryString : ''}`;

    log.info(`Fetching batch logs for ${batchId}`);
    const logs = await api.get(url);
    return { success: true, data: logs };
  } catch (error) {
    log.error(`Failed to fetch batch logs:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * List import batches handler
 */
ipcMain.handle('import:listBatches', async (event, filters = {}) => {
  try {
    const params = new URLSearchParams();
    if (filters.loc_uuid) params.append('loc_uuid', filters.loc_uuid);
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());

    const queryString = params.toString();
    const url = `/api/import/batches${queryString ? '?' + queryString : ''}`;

    log.info('Fetching import batches');
    const batches = await api.get(url);
    return { success: true, data: batches };
  } catch (error) {
    log.error('Failed to fetch import batches:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * Configuration handlers
 */
ipcMain.handle('config:get', async () => {
  try {
    log.info('Fetching configuration');
    const config = await api.get('/api/config');
    return { success: true, data: config };
  } catch (error) {
    log.error('Failed to fetch configuration:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('config:update', async (event, configData) => {
  try {
    validateRequired(configData, 'configData');

    log.info('Updating configuration');
    const config = await api.put('/api/config', configData);
    return { success: true, data: config };
  } catch (error) {
    log.error('Failed to update configuration:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * URL Archive API handlers
 */
ipcMain.handle('urls:archive', async (event, data) => {
  try {
    validateRequired(data, 'data');
    validateRequired(data.locationId, 'locationId');
    validateString(data.locationId, 'locationId');
    validateRequired(data.url, 'url');
    validateString(data.url, 'url');

    log.info(`Archiving URL for location ${data.locationId}: ${data.url}`);

    const response = await api.post(`/api/locations/${data.locationId}/urls`, {
      url: data.url,
      title: data.title || null,
      description: data.description || null
    });

    log.info(`Successfully archived URL: ${data.url}`);
    return { success: true, data: response };
  } catch (error) {
    log.error(`Failed to archive URL:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('urls:getByLocation', async (event, locationId) => {
  try {
    validateRequired(locationId, 'locationId');
    validateString(locationId, 'locationId');

    log.info(`Fetching archived URLs for location ${locationId}`);

    const urls = await api.get(`/api/locations/${locationId}/archives`);

    return { success: true, data: urls };
  } catch (error) {
    log.error(`Failed to fetch URLs for location ${locationId}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('urls:delete', async (event, urlUuid) => {
  try {
    validateRequired(urlUuid, 'urlUuid');
    validateString(urlUuid, 'urlUuid');

    log.info(`Deleting URL ${urlUuid}`);

    const response = await api.delete(`/api/urls/${urlUuid}`);

    log.info(`Successfully deleted URL ${urlUuid}`);
    return { success: true, data: response };
  } catch (error) {
    log.error(`Failed to delete URL ${urlUuid}:`, error);
    return { success: false, error: sanitizeError(error) };
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

/**
 * Browser handlers
 */
ipcMain.handle('browser:create', async () => {
  try {
    if (!browserManager) {
      browserManager = new BrowserManager(mainWindow);
    }

    const view = browserManager.create();
    if (!view) {
      return { success: false, error: 'Failed to create browser view' };
    }

    log.info('Browser view created via IPC');
    return { success: true };
  } catch (error) {
    log.error('Failed to create browser:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:navigate', async (event, url) => {
  try {
    validateRequired(url, 'url');
    validateString(url, 'url');

    if (!browserManager || !browserManager.isCreated()) {
      return { success: false, error: 'Browser not initialized' };
    }

    browserManager.navigate(url);
    return { success: true };
  } catch (error) {
    log.error(`Failed to navigate to ${url}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:goBack', async () => {
  try {
    if (!browserManager || !browserManager.isCreated()) {
      return { success: false, error: 'Browser not initialized' };
    }

    browserManager.goBack();
    return { success: true };
  } catch (error) {
    log.error('Failed to go back:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:goForward', async () => {
  try {
    if (!browserManager || !browserManager.isCreated()) {
      return { success: false, error: 'Browser not initialized' };
    }

    browserManager.goForward();
    return { success: true };
  } catch (error) {
    log.error('Failed to go forward:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:reload', async () => {
  try {
    if (!browserManager || !browserManager.isCreated()) {
      return { success: false, error: 'Browser not initialized' };
    }

    browserManager.reload();
    return { success: true };
  } catch (error) {
    log.error('Failed to reload:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:setBounds', async (event, bounds) => {
  try {
    validateRequired(bounds, 'bounds');

    if (!browserManager || !browserManager.isCreated()) {
      return { success: false, error: 'Browser not initialized' };
    }

    browserManager.setBounds(bounds);
    return { success: true };
  } catch (error) {
    log.error('Failed to set browser bounds:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:getCookies', async (event, domain) => {
  try {
    validateRequired(domain, 'domain');
    validateString(domain, 'domain');

    if (!browserManager || !browserManager.isCreated()) {
      return { success: false, error: 'Browser not initialized' };
    }

    const cookies = await browserManager.getCookies(domain);
    return { success: true, data: cookies };
  } catch (error) {
    log.error(`Failed to get cookies for ${domain}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:exportCookies', async (event, domain) => {
  try {
    validateRequired(domain, 'domain');
    validateString(domain, 'domain');

    if (!browserManager || !browserManager.isCreated()) {
      return { success: false, error: 'Browser not initialized' };
    }

    const cookieString = await browserManager.exportCookiesForArchiveBox(domain);
    return { success: true, data: cookieString };
  } catch (error) {
    log.error(`Failed to export cookies for ${domain}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:destroy', async () => {
  try {
    if (browserManager) {
      browserManager.destroy();
      log.info('Browser view destroyed via IPC');
    }
    return { success: true };
  } catch (error) {
    log.error('Failed to destroy browser:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:getCurrentUrl', async () => {
  try {
    if (!browserManager || !browserManager.isCreated()) {
      return { success: false, error: 'Browser not initialized' };
    }

    const url = browserManager.getCurrentUrl();
    return { success: true, data: url };
  } catch (error) {
    log.error('Failed to get current URL:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('browser:getCurrentTitle', async () => {
  try {
    if (!browserManager || !browserManager.isCreated()) {
      return { success: false, error: 'Browser not initialized' };
    }

    const title = browserManager.getCurrentTitle();
    return { success: true, data: title };
  } catch (error) {
    log.error('Failed to get current title:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

/**
 * Bookmark handlers
 */
ipcMain.handle('bookmarks:create', async (event, bookmarkData) => {
  try {
    validateRequired(bookmarkData, 'bookmarkData');

    log.info('Creating bookmark via IPC');
    const bookmark = await api.post('/api/bookmarks', bookmarkData);
    return { success: true, data: bookmark };
  } catch (error) {
    log.error('Failed to create bookmark:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('bookmarks:getAll', async (event, filters = {}) => {
  try {
    const params = new URLSearchParams();

    if (filters.folder) params.append('folder', filters.folder);
    if (filters.loc_uuid) params.append('loc_uuid', filters.loc_uuid);
    if (filters.search) params.append('search', filters.search);
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());
    if (filters.order) params.append('order', filters.order);

    const queryString = params.toString();
    const url = `/api/bookmarks${queryString ? '?' + queryString : ''}`;

    log.info('Fetching bookmarks via IPC');
    const bookmarks = await api.get(url);
    return { success: true, data: bookmarks };
  } catch (error) {
    log.error('Failed to fetch bookmarks:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('bookmarks:getById', async (event, bookmarkUuid) => {
  try {
    validateRequired(bookmarkUuid, 'bookmarkUuid');
    validateString(bookmarkUuid, 'bookmarkUuid');

    log.info(`Fetching bookmark ${bookmarkUuid} via IPC`);
    const bookmark = await api.get(`/api/bookmarks/${bookmarkUuid}`);
    return { success: true, data: bookmark };
  } catch (error) {
    log.error(`Failed to fetch bookmark ${bookmarkUuid}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('bookmarks:update', async (event, bookmarkUuid, bookmarkData) => {
  try {
    validateRequired(bookmarkUuid, 'bookmarkUuid');
    validateString(bookmarkUuid, 'bookmarkUuid');
    validateRequired(bookmarkData, 'bookmarkData');

    log.info(`Updating bookmark ${bookmarkUuid} via IPC`);
    const bookmark = await api.put(`/api/bookmarks/${bookmarkUuid}`, bookmarkData);
    return { success: true, data: bookmark };
  } catch (error) {
    log.error(`Failed to update bookmark ${bookmarkUuid}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('bookmarks:delete', async (event, bookmarkUuid) => {
  try {
    validateRequired(bookmarkUuid, 'bookmarkUuid');
    validateString(bookmarkUuid, 'bookmarkUuid');

    log.info(`Deleting bookmark ${bookmarkUuid} via IPC`);
    await api.delete(`/api/bookmarks/${bookmarkUuid}`);
    return { success: true };
  } catch (error) {
    log.error(`Failed to delete bookmark ${bookmarkUuid}:`, error);
    return { success: false, error: sanitizeError(error) };
  }
});

ipcMain.handle('bookmarks:getFolders', async () => {
  try {
    log.info('Fetching bookmark folders via IPC');
    const folders = await api.get('/api/bookmarks/folders');
    return { success: true, data: folders };
  } catch (error) {
    log.error('Failed to fetch bookmark folders:', error);
    return { success: false, error: sanitizeError(error) };
  }
});

// App lifecycle

app.whenReady().then(async () => {
  // Set app user model id for Windows
  app.setAppUserModelId('com.abandonedupstate.app');

  // Clear cache to prevent stale code issues
  await clearAppCache();

  createWindow();

  // Initialize auto-updater (production only - requires signed builds)
  if (app.isPackaged) {
    initAutoUpdater(mainWindow);
    registerUpdateHandlers(ipcMain);
  } else {
    log.info('Auto-updater disabled in development mode');
  }

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
