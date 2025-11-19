/**
 * AUPAT Desktop v0.1.0 - Main Process Entry Point
 *
 * Pure Electron desktop application with direct SQLite access.
 * NO Flask, NO HTTP API - everything runs locally.
 *
 * Architecture (LILBITS Compliant):
 * - config-loader: Settings and configuration
 * - preflight: Health checks before startup
 * - window-manager: Window creation and security
 * - browser-init: Browser IPC handlers
 * - lifecycle: App lifecycle management
 * - error-handler: Crash recovery
 * - ipc-handlers: Database/API IPC handlers
 *
 * Security:
 * - contextIsolation: true
 * - nodeIntegration: false
 * - sandbox: true
 * - All IPC via preload script
 *
 * Version: 1.0.0 - LILBITS Refactor
 * Last Updated: 2025-11-19
 * LOC: ~60 lines (LILBITS compliant)
 */

import { app, dialog } from 'electron';
import log from 'electron-log';

// LILBITS modules (one function each)
import { initConfig } from './config-loader.js';
import { runPreflightChecks } from './preflight.js';
import { createMainWindow } from './window-manager.js';
import { initBrowserHandlers } from './browser-init.js';
import { registerLifecycleHandlers } from './lifecycle.js';
import { registerErrorHandlers } from './error-handler.js';
import { initializeHandlers } from './ipc-handlers.js';
import { clearCacheIfNeeded } from './cache-manager.js';

// Configure logging
log.transports.file.level = 'info';
log.info('='.repeat(60));
log.info('AUPAT v0.1.0 starting...');
log.info('LILBITS Architecture - One Script = One Function');
log.info('='.repeat(60));

// Application entry point
app.whenReady().then(async () => {
  // Set app user model id for Windows
  app.setAppUserModelId('com.abandonedupstate.app');

  try {
    // Step 1: Load configuration
    log.info('[1/7] Loading configuration...');
    const config = initConfig();

    // Step 2: Clear cache if needed (version upgrade)
    log.info('[2/7] Checking cache...');
    await clearCacheIfNeeded(config.store, config.version);

    // Step 3: Run preflight health checks
    log.info('[3/7] Running preflight checks...');
    const preflightResult = runPreflightChecks(config);
    if (!preflightResult.success) {
      _showPreflightError(preflightResult);
      app.quit();
      return;
    }

    // Step 4: Initialize database backend
    log.info('[4/7] Initializing database backend...');
    initializeHandlers(config.store);

    // Step 5: Initialize browser handlers
    log.info('[5/7] Initializing browser handlers...');
    const mainWindow = createMainWindow();
    initBrowserHandlers(mainWindow);

    // Step 6: Register lifecycle handlers
    log.info('[6/7] Registering lifecycle handlers...');
    registerLifecycleHandlers(createMainWindow);

    // Step 7: Register error handlers
    log.info('[7/7] Registering error handlers...');
    registerErrorHandlers();

    log.info('='.repeat(60));
    log.info('AUPAT v0.1.0 ready!');
    log.info(`Database: ${config.dbPath}`);
    log.info(`Archive: ${config.archiveRoot}`);
    log.info('='.repeat(60));
  } catch (error) {
    log.error('Fatal error during startup:', error);
    dialog.showErrorBox(
      'Startup Error',
      `AUPAT failed to start:\n\n${error.message}\n\nCheck the logs for details.`
    );
    app.quit();
  }
});

/**
 * INTERNAL: Show preflight error dialog and exit.
 *
 * Displays user-friendly error message with recovery instructions
 * when preflight checks fail.
 *
 * @param {Object} result - Preflight check result
 */
function _showPreflightError(result) {
  log.error('Preflight check failed:', result.error);

  dialog.showErrorBox(
    'Startup Error - Configuration Problem',
    `${result.error}\n\n${result.recovery}`
  );
}
