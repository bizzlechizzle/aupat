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

  const dispatch = createEventDispatcher();

  // Form state
  let formData = {
    loc_name: '',
    aka_name: '',
    state: 'ny',
    type: 'industrial',
    sub_type: '',
    street_address: '',
    city: '',
    zip_code: '',
    lat: null,
    lon: null,
    gps_source: 'manual'
  };

  let errors = {};
  let isSubmitting = false;

  // US States
  const states = [
    { code: 'ny', name: 'New York' },
    { code: 'pa', name: 'Pennsylvania' },
    { code: 'vt', name: 'Vermont' },
    { code: 'ma', name: 'Massachusetts' },
    { code: 'ct', name: 'Connecticut' },
    { code: 'nj', name: 'New Jersey' },
    { code: 'me', name: 'Maine' },
    { code: 'nh', name: 'New Hampshire' },
    { code: 'ri', name: 'Rhode Island' }
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

  // Load data for edit mode
  $: if (mode === 'edit' && location) {
    formData = {
      loc_name: location.loc_name || '',
      aka_name: location.aka_name || '',
      state: location.state || 'ny',
      type: location.type || 'industrial',
      sub_type: location.sub_type || '',
      street_address: location.street_address || '',
      city: location.city || '',
      zip_code: location.zip_code || '',
      lat: location.lat,
      lon: location.lon,
      gps_source: location.gps_source || 'manual'
    };
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

    isSubmitting = true;

    try {
      // Prepare data for API
      const data = {
        loc_name: formData.loc_name.trim(),
        aka_name: formData.aka_name.trim() || null,
        state: formData.state,
        type: formData.type,
        sub_type: formData.sub_type.trim() || null,
        street_address: formData.street_address.trim() || null,
        city: formData.city.trim() || null,
        zip_code: formData.zip_code.trim() || null,
        lat: formData.lat !== null && formData.lat !== '' ? parseFloat(formData.lat) : null,
        lon: formData.lon !== null && formData.lon !== '' ? parseFloat(formData.lon) : null,
        gps_source: formData.gps_source
      };

      if (mode === 'create') {
        await locations.create(data);
        dispatch('created');
      } else {
        await locations.update(location.loc_uuid, data);
        dispatch('updated');
      }

      close();
    } catch (error) {
      console.error('Failed to save location:', error);
      errors.submit = error.message || 'Failed to save location';
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
      aka_name: '',
      state: 'ny',
      type: 'industrial',
      sub_type: '',
      street_address: '',
      city: '',
      zip_code: '',
      lat: null,
      lon: null,
      gps_source: 'manual'
    };
    errors = {};
  }

  function handleKeydown(event) {
    if (event.key === 'Escape') {
      close();
    }
  }
</script>

{#if isOpen}
  <div
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    on:click={close}
    on:keydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    tabindex="-1"
  >
    <div
      class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      on:click|stopPropagation
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
              <select
                id="state"
                bind:value={formData.state}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {#each states as state}
                  <option value={state.code}>{state.name}</option>
                {/each}
              </select>
            </div>

            <div>
              <label for="type" class="block text-sm font-medium text-gray-700 mb-1">
                Type <span class="text-red-500">*</span>
              </label>
              <select
                id="type"
                bind:value={formData.type}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {#each types as type}
                  <option value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                {/each}
              </select>
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
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., textile mill, warehouse"
            />
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
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Albany"
              />
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
