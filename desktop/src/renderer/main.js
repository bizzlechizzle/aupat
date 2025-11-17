/**
 * AUPAT Desktop - Renderer Entry Point
 *
 * Mounts the Svelte app and initializes stores
 */

import './styles/app.css';
import App from './App.svelte';
import { settings } from './stores/settings.js';

// Initialize settings on app start
settings.load();

const app = new App({
  target: document.getElementById('app')
});

export default app;
