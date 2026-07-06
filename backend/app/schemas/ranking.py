from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScoreBreakdown(BaseModel):
    semantic_similarity_score: float
    matched_skills: list[str] = Field(default_factory=list)
    experience_score: float
    education_score: float
    certification_score: float
    recency_score: float
    skills_match_score: float
    rule_score: float
    final_score: float
    llm_explanation: str | None = None


class RankRequest(BaseModel):
    job_description_text: str = Field(..., min_length=1)
    job_description_title: str = Field(default="Untitled Role", max_length=256)
    candidate_ids: list[int] = Field(default_factory=list)
    job_description_id: int | None = None


class RankedCandidateOut(BaseModel):
    candidate_id: int
    filename: str
    rank: int
    semantic_score: float
    rule_score: float
    final_score: float
    breakdown: ScoreBreakdown


class RankResponse(BaseModel):
    job_description_id: int
    job_description_title: str
    ranked_candidates: list[RankedCandidateOut]


class RankingResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_description_id: int
    candidate_id: int
    semantic_score: float
    rule_score: float
    final_score: float
    breakdown: dict
    created_at: datetime
