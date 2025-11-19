<script>
  /**
   * Import Interface Component
   *
   * Handles drag-and-drop file uploads for images, videos, and documents.
   * Files are associated with a location and sent to AUPAT Core API.
   */

  import { onMount } from 'svelte';
  import { locations } from '../stores/locations.js';
  import LocationForm from './LocationForm.svelte';

  // Allowed file extensions
  // Comprehensive list based on exiftool (images) and ffmpeg (videos) support
  const ALLOWED_EXTENSIONS = {
    images: [
      // Common formats
      'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tif', 'tiff', 'webp',
      // Apple formats
      'heic', 'heif',
      // RAW formats (Canon)
      'cr2', 'cr3', 'crw',
      // RAW formats (Nikon)
      'nef', 'nrw',
      // RAW formats (Sony)
      'arw', 'srf', 'sr2',
      // RAW formats (Other manufacturers)
      'orf', 'orf',      // Olympus
      'rw2', 'raw',      // Panasonic
      'raf',             // Fuji
      'pef', 'ptx',      // Pentax
      'srw',             // Samsung
      '3fr', 'fff',      // Hasselblad
      'iiq',             // Phase One
      'erf',             // Epson
      'mef',             // Mamiya
      'mrw',             // Minolta
      'rwl',             // Leica
      'dng',             // Adobe Digital Negative
      // Advanced formats
      'jp2', 'j2k', 'jpf', 'jxl',  // JPEG 2000 / JPEG XL
      'exr',             // High dynamic range
      'psd', 'psb',      // Photoshop
      'svg',             // Vector
      'ico', 'cur'       // Icons
    ],
    videos: [
      // Common formats
      'mp4', 'm4v', 'mov', 'avi', 'mkv', 'webm',
      // MPEG formats
      'mpg', 'mpeg', 'm2v', 'mp2', 'mpe', 'mpv',
      // Broadcast/camera formats
      'mts', 'm2ts', 'ts', 'mxf', 'dv',
      // Mobile formats
      '3gp', '3g2',
      // Streaming formats
      'flv', 'f4v',
      // Windows formats
      'wmv', 'asf', 'dvr-ms',
      // Other formats
      'ogv', 'ogg', 'vob', 'rm', 'rmvb', 'divx', 'xvid',
      // Alternate/legacy
      'qt', 'movie', 'amv'
    ],
    documents: ['pdf', 'txt', 'doc', 'docx']
  };

  // Component state
  let selectedLocationId = '';
  let uploadQueue = [];
  let isDragging = false;
  let showFileInput = false;
  let showLocationForm = false;
  let prefillGPS = null;

  // Sublocation state
  let sublocations = [];
  let selectedSublocationId = '';
  let createNewSublocation = false;
  let newSublocationName = '';
  let newSublocationShort = '';
  let newSublocationIsPrimary = false;

  // File input reference
  let fileInputElement;

  onMount(() => {
    // Load locations for dropdown
    locations.fetchAll();

    // Check for pre-filled GPS coordinates from map right-click
    const prefillData = window.sessionStorage.getItem('prefillGPS');
    if (prefillData) {
      try {
        prefillGPS = JSON.parse(prefillData);
        // Automatically open location form with pre-filled coordinates
        showLocationForm = true;
        // Clear session storage after using
        window.sessionStorage.removeItem('prefillGPS');
      } catch (error) {
        console.error('Failed to parse prefillGPS:', error);
      }
    }
  });

  // Load sublocations when location changes
  $: if (selectedLocationId) {
    loadSublocations(selectedLocationId);
  } else {
    sublocations = [];
    selectedSublocationId = '';
    createNewSublocation = false;
  }

  /**
   * Load sublocations for selected location
   */
  async function loadSublocations(locationId) {
    try {
      const response = await window.api.locations.getById(locationId);
      if (response.success && response.data.sub_locations) {
        sublocations = response.data.sub_locations;
      } else {
        sublocations = [];
      }
      // Reset sublocation selection
      selectedSublocationId = '';
      createNewSublocation = false;
      newSublocationName = '';
      newSublocationShort = '';
      newSublocationIsPrimary = false;
    } catch (error) {
      console.error('Failed to load sublocations:', error);
      sublocations = [];
    }
  }

  /**
   * Open location creation modal
   */
  function openCreateLocation() {
    showLocationForm = true;
  }

  /**
   * Handle location created
   */
  function handleLocationCreated(event) {
    showLocationForm = false;
    prefillGPS = null; // Clear pre-filled GPS
    const newLocation = event.detail;
    if (newLocation && newLocation.loc_uuid) {
      selectedLocationId = newLocation.loc_uuid;
    }
    // Refresh locations list
    locations.fetchAll();
  }

  /**
   * Handle location form close
   */
  function handleLocationFormClose() {
    showLocationForm = false;
    prefillGPS = null; // Clear pre-filled GPS
  }

  /**
   * Check if file extension is allowed
   */
  function isValidFile(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const allExtensions = [
      ...ALLOWED_EXTENSIONS.images,
      ...ALLOWED_EXTENSIONS.videos,
      ...ALLOWED_EXTENSIONS.documents
    ];
    return allExtensions.includes(ext);
  }

  /**
   * Get file category based on extension
   */
  function getFileCategory(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    if (ALLOWED_EXTENSIONS.images.includes(ext)) return 'image';
    if (ALLOWED_EXTENSIONS.videos.includes(ext)) return 'video';
    if (ALLOWED_EXTENSIONS.documents.includes(ext)) return 'document';
    return 'unknown';
  }

  /**
   * Handle drag over event
   */
  function handleDragOver(event) {
    event.preventDefault();
    isDragging = true;
  }

  /**
   * Handle drag leave event
   */
  function handleDragLeave(event) {
    event.preventDefault();
    isDragging = false;
  }

  /**
   * Handle keyboard activation (for accessibility)
   */
  function handleKeyPress(event) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (selectedLocationId && fileInputElement) {
        fileInputElement.click();
      }
    }
  }

  /**
   * Handle file drop
   */
  async function handleDrop(event) {
    event.preventDefault();
    isDragging = false;

    if (!selectedLocationId) {
      alert('Please select a location first');
      return;
    }

    // Use DataTransferItem API to handle folders
    const items = event.dataTransfer.items;
    if (items) {
      const files = await getAllFiles(items);
      addFilesToQueue(files);
    } else {
      // Fallback for older browsers
      const files = Array.from(event.dataTransfer.files);
      addFilesToQueue(files);
    }
  }

  /**
   * Recursively get all files from dropped items (including folders)
   */
  async function getAllFiles(items) {
    const files = [];

    async function traverseEntry(entry) {
      if (entry.isFile) {
        const file = await new Promise((resolve, reject) => {
          entry.file(resolve, reject);
        });
        files.push(file);
      } else if (entry.isDirectory) {
        const reader = entry.createReader();
        const entries = await new Promise((resolve, reject) => {
          reader.readEntries(resolve, reject);
        });
        for (const childEntry of entries) {
          await traverseEntry(childEntry);
        }
      }
    }

    for (const item of items) {
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry();
        if (entry) {
          await traverseEntry(entry);
        }
      }
    }

    return files;
  }

  /**
   * Handle file input change
   */
  function handleFileSelect(event) {
    if (!selectedLocationId) {
      alert('Please select a location first');
      event.target.value = '';
      return;
    }

    const files = Array.from(event.target.files);
    addFilesToQueue(files);
    event.target.value = '';
  }

  /**
   * Add files to upload queue
   */
  function addFilesToQueue(files) {
    const validFiles = files.filter(file => {
      if (!isValidFile(file.name)) {
        console.warn(`Skipped invalid file: ${file.name}`);
        return false;
      }
      return true;
    });

    const newItems = validFiles.map(file => ({
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file,
      locationId: selectedLocationId,
      category: getFileCategory(file.name),
      status: 'pending',
      progress: 0,
      error: null
    }));

    uploadQueue = [...uploadQueue, ...newItems];

    // Start upload process
    processQueue();
  }

  /**
   * Process upload queue
   */
  async function processQueue() {
    const pending = uploadQueue.filter(item => item.status === 'pending');

    for (const item of pending) {
      await uploadFile(item);
    }
  }

  /**
   * Upload single file
   */
  async function uploadFile(item) {
    // Update status to uploading
    uploadQueue = uploadQueue.map(i =>
      i.id === item.id ? { ...i, status: 'uploading', progress: 0 } : i
    );

    try {
      // Read file as base64 (simpler than multipart for IPC)
      const base64Data = await readFileAsBase64(item.file);

      // Simulate progress (in real implementation, this would come from API)
      updateProgress(item.id, 30);

      // Prepare sublocation data if applicable
      let sublocationData = null;
      if (createNewSublocation && newSublocationName.trim()) {
        sublocationData = {
          name: newSublocationName.trim(),
          sub_short: newSublocationShort.trim() || null,
          is_primary: newSublocationIsPrimary
        };
      }

      // Send to main process via IPC
      const response = await window.api.import.uploadFile({
        locationId: item.locationId,
        filename: item.file.name,
        category: item.category,
        size: item.file.size,
        data: base64Data,
        sub_location: sublocationData
      });

      updateProgress(item.id, 100);

      if (response && response.success) {
        uploadQueue = uploadQueue.map(i =>
          i.id === item.id ? { ...i, status: 'success', progress: 100 } : i
        );
      } else {
        // Handle error from API
        const errorMsg = response?.error || response?.message || 'Upload failed';
        throw new Error(errorMsg);
      }
    } catch (error) {
      console.error('Upload error:', error);
      uploadQueue = uploadQueue.map(i =>
        i.id === item.id
          ? { ...i, status: 'error', error: error.message }
          : i
      );
    }
  }

  /**
   * Read file as base64
   */
  function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Update upload progress
   */
  function updateProgress(id, progress) {
    uploadQueue = uploadQueue.map(item =>
      item.id === id ? { ...item, progress } : item
    );
  }

  /**
   * Retry failed upload
   */
  function retryUpload(item) {
    uploadQueue = uploadQueue.map(i =>
      i.id === item.id ? { ...i, status: 'pending', error: null, progress: 0 } : i
    );
    processQueue();
  }

  /**
   * Remove item from queue
   */
  function removeItem(id) {
    uploadQueue = uploadQueue.filter(item => item.id !== id);
  }

  /**
   * Clear completed uploads
   */
  function clearCompleted() {
    uploadQueue = uploadQueue.filter(item => item.status !== 'success');
  }

  /**
   * Format file size
   */
  function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }
