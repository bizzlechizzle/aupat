/**
 * AUPAT Preload Script
 *
 * Securely exposes IPC handlers to the renderer process (Svelte).
 * Uses contextBridge to prevent direct Node.js access in renderer.
 *
 * Security:
 * - contextIsolation: true
 * - nodeIntegration: false
 * - Only specific APIs exposed via contextBridge
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose API to renderer via window.api
contextBridge.exposeInMainWorld('api', {
  // ============================================================================
  // LOCATION API
  // ============================================================================
  location: {
    /**
     * Create new location
     * @param {Object} locationData - Location data (name, state, type, etc.)
     * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
     */
    create: (locationData) => ipcRenderer.invoke('location:create', locationData),

    /**
     * Get location by UUID
     * @param {string} locUuid - Location UUID
     * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
     */
    get: (locUuid) => ipcRenderer.invoke('location:get', locUuid),

    /**
     * Get all locations
     * @param {Object} options - Query options (limit, offset, orderBy)
     * @returns {Promise<{success: boolean, data?: Array, error?: string}>}
     */
    getAll: (options) => ipcRenderer.invoke('location:getAll', options),

    /**
     * Search locations (autocomplete)
     * @param {string} searchTerm - Search term
     * @param {number} limit - Max results
     * @returns {Promise<{success: boolean, data?: Array, error?: string}>}
     */
    search: (searchTerm, limit) => ipcRenderer.invoke('location:search', searchTerm, limit),

    /**
     * Update location
     * @param {string} locUuid - Location UUID
     * @param {Object} updates - Fields to update
     * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
     */
    update: (locUuid, updates) => ipcRenderer.invoke('location:update', locUuid, updates),

    /**
     * Delete location
     * @param {string} locUuid - Location UUID
     * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
     */
    delete: (locUuid) => ipcRenderer.invoke('location:delete', locUuid)
  },

  // ============================================================================
  // IMPORT API
  // ============================================================================
  import: {
    /**
     * Import single file
     * @param {string} filePath - Source file path
     * @param {Object} locationData - Location info (locUuid, locShort, state, type)
     * @param {Object} options - Import options (deleteSource)
     * @returns {Promise<{success: boolean, fileUuid?: string, error?: string}>}
     */
    file: (filePath, locationData, options) =>
      ipcRenderer.invoke('import:file', filePath, locationData, options),

    /**
     * Import multiple files (batch)
     * @param {Array<string>} filePaths - Array of file paths
     * @param {Object} locationData - Location info
     * @param {Object} options - Import options
     * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
     */
    batch: (filePaths, locationData, options) =>
      ipcRenderer.invoke('import:batch', filePaths, locationData, options),

    /**
     * Listen for import progress updates
     * @param {Function} callback - Called with {current, total}
     */
    onProgress: (callback) => {
      ipcRenderer.on('import:progress', (event, data) => callback(data));
    },

    /**
     * Remove progress listener
     */
    removeProgressListener: () => {
      ipcRenderer.removeAllListeners('import:progress');
    }
  },

  // ============================================================================
  // SETTINGS API
  // ============================================================================
  settings: {
    /**
     * Get all settings
     * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
     */
    getAll: () => ipcRenderer.invoke('settings:getAll'),

    /**
     * Update settings
     * @param {Object} updates - Settings to update
     * @returns {Promise<{success: boolean, error?: string}>}
     */
    update: (updates) => ipcRenderer.invoke('settings:update', updates),

    /**
     * Choose folder (opens native dialog)
     * @param {string} title - Dialog title
     * @returns {Promise<{success: boolean, data?: string, canceled?: boolean, error?: string}>}
     */
    chooseFolder: (title) => ipcRenderer.invoke('settings:chooseFolder', title)
  },

  // ============================================================================
  // STATS API
  // ============================================================================
  stats: {
    /**
     * Get dashboard statistics
     * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
     */
    dashboard: () => ipcRenderer.invoke('stats:dashboard'),

    /**
     * Get locations by state
     * @returns {Promise<{success: boolean, data?: Array, error?: string}>}
     */
    byState: () => ipcRenderer.invoke('stats:byState'),

    /**
     * Get locations by type
     * @returns {Promise<{success: boolean, data?: Array, error?: string}>}
     */
    byType: () => ipcRenderer.invoke('stats:byType')
  },

  // ============================================================================
  // SYSTEM API
  // ============================================================================
  system: {
    /**
     * Get platform info
     */
    platform: process.platform,

    /**
     * Get app version
     */
    version: process.env.npm_package_version || '0.1.0'
  }
});

console.log('AUPAT preload script loaded - window.api available');
