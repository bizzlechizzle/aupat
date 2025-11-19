/**
 * AUPAT IPC Handlers
 *
 * Electron IPC handlers that connect the Svelte UI to backend modules.
 * Replaces the Flask HTTP API with direct function calls.
 *
 * Security: All handlers are exposed via contextBridge in preload.js
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

const { ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

// Import backend modules
const { getDatabase, createSchema, databaseExists } = require('./database');
const { createLocation, getLocation, getAllLocations, searchLocations, updateLocation, deleteLocation } = require('./modules/locations');
const { createLocationFolders } = require('./modules/folders');
const { importFile } = require('./modules/import');
const { getImagesByLocation, getImage, getImagePath, countImagesByLocation } = require('./modules/images');

// Database instance (initialized on app start)
let db = null;
let settings = null;

/**
 * Initialize IPC handlers and database.
 *
 * Call this from the main process on app ready.
 *
 * @param {Object} electronStore - Electron-store instance with settings
 */
function initializeHandlers(electronStore) {
  settings = electronStore;

  // Get paths from settings
  const dbPath = settings.get('dbPath') || path.join(app.getPath('userData'), 'data', 'aupat.db');
  const archiveRoot = settings.get('archiveRoot') || path.join(app.getPath('userData'), 'archive');

  // Store paths back to settings if they were defaults
  if (!settings.get('dbPath')) {
    settings.set('dbPath', dbPath);
  }
  if (!settings.get('archiveRoot')) {
    settings.set('archiveRoot', archiveRoot);
  }

  // Initialize database
  db = getDatabase(dbPath);

  // Create schema if database is new
  if (!databaseExists(dbPath) || _isEmptyDatabase(db)) {
    console.log('Creating database schema...');
    createSchema(db);
  }

  // Register all IPC handlers
  registerLocationHandlers();
  registerImportHandlers();
  registerSettingsHandlers();
  registerStatsHandlers();
  registerImagesHandlers();

  console.log('IPC handlers initialized');
}

/**
 * INTERNAL: Check if database is empty (no tables).
 */
function _isEmptyDatabase(db) {
  const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
  return tables.length === 0;
}

// ============================================================================
// LOCATION HANDLERS
// ============================================================================

