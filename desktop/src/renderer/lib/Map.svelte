<script>
  /**
   * Map View Component
   *
   * Interactive map with clustered markers for all locations.
   * Uses Leaflet.js for rendering and Supercluster for marker clustering.
   *
   * Features:
   * - Loads all locations with GPS coordinates
   * - Clusters markers at low zoom levels
   * - Click marker to view location details
   * - Performance optimized for 200k+ markers
   */

  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import L from 'leaflet';
  import Supercluster from 'supercluster';
  import { settings } from '../stores/settings.js';
  import { locations } from '../stores/locations.js';
  import LocationDetail from './LocationDetail.svelte';

  const dispatch = createEventDispatcher();

  let mapContainer;
  let map;
  let markerLayer;
  let supercluster;
  let markers = [];
  let selectedLocation = null;

  // Filter state (v0.1.5)
  let activeFilters = {
    favorites: false,
    historical: false,
    undocumented: false
  };

  // Subscribe to settings for map defaults
  let mapCenter;
  let mapZoom;

  const unsubscribeSettings = settings.subscribe(s => {
    mapCenter = s.mapCenter;
    mapZoom = s.mapZoom;
  });

  onMount(async () => {
    // Initialize Leaflet map
    map = L.map(mapContainer).setView([mapCenter.lat, mapCenter.lng], mapZoom);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(map);

    // Initialize marker layer
    markerLayer = L.layerGroup().addTo(map);

    // Load markers from API
    await loadMarkers();

    // Update clusters on map move/zoom
    map.on('moveend', updateClusters);
    map.on('zoomend', updateClusters);
  });

  onDestroy(() => {
    if (map) {
      map.remove();
    }
    unsubscribeSettings();
  });

  /**
   * Load markers from AUPAT Core API
   */
  async function loadMarkers() {
    try {
      const response = await window.api.map.getMarkers();

      if (response.success) {
        // Convert to GeoJSON format for Supercluster
        const features = response.data
          .filter(loc => loc.lat && loc.lon)
          .map(loc => ({
            type: 'Feature',
            properties: {
              id: loc.loc_uuid,
              name: loc.loc_name,
              type: loc.type
            },
            geometry: {
              type: 'Point',
              coordinates: [loc.lon, loc.lat]
            }
          }));

        markers = features;

        // Initialize Supercluster
        supercluster = new Supercluster({
          radius: 60,
          maxZoom: 16
        });
        supercluster.load(features);

        // Initial render
        updateClusters();
      }
    } catch (error) {
      console.error('Failed to load markers:', error);
    }
  }

  /**
   * Update visible markers based on current map bounds and zoom
   */
  function updateClusters() {
    if (!map || !supercluster) return;

    // Clear existing markers
    markerLayer.clearLayers();

    // Get current map bounds and zoom
    const bounds = map.getBounds();
    const zoom = map.getZoom();

    // Get clusters for current view
    const clusters = supercluster.getClusters(
      [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()],
      Math.floor(zoom)
    );

    // Render clusters/markers
    clusters.forEach(cluster => {
      const [lng, lat] = cluster.geometry.coordinates;
      const properties = cluster.properties;

      if (cluster.properties.cluster) {
        // Render cluster
        const count = properties.point_count;
        const size = count < 100 ? 'small' : count < 1000 ? 'medium' : 'large';

        const clusterMarker = L.marker([lat, lng], {
          icon: L.divIcon({
            html: `<div class="cluster-marker cluster-${size}">${count}</div>`,
            className: 'cluster-marker-wrapper',
            iconSize: [40, 40]
          })
        });

        clusterMarker.on('click', () => {
          // Zoom into cluster
          const expansionZoom = supercluster.getClusterExpansionZoom(
            cluster.properties.cluster_id
          );
          map.setView([lat, lng], expansionZoom);
        });

        clusterMarker.addTo(markerLayer);
      } else {
        // Render individual marker
        const marker = L.marker([lat, lng], {
          icon: L.divIcon({
            html: '<div class="location-marker"></div>',
            className: 'location-marker-wrapper',
            iconSize: [12, 12]
          })
        });

        marker.on('click', () => {
          handleMarkerClick(properties.id);
        });

        marker.addTo(markerLayer);
      }
    });
  }

  /**
   * Handle marker click - dispatch event to parent or show sidebar
   */
  async function handleMarkerClick(locationId) {
    try {
      const response = await window.api.locations.getById(locationId);

      if (response.success) {
        // Dispatch event to parent (App.svelte) to navigate to location page
        dispatch('locationClick', { location: response.data });

        // Also set selectedLocation for sidebar preview (optional fallback)
        // selectedLocation = response.data;
      }
    } catch (error) {
      console.error('Failed to load location details:', error);
    }
  }

  /**
   * Close location detail sidebar
   */
  function closeDetail() {
    selectedLocation = null;
  }

  /**
   * Toggle filter and reload markers (v0.1.5)
   */
  function toggleFilter(filterName) {
    activeFilters[filterName] = !activeFilters[filterName];
    loadMarkers(); // Reload with new filters
  }

  /**
   * Go to random location (v0.1.5)
   */
  async function goToRandomLocation() {
    try {
      const response = await fetch('/api/locations/random');
      const result = await response.json();
      if (result.success && result.data) {
        const loc = result.data;
        if (loc.lat && loc.lon) {
          map.setView([loc.lat, loc.lon], 16);
        }
      }
    } catch (err) {
      console.error('Failed to go to random location:', err);
    }
  }
