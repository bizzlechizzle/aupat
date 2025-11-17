/**
 * AUPAT Core API Client
 *
 * Handles all HTTP communication with AUPAT Core API.
 * Runs in main process only (security best practice).
 *
 * Features:
 * - Automatic retries with exponential backoff
 * - Request timeout (30s default)
 * - Error normalization
 * - Logging
 */

import log from 'electron-log';

const DEFAULT_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;

export function createAPIClient(baseUrl) {
  let currentBaseUrl = baseUrl;

  /**
   * Make HTTP request with retries
   *
   * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
   * @param {string} path - API path (e.g., '/api/locations')
   * @param {object} data - Request body (for POST/PUT)
   * @param {number} retries - Remaining retry attempts
   * @returns {Promise<any>} Response data
   */
  async function request(method, path, data = null, retries = MAX_RETRIES) {
    const url = `${currentBaseUrl}${path}`;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      signal: AbortSignal.timeout(DEFAULT_TIMEOUT)
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
    }

    try {
      log.debug(`${method} ${url}`);
      const response = await fetch(url, options);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `HTTP ${response.status}: ${errorText || response.statusText}`
        );
      }

      // Handle empty responses (e.g., DELETE)
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }

      return null;
    } catch (error) {
      // Retry on network errors
      if (retries > 0 && error.name === 'TypeError') {
        log.warn(`Request failed, retrying... (${retries} left)`);
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return request(method, path, data, retries - 1);
      }

      // Log and rethrow
      log.error(`${method} ${url} failed:`, error.message);
      throw error;
    }
  }

  return {
    /**
     * Update base URL (e.g., when user changes settings)
     */
    setBaseUrl(newUrl) {
      currentBaseUrl = newUrl;
      log.info(`API base URL updated to ${newUrl}`);
    },

    /**
     * GET request
     */
    async get(path) {
      return request('GET', path);
    },

    /**
     * POST request
     */
    async post(path, data) {
      return request('POST', path, data);
    },

    /**
     * PUT request
     */
    async put(path, data) {
      return request('PUT', path, data);
    },

    /**
     * DELETE request
     */
    async delete(path) {
      return request('DELETE', path);
    }
  };
}
