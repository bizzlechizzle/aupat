/**
 * AUPAT Lifecycle Handlers
 *
 * ONE FUNCTION: Manage application lifecycle events
 *
 * LILBITS Principle: One script = one function
 * This module handles Electron app lifecycle events like activate
 * (macOS dock icon click) and window-all-closed (quit on non-macOS).
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import { app, BrowserWindow } from 'electron';
import log from 'electron-log';

/**
 * Register application lifecycle handlers.
 *
 * Handles:
 * - activate: Re-create window when macOS dock icon clicked
 * - window-all-closed: Quit app on non-macOS platforms
 *
 * @param {Function} createWindowFn - Function to create main window
 */
export function registerLifecycleHandlers(createWindowFn) {
  // macOS: Re-create window when dock icon is clicked and no windows open
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      log.info('Reactivating app (macOS dock click)');
      createWindowFn();
    }
  });

  // Quit when all windows are closed (except on macOS)
  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      log.info('All windows closed, quitting app');
      app.quit();
    }
  });

  log.info('Lifecycle handlers registered');
}
