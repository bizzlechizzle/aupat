<script>
  /**
   * Browser Component
   *
   * Embedded web browser using Electron webview.
   * Allows browsing and saving bookmarks to locations.
   *
   * LILBITS: One component = One function (web browsing)
   */

  import { onMount, createEventDispatcher } from 'svelte';
  import BrowserToolbar from './BrowserToolbar.svelte';

  const dispatch = createEventDispatcher();

  let currentUrl = 'https://www.abandonedupstate.com';
  let currentTitle = '';
  let canGoBack = false;
  let canGoForward = false;
  let isLoading = false;
  let webview;

  // Bookmark state
  let showBookmarkDialog = false;
  let bookmarkData = {
    url: '',
    title: '',
    state: 'ny',
    type: 'industrial',
    loc_uuid: null
  };

  onMount(() => {
    // Get webview element
    webview = document.querySelector('webview');

    if (webview) {
      // Setup event listeners
      webview.addEventListener('did-start-loading', handleStartLoading);
      webview.addEventListener('did-stop-loading', handleStopLoading);
      webview.addEventListener('did-navigate', handleNavigate);
      webview.addEventListener('did-navigate-in-page', handleNavigate);
      webview.addEventListener('page-title-updated', handleTitleUpdate);
      webview.addEventListener('new-window', handleNewWindow);
    }

    return () => {
      if (webview) {
        webview.removeEventListener('did-start-loading', handleStartLoading);
        webview.removeEventListener('did-stop-loading', handleStopLoading);
        webview.removeEventListener('did-navigate', handleNavigate);
        webview.removeEventListener('did-navigate-in-page', handleNavigate);
        webview.removeEventListener('page-title-updated', handleTitleUpdate);
        webview.removeEventListener('new-window', handleNewWindow);
      }
    };
  });

  function handleStartLoading() {
    isLoading = true;
  }

  function handleStopLoading() {
    isLoading = false;
    updateNavigationState();
  }

  function handleNavigate(event) {
    currentUrl = event.url;
    updateNavigationState();
  }

  function handleTitleUpdate(event) {
    currentTitle = event.title;
  }

  function handleNewWindow(event) {
    // Open new windows in same webview
    if (webview) {
      webview.loadURL(event.url);
    }
  }

  function updateNavigationState() {
    if (webview) {
      canGoBack = webview.canGoBack();
      canGoForward = webview.canGoForward();
    }
  }

  function navigate(url) {
    if (webview) {
      // Ensure URL has protocol
      let finalUrl = url;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        finalUrl = 'https://' + url;
      }
      webview.loadURL(finalUrl);
      currentUrl = finalUrl;
    }
  }

  function goBack() {
    if (webview && canGoBack) {
      webview.goBack();
    }
  }

  function goForward() {
    if (webview && canGoForward) {
      webview.goForward();
    }
  }

  function reload() {
    if (webview) {
      webview.reload();
    }
  }

  function stop() {
    if (webview) {
      webview.stop();
    }
  }

  function openBookmarkDialog() {
    bookmarkData = {
      url: currentUrl,
      title: currentTitle || currentUrl,
      state: 'ny',
      type: 'industrial',
      loc_uuid: null
    };
    showBookmarkDialog = true;
  }

  function closeBookmarkDialog() {
    showBookmarkDialog = false;
  }

  async function saveBookmark() {
    try {
      const response = await window.api.bookmarks.create(bookmarkData);
      if (response && response.success) {
        closeBookmarkDialog();
        alert('Bookmark saved successfully!');
      } else {
        alert('Failed to save bookmark: ' + (response?.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Failed to save bookmark:', error);
      alert('Failed to save bookmark: ' + error.message);
    }
  }
</script>

<div class="browser h-full flex flex-col bg-white">
  <!-- Toolbar -->
  <BrowserToolbar
    url={currentUrl}
    {canGoBack}
    {canGoForward}
    {isLoading}
    on:navigate={(e) => navigate(e.detail.url)}
    on:back={goBack}
    on:forward={goForward}
    on:reload={reload}
    on:stop={stop}
    on:bookmark={openBookmarkDialog}
  />

  <!-- Webview -->
  <div class="flex-1 relative">
    <webview
      src={currentUrl}
      class="w-full h-full"
      allowpopups
    />
  </div>
</div>

<!-- Bookmark Dialog -->
{#if showBookmarkDialog}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" on:click={closeBookmarkDialog}>
    <div class="bg-white rounded-lg p-6 max-w-md w-full m-4" on:click|stopPropagation>
      <h2 class="text-2xl font-bold text-gray-900 mb-4">Save Bookmark</h2>

      <form on:submit|preventDefault={saveBookmark} class="space-y-4">
        <div>
          <label for="bookmark-title" class="block text-sm font-medium text-gray-700 mb-1">
            Title
          </label>
          <input
            id="bookmark-title"
            type="text"
            bind:value={bookmarkData.title}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
        </div>

        <div>
          <label for="bookmark-url" class="block text-sm font-medium text-gray-700 mb-1">
            URL
          </label>
          <input
            id="bookmark-url"
            type="url"
            bind:value={bookmarkData.url}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
            readonly
          />
        </div>

        <div class="flex gap-3 justify-end">
          <button
            type="button"
            on:click={closeBookmarkDialog}
            class="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="px-6 py-2 rounded-lg font-semibold text-white transition-colors"
            style="background-color: var(--au-accent-brown, #b9975c);"
          >
            Save
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
