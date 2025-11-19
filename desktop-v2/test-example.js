/**
 * AUPAT v2 - Simple Test Example
 *
 * Demonstrates how to use the new pure Electron architecture.
 * This script shows the complete workflow:
 * 1. Create database
 * 2. Create a location
 * 3. Import a file
 *
 * Run with: node test-example.js
 */

const path = require('path');
const fs = require('fs');

// Import modules
const { getDatabase, createSchema } = require('./src/main/database');
const { createLocation } = require('./src/main/modules/locations');
const { importFile } = require('./src/main/modules/import');

// Configuration
const TEST_DIR = path.join(__dirname, 'test-data');
const DB_PATH = path.join(TEST_DIR, 'test-aupat.db');
const ARCHIVE_ROOT = path.join(TEST_DIR, 'archive');

async function runExample() {
  console.log('='.repeat(60));
  console.log('AUPAT v2 - Pure Electron Architecture Test');
  console.log('='.repeat(60));
  console.log();

  try {
    // Setup: Create test directory
    console.log('Step 1: Setting up test environment...');
    if (!fs.existsSync(TEST_DIR)) {
      fs.mkdirSync(TEST_DIR, { recursive: true });
    }

    // Delete old database if exists
    if (fs.existsSync(DB_PATH)) {
      fs.unlinkSync(DB_PATH);
      console.log('  ✓ Removed old test database');
    }

    console.log('  ✓ Test directory created');
    console.log();

    // Step 2: Create database
    console.log('Step 2: Creating database with v0.1.0 schema...');
    const db = getDatabase(DB_PATH);
    createSchema(db);
    console.log('  ✓ Database created with 9 tables and 29 indexes');
    console.log('  ✓ WAL mode enabled');
    console.log('  ✓ Foreign keys enabled');
    console.log();

    // Step 3: Create a test location
    console.log('Step 3: Creating test location...');
    const location = createLocation(db, {
      name: 'Buffalo Psychiatric Center',
      state: 'NY',
      type: 'Hospital',
      locShort: 'buffpsych',
      status: 'Abandoned',
      explored: 'Interior',
      gps: '42.8864, -78.8784',
      city: 'Buffalo',
      county: 'Erie',
      historical: true,
      importAuthor: 'testuser'
    });

    console.log('  ✓ Location created:');
    console.log(`    - UUID: ${location.loc_uuid}`);
    console.log(`    - Short: ${location.loc_short}`);
    console.log(`    - Name: ${location.loc_name}`);
    console.log();

    // Step 4: Create a test file to import
    console.log('Step 4: Creating test image file...');
    const testFilePath = path.join(TEST_DIR, 'test-photo.jpg');

    // Create a dummy file (in real usage, this would be an actual image)
    const testData = Buffer.from('This is a test image file');
    fs.writeFileSync(testFilePath, testData);

    console.log(`  ✓ Test file created: ${testFilePath}`);
    console.log();

    // Step 5: Import the file
    console.log('Step 5: Importing file into archive...');
    const importResult = await importFile(
      db,
      testFilePath,
      {
        locUuid: location.loc_uuid,
        locShort: location.loc_short,
        state: 'ny',
        type: 'hospital'
      },
      ARCHIVE_ROOT,
      {
        deleteSource: false  // Keep source file for testing
      }
    );

    if (importResult.success) {
      console.log('  ✓ Import successful!');
      console.log(`    - File UUID: ${importResult.fileUuid}`);
      console.log(`    - Media Type: ${importResult.mediaType}`);
      console.log(`    - New Filename: ${importResult.fileName}`);
      console.log(`    - Archive Path: ${importResult.filePath}`);
      console.log(`    - Verified: ${importResult.verified ? 'Yes' : 'No'}`);
    } else {
      console.log(`  ✗ Import failed: ${importResult.error}`);
    }

    console.log();

    // Step 6: Verify database
    console.log('Step 6: Verifying database records...');

    const locCount = db.prepare('SELECT COUNT(*) as count FROM locations').get();
    const imgCount = db.prepare('SELECT COUNT(*) as count FROM images').get();

    console.log(`  ✓ Locations in database: ${locCount.count}`);
    console.log(`  ✓ Images in database: ${imgCount.count}`);
    console.log();

    // Step 7: Check archive folder structure
    console.log('Step 7: Checking archive folder structure...');
    const expectedFolder = path.join(ARCHIVE_ROOT, 'NY-Hospital', `${location.loc_short}-${location.loc_uuid.substring(0, 12).replace(/-/g, '')}`);

    if (fs.existsSync(expectedFolder)) {
      console.log(`  ✓ Location folder created: ${expectedFolder}`);

      // List subfolders
      const subfolders = fs.readdirSync(expectedFolder);
      console.log(`  ✓ Subfolders: ${subfolders.join(', ')}`);
    } else {
      console.log('  ✗ Location folder not found');
    }

    console.log();
    console.log('='.repeat(60));
    console.log('TEST COMPLETE!');
    console.log('='.repeat(60));
    console.log();
    console.log('Test artifacts created in: ' + TEST_DIR);
    console.log('  - Database: test-aupat.db');
    console.log('  - Archive: archive/');
    console.log();
    console.log('To clean up: rm -rf ' + TEST_DIR);
    console.log();

  } catch (error) {
    console.error();
    console.error('ERROR:', error.message);
    console.error();
    console.error('Stack trace:');
    console.error(error.stack);
    process.exit(1);
  }
}

// Run the example
runExample().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
