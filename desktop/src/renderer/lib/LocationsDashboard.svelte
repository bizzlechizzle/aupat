<script>
  /**
   * Locations Dashboard
   *
   * Main dashboard view with:
   * - Quick links (Favorites, Random, Un-Documented, Historical, To-Do)
   * - Pinned locations (top 5)
   * - Recent locations (last 5)
   * - Recently updated (last 5)
   * - Top states (top 5)
   * - Top types (top 10)
   */

  import { onMount, createEventDispatcher } from 'svelte';
  import LocationCard from './LocationCard.svelte';
  import StatsCard from './StatsCard.svelte';

  const dispatch = createEventDispatcher();

  let stats = {
    pinned: [],
    recent: [],
    updated: [],
    states: [],
    types: [],
    counts: {
      total: 0,
      favorites: 0,
      undocumented: 0,
      historical: 0,
      with_notes: 0
    }
  };

  let loading = true;
  let error = null;

  onMount(async () => {
    await loadStats();
  });

  async function loadStats() {
    try {
      loading = true;
      error = null;
      const response = await window.api.stats.getDashboard();

      if (response && response.success) {
        stats = response.data;
      } else {
        error = response?.error || 'Failed to load dashboard statistics';
      }
    } catch (err) {
      console.error('Failed to load stats:', err);
      error = err.message || 'Failed to load dashboard statistics';
    } finally {
      loading = false;
    }
  }

  function handleLocationClick(event) {
    dispatch('locationClick', event.detail);
  }

  function handleStateClick(event) {
    // Filter locations by state
    dispatch('filterByState', { state: event.detail.item.state });
  }

  function handleTypeClick(event) {
    // Filter locations by type
    dispatch('filterByType', { type: event.detail.item.type });
  }

  async function handleRandomClick() {
    try {
      const response = await window.api.stats.getRandom();
      if (response && response.success && response.data) {
        dispatch('locationClick', { location: response.data });
      }
    } catch (err) {
      console.error('Failed to get random location:', err);
    }
  }

  function handleQuickLinkClick(filter) {
    dispatch('quickLink', { filter });
  }
</script>

<div class="dashboard p-8 bg-gray-50 min-h-full">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-2">Locations Dashboard</h1>
    <p class="text-gray-600">
      Total Locations: <span class="font-semibold">{stats.counts.total}</span>
    </p>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-20">
      <div class="text-gray-500">Loading dashboard...</div>
    </div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <p class="text-red-800 font-semibold">Error loading dashboard</p>
      <p class="text-red-600 text-sm mt-1">{error}</p>
      <button
        on:click={loadStats}
        class="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
      >
        Retry
      </button>
    </div>
  {:else}
    <!-- Quick Links -->
    <div class="mb-8">
      <h2 class="text-xl font-bold text-gray-800 mb-4">Quick Links</h2>
      <div class="flex flex-wrap gap-3">
        <button
          on:click={() => handleQuickLinkClick('favorites')}
          class="quick-link-btn px-6 py-3 bg-white rounded-lg shadow-md hover:shadow-lg transition-all font-semibold"
          style="color: var(--au-accent-brown, #b9975c);"
        >
          ⭐ Favorites ({stats.counts.favorites})
        </button>
        <button
          on:click={handleRandomClick}
          class="quick-link-btn px-6 py-3 bg-white rounded-lg shadow-md hover:shadow-lg transition-all font-semibold"
          style="color: var(--au-accent-brown, #b9975c);"
        >
          🎲 Random Location
        </button>
        <button
          on:click={() => handleQuickLinkClick('undocumented')}
          class="quick-link-btn px-6 py-3 bg-white rounded-lg shadow-md hover:shadow-lg transition-all font-semibold"
          style="color: var(--au-accent-brown, #b9975c);"
        >
          📝 Un-Documented ({stats.counts.undocumented})
        </button>
        <button
          on:click={() => handleQuickLinkClick('historical')}
          class="quick-link-btn px-6 py-3 bg-white rounded-lg shadow-md hover:shadow-lg transition-all font-semibold"
          style="color: var(--au-accent-brown, #b9975c);"
        >
          🏛️ Historical ({stats.counts.historical})
        </button>
        <button
          on:click={() => handleQuickLinkClick('with_notes')}
          class="quick-link-btn px-6 py-3 bg-white rounded-lg shadow-md hover:shadow-lg transition-all font-semibold"
          style="color: var(--au-accent-brown, #b9975c);"
        >
          📋 With Notes ({stats.counts.with_notes})
        </button>
      </div>
    </div>

    <!-- Pinned Locations -->
    {#if stats.pinned && stats.pinned.length > 0}
      <section class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-800">Pinned Locations</h2>
          <button class="text-sm hover:underline" style="color: var(--au-accent-brown, #b9975c);">
            View All →
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {#each stats.pinned as location}
            <LocationCard {location} on:click={handleLocationClick} />
          {/each}
        </div>
      </section>
    {/if}

    <!-- Recent and Updated in 2 columns -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
      <!-- Recent Locations -->
      <section>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-800">Recent Locations</h2>
          <button class="text-sm hover:underline" style="color: var(--au-accent-brown, #b9975c);">
            View All →
          </button>
        </div>
        <div class="space-y-3">
          {#if stats.recent && stats.recent.length > 0}
            {#each stats.recent as location}
              <LocationCard {location} showDate={true} dateLabel="Added" on:click={handleLocationClick} />
            {/each}
          {:else}
            <p class="text-gray-500 text-sm">No recent locations</p>
          {/if}
        </div>
      </section>

      <!-- Recently Updated -->
      <section>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-800">Recently Updated</h2>
          <button class="text-sm hover:underline" style="color: var(--au-accent-brown, #b9975c);">
            View All →
          </button>
        </div>
        <div class="space-y-3">
          {#if stats.updated && stats.updated.length > 0}
            {#each stats.updated as location}
              <LocationCard {location} showDate={true} dateLabel="Updated" on:click={handleLocationClick} />
            {/each}
          {:else}
            <p class="text-gray-500 text-sm">No recently updated locations</p>
          {/if}
        </div>
      </section>
    </div>

    <!-- States and Types in 2 columns -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <StatsCard
        title="Top States"
        items={stats.states}
        on:itemClick={handleStateClick}
      />
      <StatsCard
        title="Top Types"
        items={stats.types}
        type="grid"
        on:itemClick={handleTypeClick}
      />
    </div>
  {/if}
</div>

<style>
  .quick-link-btn:hover {
    transform: translateY(-2px);
  }
</style>
