import { contextBridge, ipcRenderer } from "electron";
contextBridge.exposeInMainWorld("api", {
  /**
   * Settings API
   */
  settings: {
    get: () => ipcRenderer.invoke("settings:get"),
    set: (key, value) => ipcRenderer.invoke("settings:set", key, value)
  },
  /**
   * Locations API
   */
  locations: {
    getAll: () => ipcRenderer.invoke("locations:getAll"),
    getById: (id) => ipcRenderer.invoke("locations:getById", id),
    create: (data) => ipcRenderer.invoke("locations:create", data),
    update: (id, data) => ipcRenderer.invoke("locations:update", id, data),
    delete: (id) => ipcRenderer.invoke("locations:delete", id)
  },
  /**
   * Map API
   */
  map: {
    getMarkers: () => ipcRenderer.invoke("map:getMarkers")
  },
  /**
   * Health check
   */
  health: {
    check: () => ipcRenderer.invoke("api:health")
  }
});
