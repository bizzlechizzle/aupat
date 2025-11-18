<script>
  /**
   * Browser View Component
   *
   * Embedded Chromium browser for researching locations and archiving web pages.
   * Uses Electron BrowserView with browser-manager.js backend.
   *
   * Features:
   * - URL navigation with address bar
   * - Back/forward/reload controls
   * - Bookmark current page (saves to AUPAT database)
   * - Archive current page (sends to ArchiveBox)
   * - Cookie export for archiving
   */

  import { onMount, onDestroy } from 'svelte';

  // Browser state
  let currentUrl = 'https://www.google.com';
  let urlInput = '';
  let currentTitle = '';
  let canGoBack = false;
  let canGoForward = false;
  let isLoading = false;

  // Bookmark state
  let showBookmarkDialog = false;
  let bookmarkTitle = '';
  let bookmarkTags = '';
  let bookmarkFolder = '';

  // Archive state
  let showArchiveDialog = false;
  let archiveLocationId = '';
  let locations = [];

  let browserCreated = false;
  let error = null;

  onMount(async () => {
    try {
      // Create browser view via IPC
      const result = await window.api.browser.create();
      if (!result.success) {
        error = result.error || 'Failed to create browser view';
        return;
      }

      browserCreated = true;
      urlInput = currentUrl;

      // Navigate to initial URL
      await navigateToUrl(currentUrl);

      // Set up event listeners for browser updates
      window.api.browser.onUrlChanged((url) => {
        currentUrl = url;
        urlInput = url;
      });

      window.api.browser.onTitleChanged((title) => {
        currentTitle = title;
      });

      window.api.browser.onLoadStart(() => {
        isLoading = true;
      });

      window.api.browser.onLoadStop(() => {
        isLoading = false;
      });

      window.api.browser.onCanGoBack((can) => {
        canGoBack = can;
      });

      window.api.browser.onCanGoForward((can) => {
        canGoForward = can;
      });

      // Load locations for archive dialog
      await loadLocations();

    } catch (err) {
      console.error('Browser initialization failed:', err);
      error = err.message;
    }
  });

  onDestroy(() => {
    // Browser view is managed by main process, don't destroy here
    // It will be cleaned up when window closes
  });

  async function loadLocations() {
    try {
      const response = await window.api.locations.getAll();
      if (response.success) {
        locations = response.data || [];
      }
    } catch (err) {
      console.error('Failed to load locations:', err);
    }
  }

  async function navigateToUrl(url) {
    try {
      // Add https:// if no protocol specified
      if (!url.match(/^https?:\/\//)) {
        url = 'https://' + url;
      }

      const result = await window.api.browser.navigate(url);
      if (!result.success) {
        error = result.error;
      }
    } catch (err) {
      console.error('Navigation failed:', err);
      error = err.message;
    }
  }

  function handleUrlSubmit(event) {
    event.preventDefault();
    if (urlInput.trim()) {
      navigateToUrl(urlInput.trim());
    }
  }

  async function goBack() {
    try {
      await window.api.browser.goBack();
    } catch (err) {
      console.error('Go back failed:', err);
    }
  }

  async function goForward() {
    try {
      await window.api.browser.goForward();
    } catch (err) {
      console.error('Go forward failed:', err);
    }
  }

  async function reload() {
    try {
      await window.api.browser.reload();
    } catch (err) {
      console.error('Reload failed:', err);
    }
  }

  function openBookmarkDialog() {
    bookmarkTitle = currentTitle || currentUrl;
    bookmarkTags = '';
    bookmarkFolder = '';
    showBookmarkDialog = true;
  }

  async function saveBookmark() {
    try {
      const response = await window.api.bookmarks.create({
        url: currentUrl,
        title: bookmarkTitle,
        tags: bookmarkTags,
        folder: bookmarkFolder,
        browser: 'aupat-internal'
      });

      if (response.success) {
        showBookmarkDialog = false;
        // Show success message (could add toast notification)
      } else {
        error = response.error || 'Failed to save bookmark';
      }
    } catch (err) {
      console.error('Save bookmark failed:', err);
      error = err.message;
    }
  }

  function openArchiveDialog() {
    showArchiveDialog = true;
  }

  async function archivePage() {
    try {
      if (!archiveLocationId) {
        error = 'Please select a location';
        return;
      }

      // Send to ArchiveBox via API
      const response = await window.api.urls.archive({
        loc_uuid: archiveLocationId,
        url: currentUrl,
        title: currentTitle || currentUrl
      });

      if (response.success) {
        showArchiveDialog = false;
        // Show success message
      } else {
        error = response.error || 'Failed to archive page';
      }
    } catch (err) {
      console.error('Archive failed:', err);
      error = err.message;
    }
  }
</script>

<div class="browser-container h-full flex flex-col bg-white">
  <!-- Toolbar -->
  <div class="toolbar bg-gray-100 border-b border-gray-300 p-2 flex items-center gap-2">
    <!-- Navigation buttons -->
    <button
      on:click={goBack}
      disabled={!canGoBack}
      class="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
      title="Back"
    >
      ←
    </button>

    <button
      on:click={goForward}
      disabled={!canGoForward}
      class="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
      title="Forward"
    >
      →
    </button>

    <button
      on:click={reload}
      class="p-2 rounded hover:bg-gray-200"
      title="Reload"
    >
      ↻
    </button>

    <!-- URL bar -->
    <form on:submit={handleUrlSubmit} class="flex-1 flex">
      <input
        type="text"
        bind:value={urlInput}
        placeholder="Enter URL or search..."
        class="flex-1 px-3 py-1 border border-gray-300 rounded-l focus:outline-none focus:border-blue-500"
      />
      <button
        type="submit"
        class="px-4 py-1 bg-blue-500 text-white rounded-r hover:bg-blue-600"
      >
        Go
      </button>
    </form>

    <!-- Bookmark button -->
    <button
      on:click={openBookmarkDialog}
      class="p-2 rounded hover:bg-gray-200"
      title="Bookmark this page"
    >
      ⭐
    </button>

    <!-- Archive button -->
    <button
      on:click={openArchiveDialog}
      class="p-2 rounded hover:bg-gray-200"
      title="Archive this page"
    >
      📦
    </button>
  </div>

  <!-- Loading indicator -->
  {#if isLoading}
    <div class="h-1 bg-blue-500 animate-pulse"></div>
  {/if}

  <!-- Error message -->
  {#if error}
    <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-3">
      <button on:click={() => error = null} class="float-right">×</button>
      <strong>Error:</strong> {error}
    </div>
  {/if}

  <!-- Browser content area -->
  <div class="flex-1 bg-gray-50 flex items-center justify-center">
    {#if browserCreated}
      <div class="text-gray-500">
        <p class="text-center">Browser view is displayed in the window above this content.</p>
        <p class="text-sm text-center mt-2">Current page: {currentTitle || currentUrl}</p>
      </div>
    {:else if error}
      <div class="text-red-500">
        <p>Browser failed to initialize</p>
      </div>
    {:else}
      <div class="text-gray-500">
        <p>Loading browser...</p>
      </div>
    {/if}
  </div>
</div>

<!-- Bookmark Dialog -->
{#if showBookmarkDialog}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-96 max-w-full">
      <h2 class="text-xl font-bold mb-4">Save Bookmark</h2>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-1">URL</label>
          <input
            type="text"
            value={currentUrl}
            disabled
            class="w-full px-3 py-2 border border-gray-300 rounded bg-gray-100"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Title</label>
          <input
            type="text"
            bind:value={bookmarkTitle}
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Folder</label>
          <input
            type="text"
            bind:value={bookmarkFolder}
            placeholder="e.g., Research, Locations, etc."
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Tags (comma-separated)</label>
          <input
            type="text"
            bind:value={bookmarkTags}
            placeholder="abandoned, industrial, etc."
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div class="flex justify-end gap-2 mt-6">
        <button
          on:click={() => showBookmarkDialog = false}
          class="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          on:click={saveBookmark}
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Save Bookmark
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Archive Dialog -->
{#if showArchiveDialog}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-96 max-w-full">
      <h2 class="text-xl font-bold mb-4">Archive Page</h2>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-1">URL</label>
          <input
            type="text"
            value={currentUrl}
            disabled
            class="w-full px-3 py-2 border border-gray-300 rounded bg-gray-100"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Associate with Location *</label>
          <select
            bind:value={archiveLocationId}
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
          >
            <option value="">Select a location...</option>
            {#each locations as location}
              <option value={location.loc_uuid}>
                {location.loc_name} ({location.state})
              </option>
            {/each}
          </select>
        </div>
      </div>

      <div class="flex justify-end gap-2 mt-6">
        <button
          on:click={() => showArchiveDialog = false}
          class="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          on:click={archivePage}
          class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Archive Page
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .browser-container {
    position: relative;
  }

  .toolbar {
    user-select: none;
    -webkit-user-select: none;
  }
</style>
