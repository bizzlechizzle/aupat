<script>
  /**
   * Notes Section Component
   *
   * Displays and manages notes for a location.
   * Features: list, create, edit, delete notes.
   *
   * LILBITS: One component = One function (notes management)
   */

  import { onMount, createEventDispatcher } from 'svelte';

  export let locationUuid;

  const dispatch = createEventDispatcher();

  let notes = [];
  let loading = true;
  let error = null;

  // Form state
  let showForm = false;
  let editingNote = null;
  let formData = {
    note_title: '',
    note_body: ''
  };
  let formError = null;
  let saving = false;

  onMount(async () => {
    await loadNotes();
  });

  async function loadNotes() {
    try {
      loading = true;
      error = null;
      const response = await window.api.notes.getByLocation(locationUuid);
      if (response && response.success) {
        notes = response.data || [];
      } else {
        error = response?.error || 'Failed to load notes';
      }
    } catch (err) {
      console.error('Failed to load notes:', err);
      error = err.message;
    } finally {
      loading = false;
    }
  }

  function openCreateForm() {
    editingNote = null;
    formData = { note_title: '', note_body: '' };
    formError = null;
    showForm = true;
  }

  function openEditForm(note) {
    editingNote = note;
    formData = {
      note_title: note.note_title || '',
      note_body: note.note_body || ''
    };
    formError = null;
    showForm = true;
  }

  function closeForm() {
    showForm = false;
    editingNote = null;
    formData = { note_title: '', note_body: '' };
    formError = null;
  }

  async function handleSubmit() {
    formError = null;

    if (!formData.note_title.trim()) {
      formError = 'Note title is required';
      return;
    }

    try {
      saving = true;

      if (editingNote) {
        // Update existing note
        const response = await window.api.notes.update(editingNote.note_uuid, formData);
        if (response && response.success) {
          await loadNotes();
          closeForm();
        } else {
          formError = response?.error || 'Failed to update note';
        }
      } else {
        // Create new note
        const response = await window.api.notes.create({
          loc_uuid: locationUuid,
          ...formData
        });
        if (response && response.success) {
          await loadNotes();
          closeForm();
        } else {
          formError = response?.error || 'Failed to create note';
        }
      }
    } catch (err) {
      console.error('Failed to save note:', err);
      formError = err.message;
    } finally {
      saving = false;
    }
  }

  async function handleDelete(note) {
    if (!confirm(`Delete note "${note.note_title}"?`)) {
      return;
    }

    try {
      const response = await window.api.notes.delete(note.note_uuid);
      if (response && response.success) {
        await loadNotes();
      } else {
        alert('Failed to delete note: ' + (response?.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('Failed to delete note:', err);
      alert('Failed to delete note: ' + err.message);
    }
  }

  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
</script>

<div class="notes-section bg-white rounded-lg shadow-md p-6">
  <div class="flex items-center justify-between mb-4">
    <h2 class="text-xl font-bold text-gray-800">Notes</h2>
    <button
      on:click={openCreateForm}
      class="px-4 py-2 rounded-lg font-semibold text-white transition-colors"
      style="background-color: var(--au-accent-brown, #b9975c);"
    >
      Add Note
    </button>
  </div>

  {#if loading}
    <p class="text-gray-500">Loading notes...</p>
  {:else if error}
    <p class="text-red-600">Error: {error}</p>
  {:else if notes.length === 0}
    <p class="text-gray-500">No notes yet. Click "Add Note" to create one.</p>
  {:else}
    <div class="space-y-3">
      {#each notes as note}
        <div class="note-item border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h3 class="font-semibold text-gray-900 mb-1">{note.note_title}</h3>
              {#if note.note_body}
                <p class="text-sm text-gray-600 line-clamp-2">{note.note_body}</p>
              {/if}
              <p class="text-xs text-gray-400 mt-2">
                {formatDate(note.created_at)}
                {#if note.updated_at && note.updated_at !== note.created_at}
                  (edited {formatDate(note.updated_at)})
                {/if}
              </p>
            </div>
            <div class="flex gap-2 ml-4">
              <button
                on:click={() => openEditForm(note)}
                class="text-sm px-3 py-1 rounded hover:bg-gray-100 transition-colors"
                style="color: var(--au-accent-brown, #b9975c);"
              >
                Edit
              </button>
              <button
                on:click={() => handleDelete(note)}
                class="text-sm text-red-600 px-3 py-1 rounded hover:bg-red-50 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- Note Form Modal -->
{#if showForm}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" on:click={closeForm}>
    <div class="bg-white rounded-lg p-6 max-w-2xl w-full m-4" on:click|stopPropagation>
      <h2 class="text-2xl font-bold text-gray-900 mb-4">
        {editingNote ? 'Edit Note' : 'Create Note'}
      </h2>

      <form on:submit|preventDefault={handleSubmit} class="space-y-4">
        <div>
          <label for="note_title" class="block text-sm font-medium text-gray-700 mb-1">
            Title <span class="text-red-500">*</span>
          </label>
          <input
            id="note_title"
            type="text"
            bind:value={formData.note_title}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
            autofocus
          />
        </div>

        <div>
          <label for="note_body" class="block text-sm font-medium text-gray-700 mb-1">
            Content
          </label>
          <textarea
            id="note_body"
            bind:value={formData.note_body}
            rows="8"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Write your note here..."
          />
        </div>

        {#if formError}
          <p class="text-red-600 text-sm">{formError}</p>
        {/if}

        <div class="flex gap-3 justify-end">
          <button
            type="button"
            on:click={closeForm}
            class="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            type="submit"
            class="px-6 py-2 rounded-lg font-semibold text-white transition-colors"
            style="background-color: var(--au-accent-brown, #b9975c);"
            disabled={saving}
          >
            {saving ? 'Saving...' : editingNote ? 'Update' : 'Create'}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
