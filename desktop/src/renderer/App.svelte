<script>
  /**
   * Abandoned Upstate - Root Component
   *
   * Main app container with sidebar navigation and content area
   */

  import { onMount } from 'svelte';
  import ErrorBoundary from './lib/ErrorBoundary.svelte';
  import Map from './lib/Map.svelte';
  import LocationsList from './lib/LocationsList.svelte';
  import LocationPage from './lib/LocationPage.svelte';
  import Import from './lib/Import.svelte';
  import Settings from './lib/Settings.svelte';
  import Bookmarks from './lib/Bookmarks.svelte';
  import { locations } from './stores/locations.js';
  import logo from './assets/logo.png';
  import './styles/theme.css';

  // Current active view
  let currentView = 'map'; // 'map', 'locations', 'location-page', 'import', 'bookmarks', 'settings'
  let selectedLocationUuid = null;

  // Navigation menu items
  const menuItems = [
    { id: 'map', label: 'Map View' },
    { id: 'locations', label: 'Locations' },
    { id: 'bookmarks', label: 'Bookmarks' },
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
    // Clear selected location when switching away from location page
    if (view !== 'location-page') {
      selectedLocationUuid = null;
    }
  }

  function navigateToLocation(uuid) {
    selectedLocationUuid = uuid;
    currentView = 'location-page';
  }

  function handleLocationClick(event) {
    const { location } = event.detail;
    if (location && location.loc_uuid) {
      navigateToLocation(location.loc_uuid);
    }
  }

  function handleLocationPageClose() {
    // Return to map view
    currentView = 'map';
    selectedLocationUuid = null;
  }

  function handleLocationPageNavigate(event) {
    const { uuid } = event.detail;
    navigateToLocation(uuid);
  }

  function handleError(event) {
    console.error('App-level error:', event.detail);
    // Could send to error reporting service here
  }
</script>

<ErrorBoundary on:error={handleError}>
<div class="flex h-screen bg-gray-50">
  <!-- Sidebar Navigation -->
  <aside class="w-64 bg-white shadow-lg flex flex-col">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200 flex flex-col items-center">
      <img src={logo} alt="Abandoned Upstate" class="w-40 h-40 object-contain mb-3" />
      <p class="text-sm text-gray-600 font-medium" style="font-family: var(--au-font-mono); text-transform: uppercase; letter-spacing: 0.05em;">Abandoned Upstate</p>
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
  <main class="flex-1 overflow-auto {currentView === 'location-page' ? 'location-page-view' : ''}">
    {#if currentView === 'map'}
      <ErrorBoundary fallbackMessage="Map view encountered an error">
        <Map on:locationClick={handleLocationClick} />
      </ErrorBoundary>
    {:else if currentView === 'locations'}
      <ErrorBoundary fallbackMessage="Locations list encountered an error">
        <LocationsList on:locationClick={handleLocationClick} />
      </ErrorBoundary>
    {:else if currentView === 'location-page' && selectedLocationUuid}
      <ErrorBoundary fallbackMessage="Location page encountered an error">
        <LocationPage
          locationUuid={selectedLocationUuid}
          on:close={handleLocationPageClose}
          on:navigate={handleLocationPageNavigate}
        />
      </ErrorBoundary>
    {:else if currentView === 'bookmarks'}
      <ErrorBoundary fallbackMessage="Bookmarks view encountered an error">
        <Bookmarks />
      </ErrorBoundary>
    {:else if currentView === 'import'}
      <ErrorBoundary fallbackMessage="Import view encountered an error">
        <Import />
      </ErrorBoundary>
    {:else if currentView === 'settings'}
      <ErrorBoundary fallbackMessage="Settings encountered an error">
        <Settings />
      </ErrorBoundary>
    {/if}
  </main>
</div>
</ErrorBoundary>
