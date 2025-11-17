<script>
  /**
   * Locations List View
   *
   * Table view of all locations with search and CRUD operations.
   * This is a stub implementation.
   */

  import { onMount } from 'svelte';
  import { locations } from '../stores/locations.js';

  let locationItems = [];
  let loading = false;

  onMount(async () => {
    loading = true;
    await locations.fetchAll();
    loading = false;
  });

  locations.subscribe(state => {
    locationItems = state.items;
    loading = state.loading;
  });
</script>

<div class="p-8">
  <div class="mb-6">
    <h2 class="text-2xl font-bold text-gray-800">All Locations</h2>
    <p class="text-gray-600 mt-1">
      {locationItems.length} location{locationItems.length !== 1 ? 's' : ''}
    </p>
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
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each locationItems as location}
            <tr class="hover:bg-gray-50 cursor-pointer">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {location.loc_name}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                {location.type || '-'}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {location.state || '-'}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {#if location.lat && location.lon}
                  {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
                {:else}
                  -
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
