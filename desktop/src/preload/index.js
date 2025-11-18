/**
 * AUPAT Desktop - Preload Script
 *
 * Secure IPC bridge between main and renderer processes.
 * Exposes minimal, validated API to renderer.
 *
 * Security:
 * - Uses contextBridge (no direct access to Node APIs in renderer)
 * - All IPC calls validated in main process
 * - No eval, no arbitrary code execution
 *
 * @see https://www.electronjs.org/docs/latest/tutorial/context-isolation
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('api', {
  /**
   * Settings API
   */
  settings: {
    get: () => ipcRenderer.invoke('settings:get'),
    set: (key, value) => ipcRenderer.invoke('settings:set', key, value)
  },

  /**
   * Locations API
   */
  locations: {
    getAll: () => ipcRenderer.invoke('locations:getAll'),
    getById: (id) => ipcRenderer.invoke('locations:getById', id),
    create: (data) => ipcRenderer.invoke('locations:create', data),
    update: (id, data) => ipcRenderer.invoke('locations:update', id, data),
    delete: (id) => ipcRenderer.invoke('locations:delete', id),
    autocomplete: (field, options) => ipcRenderer.invoke('locations:autocomplete', field, options)
  },

  /**
   * Map API
   */
  map: {
    getMarkers: () => ipcRenderer.invoke('map:getMarkers')
  },

  /**
   * Images API
   */
  images: {
    getByLocation: (locUuid, limit, offset) => ipcRenderer.invoke('images:getByLocation', locUuid, limit, offset),
    getThumbnailUrl: (assetId) => ipcRenderer.invoke('images:getThumbnailUrl', assetId),
    getOriginalUrl: (assetId) => ipcRenderer.invoke('images:getOriginalUrl', assetId)
  },

  /**
   * Import API
   */
  import: {
    uploadFile: (fileData) => ipcRenderer.invoke('import:uploadFile', fileData),
    bulkImport: (data) => ipcRenderer.invoke('import:bulkImport', data),
    getBatchStatus: (batchId) => ipcRenderer.invoke('import:getBatchStatus', batchId),
    getBatchLogs: (batchId, filters) => ipcRenderer.invoke('import:getBatchLogs', batchId, filters),
    listBatches: (filters) => ipcRenderer.invoke('import:listBatches', filters)
  },

  /**
   * Dialog API
   */
  dialog: {
    selectDirectory: () => ipcRenderer.invoke('dialog:selectDirectory')
  },

  /**
   * URLs API (Web Archive)
   */
  urls: {
    archive: (data) => ipcRenderer.invoke('urls:archive', data),
    getByLocation: (locationId) => ipcRenderer.invoke('urls:getByLocation', locationId),
    delete: (urlUuid) => ipcRenderer.invoke('urls:delete', urlUuid)
  },

  /**
   * Bookmarks API
   */
  bookmarks: {
    getAll: (filters) => ipcRenderer.invoke('bookmarks:getAll', filters),
    getById: (bookmarkUuid) => ipcRenderer.invoke('bookmarks:getById', bookmarkUuid),
    create: (bookmarkData) => ipcRenderer.invoke('bookmarks:create', bookmarkData),
    update: (bookmarkUuid, bookmarkData) => ipcRenderer.invoke('bookmarks:update', bookmarkUuid, bookmarkData),
    delete: (bookmarkUuid) => ipcRenderer.invoke('bookmarks:delete', bookmarkUuid),
    getFolders: () => ipcRenderer.invoke('bookmarks:getFolders')
  },

  /**
   * Health check
   */
  health: {
    check: () => ipcRenderer.invoke('api:health')
  },

  /**
   * Auto-Update API
   */
  updates: {
    check: () => ipcRenderer.invoke('update:check'),
    download: () => ipcRenderer.invoke('update:download'),
    install: () => ipcRenderer.invoke('update:install'),
    version: () => ipcRenderer.invoke('update:version'),
    onAvailable: (callback) => ipcRenderer.on('update-available', (_, data) => callback(data)),
    onDownloaded: (callback) => ipcRenderer.on('update-downloaded', (_, data) => callback(data)),
    onProgress: (callback) => ipcRenderer.on('update-progress', (_, data) => callback(data)),
    onError: (callback) => ipcRenderer.on('update-error', (_, data) => callback(data)),
    removeAvailableListener: (callback) => ipcRenderer.removeListener('update-available', callback),
    removeDownloadedListener: (callback) => ipcRenderer.removeListener('update-downloaded', callback),
    removeProgressListener: (callback) => ipcRenderer.removeListener('update-progress', callback),
    removeErrorListener: (callback) => ipcRenderer.removeListener('update-error', callback)
  }
});
