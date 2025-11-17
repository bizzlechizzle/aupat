/**
 * Vitest Configuration
 *
 * Test configuration for AUPAT Desktop unit and integration tests.
 */

import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/**',
        'dist-electron/**',
        'dist-builder/**',
        'tests/**'
      ]
    }
  }
});
