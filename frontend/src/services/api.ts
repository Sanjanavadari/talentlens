import axios from 'axios'

import type {
  Candidate,
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
): Promise<RankResponse> {
  const response = await api.post<RankResponse>('/rank', {
    candidate_ids: candidateIds,
    job_description_id: jobDescriptionId,
    job_description_text: jobDescription.text,
    job_description_title: jobDescription.title,
  })
  return response.data
}

export async function listCandidates(): Promise<Candidate[]> {
  const response = await api.get<Candidate[]>('/candidates')
  return response.data
}
