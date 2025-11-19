/**
 * AUPAT Preflight Checks
 *
 * ONE FUNCTION: Validate environment before app starts
 *
 * LILBITS Principle: One script = one function
 * This module performs health checks on database paths, archive directories,
 * and file system permissions before initializing the application.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import { dirname } from 'path';
import fs from 'fs';
import log from 'electron-log';

/**
 * Perform preflight health checks before app initialization.
 *
 * Validates:
 * - Database path is writable
 * - Archive root is writable
 * - Required directories can be created
 *
 * @param {Object} config - Configuration object
 * @param {string} config.dbPath - Database file path
 * @param {string} config.archiveRoot - Archive root directory
 * @returns {Object} Result object
 * @returns {boolean} result.success - True if all checks passed
 * @returns {string} [result.error] - Error message if checks failed
 * @returns {string} [result.recovery] - User-friendly recovery instructions
 */
export function runPreflightChecks(config) {
  log.info('Running preflight checks...');

  // Check 1: Database directory writable
  const dbCheck = _checkDatabasePath(config.dbPath);
  if (!dbCheck.success) {
    return dbCheck;
  }

  // Check 2: Archive directory writable
  const archiveCheck = _checkArchivePath(config.archiveRoot);
  if (!archiveCheck.success) {
    return archiveCheck;
  }

  log.info('✓ All preflight checks passed');
  return { success: true };
}

/**
 * INTERNAL: Check if database path is accessible and writable.
 *
 * Creates database directory if it doesn't exist, then tests
 * write permissions.
 *
 * @param {string} dbPath - Database file path
 * @returns {Object} Check result
 */
function _checkDatabasePath(dbPath) {
  const dbDir = dirname(dbPath);

  try {
    // Create directory if it doesn't exist
    if (!fs.existsSync(dbDir)) {
      fs.mkdirSync(dbDir, { recursive: true });
      log.info(`Created database directory: ${dbDir}`);
    }

    // Test write access
    fs.accessSync(dbDir, fs.constants.W_OK);
    log.info('✓ Database directory writable');

    return { success: true };
  } catch (error) {
    log.error('✗ Database directory not writable:', error);

    return {
      success: false,
      error: `Cannot write to database directory: ${dbDir}`,
      recovery: `
Fix: Check folder permissions
1. Open terminal/command prompt
2. Run: chmod 755 "${dbDir}" (Mac/Linux)
   or: Right-click folder → Properties → Security (Windows)
3. Restart the application

If problem persists, change database location in Settings.
      `.trim()
    };
  }
}

/**
 * INTERNAL: Check if archive root is accessible and writable.
 *
 * Creates archive directory if it doesn't exist, then tests
 * write permissions.
 *
 * @param {string} archiveRoot - Archive root directory
 * @returns {Object} Check result
 */
function _checkArchivePath(archiveRoot) {
  try {
    // Create directory if it doesn't exist
    if (!fs.existsSync(archiveRoot)) {
      fs.mkdirSync(archiveRoot, { recursive: true });
      log.info(`Created archive directory: ${archiveRoot}`);
    }

    // Test write access
    fs.accessSync(archiveRoot, fs.constants.W_OK);
    log.info('✓ Archive directory writable');

    return { success: true };
  } catch (error) {
    log.error('✗ Archive directory not writable:', error);

    return {
      success: false,
      error: `Cannot write to archive directory: ${archiveRoot}`,
      recovery: `
Fix: Check folder permissions
1. Open terminal/command prompt
2. Run: chmod 755 "${archiveRoot}" (Mac/Linux)
   or: Right-click folder → Properties → Security (Windows)
3. Restart the application

If problem persists, change archive location in Settings.
      `.trim()
    };
  }
}
