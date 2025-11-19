/**
 * AUPAT Window Manager
 *
 * ONE FUNCTION: Create and manage the main application window
 *
 * LILBITS Principle: One script = one function
 * This module handles BrowserWindow creation with security settings,
 * renderer loading, and external link handling.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import { app, BrowserWindow, shell } from 'electron';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import log from 'electron-log';

// ES modules don't have __dirname, so we derive it
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Create the main application window with security settings.
 *
 * Configures:
 * - Security: sandbox, contextIsolation, no nodeIntegration
 * - Size: 1400x900 default
 * - Preload script for IPC bridge
 * - External link handling (opens in default browser)
 * - DevTools auto-open in development mode
 *
 * @returns {BrowserWindow} The created main window
 */
export function createMainWindow() {
  const mainWindow = new BrowserWindow({
    title: 'AUPAT - Abandoned Upstate Photo Archive Tool',
    width: 1400,
    height: 900,
    show: false, // Show only when ready
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
      webviewTag: true // Required for embedded browser feature
    }
  });

  // Show window when ready (prevents white flash)
  mainWindow.on('ready-to-show', () => {
    mainWindow.show();
    log.info('Main window ready');
  });

  // Open external links in default browser (security best practice)
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url);
    return { action: 'deny' };
  });

  // Load renderer (dev server or built files)
  _loadRenderer(mainWindow);

  return mainWindow;
}

/**
 * INTERNAL: Load the renderer process.
 *
 * In development: loads from Vite dev server (with DevTools)
 * In production: loads from built HTML file
 *
 * @param {BrowserWindow} window - The main window instance
 */
function _loadRenderer(window) {
  if (!app.isPackaged && process.env['ELECTRON_RENDERER_URL']) {
    // Development mode: load from Vite dev server
    window.loadURL(process.env['ELECTRON_RENDERER_URL']);
    window.webContents.openDevTools(); // Auto-open DevTools
    log.info('Loaded renderer from dev server');
  } else {
    // Production mode: load from built files
    window.loadFile(join(__dirname, '../renderer/index.html'));
    log.info('Loaded renderer from built files');
  }
}
