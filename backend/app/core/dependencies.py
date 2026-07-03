from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db as _get_db
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import CandidateVectorIndex


def get_db() -> Generator[Session, None, None]:
    yield from _get_db()


def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service


def get_candidate_index(request: Request) -> CandidateVectorIndex:
    return request.app.state.candidate_index


def get_embedding_cache(request: Request) -> CandidateEmbeddingCache:
    return request.app.state.embedding_cache
