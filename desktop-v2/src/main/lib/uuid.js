/**
 * AUPAT UUID Module
 *
 * ONE FUNCTION: Generate UUID4 with collision detection
 *
 * LILBITS Principle: One script = one function
 * This module handles UUID4 generation with database collision checks.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

const crypto = require('crypto');

/**
 * Generate a unique UUID4 identifier with collision detection.
 *
 * Generates a UUID4 and verifies that the first 12 characters are unique
 * in the specified table. If a collision is detected, generates a new UUID
 * and retries until a unique value is found (max 100 attempts).
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} tableName - Table to check for uniqueness ('locations', 'sub_locations', 'urls')
 * @param {string} uuidField - Name of the UUID field in the table (e.g., 'loc_uuid', 'sub_uuid', 'url_uuid')
 * @param {number} [hashLength=12] - Number of characters to check for uniqueness (default: 12)
 * @returns {string} Full UUID4 as a string (36 characters with dashes)
 * @throws {Error} If unable to generate unique UUID after 100 attempts
 *
 * @example
 * // Generate location UUID
 * const db = require('./database');
 * const locUuid = generateUUID(db, 'locations', 'loc_uuid');
 * const locUuid12 = locUuid.substring(0, 12);  // First 12 chars for filename
 *
 * @example
 * // Generate sub-location UUID
 * const subUuid = generateUUID(db, 'sub_locations', 'sub_uuid');
 *
 * @example
 * // Generate URL UUID
 * const urlUuid = generateUUID(db, 'urls', 'url_uuid');
 *
 * Notes:
 * - UUID4 collision probability for 12 hex chars (48 bits): ~1 in 281 trillion
 * - 50% collision probability at ~16.7 million records
 * - Collisions are extremely rare but checked to be safe
 * - Returns full UUID (36 chars); extract first 12 when needed for filenames
 */
function generateUUID(db, tableName, uuidField, hashLength = 12) {
  const MAX_RETRIES = 100;  // Safety limit to prevent infinite loop
  let retries = 0;

  // Validate inputs
  if (!db || typeof db.prepare !== 'function') {
    throw new Error('Invalid database instance');
  }

  if (!tableName || typeof tableName !== 'string') {
    throw new Error('Table name must be a non-empty string');
  }

  if (!uuidField || typeof uuidField !== 'string') {
    throw new Error('UUID field name must be a non-empty string');
  }

  if (hashLength < 1 || hashLength > 36) {
    throw new Error('Hash length must be between 1 and 36');
  }

  // Prepare SQL query for collision detection
  // Use SUBSTR to check first N characters
  const query = db.prepare(`
    SELECT ${uuidField}
    FROM ${tableName}
    WHERE SUBSTR(${uuidField}, 1, ?) = ?
    LIMIT 1
  `);

  while (retries < MAX_RETRIES) {
    // Generate new UUID4 using Node.js built-in crypto
    const newUuid = crypto.randomUUID();  // Returns format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    const uuidPrefix = newUuid.substring(0, hashLength);

    // Check if this prefix already exists in database
    const existing = query.get(hashLength, uuidPrefix);

    if (!existing) {
      // No collision - return the full UUID
      return newUuid;
    }

    // Collision detected - log and retry
    console.warn(`UUID collision detected: ${uuidPrefix} (attempt ${retries + 1}/${MAX_RETRIES})`);
    retries++;
  }

  // If we get here, we failed to generate a unique UUID after max retries
  throw new Error(`Failed to generate unique UUID after ${MAX_RETRIES} attempts for table ${tableName}`);
}

/**
 * Generate UUID4 without collision detection (fast, but risky).
 *
 * USE SPARINGLY: This does not check for collisions in the database.
 * Only use when you're absolutely sure collisions won't happen
 * (e.g., temporary IDs, non-database usage, or testing).
 *
 * For production use with database records, always use generateUUID()
 * with collision detection.
 *
 * @returns {string} Full UUID4 as a string (36 characters with dashes)
 *
 * @example
 * // Generate temporary UUID (no database check)
 * const tempId = generateUUIDFast();
 */
function generateUUIDFast() {
  return crypto.randomUUID();
}

/**
 * Check if a UUID (or UUID prefix) already exists in the database.
 *
 * Helper function to manually check for UUID collisions.
 * Useful for validation or debugging.
 *
 * @param {Object} db - better-sqlite3 database instance
 * @param {string} tableName - Table to check
 * @param {string} uuidField - Name of the UUID field
 * @param {string} uuidValue - UUID or UUID prefix to check
 * @returns {boolean} True if UUID exists, false otherwise
 *
 * @example
 * // Check if a location UUID exists
 * const exists = uuidExists(db, 'locations', 'loc_uuid', 'a1b2c3d4-...');
 * if (exists) {
 *   console.log('This UUID is already in use');
 * }
 */
function uuidExists(db, tableName, uuidField, uuidValue) {
  if (!db || typeof db.prepare !== 'function') {
    throw new Error('Invalid database instance');
  }

  const query = db.prepare(`
    SELECT ${uuidField}
    FROM ${tableName}
    WHERE ${uuidField} LIKE ?
    LIMIT 1
  `);

  const result = query.get(`${uuidValue}%`);
  return result !== undefined;
}

// Export functions
module.exports = {
  generateUUID,
  generateUUIDFast,
  uuidExists
};
