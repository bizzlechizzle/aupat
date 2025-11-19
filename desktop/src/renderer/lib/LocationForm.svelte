<script>
  /**
   * Location Create/Edit Form Component
   *
   * Modal dialog for creating new locations or editing existing ones.
   * Supports manual GPS entry and form validation.
   */

  import { createEventDispatcher, onMount } from 'svelte';
  import { locations } from '../stores/locations.js';

  export let isOpen = false;
  export let mode = 'create'; // 'create' or 'edit'
  export let location = null; // For edit mode
  export let prefillGPS = null; // Optional { lat, lng } to pre-fill GPS coordinates

  const dispatch = createEventDispatcher();

  let nameInput; // Reference to the name input for autofocus

  // Form state
  let formData = {
    loc_name: '',
    loc_short: '',
    aka_name: '',
    state: 'ny',
    type: 'industrial',
    sub_type: '',
    status: '',
    explored: '',
    street_address: '',
    city: '',
    zip_code: '',
    county: '',
    region: '',
    lat: null,
    lon: null,
    gps_source: 'manual',
    imp_author: '',
    historical: false
  };

  let errors = {};
  let isSubmitting = false;
  let lastLoadedLocationId = null; // Track which location we've loaded to prevent re-initialization

  // Autocomplete data
  let typeOptions = [];
  let subTypeOptions = [];
  let stateOptions = [];
  let authorOptions = [];
  let cityOptions = [];

  // US States - comprehensive list for autocomplete
  const states = [
    { code: 'al', name: 'Alabama' },
    { code: 'ak', name: 'Alaska' },
    { code: 'az', name: 'Arizona' },
    { code: 'ar', name: 'Arkansas' },
    { code: 'ca', name: 'California' },
    { code: 'co', name: 'Colorado' },
    { code: 'ct', name: 'Connecticut' },
    { code: 'de', name: 'Delaware' },
    { code: 'fl', name: 'Florida' },
    { code: 'ga', name: 'Georgia' },
    { code: 'hi', name: 'Hawaii' },
    { code: 'id', name: 'Idaho' },
    { code: 'il', name: 'Illinois' },
    { code: 'in', name: 'Indiana' },
    { code: 'ia', name: 'Iowa' },
    { code: 'ks', name: 'Kansas' },
    { code: 'ky', name: 'Kentucky' },
    { code: 'la', name: 'Louisiana' },
    { code: 'me', name: 'Maine' },
    { code: 'md', name: 'Maryland' },
    { code: 'ma', name: 'Massachusetts' },
    { code: 'mi', name: 'Michigan' },
    { code: 'mn', name: 'Minnesota' },
    { code: 'ms', name: 'Mississippi' },
    { code: 'mo', name: 'Missouri' },
    { code: 'mt', name: 'Montana' },
    { code: 'ne', name: 'Nebraska' },
    { code: 'nv', name: 'Nevada' },
    { code: 'nh', name: 'New Hampshire' },
    { code: 'nj', name: 'New Jersey' },
    { code: 'nm', name: 'New Mexico' },
    { code: 'ny', name: 'New York' },
    { code: 'nc', name: 'North Carolina' },
    { code: 'nd', name: 'North Dakota' },
    { code: 'oh', name: 'Ohio' },
    { code: 'ok', name: 'Oklahoma' },
    { code: 'or', name: 'Oregon' },
    { code: 'pa', name: 'Pennsylvania' },
    { code: 'ri', name: 'Rhode Island' },
    { code: 'sc', name: 'South Carolina' },
    { code: 'sd', name: 'South Dakota' },
    { code: 'tn', name: 'Tennessee' },
    { code: 'tx', name: 'Texas' },
    { code: 'ut', name: 'Utah' },
    { code: 'vt', name: 'Vermont' },
    { code: 'va', name: 'Virginia' },
    { code: 'wa', name: 'Washington' },
    { code: 'wv', name: 'West Virginia' },
    { code: 'wi', name: 'Wisconsin' },
    { code: 'wy', name: 'Wyoming' },
    { code: 'dc', name: 'District of Columbia' },
    { code: 'pr', name: 'Puerto Rico' },
    { code: 'vi', name: 'US Virgin Islands' },
    { code: 'gu', name: 'Guam' },
    { code: 'as', name: 'American Samoa' },
    { code: 'mp', name: 'Northern Mariana Islands' }
  ];

  // Location types
  const types = [
    'industrial',
    'residential',
    'commercial',
    'institutional',
    'religious',
    'recreational',
    'transportation',
    'agricultural',
    'military',
    'other'
  ];

  // Load data for edit mode - only when location ID changes to prevent overwriting user input
  $: if (mode === 'edit' && location && location.loc_uuid !== lastLoadedLocationId) {
    lastLoadedLocationId = location.loc_uuid;
    formData = {
      loc_name: location.loc_name || '',
      loc_short: location.loc_short || '',
      aka_name: location.aka_name || '',
      state: location.state || 'ny',
      type: location.type || 'industrial',
      sub_type: location.sub_type || '',
      status: location.status || '',
      explored: location.explored || '',
      street_address: location.street_address || '',
      city: location.city || '',
      zip_code: location.zip_code || '',
      county: location.county || '',
      region: location.region || '',
      lat: location.lat,
      lon: location.lon,
      gps_source: location.gps_source || 'manual',
      imp_author: location.imp_author || '',
      historical: location.historical || false
    };
  }

  // Pre-fill GPS coordinates when provided (for create mode)
  $: if (mode === 'create' && prefillGPS && prefillGPS.lat && prefillGPS.lng) {
    formData.lat = prefillGPS.lat;
    formData.lon = prefillGPS.lng;
    formData.gps_source = 'manual';
  }

  // Load autocomplete options when form opens and focus first input
  $: if (isOpen) {
    loadAutocompleteOptions();
    // Focus the name input after a short delay to ensure DOM is ready
    setTimeout(() => {
      if (nameInput) {
        nameInput.focus();
      }
    }, 100);
  }

  // Update sub_type options when type changes
  $: if (formData.type) {
    loadSubTypeOptions(formData.type);
  }

  async function loadAutocompleteOptions() {
    try {
      // Load all autocomplete options in parallel
      const [typeRes, stateRes, authorRes, cityRes] = await Promise.all([
        window.api.locations.autocomplete('type', { limit: 50 }),
        window.api.locations.autocomplete('state', { limit: 50 }),
        window.api.locations.autocomplete('imp_author', { limit: 50 }),
        window.api.locations.autocomplete('city', { limit: 50 })
      ]);

      if (typeRes.success) typeOptions = typeRes.data;
      if (stateRes.success) stateOptions = stateRes.data;
      if (authorRes.success) authorOptions = authorRes.data;
      if (cityRes.success) cityOptions = cityRes.data;

      // Set defaults to most popular if creating new location
      if (mode === 'create') {
        if (typeOptions.length > 0 && !formData.type) {
          formData.type = typeOptions[0].value;
        }
        if (stateOptions.length > 0 && !formData.state) {
          formData.state = stateOptions[0].value;
        }
        if (authorOptions.length > 0 && !formData.imp_author) {
          formData.imp_author = authorOptions[0].value;
        }
      }
    } catch (error) {
      console.error('Failed to load autocomplete options:', error);
    }
  }

  async function loadSubTypeOptions(type) {
    try {
      const res = await window.api.locations.autocomplete('sub_type', { type, limit: 50 });
      if (res.success) {
        subTypeOptions = res.data;
      }
    } catch (error) {
      console.error('Failed to load sub_type options:', error);
    }
  }

  function validateForm() {
    errors = {};

    if (!formData.loc_name || formData.loc_name.trim() === '') {
      errors.loc_name = 'Location name is required';
    }

    if (!formData.state) {
      errors.state = 'State is required';
    }

    if (!formData.type) {
      errors.type = 'Location type is required';
    }

    if (formData.lat !== null && formData.lat !== '') {
      const lat = parseFloat(formData.lat);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        errors.lat = 'Latitude must be between -90 and 90';
      }
    }

    if (formData.lon !== null && formData.lon !== '') {
      const lon = parseFloat(formData.lon);
      if (isNaN(lon) || lon < -180 || lon > 180) {
        errors.lon = 'Longitude must be between -180 and 180';
      }
    }

    return Object.keys(errors).length === 0;
  }

  async function handleSubmit() {
    if (!validateForm()) {
      return;
    }

    // Additional validation for edit mode
    if (mode === 'edit') {
      if (!location) {
        errors.submit = 'No location selected for editing';
        return;
      }
      if (!location.loc_uuid) {
        errors.submit = 'Location UUID is missing';
        return;
      }
    }

    isSubmitting = true;

    try {
      // Prepare data for API
      const data = {
        loc_name: formData.loc_name.trim(),
        loc_short: formData.loc_short.trim() || null,
        aka_name: formData.aka_name.trim() || null,
        state: formData.state,
        type: formData.type,
        sub_type: formData.sub_type.trim() || null,
        status: formData.status || null,
        explored: formData.explored || null,
        street_address: formData.street_address.trim() || null,
        city: formData.city.trim() || null,
        zip_code: formData.zip_code.trim() || null,
        county: formData.county.trim() || null,
        region: formData.region.trim() || null,
        lat: formData.lat !== null && formData.lat !== '' ? parseFloat(formData.lat) : null,
        lon: formData.lon !== null && formData.lon !== '' ? parseFloat(formData.lon) : null,
        gps_source: formData.gps_source,
        imp_author: formData.imp_author.trim() || null,
        historical: formData.historical || false
      };

      if (mode === 'create') {
        console.log('Creating new location:', data);
        const newLocation = await locations.create(data);
        console.log('Location created successfully:', newLocation);
        dispatch('created', newLocation);
      } else {
        console.log('Updating location:', location.loc_uuid, data);
        const updatedLocation = await locations.update(location.loc_uuid, data);
        console.log('Location updated successfully:', updatedLocation);
        dispatch('updated', updatedLocation);
      }

      close();
    } catch (error) {
      console.error('Failed to save location:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        mode,
        locationId: location?.loc_uuid
      });

      // Check for collision error
      if (error.message && error.message.includes('already exists')) {
        errors.loc_name = 'A location with this name already exists';
        errors.submit = 'Name collision detected. Please use a different name.';
      } else {
        errors.submit = error.message || 'Failed to save location';
      }
    } finally {
      isSubmitting = false;
    }
  }

  function close() {
    isOpen = false;
    dispatch('close');
    resetForm();
  }

  function resetForm() {
    formData = {
      loc_name: '',
      loc_short: '',
      aka_name: '',
      state: 'ny',
      type: 'industrial',
      sub_type: '',
      status: '',
      explored: '',
      street_address: '',
      city: '',
      zip_code: '',
      county: '',
      region: '',
      lat: null,
      lon: null,
      gps_source: 'manual',
      imp_author: '',
      historical: false
    };
    errors = {};
    lastLoadedLocationId = null; // Reset so next edit loads fresh data
  }

  function handleOverlayKeydown(event) {
    // Only handle Escape key, and only when not focused on an input
    if (event.key === 'Escape' && isOpen) {
      // Don't close if user is typing in an input field
      const target = event.target;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA')) {
        // Let input handle Escape (e.g., clearing autocomplete)
        return;
      }
      close();
    }
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
  <div
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    on:click={close}
    on:keydown={handleOverlayKeydown}
    role="dialog"
    aria-modal="true"
  >
    <div
      class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      on:click|stopPropagation
      on:keydown|stopPropagation
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h2 class="text-2xl font-bold text-gray-800">
          {mode === 'create' ? 'Add New Location' : 'Edit Location'}
        </h2>
        <button
          on:click={close}
          class="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Form -->
      <form on:submit|preventDefault={handleSubmit} class="p-6 space-y-6">
        <!-- Basic Information -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-700">Basic Information</h3>

          <!-- Location Name -->
          <div>
            <label for="loc_name" class="block text-sm font-medium text-gray-700 mb-1">
              Location Name <span class="text-red-500">*</span>
            </label>
            <input
              bind:this={nameInput}
              id="loc_name"
              type="text"
              bind:value={formData.loc_name}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent {errors.loc_name ? 'border-red-500' : ''}"
              placeholder="e.g., Abandoned Factory"
              required
            />
            {#if errors.loc_name}
              <p class="mt-1 text-sm text-red-600">{errors.loc_name}</p>
            {/if}
          </div>

          <!-- Short Name -->
          <div>
            <label for="loc_short" class="block text-sm font-medium text-gray-700 mb-1">
              Short Name
            </label>
            <input
              id="loc_short"
              type="text"
              bind:value={formData.loc_short}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., oldmill"
              maxlength="12"
            />
            <p class="mt-1 text-xs text-gray-500">
              Optional short identifier (max 12 chars). Auto-generated if empty.
            </p>
          </div>

          <!-- AKA Name -->
          <div>
            <label for="aka_name" class="block text-sm font-medium text-gray-700 mb-1">
              Also Known As
            </label>
            <input
              id="aka_name"
              type="text"
              bind:value={formData.aka_name}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Alternative name"
            />
          </div>

          <!-- State and Type -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="state" class="block text-sm font-medium text-gray-700 mb-1">
                State <span class="text-red-500">*</span>
              </label>
              <input
                id="state"
                type="text"
                bind:value={formData.state}
                list="state_datalist"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent {errors.state ? 'border-red-500' : ''}"
                placeholder="e.g., ny, ca, tx"
                maxlength="2"
                required
              />
              <datalist id="state_datalist">
                {#each states as state}
                  <option value={state.code}>{state.name}</option>
                {/each}
                {#each stateOptions as option}
                  <option value={option.value}>{option.value} ({option.count})</option>
                {/each}
              </datalist>
              <p class="mt-1 text-xs text-gray-500">
                Enter 2-letter state code (e.g., ny, ca, tx) or type to search
              </p>
              {#if errors.state}
                <p class="mt-1 text-sm text-red-600">{errors.state}</p>
              {/if}
            </div>

            <div>
              <label for="type" class="block text-sm font-medium text-gray-700 mb-1">
                Type <span class="text-red-500">*</span>
              </label>
              <input
                id="type"
                type="text"
                bind:value={formData.type}
                list="type_datalist"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent {errors.type ? 'border-red-500' : ''}"
                placeholder="e.g., industrial, residential"
                required
              />
              <datalist id="type_datalist">
                {#each types as type}
                  <option value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                {/each}
                {#each typeOptions as option}
                  <option value={option.value}>{option.value} ({option.count})</option>
                {/each}
              </datalist>
              <p class="mt-1 text-xs text-gray-500">
                Enter location type or select from suggestions
              </p>
              {#if errors.type}
                <p class="mt-1 text-sm text-red-600">{errors.type}</p>
              {/if}
            </div>
          </div>

          <!-- Sub Type -->
          <div>
            <label for="sub_type" class="block text-sm font-medium text-gray-700 mb-1">
              Sub Type
            </label>
            <input
              id="sub_type"
              type="text"
              bind:value={formData.sub_type}
              list="sub_type_options"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., textile mill, warehouse"
            />
            <datalist id="sub_type_options">
              {#each subTypeOptions as option}
                <option value={option.value}>{option.value} ({option.count})</option>
              {/each}
            </datalist>
          </div>

          <!-- Status and Explored -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="status" class="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status"
                bind:value={formData.status}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">-- Select Status --</option>
                <option value="Abandoned">Abandoned</option>
                <option value="Demolished">Demolished</option>
                <option value="Rehabbed">Rehabbed</option>
                <option value="Future Classic">Future Classic</option>
                <option value="Unknown">Unknown</option>
                <option value="Recently Sold">Recently Sold</option>
              </select>
            </div>

            <div>
              <label for="explored" class="block text-sm font-medium text-gray-700 mb-1">
                Explored
              </label>
              <select
                id="explored"
                bind:value={formData.explored}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">-- Select Explored --</option>
                <option value="Interior">Interior</option>
                <option value="Exterior">Exterior</option>
                <option value="Un-Documented">Un-Documented</option>
                <option value="N/A">N/A</option>
              </select>
            </div>
          </div>

          <!-- Historical Checkbox -->
          <div class="flex items-center">
            <input
              id="historical"
              type="checkbox"
              bind:checked={formData.historical}
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label for="historical" class="ml-2 block text-sm text-gray-700">
              Mark as Historical Location
            </label>
          </div>

          <!-- Author -->
          <div>
            <label for="imp_author" class="block text-sm font-medium text-gray-700 mb-1">
              Author
            </label>
            <input
              id="imp_author"
              type="text"
              bind:value={formData.imp_author}
              list="author_options"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Your name or username"
            />
            <datalist id="author_options">
              {#each authorOptions as option}
                <option value={option.value}>{option.value} ({option.count})</option>
              {/each}
            </datalist>
          </div>
        </div>

        <!-- Address Information -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-700">Address</h3>

          <div>
            <label for="street_address" class="block text-sm font-medium text-gray-700 mb-1">
              Street Address
            </label>
            <input
              id="street_address"
              type="text"
              bind:value={formData.street_address}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="123 Main St"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="city" class="block text-sm font-medium text-gray-700 mb-1">
                City
              </label>
              <input
                id="city"
                type="text"
                bind:value={formData.city}
                list="city_options"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Albany"
              />
              <datalist id="city_options">
                {#each cityOptions as option}
                  <option value={option.value}>{option.value} ({option.count})</option>
                {/each}
              </datalist>
            </div>

            <div>
              <label for="zip_code" class="block text-sm font-medium text-gray-700 mb-1">
                ZIP Code
              </label>
              <input
                id="zip_code"
                type="text"
                bind:value={formData.zip_code}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="12203"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="county" class="block text-sm font-medium text-gray-700 mb-1">
                County
              </label>
              <input
                id="county"
                type="text"
                bind:value={formData.county}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Erie County"
              />
            </div>

            <div>
              <label for="region" class="block text-sm font-medium text-gray-700 mb-1">
                Region
              </label>
              <input
                id="region"
                type="text"
                bind:value={formData.region}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Western NY"
              />
            </div>
          </div>
        </div>

        <!-- GPS Coordinates -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-700">GPS Coordinates</h3>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="lat" class="block text-sm font-medium text-gray-700 mb-1">
                Latitude
              </label>
              <input
                id="lat"
                type="number"
                step="any"
                bind:value={formData.lat}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent {errors.lat ? 'border-red-500' : ''}"
                placeholder="42.6526"
              />
              {#if errors.lat}
                <p class="mt-1 text-sm text-red-600">{errors.lat}</p>
              {/if}
            </div>

            <div>
              <label for="lon" class="block text-sm font-medium text-gray-700 mb-1">
                Longitude
              </label>
              <input
                id="lon"
                type="number"
                step="any"
                bind:value={formData.lon}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent {errors.lon ? 'border-red-500' : ''}"
                placeholder="-73.7562"
              />
              {#if errors.lon}
                <p class="mt-1 text-sm text-red-600">{errors.lon}</p>
              {/if}
            </div>
          </div>

          <p class="text-sm text-gray-500">
            Tip: Click on the map in the Map View to get coordinates, or leave empty to add later.
          </p>
        </div>

        <!-- Error Message -->
        {#if errors.submit}
          <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <p class="text-sm text-red-600">{errors.submit}</p>
          </div>
        {/if}

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            on:click={close}
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300 disabled:cursor-not-allowed"
            disabled={isSubmitting}
          >
            {#if isSubmitting}
              Saving...
            {:else}
              {mode === 'create' ? 'Create Location' : 'Save Changes'}
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
