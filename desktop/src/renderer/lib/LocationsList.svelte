<script>
  /**
   * Locations List View
   *
   * Table view of all locations with search and CRUD operations.
   * Click on a location row to view details.
   */

  import { onMount, createEventDispatcher } from 'svelte';
  import { locations } from '../stores/locations.js';
  import LocationForm from './LocationForm.svelte';
  import LocationDetail from './LocationDetail.svelte';

  const dispatch = createEventDispatcher();

  let locationItems = [];
  let loading = false;
  let searchQuery = '';
  let showForm = false;
  let formMode = 'create';
  let selectedLocation = null;
  let detailLocation = null;

  // Filter state (v0.1.5)
  let activeFilters = {
    favorites: false,
    historical: false,
    undocumented: false
  };

  onMount(async () => {
    loading = true;
    await locations.fetchAll();
    loading = false;
  });

  locations.subscribe(state => {
    locationItems = state.items;
    loading = state.loading;
  });

  // Filter locations by search query and filters (v0.1.5)
  $: filteredLocations = locationItems.filter(loc => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesSearch = (
        loc.loc_name?.toLowerCase().includes(query) ||
        loc.aka_name?.toLowerCase().includes(query) ||
        loc.type?.toLowerCase().includes(query) ||
        loc.state?.toLowerCase().includes(query) ||
        loc.city?.toLowerCase().includes(query)
      );
      if (!matchesSearch) return false;
    }

    // Status filters
    if (activeFilters.favorites && !loc.is_favorite) return false;
    if (activeFilters.historical && !loc.is_historical) return false;
    if (activeFilters.undocumented && !loc.is_undocumented) return false;

    return true;
  });

  function toggleFilter(filterName) {
    activeFilters[filterName] = !activeFilters[filterName];
  }

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

  function openDetailView(location) {
    detailLocation = location;
  }

  function closeDetailView() {
    detailLocation = null;
  }

  function handleRowClick(location) {
    // Dispatch event to parent (App.svelte) to navigate to location page
    dispatch('locationClick', { location });

    // Optional: Also open detail view for sidebar preview
    // openDetailView(location);
  }
</script>

<div class="p-8">
  <div class="mb-6">
    <div class="flex items-center justify-between mb-3">
      <div>
        <h2 class="text-2xl font-bold text-gray-800">All Locations</h2>
        <p class="text-gray-600 mt-1">
          {filteredLocations.length} of {locationItems.length} location{locationItems.length !== 1 ? 's' : ''}
        </p>
      </div>
      <button
        on:click={openCreateForm}
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Add Location
      </button>
    </div>

    <!-- Filter Buttons -->
    <div class="flex gap-2">
      <button
        on:click={() => toggleFilter('favorites')}
        class="px-3 py-1 text-sm rounded border-2 transition {activeFilters.favorites ? 'bg-blue-500 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'}"
      >
        Favorites
      </button>
      <button
        on:click={() => toggleFilter('historical')}
        class="px-3 py-1 text-sm rounded border-2 transition {activeFilters.historical ? 'bg-blue-500 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'}"
      >
        Historical
      </button>
      <button
        on:click={() => toggleFilter('undocumented')}
        class="px-3 py-1 text-sm rounded border-2 transition {activeFilters.undocumented ? 'bg-blue-500 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'}"
      >
        Undocumented
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
            <tr
              class="hover:bg-gray-50 cursor-pointer transition-colors"
              on:click={() => handleRowClick(location)}
            >
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
                  on:click|stopPropagation={() => openEditForm(location)}
                  class="text-blue-600 hover:text-blue-900"
                >
                  Edit
                </button>
                <button
                  on:click|stopPropagation={() => handleDelete(location)}
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

<!-- Location Detail Sidebar -->
{#if detailLocation}
  <LocationDetail location={detailLocation} onClose={closeDetailView} />
{/if}