</script>

<div class="h-full flex flex-col bg-gray-50">
  <!-- Header -->
  <div class="bg-white border-b border-gray-200 p-6">
    <h2 class="text-2xl font-bold text-gray-800 mb-4">Import Files</h2>

    <!-- Location Selector -->
    <div class="max-w-2xl">
      <label for="location-select" class="block text-sm font-medium text-gray-700 mb-2">
        Select Location
      </label>
      <div class="flex gap-3">
        <select
          id="location-select"
          bind:value={selectedLocationId}
          class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">-- Choose a location --</option>
          {#if $locations.loading}
            <option value="" disabled>Loading locations...</option>
          {:else if $locations.error}
            <option value="" disabled>Error: {$locations.error}</option>
          {:else if $locations.items && $locations.items.length === 0}
            <option value="" disabled>No locations found</option>
          {:else if $locations.items}
            {#each $locations.items as location}
              <option value={location.loc_uuid}>
                {location.loc_name || 'Unnamed'} ({location.type || 'Unknown'})
              </option>
            {/each}
          {/if}
        </select>
        <button
          on:click={openCreateLocation}
          class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium whitespace-nowrap"
          title="Create a new location"
        >
          + Add Location
        </button>
      </div>
      {#if $locations.items && $locations.items.length === 0 && !$locations.loading && !$locations.error}
        <p class="mt-2 text-sm text-gray-600">
          No locations found. Click "Add Location" to create your first location.
        </p>
      {/if}
      {#if $locations.error}
        <p class="mt-2 text-sm text-red-600">
          <strong>Cannot connect to backend:</strong> {$locations.error}
          <br />
          Please ensure the AUPAT API server is running (check scripts/api_routes_v012.py).
        </p>
      {/if}
    </div>

    <!-- Sub-Location Section (only shown if location is selected) -->
    {#if selectedLocationId}
      <div class="max-w-2xl mt-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Sub-Location (Optional)
        </label>

        <!-- Option to use existing or create new sublocation -->
        <div class="space-y-3">
          <div>
            <label class="flex items-center gap-2">
              <input
                type="radio"
                name="sublocation-option"
                value="none"
                checked={!createNewSublocation}
                on:change={() => {
                  createNewSublocation = false;
                  selectedSublocationId = '';
                }}
                class="text-blue-600"
              />
              <span class="text-sm">No sub-location</span>
            </label>
          </div>

          {#if sublocations && sublocations.length > 0}
            <div>
              <label class="flex items-center gap-2 mb-2">
                <input
                  type="radio"
                  name="sublocation-option"
                  value="existing"
                  checked={selectedSublocationId !== '' && !createNewSublocation}
                  on:change={() => {
                    createNewSublocation = false;
                  }}
                  class="text-blue-600"
                />
                <span class="text-sm">Use existing sub-location</span>
              </label>
              {#if selectedSublocationId !== '' || (!createNewSublocation && selectedSublocationId === '')}
                <select
                  bind:value={selectedSublocationId}
                  class="w-full ml-6 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">-- Choose sub-location --</option>
                  {#each sublocations as subloc}
                    <option value={subloc.sub_uuid}>
                      {subloc.sub_name} {subloc.is_primary ? '(Primary)' : ''}
                    </option>
                  {/each}
                </select>
              {/if}
            </div>
          {/if}

          <div>
            <label class="flex items-center gap-2 mb-2">
              <input
                type="radio"
                name="sublocation-option"
                value="new"
                bind:checked={createNewSublocation}
                class="text-blue-600"
              />
              <span class="text-sm">Create new sub-location</span>
            </label>

            {#if createNewSublocation}
              <div class="ml-6 space-y-3">
                <div>
                  <label for="sub-name" class="block text-xs text-gray-600 mb-1">
                    Sub-Location Name *
                  </label>
                  <input
                    type="text"
                    id="sub-name"
                    bind:value={newSublocationName}
                    placeholder="e.g., Basement, Main Building"
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label for="sub-short" class="block text-xs text-gray-600 mb-1">
                      Short Name
                    </label>
                    <input
                      type="text"
                      id="sub-short"
                      bind:value={newSublocationShort}
                      placeholder="e.g., basement"
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div class="flex items-end pb-2">
                    <label class="flex items-center gap-2">
                      <input
                        type="checkbox"
                        bind:checked={newSublocationIsPrimary}
                        class="rounded text-blue-600"
                      />
                      <span class="text-sm text-gray-700">Primary Sub-Location</span>
                    </label>
                  </div>
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Upload Area -->
  <div class="flex-1 overflow-auto p-6">
    <div class="max-w-4xl mx-auto">
      <!-- Drag and Drop Zone -->
      <div
        class="border-2 border-dashed rounded-lg p-12 text-center transition-colors {isDragging
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 bg-white'} {!selectedLocationId
          ? 'opacity-50 cursor-not-allowed'
          : 'cursor-pointer'}"
        on:dragover={handleDragOver}
        on:dragleave={handleDragLeave}
        on:drop={handleDrop}
        on:click={() => selectedLocationId && fileInputElement.click()}
        on:keypress={handleKeyPress}
        role="button"
        tabindex="0"
      >
        <svg
          class="mx-auto h-16 w-16 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <p class="mt-4 text-lg text-gray-600">
          {#if selectedLocationId}
            Drag and drop files here, or click to select
          {:else}
            Select a location first
          {/if}
        </p>
        <p class="mt-2 text-sm text-gray-500">
          Supported: Images (JPG, PNG, HEIC), Videos (MP4, MOV), Documents (PDF)
        </p>
      </div>

      <!-- Hidden file input -->
      <input
        type="file"
        multiple
        bind:this={fileInputElement}
        on:change={handleFileSelect}
        class="hidden"
        accept=".jpg,.jpeg,.png,.heic,.heif,.dng,.cr2,.nef,.arw,.mp4,.mov,.avi,.mkv,.mts,.m2ts,.pdf,.txt,.doc,.docx"
      />

      <!-- Upload Queue -->
      {#if uploadQueue.length > 0}
        <div class="mt-8">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-800">
              Upload Queue ({uploadQueue.length})
            </h3>
            <button
              on:click={clearCompleted}
              class="text-sm text-blue-600 hover:text-blue-800"
              disabled={!uploadQueue.some(item => item.status === 'success')}
            >
              Clear Completed
            </button>
          </div>

          <div class="space-y-3">
            {#each uploadQueue as item (item.id)}
              <div class="bg-white border border-gray-200 rounded-lg p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-800 truncate">
                      {item.file.name}
                    </p>
                    <p class="text-xs text-gray-500">
                      {formatFileSize(item.file.size)} - {item.category}
                    </p>
                  </div>

                  <div class="ml-4 flex items-center gap-2">
                    {#if item.status === 'success'}
                      <span class="text-green-600 text-sm font-medium">Complete</span>
                    {:else if item.status === 'error'}
                      <button
                        on:click={() => retryUpload(item)}
                        class="text-sm text-blue-600 hover:text-blue-800"
                      >
                        Retry
                      </button>
                    {:else if item.status === 'uploading'}
                      <span class="text-blue-600 text-sm font-medium">
                        {item.progress}%
                      </span>
                    {/if}

                    <button
                      on:click={() => removeItem(item.id)}
                      class="text-gray-400 hover:text-red-600"
                      disabled={item.status === 'uploading'}
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

                <!-- Progress Bar -->
                {#if item.status === 'uploading'}
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div
                      class="h-2 rounded-full transition-all duration-300"
                      style="width: {item.progress}%; background-color: var(--au-accent-brown, #b9975c);"
                    />
                  </div>
                {/if}

                <!-- Error Message -->
                {#if item.status === 'error'}
                  <p class="text-sm text-red-600 mt-2">{item.error}</p>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Location Creation Modal -->
<LocationForm
  bind:isOpen={showLocationForm}
  mode="create"
  prefillGPS={prefillGPS}
  on:created={handleLocationCreated}
  on:close={handleLocationFormClose}
/>