</script>

<div class="relative w-full h-full">
  <!-- Map Container -->
  <!-- Filter Toolbar -->
  <div class="filter-toolbar">
    <button
      on:click={() => toggleFilter('favorites')}
      class="filter-btn {activeFilters.favorites ? 'active' : ''}"
      title="Show favorites only"
    >
      Favorites
    </button>
    <button
      on:click={() => toggleFilter('historical')}
      class="filter-btn {activeFilters.historical ? 'active' : ''}"
      title="Show historical locations only"
    >
      Historical
    </button>
    <button
      on:click={() => toggleFilter('undocumented')}
      class="filter-btn {activeFilters.undocumented ? 'active' : ''}"
      title="Show undocumented locations only"
    >
      Undocumented
    </button>
    <button
      on:click={goToRandomLocation}
      class="filter-btn random-btn"
      title="Go to random location"
    >
      Random
    </button>
  </div>

  <div bind:this={mapContainer} class="map-container" />

  <!-- Location Detail Sidebar (when marker clicked) -->
  {#if selectedLocation}
    <LocationDetail location={selectedLocation} onClose={closeDetail} />
  {/if}

  <!-- Loading Indicator -->
  {#if markers.length === 0}
    <div class="absolute top-4 left-1/2 transform -translate-x-1/2 bg-white rounded-lg shadow-lg px-4 py-2">
      <p class="text-sm text-gray-600">Loading locations...</p>
    </div>
  {/if}
</div>

<style>
  .map-container {
    width: 100%;
    height: 100%;
  }

  /* Cluster marker styles - Abandoned Upstate branding */
  :global(.cluster-marker-wrapper) {
    background: none;
    border: none;
  }

  :global(.cluster-marker) {
    background: var(--au-accent-brown, #b9975c);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-family: var(--au-font-mono, monospace);
    font-size: 12px;
    width: 40px;
    height: 40px;
    border: 2px solid white;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  :global(.cluster-marker.cluster-medium) {
    background: var(--au-accent-gold, #d4af37);
    width: 50px;
    height: 50px;
    font-size: 14px;
  }

  :global(.cluster-marker.cluster-large) {
    background: var(--au-accent-rust, #a0522d);
    width: 60px;
    height: 60px;
    font-size: 16px;
  }

  /* Individual location marker - Abandoned Upstate branding */
  :global(.location-marker-wrapper) {
    background: none;
    border: none;
  }

  :global(.location-marker) {
    background: var(--au-black, #000000);
    border-radius: 50%;
    width: 12px;
    height: 12px;
    border: 2px solid white;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
  }

  :global(.location-marker:hover) {
    background: var(--au-accent-brown, #b9975c);
    transform: scale(1.3);
    cursor: pointer;
  }

  /* Filter Toolbar (v0.1.5) */
  .filter-toolbar {
    position: absolute;
    top: 10px;
    left: 10px;
    z-index: 1000;
    display: flex;
    gap: 8px;
  }

  .filter-btn {
    background: white;
    border: 2px solid #ddd;
    padding: 8px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: all 0.2s;
  }

  .filter-btn:hover {
    background: #f0f0f0;
    border-color: #999;
  }

  .filter-btn.active {
    background: #007bff;
    color: white;
    border-color: #0056b3;
  }

  .random-btn {
    background: #28a745;
    color: white;
    border-color: #1e7e34;
  }

  .random-btn:hover {
    background: #218838;
  }
</style>
