/**
 * Abandoned Upstate - Auto-Update Module
 *
 * Handles automatic updates via electron-updater.
 * Checks GitHub releases for new versions.
 *
 * Features:
 * - Automatic update checking (every 4 hours + on startup)
 * - User-controlled download (doesn't auto-download)
 * - Progress reporting
 * - Install on restart
 *
 * Security:
 * - Only downloads from official GitHub releases
 * - Verifies signatures (macOS code signing)
 */

import pkg from 'electron-updater';
const { autoUpdater } = pkg;
import log from 'electron-log';

/**
 * Initialize auto-updater
 * @param {BrowserWindow} mainWindow - Main application window
 */
export function initAutoUpdater(mainWindow) {
  // Configure logging
  autoUpdater.logger = log;
  autoUpdater.logger.transports.file.level = 'info';

  // Don't auto-download updates (ask user first)
  autoUpdater.autoDownload = false;

  // Don't auto-install after download (wait for user)
  autoUpdater.autoInstallOnAppQuit = false;

  log.info('Auto-updater initialized');
  log.info(`Current version: ${autoUpdater.currentVersion.version}`);

  // Check for updates every 4 hours
  setInterval(() => {
    log.info('Periodic update check...');
    autoUpdater.checkForUpdates();
  }, 4 * 60 * 60 * 1000);

  // Check on startup (after 10 seconds to avoid overwhelming on launch)
  setTimeout(() => {
    log.info('Startup update check...');
    autoUpdater.checkForUpdates();
  }, 10000);

  // Event: Update available
  autoUpdater.on('update-available', (info) => {
    log.info('Update available:', {
      version: info.version,
      releaseDate: info.releaseDate,
      files: info.files.map(f => f.url)
    });

    // Notify renderer process
    mainWindow.webContents.send('update-available', {
      version: info.version,
      releaseDate: info.releaseDate,
      releaseNotes: info.releaseNotes
    });
  });

  // Event: No update available
  autoUpdater.on('update-not-available', (info) => {
    log.info('No update available. Current version is latest:', info.version);
  });

  // Event: Update downloaded and ready
  autoUpdater.on('update-downloaded', (info) => {
    log.info('Update downloaded and ready to install:', {
      version: info.version,
      files: info.files.map(f => ({ name: f.name, size: f.size }))
    });

    // Notify renderer process
    mainWindow.webContents.send('update-downloaded', {
      version: info.version
    });
  });

  // Event: Download progress
  autoUpdater.on('download-progress', (progress) => {
    log.info(`Download progress: ${progress.percent.toFixed(2)}%`);

    // Notify renderer process
    mainWindow.webContents.send('update-progress', {
      percent: Math.round(progress.percent),
      transferred: progress.transferred,
      total: progress.total,
      bytesPerSecond: progress.bytesPerSecond
    });
  });

  // Event: Error
  autoUpdater.on('error', (error) => {
    log.error('Update error:', error);

    // Notify renderer process
    mainWindow.webContents.send('update-error', {
      message: error.message,
      code: error.code || 'UNKNOWN_ERROR'
    });
  });

  // Event: Checking for updates
  autoUpdater.on('checking-for-update', () => {
    log.info('Checking for updates...');
  });
}

/**
 * Register IPC handlers for update actions
 * @param {IpcMain} ipcMain - Electron IPC main instance
 */
export function registerUpdateHandlers(ipcMain) {
  /**
   * Manually check for updates
   */
  ipcMain.handle('update:check', async () => {
    try {
      log.info('Manual update check requested');
      const result = await autoUpdater.checkForUpdates();
      return {
        success: true,
        updateInfo: result ? result.updateInfo : null
      };
    } catch (error) {
      log.error('Update check failed:', error);
      return {
        success: false,
        error: error.message
      };
    }
  });

  /**
   * Start downloading update
   */
  ipcMain.handle('update:download', async () => {
    try {
      log.info('Update download requested');
      await autoUpdater.downloadUpdate();
      return { success: true };
    } catch (error) {
      log.error('Update download failed:', error);
      return {
        success: false,
        error: error.message
      };
    }
  });

  /**
   * Install update and restart app
   * @param {boolean} isSilent - Silent install (no prompts)
   * @param {boolean} isForceRunAfter - Force run after install
   */
  ipcMain.handle('update:install', async () => {
    try {
      log.info('Update install requested - app will restart');
      // quitAndInstall(isSilent, isForceRunAfter)
      // false = show prompts, true = run app after install
      autoUpdater.quitAndInstall(false, true);
      return { success: true };
    } catch (error) {
      log.error('Update install failed:', error);
      return {
        success: false,
        error: error.message
      };
    }
  });

  /**
   * Get current version info
   */
  ipcMain.handle('update:version', async () => {
    return {
      success: true,
      currentVersion: autoUpdater.currentVersion.version,
      appVersion: require('../../../package.json').version
    };
  });

  log.info('Update IPC handlers registered');
}
