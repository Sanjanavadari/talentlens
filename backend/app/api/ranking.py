from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_embedding_cache, get_embedding_service
from app.schemas.ranking import RankResponse
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.embedding_service import EmbeddingService
from app.services.ranking_service import parse_rank_request, rank_candidates

router = APIRouter()


@router.post("/rank", response_model=RankResponse)
async def post_rank(
    request: Request,
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    embedding_cache: CandidateEmbeddingCache = Depends(get_embedding_cache),
) -> RankResponse:
    payload, new_resumes = await parse_rank_request(request)
    return rank_candidates(
        db=db,
        embedding_service=embedding_service,
        embedding_cache=embedding_cache,
        payload=payload,
        new_resumes=new_resumes,
    )
