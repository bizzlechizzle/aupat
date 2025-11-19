/**
 * AUPAT Database Module
 *
 * ONE FUNCTION: Provide SQLite database connection and queries
 *
 * LILBITS Principle: One script = one function
 * This module handles SQLite database connection using better-sqlite3.
 *
 * Version: 1.1.0 - Converted to ESM
 * Last Updated: 2025-11-19
 */

import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

// Singleton database instance
let dbInstance = null;
let dbPath = null;

/**
 * Get or create database connection.
 *
 * Uses better-sqlite3 for synchronous, fast SQLite access.
 * Automatically enables:
 * - WAL mode (Write-Ahead Logging) for better concurrency
 * - Foreign keys for data integrity
 *
 * @param {string} [databasePath=null] - Path to database file (required on first call)
 * @returns {Database} better-sqlite3 database instance
 * @throws {Error} If database path not provided on first call
 *
 * @example
 * // First call - provide path
 * const db = getDatabase('/data/aupat/aupat.db');
 *
 * @example
 * // Subsequent calls - no path needed
 * const db = getDatabase();
 *
 * @example
 * // Use the database
 * const db = getDatabase();
 * const locations = db.prepare('SELECT * FROM locations').all();
 */
function getDatabase(databasePath = null) {
  // If we already have a connection, return it
  if (dbInstance && dbInstance.open) {
    return dbInstance;
  }

  // First call - need database path
  if (!databasePath && !dbPath) {
    throw new Error('Database path required on first call to getDatabase()');
  }

  // Use provided path or stored path
  const actualPath = databasePath || dbPath;

  // Ensure database directory exists
  const dbDir = path.dirname(actualPath);
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }

  // Create or open database
  dbInstance = new Database(actualPath);
  dbPath = actualPath;

  // Enable WAL mode (Write-Ahead Logging) for better concurrency
  // Multiple readers can access database while one writer is active
  dbInstance.pragma('journal_mode = WAL');

  // Enable foreign keys for data integrity
  dbInstance.pragma('foreign_keys = ON');

  console.log(`Database connected: ${actualPath}`);
  console.log(`WAL mode: ${dbInstance.pragma('journal_mode', { simple: true })}`);
  console.log(`Foreign keys: ${dbInstance.pragma('foreign_keys', { simple: true })}`);

  return dbInstance;
}

/**
 * Close database connection.
 *
 * Call this when shutting down the application.
 * Database will auto-close when process exits, but explicit close is better.
 *
 * @example
 * closeDatabase();
 */
function closeDatabase() {
  if (dbInstance && dbInstance.open) {
    dbInstance.close();
    console.log('Database connection closed');
    dbInstance = null;
  }
}

/**
 * Check if database file exists.
 *
 * @param {string} databasePath - Path to check
 * @returns {boolean} True if database file exists
 *
 * @example
 * if (databaseExists('/data/aupat/aupat.db')) {
 *   console.log('Database found');
 * }
 */
function databaseExists(databasePath) {
  return fs.existsSync(databasePath);
}

/**
 * Create v0.1.0 database schema.
 *
 * Creates all tables and indexes per AUPAT v0.1.0 specification:
 * - locations (main location records)
 * - sub_locations (sub-locations within locations)
 * - images (photo files)
 * - videos (video files)
 * - documents (document files)
 * - urls (archived URLs)
 * - maps (map files)
 * - bookmarks (browser bookmarks)
 * - notes (user notes)
 *
 * @param {Database} db - better-sqlite3 database instance
 * @throws {Error} If schema creation fails
 *
 * @example
 * const db = getDatabase('/data/aupat/aupat.db');
 * createSchema(db);
 */
