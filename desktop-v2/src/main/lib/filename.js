/**
 * AUPAT Filename Module
 *
 * ONE FUNCTION: Generate standardized filenames per AUPAT specification
 *
 * LILBITS Principle: One script = one function
 * This module handles filename generation for all media types.
 *
 * Filename Format:
 * - Without sub-location: {locuuid12}-{sha12}.{ext}
 * - With sub-location: {locuuid12}-{subuuid12}-{sha12}.{ext}
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

/**
 * Generate standardized filename for media files.
 *
 * Creates filenames following the AUPAT naming convention:
 * - Without sub-location: {locuuid12}-{sha12}.{ext}
 * - With sub-location: {locuuid12}-{subuuid12}-{sha12}.{ext}
 *
 * All UUIDs and SHA256 hashes should be provided as FULL values.
 * This function will extract the first 12 characters automatically.
 *
 * @param {string} mediaType - Type of media: 'img', 'vid', 'doc', 'map', or 'url'
 * @param {string} locUuid - Full location UUID (36 chars)
 * @param {string} sha256 - Full SHA256 hash (64 chars) - not used for URLs
 * @param {string} extension - File extension without dot (e.g., 'jpg', 'mp4', 'pdf')
 * @param {string|null} [subUuid=null] - Optional full sub-location UUID (36 chars)
 * @returns {string} Standardized filename
 * @throws {Error} If required parameters are invalid
 *
 * @example
 * // Image without sub-location
 * const filename = generateFilename(
 *   'img',
 *   'a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7',
 *   'f7e8d9c0b1a2f3e4d5c6b7a8e9f0d1c2b3a4e5f6d7c8b9a0e1f2d3c4b5a6e7f8d9c0',
 *   'jpg'
 * );
 * // Returns: 'a1b2c3d4e5f6-f7e8d9c0b1a2.jpg'
 *
 * @example
 * // Video with sub-location
 * const filename = generateFilename(
 *   'vid',
 *   'a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7',
 *   'f7e8d9c0b1a2f3e4d5c6b7a8e9f0d1c2b3a4e5f6d7c8b9a0e1f2d3c4b5a6e7f8d9c0',
 *   'mp4',
 *   'b2c3d4e5-f6a7-4890-b1c2-d3e4f5a6b7c8'
 * );
 * // Returns: 'a1b2c3d4e5f6-b2c3d4e5f6a7-f7e8d9c0b1a2.mp4'
 *
 * @example
 * // URL (no SHA256 needed)
 * const filename = generateFilename(
 *   'url',
 *   'a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7',
 *   null,  // URLs use UUID, not SHA256
 *   'html'
 * );
 * // Returns: 'a1b2c3d4e5f6-{urluuid12}.html'
 */
function generateFilename(mediaType, locUuid, sha256, extension, subUuid = null) {
  // Validate media type
  const validTypes = ['img', 'vid', 'doc', 'map', 'url'];
  if (!validTypes.includes(mediaType)) {
    throw new Error(`Invalid media type: ${mediaType}. Must be one of: ${validTypes.join(', ')}`);
  }

  // Validate location UUID
  if (!locUuid || typeof locUuid !== 'string') {
    throw new Error('Location UUID must be a non-empty string');
  }

  // Validate extension
  if (!extension || typeof extension !== 'string') {
    throw new Error('Extension must be a non-empty string');
  }

  // Extract first 12 characters from location UUID (remove dashes)
  const locUuid12 = _extractFirst12(locUuid);

  // For URLs, we generate a URL UUID instead of using SHA256
  if (mediaType === 'url') {
    // URLs use their own UUID (generated elsewhere)
    // For now, we'll use the SHA256 parameter as the URL UUID if provided
    const urlUuid12 = sha256 ? _extractFirst12(sha256) : 'placeholder12';

    if (subUuid) {
      const subUuid12 = _extractFirst12(subUuid);
      return `${locUuid12}-${subUuid12}-${urlUuid12}.${extension}`;
    }
    return `${locUuid12}-${urlUuid12}.${extension}`;
  }

  // Validate SHA256 for file-based media
  if (!sha256 || typeof sha256 !== 'string') {
    throw new Error('SHA256 hash must be a non-empty string for file-based media');
  }

  // Extract first 12 characters from SHA256
  const sha12 = _extractFirst12(sha256);

  // Build filename based on whether there's a sub-location
  if (subUuid) {
    // Format: {locuuid12}-{subuuid12}-{sha12}.{ext}
    const subUuid12 = _extractFirst12(subUuid);
    return `${locUuid12}-${subUuid12}-${sha12}.${extension}`;
  } else {
    // Format: {locuuid12}-{sha12}.{ext}
    return `${locUuid12}-${sha12}.${extension}`;
  }
}

