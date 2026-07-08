import type { ScoreBreakdown } from '../types'

interface ScoreBreakdownPanelProps {
  breakdown: ScoreBreakdown
  explanationLoading?: boolean
  onRequestExplanation?: () => Promise<void> | void
}

const METRIC_ROWS: Array<{
  key: keyof ScoreBreakdown
  label: string
  weight?: string
}> = [
  {
    key: 'semantic_similarity_score',
    label: 'Semantic similarity',
    weight: '70% of final',
  },
  { key: 'experience_score', label: 'Experience' },
  { key: 'skills_match_score', label: 'Skills match' },
  { key: 'education_score', label: 'Education' },
  { key: 'certification_score', label: 'Certifications' },
  { key: 'recency_score', label: 'Recency' },
  { key: 'rule_score', label: 'Rule-based composite', weight: '30% of final' },
  { key: 'final_score', label: 'Final weighted score' },
]

function formatScore(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function ScoreBreakdownPanel({
  breakdown,
  explanationLoading = false,
  onRequestExplanation,
}: ScoreBreakdownPanelProps) {
  const explanation = breakdown.llm_explanation?.trim() || null
  const canRequest = Boolean(onRequestExplanation) && !explanation

  return (
    <div className="mt-4 space-y-3 rounded-xl border border-slate-200 bg-slate-50/80 p-4">
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-sm font-semibold text-slate-900">Score breakdown</h4>
        <p className="text-xs text-slate-500">final = 0.7 × semantic + 0.3 × rule</p>
      </div>

      <dl className="space-y-2">
        {METRIC_ROWS.map(({ key, label, weight }) => {
          const value = breakdown[key]
          if (typeof value !== 'number') {
            return null
          }

          const isFinal = key === 'final_score'
          return (
            <div
              key={key}
              className={`grid grid-cols-[1fr_auto] items-center gap-3 rounded-lg px-3 py-2 ${
                isFinal ? 'bg-violet-100/70 ring-1 ring-violet-200' : 'bg-white'
              }`}
            >
              <div>
                <dt className="text-sm font-medium text-slate-800">{label}</dt>
                {weight ? (
                  <dd className="text-xs text-slate-500">{weight}</dd>
                ) : null}
              </div>
              <dd
                className={`text-sm font-semibold tabular-nums ${
                  isFinal ? 'text-violet-700' : 'text-slate-700'
                }`}
              >
                {formatScore(value)}
              </dd>
            </div>
          )
        })}
      </dl>

      {breakdown.matched_skills.length > 0 ? (
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
            Matched skills
          </p>
          <div className="flex flex-wrap gap-2">
            {breakdown.matched_skills.map((skill) => (
              <span
                key={skill}
                className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-800"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="border-t border-slate-200 pt-3">
        {canRequest ? (
          <button
            type="button"
            disabled={explanationLoading}
            onClick={() => void onRequestExplanation?.()}
            className="text-sm font-medium text-violet-700 hover:text-violet-900 disabled:cursor-not-allowed disabled:text-violet-400"
          >
            {explanationLoading ? 'Generating AI explanation…' : 'Get AI explanation'}
          </button>
        ) : null}

        {explanation ? (
          <div className="rounded-lg border border-violet-200 bg-violet-50/80 px-3 py-3">
            <p className="mb-1 text-xs font-medium uppercase tracking-wide text-violet-700">
              AI explanation
            </p>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
              {explanation}
            </p>
          </div>
        ) : null}

        {!canRequest && !explanation && explanationLoading ? (
          <p className="text-sm text-slate-500">Generating AI explanation…</p>
        ) : null}
      </div>
    </div>
  )
}
