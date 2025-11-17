<script>
  /**
   * AUPAT Desktop - Root Component
   *
   * Main app container with sidebar navigation and content area
   */

  import { onMount } from 'svelte';
  import Map from './lib/Map.svelte';
  import LocationsList from './lib/LocationsList.svelte';
  import Settings from './lib/Settings.svelte';
  import { locations } from './stores/locations.js';
  import logo from './assets/logo.png';

  // Current active view
  let currentView = 'map'; // 'map', 'locations', 'import', 'settings'

  // Navigation menu items
  const menuItems = [
    { id: 'map', label: 'Map View' },
    { id: 'locations', label: 'Locations' },
    { id: 'import', label: 'Import' },
    { id: 'settings', label: 'Settings' }
  ];

  // Health check status
  let healthStatus = null;

  onMount(async () => {
    // Check API health on startup
    try {
      const response = await window.api.health.check();
      healthStatus = response.success ? 'healthy' : 'error';
    } catch (error) {
      console.error('Health check failed:', error);
      healthStatus = 'error';
    }

    // Load locations
    locations.fetchAll();
  });

  function setView(view) {
    currentView = view;
  }
</script>

<div class="flex h-screen bg-gray-50">
  <!-- Sidebar Navigation -->
  <aside class="w-64 bg-white shadow-lg flex flex-col">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200 flex flex-col items-center">
      <img src={logo} alt="Abandoned Upstate" class="w-24 h-24 object-contain mb-3" />
      <p class="text-sm text-gray-600 font-medium">Archive Tool</p>
    </div>

    <!-- Navigation Menu -->
    <nav class="flex-1 p-4 space-y-2">
      {#each menuItems as item}
        <button
          on:click={() => setView(item.id)}
          class="w-full px-4 py-3 rounded-lg text-left transition-colors {currentView === item.id
            ? 'bg-blue-50 text-blue-700 font-medium'
            : 'text-gray-700 hover:bg-gray-50'}"
        >
          {item.label}
        </button>
      {/each}
    </nav>

    <!-- Footer with health status -->
    <div class="p-4 border-t border-gray-200">
      <div class="flex items-center gap-2 text-sm">
        <div
          class="w-2 h-2 rounded-full {healthStatus === 'healthy'
            ? 'bg-green-500'
            : healthStatus === 'error'
            ? 'bg-red-500'
            : 'bg-gray-300'}"
        />
        <span class="text-gray-600">
          {healthStatus === 'healthy'
            ? 'API Connected'
            : healthStatus === 'error'
            ? 'API Offline'
            : 'Checking...'}
        </span>
      </div>
    </div>
  </aside>

  <!-- Main Content Area -->
  <main class="flex-1 overflow-hidden">
    {#if currentView === 'map'}
      <Map />
    {:else if currentView === 'locations'}
      <LocationsList />
    {:else if currentView === 'import'}
      <div class="p-8">
        <h2 class="text-2xl font-bold mb-4">Import</h2>
        <p class="text-gray-600">Import interface coming in next iteration...</p>
      </div>
    {:else if currentView === 'settings'}
      <Settings />
    {/if}
  </main>
</div>
