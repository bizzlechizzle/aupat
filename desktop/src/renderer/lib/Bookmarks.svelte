<script>
  /**
   * Bookmarks View
   *
   * Browse, search, and manage browser bookmarks.
   * Bookmarks can be associated with locations for research organization.
   */

  import { onMount } from 'svelte';

  let bookmarks = [];
  let folders = [];
  let loading = false;
  let searchQuery = '';
  let selectedFolder = '';
  let orderBy = 'created';
  let totalCount = 0;

  // Pagination
  let limit = 100;
  let offset = 0;

  // Form state
  let showForm = false;
  let formMode = 'create';
  let selectedBookmark = null;

  onMount(async () => {
    await loadBookmarks();
    await loadFolders();
  });

  async function loadBookmarks() {
    loading = true;
    try {
      const filters = {
        limit,
        offset,
        order: orderBy
      };

      if (searchQuery) {
        filters.search = searchQuery;
      }

      if (selectedFolder) {
        filters.folder = selectedFolder;
      }

      const response = await window.api.bookmarks.getAll(filters);
      if (response.success) {
        bookmarks = response.data.bookmarks || [];
        totalCount = response.data.total || 0;
      } else {
        console.error('Failed to load bookmarks:', response.error);
        alert(`Failed to load bookmarks: ${response.error}`);
      }
    } catch (error) {
      console.error('Error loading bookmarks:', error);
      alert(`Error loading bookmarks: ${error.message}`);
    } finally {
      loading = false;
    }
  }

  async function loadFolders() {
    try {
      const response = await window.api.bookmarks.getFolders();
      if (response.success) {
        folders = response.data.folders || [];
      }
    } catch (error) {
      console.error('Error loading folders:', error);
    }
  }

  async function handleDelete(bookmark) {
    if (!confirm(`Delete bookmark "${bookmark.title || bookmark.url}"?`)) {
      return;
    }

    try {
      const response = await window.api.bookmarks.delete(bookmark.bookmark_uuid);
      if (response.success) {
        await loadBookmarks();
      } else {
        alert(`Failed to delete bookmark: ${response.error}`);
      }
    } catch (error) {
      alert(`Error deleting bookmark: ${error.message}`);
    }
  }

  function openUrl(url) {
    // Open URL in external browser
    if (url) {
      window.open(url, '_blank');
    }
  }

  function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString();
    } catch {
      return '-';
    }
  }

  function getDomain(url) {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch {
      return url;
    }
  }

  // Reactive statements
  $: {
    // Reload when filters change
    if (!loading) {
      offset = 0; // Reset to first page
      loadBookmarks();
    }
  }
</script>

<div class="p-8">
  <div class="mb-6 flex items-center justify-between">
    <div>
      <h2 class="text-2xl font-bold text-gray-800" style="font-family: var(--au-font-heading); text-transform: uppercase; letter-spacing: 0.05em;">
        Browser Bookmarks
      </h2>
      <p class="text-gray-600 mt-1">
        {totalCount} bookmark{totalCount !== 1 ? 's' : ''}
        {selectedFolder ? ` in "${selectedFolder}"` : ''}
      </p>
    </div>
  </div>

  <!-- Filters -->
  <div class="mb-4 grid grid-cols-1 md:grid-cols-3 gap-4">
    <!-- Search -->
    <input
      type="text"
      bind:value={searchQuery}
      placeholder="Search bookmarks..."
      class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    />

    <!-- Folder filter -->
    <select
      bind:value={selectedFolder}
      class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    >
      <option value="">All Folders</option>
      {#each folders as folder}
        <option value={folder}>{folder}</option>
      {/each}
    </select>

    <!-- Sort order -->
    <select
      bind:value={orderBy}
      class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    >
      <option value="created">Recently Added</option>
      <option value="updated">Recently Updated</option>
      <option value="visits">Most Visited</option>
      <option value="title">Title (A-Z)</option>
    </select>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <p class="text-gray-600">Loading bookmarks...</p>
    </div>
  {:else if bookmarks.length === 0}
    <div class="bg-gray-50 rounded-lg p-8 text-center">
      <p class="text-gray-600">No bookmarks found</p>
      <p class="text-sm text-gray-500 mt-2">
        {searchQuery || selectedFolder
          ? 'Try adjusting your filters'
          : 'Import browser bookmarks to get started'}
      </p>
    </div>
  {:else}
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Title
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Domain
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Folder
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tags
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Visits
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Added
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each bookmarks as bookmark}
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4 text-sm">
                <div class="flex flex-col">
                  <button
                    on:click={() => openUrl(bookmark.url)}
                    class="font-medium text-blue-600 hover:text-blue-900 text-left hover:underline"
                  >
                    {bookmark.title || 'Untitled'}
                  </button>
                  {#if bookmark.description}
                    <span class="text-gray-500 text-xs mt-1">{bookmark.description}</span>
                  {/if}
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {getDomain(bookmark.url)}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {bookmark.folder || '-'}
              </td>
              <td class="px-6 py-4 text-sm">
                {#if bookmark.tags && bookmark.tags.length > 0}
                  <div class="flex flex-wrap gap-1">
                    {#each bookmark.tags as tag}
                      <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                        {tag}
                      </span>
                    {/each}
                  </div>
                {:else}
                  <span class="text-gray-400">-</span>
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {bookmark.visit_count || 0}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(bookmark.created_at)}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                <button
                  on:click={() => openUrl(bookmark.url)}
                  class="text-blue-600 hover:text-blue-900"
                  title="Open URL"
                >
                  Visit
                </button>
                <button
                  on:click={() => handleDelete(bookmark)}
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

    <!-- Pagination info -->
    {#if totalCount > limit}
      <div class="mt-4 flex justify-between items-center">
        <p class="text-sm text-gray-600">
          Showing {offset + 1}-{Math.min(offset + limit, totalCount)} of {totalCount}
        </p>
        <div class="space-x-2">
          <button
            on:click={() => { offset = Math.max(0, offset - limit); loadBookmarks(); }}
            disabled={offset === 0}
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            on:click={() => { offset = offset + limit; loadBookmarks(); }}
            disabled={offset + limit >= totalCount}
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  /* Additional component-specific styles if needed */
</style>
