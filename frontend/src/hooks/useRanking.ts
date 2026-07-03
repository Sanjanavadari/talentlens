import { useCallback, useState } from 'react'

import {
  rankCandidates,
  submitJobDescription,
  uploadResumes,
} from '../services/api'
import type { Candidate, RankResponse } from '../types'

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

export function useRanking() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [rankResponse, setRankResponse] = useState<RankResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reset = useCallback(() => {
    setCandidates([])
    setRankResponse(null)
    setError(null)
  }, [])

  const runRanking = useCallback(
    async (files: File[], title: string, text: string) => {
      setLoading(true)
      setError(null)
      setRankResponse(null)

      try {
        const trimmedTitle = title.trim()
        const trimmedText = text.trim()

        if (!trimmedTitle || !trimmedText) {
          throw new Error('Job title and description are required.')
        }
        if (files.length === 0) {
          throw new Error('Upload at least one resume PDF.')
        }

        const uploaded = await uploadResumes(files)
        setCandidates(uploaded)

        const jobDescription = await submitJobDescription({
          title: trimmedTitle,
          text: trimmedText,
        })

        const ranked = await rankCandidates(
          uploaded.map((candidate) => candidate.id),
          jobDescription.id,
          { title: trimmedTitle, text: trimmedText },
        )

        setRankResponse(ranked)
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  return {
    candidates,
    rankResponse,
    loading,
    error,
    runRanking,
    reset,
  }
}
