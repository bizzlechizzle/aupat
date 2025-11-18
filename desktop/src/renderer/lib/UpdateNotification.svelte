<script>
  /**
   * Abandoned Upstate - Auto-Update Notification Component
   *
   * Displays update notifications and controls update flow.
   * Shows banners for:
   * - Update available (with Download button)
   * - Download progress
   * - Update ready (with Restart Now button)
   * - Errors
   */

  import { onMount, onDestroy } from 'svelte';

  // Update state
  let updateAvailable = false;
  let updateVersion = null;
  let updateReleaseNotes = null;
  let updateReleaseDate = null;

  let downloading = false;
  let downloadProgress = 0;
  let downloadSpeed = 0;

  let updateReady = false;
  let updateError = null;

  // State visibility controls
  let showBanner = false;

  // Event handlers
  let handleAvailable, handleDownloaded, handleProgress, handleError;

  onMount(() => {
    // Set up event listeners for update events
    handleAvailable = (data) => {
      updateAvailable = true;
      updateVersion = data.version;
      updateReleaseNotes = data.releaseNotes;
      updateReleaseDate = data.releaseDate;
      showBanner = true;
      console.log('Update available:', data.version);
    };

    handleDownloaded = (data) => {
      downloading = false;
      updateReady = true;
      updateVersion = data.version;
      showBanner = true;
      console.log('Update downloaded:', data.version);
    };

    handleProgress = (data) => {
      downloadProgress = data.percent;
      downloadSpeed = data.bytesPerSecond;
      console.log(`Download progress: ${data.percent}%`);
    };

    handleError = (data) => {
      updateError = data.message;
      downloading = false;
      showBanner = true;
      console.error('Update error:', data.message);
    };

    // Register event listeners
    window.api.updates.onAvailable(handleAvailable);
    window.api.updates.onDownloaded(handleDownloaded);
    window.api.updates.onProgress(handleProgress);
    window.api.updates.onError(handleError);
  });

  onDestroy(() => {
    // Clean up event listeners
    if (handleAvailable) window.api.updates.removeAvailableListener(handleAvailable);
    if (handleDownloaded) window.api.updates.removeDownloadedListener(handleDownloaded);
    if (handleProgress) window.api.updates.removeProgressListener(handleProgress);
    if (handleError) window.api.updates.removeErrorListener(handleError);
  });

  async function downloadUpdate() {
    try {
      updateError = null;
      downloading = true;
      const result = await window.api.updates.download();
      if (!result.success) {
        updateError = result.error || 'Failed to start download';
        downloading = false;
      }
    } catch (error) {
      updateError = error.message || 'Failed to start download';
      downloading = false;
    }
  }

  async function installUpdate() {
    try {
      const result = await window.api.updates.install();
      if (!result.success) {
        updateError = result.error || 'Failed to install update';
      }
      // If successful, app will restart automatically
    } catch (error) {
      updateError = error.message || 'Failed to install update';
    }
  }

  function dismissBanner() {
    showBanner = false;
  }

  function formatBytes(bytes) {
    if (bytes === 0) return '0 B/s';
    const k = 1024;
    const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }
</script>

{#if showBanner}
  <!-- Update Available Banner -->
  {#if updateAvailable && !downloading && !updateReady}
    <div class="update-banner update-available">
      <div class="update-content">
        <div class="update-icon">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 6V10L13 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="update-message">
          <p class="update-title">Update Available: v{updateVersion}</p>
          {#if updateReleaseDate}
            <p class="update-subtitle">Released {new Date(updateReleaseDate).toLocaleDateString()}</p>
          {/if}
        </div>
      </div>
      <div class="update-actions">
        <button on:click={downloadUpdate} class="btn-primary">
          Download Update
        </button>
        <button on:click={dismissBanner} class="btn-secondary">
          Later
        </button>
      </div>
    </div>
  {/if}

  <!-- Download Progress Banner -->
  {#if downloading}
    <div class="update-banner update-downloading">
      <div class="update-content">
        <div class="update-icon">
          <svg class="spinner" width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18C14.4183 18 18 14.4183 18 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="update-message">
          <p class="update-title">Downloading Update v{updateVersion}</p>
          <div class="progress-container">
            <div class="progress-bar">
              <div class="progress-fill" style="width: {downloadProgress}%"></div>
            </div>
            <p class="progress-text">{downloadProgress}% • {formatBytes(downloadSpeed)}</p>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <!-- Update Ready Banner -->
  {#if updateReady && !downloading}
    <div class="update-banner update-ready">
      <div class="update-content">
        <div class="update-icon">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 5L7.5 13.5L4 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="update-message">
          <p class="update-title">Update Ready: v{updateVersion}</p>
          <p class="update-subtitle">Restart to install the update</p>
        </div>
      </div>
      <div class="update-actions">
        <button on:click={installUpdate} class="btn-primary">
          Restart Now
        </button>
        <button on:click={dismissBanner} class="btn-secondary">
          Later
        </button>
      </div>
    </div>
  {/if}

  <!-- Error Banner -->
  {#if updateError}
    <div class="update-banner update-error">
      <div class="update-content">
        <div class="update-icon">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 6V10M10 14H10.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="update-message">
          <p class="update-title">Update Failed</p>
          <p class="update-subtitle">{updateError}</p>
        </div>
      </div>
      <div class="update-actions">
        <button on:click={dismissBanner} class="btn-secondary">
          Dismiss
        </button>
      </div>
    </div>
  {/if}
{/if}

<style>
  .update-banner {
    position: fixed;
    top: 0;
    left: 16rem; /* offset for sidebar (w-64 = 16rem) */
    right: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    animation: slideDown 0.3s ease-out;
  }

  @keyframes slideDown {
    from {
      transform: translateY(-100%);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  .update-available {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .update-downloading {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
  }

  .update-ready {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
  }

  .update-error {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    color: white;
  }

  .update-content {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex: 1;
  }

  .update-icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .update-message {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .update-title {
    font-weight: 600;
    font-size: 0.95rem;
    margin: 0;
  }

  .update-subtitle {
    font-size: 0.85rem;
    opacity: 0.9;
    margin: 0;
  }

  .update-actions {
    display: flex;
    gap: 0.75rem;
  }

  .btn-primary,
  .btn-secondary {
    padding: 0.5rem 1.25rem;
    border-radius: 0.375rem;
    font-weight: 500;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    outline: none;
  }

  .btn-primary {
    background: white;
    color: #1a202c;
  }

  .btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }

  .btn-secondary {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.3);
  }

  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  .progress-container {
    margin-top: 0.5rem;
    width: 300px;
  }

  .progress-bar {
    width: 100%;
    height: 6px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: white;
    border-radius: 3px;
    transition: width 0.3s ease;
  }

  .progress-text {
    font-size: 0.75rem;
    margin-top: 0.25rem;
    opacity: 0.9;
  }
</style>
