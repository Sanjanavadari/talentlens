import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { RankedCandidate } from '../types'

interface ScoreChartProps {
  candidates: RankedCandidate[]
  maxItems?: number
}

function shortLabel(filename: string): string {
  return filename
    .replace(/\.pdf$/i, '')
    .replace(/^\d+_/, '')
    .split('_')
    .slice(0, 2)
    .join(' ')
}

export function ScoreChart({ candidates, maxItems = 5 }: ScoreChartProps) {
  const topCandidates = candidates.slice(0, maxItems)
  if (topCandidates.length === 0) {
    return null
  }

  const data = topCandidates.map((candidate) => ({
    name: shortLabel(candidate.filename),
    final: Number((candidate.final_score * 100).toFixed(1)),
    semantic: Number((candidate.semantic_score * 100).toFixed(1)),
    rule: Number((candidate.rule_score * 100).toFixed(1)),
  }))

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-900">Top candidates</h3>
        <p className="text-sm text-slate-500">
          Comparing final, semantic, and rule-based scores
        </p>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: '#64748b' }}
              interval={0}
              angle={-20}
              textAnchor="end"
              height={60}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              formatter={(value) => [`${value}%`, '']}
              contentStyle={{
                borderRadius: '12px',
                borderColor: '#e2e8f0',
              }}
            />
            <Legend />
            <Bar dataKey="final" name="Final" fill="#7c3aed" radius={[4, 4, 0, 0]} />
            <Bar dataKey="semantic" name="Semantic" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
            <Bar dataKey="rule" name="Rule" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
