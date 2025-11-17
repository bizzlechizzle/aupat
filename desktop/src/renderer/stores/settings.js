/**
 * Settings Store
 *
 * Manages application settings (API URLs, map defaults, etc.)
 * Persists via electron-store in main process
 */

import { writable } from 'svelte/store';

// Default settings (fallback if API unavailable)
const defaultSettings = {
  apiUrl: 'http://localhost:5001',
  immichUrl: 'http://localhost:2283',
  archiveboxUrl: 'http://localhost:8001',
  mapCenter: { lat: 42.6526, lng: -73.7562 }, // Albany, NY
  mapZoom: 10
};

function createSettingsStore() {
  const { subscribe, set, update } = writable(defaultSettings);

  return {
    subscribe,

    /**
     * Load settings from main process
     */
    async load() {
      try {
        const settings = await window.api.settings.get();
        set(settings);
      } catch (error) {
        console.error('Failed to load settings:', error);
        set(defaultSettings);
      }
    },

    /**
     * Update a single setting
     */
    async updateSetting(key, value) {
      try {
        await window.api.settings.set(key, value);
        update(s => ({ ...s, [key]: value }));
      } catch (error) {
        console.error(`Failed to update setting ${key}:`, error);
        throw error;
      }
    }
  };
}

export const settings = createSettingsStore();
