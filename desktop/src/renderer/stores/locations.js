/**
 * Locations Store
 *
 * Manages location data fetched from AUPAT Core API
 * Provides reactive state for location list and selected location
 */

import { writable, derived } from 'svelte/store';

function createLocationsStore() {
  const { subscribe, set, update } = writable({
    items: [],
    loading: false,
    error: null,
    selectedId: null
  });

  return {
    subscribe,

    /**
     * Fetch all locations from API
     */
    async fetchAll() {
      update(s => ({ ...s, loading: true, error: null }));

      try {
        const response = await window.api.locations.getAll();

        if (response.success) {
          update(s => ({
            ...s,
            items: response.data,
            loading: false
          }));
        } else {
          throw new Error(response.error);
        }
      } catch (error) {
        console.error('Failed to fetch locations:', error);
        update(s => ({
          ...s,
          loading: false,
          error: error.message
        }));
      }
    },

    /**
     * Select a location by ID
     */
    select(id) {
      update(s => ({ ...s, selectedId: id }));
    },

    /**
     * Deselect current location
     */
    deselect() {
      update(s => ({ ...s, selectedId: null }));
    },

    /**
     * Create new location
     */
    async create(locationData) {
      try {
        const response = await window.api.locations.create(locationData);

        if (response.success) {
          update(s => ({
            ...s,
            items: [...s.items, response.data]
          }));
          return response.data;
        } else {
          throw new Error(response.error);
        }
      } catch (error) {
        console.error('Failed to create location:', error);
        throw error;
      }
    },

    /**
     * Update existing location
     */
    async update(id, locationData) {
      try {
        console.log('[Store] Updating location:', id, locationData);

        if (!id) {
          throw new Error('Location ID is required for update');
        }

        const response = await window.api.locations.update(id, locationData);
        console.log('[Store] Update response:', response);

        if (response.success) {
          update(s => ({
            ...s,
            items: s.items.map(item =>
              item.loc_uuid === id ? response.data : item
            )
          }));
          console.log('[Store] Location updated successfully');
          return response.data;
        } else {
          const errorMsg = response.error || 'Update failed with no error message';
          console.error('[Store] Update failed:', errorMsg);
          throw new Error(errorMsg);
        }
      } catch (error) {
        console.error('[Store] Failed to update location:', error);
        console.error('[Store] Error type:', error.constructor.name);
        console.error('[Store] Error message:', error.message);
        throw error;
      }
    },

    /**
     * Delete location
     */
    async delete(id) {
      try {
        const response = await window.api.locations.delete(id);

        if (response.success) {
          update(s => ({
            ...s,
            items: s.items.filter(item => item.loc_uuid !== id),
            selectedId: s.selectedId === id ? null : s.selectedId
          }));
        } else {
          throw new Error(response.error);
        }
      } catch (error) {
        console.error('Failed to delete location:', error);
        throw error;
      }
    }
  };
}

export const locations = createLocationsStore();

/**
 * Derived store: Selected location details
 */
export const selectedLocation = derived(
  locations,
  ($locations) => {
    if (!$locations.selectedId) return null;
    return $locations.items.find(
      item => item.loc_uuid === $locations.selectedId
    );
  }
);
