/**
 * AUPAT IPC Handlers
 *
 * Electron IPC handlers that connect the Svelte UI to backend modules.
 * Replaces the Flask HTTP API with direct function calls.
 *
 * Security: All handlers are exposed via contextBridge in preload.js
 *
 * Version: 1.1.0 - Converted to ESM
 * Last Updated: 2025-11-19
 */

import { ipcMain } from 'electron';
import path from 'path';
import fs from 'fs';

// Import backend modules
import { getDatabase, createSchema, databaseExists } from './database/index.js';
import { createLocation, getLocation, getAllLocations, searchLocations, updateLocation, deleteLocation } from './modules/locations.js';
import { createLocationFolders } from './modules/folders.js';
import { importFile } from './modules/import.js';
import { getImagesByLocation, getImage, getImagePath, countImagesByLocation } from './modules/images.js';

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

  // Get paths from settings (already set with defaults in main process)
  const dbPath = settings.get('dbPath');
  const archiveRoot = settings.get('archiveRoot');

  // Ensure directories exist
  const dbDir = path.dirname(dbPath);
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }
  if (!fs.existsSync(archiveRoot)) {
    fs.mkdirSync(archiveRoot, { recursive: true });
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
  registerHealthHandlers();
  registerConfigHandlers();
  registerDialogHandlers();

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

// ============================================================================
// HEALTH HANDLERS
// ============================================================================

function registerHealthHandlers() {
  /**
   * Check database health
   */
  ipcMain.handle('health:check', async () => {
    try {
      // Check if database is connected and accessible
      if (!db) {
        return { success: false, error: 'Database not initialized' };
      }

      // Test database with simple query
      const result = db.prepare('SELECT COUNT(*) as count FROM locations').get();
      const locationCount = result.count;

      // Check if tables exist
      const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
      const hasSchema = tables.length > 0;

      return {
        success: true,
        data: {
          status: 'healthy',
          database: 'connected',
          locationCount,
          hasSchema,
          dbPath: settings.get('dbPath'),
          archiveRoot: settings.get('archiveRoot')
        }
      };
    } catch (error) {
      console.error('health:check error:', error);
      return {
        success: false,
        error: error.message,
        data: {
          status: 'error',
          database: 'error'
        }
      };
    }
  });
}

// ============================================================================
// CONFIG HANDLERS
// ============================================================================

function registerConfigHandlers() {
  /**
   * Get configuration
   */
  ipcMain.handle('config:get', async () => {
    try {
      return {
        success: true,
        data: {
          configured: true,
          db_path: settings.get('dbPath'),
          archive_path: settings.get('archiveRoot'),
          staging_path: settings.get('stagingPath', ''),
          backup_path: settings.get('backupPath', ''),
          deleteAfterImport: settings.get('deleteAfterImport', false),
          importAuthor: settings.get('importAuthor', '')
        }
      };
    } catch (error) {
      console.error('config:get error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Update configuration
   */
  ipcMain.handle('config:update', async (event, updates) => {
    try {
      for (const [key, value] of Object.entries(updates)) {
        // Map config keys to settings keys
        const settingsKey = {
          'db_path': 'dbPath',
          'archive_path': 'archiveRoot',
          'staging_path': 'stagingPath',
          'backup_path': 'backupPath'
        }[key] || key;

        settings.set(settingsKey, value);
      }
      return { success: true };
    } catch (error) {
      console.error('config:update error:', error);
      return { success: false, error: error.message };
    }
  });
}

// ============================================================================
// DIALOG HANDLERS
// ============================================================================

function registerDialogHandlers() {
  /**
   * Select directory dialog
   */
  ipcMain.handle('dialog:selectDirectory', async (event, options = {}) => {
    const { dialog } = require('electron');
    try {
      const result = await dialog.showOpenDialog({
        title: options.title || 'Select Directory',
        properties: ['openDirectory', 'createDirectory']
      });

      if (result.canceled) {
        return { success: false, canceled: true };
      }

      return { success: true, path: result.filePaths[0] };
    } catch (error) {
      console.error('dialog:selectDirectory error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Select file dialog
   */
  ipcMain.handle('dialog:selectFile', async (event, options = {}) => {
    const { dialog } = require('electron');
    try {
      const result = await dialog.showOpenDialog({
        title: options.title || 'Select File',
        properties: ['openFile'],
        filters: options.filters || []
      });

      if (result.canceled) {
        return { success: false, canceled: true };
      }

      return { success: true, path: result.filePaths[0] };
    } catch (error) {
      console.error('dialog:selectFile error:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Select multiple files dialog
   */
  ipcMain.handle('dialog:selectFiles', async (event, options = {}) => {
    const { dialog } = require('electron');
    try {
      const result = await dialog.showOpenDialog({
        title: options.title || 'Select Files',
        properties: ['openFile', 'multiSelections'],
        filters: options.filters || []
      });

      if (result.canceled) {
        return { success: false, canceled: true };
      }

      return { success: true, paths: result.filePaths };
    } catch (error) {
      console.error('dialog:selectFiles error:', error);
      return { success: false, error: error.message };
    }
  });
}

// Export (ESM format)
export {
  initializeHandlers
};
