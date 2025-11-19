<script>
  /**
   * Sub-Locations List Component
   *
   * Displays sub-locations for a location.
   * Shows name, short name, and primary indicator.
   *
   * LILBITS: One component = One function (sub-locations display)
   */

  export let subLocations = [];
  export let locationName = '';

  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function handleSubLocationClick(subLocation) {
    dispatch('sublocationClick', { subLocation });
  }
</script>

{#if subLocations && subLocations.length > 0}
  <div class="sub-locations-section bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-4">Sub-Locations</h2>
    <div class="space-y-3">
      {#each subLocations as subLoc}
        <button
          on:click={() => handleSubLocationClick(subLoc)}
          class="sub-location-item w-full text-left border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-semibold text-gray-900">
                {subLoc.sub_name}
                {#if subLoc.is_primary}
                  <span class="ml-2 text-xs font-medium px-2 py-1 rounded" style="background-color: var(--au-accent-brown, #b9975c); color: white;">
                    Primary
                  </span>
                {/if}
              </h3>
              {#if subLoc.sub_short}
                <p class="text-sm text-gray-600 mt-1">{subLoc.sub_short}</p>
              {/if}
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>
      {/each}
    </div>
  </div>
{:else}
  <div class="sub-locations-section bg-gray-50 rounded-lg p-6 text-center">
    <p class="text-gray-500">No sub-locations for {locationName}</p>
  </div>
{/if}

<style>
  .sub-location-item:hover {
    transform: translateX(2px);
  }
</style>
