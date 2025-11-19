/**
 * AUPAT Folders Module
 *
 * ONE FUNCTION: Create archive folder structure
 *
 * LILBITS Principle: One script = one function
 * This module handles creation of the archive folder hierarchy.
 *
 * Folder Structure:
 * Archive/
 * ├── {State-Type}/               # Example: "NY-Hospital"
 * │   └── {locshort-locuuid12}/   # Example: "buffpsych-a1b2c3d4e5f6"
 * │       ├── doc-org-locuuid12/
 * │       ├── img-org-locuuid12/
 * │       └── vid-org-locuuid12/
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

const fs = require('fs-extra');
const path = require('path');
const { generateLocationFolderName, generateMediaFolderName } = require('../lib/filename');
const { normalizeLocationType, normalizeStateCode } = require('../lib/normalize');

/**
 * Create complete folder structure for a location.
 *
 * Creates the full hierarchy:
 * 1. Archive root (if doesn't exist)
 * 2. State-Type folder
 * 3. Location folder
 * 4. Media subfolders (img, vid, doc)
 *
 * @param {string} archiveRoot - Path to archive root directory
 * @param {string} state - State code (e.g., "ny", "ca")
 * @param {string} locationType - Location type (e.g., "hospital", "industrial")
 * @param {string} locShort - Short name for location (e.g., "buffpsych")
 * @param {string} locUuid - Full location UUID (36 chars)
 * @returns {Object} Object with created folder paths
 * @throws {Error} If folder creation fails
 *
 * @example
 * const folders = createLocationFolders(
 *   '/data/aupat/archive',
 *   'ny',
 *   'hospital',
 *   'buffpsych',
 *   'a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7'
 * );
 * // Returns:
 * // {
 * //   stateTypeFolder: '/data/aupat/archive/NY-Hospital',
 * //   locationFolder: '/data/aupat/archive/NY-Hospital/buffpsych-a1b2c3d4e5f6',
 * //   imgFolder: '/data/aupat/archive/NY-Hospital/buffpsych-a1b2c3d4e5f6/img-org-a1b2c3d4e5f6',
 * //   vidFolder: '/data/aupat/archive/NY-Hospital/buffpsych-a1b2c3d4e5f6/vid-org-a1b2c3d4e5f6',
 * //   docFolder: '/data/aupat/archive/NY-Hospital/buffpsych-a1b2c3d4e5f6/doc-org-a1b2c3d4e5f6'
 * // }
 */
function createLocationFolders(archiveRoot, state, locationType, locShort, locUuid) {
  // Validate inputs
  if (!archiveRoot || typeof archiveRoot !== 'string') {
    throw new Error('Archive root must be a non-empty string');
  }

  if (!state || !locationType || !locShort || !locUuid) {
    throw new Error('Missing required parameters: state, locationType, locShort, or locUuid');
  }

  try {
    // Normalize state and type
    const stateNorm = normalizeStateCode(state).toUpperCase();  // NY
    const typeNorm = normalizeLocationType(locationType);       // hospital
    const typeCapitalized = _capitalizeFirst(typeNorm);         // Hospital

    // Generate folder names
    const stateTypeFolderName = `${stateNorm}-${typeCapitalized}`;  // NY-Hospital
    const locationFolderName = generateLocationFolderName(locShort, locUuid);  // buffpsych-a1b2c3d4e5f6
    const imgFolderName = generateMediaFolderName('img', locUuid);  // img-org-a1b2c3d4e5f6
    const vidFolderName = generateMediaFolderName('vid', locUuid);  // vid-org-a1b2c3d4e5f6
    const docFolderName = generateMediaFolderName('doc', locUuid);  // doc-org-a1b2c3d4e5f6

    // Build full paths
    const stateTypeFolder = path.join(archiveRoot, stateTypeFolderName);
    const locationFolder = path.join(stateTypeFolder, locationFolderName);
    const imgFolder = path.join(locationFolder, imgFolderName);
    const vidFolder = path.join(locationFolder, vidFolderName);
    const docFolder = path.join(locationFolder, docFolderName);

    // Create folders (recursive, no error if exists)
    fs.ensureDirSync(archiveRoot);
    fs.ensureDirSync(stateTypeFolder);
    fs.ensureDirSync(locationFolder);
    fs.ensureDirSync(imgFolder);
    fs.ensureDirSync(vidFolder);
    fs.ensureDirSync(docFolder);

    console.log(`Created folder structure for: ${locationFolderName}`);

    return {
      stateTypeFolder,
      locationFolder,
      imgFolder,
      vidFolder,
      docFolder
    };

  } catch (error) {
    throw new Error(`Failed to create folder structure: ${error.message}`);
  }
}

