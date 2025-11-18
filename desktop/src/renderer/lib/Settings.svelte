<script>
  /**
   * Settings Page
   *
   * Configure API URLs, map defaults, and application preferences.
   */

  import { onMount } from 'svelte';
  import { settings } from '../stores/settings.js';

  let currentSettings = {
    apiUrl: '',
    immichUrl: '',
    archiveboxUrl: '',
    mapCenter: { lat: 0, lng: 0 },
    mapZoom: 10
  };

  let saveStatus = null; // null, 'saving', 'success', 'error'

  onMount(async () => {
    await settings.load();
  });

  settings.subscribe(s => {
    currentSettings = { ...s };
  });

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
</script>

<div class="p-8 max-w-2xl">
  <div class="mb-6">
    <h2 class="text-2xl font-bold text-gray-800">Settings</h2>
    <p class="text-gray-600 mt-1">Configure AUPAT Desktop application</p>
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