function createSchema(db) {
  console.log('Creating v0.1.0 database schema...');

  // Use transaction for atomic schema creation
  const createTables = db.transaction(() => {
    // 1. Locations table
    db.exec(`
      CREATE TABLE IF NOT EXISTS locations (
        loc_uuid TEXT PRIMARY KEY,
        loc_name TEXT NOT NULL,
        loc_short TEXT,
        status TEXT,
        explored TEXT,
        type TEXT NOT NULL,
        sub_type TEXT,
        street TEXT,
        state TEXT NOT NULL,
        city TEXT,
        zip_code TEXT,
        county TEXT,
        region TEXT,
        gps_lat REAL,
        gps_lon REAL,
        import_author TEXT,
        historical INTEGER DEFAULT 0,
        pinned INTEGER DEFAULT 0,
        documented INTEGER DEFAULT 1,
        favorite INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    `);

    // 2. Sub-locations table
    db.exec(`
      CREATE TABLE IF NOT EXISTS sub_locations (
        sub_uuid TEXT PRIMARY KEY,
        loc_uuid TEXT NOT NULL,
        sub_name TEXT NOT NULL,
        sub_short TEXT,
        is_primary INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
      )
    `);

    // 3. Images table
    db.exec(`
      CREATE TABLE IF NOT EXISTS images (
        img_uuid TEXT PRIMARY KEY,
        loc_uuid TEXT NOT NULL,
        sub_uuid TEXT,
        img_sha TEXT NOT NULL,
        original_name TEXT,
        original_path TEXT,
        img_name TEXT NOT NULL,
        img_ext TEXT,
        img_path TEXT,
        created_at TEXT NOT NULL,
        verified INTEGER DEFAULT 0,
        FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
        FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
      )
    `);

    // 4. Videos table
    db.exec(`
      CREATE TABLE IF NOT EXISTS videos (
        vid_uuid TEXT PRIMARY KEY,
        loc_uuid TEXT NOT NULL,
        sub_uuid TEXT,
        vid_sha TEXT NOT NULL,
        original_name TEXT,
        original_path TEXT,
        vid_name TEXT NOT NULL,
        vid_ext TEXT,
        vid_path TEXT,
        created_at TEXT NOT NULL,
        verified INTEGER DEFAULT 0,
        FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
        FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
      )
    `);

    // 5. Documents table
    db.exec(`
      CREATE TABLE IF NOT EXISTS documents (
        doc_uuid TEXT PRIMARY KEY,
        loc_uuid TEXT NOT NULL,
        sub_uuid TEXT,
        doc_sha TEXT NOT NULL,
        original_name TEXT,
        original_path TEXT,
        doc_name TEXT NOT NULL,
        doc_ext TEXT,
        doc_path TEXT,
        created_at TEXT NOT NULL,
        verified INTEGER DEFAULT 0,
        FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
        FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
      )
    `);

    // 6. URLs table
    db.exec(`
      CREATE TABLE IF NOT EXISTS urls (
        url_uuid TEXT PRIMARY KEY,
        loc_uuid TEXT NOT NULL,
        sub_uuid TEXT,
        url TEXT NOT NULL,
        title TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
        FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
      )
    `);

    // 7. Maps table
    db.exec(`
      CREATE TABLE IF NOT EXISTS maps (
        map_uuid TEXT PRIMARY KEY,
        loc_uuid TEXT NOT NULL,
        sub_uuid TEXT,
        map_sha TEXT NOT NULL,
        original_name TEXT,
        original_path TEXT,
        map_name TEXT NOT NULL,
        map_ext TEXT,
        map_path TEXT,
        created_at TEXT NOT NULL,
        verified INTEGER DEFAULT 0,
        FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE,
        FOREIGN KEY (sub_uuid) REFERENCES sub_locations(sub_uuid) ON DELETE SET NULL
      )
    `);

    // 8. Bookmarks table (Browser feature)
    db.exec(`
      CREATE TABLE IF NOT EXISTS bookmarks (
        bookmark_uuid TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        title TEXT,
        state TEXT,
        type TEXT,
        loc_uuid TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE SET NULL
      )
    `);

    // 9. Notes table (User Notes feature)
    db.exec(`
      CREATE TABLE IF NOT EXISTS notes (
        note_uuid TEXT PRIMARY KEY,
        loc_uuid TEXT NOT NULL,
        title TEXT,
        content TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (loc_uuid) REFERENCES locations(loc_uuid) ON DELETE CASCADE
      )
    `);
  });

  // Execute transaction
  createTables();

  console.log('Database tables created');

  // Create indexes
  createIndexes(db);
}

/**
 * Create performance indexes.
 *
 * @param {Database} db - better-sqlite3 database instance
 */
function createIndexes(db) {
  console.log('Creating database indexes...');

  const indexes = [
    // Locations indexes
    'CREATE INDEX IF NOT EXISTS idx_locations_state ON locations(state)',
    'CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(type)',
    'CREATE INDEX IF NOT EXISTS idx_locations_historical ON locations(historical)',
    'CREATE INDEX IF NOT EXISTS idx_locations_pinned ON locations(pinned DESC)',
    'CREATE INDEX IF NOT EXISTS idx_locations_documented ON locations(documented)',
    'CREATE INDEX IF NOT EXISTS idx_locations_favorite ON locations(favorite)',
    'CREATE INDEX IF NOT EXISTS idx_locations_updated ON locations(updated_at)',
    'CREATE INDEX IF NOT EXISTS idx_locations_gps ON locations(gps_lat, gps_lon)',

    // Sub-locations indexes
    'CREATE INDEX IF NOT EXISTS idx_sub_locations_loc ON sub_locations(loc_uuid)',
    'CREATE INDEX IF NOT EXISTS idx_sub_locations_primary ON sub_locations(is_primary)',

    // Images indexes
    'CREATE INDEX IF NOT EXISTS idx_images_loc ON images(loc_uuid)',
    'CREATE INDEX IF NOT EXISTS idx_images_sub ON images(sub_uuid)',
    'CREATE INDEX IF NOT EXISTS idx_images_sha ON images(img_sha)',

    // Videos indexes
    'CREATE INDEX IF NOT EXISTS idx_videos_loc ON videos(loc_uuid)',
    'CREATE INDEX IF NOT EXISTS idx_videos_sub ON videos(sub_uuid)',
    'CREATE INDEX IF NOT EXISTS idx_videos_sha ON videos(vid_sha)',

    // Documents indexes
    'CREATE INDEX IF NOT EXISTS idx_documents_loc ON documents(loc_uuid)',
    'CREATE INDEX IF NOT EXISTS idx_documents_sha ON documents(doc_sha)',

    // URLs indexes
    'CREATE INDEX IF NOT EXISTS idx_urls_loc ON urls(loc_uuid)',

    // Maps indexes
    'CREATE INDEX IF NOT EXISTS idx_maps_loc ON maps(loc_uuid)',
    'CREATE INDEX IF NOT EXISTS idx_maps_sha ON maps(map_sha)',

    // Bookmarks indexes
    'CREATE INDEX IF NOT EXISTS idx_bookmarks_loc ON bookmarks(loc_uuid)',
    'CREATE INDEX IF NOT EXISTS idx_bookmarks_state ON bookmarks(state)',
    'CREATE INDEX IF NOT EXISTS idx_bookmarks_type ON bookmarks(type)',

    // Notes indexes
    'CREATE INDEX IF NOT EXISTS idx_notes_loc ON notes(loc_uuid)'
  ];

  indexes.forEach(sql => db.exec(sql));

  console.log(`Created ${indexes.length} indexes`);
}

// Export functions (ESM format)
export {
  getDatabase,
  closeDatabase,
  databaseExists,
  createSchema
};
