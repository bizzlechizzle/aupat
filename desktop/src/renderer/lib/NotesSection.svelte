<script>
  /**
   * Notes Section Component
   *
   * Displays user notes for a location with CRUD operations.
   * Multiple notes can be attached to each location.
   *
   * Features:
   * - List of note titles
   * - Add new note
   * - Edit existing note
   * - Delete note
   * - Simple textarea editor
   */

  import { createEventDispatcher } from 'svelte';

  export let locationUuid;
  export let notes = [];

  const dispatch = createEventDispatcher();

  // Edit state
  let editingNoteId = null;
  let showAddForm = false;

  // Form data
  let noteTitle = '';
  let noteContent = '';

  // Loading states
  let saving = false;
  let deleting = null;
  let error = null;

  function startAddNote() {
    noteTitle = '';
    noteContent = '';
    editingNoteId = null;
    showAddForm = true;
  }

  function startEditNote(note) {
    noteTitle = note.title || '';
    noteContent = note.content || '';
    editingNoteId = note.note_uuid;
    showAddForm = true;
  }

  function cancelEdit() {
    noteTitle = '';
    noteContent = '';
    editingNoteId = null;
    showAddForm = false;
    error = null;
  }

  async function saveNote() {
    if (!noteContent.trim()) {
      error = 'Note content is required';
      return;
    }

    saving = true;
    error = null;

    try {
      if (editingNoteId) {
        // Update existing note
        const response = await fetch(`/api/notes/${editingNoteId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: noteTitle.trim(),
            content: noteContent.trim()
          })
        });

        const result = await response.json();
        if (!result.success) {
          error = result.error || 'Failed to update note';
          return;
        }

        // Update in list
        notes = notes.map(n =>
          n.note_uuid === editingNoteId ? result.data : n
        );

      } else {
        // Create new note
        const response = await fetch(`/api/locations/${locationUuid}/notes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: noteTitle.trim(),
            content: noteContent.trim()
          })
        });

        const result = await response.json();
        if (!result.success) {
          error = result.error || 'Failed to create note';
          return;
        }

        // Add to list
        notes = [result.data, ...notes];
      }

      // Close form
      cancelEdit();
      dispatch('notesUpdated', notes);

    } catch (err) {
      console.error('Save note failed:', err);
      error = err.message;
    } finally {
      saving = false;
    }
  }

  async function deleteNote(noteUuid) {
    if (!confirm('Delete this note?')) return;

    deleting = noteUuid;
    error = null;

    try {
      const response = await fetch(`/api/notes/${noteUuid}`, {
        method: 'DELETE'
      });

      const result = await response.json();
      if (!result.success) {
        error = result.error || 'Failed to delete note';
        return;
      }

      // Remove from list
      notes = notes.filter(n => n.note_uuid !== noteUuid);
      dispatch('notesUpdated', notes);

    } catch (err) {
      console.error('Delete note failed:', err);
      error = err.message;
    } finally {
      deleting = null;
    }
  }

  function formatDate(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  }
</script>

<div class="notes-section">
  <div class="flex justify-between items-center mb-4">
    <h3 class="text-lg font-semibold text-gray-800">User Notes</h3>
    <button
      on:click={startAddNote}
      class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
    >
      + Add Note
    </button>
  </div>

  <!-- Error message -->
  {#if error}
    <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 mb-4">
      <button on:click={() => error = null} class="float-right">×</button>
      {error}
    </div>
  {/if}

  <!-- Add/Edit Form -->
  {#if showAddForm}
    <div class="bg-gray-50 border border-gray-300 rounded-lg p-4 mb-4">
      <h4 class="font-medium mb-3">
        {editingNoteId ? 'Edit Note' : 'New Note'}
      </h4>

      <div class="space-y-3">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Title (optional)
          </label>
          <input
            type="text"
            bind:value={noteTitle}
            placeholder="Note title..."
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Content *
          </label>
          <textarea
            bind:value={noteContent}
            placeholder="Your notes..."
            rows="6"
            class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500 font-mono text-sm"
          ></textarea>
        </div>

        <div class="flex justify-end gap-2">
          <button
            on:click={cancelEdit}
            class="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            on:click={saveNote}
            disabled={saving}
            class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Note'}
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Notes List -->
  {#if notes.length === 0}
    <div class="text-center py-8 text-gray-500">
      <p>No notes yet. Click "Add Note" to create one.</p>
    </div>
  {:else}
    <div class="space-y-3">
      {#each notes as note}
        <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
          <div class="flex justify-between items-start mb-2">
            <div class="flex-1">
              {#if note.title}
                <h4 class="font-medium text-gray-900">{note.title}</h4>
              {/if}
              <p class="text-xs text-gray-500">
                Updated: {formatDate(note.updated_at)}
              </p>
            </div>

            <div class="flex gap-2">
              <button
                on:click={() => startEditNote(note)}
                class="text-blue-600 hover:text-blue-800 text-sm"
              >
                Edit
              </button>
              <button
                on:click={() => deleteNote(note.note_uuid)}
                disabled={deleting === note.note_uuid}
                class="text-red-600 hover:text-red-800 text-sm disabled:opacity-50"
              >
                {deleting === note.note_uuid ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>

          <div class="text-gray-700 text-sm whitespace-pre-wrap font-mono">
            {note.content}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .notes-section {
    /* Optional: Add custom styling */
  }
</style>
