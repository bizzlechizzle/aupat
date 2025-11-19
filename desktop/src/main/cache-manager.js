/**
 * AUPAT Cache Manager
 *
 * ONE FUNCTION: Manage application cache clearing
 *
 * LILBITS Principle: One script = one function
 * This module handles conditional cache clearing - only clears when
 * app version changes, avoiding unnecessary slowdown on every startup.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import { session } from 'electron';
import log from 'electron-log';

/**
 * Clear application cache if version has changed.
 *
 * Checks stored lastClearedVersion against current app version.
 * Only clears cache on version upgrade to improve startup performance.
 *
 * @param {Store} store - Electron-store instance
 * @param {string} currentVersion - Current app version
 */
export async function clearCacheIfNeeded(store, currentVersion) {
  const lastClearedVersion = store.get('lastClearedVersion');

  if (lastClearedVersion !== currentVersion) {
    log.info(`Version changed (${lastClearedVersion} → ${currentVersion}), clearing cache...`);

    try {
      await session.defaultSession.clearCache();
      store.set('lastClearedVersion', currentVersion);
      log.info('✓ Cache cleared successfully');
    } catch (error) {
      log.warn('Failed to clear cache:', error);
    }
  } else {
    log.info(`✓ Cache up to date (v${currentVersion})`);
  }
}