/**
 * Generate location folder name.
 *
 * Format: {locshort}-{locuuid12}
 *
 * @param {string} locShort - Short name for location (user-provided)
 * @param {string} locUuid - Full location UUID (36 chars)
 * @returns {string} Location folder name
 *
 * @example
 * const folderName = generateLocationFolderName(
 *   'buffpsych',
 *   'a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7'
 * );
 * // Returns: 'buffpsych-a1b2c3d4e5f6'
 */
function generateLocationFolderName(locShort, locUuid) {
  if (!locShort || typeof locShort !== 'string') {
    throw new Error('Location short name must be a non-empty string');
  }

  if (!locUuid || typeof locUuid !== 'string') {
    throw new Error('Location UUID must be a non-empty string');
  }

  const locUuid12 = _extractFirst12(locUuid);
  return `${locShort}-${locUuid12}`;
}

/**
 * Generate media subfolder name within a location.
 *
 * Format: {media-type}-org-{locuuid12}
 * Examples: img-org-a1b2c3d4e5f6, vid-org-a1b2c3d4e5f6, doc-org-a1b2c3d4e5f6
 *
 * @param {string} mediaType - Type of media: 'img', 'vid', or 'doc'
 * @param {string} locUuid - Full location UUID (36 chars)
 * @returns {string} Media subfolder name
 *
 * @example
 * const folderName = generateMediaFolderName(
 *   'img',
 *   'a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7'
 * );
 * // Returns: 'img-org-a1b2c3d4e5f6'
 */
function generateMediaFolderName(mediaType, locUuid) {
  const validTypes = ['img', 'vid', 'doc'];
  if (!validTypes.includes(mediaType)) {
    throw new Error(`Invalid media type: ${mediaType}. Must be one of: ${validTypes.join(', ')}`);
  }

  if (!locUuid || typeof locUuid !== 'string') {
    throw new Error('Location UUID must be a non-empty string');
  }

  const locUuid12 = _extractFirst12(locUuid);
  return `${mediaType}-org-${locUuid12}`;
}

/**
 * INTERNAL: Extract first 12 alphanumeric characters from a string.
 *
 * Removes dashes and extracts first 12 characters.
 * Used for converting full UUIDs and SHA256 hashes to 12-char versions.
 *
 * @private
 * @param {string} str - String to extract from (UUID or SHA256)
 * @returns {string} First 12 alphanumeric characters (no dashes)
 *
 * @example
 * _extractFirst12('a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7')
 * // Returns: 'a1b2c3d4e5f6'
 */
function _extractFirst12(str) {
  if (!str || typeof str !== 'string') {
    throw new Error('Input must be a non-empty string');
  }

  // Remove dashes and take first 12 characters
  const clean = str.replace(/-/g, '');

  if (clean.length < 12) {
    throw new Error(`String too short: ${str} (need at least 12 chars after removing dashes)`);
  }

  return clean.substring(0, 12);
}

// Export functions
module.exports = {
  generateFilename,
  generateLocationFolderName,
  generateMediaFolderName
};
