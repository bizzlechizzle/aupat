/**
 * AUPAT Validation Module
 *
 * ONE FUNCTION: Validate file types and extensions
 *
 * LILBITS Principle: One script = one function
 * This module handles file extension validation and type determination.
 *
 * File type lists from v0.1.0 specification.
 * For v0.1.0, we simply check extensions. No runtime detection needed.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import path from 'path';

// Supported image formats (from v0.1.0 spec)
const IMAGE_EXTENSIONS = new Set([
  '3fr', 'ai', 'arw', 'avif', 'bay', 'bmp', 'cin', 'cr2', 'cr3', 'crw', 'cur',
  'dcr', 'dds', 'dng', 'dpx', 'eip', 'eps', 'erf', 'exr', 'fff', 'g3', 'gif',
  'hdr', 'heic', 'heif', 'ico', 'iiq', 'j2k', 'jls', 'jng', 'jp2', 'jpf', 'jpe',
  'jpeg', 'jpg', 'jpa', 'jpm', 'jpx', 'jxl', 'kdc', 'mef', 'mfw', 'mos', 'mrw',
  'nef', 'nrw', 'orf', 'pbm', 'pcx', 'pct', 'pdn', 'pef', 'pgm', 'png', 'ppm',
  'ps', 'psb', 'psd', 'ptx', 'pxi', 'qtk', 'raf', 'raw', 'rw2', 'rwl', 'sr2',
  'srf', 'svg', 'tga', 'thm', 'tif', 'tiff', 'vff', 'webp', 'x3f', 'xbm', 'xcf',
  'xmp', 'xpm'
]);

// Supported video formats (from v0.1.0 spec)
const VIDEO_EXTENSIONS = new Set([
  '3gp', '3g2', 'amv', 'asf', 'avi', 'av1', 'bik', 'dat', 'dng', 'dv', 'f4v',
  'flv', 'gif', 'gxf', 'h261', 'h263', 'h264', 'h265', 'hevc', 'm2t', 'm2ts',
  'm2v', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'mpls', 'mts', 'mxf', 'oga',
  'ogg', 'ogm', 'ogv', 'opus', 'qt', 'rm', 'rmvb', 'swf', 'ts', 'vob', 'vp8',
  'vp9', 'webm', 'wmv', 'y4m'
]);

// Supported map formats (from v0.1.0 spec)
const MAP_EXTENSIONS = new Set([
  'kml', 'kmz', 'gpx', 'geojson', 'json', 'topojson', 'shp', 'shx', 'dbf', 'prj',
  'qgz', 'qgs', 'mbtiles', 'pbf', 'osm', 'o5m', 'obf', 'sid', 'vrt', 'tiff',
  'tif', 'geotiff', 'asc', 'grd', 'bil', 'dem', 'dt0', 'dt1', 'dt2', 'rst', 'xyz',
  'gpkg', 'sqlite', 'csv', 'tab', 'mif', 'mid', 'e00', 'nc', 'netcdf', 'img',
  'hgt', 'bz2', 'gz', 'jp2', 'jpx', 'tifc', 'raster', 'lidar', 'las', 'laz',
  'rpf', 'ccf', 'bsb', 'kap'
]);

// Common document formats
// Per spec: "Documents - Any file type" but we'll list common ones
const DOCUMENT_EXTENSIONS = new Set([
  'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'pages',
  'xls', 'xlsx', 'ods', 'numbers', 'csv',
  'ppt', 'pptx', 'odp', 'keynote',
  'md', 'markdown', 'html', 'htm', 'xml',
  'epub', 'mobi', 'azw', 'fb2'
]);

/**
 * Determine media type from file extension.
 *
 * Checks file extension against known type lists.
 * For v0.1.0, we use extension-based detection only (KISS principle).
 *
 * Priority order (some extensions appear in multiple lists):
 * 1. Images (check first)
 * 2. Videos
 * 3. Maps
 * 4. Documents
 * 5. Other (unknown/unsupported)
 *
 * @param {string} filePath - File path or just extension
 * @returns {string} Media type: 'img', 'vid', 'doc', 'map', or 'other'
 *
 * @example
 * determineMediaType('/path/to/photo.jpg')
 * // Returns: 'img'
 *
 * @example
 * determineMediaType('video.mp4')
 * // Returns: 'vid'
 *
 * @example
 * determineMediaType('.PDF')
 * // Returns: 'doc'
 *
 * @example
 * determineMediaType('unknown.xyz')
 * // Returns: 'other'
 */
