from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CandidateNoteCreate(BaseModel):
    note_text: str = Field(..., min_length=1)


class CandidateNoteUpdate(BaseModel):
    note_text: str = Field(..., min_length=1)


class CandidateNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    note_text: str
    created_at: datetime
    updated_at: datetime
