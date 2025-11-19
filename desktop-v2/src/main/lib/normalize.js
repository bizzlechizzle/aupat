/**
 * AUPAT Normalization Module
 *
 * ONE FUNCTION: Normalize text and data for consistent storage
 *
 * LILBITS Principle: One script = one function
 * This module handles text normalization (location names, states, extensions, etc.)
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

// Valid US state codes (USPS two-letter abbreviations + territories)
const VALID_US_STATES = new Set([
  'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga',
  'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
  'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
  'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
  'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy',
  'dc', 'pr', 'vi', 'gu', 'as', 'mp'  // DC + territories
]);

// Common location types (validated list)
const VALID_LOCATION_TYPES = new Set([
  'industrial', 'residential', 'commercial', 'institutional',
  'agricultural', 'recreational', 'infrastructure', 'military',
  'religious', 'educational', 'healthcare', 'transportation',
  'mixed-use', 'other'
]);

/**
 * Normalize location name for consistent storage.
 *
 * Applies:
 * 1. Trim whitespace
 * 2. Collapse multiple spaces to single space
 * 3. Title case conversion
 *
 * @param {string} name - Raw location name (e.g., "abandoned factory", "Old Mill")
 * @returns {string} Normalized location name in Title Case
 * @throws {Error} If name is empty after normalization
 *
 * @example
 * normalizeLocationName("abandoned factory")
 * // Returns: "Abandoned Factory"
 *
 * @example
 * normalizeLocationName("  old   mill  ")
 * // Returns: "Old Mill"
 *
 * @example
 * normalizeLocationName("buffalo psychiatric center")
 * // Returns: "Buffalo Psychiatric Center"
 */
function normalizeLocationName(name) {
  if (!name || typeof name !== 'string') {
    throw new Error('Location name must be a non-empty string');
  }

  // Trim and collapse multiple spaces
  let normalized = name.trim().replace(/\s+/g, ' ');

  if (!normalized) {
    throw new Error('Location name cannot be empty after normalization');
  }

  // Convert to title case
  normalized = _toTitleCase(normalized);

  return normalized;
}

/**
 * Normalize "short name" for location folders.
 *
 * Applies:
 * 1. Lowercase conversion
 * 2. Remove special characters (keep letters, numbers, hyphens)
 * 3. Collapse multiple hyphens
 * 4. Trim hyphens from start/end
 *
 * @param {string} shortName - User-provided short name
 * @returns {string} Normalized short name (lowercase, alphanumeric + hyphens)
 *
 * @example
 * normalizeShortName("Buff Psych")
 * // Returns: "buffpsych"
 *
 * @example
 * normalizeShortName("Old Mill #2")
 * // Returns: "oldmill2"
 *
 * @example
 * normalizeShortName("Factory--Building-A")
 * // Returns: "factory-building-a"
 */
function normalizeShortName(shortName) {
  if (!shortName || typeof shortName !== 'string') {
    throw new Error('Short name must be a non-empty string');
  }

  // Lowercase and remove special chars (keep letters, numbers, hyphens, spaces)
  let normalized = shortName
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')  // Remove special chars
    .replace(/\s+/g, '')           // Remove spaces
    .replace(/-+/g, '-')           // Collapse multiple hyphens
    .replace(/^-+|-+$/g, '');      // Trim hyphens from start/end

  if (!normalized) {
    throw new Error('Short name cannot be empty after normalization');
  }

  return normalized;
}

/**
 * Normalize US state code to lowercase two-letter abbreviation.
 *
 * @param {string} state - State code (e.g., "NY", "ny", "Ca")
 * @returns {string} Normalized lowercase state code
 * @throws {Error} If state code is invalid
 *
 * @example
 * normalizeStateCode("NY")
 * // Returns: "ny"
 *
 * @example
 * normalizeStateCode("California")
 * // Throws: Error (only accepts 2-letter codes)
 *
 * Notes:
 * - For v0.1.0, only accepts 2-letter codes
 * - Validates against USPS standard state codes
 * - Allows custom codes with warning (per spec)
 */
function normalizeStateCode(state) {
  if (!state || typeof state !== 'string') {
    throw new Error('State code cannot be empty');
  }

  const stateCode = state.trim().toLowerCase();

  // Warn if not in valid list (but allow it per spec)
  if (!VALID_US_STATES.has(stateCode)) {
    console.warn(
      `Custom state code: '${state}'. Not in standard USPS list. ` +
      `Standard examples: ny, ca, tx. Using '${stateCode}' as-is.`
    );
  }

  return stateCode;
}

/**
 * Normalize location type with optional auto-correction.
 *
 * Applies:
 * 1. Lowercase conversion
 * 2. Trim whitespace
 * 3. Replace spaces with hyphens
 * 4. Validate against known types
 *
 * @param {string} locationType - Location type (e.g., "Industrial", "hospital")
 * @returns {string} Normalized lowercase location type
 *
 * @example
 * normalizeLocationType("Industrial")
 * // Returns: "industrial"
 *
 * @example
 * normalizeLocationType("health care")
 * // Returns: "health-care"
 *
 * @example
 * normalizeLocationType("custom type")
 * // Returns: "custom-type" (with warning)
 */