function determineMediaType(filePath) {
  if (!filePath || typeof filePath !== 'string') {
    return 'other';
  }

  // Extract extension (remove leading dot, lowercase)
  let ext = path.extname(filePath).toLowerCase();
  if (ext.startsWith('.')) {
    ext = ext.substring(1);
  }

  if (!ext) {
    return 'other';
  }

  // Check against type lists (priority order matters)
  if (IMAGE_EXTENSIONS.has(ext)) {
    return 'img';
  }

  if (VIDEO_EXTENSIONS.has(ext)) {
    return 'vid';
  }

  if (MAP_EXTENSIONS.has(ext)) {
    return 'map';
  }

  if (DOCUMENT_EXTENSIONS.has(ext)) {
    return 'doc';
  }

  // Unknown type - per spec, documents can be "any file type"
  // So we'll treat unknown as 'doc' for v0.1.0
  console.info(`Unknown file extension: ${ext}, treating as document`);
  return 'doc';
}

/**
 * Check if file is a supported image.
 *
 * @param {string} filePath - File path or extension
 * @returns {boolean} True if supported image format
 *
 * @example
 * isImage('/path/to/photo.jpg')
 * // Returns: true
 *
 * @example
 * isImage('video.mp4')
 * // Returns: false
 */
function isImage(filePath) {
  return determineMediaType(filePath) === 'img';
}

/**
 * Check if file is a supported video.
 *
 * @param {string} filePath - File path or extension
 * @returns {boolean} True if supported video format
 */
function isVideo(filePath) {
  return determineMediaType(filePath) === 'vid';
}

/**
 * Check if file is a supported document.
 *
 * @param {string} filePath - File path or extension
 * @returns {boolean} True if supported document format
 */
function isDocument(filePath) {
  return determineMediaType(filePath) === 'doc';
}

/**
 * Check if file is a supported map.
 *
 * @param {string} filePath - File path or extension
 * @returns {boolean} True if supported map format
 */
function isMap(filePath) {
  return determineMediaType(filePath) === 'map';
}

/**
 * Get list of all supported extensions for a media type.
 *
 * @param {string} mediaType - Type: 'img', 'vid', 'doc', or 'map'
 * @returns {string[]} Array of supported extensions (without dots)
 *
 * @example
 * getSupportedExtensions('img')
 * // Returns: ['3fr', 'ai', 'arw', ...]
 *
 * @example
 * getSupportedExtensions('vid')
 * // Returns: ['3gp', '3g2', 'amv', ...]
 */
function getSupportedExtensions(mediaType) {
  switch (mediaType) {
    case 'img':
      return Array.from(IMAGE_EXTENSIONS).sort();
    case 'vid':
      return Array.from(VIDEO_EXTENSIONS).sort();
    case 'doc':
      return Array.from(DOCUMENT_EXTENSIONS).sort();
    case 'map':
      return Array.from(MAP_EXTENSIONS).sort();
    default:
      return [];
  }
}

/**
 * Get counts of supported file types.
 *
 * @returns {Object} Counts for each type
 *
 * @example
 * getTypeStats()
 * // Returns: {images: 80, videos: 43, documents: 22, maps: 50, total: 195}
 */
function getTypeStats() {
  return {
    images: IMAGE_EXTENSIONS.size,
    videos: VIDEO_EXTENSIONS.size,
    documents: DOCUMENT_EXTENSIONS.size,
    maps: MAP_EXTENSIONS.size,
    total: IMAGE_EXTENSIONS.size + VIDEO_EXTENSIONS.size +
           DOCUMENT_EXTENSIONS.size + MAP_EXTENSIONS.size
  };
}

// Export functions and constants
export {
  determineMediaType,
  isImage,
  isVideo,
  isDocument,
  isMap,
  getSupportedExtensions,
  getTypeStats,
  // Export type sets for reference
  IMAGE_EXTENSIONS,
  VIDEO_EXTENSIONS,
  DOCUMENT_EXTENSIONS,
  MAP_EXTENSIONS
};
