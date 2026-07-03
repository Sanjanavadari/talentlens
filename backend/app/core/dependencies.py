from fastapi import Request

from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import CandidateVectorIndex


def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service


def get_candidate_index(request: Request) -> CandidateVectorIndex:
    return request.app.state.candidate_index


def get_embedding_cache(request: Request) -> CandidateEmbeddingCache:
    return request.app.state.embedding_cache
