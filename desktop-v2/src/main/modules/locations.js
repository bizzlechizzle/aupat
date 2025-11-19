/**
 * AUPAT Locations Module
 *
 * ONE FUNCTION: Location CRUD operations
 *
 * LILBITS Principle: One script = one function
 * This module handles Create, Read, Update, Delete operations for locations.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

const { generateUUID } = require('../lib/uuid');
const { normalizeLocationName, normalizeShortName, normalizeStateCode, normalizeLocationType, normalizeDatetime } = require('../lib/normalize');
const { parseGPS } = require('../lib/gps');

/**
 * Create new location in database.
 *
 * Required fields:
 * - name: Location name
 * - state: State code (2 letters)
 * - type: Location type
 *
 * Optional fields per v0.1.0 spec:
 * - locShort: Short name (auto-generated from name if not provided)
 * - status, explored, subType, street, city, zipCode, county, region
 * - gps: GPS coordinates as string (will be parsed)
 * - importAuthor, historical
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {Object} locationData - Location data object
 * @returns {Object} Created location with loc_uuid and loc_short
 * @throws {Error} If validation fails or database insert fails
 *
 * @example
 * const location = createLocation(db, {
 *   name: 'Buffalo Psychiatric Center',
 *   state: 'NY',
 *   type: 'Hospital',
 *   locShort: 'buffpsych',
 *   gps: '42.8864, -78.8784',
 *   status: 'Abandoned',
 *   historical: true
 * });
 * // Returns: {loc_uuid: 'a1b2c3d4-...', loc_short: 'buffpsych'}
 */
