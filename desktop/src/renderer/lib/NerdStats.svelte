<script>
  /**
   * Nerd Stats Component
   *
   * Displays technical statistics and metadata about a location.
   * Shows counts, dates, GPS, and other nerdy details.
   *
   * LILBITS: One component = One function (stats display)
   */

  export let location = null;
  export let imagesCount = 0;
  export let videosCount = 0;
  export let documentsCount = 0;
  export let notesCount = 0;
  export let subLocationsCount = 0;

  function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function formatCoordinates(lat, lon) {
    if (!lat || !lon) return 'No GPS data';
    return `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
  }

  $: stats = [
    {
      label: 'Location UUID',
      value: location?.loc_uuid || 'N/A',
      mono: true
    },
    {
      label: 'Short Name',
      value: location?.loc_short || 'N/A'
    },
    {
      label: 'State',
      value: location?.state?.toUpperCase() || 'N/A'
    },
    {
      label: 'Type',
      value: location?.type || 'N/A',
      capitalize: true
    },
    {
      label: 'Sub-Type',
      value: location?.sub_type || 'None',
      capitalize: true
    },
    {
      label: 'GPS Coordinates',
      value: formatCoordinates(location?.lat, location?.lon),
      mono: true
    },
    {
      label: 'GPS Source',
      value: location?.gps_source || 'N/A',
      capitalize: true
    },
    {
      label: 'Created',
      value: formatDate(location?.created_at)
    },
    {
      label: 'Last Updated',
      value: formatDate(location?.updated_at)
    },
    {
      label: 'Import Author',
      value: location?.import_author || location?.imp_author || 'Unknown'
    },
    {
      label: 'Historical',
      value: location?.historical ? 'Yes' : 'No'
    },
    {
      label: 'Status',
      value: location?.status || 'Unknown',
      capitalize: true
    },
    {
      label: 'Explored',
      value: location?.explored || 'Unknown',
      capitalize: true
    }
  ];

  $: mediaCounts = [
    { label: 'Images', value: imagesCount, color: 'blue' },
    { label: 'Videos', value: videosCount, color: 'purple' },
    { label: 'Documents', value: documentsCount, color: 'green' },
    { label: 'Notes', value: notesCount, color: 'yellow' },
    { label: 'Sub-Locations', value: subLocationsCount, color: 'orange' }
  ];

  $: totalMedia = imagesCount + videosCount + documentsCount;
</script>

<div class="nerd-stats-section bg-white rounded-lg shadow-md p-6">
  <h2 class="text-xl font-bold text-gray-800 mb-4">Nerd Stats</h2>

  <!-- Media Counts -->
  <div class="mb-6">
    <h3 class="text-sm font-semibold text-gray-700 mb-3">Media Summary</h3>
    <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
      {#each mediaCounts as item}
        <div class="stat-card bg-gray-50 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold" style="color: var(--au-accent-brown, #b9975c);">
            {item.value}
          </div>
          <div class="text-xs text-gray-600 mt-1">{item.label}</div>
        </div>
      {/each}
    </div>
  </div>

  <!-- Total -->
  <div class="mb-6 p-4 bg-gray-50 rounded-lg">
    <div class="flex items-center justify-between">
      <span class="text-sm font-semibold text-gray-700">Total Media Files</span>
      <span class="text-2xl font-bold" style="color: var(--au-accent-brown, #b9975c);">
        {totalMedia}
      </span>
    </div>
  </div>

  <!-- Location Details -->
  <div class="mb-4">
    <h3 class="text-sm font-semibold text-gray-700 mb-3">Location Details</h3>
    <div class="space-y-2">
      {#each stats as stat}
        <div class="stat-row flex items-start justify-between py-2 border-b border-gray-100">
          <span class="text-sm text-gray-600 font-medium">{stat.label}</span>
          <span
            class="text-sm text-gray-900 text-right max-w-xs break-all"
            class:font-mono={stat.mono}
            class:capitalize={stat.capitalize}
          >
            {stat.value}
          </span>
        </div>
      {/each}
    </div>
  </div>

  <!-- Address if available -->
  {#if location?.street_address || location?.city || location?.zip_code || location?.county}
    <div class="mt-6 p-4 bg-gray-50 rounded-lg">
      <h3 class="text-sm font-semibold text-gray-700 mb-2">Address</h3>
      <div class="text-sm text-gray-900">
        {#if location.street_address}
          <div>{location.street_address}</div>
        {/if}
        <div>
          {#if location.city}{location.city},{/if}
          {#if location.state}{location.state.toUpperCase()}{/if}
          {#if location.zip_code}{location.zip_code}{/if}
        </div>
        {#if location.county}
          <div class="text-gray-600 mt-1">{location.county} County</div>
        {/if}
        {#if location.region}
          <div class="text-gray-600">{location.region}</div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .font-mono {
    font-family: 'Courier New', Courier, monospace;
    font-size: 0.85em;
  }

  .stat-card {
    transition: transform 0.2s;
  }

  .stat-card:hover {
    transform: translateY(-2px);
  }
</style>
