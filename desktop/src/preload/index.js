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

import { contextBridge, ipcRenderer } from 'electron';

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
    delete: (id) => ipcRenderer.invoke('locations:delete', id)
  },

  /**
   * Map API
   */
  map: {
    getMarkers: () => ipcRenderer.invoke('map:getMarkers')
  },

  /**
   * Health check
   */
  health: {
    check: () => ipcRenderer.invoke('api:health')
  }
});