function normalizeLocationType(locationType) {
  if (!locationType || typeof locationType !== 'string') {
    throw new Error('Location type cannot be empty');
  }

  // Lowercase, trim, replace spaces with hyphens
  let normalized = locationType
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-');

  if (!normalized) {
    throw new Error('Location type cannot be empty after normalization');
  }

  // Warn if not in valid list (but allow it per spec)
  if (!VALID_LOCATION_TYPES.has(normalized)) {
    console.info(
      `Custom location type: '${normalized}'. ` +
      `Common types: ${Array.from(VALID_LOCATION_TYPES).sort().join(', ')}. ` +
      `Using '${normalized}' as-is per specification.`
    );
  }

  return normalized;
}

/**
 * Normalize file extension to lowercase without leading dot.
 *
 * @param {string} extension - File extension (e.g., ".JPG", "mp4", ".PDF")
 * @returns {string} Normalized lowercase extension without dot (e.g., "jpg", "mp4")
 *
 * @example
 * normalizeExtension(".JPG")
 * // Returns: "jpg"
 *
 * @example
 * normalizeExtension("MP4")
 * // Returns: "mp4"
 *
 * @example
 * normalizeExtension(".pdf")
 * // Returns: "pdf"
 */
function normalizeExtension(extension) {
  if (!extension || typeof extension !== 'string') {
    throw new Error('Extension cannot be empty');
  }

  // Remove leading dot and convert to lowercase
  const normalized = extension.replace(/^\.+/, '').toLowerCase();

  if (!normalized) {
    throw new Error('Extension cannot be empty after normalization');
  }

  return normalized;
}

/**
 * Normalize import author username.
 *
 * @param {string|null} author - Author username (nullable)
 * @returns {string|null} Normalized author (lowercase, trimmed), or null if empty
 *
 * @example
 * normalizeAuthor("Bryant")
 * // Returns: "bryant"
 *
 * @example
 * normalizeAuthor("  Admin  ")
 * // Returns: "admin"
 *
 * @example
 * normalizeAuthor(null)
 * // Returns: null
 */
function normalizeAuthor(author) {
  if (!author || typeof author !== 'string' || !author.trim()) {
    return null;
  }

  return author.trim().toLowerCase();
}

/**
 * Normalize datetime to ISO 8601 format.
 *
 * For v0.1.0, accepts:
 * - ISO 8601 strings (e.g., "2025-11-19T10:30:00")
 * - Date objects
 * - null/undefined (returns current time)
 *
 * @param {string|Date|null} dtInput - Date/time input, or null for current time
 * @returns {string} ISO 8601 formatted datetime string
 *
 * @example
 * normalizeDatetime(new Date("2025-11-19"))
 * // Returns: "2025-11-19T00:00:00.000Z"
 *
 * @example
 * normalizeDatetime("2025-11-19T10:30:00")
 * // Returns: "2025-11-19T10:30:00.000Z"
 *
 * @example
 * normalizeDatetime(null)
 * // Returns: current time in ISO format
 *
 * Notes:
 * - For v0.1.0, uses basic Date parsing
 * - Future versions may add flexible date parsing library
 */
function normalizeDatetime(dtInput) {
  // If no input, use current time
  if (dtInput === null || dtInput === undefined || dtInput === '') {
    return new Date().toISOString();
  }

  // If already a Date object
  if (dtInput instanceof Date) {
    return dtInput.toISOString();
  }

  // If string, try to parse
  if (typeof dtInput === 'string') {
    const dt = new Date(dtInput);
    if (isNaN(dt.getTime())) {
      throw new Error(`Invalid datetime format: '${dtInput}'`);
    }
    return dt.toISOString();
  }

  throw new Error(`Invalid datetime input type: ${typeof dtInput}`);
}

/**
 * INTERNAL: Convert string to Title Case.
 *
 * Capitalizes the first letter of each word.
 *
 * @private
 * @param {string} str - String to convert
 * @returns {string} Title Cased string
 *
 * @example
 * _toTitleCase("buffalo psychiatric center")
 * // Returns: "Buffalo Psychiatric Center"
 */
function _toTitleCase(str) {
  return str
    .split(' ')
    .map(word => {
      if (!word) return word;
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(' ');
}

// Export functions
module.exports = {
  normalizeLocationName,
  normalizeShortName,
  normalizeStateCode,
  normalizeLocationType,
  normalizeExtension,
  normalizeAuthor,
  normalizeDatetime,
  VALID_US_STATES,        // Export for reference
  VALID_LOCATION_TYPES    // Export for reference
};
