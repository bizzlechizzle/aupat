/**
 * AUPAT v2 - Images API Test
 *
 * Tests the new Images API functionality.
 * Run with: node test-images-api.js
 */

const path = require('path');
const fs = require('fs');

// Import modules
const { getDatabase, createSchema } = require('./src/main/database');
const { createLocation } = require('./src/main/modules/locations');
const { importFile } = require('./src/main/modules/import');
const { getImagesByLocation, getImage, getImagePath, countImagesByLocation } = require('./src/main/modules/images');

// Configuration
const TEST_DIR = path.join(__dirname, 'test-data');
const DB_PATH = path.join(TEST_DIR, 'test-aupat.db');
const ARCHIVE_ROOT = path.join(TEST_DIR, 'archive');

async function runTest() {
  console.log('='.repeat(60));
  console.log('AUPAT v2 - Images API Test');
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
    console.log('Step 2: Creating database...');
    const db = getDatabase(DB_PATH);
    createSchema(db);
    console.log('  ✓ Database created');
    console.log();

    // Step 3: Create test location
    console.log('Step 3: Creating test location...');
    const location = createLocation(db, {
      name: 'Buffalo Psychiatric Center',
      state: 'NY',
      type: 'Hospital',
      locShort: 'buffpsych',
      gps: '42.8864, -78.8784'
    });
    console.log(`  ✓ Location created: ${location.loc_short}`);
    console.log();

    // Step 4: Create test image files
    console.log('Step 4: Creating test image files...');
    const testImages = [];
    for (let i = 1; i <= 3; i++) {
      const testImagePath = path.join(TEST_DIR, `test-photo-${i}.jpg`);
      const imageData = `Test image ${i} for Images API test`;
      fs.writeFileSync(testImagePath, imageData);
      testImages.push(testImagePath);
      console.log(`  ✓ Created: test-photo-${i}.jpg`);
    }
    console.log();

    // Step 5: Import images
    console.log('Step 5: Importing images...');
    const importedImages = [];
    for (const imagePath of testImages) {
      const result = await importFile(
        db,
        imagePath,
        {
          locUuid: location.loc_uuid,
          locShort: location.loc_short,
          state: 'ny',
          type: 'hospital'
        },
        ARCHIVE_ROOT,
        { deleteSource: false }
      );

      if (result.success) {
        importedImages.push(result.fileUuid);
        console.log(`  ✓ Imported: ${result.fileName}`);
      } else {
        console.error(`  ✗ Failed to import: ${result.error}`);
      }
    }
    console.log();

    // Step 6: Test Images API
    console.log('Step 6: Testing Images API...');
    console.log();

    // Test 6.1: Get images by location
    console.log('  Test 6.1: getImagesByLocation()');
    const images = getImagesByLocation(db, location.loc_uuid, { limit: 10, offset: 0 });
    console.log(`  ✓ Found ${images.length} images`);
    images.forEach((img, idx) => {
      console.log(`    ${idx + 1}. ${img.img_name} (${img.img_uuid})`);
    });
    console.log();

    // Test 6.2: Get single image
    if (images.length > 0) {
      console.log('  Test 6.2: getImage()');
      const firstImage = getImage(db, images[0].img_uuid);
      if (firstImage) {
        console.log(`  ✓ Retrieved image: ${firstImage.img_name}`);
        console.log(`    - SHA: ${firstImage.img_sha}`);
        console.log(`    - Original: ${firstImage.original_name}`);
        console.log(`    - Verified: ${firstImage.verified ? 'Yes' : 'No'}`);
      } else {
        console.log('  ✗ Failed to retrieve image');
      }
      console.log();
    }

    // Test 6.3: Get image path
    if (images.length > 0) {
      console.log('  Test 6.3: getImagePath()');
      const pathResult = getImagePath(db, images[0].img_uuid, ARCHIVE_ROOT);
      if (pathResult.success) {
        console.log(`  ✓ Image path: ${pathResult.path}`);
        console.log(`  ✓ File exists: ${fs.existsSync(pathResult.path) ? 'Yes' : 'No'}`);
      } else {
        console.log(`  ✗ Failed: ${pathResult.error}`);
      }
      console.log();
    }

    // Test 6.4: Count images
    console.log('  Test 6.4: countImagesByLocation()');
    const count = countImagesByLocation(db, location.loc_uuid);
    console.log(`  ✓ Image count: ${count}`);
    console.log();

    // Step 7: Verify results
    console.log('Step 7: Verifying results...');
    if (count === 3 && images.length === 3) {
      console.log('  ✓ All tests passed!');
    } else {
      console.log('  ✗ Test mismatch');
      console.log(`    Expected: 3 images`);
      console.log(`    Got: ${count} in count, ${images.length} in query`);
    }
    console.log();

    console.log('='.repeat(60));
    console.log('IMAGES API TEST COMPLETE!');
    console.log('='.repeat(60));
    console.log();
    console.log(`Test artifacts in: ${TEST_DIR}`);
    console.log(`To clean up: rm -rf ${TEST_DIR}`);
    console.log();

  } catch (error) {
    console.error('Test failed:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

runTest();
