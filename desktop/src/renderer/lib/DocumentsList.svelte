<script>
  /**
   * Documents List Component
   *
   * Displays documents associated with a location.
   * Shows document name, type, and file size.
   *
   * LILBITS: One component = One function (documents display)
   */

  export let documents = [];
  export let locationUuid = '';

  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function formatFileSize(bytes) {
    if (!bytes) return 'Unknown size';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  function getFileIcon(ext) {
    if (!ext) return 'document';
    const lower = ext.toLowerCase();
    if (lower === 'pdf') return 'pdf';
    if (['doc', 'docx'].includes(lower)) return 'word';
    if (['txt', 'md'].includes(lower)) return 'text';
    return 'document';
  }

  function handleDocumentClick(doc) {
    dispatch('documentClick', { document: doc });
  }

  function handleOpenDocument(doc) {
    dispatch('openDocument', { document: doc });
  }
</script>

<div class="documents-section bg-white rounded-lg shadow-md p-6">
  <h2 class="text-xl font-bold text-gray-800 mb-4">Documents</h2>

  {#if documents && documents.length > 0}
    <div class="space-y-3">
      {#each documents as doc}
        <div
          class="document-item border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex items-start gap-3 flex-1">
              <div class="w-10 h-10 rounded bg-gray-100 flex items-center justify-center flex-shrink-0">
                <svg class="w-6 h-6 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-gray-900 truncate">
                  {doc.doc_name || doc.original_name || 'Untitled Document'}
                </h3>
                <p class="text-sm text-gray-600 mt-1">
                  {doc.doc_ext ? doc.doc_ext.toUpperCase() : 'Unknown'} • {formatFileSize(doc.doc_size)}
                </p>
                {#if doc.created_at}
                  <p class="text-xs text-gray-400 mt-1">
                    Added {new Date(doc.created_at).toLocaleDateString()}
                  </p>
                {/if}
              </div>
            </div>
            <button
              on:click={() => handleOpenDocument(doc)}
              class="ml-4 px-4 py-2 rounded-lg text-sm font-medium transition-colors text-white"
              style="background-color: var(--au-accent-brown, #b9975c);"
            >
              Open
            </button>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <p class="text-gray-500 text-center py-8">No documents uploaded yet</p>
  {/if}
</div>

<style>
  .document-item:hover {
    transform: translateY(-1px);
  }
</style>
