/**
 * AUPAT Browser Manager IPC Handlers
 *
 * ONE FUNCTION: Register IPC handlers for embedded browser feature
 *
 * LILBITS Principle: One script = one function
 * This module registers all IPC handlers for the embedded browser view
 * used for web archiving. Extracted from main index.js for separation of concerns.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import { ipcMain } from 'electron';
import { BrowserManager } from './browser-manager.js';
import log from 'electron-log';

// Module-level browser manager instance
let browserManager = null;

/**
 * Initialize browser manager and register IPC handlers.
 *
 * Sets up IPC handlers for browser operations:
 * - Create/destroy browser view
 * - Navigation (navigate, back, forward, reload)
 * - State management (bounds, cookies)
 * - URL/title tracking
 *
 * @param {BrowserWindow} mainWindow - The main application window
 */
export function initBrowserHandlers(mainWindow) {
  // Register all browser IPC handlers
  _registerCreateHandler(mainWindow);
  _registerNavigationHandlers();
  _registerStateHandlers();
  _registerCookieHandlers();
  _registerDestroyHandler();

  log.info('Browser IPC handlers registered');
}

/**
 * INTERNAL: Validate browser manager is initialized.
 *
 * Helper function to check if browser manager exists and is created.
 * Returns error object if validation fails, null if valid.
 *
 * @returns {Object|null} Error object or null
 */
function _validateBrowserManager() {
  if (!browserManager || !browserManager.isCreated()) {
    return { success: false, error: 'Browser not initialized' };
  }
  return null;
}

/**
 * INTERNAL: Register browser creation handler.
 */
function _registerCreateHandler(mainWindow) {
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
}

/**
 * INTERNAL: Register navigation handlers.
 */
function _registerNavigationHandlers() {
  ipcMain.handle('browser:navigate', async (event, url) => {
    try {
      const error = _validateBrowserManager();
      if (error) return error;

      browserManager.navigate(url);
      return { success: true };
    } catch (error) {
      log.error('Failed to navigate:', error);
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:goBack', async () => {
    try {
      const error = _validateBrowserManager();
      if (error) return error;

      browserManager.goBack();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:goForward', async () => {
    try {
      const error = _validateBrowserManager();
      if (error) return error;

      browserManager.goForward();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:reload', async () => {
    try {
      const error = _validateBrowserManager();
      if (error) return error;

      browserManager.reload();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
}

/**
 * INTERNAL: Register state management handlers.
 */
function _registerStateHandlers() {
  ipcMain.handle('browser:setBounds', async (event, bounds) => {
    try {
      const error = _validateBrowserManager();
      if (error) return error;

      browserManager.setBounds(bounds);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:getCurrentUrl', async () => {
    try {
      const error = _validateBrowserManager();
      if (error) return error;

      const url = browserManager.getCurrentUrl();
      return { success: true, data: url };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:getCurrentTitle', async () => {
    try {
      const error = _validateBrowserManager();
      if (error) return error;

      const title = browserManager.getCurrentTitle();
      return { success: true, data: title };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
}

/**
 * INTERNAL: Register cookie handlers.
 */
function _registerCookieHandlers() {
  ipcMain.handle('browser:getCookies', async (event, domain) => {
    try {
      const error = _validateBrowserManager();
      if (error) return error;

      const cookies = await browserManager.getCookies(domain);
      return { success: true, data: cookies };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('browser:exportCookies', async (event, domain) => {
    try {
      const error = _validateBrowserManager();
      if (error) return error;

      const cookieString = await browserManager.exportCookiesForArchiveBox(domain);
      return { success: true, data: cookieString };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
}

/**
 * INTERNAL: Register browser destruction handler.
 */
function _registerDestroyHandler() {
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
}
