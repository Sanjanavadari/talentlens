"""Persist and cache candidate embeddings to avoid re-embedding on re-rank."""

from __future__ import annotations

import hashlib

import numpy as np
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import CandidateVectorIndex
from app.utils.embed_text import build_candidate_embed_text


def _hash_embed_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class CandidateEmbeddingCache:
    """DB-backed embedding storage with an in-memory FAISS index mirror."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_index: CandidateVectorIndex,
    ) -> None:
        self._embedding_service = embedding_service
        self._vector_index = vector_index

    def embed_text_for_candidate(self, parsed_fields: dict, raw_text: str) -> str:
        return build_candidate_embed_text(parsed_fields, raw_text)

    def get_or_compute(
        self,
        db: Session,
        candidate: Candidate,
        *,
        force: bool = False,
    ) -> np.ndarray:
        embed_text = self.embed_text_for_candidate(candidate.parsed_fields, candidate.raw_text)
        text_hash = _hash_embed_text(embed_text)

        if (
            not force
            and candidate.embedding is not None
            and candidate.embedding_text_hash == text_hash
            and candidate.embedding_model == self._embedding_service.model_name
        ):
            vector = np.asarray(candidate.embedding, dtype=np.float32)
            self._vector_index.upsert(candidate.id, vector)
            return vector

        vector = self._embedding_service.embed_text(embed_text)
        candidate.embedding = vector.tolist()
        candidate.embedding_text_hash = text_hash
        candidate.embedding_model = self._embedding_service.model_name
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        self._vector_index.upsert(candidate.id, vector)
        return vector

    def hydrate_index_from_db(self, db: Session) -> int:
        candidates = (
            db.query(Candidate)
            .filter(
                Candidate.embedding.isnot(None),
                Candidate.embedding_model == self._embedding_service.model_name,
            )
            .all()
        )
        entries: list[tuple[int, np.ndarray]] = []
        for candidate in candidates:
            vector = np.asarray(candidate.embedding, dtype=np.float32)
            if vector.shape[-1] != self._vector_index.dimension:
                continue
            entries.append((candidate.id, vector))
        self._vector_index.rebuild(entries)
        return len(entries)
