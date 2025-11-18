<script>
  /**
   * Settings Page
   *
   * Configure API URLs, map defaults, and application preferences.
   */

  import { onMount } from 'svelte';
  import { settings } from '../stores/settings.js';
  import { locations } from '../stores/locations.js';
  import MapImportDialog from './MapImportDialog.svelte';

  let currentSettings = {
    apiUrl: '',
    immichUrl: '',
    archiveboxUrl: '',
    mapCenter: { lat: 0, lng: 0 },
    mapZoom: 10,
    deleteImportMedia: false
  };

  let archiveConfig = {
    configured: false,
    db_path: '',
    staging_path: '',
    archive_path: '',
    backup_path: ''
  };

  let saveStatus = null; // null, 'saving', 'success', 'error'
  let configSaveStatus = null; // null, 'saving', 'success', 'error'
  let showMapImport = false;

  onMount(async () => {
    await settings.load();
    await loadArchiveConfig();
  });

  settings.subscribe(s => {
    currentSettings = { ...s };
  });

  async function loadArchiveConfig() {
    try {
      const result = await window.api.config.get();
      if (result.success) {
        archiveConfig = { ...result.data };
      }
    } catch (error) {
      console.error('Failed to load archive config:', error);
    }
  }

  async function handleSave(key, value) {
    try {
      saveStatus = 'saving';
      await settings.updateSetting(key, value);
      saveStatus = 'success';
      setTimeout(() => { saveStatus = null; }, 2000);
    } catch (error) {
      console.error('Failed to save setting:', error);
      saveStatus = 'error';
      setTimeout(() => { saveStatus = null; }, 3000);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    // Save all settings
    handleSave('apiUrl', currentSettings.apiUrl);
    handleSave('immichUrl', currentSettings.immichUrl);
    handleSave('archiveboxUrl', currentSettings.archiveboxUrl);
  }

  function openMapImport() {
    showMapImport = true;
  }

  function handleMapImported(event) {
    showMapImport = false;
    const { mode, count } = event.detail;

    // Refresh locations if in full import mode
    if (mode === 'full' && count > 0) {
      locations.fetchAll();
    }
  }

  async function handleBrowseDirectory(field) {
    try {
      const result = await window.api.dialog.selectDirectory();

      if (result.success && result.path) {
        archiveConfig[field] = result.path;
      }
    } catch (error) {
      console.error('Failed to browse directory:', error);
    }
  }

  async function handleSaveArchiveConfig() {
    try {
      configSaveStatus = 'saving';

      const result = await window.api.config.update({
        db_path: archiveConfig.db_path,
        staging_path: archiveConfig.staging_path,
        archive_path: archiveConfig.archive_path,
        backup_path: archiveConfig.backup_path
      });

      if (result.success) {
        archiveConfig = { ...result.data };
        configSaveStatus = 'success';
        setTimeout(() => { configSaveStatus = null; }, 2000);
      } else {
        configSaveStatus = 'error';
        setTimeout(() => { configSaveStatus = null; }, 3000);
      }
    } catch (error) {
      console.error('Failed to save archive config:', error);
      configSaveStatus = 'error';
      setTimeout(() => { configSaveStatus = null; }, 3000);
    }
  }
</script>

<div class="p-8 max-w-2xl">
  <div class="mb-6">
    <h2 class="text-2xl font-bold text-gray-800">Settings</h2>
    <p class="text-gray-600 mt-1">Configure Abandoned Upstate application</p>
  </div>

  <form on:submit={handleSubmit} class="space-y-6">
    <!-- API Settings -->
    <div class="bg-white shadow rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 mb-4">API Configuration</h3>

      <div class="space-y-4">
        <!-- AUPAT Core API URL -->
        <div>
          <label for="apiUrl" class="block text-sm font-medium text-gray-700 mb-1">
            AUPAT Core API URL
          </label>
          <input
            id="apiUrl"
            type="url"
            bind:value={currentSettings.apiUrl}
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="http://localhost:5002"
          />
        </div>

        <!-- Immich API URL -->
        <div>
          <label for="immichUrl" class="block text-sm font-medium text-gray-700 mb-1">
            Immich API URL
          </label>
          <input
            id="immichUrl"
            type="url"
            bind:value={currentSettings.immichUrl}
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="http://localhost:2283"
          />
        </div>

        <!-- ArchiveBox API URL -->
        <div>
          <label for="archiveboxUrl" class="block text-sm font-medium text-gray-700 mb-1">
            ArchiveBox API URL
          </label>
          <input
            id="archiveboxUrl"
            type="url"
            bind:value={currentSettings.archiveboxUrl}
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="http://localhost:8001"
          />
        </div>
      </div>
    </div>

    <!-- Map Settings -->
    <div class="bg-white shadow rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 mb-4">Map Defaults</h3>

      <div class="space-y-4">
        <!-- Default Latitude -->
        <div>
          <label for="mapLat" class="block text-sm font-medium text-gray-700 mb-1">
            Default Latitude
          </label>
          <input
            id="mapLat"
            type="number"
            step="0.0001"
            bind:value={currentSettings.mapCenter.lat}
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Default Longitude -->
        <div>
          <label for="mapLng" class="block text-sm font-medium text-gray-700 mb-1">
            Default Longitude
          </label>
          <input
            id="mapLng"
            type="number"
            step="0.0001"
            bind:value={currentSettings.mapCenter.lng}
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Default Zoom -->
        <div>
          <label for="mapZoom" class="block text-sm font-medium text-gray-700 mb-1">
            Default Zoom Level (1-18)
          </label>
          <input
            id="mapZoom"
            type="number"
            min="1"
            max="18"
            bind:value={currentSettings.mapZoom}
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>

    <!-- Archive Paths Configuration -->
    <div class="bg-white shadow rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 mb-2">Archive Paths</h3>
      <p class="text-sm text-gray-600 mb-4">
        Configure where media files are staged, archived, and backed up during the import workflow.
      </p>

      <div class="space-y-4">
        <!-- Database Path -->
        <div>
          <label for="dbPath" class="block text-sm font-medium text-gray-700 mb-1">
            Database Path
          </label>
          <div class="flex gap-2">
            <input
              id="dbPath"
              type="text"
              bind:value={archiveConfig.db_path}
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="/home/user/aupat/data/aupat.db"
            />
          </div>
          <p class="text-xs text-gray-500 mt-1">Path to SQLite database file</p>
        </div>

        <!-- Staging Path -->
        <div>
          <label for="stagingPath" class="block text-sm font-medium text-gray-700 mb-1">
            Staging Directory
          </label>
          <div class="flex gap-2">
            <input
              id="stagingPath"
              type="text"
              bind:value={archiveConfig.staging_path}
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="/home/user/aupat/data/ingest"
            />
            <button
              type="button"
              on:click={() => handleBrowseDirectory('staging_path')}
              class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Browse
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-1">Temporary staging area for imports (STEP 2)</p>
        </div>

        <!-- Archive Path -->
        <div>
          <label for="archivePath" class="block text-sm font-medium text-gray-700 mb-1">
            Archive Directory
          </label>
          <div class="flex gap-2">
            <input
              id="archivePath"
              type="text"
              bind:value={archiveConfig.archive_path}
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="/home/user/aupat/data/archive"
            />
            <button
              type="button"
              on:click={() => handleBrowseDirectory('archive_path')}
              class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Browse
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-1">Final archive location (STEP 5)</p>
        </div>

        <!-- Backup Path -->
        <div>
          <label for="backupPath" class="block text-sm font-medium text-gray-700 mb-1">
            Backup Directory
          </label>
          <div class="flex gap-2">
            <input
              id="backupPath"
              type="text"
              bind:value={archiveConfig.backup_path}
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="/home/user/aupat/data/backups"
            />
            <button
              type="button"
              on:click={() => handleBrowseDirectory('backup_path')}
              class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Browse
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-1">Database backups before imports (STEP 0)</p>
        </div>
      </div>

      <!-- Save Archive Config Button -->
      <div class="flex items-center gap-4 mt-6 pt-4 border-t border-gray-200">
        <button
          type="button"
          on:click={handleSaveArchiveConfig}
          class="px-6 py-2 bg-brown-600 text-white rounded-md hover:bg-brown-700 focus:outline-none focus:ring-2 focus:ring-brown-500 focus:ring-offset-2"
        >
          Save Archive Paths
        </button>

        {#if configSaveStatus === 'saving'}
          <span class="text-sm text-gray-600">Saving...</span>
        {:else if configSaveStatus === 'success'}
          <span class="text-sm text-green-600">Archive paths saved successfully</span>
        {:else if configSaveStatus === 'error'}
          <span class="text-sm text-red-600">Failed to save archive paths</span>
        {/if}
      </div>
    </div>

    <!-- Import Settings (v0.1.5) -->
    <div class="bg-white shadow rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 mb-4">Import Settings</h3>

      <div class="space-y-4">
        <!-- Delete Import Media -->
        <div class="flex items-center">
          <input
            id="deleteImportMedia"
            type="checkbox"
            bind:checked={currentSettings.deleteImportMedia}
            on:change={() => handleSave('deleteImportMedia', currentSettings.deleteImportMedia)}
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label for="deleteImportMedia" class="ml-2 block text-sm text-gray-900">
            Delete source files after successful import
          </label>
        </div>
        <p class="text-sm text-gray-500 ml-6">
          When enabled, original media files will be deleted from the source directory after being successfully imported into the archive. Use with caution.
        </p>
      </div>
    </div>

    <!-- Map Import -->
    <div class="bg-white shadow rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 mb-2">Map Import</h3>
      <p class="text-sm text-gray-600 mb-4">
        Import locations from CSV, JSON, GeoJSON, KML, or KMZ files
      </p>

      <button
        type="button"
        on:click={openMapImport}
        class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
      >
        Import Map File
      </button>
    </div>

    <!-- Save Button -->
    <div class="flex items-center gap-4">
      <button
        type="submit"
        class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        Save Settings
      </button>

      {#if saveStatus === 'saving'}
        <span class="text-sm text-gray-600">Saving...</span>
      {:else if saveStatus === 'success'}
        <span class="text-sm text-green-600">Settings saved successfully</span>
      {:else if saveStatus === 'error'}
        <span class="text-sm text-red-600">Failed to save settings</span>
      {/if}
    </div>
  </form>
</div>

<!-- Map Import Dialog -->
<MapImportDialog
  bind:isOpen={showMapImport}
  on:close={() => showMapImport = false}
  on:imported={handleMapImported}
/>
