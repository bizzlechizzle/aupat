<script>
  /**
   * Location Card Component
   *
   * Reusable card for displaying location summary.
   * Used in dashboard for pinned, recent, and updated sections.
   */

  import { createEventDispatcher } from 'svelte';

  export let location;
  export let showDate = false;
  export let dateLabel = '';

  const dispatch = createEventDispatcher();

  function handleClick() {
    dispatch('click', { location });
  }

  // Format date to readable string
  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
</script>

<button
  on:click={handleClick}
  class="location-card bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-4 text-left w-full"
>
  <!-- Location Name -->
  <h3 class="font-semibold text-gray-900 text-lg mb-1 truncate">
    {location.loc_name || 'Unnamed Location'}
  </h3>

  <!-- Type and State -->
  <div class="flex items-center gap-2 text-sm text-gray-600 mb-2">
    <span class="capitalize">{location.type || 'Unknown'}</span>
    <span>•</span>
    <span class="uppercase">{location.state || 'N/A'}</span>
    {#if location.city}
      <span>•</span>
      <span>{location.city}</span>
    {/if}
  </div>

  <!-- Date (if requested) -->
  {#if showDate && dateLabel}
    <div class="text-xs text-gray-500">
      {dateLabel}: {formatDate(location.created_at || location.updated_at)}
    </div>
  {/if}

  <!-- GPS indicator (if available) -->
  {#if location.gps_lat && location.gps_lon}
    <div class="mt-2 flex items-center gap-1 text-xs" style="color: var(--au-accent-brown, #b9975c);">
      <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
      </svg>
      <span>GPS</span>
    </div>
  {/if}
</button>

<style>
  .location-card:hover {
    transform: translateY(-2px);
  }
</style>
