from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ParsedFields(BaseModel):
    skills: list[str] = Field(default_factory=list)
    years_of_experience: float = 0.0
    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    recent_experience_end: str | None = None


class CandidateCreate(BaseModel):
    filename: str
    raw_text: str
    parsed_fields: ParsedFields | dict[str, Any] = Field(default_factory=dict)


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    raw_text: str
    parsed_fields: dict[str, Any]
    created_at: datetime
