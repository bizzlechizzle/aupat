/**
 * AUPAT Images Module
 *
 * ONE FUNCTION: Image retrieval operations
 *
 * LILBITS Principle: One script = one function
 * This module handles image data retrieval and file path resolution.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

const path = require('path');
const fs = require('fs');

/**
 * Get images by location UUID.
 *
 * Returns image records for a specific location with pagination support.
 * Includes path resolution for accessing image files in the archive.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} locUuid - Location UUID
 * @param {Object} options - Query options
 * @param {number} options.limit - Maximum results (default: 100)
 * @param {number} options.offset - Results offset (default: 0)
 * @param {string} options.orderBy - Order by clause (default: 'created_at DESC')
 * @returns {Array<Object>} Array of image objects
 *
 * @example
 * const images = getImagesByLocation(db, 'loc-uuid-123', {
 *   limit: 50,
 *   offset: 0,
 *   orderBy: 'created_at DESC'
 * });
 */
function getImagesByLocation(db, locUuid, options = {}) {
  if (!locUuid) {
    throw new Error('Location UUID is required');
  }

  const limit = options.limit || 100;
  const offset = options.offset || 0;
  const orderBy = options.orderBy || 'created_at DESC';

  const query = db.prepare(`
    SELECT
      img_uuid,
      loc_uuid,
      sub_uuid,
      img_sha,
      original_name,
      original_path,
      img_name,
      img_ext,
      img_path,
      created_at,
      verified
    FROM images
    WHERE loc_uuid = ?
    ORDER BY ${orderBy}
    LIMIT ? OFFSET ?
  `);

  return query.all(locUuid, limit, offset);
}

/**
 * Get single image by UUID.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} imgUuid - Image UUID
 * @returns {Object|null} Image object or null if not found
 *
 * @example
 * const image = getImage(db, 'img-uuid-123');
 * if (image) {
 *   console.log('Image found:', image.img_name);
 * }
 */
function getImage(db, imgUuid) {
  if (!imgUuid) {
    throw new Error('Image UUID is required');
  }

  const query = db.prepare(`
    SELECT
      img_uuid,
      loc_uuid,
      sub_uuid,
      img_sha,
      original_name,
      original_path,
      img_name,
      img_ext,
      img_path,
      created_at,
      verified
    FROM images
    WHERE img_uuid = ?
  `);

  return query.get(imgUuid);
}

/**
 * Get absolute file path for image.
 *
 * Returns the full path to the image file.
 * The img_path in database is already the full absolute path.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} imgUuid - Image UUID
 * @param {string} archiveRoot - Root archive directory (not used, kept for API compatibility)
 * @returns {Object} {success: boolean, path?: string, error?: string}
 *
 * @example
 * const result = getImagePath(db, 'img-uuid-123', '/archive/root');
 * if (result.success) {
 *   console.log('Image at:', result.path);
 * }
 */
function getImagePath(db, imgUuid, archiveRoot) {
  const image = getImage(db, imgUuid);

  if (!image) {
    return { success: false, error: 'Image not found' };
  }

  if (!image.img_path) {
    return { success: false, error: 'Image path not set in database' };
  }

  // img_path is already the full absolute path from import module
  const absolutePath = image.img_path;

  // Verify file exists
  if (!fs.existsSync(absolutePath)) {
    return {
      success: false,
      error: `Image file not found: ${absolutePath}`
    };
  }

  return {
    success: true,
    path: absolutePath,
    filename: image.img_name,
    extension: image.img_ext
  };
}

/**
 * Get image metadata.
 *
 * Returns image information including file details and verification status.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} imgUuid - Image UUID
 * @returns {Object|null} Image metadata or null if not found
 *
 * @example
 * const metadata = getImageMetadata(db, 'img-uuid-123');
 * if (metadata) {
 *   console.log('SHA:', metadata.img_sha);
 *   console.log('Verified:', metadata.verified);
 * }
 */
function getImageMetadata(db, imgUuid) {
  return getImage(db, imgUuid);
}

/**
 * Count images for a location.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} locUuid - Location UUID
 * @returns {number} Image count
 *
 * @example
 * const count = countImagesByLocation(db, 'loc-uuid-123');
 * console.log(`Location has ${count} images`);
 */
function countImagesByLocation(db, locUuid) {
  if (!locUuid) {
    throw new Error('Location UUID is required');
  }

  const query = db.prepare(`
    SELECT COUNT(*) as count
    FROM images
    WHERE loc_uuid = ?
  `);

  const result = query.get(locUuid);
  return result.count;
}

// Export functions
module.exports = {
  getImagesByLocation,
  getImage,
  getImagePath,
  getImageMetadata,
  countImagesByLocation
};
