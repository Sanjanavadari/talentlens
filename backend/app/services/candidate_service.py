from __future__ import annotations

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateOut
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.info_extractor import extract_structured_fields
from app.services.resume_parser import extract_text_from_pdf_bytes


def _candidate_has_skill(parsed_fields: dict, skill: str) -> bool:
    needle = skill.strip().lower()
    if not needle:
        return True
    skills = parsed_fields.get("skills") or []
    return any(needle in str(item).lower() for item in skills)


def _candidate_years(parsed_fields: dict) -> float:
    try:
        return float(parsed_fields.get("years_of_experience") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def list_candidates(
    db: Session,
    recruiter_id: int,
    *,
    skill: str | None = None,
    min_experience_years: float | None = None,
    search: str | None = None,
) -> list[CandidateOut]:
    query = db.query(Candidate).filter(Candidate.recruiter_id == recruiter_id)

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Candidate.filename.ilike(pattern),
                Candidate.raw_text.ilike(pattern),
            )
        )

    candidates = query.order_by(Candidate.created_at.desc()).all()

    if skill and skill.strip():
        candidates = [
            candidate
            for candidate in candidates
            if _candidate_has_skill(candidate.parsed_fields or {}, skill)
        ]

    if min_experience_years is not None:
        candidates = [
            candidate
            for candidate in candidates
            if _candidate_years(candidate.parsed_fields or {}) >= min_experience_years
        ]

    return [CandidateOut.model_validate(candidate) for candidate in candidates]


def upload_resumes(
    db: Session,
    recruiter_id: int,
    files: list[UploadFile],
    embedding_cache: CandidateEmbeddingCache,
    settings: Settings | None = None,
) -> list[CandidateOut]:
    settings = settings or get_settings()
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one resume file is required.",
        )
    if len(files) > settings.max_resumes_per_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.max_resumes_per_request} resumes per request.",
        )

    created: list[CandidateOut] = []
    for upload in files:
        filename = upload.filename or "resume.pdf"
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only PDF resumes are supported: {filename}",
            )

        data = upload.file.read()
        if len(data) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds upload limit: {filename}",
            )
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Empty file: {filename}",
            )

        raw_text = extract_text_from_pdf_bytes(data)
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not extract text from PDF: {filename}",
            )

        parsed_fields = extract_structured_fields(raw_text)
        candidate = Candidate(
            recruiter_id=recruiter_id,
            filename=filename,
            raw_text=raw_text,
            parsed_fields=parsed_fields,
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        embedding_cache.get_or_compute(db, candidate)
        created.append(CandidateOut.model_validate(candidate))

    return created


def ingest_resume_bytes(
    db: Session,
    recruiter_id: int,
    filename: str,
    data: bytes,
    embedding_cache: CandidateEmbeddingCache,
    settings: Settings | None = None,
) -> Candidate:
    settings = settings or get_settings()
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF resumes are supported: {filename}",
        )
    if len(data) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds upload limit: {filename}",
        )

    raw_text = extract_text_from_pdf_bytes(data)
    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not extract text from PDF: {filename}",
        )

    parsed_fields = extract_structured_fields(raw_text)
    candidate = Candidate(
        recruiter_id=recruiter_id,
        filename=filename,
        raw_text=raw_text,
        parsed_fields=parsed_fields,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    embedding_cache.get_or_compute(db, candidate)
    return candidate


def get_candidate_for_recruiter_or_404(
    db: Session,
    candidate_id: int,
    recruiter_id: int,
) -> Candidate:
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id, Candidate.recruiter_id == recruiter_id)
        .first()
    )
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found.",
        )
    return candidate
