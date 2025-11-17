import { ipcMain, app, BrowserWindow, shell } from "electron";
import { join } from "path";
import log from "electron-log";
import Store from "electron-store";
import __cjs_url__ from "node:url";
import __cjs_path__ from "node:path";
import __cjs_mod__ from "node:module";
const __filename = __cjs_url__.fileURLToPath(import.meta.url);
const __dirname = __cjs_path__.dirname(__filename);
const require2 = __cjs_mod__.createRequire(import.meta.url);
const DEFAULT_TIMEOUT = 3e4;
const MAX_RETRIES = 3;
function createAPIClient(baseUrl) {
  let currentBaseUrl = baseUrl;
  async function request(method, path, data = null, retries = MAX_RETRIES) {
    const url = `${currentBaseUrl}${path}`;
    const options = {
      method,
      headers: {
        "Content-Type": "application/json"
      },
      signal: AbortSignal.timeout(DEFAULT_TIMEOUT)
    };
    if (data && (method === "POST" || method === "PUT")) {
      options.body = JSON.stringify(data);
    }
    try {
      log.debug(`${method} ${url}`);
      const response = await fetch(url, options);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `HTTP ${response.status}: ${errorText || response.statusText}`
        );
      }
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return await response.json();
      }
      return null;
    } catch (error) {
      if (retries > 0 && error.name === "TypeError") {
        log.warn(`Request failed, retrying... (${retries} left)`);
        await new Promise((resolve) => setTimeout(resolve, 1e3));
        return request(method, path, data, retries - 1);
      }
      log.error(`${method} ${url} failed:`, error.message);
      throw error;
    }
  }
  return {
    /**
     * Update base URL (e.g., when user changes settings)
     */
    setBaseUrl(newUrl) {
      currentBaseUrl = newUrl;
      log.info(`API base URL updated to ${newUrl}`);
    },
    /**
     * GET request
     */
    async get(path) {
      return request("GET", path);
    },
    /**
     * POST request
     */
    async post(path, data) {
      return request("POST", path, data);
    },
    /**
     * PUT request
     */
    async put(path, data) {
      return request("PUT", path, data);
    },
    /**
     * DELETE request
     */
    async delete(path) {
      return request("DELETE", path);
    }
  };
}
log.transports.file.level = "info";
log.info("AUPAT Desktop starting...");
const store = new Store({
  defaults: {
    apiUrl: "http://localhost:5001",
    immichUrl: "http://localhost:2283",
    archiveboxUrl: "http://localhost:8001",
    mapCenter: { lat: 42.6526, lng: -73.7562 },
    // Albany, NY
    mapZoom: 10
  }
});
const api = createAPIClient(store.get("apiUrl"));
let mainWindow;
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, "../preload/index.js"),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  mainWindow.on("ready-to-show", () => {
    mainWindow.show();
    log.info("Main window ready");
  });
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url);
    return { action: "deny" };
  });
  if (!app.isPackaged && process.env["ELECTRON_RENDERER_URL"]) {
    mainWindow.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    mainWindow.loadFile(join(__dirname, "../renderer/index.html"));
  }
}
ipcMain.handle("settings:get", async () => {
  log.info("Getting all settings");
  return store.store;
});
ipcMain.handle("settings:set", async (event, key, value) => {
  log.info(`Setting ${key} = ${value}`);
  store.set(key, value);
  if (key === "apiUrl") {
    api.setBaseUrl(value);
  }
  return true;
});
ipcMain.handle("locations:getAll", async () => {
  try {
    log.info("Fetching all locations");
    const locations = await api.get("/api/locations");
    return { success: true, data: locations };
  } catch (error) {
    log.error("Failed to fetch locations:", error);
    return { success: false, error: error.message };
  }
});
ipcMain.handle("locations:getById", async (event, id) => {
  try {
    log.info(`Fetching location ${id}`);
    const location = await api.get(`/api/locations/${id}`);
    return { success: true, data: location };
  } catch (error) {
    log.error(`Failed to fetch location ${id}:`, error);
    return { success: false, error: error.message };
  }
});
ipcMain.handle("locations:create", async (event, locationData) => {
  try {
    log.info("Creating new location");
    const location = await api.post("/api/locations", locationData);
    return { success: true, data: location };
  } catch (error) {
    log.error("Failed to create location:", error);
    return { success: false, error: error.message };
  }
});
ipcMain.handle("locations:update", async (event, id, locationData) => {
  try {
    log.info(`Updating location ${id}`);
    const location = await api.put(`/api/locations/${id}`, locationData);
    return { success: true, data: location };
  } catch (error) {
    log.error(`Failed to update location ${id}:`, error);
    return { success: false, error: error.message };
  }
});
ipcMain.handle("locations:delete", async (event, id) => {
  try {
    log.info(`Deleting location ${id}`);
    await api.delete(`/api/locations/${id}`);
    return { success: true };
  } catch (error) {
    log.error(`Failed to delete location ${id}:`, error);
    return { success: false, error: error.message };
  }
});
ipcMain.handle("map:getMarkers", async () => {
  try {
    log.info("Fetching map markers");
    const markers = await api.get("/api/map/markers");
    return { success: true, data: markers };
  } catch (error) {
    log.error("Failed to fetch map markers:", error);
    return { success: false, error: error.message };
  }
});
ipcMain.handle("api:health", async () => {
  try {
    const health = await api.get("/api/health");
    return { success: true, data: health };
  } catch (error) {
    log.error("Health check failed:", error);
    return { success: false, error: error.message };
  }
});
app.whenReady().then(() => {
  app.setAppUserModelId("com.aupat.desktop");
  createWindow();
  app.on("activate", function() {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
