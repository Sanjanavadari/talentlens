from __future__ import annotations

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateOut
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.info_extractor import extract_structured_fields
from app.services.resume_parser import extract_text_from_pdf_bytes


def list_candidates(db: Session) -> list[CandidateOut]:
    candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    return [CandidateOut.model_validate(candidate) for candidate in candidates]


def upload_resumes(
    db: Session,
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
        filename=filename,
        raw_text=raw_text,
        parsed_fields=parsed_fields,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    embedding_cache.get_or_compute(db, candidate)
    return candidate