function createLocation(db, locationData) {
  // Validate required fields
  if (!locationData.name || !locationData.name.trim()) {
    throw new Error('Location name is required');
  }
  if (!locationData.state || !locationData.state.trim()) {
    throw new Error('State is required');
  }
  if (!locationData.type || !locationData.type.trim()) {
    throw new Error('Location type is required');
  }

  // Normalize inputs
  const nameNorm = normalizeLocationName(locationData.name);
  const stateNorm = normalizeStateCode(locationData.state);
  const typeNorm = normalizeLocationType(locationData.type);

  // Generate or normalize short name
  let locShort = locationData.locShort;
  if (!locShort) {
    // Auto-generate: first word of name, max 12 chars, lowercase
    locShort = nameNorm.split(' ')[0].substring(0, 12).toLowerCase();
  }
  locShort = normalizeShortName(locShort);

  // Normalize optional fields
  const subTypeNorm = locationData.subType ? normalizeLocationType(locationData.subType) : null;

  // Parse GPS if provided
  let gpsLat = null, gpsLon = null;
  if (locationData.gps) {
    const gpsParseLocation = parseGPS(locationData.gps);
    if (gpsParseLocation) {
      gpsLat = gpsParseLocation.lat;
      gpsLon = gpsParseLocation.lon;
    }
  }

  // Generate UUID with collision detection
  const locUuid = generateUUID(db, 'locations', 'loc_uuid');

  // Get current timestamp
  const timestamp = normalizeDatetime(null);

  // Prepare insert statement
  const insert = db.prepare(`
    INSERT INTO locations (
      loc_uuid, loc_name, loc_short, status, explored,
      type, sub_type, street, state, city, zip_code,
      county, region, gps_lat, gps_lon, import_author,
      historical, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  // Execute insert
  try {
    insert.run(
      locUuid,
      nameNorm,
      locShort,
      locationData.status || null,
      locationData.explored || null,
      typeNorm,
      subTypeNorm,
      locationData.street || null,
      stateNorm,
      locationData.city || null,
      locationData.zipCode || null,
      locationData.county || null,
      locationData.region || null,
      gpsLat,
      gpsLon,
      locationData.importAuthor || null,
      locationData.historical ? 1 : 0,
      timestamp,
      timestamp
    );

    console.log(`Created location: ${nameNorm} (${locUuid})`);

    return {
      loc_uuid: locUuid,
      loc_short: locShort,
      loc_name: nameNorm
    };

  } catch (error) {
    throw new Error(`Failed to create location: ${error.message}`);
  }
}

/**
 * Get location by UUID.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} locUuid - Location UUID
 * @returns {Object|null} Location object, or null if not found
 *
 * @example
 * const location = getLocation(db, 'a1b2c3d4-...');
 */
function getLocation(db, locUuid) {
  const query = db.prepare('SELECT * FROM locations WHERE loc_uuid = ?');
  return query.get(locUuid);
}

/**
 * Get all locations.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {Object} [options={}] - Query options (limit, offset, orderBy)
 * @returns {Array} Array of location objects
 *
 * @example
 * // Get all locations
 * const locations = getAllLocations(db);
 *
 * @example
 * // Get with pagination
 * const locations = getAllLocations(db, {limit: 10, offset: 0});
 */
function getAllLocations(db, options = {}) {
  let sql = 'SELECT * FROM locations';

  // Add ordering
  const orderBy = options.orderBy || 'updated_at DESC';
  sql += ` ORDER BY ${orderBy}`;

  // Add pagination
  if (options.limit) {
    sql += ` LIMIT ${parseInt(options.limit)}`;
    if (options.offset) {
      sql += ` OFFSET ${parseInt(options.offset)}`;
    }
  }

  const query = db.prepare(sql);
  return query.all();
}

/**
 * Search locations by name.
 *
 * Used for autocomplete functionality.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} searchTerm - Search term (partial name match)
 * @param {number} [limit=10] - Maximum results to return
 * @returns {Array} Array of matching locations
 *
 * @example
 * const matches = searchLocations(db, 'buff');
 * // Returns locations with names containing 'buff'
 */
function searchLocations(db, searchTerm, limit = 10) {
  const query = db.prepare(`
    SELECT loc_uuid, loc_name, loc_short, state, type, city
    FROM locations
    WHERE loc_name LIKE ?
    ORDER BY loc_name
    LIMIT ?
  `);

  return query.all(`%${searchTerm}%`, limit);
}

/**
 * Update location.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} locUuid - Location UUID
 * @param {Object} updates - Fields to update
 * @returns {boolean} True if updated successfully
 *
 * @example
 * updateLocation(db, 'a1b2c3d4-...', {
 *   status: 'Demolished',
 *   gps: '42.8864, -78.8784'
 * });
 */
function updateLocation(db, locUuid, updates) {
  // Build SET clause dynamically from updates
  const fields = [];
  const values = [];

  // Map of allowed update fields
  const allowedFields = {
    loc_name: 'loc_name',
    name: 'loc_name',
    status: 'status',
    explored: 'explored',
    subType: 'sub_type',
    street: 'street',
    city: 'city',
    zipCode: 'zip_code',
    county: 'county',
    region: 'region',
    importAuthor: 'import_author',
    historical: 'historical',
    pinned: 'pinned',
    documented: 'documented',
    favorite: 'favorite'
  };

  // Process updates
  for (const [key, value] of Object.entries(updates)) {
    const dbField = allowedFields[key];
    if (dbField) {
      fields.push(`${dbField} = ?`);
      values.push(value);
    }
  }

  // Handle GPS specially (needs parsing)
  if (updates.gps) {
    const gpsCoords = parseGPS(updates.gps);
    if (gpsCoords) {
      fields.push('gps_lat = ?', 'gps_lon = ?');
      values.push(gpsCoords.lat, gpsCoords.lon);
    }
  }

  if (fields.length === 0) {
    throw new Error('No valid fields to update');
  }

  // Always update updated_at
  fields.push('updated_at = ?');
  values.push(normalizeDatetime(null));

  // Add loc_uuid to values (for WHERE clause)
  values.push(locUuid);

  // Build and execute query
  const sql = `UPDATE locations SET ${fields.join(', ')} WHERE loc_uuid = ?`;
  const update = db.prepare(sql);

  try {
    const result = update.run(...values);
    return result.changes > 0;
  } catch (error) {
    throw new Error(`Failed to update location: ${error.message}`);
  }
}

/**
 * Delete location (and all associated media via CASCADE).
 *
 * WARNING: This will delete all images, videos, documents, etc. for this location.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} locUuid - Location UUID
 * @returns {boolean} True if deleted successfully
 *
 * @example
 * const deleted = deleteLocation(db, 'a1b2c3d4-...');
 */
function deleteLocation(db, locUuid) {
  const query = db.prepare('DELETE FROM locations WHERE loc_uuid = ?');

  try {
    const result = query.run(locUuid);
    if (result.changes > 0) {
      console.log(`Deleted location: ${locUuid} (and all associated media)`);
      return true;
    }
    return false;
  } catch (error) {
    throw new Error(`Failed to delete location: ${error.message}`);
  }
}

// Export functions
module.exports = {
  createLocation,
  getLocation,
  getAllLocations,
  searchLocations,
  updateLocation,
  deleteLocation
};
