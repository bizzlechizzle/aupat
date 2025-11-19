<script>
  /**
   * Browser Toolbar Component
   *
   * Navigation toolbar for browser with URL bar and controls.
   *
   * LILBITS: One component = One function (toolbar controls)
   */

  import { createEventDispatcher } from 'svelte';

  export let url = '';
  export let canGoBack = false;
  export let canGoForward = false;
  export let isLoading = false;

  const dispatch = createEventDispatcher();

  let urlInput = url;

  // Update input when url prop changes
  $: urlInput = url;

  function handleSubmit() {
    dispatch('navigate', { url: urlInput });
  }

  function handleBack() {
    dispatch('back');
  }

  function handleForward() {
    dispatch('forward');
  }

  function handleReload() {
    if (isLoading) {
      dispatch('stop');
    } else {
      dispatch('reload');
    }
  }

  function handleBookmark() {
    dispatch('bookmark');
  }
</script>

<div class="browser-toolbar flex items-center gap-2 p-3 border-b border-gray-200 bg-gray-50">
  <!-- Back/Forward buttons -->
  <div class="flex gap-1">
    <button
      on:click={handleBack}
      disabled={!canGoBack}
      class="p-2 rounded hover:bg-gray-200 transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
      title="Go back"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>
    <button
      on:click={handleForward}
      disabled={!canGoForward}
      class="p-2 rounded hover:bg-gray-200 transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
      title="Go forward"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </button>
    <button
      on:click={handleReload}
      class="p-2 rounded hover:bg-gray-200 transition-colors"
      title={isLoading ? 'Stop' : 'Reload'}
    >
      {#if isLoading}
        <svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      {:else}
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      {/if}
    </button>
  </div>

  <!-- URL bar -->
  <form on:submit|preventDefault={handleSubmit} class="flex-1">
    <input
      type="text"
      bind:value={urlInput}
      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      placeholder="Enter URL..."
    />
  </form>

  <!-- Bookmark button -->
  <button
    on:click={handleBookmark}
    class="p-2 rounded hover:bg-gray-200 transition-colors"
    title="Save bookmark"
    style="color: var(--au-accent-brown, #b9975c);"
  >
    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
    </svg>
  </button>
</div>
