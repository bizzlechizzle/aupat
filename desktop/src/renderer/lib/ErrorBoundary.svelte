<script>
  /**
   * Error Boundary Component
   *
   * Catches errors in child components and displays a fallback UI.
   * Prevents entire app from crashing when a component fails.
   */

  import { createEventDispatcher, onMount, onDestroy } from 'svelte';

  export let fallbackMessage = 'Something went wrong';
  export let showDetails = true;

  const dispatch = createEventDispatcher();

  let error = null;
  let errorInfo = null;
  let hasError = false;

  function handleError(event) {
    // Prevent default error handling
    event.preventDefault();

    error = event.error || event.reason || new Error('Unknown error');
    errorInfo = {
      message: error.message || 'Unknown error',
      stack: error.stack || '',
      timestamp: new Date().toISOString()
    };

    hasError = true;

    // Log to console
    console.error('Error caught by boundary:', error);

    // Dispatch event for parent components
    dispatch('error', { error, errorInfo });

    return false;
  }

  function reset() {
    error = null;
    errorInfo = null;
    hasError = false;
  }

  onMount(() => {
    // Listen for unhandled errors
    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleError);
  });

  onDestroy(() => {
    window.removeEventListener('error', handleError);
    window.removeEventListener('unhandledrejection', handleError);
  });
</script>

{#if hasError}
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-6">
    <div class="max-w-2xl w-full bg-white shadow-lg rounded-lg p-8">
      <!-- Error Icon -->
      <div class="flex items-center justify-center w-16 h-16 mx-auto bg-red-100 rounded-full mb-6">
        <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>

      <!-- Error Message -->
      <h2 class="text-2xl font-bold text-gray-900 text-center mb-4">
        {fallbackMessage}
      </h2>

      <p class="text-gray-600 text-center mb-6">
        The application encountered an unexpected error. You can try reloading the app or contact support if the problem persists.
      </p>

      {#if showDetails && errorInfo}
        <div class="bg-gray-50 rounded-lg p-4 mb-6">
          <h3 class="text-sm font-semibold text-gray-700 mb-2">Error Details:</h3>
          <p class="text-sm text-red-600 font-mono mb-2">{errorInfo.message}</p>
          {#if errorInfo.stack}
            <details class="text-xs text-gray-600">
              <summary class="cursor-pointer hover:text-gray-800 mb-2">Stack Trace</summary>
              <pre class="bg-white p-2 rounded border border-gray-200 overflow-x-auto">{errorInfo.stack}</pre>
            </details>
          {/if}
          <p class="text-xs text-gray-500 mt-2">Time: {new Date(errorInfo.timestamp).toLocaleString()}</p>
        </div>
      {/if}

      <!-- Actions -->
      <div class="flex justify-center gap-4">
        <button
          on:click={reset}
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
        <button
          on:click={() => window.location.reload()}
          class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Reload App
        </button>
      </div>
    </div>
  </div>
{:else}
  <slot />
{/if}
