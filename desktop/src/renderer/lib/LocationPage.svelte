<script>
  /**
   * Abandoned Upstate - Location Page Component
   *
   * Dedicated full-page view for each location with blog-style layout.
   * Inspired by abandonedupstate.com design system.
   *
   * Features:
   * - Hero image (full-width)
   * - Dashboard-style WHO/WHAT/WHERE/WHEN/WHY sections
   * - Rich narrative with markdown support
   * - Image gallery
   * - Archived URLs with ArchiveBox integration
   * - Related locations
   * - Print-friendly layout
   */

  import { onMount, createEventDispatcher } from 'svelte';
  import { marked } from 'marked';
  import LocationForm from './LocationForm.svelte';
  import NotesSection from './NotesSection.svelte';
  import SubLocationsList from './SubLocationsList.svelte';
  import DocumentsList from './DocumentsList.svelte';
  import NerdStats from './NerdStats.svelte';

  export let locationUuid;

  const dispatch = createEventDispatcher();

  // Edit/Import state
  let showEditForm = false;
  let showImportDialog = false;
  let importSourcePath = '';
  let importInProgress = false;
  let importError = null;
  let importBatchId = null;
  let importWorkflowResults = [];
  let importCompleted = false;

  // State
  let location = null;
  let images = [];
  let videos = [];
  let documents = [];
  let notes = [];
  let subLocations = [];
  let archivedUrls = [];
  let relatedLocations = [];
  let loading = true;
  let error = null;
  let selectedImage = null;

  // URL archiving state
  let newUrl = '';
  let newUrlTitle = '';
  let newUrlDescription = '';
  let archiving = false;
  let urlsError = null;

  onMount(async () => {
    await loadLocationData();
  });

  async function loadLocationData() {
    loading = true;
    error = null;

    try {
      // Load location details
      const locResponse = await window.api.locations.getById(locationUuid);
      if (!locResponse.success) {
        error = locResponse.error || 'Location not found';
        return;
      }
      location = locResponse.data;

      // Extract sub-locations from response
      if (location.sub_locations) {
        subLocations = location.sub_locations;
      }

      // Load associated media and data in parallel
      await Promise.all([
        loadImages(),
        loadVideos(),
        loadArchivedUrls(),
        loadRelatedLocations()
      ]);

    } catch (err) {
      console.error('Failed to load location:', err);
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function loadImages() {
    try {
      const response = await window.api.images.getByLocation(locationUuid, 100, 0);
      if (response.success) {
        const imagesWithAssets = response.data.filter(img => img.immich_asset_id);
        images = await Promise.all(
          imagesWithAssets.map(async (img) => {
            const thumbnailUrl = await window.api.images.getThumbnailUrl(img.immich_asset_id);
            const originalUrl = await window.api.images.getOriginalUrl(img.immich_asset_id);
            return { ...img, thumbnailUrl, originalUrl };
          })
        );
      }
    } catch (err) {
      console.error('Failed to load images:', err);
    }
  }

  async function loadVideos() {
    try {
      const response = await window.api.videos.getByLocation(locationUuid);
      if (response.success) {
        videos = response.data || [];
      }
    } catch (err) {
      console.error('Failed to load videos:', err);
    }
  }

  async function loadArchivedUrls() {
    try {
      const response = await window.api.urls.getByLocation(locationUuid);
      if (response.success) {
        archivedUrls = response.data || [];
      }
    } catch (err) {
      console.error('Failed to load archived URLs:', err);
    }
  }

  async function loadRelatedLocations() {
    if (!location || !location.lat || !location.lon) return;

    try {
      // Get nearby locations within 10km
      const response = await window.api.locations.getAll();
      if (response.success) {
        const allLocations = response.data || [];

        // Calculate distances and filter nearby
        relatedLocations = allLocations
          .filter(loc => loc.loc_uuid !== locationUuid && loc.lat && loc.lon)
          .map(loc => ({
            ...loc,
            distance: calculateDistance(
              location.lat,
              location.lon,
              loc.lat,
              loc.lon
            )
          }))
          .filter(loc => loc.distance <= 10) // Within 10km
          .sort((a, b) => a.distance - b.distance)
          .slice(0, 5); // Top 5 closest
      }
    } catch (err) {
      console.error('Failed to load related locations:', err);
    }
  }

  function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }

  function getHeroImage() {
    if (images.length > 0) {
      return images[0].originalUrl;
    }
    return null;
  }

  function renderMarkdown(text) {
    if (!text) return '';
    try {
      return marked(text, { breaks: true });
    } catch (err) {
      console.error('Markdown rendering error:', err);
      return text; // Fallback to plain text
    }
  }

  function goBack() {
    dispatch('close');
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

  async function archiveUrl() {
    if (!newUrl.trim()) return;

    archiving = true;
    urlsError = null;

    try {
      const response = await window.api.urls.archive({
        locationId: locationUuid,
        url: newUrl.trim(),
        title: newUrlTitle.trim() || null,
        description: newUrlDescription.trim() || null
      });

      if (response.success) {
        newUrl = '';
        newUrlTitle = '';
        newUrlDescription = '';
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

  function navigateToLocation(uuid) {
    dispatch('navigate', { uuid });
  }

  function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  }

  function getGpsConfidenceLabel(confidence) {
    switch (confidence) {
      case 'precise': return 'Precise GPS';
      case 'city': return 'Approximate (City Center)';
      case 'county': return 'Approximate (County Center)';
      case 'state': return 'Approximate (State Center)';
      default: return 'Location Data';
    }
  }

  async function handleLocationUpdated(event) {
    showEditForm = false;
    // Reload location data to show updated information
    await loadLocationData();
  }

  function handleEditFormClosed() {
    showEditForm = false;
  }

  function handleImportDialogClosed() {
    // Reset import state when closing
    showImportDialog = false;
    importSourcePath = '';
    importInProgress = false;
    importError = null;
    importBatchId = null;
    importWorkflowResults = [];
    importCompleted = false;
  }

  async function handleBrowseDirectory() {
    try {
      const result = await window.api.dialog.selectDirectory();

      if (result.success && result.path) {
        importSourcePath = result.path;
        importError = null;
      } else if (!result.canceled) {
        importError = result.error || 'Failed to select directory';
      }
    } catch (err) {
      console.error('Failed to browse directory:', err);
      importError = err.message || 'Failed to open directory picker';
    }
  }

  async function handleStartImport() {
    if (!importSourcePath) {
      importError = 'Please select a source directory';
      return;
    }

    importInProgress = true;
    importError = null;
    importWorkflowResults = [];
    importCompleted = false;

    try {
      const result = await window.api.import.bulkImport({
        locationId: locationUuid,
        sourcePath: importSourcePath,
        author: 'desktop-app'
      });

      if (result.success) {
        importBatchId = result.data.batch_id;
        importWorkflowResults = result.data.workflow_results || [];
        importCompleted = true;

        // Reload images and videos to show newly imported media
        await Promise.all([
          loadImages(),
          loadVideos()
        ]);
      } else {
        importError = result.error || 'Import failed';
      }
    } catch (err) {
      console.error('Import failed:', err);
      importError = err.message || 'Import failed';
    } finally {
      importInProgress = false;
    }
  }

  function getStepStatus(stepName) {
    const result = importWorkflowResults.find(r => r.step === stepName);
    return result?.status || 'pending';
  }

  function getStepIcon(stepName) {
    const status = getStepStatus(stepName);
    if (status === 'success') return '✓';
    if (status === 'error') return '✗';
    if (status === 'skipped') return '○';
    return '○';
  }

  function getStepClass(stepName) {
    const status = getStepStatus(stepName);
    if (status === 'success') return 'text-green-600';
    if (status === 'error') return 'text-red-600';
    if (status === 'skipped') return 'text-gray-400';
    return 'text-gray-400';
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<article class="location-page">
  {#if loading}
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading location...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <h2>Location Not Found</h2>
      <p>{error}</p>
      <button class="au-btn au-btn-primary" on:click={goBack}>
        &larr; Back to Map
      </button>
    </div>
  {:else if location}
    <!-- Hero Image -->
    <header class="hero">
      {#if getHeroImage()}
        <img src={getHeroImage()} alt={location.loc_name} class="hero-image" />
      {:else}
        <div class="hero-placeholder">
          <div class="hero-icon">🏚️</div>
          <p class="hero-placeholder-text">No Image</p>
        </div>
      {/if}
      <button class="back-button au-btn au-btn-outline" on:click={goBack}>
        &larr; Back to Map
      </button>
      <div class="action-buttons">
        <button class="edit-button au-btn au-btn-primary" on:click={() => showEditForm = true}>
          Edit Location
        </button>
        <button class="import-button au-btn au-btn-brown" on:click={() => showImportDialog = true}>
          Import Media
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="content">
      <div class="content-container">
        <!-- Location Title -->
        <div class="title-section">
          <h1 class="location-title">{location.loc_name}</h1>
          {#if location.aka_name}
            <p class="aka-name">Also known as: {location.aka_name}</p>
          {/if}

          <div class="metadata-badges">
            {#if location.type}
              <span class="au-badge au-badge-brown">{location.type}</span>
            {/if}
            {#if location.sub_type}
              <span class="au-badge au-badge-gray">{location.sub_type}</span>
            {/if}
            {#if location.state}
              <span class="au-badge au-badge-black">{location.state}</span>
            {/if}
            {#if location.gps_confidence}
              <span class="au-badge au-badge-gray">
                {location.gps_confidence === 'precise' ? '📍' : '⊙'}
                {getGpsConfidenceLabel(location.gps_confidence)}
              </span>
            {/if}
          </div>
        </div>

        <hr class="au-section-divider" />

        <!-- THE STORY -->
        {#if location.notes}
          <section class="content-section">
            <h2>The Story</h2>
            <div class="au-prose">
              {@html renderMarkdown(location.notes)}
            </div>
          </section>

          <hr class="au-section-divider" />
        {/if}

        <!-- WHERE -->
        <section class="content-section">
          <h2>Where</h2>
          <div class="info-grid">
            {#if location.street_address}
              <div class="info-item">
                <span class="info-label">Street Address</span>
                <span class="info-value">{location.street_address}</span>
              </div>
            {/if}
            {#if location.city}
              <div class="info-item">
                <span class="info-label">City</span>
                <span class="info-value">{location.city}</span>
              </div>
            {/if}
            {#if location.county}
              <div class="info-item">
                <span class="info-label">County</span>
                <span class="info-value">{location.county}</span>
              </div>
            {/if}
            {#if location.state}
              <div class="info-item">
                <span class="info-label">State</span>
                <span class="info-value">{location.state}</span>
              </div>
            {/if}
            {#if location.zip_code}
              <div class="info-item">
                <span class="info-label">ZIP Code</span>
                <span class="info-value">{location.zip_code}</span>
              </div>
            {/if}
            {#if location.lat && location.lon}
              <div class="info-item">
                <span class="info-label">GPS Coordinates</span>
                <span class="info-value font-mono">
                  {location.lat.toFixed(6)}°N, {location.lon.toFixed(6)}°W
                </span>
              </div>
            {/if}
          </div>
        </section>

        <hr class="au-section-divider" />

        <!-- WHEN -->
        <section class="content-section">
          <h2>When</h2>
          <div class="info-grid">
            {#if location.built_date}
              <div class="info-item">
                <span class="info-label">Built</span>
                <span class="info-value">{location.built_date}</span>
              </div>
            {/if}
            {#if location.abandoned_date}
              <div class="info-item">
                <span class="info-label">Abandoned</span>
                <span class="info-value">{location.abandoned_date}</span>
              </div>
            {/if}
            {#if location.last_visited}
              <div class="info-item">
                <span class="info-label">Last Visited</span>
                <span class="info-value">{formatDate(location.last_visited)}</span>
              </div>
            {/if}
            {#if location.loc_add}
              <div class="info-item">
                <span class="info-label">Added to Archive</span>
                <span class="info-value">{formatDate(location.loc_add)}</span>
              </div>
            {/if}
            {#if location.loc_update}
              <div class="info-item">
                <span class="info-label">Last Updated</span>
                <span class="info-value">{formatDate(location.loc_update)}</span>
              </div>
            {/if}
          </div>
        </section>

        <hr class="au-section-divider" />

        <!-- IMAGES -->
        {#if images.length > 0}
          <section class="content-section">
            <h2>Images ({images.length})</h2>
            <div class="image-gallery">
              {#each images as image}
                <button
                  on:click={() => openLightbox(image)}
                  class="gallery-item"
                >
                  <img
                    src={image.thumbnailUrl}
                    alt={image.img_name}
                    loading="lazy"
                  />
                </button>
              {/each}
            </div>
          </section>

          <hr class="au-section-divider" />
        {/if}

        <!-- VIDEOS -->
        {#if videos.length > 0}
          <section class="content-section">
            <h2>Videos ({videos.length})</h2>
            <div class="video-list">
              {#each videos as video}
                <div class="video-item au-card">
                  <p class="font-mono">{video.vid_name}</p>
                  {#if video.vid_notes}
                    <p class="au-text-muted text-sm">{video.vid_notes}</p>
                  {/if}
                </div>
              {/each}
            </div>
          </section>

          <hr class="au-section-divider" />
        {/if}

        <!-- ARCHIVED URLS -->
        <section class="content-section">
          <h2>Archived URLs ({archivedUrls.length})</h2>

          <!-- Add URL Form -->
          <div class="url-form au-card" style="margin-bottom: 1.5rem;">
            <h4>Add URL to Archive</h4>
            <input
              type="url"
              bind:value={newUrl}
              placeholder="https://example.com"
              class="url-input"
            />
            <input
              type="text"
              bind:value={newUrlTitle}
              placeholder="Title (optional)"
              class="url-input"
            />
            <textarea
              bind:value={newUrlDescription}
              placeholder="Description (optional)"
              rows="3"
              class="url-textarea"
            />
            <button
              on:click={archiveUrl}
              disabled={!newUrl.trim() || archiving}
              class="au-btn au-btn-primary"
            >
              {archiving ? 'Archiving...' : 'Archive URL'}
            </button>
          </div>

          <!-- Error Message -->
          {#if urlsError}
            <div class="error-message">{urlsError}</div>
          {/if}

          <!-- URLs List -->
          {#if archivedUrls.length === 0}
            <p class="au-text-muted">No archived URLs yet.</p>
          {:else}
            <div class="urls-list">
              {#each archivedUrls as archivedUrl}
                <div class="url-item au-card">
                  <div class="url-content">
                    <a
                      href={archivedUrl.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      class="url-link"
                    >
                      {archivedUrl.url_title || archivedUrl.url}
                    </a>
                    {#if archivedUrl.url_title}
                      <p class="url-actual au-text-caption">{archivedUrl.url}</p>
                    {/if}
                    {#if archivedUrl.url_desc}
                      <p class="url-desc au-text-muted">{archivedUrl.url_desc}</p>
                    {/if}
                    <div class="url-meta">
                      <span class="au-badge au-badge-gray">
                        {archivedUrl.archive_status || 'pending'}
                      </span>
                      {#if archivedUrl.archive_date}
                        <span class="au-text-caption">
                          Archived {formatDate(archivedUrl.archive_date)}
                        </span>
                      {/if}
                    </div>
                  </div>
                  <button
                    on:click={() => deleteUrl(archivedUrl.url_uuid)}
                    class="url-delete"
                    title="Delete URL"
                  >
                    ✕
                  </button>
                </div>
              {/each}
            </div>
          {/if}
        </section>

        <!-- RELATED LOCATIONS -->
        {#if relatedLocations.length > 0}
          <hr class="au-section-divider" />

          <section class="content-section">
            <h2>Nearby Locations</h2>
            <div class="related-locations">
              {#each relatedLocations as related}
                <button
                  on:click={() => navigateToLocation(related.loc_uuid)}
                  class="related-item au-card au-card-hover"
                >
                  <div class="related-content">
                    <h4>{related.loc_name}</h4>
                    <div class="related-meta">
                      {#if related.type}
                        <span class="au-badge au-badge-gray">{related.type}</span>
                      {/if}
                      <span class="au-text-caption">
                        {related.distance.toFixed(1)} km away
                      </span>
                    </div>
                  </div>
                </button>
              {/each}
            </div>
          </section>
        {/if}

        <!-- SUB-LOCATIONS -->
        <hr class="au-section-divider" />
        <section class="content-section">
          <SubLocationsList
            subLocations={subLocations}
            locationName={location?.loc_name || ''}
          />
        </section>

        <!-- NOTES -->
        <hr class="au-section-divider" />
        <section class="content-section">
          <NotesSection locationUuid={locationUuid} />
        </section>

        <!-- DOCUMENTS -->
        <hr class="au-section-divider" />
        <section class="content-section">
          <DocumentsList documents={documents} locationUuid={locationUuid} />
        </section>

        <!-- NERD STATS -->
        <hr class="au-section-divider" />
        <section class="content-section">
          <NerdStats
            {location}
            imagesCount={images.length}
            videosCount={videos.length}
            documentsCount={documents.length}
            notesCount={notes.length}
            subLocationsCount={subLocations.length}
          />
        </section>
      </div>
    </main>
  {/if}
</article>

<!-- Lightbox Modal -->
{#if selectedImage}
  <div
    role="dialog"
    aria-modal="true"
    class="lightbox"
    on:click={closeLightbox}
    on:keydown={handleKeydown}
  >
    <button
      on:click={closeLightbox}
      class="lightbox-close"
      aria-label="Close lightbox"
    >
      ✕
    </button>

    <div class="lightbox-content" on:click={(e) => e.stopPropagation()} on:keydown={(e) => e.stopPropagation()}>
      <img
        src={selectedImage.originalUrl}
        alt={selectedImage.img_name}
        class="lightbox-image"
      />

      <div class="lightbox-meta">
        <p class="font-mono">{selectedImage.img_name}</p>
        {#if selectedImage.img_width && selectedImage.img_height}
          <p class="au-text-caption">
            {selectedImage.img_width} × {selectedImage.img_height}
          </p>
        {/if}
        {#if selectedImage.gps_lat && selectedImage.gps_lon}
          <p class="au-text-caption">
            GPS: {selectedImage.gps_lat.toFixed(6)}, {selectedImage.gps_lon.toFixed(6)}
          </p>
        {/if}
      </div>
    </div>
  </div>
{/if}

<!-- Edit Location Form -->
<LocationForm
  isOpen={showEditForm}
  mode="edit"
  location={location}
  on:updated={handleLocationUpdated}
  on:close={handleEditFormClosed}
/>

<!-- Import Media Dialog (placeholder for now) -->
{#if showImportDialog}
  <div
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    on:click={handleImportDialogClosed}
    on:keydown={(e) => e.key === 'Escape' && handleImportDialogClosed()}
    role="dialog"
    aria-modal="true"
  >
    <div
      class="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6"
      on:click|stopPropagation
      on:keydown|stopPropagation
    >
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-800">Import Media</h2>
        <button
          on:click={handleImportDialogClosed}
          class="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="space-y-4">
        <!-- Directory Selection -->
        {#if !importCompleted}
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Source Directory
            </label>
            <div class="flex gap-2">
              <input
                type="text"
                bind:value={importSourcePath}
                placeholder="/path/to/media"
                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={importInProgress}
              />
              <button
                on:click={handleBrowseDirectory}
                class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:bg-gray-400"
                disabled={importInProgress}
              >
                Browse
              </button>
            </div>
          </div>
        {/if}

        <!-- Workflow Steps Progress -->
        {#if importInProgress || importCompleted}
          <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 class="font-semibold text-gray-900 mb-3">Import Workflow Progress</h3>
            <div class="space-y-2">
              {#each [
                'STEP 2: Import to staging',
                'STEP 3: Organize and categorize',
                'STEP 4: Create archive folders',
                'STEP 5: Ingest to archive',
                'STEP 6: Verify integrity'
              ] as step}
                <div class="flex items-center gap-2">
                  <span class="{getStepClass(step)} font-bold text-lg w-6">
                    {getStepIcon(step)}
                  </span>
                  <span class="text-sm {getStepClass(step)}">
                    {step}
                  </span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Success Message -->
        {#if importCompleted && !importError}
          <div class="bg-green-50 border border-green-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <span class="text-green-600 text-xl">✓</span>
              <div class="flex-1">
                <h3 class="font-semibold text-green-900 mb-1">Import Completed Successfully</h3>
                <p class="text-sm text-green-800">
                  All 6 workflow steps completed. Media files have been imported, organized, and archived.
                </p>
                {#if importBatchId}
                  <p class="text-xs text-green-700 mt-2 font-mono">
                    Batch ID: {importBatchId}
                  </p>
                {/if}
              </div>
            </div>
          </div>
        {/if}

        <!-- Error Message -->
        {#if importError}
          <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <span class="text-red-600 text-xl">✗</span>
              <div class="flex-1">
                <h3 class="font-semibold text-red-900 mb-1">Import Failed</h3>
                <p class="text-sm text-red-800">{importError}</p>
              </div>
            </div>
          </div>
        {/if}

        <!-- Info Box -->
        {#if !importInProgress && !importCompleted}
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 class="font-semibold text-blue-900 mb-2">6-Step Archive Workflow</h3>
            <p class="text-sm text-blue-800 mb-3">
              This import process follows the exact workflow from the archive scripts:
            </p>
            <ol class="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>Database backup</li>
              <li>Import to staging (SHA256 deduplication)</li>
              <li>Extract EXIF & categorize hardware (phone/DSLR/drone)</li>
              <li>Create archive folder structure</li>
              <li>Hardlink staging → archive</li>
              <li>Verify SHA256 integrity</li>
            </ol>
          </div>
        {/if}

        <!-- Action Buttons -->
        <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            on:click={handleImportDialogClosed}
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:bg-gray-200"
            disabled={importInProgress}
          >
            {importCompleted ? 'Close' : 'Cancel'}
          </button>
          {#if !importCompleted}
            <button
              on:click={handleStartImport}
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300 disabled:cursor-not-allowed"
              disabled={importInProgress || !importSourcePath}
            >
              {importInProgress ? 'Importing...' : 'Start Import'}
            </button>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  /* === LAYOUT === */
  .location-page {
    min-height: 100vh;
    background: var(--au-bg-primary);
  }

  .loading-state,
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 50vh;
    padding: var(--au-space-8);
    text-align: center;
  }

  .loading-spinner {
    width: 48px;
    height: 48px;
    border: 4px solid var(--au-border-color);
    border-top-color: var(--au-accent-brown);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* === HERO === */
  .hero {
    position: relative;
    width: 100%;
    height: 60vh;
    min-height: 400px;
    max-height: 600px;
    background: var(--au-dark-gray);
    overflow: hidden;
  }

  .hero-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .hero-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--au-dark-gray) 0%, var(--au-text-dark) 100%);
  }

  .hero-icon {
    font-size: 6rem;
    margin-bottom: var(--au-space-4);
    opacity: 0.5;
  }

  .hero-placeholder-text {
    font-family: var(--au-font-mono);
    color: var(--au-text-light);
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .back-button {
    position: absolute;
    top: var(--au-space-6);
    left: var(--au-space-6);
    z-index: 10;
    background: rgba(0, 0, 0, 0.7);
    color: var(--au-white);
    border-color: var(--au-white);
    backdrop-filter: blur(4px);
  }

  .back-button:hover {
    background: var(--au-accent-brown);
    border-color: var(--au-accent-brown);
  }

  .action-buttons {
    position: absolute;
    top: var(--au-space-6);
    right: var(--au-space-6);
    z-index: 10;
    display: flex;
    gap: var(--au-space-3);
  }

  .edit-button,
  .import-button {
    background: rgba(0, 0, 0, 0.7);
    border-color: var(--au-white);
    color: var(--au-white);
    backdrop-filter: blur(4px);
  }

  .edit-button:hover {
    background: var(--au-accent-brown);
    border-color: var(--au-accent-brown);
  }

  .import-button:hover {
    background: rgba(185, 151, 92, 0.9);
    border-color: var(--au-accent-brown);
  }

  /* === CONTENT === */
  .content {
    padding: var(--au-space-12) var(--au-space-6);
  }

  .content-container {
    max-width: 900px;
    margin: 0 auto;
  }

  .title-section {
    margin-bottom: var(--au-space-8);
  }

  .location-title {
    font-size: var(--au-text-5xl);
    margin-bottom: var(--au-space-3);
    line-height: 1.1;
  }

  .aka-name {
    font-style: italic;
    color: var(--au-text-secondary);
    margin-bottom: var(--au-space-4);
  }

  .metadata-badges {
    display: flex;
    flex-wrap: wrap;
    gap: var(--au-space-2);
  }

  .content-section {
    margin-bottom: var(--au-space-8);
  }

  /* === INFO GRID === */
  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: var(--au-space-4);
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: var(--au-space-1);
  }

  .info-label {
    font-family: var(--au-font-mono);
    font-size: var(--au-text-xs);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--au-text-secondary);
  }

  .info-value {
    font-size: var(--au-text-base);
    color: var(--au-text-primary);
  }

  /* === IMAGE GALLERY === */
  .image-gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: var(--au-space-4);
  }

  .gallery-item {
    position: relative;
    aspect-ratio: 1;
    overflow: hidden;
    border-radius: var(--au-border-radius-lg);
    cursor: pointer;
    transition: transform var(--au-transition-base);
    border: none;
    padding: 0;
    background: var(--au-bg-tertiary);
  }

  .gallery-item:hover {
    transform: scale(1.05);
  }

  .gallery-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  /* === VIDEO LIST === */
  .video-list {
    display: flex;
    flex-direction: column;
    gap: var(--au-space-3);
  }

  .video-item {
    padding: var(--au-space-4);
  }

  /* === URL FORM & LIST === */
  .url-form h4 {
    margin-bottom: var(--au-space-4);
  }

  .url-input,
  .url-textarea {
    width: 100%;
    padding: var(--au-space-3);
    margin-bottom: var(--au-space-3);
    border: 1px solid var(--au-border-color);
    border-radius: var(--au-border-radius);
    font-family: var(--au-font-system);
    font-size: var(--au-text-base);
    background: var(--au-bg-primary);
    color: var(--au-text-primary);
  }

  .url-input:focus,
  .url-textarea:focus {
    outline: none;
    border-color: var(--au-accent-brown);
    box-shadow: 0 0 0 3px rgba(185, 151, 92, 0.1);
  }

  .url-textarea {
    resize: vertical;
  }

  .urls-list {
    display: flex;
    flex-direction: column;
    gap: var(--au-space-3);
  }

  .url-item {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--au-space-4);
    padding: var(--au-space-4);
  }

  .url-content {
    flex: 1;
  }

  .url-link {
    font-weight: 600;
    word-break: break-all;
  }

  .url-actual {
    margin-top: var(--au-space-1);
    word-break: break-all;
  }

  .url-desc {
    margin-top: var(--au-space-2);
  }

  .url-meta {
    display: flex;
    align-items: center;
    gap: var(--au-space-3);
    margin-top: var(--au-space-2);
  }

  .url-delete {
    background: none;
    border: none;
    color: var(--au-text-secondary);
    cursor: pointer;
    font-size: var(--au-text-xl);
    padding: var(--au-space-1);
    line-height: 1;
    transition: color var(--au-transition-fast);
  }

  .url-delete:hover {
    color: var(--au-error);
  }

  .error-message {
    background: rgba(139, 76, 76, 0.1);
    border: 1px solid var(--au-error);
    color: var(--au-error);
    padding: var(--au-space-3);
    border-radius: var(--au-border-radius);
    margin-bottom: var(--au-space-4);
  }

  /* === RELATED LOCATIONS === */
  .related-locations {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: var(--au-space-4);
  }

  .related-item {
    text-align: left;
    border: none;
    cursor: pointer;
    padding: var(--au-space-4);
  }

  .related-content h4 {
    margin-bottom: var(--au-space-2);
    text-transform: none;
    font-size: var(--au-text-lg);
  }

  .related-meta {
    display: flex;
    align-items: center;
    gap: var(--au-space-2);
    flex-wrap: wrap;
  }

  /* === LIGHTBOX === */
  .lightbox {
    position: fixed;
    inset: 0;
    z-index: var(--au-z-modal);
    background: rgba(0, 0, 0, 0.95);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--au-space-8);
  }

  .lightbox-close {
    position: absolute;
    top: var(--au-space-6);
    right: var(--au-space-6);
    background: none;
    border: none;
    color: var(--au-white);
    font-size: var(--au-text-4xl);
    cursor: pointer;
    z-index: 10;
    line-height: 1;
    padding: 0;
    transition: color var(--au-transition-fast);
  }

  .lightbox-close:hover {
    color: var(--au-accent-gold);
  }

  .lightbox-content {
    max-width: 90vw;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .lightbox-image {
    max-width: 100%;
    max-height: calc(90vh - 100px);
    object-fit: contain;
    border-radius: var(--au-border-radius-lg);
  }

  .lightbox-meta {
    margin-top: var(--au-space-4);
    text-align: center;
    color: var(--au-text-light);
  }

  .lightbox-meta p {
    margin-bottom: var(--au-space-1);
  }

  /* === UTILITIES === */
  .font-mono {
    font-family: var(--au-font-mono);
  }

  .text-sm {
    font-size: var(--au-text-sm);
  }

  /* === RESPONSIVE === */
  @media (max-width: 768px) {
    .content {
      padding: var(--au-space-8) var(--au-space-4);
    }

    .location-title {
      font-size: var(--au-text-3xl);
    }

    .hero {
      height: 40vh;
      min-height: 300px;
    }

    .back-button {
      top: var(--au-space-4);
      left: var(--au-space-4);
    }

    .action-buttons {
      top: auto;
      bottom: var(--au-space-4);
      right: var(--au-space-4);
      flex-direction: column;
    }

    .image-gallery {
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    }

    .related-locations {
      grid-template-columns: 1fr;
    }
  }

  /* === PRINT STYLES === */
  @media print {
    .back-button,
    .url-form,
    .url-delete,
    .lightbox {
      display: none !important;
    }

    .hero {
      height: 400px;
      page-break-after: avoid;
    }

    .content-section {
      page-break-inside: avoid;
    }
  }
</style>
