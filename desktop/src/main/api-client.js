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
const BASE_DELAY = 1000; // 1 second base delay for exponential backoff

/**
 * Determine if an error is retryable
 *
 * @param {Error} error - Error object
 * @param {Response} response - HTTP response (if available)
 * @returns {boolean} True if error should be retried
 */
function isRetryableError(error, response = null) {
  // Check error object if provided
  if (error && error.name) {
    // Network errors (connection refused, DNS failure, etc.)
    if (error.name === 'TypeError') {
      return true;
    }

    // Timeout errors
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      return true;
    }
  }

  // HTTP errors - only retry server errors and rate limits
  if (response && response.status) {
    const status = response.status;
    // 5xx server errors
    if (status >= 500 && status < 600) {
      return true;
    }
    // 429 rate limit
    if (status === 429) {
      return true;
    }
  }

  // All other errors are not retryable (4xx client errors, etc.)
  return false;
}

/**
 * Calculate exponential backoff delay
 *
 * @param {number} attempt - Retry attempt number (0-indexed)
 * @returns {number} Delay in milliseconds
 */
function calculateBackoffDelay(attempt) {
  // Exponential: 1s, 2s, 4s
  return BASE_DELAY * Math.pow(2, attempt);
}

export function createAPIClient(baseUrl) {
  let currentBaseUrl = baseUrl;

  /**
   * Make HTTP request with retries
   *
   * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
   * @param {string} path - API path (e.g., '/api/locations')
   * @param {object} data - Request body (for POST/PUT)
   * @param {number} attempt - Current attempt number (0-indexed)
   * @returns {Promise<any>} Response data
   */
  async function request(method, path, data = null, attempt = 0) {
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

    let response = null;

    try {
      log.debug(`${method} ${url} (attempt ${attempt + 1}/${MAX_RETRIES + 1})`);
      response = await fetch(url, options);

      if (!response.ok) {
        // Check if error is retryable before throwing
        if (isRetryableError(null, response) && attempt < MAX_RETRIES) {
          const delay = calculateBackoffDelay(attempt);
          log.warn(
            `${method} ${url} returned ${response.status}, retrying in ${delay}ms... (attempt ${attempt + 1}/${MAX_RETRIES + 1})`
          );
          await new Promise((resolve) => setTimeout(resolve, delay));
          return request(method, path, data, attempt + 1);
        }

        // Not retryable or out of retries
        const errorText = await response.text();
        throw new Error(
          `HTTP ${response.status}: ${errorText || response.statusText}`
        );
      }

      // Handle empty responses (e.g., DELETE)
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const text = await response.text();
        // Handle empty JSON responses
        if (!text || text.trim() === '') {
          return null;
        }
        try {
          return JSON.parse(text);
        } catch (parseError) {
          log.error(`Failed to parse JSON response from ${url}:`, parseError?.message || parseError);
          throw new Error(`Invalid JSON response: ${parseError?.message || 'unknown error'}`);
        }
      }

      return null;
    } catch (error) {
      // Retry on network errors, timeouts, and retryable HTTP errors
      if (isRetryableError(error, response) && attempt < MAX_RETRIES) {
        const delay = calculateBackoffDelay(attempt);
        const errorType = error?.name === 'AbortError' || error?.name === 'TimeoutError'
          ? 'timeout'
          : error?.name === 'TypeError'
          ? 'network error'
          : 'error';

        log.warn(
          `${method} ${url} failed (${errorType}), retrying in ${delay}ms... (attempt ${attempt + 1}/${MAX_RETRIES + 1})`
        );
        await new Promise((resolve) => setTimeout(resolve, delay));
        return request(method, path, data, attempt + 1);
      }

      // Log and rethrow
      log.error(`${method} ${url} failed after ${attempt + 1} attempts:`, error?.message || error);
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
