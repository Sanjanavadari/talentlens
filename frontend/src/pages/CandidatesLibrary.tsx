import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { AppNav } from '../components/AppNav'
import { CandidateCard } from '../components/CandidateCard'
import { listCandidates } from '../services/api'
import type { Candidate } from '../types'

function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: unknown } } })
      .response
    const detail = response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail)) {
      return detail.map((item) => JSON.stringify(item)).join('; ')
    }
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Something went wrong. Please try again.'
}

function collectSkills(candidates: Candidate[]): string[] {
  const skills = new Set<string>()
  for (const candidate of candidates) {
    const fields = candidate.parsed_fields
    if (!fields || typeof fields !== 'object') {
      continue
    }
    const parsedSkills = (fields as { skills?: unknown }).skills
    if (!Array.isArray(parsedSkills)) {
      continue
    }
    for (const skill of parsedSkills) {
      const normalized = String(skill).trim()
      if (normalized) {
        skills.add(normalized)
      }
    }
  }
  return [...skills].sort((a, b) => a.localeCompare(b))
}

export function CandidatesLibrary() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [skillOptions, setSkillOptions] = useState<string[]>([])
  const [skill, setSkill] = useState('')
  const [minYears, setMinYears] = useState(0)
  const [search, setSearch] = useState('')
  const [appliedSearch, setAppliedSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadSkillOptions() {
      try {
        const all = await listCandidates()
        if (!cancelled) {
          setSkillOptions(collectSkills(all))
        }
      } catch {
        // Skill options are optional; the filtered list fetch surfaces errors.
      }
    }

    void loadSkillOptions()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadCandidates() {
      setLoading(true)
      setError(null)
      try {
        const results = await listCandidates({
          skill: skill || undefined,
          minExperienceYears: minYears > 0 ? minYears : undefined,
          search: appliedSearch || undefined,
        })
        if (!cancelled) {
          setCandidates(results)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err))
          setCandidates([])
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadCandidates()
    return () => {
      cancelled = true
    }
  }, [skill, minYears, appliedSearch])

  const resultLabel = useMemo(() => {
    const count = candidates.length
    return `${count} candidate${count === 1 ? '' : 's'}`
  }, [candidates.length])

  const handleSearchSubmit = (event: FormEvent) => {
    event.preventDefault()
    setAppliedSearch(search.trim())
  }

  const clearFilters = () => {
    setSkill('')
    setMinYears(0)
    setSearch('')
    setAppliedSearch('')
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-violet-600">
              TalentLens
            </p>
            <h1 className="text-2xl font-semibold text-slate-900">
              Candidates library
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Browse uploaded resumes and filter by skill, experience, or text search.
            </p>
          </div>
          <AppNav />
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[320px_1fr]">
        <section className="h-fit rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Filters</h2>
          <p className="mt-1 text-sm text-slate-500">
            Filters apply server-side against parsed candidate fields.
          </p>

          <div className="mt-6 space-y-5">
            <div>
              <label
                htmlFor="filter-skill"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Skill
              </label>
              <input
                id="filter-skill"
                list="skill-options"
                value={skill}
                onChange={(event) => setSkill(event.target.value)}
                placeholder="e.g. python"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
              />
              <datalist id="skill-options">
                {skillOptions.map((option) => (
                  <option key={option} value={option} />
                ))}
              </datalist>
            </div>

            <div>
              <label
                htmlFor="filter-min-years"
                className="mb-2 flex items-center justify-between text-sm font-medium text-slate-700"
              >
                <span>Minimum years</span>
                <span className="tabular-nums text-slate-500">{minYears}</span>
              </label>
              <input
                id="filter-min-years"
                type="range"
                min={0}
                max={20}
                step={1}
                value={minYears}
                onChange={(event) => setMinYears(Number(event.target.value))}
                className="w-full accent-violet-600"
              />
            </div>

            <form onSubmit={handleSearchSubmit}>
              <label
                htmlFor="filter-search"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Search
              </label>
              <div className="flex gap-2">
                <input
                  id="filter-search"
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Filename or resume text"
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
                />
                <button
                  type="submit"
                  className="rounded-xl bg-violet-600 px-3 py-2 text-sm font-semibold text-white hover:bg-violet-700"
                >
                  Go
                </button>
              </div>
            </form>

            <button
              type="button"
              onClick={clearFilters}
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Clear filters
            </button>
          </div>
        </section>

        <section className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <p className="text-sm font-medium text-slate-700">{resultLabel}</p>
          </div>

          {error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          {loading ? (
            <div className="flex min-h-[280px] items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="text-center">
                <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-violet-200 border-t-violet-600" />
                <p className="text-sm font-medium text-slate-700">Loading candidates…</p>
              </div>
            </div>
          ) : null}

          {!loading && candidates.length === 0 ? (
            <div className="flex min-h-[280px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center shadow-sm">
              <div>
                <p className="text-lg font-medium text-slate-800">No candidates found</p>
                <p className="mt-2 max-w-md text-sm text-slate-500">
                  Upload resumes from the ranking dashboard, or loosen the active filters.
                </p>
              </div>
            </div>
          ) : null}

          {!loading
            ? candidates.map((candidate) => (
                <CandidateCard
                  key={candidate.id}
                  variant="library"
                  candidate={candidate}
                />
              ))
            : null}
        </section>
      </main>
    </div>
  )
}
