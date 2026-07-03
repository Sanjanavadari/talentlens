import { useMemo, useState, type ChangeEvent, type FormEvent } from 'react'

import { CandidateCard } from '../components/CandidateCard'
import { ScoreChart } from '../components/ScoreChart'
import { useRanking } from '../hooks/useRanking'

export function Dashboard() {
  const { rankResponse, loading, error, runRanking, reset } = useRanking()
  const [title, setTitle] = useState('Backend Engineer')
  const [jdText, setJdText] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])

  const rankedCandidates = useMemo(() => {
    if (!rankResponse) {
      return []
    }
    return [...rankResponse.ranked_candidates].sort((a, b) => a.rank - b.rank)
  }, [rankResponse])

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? [])
    setSelectedFiles(files)
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    await runRanking(selectedFiles, title, jdText)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-violet-600">
              TalentLens
            </p>
            <h1 className="text-2xl font-semibold text-slate-900">
              Candidate Intelligence Dashboard
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Upload resumes, paste a job description, and rank candidates with explainable scores.
            </p>
          </div>
          {rankResponse ? (
            <button
              type="button"
              onClick={reset}
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Clear results
            </button>
          ) : null}
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[380px_1fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Rank candidates</h2>
          <p className="mt-1 text-sm text-slate-500">
            Upload PDF resumes and describe the role you are hiring for.
          </p>

          <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="jd-title"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Job title
              </label>
              <input
                id="jd-title"
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
                placeholder="Backend Engineer"
              />
            </div>

            <div>
              <label
                htmlFor="jd-text"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Job description
              </label>
              <textarea
                id="jd-text"
                value={jdText}
                onChange={(event) => setJdText(event.target.value)}
                rows={12}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm leading-relaxed shadow-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
                placeholder="Paste requirements, years of experience, and required skills..."
              />
            </div>

            <div>
              <label
                htmlFor="resume-files"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Resume PDFs
              </label>
              <input
                id="resume-files"
                type="file"
                accept="application/pdf,.pdf"
                multiple
                onChange={handleFileChange}
                className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-violet-600 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-violet-700"
              />
              {selectedFiles.length > 0 ? (
                <p className="mt-2 text-sm text-slate-500">
                  {selectedFiles.length} file{selectedFiles.length === 1 ? '' : 's'} selected
                </p>
              ) : null}
            </div>

            {error ? (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:bg-violet-300"
            >
              {loading ? 'Ranking candidates...' : 'Rank candidates'}
            </button>
          </form>
        </section>

        <section className="space-y-6">
          {!rankResponse && !loading ? (
            <div className="flex min-h-[420px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center shadow-sm">
              <div>
                <p className="text-lg font-medium text-slate-800">No rankings yet</p>
                <p className="mt-2 max-w-md text-sm text-slate-500">
                  Upload a few sample resumes from the backend dataset and paste a job
                  description to see ranked results with full score breakdowns.
                </p>
              </div>
            </div>
          ) : null}

          {loading ? (
            <div className="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="text-center">
                <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-violet-200 border-t-violet-600" />
                <p className="text-sm font-medium text-slate-700">
                  Parsing resumes, embedding candidates, and computing scores...
                </p>
              </div>
            </div>
          ) : null}

          {rankResponse ? (
            <>
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm font-medium uppercase tracking-wide text-violet-600">
                  Results
                </p>
                <h2 className="mt-1 text-xl font-semibold text-slate-900">
                  {rankResponse.job_description_title}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {rankedCandidates.length} candidates ranked by final weighted score
                </p>
              </div>

              <ScoreChart candidates={rankedCandidates} />

              <div className="space-y-4">
                {rankedCandidates.map((candidate) => (
                  <CandidateCard key={candidate.candidate_id} candidate={candidate} />
                ))}
              </div>
            </>
          ) : null}
        </section>
      </main>
    </div>
  )
}
