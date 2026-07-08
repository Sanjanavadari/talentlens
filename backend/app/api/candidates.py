from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import get_embedding_cache
from app.schemas.candidate import CandidateOut
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.candidate_service import list_candidates, upload_resumes

router = APIRouter()


@router.post("/upload", response_model=list[CandidateOut], status_code=201)
def upload_candidate_resumes(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    embedding_cache: CandidateEmbeddingCache = Depends(get_embedding_cache),
    settings: Settings = Depends(get_settings),
) -> list[CandidateOut]:
    return upload_resumes(db, files, embedding_cache, settings)


@router.get("", response_model=list[CandidateOut])
def get_candidates(
    skill: str | None = Query(
        default=None,
        description="Filter candidates whose parsed skills contain this value (case-insensitive).",
    ),
    min_experience_years: float | None = Query(
        default=None,
        ge=0,
        description="Minimum years of experience from parsed_fields.",
    ),
    search: str | None = Query(
        default=None,
        description="Substring match against filename or parsed resume text.",
    ),
    db: Session = Depends(get_db),
) -> list[CandidateOut]:
    return list_candidates(
        db,
        skill=skill,
        min_experience_years=min_experience_years,
        search=search,
    )
