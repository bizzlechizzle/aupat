/**
 * AUPAT Error Handler
 *
 * ONE FUNCTION: Handle uncaught errors with user-friendly recovery
 *
 * LILBITS Principle: One script = one function
 * This module registers global error handlers for uncaught exceptions
 * and unhandled promise rejections, providing user-facing dialogs
 * with recovery instructions instead of cryptic crashes.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import { app, dialog } from 'electron';
import log from 'electron-log';

/**
 * Register global error handlers.
 *
 * Handles:
 * - Uncaught exceptions: Shows error dialog, offers restart
 * - Unhandled promise rejections: Logs and shows dialog
 *
 * All errors are logged to file for debugging.
 */
export function registerErrorHandlers() {
  process.on('uncaughtException', _handleUncaughtException);
  process.on('unhandledRejection', _handleUnhandledRejection);

  log.info('Error handlers registered');
}

/**
 * INTERNAL: Handle uncaught exceptions.
 *
 * Shows user-friendly error dialog with:
 * - Clear error message
 * - Recovery instructions
 * - Option to restart or quit
 *
 * @param {Error} error - The uncaught exception
 */
function _handleUncaughtException(error) {
  log.error('Uncaught exception:', error);
  log.error('Stack trace:', error.stack);

  const errorMessage = _formatErrorForUser(error);

  const choice = dialog.showMessageBoxSync({
    type: 'error',
    title: 'Application Error',
    message: 'AUPAT encountered an unexpected error',
    detail: errorMessage,
    buttons: ['Restart', 'View Logs', 'Quit'],
    defaultId: 0,
    cancelId: 2
  });

  switch (choice) {
    case 0: // Restart
      log.info('User chose to restart after error');
      app.relaunch();
      app.quit();
      break;
    case 1: // View Logs
      log.info('User chose to view logs');
      _showLogsLocation();
      break;
    case 2: // Quit
      log.info('User chose to quit after error');
      app.quit();
      break;
  }
}

/**
 * INTERNAL: Handle unhandled promise rejections.
 *
 * Logs the rejection and shows a warning dialog if the app is ready.
 *
 * @param {*} reason - Rejection reason
 * @param {Promise} promise - The rejected promise
 */
function _handleUnhandledRejection(reason, promise) {
  log.error('Unhandled promise rejection at:', promise);
  log.error('Rejection reason:', reason);

  // Only show dialog if app is ready (avoid startup crashes)
  if (app.isReady()) {
    dialog.showMessageBox({
      type: 'warning',
      title: 'Background Error',
      message: 'A background operation failed',
      detail: `An error occurred in a background operation:\n\n${reason}\n\nThe app will continue running, but some features may not work correctly. Check the logs for details.`,
      buttons: ['OK', 'View Logs']
    }).then((result) => {
      if (result.response === 1) {
        _showLogsLocation();
      }
    });
  }
}

/**
 * INTERNAL: Format error for user-friendly display.
 *
 * Converts technical error messages into user-understandable text
 * with recovery instructions.
 *
 * @param {Error} error - The error to format
 * @returns {string} User-friendly error message
 */
function _formatErrorForUser(error) {
  const message = error.message || 'Unknown error';

  // Database errors
  if (message.includes('SQLITE') || message.includes('database')) {
    return `Database Error: ${message}

This usually happens when:
- Database file is corrupted
- Insufficient disk space
- Database file is locked by another process

Try:
1. Restart the application
2. Check if another copy of AUPAT is running
3. Verify disk space available (need at least 100MB)
4. If issue persists, delete database and restart (data will be lost)

Log location: ${log.transports.file.getFile().path}`;
  }

  // File system errors
  if (message.includes('EACCES') || message.includes('permission')) {
    return `Permission Error: ${message}

The application cannot access a required file or folder.

Try:
1. Close the application
2. Check folder permissions (need read/write access)
3. On Mac/Linux: Run 'chmod -R 755' on the app data folder
4. On Windows: Right-click folder → Properties → Security → Full Control
5. Restart the application

Log location: ${log.transports.file.getFile().path}`;
  }

  // Generic error
  return `${message}

An unexpected error occurred. This should not happen.

Please:
1. Try restarting the application
2. If problem persists, check the logs
3. Report this issue with the log file

Log location: ${log.transports.file.getFile().path}`;
}

/**
 * INTERNAL: Show logs file location to user.
 *
 * Opens a dialog showing where log files are stored.
 */
function _showLogsLocation() {
  const logPath = log.transports.file.getFile().path;

  dialog.showMessageBox({
    type: 'info',
    title: 'Log File Location',
    message: 'Log files are stored at:',
    detail: logPath,
    buttons: ['OK', 'Open Folder']
  }).then((result) => {
    if (result.response === 1) {
      // Open folder in file manager
      const { shell } = require('electron');
      const { dirname } = require('path');
      shell.showItemInFolder(logPath);
    }
  });
}
