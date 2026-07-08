export interface ParsedFields {
  skills: string[]
  years_of_experience: number
  education: string[]
  projects: string[]
  certifications: string[]
  recent_experience_end: string | null
}

export interface Candidate {
  id: number
  filename: string
  raw_text: string
  parsed_fields: ParsedFields | Record<string, unknown>
  created_at: string
}

export interface JobDescriptionCreate {
  title: string
  text: string
}

export interface JobDescription {
  id: number
  title: string
  text: string
  created_at: string
}

export interface ScoreBreakdown {
  semantic_similarity_score: number
  matched_skills: string[]
  experience_score: number
  education_score: number
  certification_score: number
  recency_score: number
  skills_match_score: number
  rule_score: number
  final_score: number
  llm_explanation?: string | null
}

export interface CandidateNote {
  id: number
  candidate_id: number
  note_text: string
  created_at: string
  updated_at: string
}

export interface CandidateNoteCreate {
  note_text: string
}

export interface CandidateNoteUpdate {
  note_text: string
}

export interface RankedCandidate {
  candidate_id: number
  filename: string
  rank: number
  semantic_score: number
  rule_score: number
  final_score: number
  breakdown: ScoreBreakdown
}

export interface RankResponse {
  job_description_id: number
  job_description_title: string
  ranked_candidates: RankedCandidate[]
}

export interface User {
  id: number
  email: string
  created_at: string
}

export interface AuthTokenResponse {
  access_token: string
  token_type: string
}
