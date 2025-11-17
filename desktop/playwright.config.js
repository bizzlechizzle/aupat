/**
 * Playwright Configuration for AUPAT Desktop E2E Tests
 *
 * Configures Playwright to test Electron desktop application.
 * Follows FAANG PE principles: fast, reliable, maintainable.
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',

  // Test execution settings
  fullyParallel: false, // Electron apps can't run in parallel
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // One Electron instance at a time

  // Reporter
  reporter: [
    ['list'],
    ['html', { outputFolder: 'test-results/html' }]
  ],

  // Global test settings
  use: {
    // Capture screenshot on failure
    screenshot: 'only-on-failure',

    // Capture trace on failure (debugging)
    trace: 'on-first-retry',

    // Timeout for each assertion
    actionTimeout: 10000,
  },

  // Test timeout
  timeout: 60000, // 60s per test (Electron startup can be slow)

  // Expect timeout
  expect: {
    timeout: 5000
  },

  // Output directories
  outputDir: 'test-results/artifacts',
});
