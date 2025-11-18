<script>
  /**
   * Map Import Dialog Component
   *
   * Allows users to import maps with two modes:
   * - Full Import: Import all locations into the database
   * - Reference Mode: Store map for fuzzy matching suggestions
   *
   * Supports CSV and GeoJSON formats with preview and duplicate detection.
   */

  import { createEventDispatcher, onMount } from 'svelte';
  import { settings } from '../stores/settings.js';

  export let isOpen = false;

  const dispatch = createEventDispatcher();

  // Load API URL from settings
  let apiUrl = 'http://localhost:5002'; // Fallback

  onMount(async () => {
    await settings.load();
  });

  settings.subscribe(s => {
    apiUrl = s.apiUrl;
  });

  // State
  let currentStep = 1; // 1: Upload, 2: Preview, 3: Import
  let fileInput;
  let selectedFile = null;
  let fileName = '';
  let fileFormat = '';

  let importMode = 'full'; // 'full' or 'reference'
  let skipDuplicates = true;
  let description = '';

  // Parsed data
  let locations = [];
  let parseErrors = [];
  let statistics = null;

  // Duplicate analysis
  let duplicateResults = [];
  let showDuplicates = false;

  // Import results
  let importResults = null;
  let isProcessing = false;
  let error = null;

  function close() {
    isOpen = false;
    resetState();
    dispatch('close');
  }

  function resetState() {
    currentStep = 1;
    selectedFile = null;
    fileName = '';
    fileFormat = '';
    importMode = 'full';
    skipDuplicates = true;
    description = '';
    locations = [];
    parseErrors = [];
    statistics = null;
    duplicateResults = [];
    showDuplicates = false;
    importResults = null;
    isProcessing = false;
    error = null;
  }

  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    selectedFile = file;
    fileName = file.name;

    // Auto-detect format
    if (fileName.endsWith('.csv')) {
      fileFormat = 'csv';
    } else if (fileName.endsWith('.json') || fileName.endsWith('.geojson')) {
      fileFormat = 'geojson';
    } else if (fileName.endsWith('.kml')) {
      fileFormat = 'kml';
    } else if (fileName.endsWith('.kmz')) {
      fileFormat = 'kmz';
    } else {
      error = 'Unsupported file format. Please use .csv, .geojson, .kml, or .kmz files.';
      selectedFile = null;
      return;
    }

    error = null;
  }

  async function parseFile() {
    if (!selectedFile) return;

    isProcessing = true;
    error = null;

    try {
      // Read file content (handle binary KMZ differently)
      let content;
      let isBase64 = false;

      if (fileFormat === 'kmz') {
        // KMZ is a binary ZIP file - read as ArrayBuffer and encode to base64
        const arrayBuffer = await selectedFile.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);
        content = btoa(String.fromCharCode(...bytes));
        isBase64 = true;
      } else {
        // KML, CSV, GeoJSON are text files
        content = await selectedFile.text();
      }

      // Send to backend for parsing
      const response = await fetch(`${apiUrl}/api/maps/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: fileName,
          format: fileFormat,
          content: content,
          isBase64: isBase64
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to parse file');
      }

      const data = await response.json();

      locations = data.locations;
      parseErrors = data.errors;
      statistics = data.statistics;

      // Move to preview step
      currentStep = 2;

    } catch (err) {
      console.error('Parse error:', err);
      error = err.message;
    } finally {
      isProcessing = false;
    }
  }

  async function checkDuplicates() {
    if (locations.length === 0) return;

    isProcessing = true;
    error = null;

    try {
      const response = await fetch(`${apiUrl}/api/maps/check-duplicates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ locations })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to check duplicates');
      }

      const data = await response.json();
      duplicateResults = data.results.filter(r => r.has_duplicates);
      showDuplicates = true;

    } catch (err) {
      console.error('Duplicate check error:', err);
      error = err.message;
    } finally {
      isProcessing = false;
    }
  }

  async function performImport() {
    if (locations.length === 0) return;

    isProcessing = true;
    error = null;

    try {
      // Read file content again (handle binary KMZ differently)
      let content;
      let isBase64 = false;

      if (fileFormat === 'kmz') {
        // KMZ is a binary ZIP file - read as ArrayBuffer and encode to base64
        const arrayBuffer = await selectedFile.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);
        content = btoa(String.fromCharCode(...bytes));
        isBase64 = true;
      } else {
        // KML, CSV, GeoJSON are text files
        content = await selectedFile.text();
      }

      const response = await fetch(`${apiUrl}/api/maps/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: fileName,
          format: fileFormat,
          mode: importMode,
          content: content,
          isBase64: isBase64,
          description: description,
          skip_duplicates: skipDuplicates
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Import failed');
      }

      const data = await response.json();
      importResults = data;

      // Move to results step
      currentStep = 3;

      // Notify parent that locations were imported
      dispatch('imported', {
        mode: importMode,
        count: data.statistics.imported
      });

    } catch (err) {
      console.error('Import error:', err);
      error = err.message;
    } finally {
      isProcessing = false;
    }
  }

  function goToStep(step) {
    currentStep = step;
  }
</script>

{#if isOpen}
  <div class="modal-overlay" on:click={close}>
    <div class="modal" on:click|stopPropagation>
      <div class="modal-header">
        <h2>Import Map</h2>
        <button class="close-btn" on:click={close}>&times;</button>
      </div>

      <div class="modal-body">
        <!-- Step Indicator -->
        <div class="steps">
          <div class="step" class:active={currentStep === 1} class:completed={currentStep > 1}>
            <span class="step-number">1</span>
            <span class="step-label">Upload</span>
          </div>
          <div class="step" class:active={currentStep === 2} class:completed={currentStep > 2}>
            <span class="step-number">2</span>
            <span class="step-label">Preview</span>
          </div>
          <div class="step" class:active={currentStep === 3}>
            <span class="step-number">3</span>
            <span class="step-label">Results</span>
          </div>
        </div>

        {#if error}
          <div class="error-message">{error}</div>
        {/if}

        <!-- Step 1: File Upload -->
        {#if currentStep === 1}
          <div class="step-content">
            <div class="upload-section">
              <input
                type="file"
                accept=".csv,.json,.geojson,.kml,.kmz"
                on:change={handleFileSelect}
                bind:this={fileInput}
                style="display: none;"
              />

              {#if selectedFile}
                <div class="file-selected">
                  <p><strong>File:</strong> {fileName}</p>
                  <p><strong>Format:</strong> {fileFormat.toUpperCase()}</p>
                  <button class="btn-secondary" on:click={() => fileInput.click()}>
                    Choose Different File
                  </button>
                </div>
              {:else}
                <div class="file-upload-area" on:click={() => fileInput.click()}>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                  </svg>
                  <p>Click to select a map file</p>
                  <p class="hint">Supports CSV, GeoJSON, KML, and KMZ formats</p>
                </div>
              {/if}
            </div>

            <div class="import-options">
              <h3>Import Mode</h3>

              <label class="radio-option">
                <input type="radio" bind:group={importMode} value="full" />
                <div>
                  <strong>Full Import</strong>
                  <p>Import all locations into your database. GPS coordinates and metadata will be saved permanently.</p>
                </div>
              </label>

              <label class="radio-option">
                <input type="radio" bind:group={importMode} value="reference" />
                <div>
                  <strong>Reference Mode</strong>
                  <p>Keep map as reference only. When you add locations, we'll suggest matches from this map.</p>
                </div>
              </label>

              <label class="checkbox-option">
                <input type="checkbox" bind:checked={skipDuplicates} />
                <span>Skip duplicate locations</span>
              </label>

              <div class="form-group">
                <label for="description">Description (Optional)</label>
                <input
                  id="description"
                  type="text"
                  bind:value={description}
                  placeholder="e.g., Northeast Abandoned Mills"
                />
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" on:click={close}>Cancel</button>
            <button
              class="btn-primary"
              on:click={parseFile}
              disabled={!selectedFile || isProcessing}
            >
              {isProcessing ? 'Parsing...' : 'Next'}
            </button>
          </div>
        {/if}

        <!-- Step 2: Preview -->
        {#if currentStep === 2}
          <div class="step-content">
            {#if statistics}
              <div class="statistics">
                <h3>Import Preview</h3>
                <div class="stat-grid">
                  <div class="stat">
                    <span class="stat-value">{statistics.valid_locations}</span>
                    <span class="stat-label">Valid Locations</span>
                  </div>
                  <div class="stat">
                    <span class="stat-value">{statistics.with_gps}</span>
                    <span class="stat-label">With GPS</span>
                  </div>
                  <div class="stat">
                    <span class="stat-value">{statistics.with_state}</span>
                    <span class="stat-label">With State</span>
                  </div>
                  <div class="stat">
                    <span class="stat-value">{statistics.invalid_rows}</span>
                    <span class="stat-label">Errors</span>
                  </div>
                </div>
              </div>
            {/if}

            {#if parseErrors.length > 0}
              <details class="errors-section">
                <summary>Parsing Errors ({parseErrors.length})</summary>
                <ul>
                  {#each parseErrors as err}
                    <li>{err}</li>
                  {/each}
                </ul>
              </details>
            {/if}

            <div class="locations-preview">
              <h4>Sample Locations (first 5)</h4>
              <div class="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>State</th>
                      <th>Type</th>
                      <th>GPS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each locations.slice(0, 5) as loc}
                      <tr>
                        <td>{loc.name}</td>
                        <td>{loc.state || '-'}</td>
                        <td>{loc.type || '-'}</td>
                        <td>
                          {#if loc.lat && loc.lon}
                            {loc.lat.toFixed(4)}, {loc.lon.toFixed(4)}
                          {:else}
                            -
                          {/if}
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>

            {#if !showDuplicates}
              <button class="btn-secondary" on:click={checkDuplicates} disabled={isProcessing}>
                {isProcessing ? 'Checking...' : 'Check for Duplicates'}
              </button>
            {/if}

            {#if showDuplicates && duplicateResults.length > 0}
              <div class="duplicates-warning">
                <h4>⚠️ Found {duplicateResults.length} potential duplicates</h4>
                <p>These locations may already exist in your database:</p>
                <ul>
                  {#each duplicateResults.slice(0, 5) as dup}
                    <li>
                      <strong>{dup.name}</strong> ({dup.state}) -
                      {dup.duplicates.length} match{dup.duplicates.length > 1 ? 'es' : ''}
                    </li>
                  {/each}
                </ul>
                {#if duplicateResults.length > 5}
                  <p class="more-info">...and {duplicateResults.length - 5} more</p>
                {/if}
                <p class="hint">
                  {#if skipDuplicates}
                    Duplicates will be skipped during import.
                  {:else}
                    Duplicates will be imported as separate entries.
                  {/if}
                </p>
              </div>
            {/if}
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" on:click={() => goToStep(1)}>Back</button>
            <button
              class="btn-primary"
              on:click={performImport}
              disabled={locations.length === 0 || isProcessing}
            >
              {isProcessing ? 'Importing...' : `Import ${statistics?.valid_locations || 0} Locations`}
            </button>
          </div>
        {/if}

        <!-- Step 3: Results -->
        {#if currentStep === 3 && importResults}
          <div class="step-content">
            <div class="success-message">
              <h3>✓ Import Complete</h3>

              <div class="results-grid">
                <div class="result-stat success">
                  <span class="value">{importResults.statistics.imported}</span>
                  <span class="label">Imported</span>
                </div>
                <div class="result-stat skipped">
                  <span class="value">{importResults.statistics.skipped}</span>
                  <span class="label">Skipped</span>
                </div>
                <div class="result-stat">
                  <span class="value">{importResults.statistics.duplicates}</span>
                  <span class="label">Duplicates</span>
                </div>
              </div>

              <div class="import-info">
                <p><strong>Mode:</strong> {importMode === 'full' ? 'Full Import' : 'Reference Mode'}</p>
                <p><strong>Map ID:</strong> {importResults.map_id}</p>
                {#if importMode === 'reference'}
                  <p class="hint">This map is now available for location suggestions when you create new locations.</p>
                {:else}
                  <p class="hint">Locations have been added to your database and will appear on the map.</p>
                {/if}
              </div>

              {#if importResults.statistics.errors && importResults.statistics.errors.length > 0}
                <details class="errors-section">
                  <summary>Import Errors ({importResults.statistics.errors.length})</summary>
                  <ul>
                    {#each importResults.statistics.errors as err}
                      <li>{err}</li>
                    {/each}
                  </ul>
                </details>
              {/if}
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-primary" on:click={close}>Done</button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: white;
    border-radius: 8px;
    width: 90%;
    max-width: 700px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }

  .modal-header {
    padding: 20px 24px;
    border-bottom: 1px solid #e0e0e0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .modal-header h2 {
    margin: 0;
    font-size: 1.5rem;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 2rem;
    cursor: pointer;
    color: #666;
    line-height: 1;
    padding: 0;
    width: 32px;
    height: 32px;
  }

  .close-btn:hover {
    color: #333;
  }

  .modal-body {
    padding: 24px;
    overflow-y: auto;
    flex: 1;
  }

  .steps {
    display: flex;
    justify-content: space-between;
    margin-bottom: 32px;
    position: relative;
  }

  .steps::before {
    content: '';
    position: absolute;
    top: 16px;
    left: 32px;
    right: 32px;
    height: 2px;
    background: #e0e0e0;
    z-index: 0;
  }

  .step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    position: relative;
    z-index: 1;
  }

  .step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #e0e0e0;
    color: #666;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
  }

  .step.active .step-number {
    background: #007bff;
    color: white;
  }

  .step.completed .step-number {
    background: #28a745;
    color: white;
  }

  .step-label {
    font-size: 0.875rem;
    color: #666;
  }

  .step.active .step-label {
    color: #007bff;
    font-weight: bold;
  }

  .error-message {
    background: #f8d7da;
    color: #721c24;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 16px;
  }

  .file-upload-area {
    border: 2px dashed #ccc;
    border-radius: 8px;
    padding: 48px 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
  }

  .file-upload-area:hover {
    border-color: #007bff;
    background: #f8f9fa;
  }

  .file-upload-area svg {
    color: #666;
    margin-bottom: 16px;
  }

  .file-upload-area p {
    margin: 8px 0;
    color: #333;
  }

  .file-upload-area .hint {
    font-size: 0.875rem;
    color: #666;
  }

  .file-selected {
    background: #f8f9fa;
    padding: 24px;
    border-radius: 8px;
    text-align: center;
  }

  .file-selected p {
    margin: 8px 0;
  }

  .file-selected button {
    margin-top: 16px;
  }

  .import-options {
    margin-top: 24px;
  }

  .import-options h3 {
    margin-bottom: 16px;
  }

  .radio-option, .checkbox-option {
    display: flex;
    gap: 12px;
    padding: 12px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    margin-bottom: 12px;
    cursor: pointer;
  }

  .radio-option:hover {
    background: #f8f9fa;
  }

  .radio-option input[type="radio"] {
    margin-top: 4px;
  }

  .radio-option p {
    margin: 4px 0 0 0;
    font-size: 0.875rem;
    color: #666;
  }

  .checkbox-option {
    align-items: center;
  }

  .form-group {
    margin-top: 16px;
  }

  .form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
  }

  .form-group input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
  }

  .statistics {
    margin-bottom: 24px;
  }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-top: 16px;
  }

  .stat {
    text-align: center;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
  }

  .stat-value {
    display: block;
    font-size: 2rem;
    font-weight: bold;
    color: #007bff;
  }

  .stat-label {
    display: block;
    font-size: 0.875rem;
    color: #666;
    margin-top: 8px;
  }

  .errors-section {
    background: #fff3cd;
    padding: 12px;
    border-radius: 4px;
    margin: 16px 0;
  }

  .errors-section summary {
    cursor: pointer;
    font-weight: bold;
    color: #856404;
  }

  .errors-section ul {
    margin: 12px 0 0 20px;
    color: #856404;
  }

  .locations-preview {
    margin: 24px 0;
  }

  .table-container {
    overflow-x: auto;
    margin-top: 12px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  th, td {
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid #e0e0e0;
  }

  th {
    background: #f8f9fa;
    font-weight: bold;
  }

  .duplicates-warning {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 16px;
    border-radius: 4px;
    margin-top: 16px;
  }

  .duplicates-warning h4 {
    margin-top: 0;
    color: #856404;
  }

  .duplicates-warning ul {
    margin: 12px 0;
  }

  .duplicates-warning .hint {
    font-size: 0.875rem;
    color: #856404;
    font-style: italic;
  }

  .duplicates-warning .more-info {
    font-style: italic;
    color: #856404;
  }

  .success-message {
    text-align: center;
  }

  .success-message h3 {
    color: #28a745;
    font-size: 1.5rem;
  }

  .results-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin: 24px 0;
  }

  .result-stat {
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    text-align: center;
  }

  .result-stat.success {
    background: #d4edda;
  }

  .result-stat.skipped {
    background: #fff3cd;
  }

  .result-stat .value {
    display: block;
    font-size: 2.5rem;
    font-weight: bold;
  }

  .result-stat.success .value {
    color: #28a745;
  }

  .result-stat.skipped .value {
    color: #856404;
  }

  .result-stat .label {
    display: block;
    font-size: 0.875rem;
    color: #666;
    margin-top: 8px;
  }

  .import-info {
    text-align: left;
    background: #f8f9fa;
    padding: 16px;
    border-radius: 4px;
    margin: 16px 0;
  }

  .import-info p {
    margin: 8px 0;
  }

  .import-info .hint {
    font-size: 0.875rem;
    color: #666;
    font-style: italic;
  }

  .modal-footer {
    padding: 16px 24px;
    border-top: 1px solid #e0e0e0;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }

  .btn-primary, .btn-secondary {
    padding: 10px 20px;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    border: none;
    font-weight: 500;
    transition: all 0.2s;
  }

  .btn-primary {
    background: #007bff;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #0056b3;
  }

  .btn-primary:disabled {
    background: #ccc;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: #6c757d;
    color: white;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #545b62;
  }

  .btn-secondary:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
</style>
