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

  onMount(async () => {
    await loadImages();
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
