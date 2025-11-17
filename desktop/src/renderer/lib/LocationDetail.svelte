<script>
  /**
   * Location Detail Sidebar
   *
   * Shows location metadata and photo gallery with Immich thumbnails.
   */

  import { onMount } from 'svelte';

  export let location;
  export let onClose;

  let images = [];
  let loading = true;
  let error = null;
  let selectedImage = null;

  // URL archiving state
  let archivedUrls = [];
  let urlsLoading = false;
  let urlsError = null;
  let newUrl = '';
  let newUrlTitle = '';
  let newUrlDescription = '';
  let archiving = false;

  onMount(async () => {
    await Promise.all([
      loadImages(),
      loadArchivedUrls()
    ]);
  });

  async function loadImages() {
    loading = true;
    error = null;

    try {
      const response = await window.api.images.getByLocation(location.loc_uuid, 50, 0);

      if (response.success) {
        // Filter images that have Immich asset IDs
        const imagesWithAssets = response.data.filter(img => img.immich_asset_id);

        // Get thumbnail URLs for each image
        images = await Promise.all(
          imagesWithAssets.map(async (img) => {
            const thumbnailUrl = await window.api.images.getThumbnailUrl(img.immich_asset_id);
            const originalUrl = await window.api.images.getOriginalUrl(img.immich_asset_id);

            return {
              ...img,
              thumbnailUrl,
              originalUrl
            };
          })
        );
      } else {
        error = response.error;
      }
    } catch (err) {
      console.error('Failed to load images:', err);
      error = err.message;
    } finally {
      loading = false;
    }
  }

  function openLightbox(image) {
    selectedImage = image;
  }

  function closeLightbox() {
    selectedImage = null;
  }

  function handleKeydown(event) {
    if (event.key === 'Escape' && selectedImage) {
      closeLightbox();
    }
  }

  async function loadArchivedUrls() {
    urlsLoading = true;
    urlsError = null;

    try {
      const response = await window.api.urls.getByLocation(location.loc_uuid);

      if (response.success) {
        archivedUrls = response.data || [];
      } else {
        urlsError = response.error;
      }
    } catch (err) {
      console.error('Failed to load archived URLs:', err);
      urlsError = err.message;
    } finally {
      urlsLoading = false;
    }
  }

  async function archiveUrl() {
    if (!newUrl.trim()) return;

    archiving = true;
    urlsError = null;

    try {
      const response = await window.api.urls.archive({
        locationId: location.loc_uuid,
        url: newUrl.trim(),
        title: newUrlTitle.trim() || null,
        description: newUrlDescription.trim() || null
      });

      if (response.success) {
        // Clear form
        newUrl = '';
        newUrlTitle = '';
        newUrlDescription = '';

        // Reload URLs
        await loadArchivedUrls();
      } else {
        urlsError = response.error;
      }
    } catch (err) {
      console.error('Failed to archive URL:', err);
      urlsError = err.message;
    } finally {
      archiving = false;
    }
  }

  async function deleteUrl(urlUuid) {
    if (!confirm('Are you sure you want to delete this archived URL?')) return;

    try {
      const response = await window.api.urls.delete(urlUuid);

      if (response.success) {
        await loadArchivedUrls();
      } else {
        urlsError = response.error;
      }
    } catch (err) {
      console.error('Failed to delete URL:', err);
      urlsError = err.message;
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="absolute top-0 right-0 h-full w-96 bg-white shadow-2xl z-10 overflow-y-auto">
  <!-- Header -->
  <div class="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
    <h2 class="text-xl font-bold text-gray-800">Location Details</h2>
    <button
      on:click={onClose}
      class="text-gray-500 hover:text-gray-700 text-2xl leading-none"
    >
      &times;
    </button>
  </div>

  <!-- Content -->
  <div class="p-4 space-y-4">
    <!-- Location Name -->
    <div>
      <h3 class="text-lg font-semibold text-gray-900">{location.loc_name}</h3>
      {#if location.type}
        <p class="text-sm text-gray-600 capitalize">{location.type}</p>
      {/if}
    </div>

    <!-- GPS Coordinates -->
    {#if location.lat && location.lon}
      <div class="text-sm">
        <p class="text-gray-600">
          GPS: {location.lat.toFixed(6)}, {location.lon.toFixed(6)}
        </p>
      </div>
    {/if}

    <!-- Address -->
    {#if location.street_address || location.city || location.state}
      <div class="text-sm text-gray-600">
        <p>{location.street_address || ''}</p>
        <p>
          {location.city || ''}{location.city && location.state ? ', ' : ''}{location.state || ''}
          {location.zip_code || ''}
        </p>
      </div>
    {/if}

    <!-- Photo Gallery -->
    <div class="mt-6">
      <h4 class="text-sm font-medium text-gray-700 mb-2">
        Photos ({images.length})
      </h4>

      {#if loading}
        <div class="bg-gray-100 rounded-lg p-8 text-center text-gray-500">
          Loading photos...
        </div>
      {:else if error}
        <div class="bg-red-50 rounded-lg p-4 text-sm text-red-600">
          Failed to load photos: {error}
        </div>
      {:else if images.length === 0}
        <div class="bg-gray-100 rounded-lg p-8 text-center text-gray-500">
          No photos with Immich assets found
        </div>
      {:else}
        <div class="grid grid-cols-2 gap-2">
          {#each images as image}
            <button
              on:click={() => openLightbox(image)}
              class="relative aspect-square overflow-hidden rounded-lg bg-gray-100 hover:opacity-90 transition-opacity cursor-pointer group"
            >
              <img
                src={image.thumbnailUrl}
                alt={image.img_name}
                class="w-full h-full object-cover"
                loading="lazy"
              />
              <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all" />
            </button>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Archived URLs Section -->
    <div class="mt-6">
      <h4 class="text-sm font-medium text-gray-700 mb-2">
        Archived URLs ({archivedUrls.length})
      </h4>

      <!-- Add URL Form -->
      <div class="bg-gray-50 rounded-lg p-3 mb-3">
        <input
          type="url"
          bind:value={newUrl}
          placeholder="https://example.com"
          class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <input
          type="text"
          bind:value={newUrlTitle}
          placeholder="Title (optional)"
          class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <textarea
          bind:value={newUrlDescription}
          placeholder="Description (optional)"
          rows="2"
          class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-2 resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          on:click={archiveUrl}
          disabled={!newUrl.trim() || archiving}
          class="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {archiving ? 'Archiving...' : 'Archive URL'}
        </button>
      </div>

      <!-- Error Message -->
      {#if urlsError}
        <div class="bg-red-50 rounded-lg p-3 text-sm text-red-600 mb-3">
          {urlsError}
        </div>
      {/if}

      <!-- URLs List -->
      {#if urlsLoading}
        <div class="bg-gray-100 rounded-lg p-8 text-center text-gray-500">
          Loading URLs...
        </div>
      {:else if archivedUrls.length === 0}
        <div class="bg-gray-100 rounded-lg p-8 text-center text-gray-500">
          No archived URLs yet
        </div>
      {:else}
        <div class="space-y-2">
          {#each archivedUrls as archivedUrl}
            <div class="bg-white border border-gray-200 rounded-lg p-3">
              <div class="flex items-start justify-between gap-2">
                <div class="flex-1 min-w-0">
                  <a
                    href={archivedUrl.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-sm text-blue-600 hover:text-blue-800 break-all block"
                  >
                    {archivedUrl.url_title || archivedUrl.url}
                  </a>
                  {#if archivedUrl.url_title}
                    <p class="text-xs text-gray-500 break-all mt-1">{archivedUrl.url}</p>
                  {/if}
                  {#if archivedUrl.url_desc}
                    <p class="text-xs text-gray-600 mt-1">{archivedUrl.url_desc}</p>
                  {/if}
                  <div class="flex items-center gap-3 mt-1">
                    <span class="text-xs text-gray-500 capitalize">
                      {archivedUrl.archive_status || 'pending'}
                    </span>
                    {#if archivedUrl.archive_date}
                      <span class="text-xs text-gray-400">
                        {new Date(archivedUrl.archive_date).toLocaleDateString()}
                      </span>
                    {/if}
                  </div>
                </div>
                <button
                  on:click={() => deleteUrl(archivedUrl.url_uuid)}
                  class="text-gray-400 hover:text-red-600 flex-shrink-0"
                  title="Delete URL"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fill-rule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Lightbox Modal -->
{#if selectedImage}
  <div
    role="dialog"
    aria-modal="true"
    class="fixed inset-0 z-50 bg-black bg-opacity-90 flex items-center justify-center"
    on:click={closeLightbox}
    on:keydown={handleKeydown}
  >
    <button
      on:click={closeLightbox}
      class="absolute top-4 right-4 text-white text-3xl hover:text-gray-300 z-10"
      aria-label="Close lightbox"
    >
      &times;
    </button>

    <div
      role="document"
      class="max-w-7xl max-h-screen p-4"
      on:click={(e) => e.stopPropagation()}
      on:keydown={(e) => e.stopPropagation()}
    >
      <img
        src={selectedImage.originalUrl}
        alt={selectedImage.img_name}
        class="max-w-full max-h-screen object-contain"
      />

      <!-- Image metadata -->
      <div class="mt-4 text-white text-sm text-center">
        <p class="font-medium">{selectedImage.img_name}</p>
        {#if selectedImage.img_width && selectedImage.img_height}
          <p class="text-gray-300">
            {selectedImage.img_width} x {selectedImage.img_height}
          </p>
        {/if}
        {#if selectedImage.gps_lat && selectedImage.gps_lon}
          <p class="text-gray-300">
            GPS: {selectedImage.gps_lat.toFixed(6)}, {selectedImage.gps_lon.toFixed(6)}
          </p>
        {/if}
      </div>
    </div>
  </div>
{/if}
