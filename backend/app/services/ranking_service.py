from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.ranking_result import RankingResult
from app.schemas.ranking import RankRequest, RankResponse, RankedCandidateOut
from app.services.candidate_service import ingest_resume_bytes
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.embedding_service import EmbeddingService
from app.services.hybrid_scoring import compute_hybrid_breakdown
from app.services.job_description_service import get_job_description_or_404
from app.services.scoring_service import JobRequirements, extract_job_requirements
from app.services.similarity_service import compute_similarity
from app.utils.embed_text import build_job_description_embed_text


async def parse_rank_request(
    request: Request,
) -> tuple[RankRequest, list[tuple[str, bytes]]]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        jd_text = form.get("job_description_text")
        if not jd_text or not str(jd_text).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="job_description_text is required.",
            )

        candidate_ids_raw = form.get("candidate_ids", "[]")
        try:
            candidate_ids = json.loads(candidate_ids_raw) if candidate_ids_raw else []
            if not isinstance(candidate_ids, list):
                raise ValueError("candidate_ids must be a JSON array")
            candidate_ids = [int(value) for value in candidate_ids]
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="candidate_ids must be a JSON array of integers.",
            ) from exc

        jd_id_raw = form.get("job_description_id")
        job_description_id = int(jd_id_raw) if jd_id_raw not in (None, "") else None

        payload = RankRequest(
            job_description_text=str(jd_text),
            job_description_title=str(form.get("job_description_title") or "Untitled Role"),
            candidate_ids=candidate_ids,
            job_description_id=job_description_id,
        )

        new_resumes: list[tuple[str, bytes]] = []
        for key, value in form.multi_items():
            if key != "resume_files":
                continue
            if not isinstance(value, UploadFile):
                continue
            filename = value.filename or "resume.pdf"
            data = await value.read()
            new_resumes.append((filename, data))
        return payload, new_resumes

    body = await request.json()
    payload = RankRequest.model_validate(body)
    return payload, []


def rank_candidates(
    db: Session,
    embedding_service: EmbeddingService,
    embedding_cache: CandidateEmbeddingCache,
    payload: RankRequest,
    new_resumes: list[tuple[str, bytes]] | None = None,
) -> RankResponse:
    job_description, jd_requirements = _resolve_job_description(db, payload)
    candidate_ids = list(payload.candidate_ids)

    for filename, data in new_resumes or []:
        candidate = ingest_resume_bytes(db, filename, data, embedding_cache)
        candidate_ids.append(candidate.id)

    candidate_ids = list(dict.fromkeys(candidate_ids))
    if not candidate_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide candidate_ids and/or resume_files to rank.",
        )

    candidates = _load_candidates(db, candidate_ids)
    jd_embedding = embedding_service.embed_text(
        build_job_description_embed_text(job_description.title, job_description.text)
    )

    scored: list[tuple[Candidate, float, Any]] = []
    for candidate in candidates:
        candidate_embedding = embedding_cache.get_or_compute(db, candidate)
        semantic_score = compute_similarity(jd_embedding, candidate_embedding)
        breakdown = compute_hybrid_breakdown(
            {"parsed_fields": candidate.parsed_fields},
            jd_requirements,
            semantic_score,
        )
        scored.append((candidate, semantic_score, breakdown))

    scored.sort(key=lambda item: item[2].final_score, reverse=True)

    ranked_candidates: list[RankedCandidateOut] = []
    for rank, (candidate, semantic_score, breakdown) in enumerate(scored, start=1):
        ranking_result = RankingResult(
            job_description_id=job_description.id,
            candidate_id=candidate.id,
            semantic_score=semantic_score,
            rule_score=breakdown.rule_score,
            final_score=breakdown.final_score,
            breakdown=breakdown.model_dump(),
        )
        db.add(ranking_result)

        ranked_candidates.append(
            RankedCandidateOut(
                candidate_id=candidate.id,
                filename=candidate.filename,
                rank=rank,
                semantic_score=semantic_score,
                rule_score=breakdown.rule_score,
                final_score=breakdown.final_score,
                breakdown=breakdown,
            )
        )

    db.commit()

    return RankResponse(
        job_description_id=job_description.id,
        job_description_title=job_description.title,
        ranked_candidates=ranked_candidates,
    )


def _resolve_job_description(
    db: Session,
    payload: RankRequest,
) -> tuple[JobDescription, JobRequirements]:
    if payload.job_description_id is not None:
        job_description = get_job_description_or_404(db, payload.job_description_id)
        requirements = extract_job_requirements(job_description.text)
        return job_description, requirements

    job_description = JobDescription(
        title=payload.job_description_title.strip(),
        text=payload.job_description_text.strip(),
    )
    db.add(job_description)
    db.commit()
    db.refresh(job_description)
    requirements = extract_job_requirements(job_description.text)
    return job_description, requirements


def _load_candidates(db: Session, candidate_ids: list[int]) -> list[Candidate]:
    candidates = db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
    found_ids = {candidate.id for candidate in candidates}
    missing = [candidate_id for candidate_id in candidate_ids if candidate_id not in found_ids]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidates not found: {missing}",
        )
    order = {candidate_id: index for index, candidate_id in enumerate(candidate_ids)}
    return sorted(candidates, key=lambda candidate: order[candidate.id])
