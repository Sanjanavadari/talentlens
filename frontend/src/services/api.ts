import axios from 'axios'

import type {
  Candidate,
  CandidateNote,
  CandidateNoteCreate,
  CandidateNoteUpdate,
  JobDescription,
  JobDescriptionCreate,
  RankResponse,
} from '../types'

const baseURL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8002/api/v1'

export const api = axios.create({
  baseURL,
  headers: {
    Accept: 'application/json',
  },
})

export async function uploadResumes(files: File[]): Promise<Candidate[]> {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }

  const response = await api.post<Candidate[]>('/candidates/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function submitJobDescription(
  jd: JobDescriptionCreate,
): Promise<JobDescription> {
  const response = await api.post<JobDescription>('/job-descriptions', jd)
  return response.data
}

export async function rankCandidates(
  candidateIds: number[],
  jobDescriptionId: number,
  jobDescription: JobDescriptionCreate,
  options?: { includeLlmExplanation?: boolean },
): Promise<RankResponse> {
  const response = await api.post<RankResponse>(
    '/rank',
    {
      candidate_ids: candidateIds,
      job_description_id: jobDescriptionId,
      job_description_text: jobDescription.text,
      job_description_title: jobDescription.title,
    },
    {
      params: {
        include_llm_explanation: options?.includeLlmExplanation ?? false,
      },
    },
  )
  return response.data
}

export interface ListCandidatesParams {
  skill?: string
  minExperienceYears?: number
  search?: string
}

export async function listCandidates(
  params?: ListCandidatesParams,
): Promise<Candidate[]> {
  const response = await api.get<Candidate[]>('/candidates', {
    params: {
      skill: params?.skill || undefined,
      min_experience_years: params?.minExperienceYears,
      search: params?.search || undefined,
    },
  })
  return response.data
}

export async function getNotes(candidateId: number): Promise<CandidateNote[]> {
  const response = await api.get<CandidateNote[]>(
    `/candidates/${candidateId}/notes`,
  )
  return response.data
}

export async function createNote(
  candidateId: number,
  payload: CandidateNoteCreate,
): Promise<CandidateNote> {
  const response = await api.post<CandidateNote>(
    `/candidates/${candidateId}/notes`,
    payload,
  )
  return response.data
}

export async function updateNote(
  noteId: number,
  payload: CandidateNoteUpdate,
): Promise<CandidateNote> {
  const response = await api.patch<CandidateNote>(
    `/candidate_notes/${noteId}`,
    payload,
  )
  return response.data
}

export async function deleteNote(noteId: number): Promise<void> {
  await api.delete(`/candidate_notes/${noteId}`)
}
