/**
 * AUPAT Configuration Loader
 *
 * ONE FUNCTION: Initialize and manage application settings
 *
 * LILBITS Principle: One script = one function
 * This module handles electron-store initialization, settings migration,
 * and default configuration values.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import { app } from 'electron';
import { join } from 'path';
import Store from 'electron-store';
import log from 'electron-log';

/**
 * Initialize application configuration store.
 *
 * Creates electron-store with defaults, handles migration from old
 * aupat-desktop settings, and removes deprecated Flask API settings.
 *
 * @returns {Object} Configuration object with store and paths
 * @returns {Store} config.store - Electron-store instance
 * @returns {string} config.dbPath - Database file path
 * @returns {string} config.archiveRoot - Archive root directory
 * @returns {string} config.version - App version
 */
export function initConfig() {
  // Initialize settings store with defaults
  const store = new Store({
    defaults: {
      // Database and archive paths (set on first run)
      dbPath: join(app.getPath('userData'), 'data', 'aupat.db'),
      archiveRoot: join(app.getPath('userData'), 'archive'),

      // Import settings
      deleteAfterImport: false,
      importAuthor: '',

      // Map settings
      mapCenter: { lat: 42.6526, lng: -73.7562 }, // Albany, NY
      mapZoom: 10,

      // Version tracking for cache management
      lastClearedVersion: null
    }
  });

  // Migrate settings from old AUPAT Desktop store
  _migrateOldSettings(store);

  // Remove deprecated Flask API settings
  _cleanupDeprecatedSettings(store);

  log.info('Configuration loaded');
  log.info(`Database: ${store.get('dbPath')}`);
  log.info(`Archive: ${store.get('archiveRoot')}`);

  return {
    store,
    dbPath: store.get('dbPath'),
    archiveRoot: store.get('archiveRoot'),
    version: app.getVersion()
  };
}

/**
 * INTERNAL: Migrate settings from old aupat-desktop store.
 *
 * Copies settings from old store if it exists and current store
 * has only default values.
 *
 * @param {Store} store - Current electron-store instance
 */
function _migrateOldSettings(store) {
  try {
    const oldStore = new Store({ name: 'aupat-desktop' });
    const defaultKeys = Object.keys(store.defaults);

    // Only migrate if old store has data and current store is fresh
    if (oldStore.size > 0 && store.size <= defaultKeys.length) {
      log.info('Migrating settings from old AUPAT Desktop...');

      for (const [key, value] of Object.entries(oldStore.store)) {
        if (!store.has(key)) {
          store.set(key, value);
          log.info(`  Migrated: ${key}`);
        }
      }

      log.info('Settings migration complete');
    }
  } catch (error) {
    log.warn('Settings migration skipped:', error.message);
  }
}

/**
 * INTERNAL: Remove deprecated settings from Flask API era.
 *
 * Removes apiUrl and other deprecated settings that are no longer
 * needed in the pure Electron (no Flask) architecture.
 *
 * @param {Store} store - Electron-store instance
 */
function _cleanupDeprecatedSettings(store) {
  const deprecated = ['apiUrl', 'flaskPort', 'apiHost'];

  for (const key of deprecated) {
    if (store.has(key)) {
      store.delete(key);
      log.info(`Removed deprecated setting: ${key}`);
    }
  }
}
