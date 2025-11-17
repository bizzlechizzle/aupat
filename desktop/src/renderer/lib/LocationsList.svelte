<script>
  /**
   * Locations List View
   *
   * Table view of all locations with search and CRUD operations.
   */

  import { onMount } from 'svelte';
  import { locations } from '../stores/locations.js';
  import LocationForm from './LocationForm.svelte';
  import MapImportDialog from './MapImportDialog.svelte';

  let locationItems = [];
  let loading = false;
  let searchQuery = '';
  let showForm = false;
  let formMode = 'create';
  let selectedLocation = null;
  let showMapImport = false;

  onMount(async () => {
    loading = true;
    await locations.fetchAll();
    loading = false;
  });

  locations.subscribe(state => {
    locationItems = state.items;
    loading = state.loading;
  });

  // Filter locations by search query
  $: filteredLocations = locationItems.filter(loc => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      loc.loc_name?.toLowerCase().includes(query) ||
      loc.aka_name?.toLowerCase().includes(query) ||
      loc.type?.toLowerCase().includes(query) ||
      loc.state?.toLowerCase().includes(query) ||
      loc.city?.toLowerCase().includes(query)
    );
  });

  function openCreateForm() {
    formMode = 'create';
    selectedLocation = null;
    showForm = true;
  }

  function openEditForm(location) {
    formMode = 'edit';
    selectedLocation = location;
    showForm = true;
  }

  async function handleDelete(location) {
    if (!confirm(`Are you sure you want to delete "${location.loc_name}"?`)) {
      return;
    }

    try {
      await locations.delete(location.loc_uuid);
    } catch (error) {
      alert(`Failed to delete location: ${error.message}`);
    }
  }

  function handleFormClose() {
    showForm = false;
    selectedLocation = null;
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
</script>

<div class="p-8">
  <div class="mb-6 flex items-center justify-between">
    <div>
      <h2 class="text-2xl font-bold text-gray-800">All Locations</h2>
      <p class="text-gray-600 mt-1">
        {filteredLocations.length} of {locationItems.length} location{locationItems.length !== 1 ? 's' : ''}
      </p>
    </div>
    <div class="flex gap-3">
      <button
        on:click={openMapImport}
        class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
      >
        Import Map
      </button>
      <button
        on:click={openCreateForm}
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Add Location
      </button>
    </div>
  </div>

  <!-- Search Bar -->
  <div class="mb-4">
    <input
      type="text"
      bind:value={searchQuery}
      placeholder="Search locations..."
      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    />
  </div>

  {#if loading}
    <p class="text-gray-600">Loading...</p>
  {:else if locationItems.length === 0}
    <div class="bg-gray-50 rounded-lg p-8 text-center">
      <p class="text-gray-600">No locations found</p>
      <p class="text-sm text-gray-500 mt-2">Import some locations to get started</p>
    </div>
  {:else}
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Name
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              State
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              GPS
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each filteredLocations as location}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {location.loc_name}
                {#if location.aka_name}
                  <span class="text-gray-500 font-normal">({location.aka_name})</span>
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                {location.type || '-'}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 uppercase">
                {location.state || '-'}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {#if location.lat && location.lon}
                  {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
                {:else}
                  -
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                <button
                  on:click={() => openEditForm(location)}
                  class="text-blue-600 hover:text-blue-900"
                >
                  Edit
                </button>
                <button
                  on:click={() => handleDelete(location)}
                  class="text-red-600 hover:text-red-900"
                >
                  Delete
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<!-- Location Form Modal -->
<LocationForm
  bind:isOpen={showForm}
  mode={formMode}
  location={selectedLocation}
  on:close={handleFormClose}
  on:created={handleFormClose}
  on:updated={handleFormClose}
/>

<!-- Map Import Dialog -->
<MapImportDialog
  bind:isOpen={showMapImport}
  on:close={() => showMapImport = false}
  on:imported={handleMapImported}
/>
