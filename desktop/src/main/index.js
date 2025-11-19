/**
 * AUPAT Desktop v0.1.0 - Main Process
 *
 * Pure Electron desktop application with direct SQLite access.
 * NO Flask, NO HTTP API - everything runs locally.
 *
 * Architecture:
 * - Main process: Database operations, file I/O
 * - Renderer process: Svelte UI
 * - IPC: Secure communication bridge
 *
 * Security:
 * - contextIsolation: true
 * - nodeIntegration: false
 * - sandbox: true
 * - All IPC via preload script
 */

import { app, BrowserWindow, shell } from 'electron';
import { join } from 'path';
import log from 'electron-log';
import Store from 'electron-store';
import { BrowserManager } from './browser-manager.js';
// REMOVED: Auto-updater violates local-only requirement for v0.1.0
// import { initAutoUpdater, registerUpdateHandlers } from './updater.js';

// Import IPC handlers (desktop-v2 backend) - FIXED: Use ESM import instead of require
import { initializeHandlers } from './ipc-handlers.js';

// Configure logging
log.transports.file.level = 'info';
log.info('AUPAT v0.1.0 starting...');

// Initialize settings store
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
    mapZoom: 10
  }
});

// Migrate settings from old AUPAT Desktop to Abandoned Upstate
try {
  const oldStore = new Store({ name: 'aupat-desktop' });
  if (oldStore.size > 0 && store.size <= Object.keys(store.defaults).length) {
    log.info('Migrating settings from old AUPAT Desktop...');
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

// Remove deprecated Flask settings
if (store.has('apiUrl')) {
  store.delete('apiUrl');
  log.info('Removed deprecated Flask apiUrl setting');
}

let mainWindow;
let browserManager;

/**
 * Clear application cache on startup
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
    title: 'AUPAT - Abandoned Upstate Photo Archive Tool',
    width: 1400,
    height: 900,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
      webviewTag: true // For browser feature
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

  // Load the renderer
  if (!app.isPackaged && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL']);
    mainWindow.webContents.openDevTools(); // Auto-open DevTools in dev mode
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'));
  }
}

/**
 * Initialize browser manager (for web archive feature)
 */
function initBrowserManager() {
  const { ipcMain } = require('electron');

  ipcMain.handle('browser:create', async () => {
    try {
      if (!browserManager) {
        browserManager = new BrowserManager(mainWindow);
      }
      const view = browserManager.create();
      if (!view) {
        return { success: false, error: 'Failed to create browser view' };
      }
      log.info('Browser view created');
      return { success: true };
    } catch (error) {
      log.error('Failed to create browser:', error);
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:navigate', async (event, url) => {
    try {
      if (!browserManager || !browserManager.isCreated()) {
        return { success: false, error: 'Browser not initialized' };
      }
      browserManager.navigate(url);
      return { success: true };
    } catch (error) {
      log.error('Failed to navigate:', error);
      return { success: false, error: error.message };
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
      return { success: false, error: error.message };
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
      return { success: false, error: error.message };
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
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:setBounds', async (event, bounds) => {
    try {
      if (!browserManager || !browserManager.isCreated()) {
        return { success: false, error: 'Browser not initialized' };
      }
      browserManager.setBounds(bounds);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:getCookies', async (event, domain) => {
    try {
      if (!browserManager || !browserManager.isCreated()) {
        return { success: false, error: 'Browser not initialized' };
      }
      const cookies = await browserManager.getCookies(domain);
      return { success: true, data: cookies };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:exportCookies', async (event, domain) => {
    try {
      if (!browserManager || !browserManager.isCreated()) {
        return { success: false, error: 'Browser not initialized' };
      }
      const cookieString = await browserManager.exportCookiesForArchiveBox(domain);
      return { success: true, data: cookieString };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:destroy', async () => {
    try {
      if (browserManager) {
        browserManager.destroy();
        log.info('Browser view destroyed');
      }
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
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
      return { success: false, error: error.message };
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
      return { success: false, error: error.message };
    }
  });

  log.info('Browser manager handlers registered');
}

// App lifecycle

app.whenReady().then(async () => {
  // Set app user model id for Windows
  app.setAppUserModelId('com.abandonedupstate.app');

  log.info('='.repeat(60));
  log.info('AUPAT v0.1.0 - Pure Electron Edition');
  log.info('NO Flask, NO HTTP API - 100% Local SQLite');
  log.info('='.repeat(60));

  // Clear cache to prevent stale code issues
  await clearAppCache();

  // Initialize desktop-v2 backend (IPC handlers)
  try {
    initializeHandlers(store);
    log.info('✓ Desktop-v2 backend initialized');
    log.info(`✓ Database: ${store.get('dbPath')}`);
    log.info(`✓ Archive: ${store.get('archiveRoot')}`);
  } catch (error) {
    log.error('Failed to initialize backend:', error);
    app.quit();
    return;
  }

  // Initialize browser manager
  initBrowserManager();

  // Create main window
  createWindow();

  // REMOVED: Auto-updater for v0.1.0 (violates local-only requirement)
  // For updates: User must manually download new version from GitHub releases
  log.info('Auto-updater disabled for v0.1.0 (local-only requirement)');

  app.on('activate', function () {
    // On macOS re-create window when dock icon is clicked
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });

  log.info('AUPAT v0.1.0 ready!');
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Handle crashes gracefully
process.on('uncaughtException', (error) => {
  log.error('Uncaught exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  log.error('Unhandled rejection at:', promise, 'reason:', reason);
});
