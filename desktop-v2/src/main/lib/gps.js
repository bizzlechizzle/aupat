/**
 * AUPAT GPS Module
 *
 * ONE FUNCTION: Parse GPS coordinates from various string formats
 *
 * LILBITS Principle: One script = one function
 * This module handles GPS coordinate parsing and validation.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

/**
 * Parse GPS coordinates from various string formats.
 *
 * Supports multiple input formats:
 * - "42.8864, -78.8784" (decimal degrees with comma)
 * - "42.8864,-78.8784" (no space)
 * - "42.8864 -78.8784" (space separated)
 * - "(42.8864, -78.8784)" (with parentheses)
 * - "lat: 42.8864, lon: -78.8784" (with labels)
 * - "latitude: 42.8864, longitude: -78.8784" (full labels)
 *
 * @param {string|null} gpsInput - GPS coordinate string in various formats
 * @returns {{lat: number, lon: number}|null} Object with lat/lon, or null if invalid
 *
 * @example
 * parseGPS("42.8864, -78.8784")
 * // Returns: {lat: 42.8864, lon: -78.8784}
 *
 * @example
 * parseGPS("(42.8864,-78.8784)")
 * // Returns: {lat: 42.8864, lon: -78.8784}
 *
 * @example
 * parseGPS("lat: 42.8864, lon: -78.8784")
 * // Returns: {lat: 42.8864, lon: -78.8784}
 *
 * @example
 * parseGPS("invalid")
 * // Returns: null
 *
 * Notes:
 * - Returns null for invalid or empty input
 * - Validates latitude range: -90 to 90
 * - Validates longitude range: -180 to 180
 * - Case insensitive for labels
 */
function parseGPS(gpsInput) {
  // Handle null, undefined, or empty strings
  if (!gpsInput || typeof gpsInput !== 'string' || !gpsInput.trim()) {
    return null;
  }

  try {
    // Clean input - remove parentheses, labels (case insensitive)
    let cleaned = gpsInput.trim();
    cleaned = cleaned.replace(/[()]/g, '');  // Remove parentheses
    cleaned = cleaned.replace(/lat(itude)?:/gi, '');  // Remove lat/latitude labels
    cleaned = cleaned.replace(/lon(gitude)?:/gi, '');  // Remove lon/longitude labels

    let lat, lon;

    // Try comma-separated first (most common format)
    if (cleaned.includes(',')) {
      const parts = cleaned.split(',');
      if (parts.length !== 2) {
        return null;
      }
      lat = parseFloat(parts[0].trim());
      lon = parseFloat(parts[1].trim());
    }
    // Try space-separated
    else if (cleaned.includes(' ')) {
      const parts = cleaned.split(/\s+/).filter(p => p);  // Split on whitespace, filter empty
      if (parts.length !== 2) {
        return null;
      }
      lat = parseFloat(parts[0]);
      lon = parseFloat(parts[1]);
    }
    // Can't parse - need separator
    else {
      return null;
    }

    // Validate that parsing worked
    if (isNaN(lat) || isNaN(lon)) {
      return null;
    }

    // Validate coordinate ranges
    // Latitude: -90 to 90 degrees
    // Longitude: -180 to 180 degrees
    if (!_isValidLatitude(lat)) {
      console.warn(`Invalid latitude: ${lat} (must be between -90 and 90)`);
      return null;
    }

    if (!_isValidLongitude(lon)) {
      console.warn(`Invalid longitude: ${lon} (must be between -180 and 180)`);
      return null;
    }

    // Return as object with lat/lon properties
    return { lat, lon };

  } catch (error) {
    // Failed to parse - return null
    console.debug(`GPS parsing failed for input: ${gpsInput}`, error);
    return null;
  }
}

/**
 * Format GPS coordinates as a standard string.
 *
 * @param {number} lat - Latitude (-90 to 90)
 * @param {number} lon - Longitude (-180 to 180)
 * @param {number} [precision=6] - Decimal places (default: 6, ~0.11m accuracy)
 * @returns {string} Formatted GPS string: "lat, lon"
 * @throws {Error} If coordinates are invalid
 *
 * @example
 * formatGPS(42.8864, -78.8784)
 * // Returns: "42.886400, -78.878400"
 *
 * @example
 * formatGPS(42.8864123, -78.8784567, 4)
 * // Returns: "42.8864, -78.8785"
 */
function formatGPS(lat, lon, precision = 6) {
  if (typeof lat !== 'number' || typeof lon !== 'number') {
    throw new Error('Latitude and longitude must be numbers');
  }

  if (!_isValidLatitude(lat)) {
    throw new Error(`Invalid latitude: ${lat} (must be between -90 and 90)`);
  }

  if (!_isValidLongitude(lon)) {
    throw new Error(`Invalid longitude: ${lon} (must be between -180 and 180)`);
  }

  return `${lat.toFixed(precision)}, ${lon.toFixed(precision)}`;
}

/**
 * Calculate distance between two GPS coordinates using Haversine formula.
 *
 * Returns the great-circle distance between two points on Earth's surface.
 *
 * @param {number} lat1 - Latitude of first point
 * @param {number} lon1 - Longitude of first point
 * @param {number} lat2 - Latitude of second point
 * @param {number} lon2 - Longitude of second point
 * @returns {number} Distance in meters
 *
 * @example
 * // Distance between Buffalo and Rochester, NY
 * const distance = calculateDistance(42.8864, -78.8784, 43.1566, -77.6088);
 * // Returns: ~99000 (meters, or ~99km)
 *
 * Notes:
 * - Uses Earth's mean radius: 6,371,000 meters
 * - Accuracy decreases for very long distances (>1000km)
 * - Good enough for location proximity checks
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
  // Validate inputs
  if (!_isValidLatitude(lat1) || !_isValidLatitude(lat2)) {
    throw new Error('Invalid latitude');
  }
  if (!_isValidLongitude(lon1) || !_isValidLongitude(lon2)) {
    throw new Error('Invalid longitude');
  }

  const EARTH_RADIUS_METERS = 6371000;  // Earth's mean radius

  // Convert to radians
  const lat1Rad = _toRadians(lat1);
  const lat2Rad = _toRadians(lat2);
  const deltaLatRad = _toRadians(lat2 - lat1);
  const deltaLonRad = _toRadians(lon2 - lon1);

  // Haversine formula
  const a = Math.sin(deltaLatRad / 2) * Math.sin(deltaLatRad / 2) +
            Math.cos(lat1Rad) * Math.cos(lat2Rad) *
            Math.sin(deltaLonRad / 2) * Math.sin(deltaLonRad / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  const distance = EARTH_RADIUS_METERS * c;

  return distance;
}

/**
 * INTERNAL: Validate latitude is in valid range.
 *
 * @private
 * @param {number} lat - Latitude to validate
 * @returns {boolean} True if valid (-90 to 90)
 */
function _isValidLatitude(lat) {
  return typeof lat === 'number' && lat >= -90 && lat <= 90;
}

/**
 * INTERNAL: Validate longitude is in valid range.
 *
 * @private
 * @param {number} lon - Longitude to validate
 * @returns {boolean} True if valid (-180 to 180)
 */
function _isValidLongitude(lon) {
  return typeof lon === 'number' && lon >= -180 && lon <= 180;
}

/**
 * INTERNAL: Convert degrees to radians.
 *
 * @private
 * @param {number} degrees - Angle in degrees
 * @returns {number} Angle in radians
 */
function _toRadians(degrees) {
  return degrees * (Math.PI / 180);
}

// Export functions
module.exports = {
  parseGPS,
  formatGPS,
  calculateDistance
};
