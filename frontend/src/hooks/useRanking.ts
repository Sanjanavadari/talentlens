import { useCallback, useRef, useState } from 'react'

import {
  rankCandidates,
  submitJobDescription,
  uploadResumes,
} from '../services/api'
import type { Candidate, JobDescriptionCreate, RankResponse } from '../types'

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

interface LastRankParams {
  candidateIds: number[]
  jobDescriptionId: number
  jobDescription: JobDescriptionCreate
}

export function useRanking() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [rankResponse, setRankResponse] = useState<RankResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [explanationLoading, setExplanationLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const lastRankParamsRef = useRef<LastRankParams | null>(null)

  const reset = useCallback(() => {
    setCandidates([])
    setRankResponse(null)
    setError(null)
    lastRankParamsRef.current = null
  }, [])

  const runRanking = useCallback(
    async (files: File[], title: string, text: string) => {
      setLoading(true)
      setError(null)
      setRankResponse(null)
      lastRankParamsRef.current = null

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

        const jobDescriptionPayload = {
          title: trimmedTitle,
          text: trimmedText,
        }
        const candidateIds = uploaded.map((candidate) => candidate.id)

        const ranked = await rankCandidates(
          candidateIds,
          jobDescription.id,
          jobDescriptionPayload,
        )

        lastRankParamsRef.current = {
          candidateIds,
          jobDescriptionId: jobDescription.id,
          jobDescription: jobDescriptionPayload,
        }
        setRankResponse(ranked)
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const requestLlmExplanations = useCallback(async () => {
    const params = lastRankParamsRef.current
    if (!params) {
      throw new Error('Rank candidates first before requesting AI explanations.')
    }

    setExplanationLoading(true)
    setError(null)

    try {
      const ranked = await rankCandidates(
        params.candidateIds,
        params.jobDescriptionId,
        params.jobDescription,
        { includeLlmExplanation: true },
      )
      setRankResponse(ranked)
    } catch (err) {
      const message = getErrorMessage(err)
      setError(message)
      throw err
    } finally {
      setExplanationLoading(false)
    }
  }, [])

  return {
    candidates,
    rankResponse,
    loading,
    explanationLoading,
    error,
    runRanking,
    requestLlmExplanations,
    reset,
  }
}
