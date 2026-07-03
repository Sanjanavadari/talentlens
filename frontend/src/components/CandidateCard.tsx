import { useState } from 'react'

import type { RankedCandidate } from '../types'
import { ScoreBreakdownPanel } from './ScoreBreakdownPanel'

interface CandidateCardProps {
  candidate: RankedCandidate
}

function rankBadgeClasses(rank: number): string {
  if (rank === 1) {
    return 'bg-amber-100 text-amber-800 ring-amber-200'
  }
  if (rank === 2) {
    return 'bg-slate-200 text-slate-800 ring-slate-300'
  }
  if (rank === 3) {
    return 'bg-orange-100 text-orange-800 ring-orange-200'
  }
  return 'bg-slate-100 text-slate-700 ring-slate-200'
}

export function CandidateCard({ candidate }: CandidateCardProps) {
  const [expanded, setExpanded] = useState(candidate.rank <= 3)
  const displayName = candidate.filename.replace(/\.pdf$/i, '').replace(/_/g, ' ')

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-4">
          <span
            className={`inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold ring-1 ${rankBadgeClasses(candidate.rank)}`}
          >
            #{candidate.rank}
          </span>
          <div className="min-w-0">
            <h3 className="truncate text-base font-semibold text-slate-900">
              {displayName}
            </h3>
            <p className="truncate text-sm text-slate-500">{candidate.filename}</p>
          </div>
        </div>

        <div className="text-right">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Overall score
          </p>
          <p className="text-3xl font-bold tabular-nums text-violet-700">
            {Math.round(candidate.final_score * 100)}%
          </p>
        </div>
      </div>

      {candidate.breakdown.matched_skills.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {candidate.breakdown.matched_skills.map((skill) => (
            <span
              key={skill}
              className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-medium text-violet-800"
            >
              {skill}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">No matched skills for this role.</p>
      )}

      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="mt-4 text-sm font-medium text-violet-700 hover:text-violet-900"
      >
        {expanded ? 'Hide breakdown' : 'View breakdown'}
      </button>

      {expanded ? <ScoreBreakdownPanel breakdown={candidate.breakdown} /> : null}
    </article>
  )
}
