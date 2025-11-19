/**
 * AUPAT Import Module
 *
 * ONE FUNCTION: Import files into archive
 *
 * LILBITS Principle: One script = one function
 * This module handles the complete file import workflow.
 *
 * Import Process (v0.1.0 spec):
 * 1. Validate file (exists, determine type)
 * 2. Check for duplicates (SHA256 lookup in database)
 * 3. Generate hash/UUID
 * 4. Create folder structure
 * 5. Copy file to archive with standardized name
 * 6. Insert database record
 * 7. Verify file integrity (re-hash)
 * 8. Delete source (if configured)
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import fs from 'fs-extra';
import path from 'path';
import { calculateSHA256  } from '../lib/hash';
import { generateUUID  } from '../lib/uuid';
import { generateFilename  } from '../lib/filename';
import { determineMediaType  } from '../lib/validate';
import { normalizeDatetime, normalizeExtension  } from '../lib/normalize';
import { createLocationFolders  } from './folders';

/**
 * Import file into AUPAT archive.
 *
 * Complete workflow with validation, deduplication, and verification.
 * Atomic operation: if any step fails, rollback occurs.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} filePath - Source file path
 * @param {Object} locationData - Location information
 * @param {string} archiveRoot - Archive root directory
 * @param {Object} [options={}] - Import options
 * @returns {Object} Result object with success status
 * @throws {Error} If import fails
 *
 * @example
 * const result = await importFile(db, '/path/to/photo.jpg', {
 *   locUuid: 'a1b2c3d4-e5f6-...',
 *   locShort: 'buffpsych',
 *   state: 'ny',
 *   type: 'hospital'
 * }, '/data/aupat/archive', {
 *   deleteSource: false
 * });
 * // Returns: {success: true, fileUuid: '...', mediaType: 'img', ...}
 */
async function importFile(db, filePath, locationData, archiveRoot, options = {}) {
  const deleteSource = options.deleteSource || false;
  let targetPath = null;

  try {
    // STEP 1: Validate file
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const stats = fs.statSync(filePath);
    if (!stats.isFile()) {
      throw new Error(`Path is not a file: ${filePath}`);
    }

    // Determine media type
    const mediaType = determineMediaType(filePath);
    const extension = normalizeExtension(path.extname(filePath));

    // Get original file info
    const originalName = path.basename(filePath);
    const originalPath = path.resolve(filePath);

    console.log(`Importing ${mediaType}: ${originalName}`);

    // STEP 2: Generate hash and check for duplicates
    const fileHash = await calculateSHA256(filePath);
    const hash12 = fileHash.substring(0, 12);

    const duplicate = _checkDuplicate(db, hash12, mediaType);
    if (duplicate) {
      throw new Error(
        `Duplicate file exists: ${duplicate.name} in location ${duplicate.loc_uuid}`
      );
    }

    // STEP 3: Generate UUID
    const tableMap = {
      'img': 'images',
      'vid': 'videos',
      'doc': 'documents',
      'map': 'maps'
    };
    const table = tableMap[mediaType] || 'documents';
    const uuidField = `${mediaType}_uuid`;

    const fileUuid = generateUUID(db, table, uuidField);

    // STEP 4: Create folder structure
    const folders = createLocationFolders(
      archiveRoot,
      locationData.state,
      locationData.type,
      locationData.locShort,
      locationData.locUuid
    );

    // Get target folder
    const folderMap = {
      'img': folders.imgFolder,
      'vid': folders.vidFolder,
      'doc': folders.docFolder,
      'map': folders.docFolder  // Maps go to doc folder for v0.1.0
    };
    const targetFolder = folderMap[mediaType];

    // STEP 5: Generate filename and copy file
    const newFilename = generateFilename(
      mediaType,
      locationData.locUuid,
      fileHash,
      extension,
      locationData.subUuid || null
    );

    targetPath = path.join(targetFolder, newFilename);

    // Copy with metadata preservation
    await fs.copy(filePath, targetPath, { preserveTimestamps: true });

    console.log(`Copied to: ${targetPath}`);

    // STEP 6: Insert database record
    const timestamp = normalizeDatetime(null);

    const fieldMap = {
      'img': 'img',
      'vid': 'vid',
      'doc': 'doc',
      'map': 'map'
    };
    const prefix = fieldMap[mediaType] || 'doc';

    const insert = db.prepare(`
      INSERT INTO ${table} (
        ${prefix}_uuid, loc_uuid, sub_uuid, ${prefix}_sha,
        original_name, original_path, ${prefix}_name, ${prefix}_ext,
        ${prefix}_path, created_at, verified
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    try {
      insert.run(
        fileUuid,
        locationData.locUuid,
        locationData.subUuid || null,
        fileHash,
        originalName,
        originalPath,
        newFilename,
        extension,
        targetPath,
        timestamp,
        0  // Not verified yet
      );
    } catch (dbError) {
      // Rollback: delete copied file
      if (fs.existsSync(targetPath)) {
        fs.unlinkSync(targetPath);
      }
      throw new Error(`Database insert failed: ${dbError.message}`);
    }

    // STEP 7: Verify file integrity
    const verifyHash = await calculateSHA256(targetPath);
    if (verifyHash !== fileHash) {
      // Rollback: delete file and database record
      fs.unlinkSync(targetPath);
      db.prepare(`DELETE FROM ${table} WHERE ${prefix}_uuid = ?`).run(fileUuid);
      throw new Error('Verification failed: hash mismatch');
    }

    // Update verified flag
    db.prepare(`UPDATE ${table} SET verified = 1 WHERE ${prefix}_uuid = ?`).run(fileUuid);

    console.log(`Verified: ${newFilename}`);

    // STEP 8: Delete source (if configured)
    if (deleteSource) {
      try {
        fs.unlinkSync(filePath);
        console.log(`Deleted source: ${filePath}`);
      } catch (deleteError) {
        // Don't fail import if source deletion fails
        console.warn(`Could not delete source: ${deleteError.message}`);
      }
    }

    return {
      success: true,
      fileUuid,
      mediaType,
      fileName: newFilename,
      filePath: targetPath,
      originalName,
      verified: true
    };

  } catch (error) {
    // Cleanup on failure
    if (targetPath && fs.existsSync(targetPath)) {
      try {
        fs.unlinkSync(targetPath);
      } catch (cleanupError) {
        console.error(`Cleanup failed: ${cleanupError.message}`);
      }
    }

    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * INTERNAL: Check if file already exists in database (by SHA256 hash).
 *
 * @private
 * @param {Object} db - Database instance
 * @param {string} hash12 - First 12 characters of SHA256
 * @param {string} mediaType - Media type (img, vid, doc, map)
 * @returns {Object|null} Duplicate file info, or null if not found
 */
function _checkDuplicate(db, hash12, mediaType) {
  const tableMap = {
    'img': 'images',
    'vid': 'videos',
    'doc': 'documents',
    'map': 'maps'
  };
  const table = tableMap[mediaType] || 'documents';
  const prefix = mediaType;

  const query = db.prepare(`
    SELECT ${prefix}_uuid, ${prefix}_name, loc_uuid
    FROM ${table}
    WHERE SUBSTR(${prefix}_sha, 1, 12) = ?
    LIMIT 1
  `);

  const result = query.get(hash12);

  if (result) {
    return {
      uuid: result[`${prefix}_uuid`],
      name: result[`${prefix}_name`],
      loc_uuid: result.loc_uuid
    };
  }

  return null;
}

// Export function
export {
  importFile
};
