<script>
  /**
   * Stats Card Component
   *
   * Displays statistics in a card format.
   * Used for states and types statistics in dashboard.
   */

  import { createEventDispatcher } from 'svelte';

  export let title = '';
  export let items = [];
  export let type = 'list'; // 'list' or 'grid'

  const dispatch = createEventDispatcher();

  function handleItemClick(item) {
    dispatch('itemClick', { item });
  }
</script>

<div class="stats-card bg-white rounded-lg shadow-md p-6">
  <h3 class="text-xl font-bold text-gray-800 mb-4">{title}</h3>

  {#if items.length === 0}
    <p class="text-gray-500 text-sm">No data available</p>
  {:else}
    <div class={type === 'grid' ? 'grid grid-cols-2 gap-3' : 'space-y-2'}>
      {#each items as item}
        <button
          on:click={() => handleItemClick(item)}
          class="stat-item flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors text-left w-full"
        >
          <span class="font-medium text-gray-700 capitalize">
            {item.state || item.type || item.name || 'Unknown'}
          </span>
          <span class="text-sm px-3 py-1 rounded-full font-semibold" style="background-color: var(--au-accent-brown, #b9975c); color: white;">
            {item.count}
          </span>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .stat-item:hover {
    transform: translateX(4px);
  }
</style>
