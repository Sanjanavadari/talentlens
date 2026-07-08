import { useCallback, useEffect, useState, type FormEvent } from 'react'

import {
  createNote,
  deleteNote,
  getNotes,
  updateNote,
} from '../services/api'
import type { CandidateNote } from '../types'

interface NotesPanelProps {
  candidateId: number
}

function formatTimestamp(value: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

export function NotesPanel({ candidateId }: NotesPanelProps) {
  const [notes, setNotes] = useState<CandidateNote[]>([])
  const [draft, setDraft] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editDraft, setEditDraft] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadNotes = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getNotes(candidateId)
      setNotes(data)
    } catch {
      setError('Failed to load notes.')
    } finally {
      setLoading(false)
    }
  }, [candidateId])

  useEffect(() => {
    void loadNotes()
  }, [loadNotes])

  const handleAdd = async (event: FormEvent) => {
    event.preventDefault()
    const noteText = draft.trim()
    if (!noteText) {
      return
    }

    setSaving(true)
    setError(null)
    try {
      const created = await createNote(candidateId, { note_text: noteText })
      setNotes((current) => [created, ...current])
      setDraft('')
    } catch {
      setError('Failed to add note.')
    } finally {
      setSaving(false)
    }
  }

  const startEdit = (note: CandidateNote) => {
    setEditingId(note.id)
    setEditDraft(note.note_text)
    setError(null)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditDraft('')
  }

  const saveEdit = async (noteId: number) => {
    const noteText = editDraft.trim()
    if (!noteText) {
      return
    }

    setSaving(true)
    setError(null)
    try {
      const updated = await updateNote(noteId, { note_text: noteText })
      setNotes((current) =>
        current.map((note) => (note.id === noteId ? updated : note)),
      )
      cancelEdit()
    } catch {
      setError('Failed to update note.')
    } finally {
      setSaving(false)
    }
  }

  const removeNote = async (noteId: number) => {
    setSaving(true)
    setError(null)
    try {
      await deleteNote(noteId)
      setNotes((current) => current.filter((note) => note.id !== noteId))
      if (editingId === noteId) {
        cancelEdit()
      }
    } catch {
      setError('Failed to delete note.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mt-4 space-y-3 rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-sm font-semibold text-slate-900">Recruiter notes</h4>
        {loading ? (
          <span className="text-xs text-slate-500">Loading…</span>
        ) : (
          <span className="text-xs text-slate-500">
            {notes.length} note{notes.length === 1 ? '' : 's'}
          </span>
        )}
      </div>

      {error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {error}
        </p>
      ) : null}

      <form className="space-y-2" onSubmit={handleAdd}>
        <label htmlFor={`note-draft-${candidateId}`} className="sr-only">
          Add a note
        </label>
        <textarea
          id={`note-draft-${candidateId}`}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={3}
          placeholder="Add a private recruiter note…"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
        />
        <button
          type="submit"
          disabled={saving || !draft.trim()}
          className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Add note
        </button>
      </form>

      {!loading && notes.length === 0 ? (
        <p className="text-sm text-slate-500">No notes yet for this candidate.</p>
      ) : null}

      <ul className="space-y-3">
        {notes.map((note) => (
          <li
            key={note.id}
            className="rounded-lg border border-slate-200 bg-slate-50/80 px-3 py-2"
          >
            {editingId === note.id ? (
              <div className="space-y-2">
                <textarea
                  value={editDraft}
                  onChange={(event) => setEditDraft(event.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
                />
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={saving || !editDraft.trim()}
                    onClick={() => void saveEdit(note.id)}
                    className="rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:bg-violet-300"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    disabled={saving}
                    onClick={cancelEdit}
                    className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <p className="whitespace-pre-wrap text-sm text-slate-800">
                  {note.note_text}
                </p>
                <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs text-slate-500">
                    {formatTimestamp(note.updated_at)}
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => startEdit(note)}
                      className="text-xs font-medium text-violet-700 hover:text-violet-900"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void removeNote(note.id)}
                      className="text-xs font-medium text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
