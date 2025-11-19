/**
 * AUPAT Desktop v2 - Main Process
 *
 * Pure Electron architecture (no Flask).
 * Direct SQLite access via better-sqlite3.
 *
 * Security:
 * - contextIsolation: true
 * - nodeIntegration: false
 * - All IPC via contextBridge in preload
 *
 * Version: 0.1.0
 * Last Updated: 2025-11-19
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');
const Store = require('electron-store');
const { initializeHandlers } = require('./ipc-handlers');

// Initialize settings store
const store = new Store({
  defaults: {
    // Database and archive paths (defaults to app user data)
    dbPath: path.join(app.getPath('userData'), 'data', 'aupat.db'),
    archiveRoot: path.join(app.getPath('userData'), 'archive'),

    // Import settings
    deleteAfterImport: false,
    importAuthor: '',

    // Map settings
    mapCenter: { lat: 42.6526, lng: -73.7562 }, // Albany, NY
    mapZoom: 10,

    // Window settings
    windowBounds: { width: 1200, height: 800 }
  }
});

let mainWindow = null;

/**
 * Create main application window
 */
function createWindow() {
  // Get saved window bounds
  const bounds = store.get('windowBounds');

  mainWindow = new BrowserWindow({
    width: bounds.width,
    height: bounds.height,
    minWidth: 800,
    minHeight: 600,
    title: 'AUPAT - Abandoned Upstate Project Archive Tool',
    webPreferences: {
      // Security settings
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,

      // Preload script for secure IPC
      preload: path.join(__dirname, '../preload/index.js')
    }
  });

  // Save window bounds on resize/move
  mainWindow.on('resize', () => {
    const bounds = mainWindow.getBounds();
    store.set('windowBounds', bounds);
  });

  mainWindow.on('move', () => {
    const bounds = mainWindow.getBounds();
    store.set('windowBounds', bounds);
  });

  // Load the app
  if (process.env.NODE_ENV === 'development') {
    // Development: load from Vite dev server
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    // Production: load built files
    mainWindow.loadFile(path.join(__dirname, '../../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  console.log('Main window created');
}

/**
 * Initialize application
 */
async function initialize() {
  console.log('='.repeat(60));
  console.log('AUPAT Desktop v2 - Pure Electron Architecture');
  console.log('='.repeat(60));
  console.log();

  // Initialize IPC handlers and database
  try {
    initializeHandlers(store);
    console.log('✓ Database and IPC handlers initialized');
  } catch (error) {
    console.error('✗ Failed to initialize:', error);
    throw error;
  }

  // Create window
  createWindow();

  console.log();
  console.log('Application ready!');
  console.log('Database:', store.get('dbPath'));
  console.log('Archive:', store.get('archiveRoot'));
  console.log();
}

// ============================================================================
// APP LIFECYCLE
// ============================================================================

// When Electron is ready
app.whenReady().then(() => {
  initialize().catch(error => {
    console.error('Fatal error during initialization:', error);
    app.quit();
  });

  // macOS: Re-create window when dock icon is clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed (except macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Handle app quit
app.on('will-quit', () => {
  console.log('Application shutting down...');
  // Database connection will auto-close
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
});