function registerLocationHandlers() {
  /**
   * Create new location
   */
  ipcMain.handle('location:create', async (event, locationData) => {
    try {
      const result = createLocation(db, locationData);
      return { success: true, data: result };
    } catch (error) {
      console.error('location:create error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Get location by UUID
   */
  ipcMain.handle('location:get', async (event, locUuid) => {
    try {
      const location = getLocation(db, locUuid);
      if (!location) {
        return { success: false, error: 'Location not found' };
      }
      return { success: true, data: location };
    } catch (error) {
      console.error('location:get error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Get all locations with pagination
   */
  ipcMain.handle('location:getAll', async (event, options = {}) => {
    try {
      const locations = getAllLocations(db, options);
      return { success: true, data: locations };
    } catch (error) {
      console.error('location:getAll error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Search locations (for autocomplete)
   */
  ipcMain.handle('location:search', async (event, searchTerm, limit = 10) => {
    try {
      const results = searchLocations(db, searchTerm, limit);
      return { success: true, data: results };
    } catch (error) {
      console.error('location:search error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Update location
   */
  ipcMain.handle('location:update', async (event, locUuid, updates) => {
    try {
      const success = updateLocation(db, locUuid, updates);
      return { success, data: { updated: success } };
    } catch (error) {
      console.error('location:update error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Delete location
   */
  ipcMain.handle('location:delete', async (event, locUuid) => {
    try {
      const success = deleteLocation(db, locUuid);
      return { success, data: { deleted: success } };
    } catch (error) {
      console.error('location:delete error:', error);
      return { success: false, error: error.message };
    }
  });
}

// ============================================================================
// IMPORT HANDLERS
// ============================================================================

function registerImportHandlers() {
  /**
   * Import single file
   */
  ipcMain.handle('import:file', async (event, filePath, locationData, options = {}) => {
    try {
      const archiveRoot = settings.get('archiveRoot');
      const deleteSource = settings.get('deleteAfterImport') || options.deleteSource || false;

      const result = await importFile(
        db,
        filePath,
        locationData,
        archiveRoot,
        { deleteSource }
      );

      return result;  // Already in format {success, ...}
    } catch (error) {
      console.error('import:file error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Import multiple files (batch)
   */
  ipcMain.handle('import:batch', async (event, filePaths, locationData, options = {}) => {
    try {
      const archiveRoot = settings.get('archiveRoot');
      const deleteSource = settings.get('deleteAfterImport') || options.deleteSource || false;

      const results = {
        total: filePaths.length,
        imported: 0,
        failed: 0,
        errors: []
      };

      for (const filePath of filePaths) {
        const result = await importFile(
          db,
          filePath,
          locationData,
          archiveRoot,
          { deleteSource }
        );

        if (result.success) {
          results.imported++;
        } else {
          results.failed++;
          results.errors.push({
            file: path.basename(filePath),
            error: result.error
          });
        }

        // Send progress update
        event.sender.send('import:progress', {
          current: results.imported + results.failed,
          total: results.total
        });
      }

      return { success: true, data: results };
    } catch (error) {
      console.error('import:batch error:', error);
      return { success: false, error: error.message };
    }
  });
}

// ============================================================================
// SETTINGS HANDLERS
// ============================================================================

function registerSettingsHandlers() {
  /**
   * Get all settings
   */
  ipcMain.handle('settings:getAll', async () => {
    try {
      return {
        success: true,
        data: {
          dbPath: settings.get('dbPath'),
          archiveRoot: settings.get('archiveRoot'),
          deleteAfterImport: settings.get('deleteAfterImport', false),
          importAuthor: settings.get('importAuthor', ''),
          mapCenter: settings.get('mapCenter'),
          mapZoom: settings.get('mapZoom')
        }
      };
    } catch (error) {
      console.error('settings:getAll error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Update settings
   */
  ipcMain.handle('settings:update', async (event, updates) => {
    try {
      for (const [key, value] of Object.entries(updates)) {
        settings.set(key, value);
      }
      return { success: true };
    } catch (error) {
      console.error('settings:update error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Choose folder (for archive/db paths)
   */
  ipcMain.handle('settings:chooseFolder', async (event, title = 'Choose Folder') => {
    const { dialog } = require('electron');
    try {
      const result = await dialog.showOpenDialog({
        title,
        properties: ['openDirectory', 'createDirectory']
      });

      if (result.canceled) {
        return { success: false, canceled: true };
      }

      return { success: true, data: result.filePaths[0] };
    } catch (error) {
      console.error('settings:chooseFolder error:', error);
      return { success: false, error: error.message };
    }
  });
}

// ============================================================================
// IMAGES HANDLERS
// ============================================================================

function registerImagesHandlers() {
  /**
   * Get images by location
   */
  ipcMain.handle('images:getByLocation', async (event, locUuid, limit, offset) => {
    try {
      const images = getImagesByLocation(db, locUuid, { limit, offset });
      return { success: true, data: images };
    } catch (error) {
      console.error('images:getByLocation error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Get single image
   */
  ipcMain.handle('images:get', async (event, imgUuid) => {
    try {
      const image = getImage(db, imgUuid);
      if (!image) {
        return { success: false, error: 'Image not found' };
      }
      return { success: true, data: image };
    } catch (error) {
      console.error('images:get error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Get image file path
   */
  ipcMain.handle('images:getPath', async (event, imgUuid) => {
    try {
      const archiveRoot = settings.get('archiveRoot');
      const result = getImagePath(db, imgUuid, archiveRoot);
      return result;
    } catch (error) {
      console.error('images:getPath error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Count images for location
   */
  ipcMain.handle('images:count', async (event, locUuid) => {
    try {
      const count = countImagesByLocation(db, locUuid);
      return { success: true, data: count };
    } catch (error) {
      console.error('images:count error:', error);
      return { success: false, error: error.message };
    }
  });
}

// ============================================================================
// STATS HANDLERS
// ============================================================================

function registerStatsHandlers() {
  /**
   * Get dashboard statistics
   */
  ipcMain.handle('stats:dashboard', async () => {
    try {
      const stats = {
        locations: db.prepare('SELECT COUNT(*) as count FROM locations').get().count,
        images: db.prepare('SELECT COUNT(*) as count FROM images').get().count,
        videos: db.prepare('SELECT COUNT(*) as count FROM videos').get().count,
        documents: db.prepare('SELECT COUNT(*) as count FROM documents').get().count,
        maps: db.prepare('SELECT COUNT(*) as count FROM maps').get().count,
        states: db.prepare('SELECT COUNT(DISTINCT state) as count FROM locations').get().count,
        types: db.prepare('SELECT COUNT(DISTINCT type) as count FROM locations').get().count
      };

      return { success: true, data: stats };
    } catch (error) {
      console.error('stats:dashboard error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Get locations by state
   */
  ipcMain.handle('stats:byState', async () => {
    try {
      const results = db.prepare(`
        SELECT state, COUNT(*) as count
        FROM locations
        GROUP BY state
        ORDER BY count DESC
      `).all();

      return { success: true, data: results };
    } catch (error) {
      console.error('stats:byState error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Get locations by type
   */
  ipcMain.handle('stats:byType', async () => {
    try {
      const results = db.prepare(`
        SELECT type, COUNT(*) as count
        FROM locations
        GROUP BY type
        ORDER BY count DESC
      `).all();

      return { success: true, data: results };
    } catch (error) {
      console.error('stats:byType error:', error);
      return { success: false, error: error.message };
    }
  });
}

// Export
module.exports = {
  initializeHandlers
};