/**
 * Get path to media subfolder for a location.
 *
 * Returns the path to the img/vid/doc folder within a location.
 * Does NOT create the folder (use createLocationFolders for that).
 *
 * @param {string} archiveRoot - Path to archive root directory
 * @param {string} state - State code
 * @param {string} locationType - Location type
 * @param {string} locShort - Short name for location
 * @param {string} locUuid - Full location UUID
 * @param {string} mediaType - Media type: 'img', 'vid', or 'doc'
 * @returns {string} Path to media subfolder
 *
 * @example
 * const imgPath = getMediaFolderPath(
 *   '/data/aupat/archive',
 *   'ny',
 *   'hospital',
 *   'buffpsych',
 *   'a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7',
 *   'img'
 * );
 * // Returns: '/data/aupat/archive/NY-Hospital/buffpsych-a1b2c3d4e5f6/img-org-a1b2c3d4e5f6'
 */
function getMediaFolderPath(archiveRoot, state, locationType, locShort, locUuid, mediaType) {
  const folders = _buildFolderPaths(archiveRoot, state, locationType, locShort, locUuid);

  switch (mediaType) {
    case 'img':
      return folders.imgFolder;
    case 'vid':
      return folders.vidFolder;
    case 'doc':
      return folders.docFolder;
    default:
      throw new Error(`Invalid media type: ${mediaType}. Must be 'img', 'vid', or 'doc'`);
  }
}

/**
 * Check if location folders exist.
 *
 * @param {string} archiveRoot - Path to archive root directory
 * @param {string} state - State code
 * @param {string} locationType - Location type
 * @param {string} locShort - Short name for location
 * @param {string} locUuid - Full location UUID
 * @returns {Object} Object with existence flags for each folder
 *
 * @example
 * const exists = locationFoldersExist(...);
 * // Returns: {locationFolder: true, imgFolder: true, vidFolder: true, docFolder: true}
 */
function locationFoldersExist(archiveRoot, state, locationType, locShort, locUuid) {
  const folders = _buildFolderPaths(archiveRoot, state, locationType, locShort, locUuid);

  return {
    locationFolder: fs.existsSync(folders.locationFolder),
    imgFolder: fs.existsSync(folders.imgFolder),
    vidFolder: fs.existsSync(folders.vidFolder),
    docFolder: fs.existsSync(folders.docFolder)
  };
}

/**
 * INTERNAL: Build folder paths without creating them.
 *
 * @private
 * @param {string} archiveRoot - Archive root path
 * @param {string} state - State code
 * @param {string} locationType - Location type
 * @param {string} locShort - Short name
 * @param {string} locUuid - Full UUID
 * @returns {Object} Object with all folder paths
 */
function _buildFolderPaths(archiveRoot, state, locationType, locShort, locUuid) {
  // Normalize
  const stateNorm = normalizeStateCode(state).toUpperCase();
  const typeNorm = normalizeLocationType(locationType);
  const typeCapitalized = _capitalizeFirst(typeNorm);

  // Generate names
  const stateTypeFolderName = `${stateNorm}-${typeCapitalized}`;
  const locationFolderName = generateLocationFolderName(locShort, locUuid);
  const imgFolderName = generateMediaFolderName('img', locUuid);
  const vidFolderName = generateMediaFolderName('vid', locUuid);
  const docFolderName = generateMediaFolderName('doc', locUuid);

  // Build paths
  const stateTypeFolder = path.join(archiveRoot, stateTypeFolderName);
  const locationFolder = path.join(stateTypeFolder, locationFolderName);
  const imgFolder = path.join(locationFolder, imgFolderName);
  const vidFolder = path.join(locationFolder, vidFolderName);
  const docFolder = path.join(locationFolder, docFolderName);

  return {
    stateTypeFolder,
    locationFolder,
    imgFolder,
    vidFolder,
    docFolder
  };
}

/**
 * INTERNAL: Capitalize first letter of string.
 *
 * @private
 * @param {string} str - String to capitalize
 * @returns {string} String with first letter capitalized
 */
function _capitalizeFirst(str) {
  if (!str || typeof str !== 'string') return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// Export functions
module.exports = {
  createLocationFolders,
  getMediaFolderPath,
  locationFoldersExist
};
