from fastapi import APIRouter, Depends, File, UploadFile
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
def get_candidates(db: Session = Depends(get_db)) -> list[CandidateOut]:
    return list_candidates(db)
