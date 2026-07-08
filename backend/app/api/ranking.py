from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, get_embedding_cache, get_embedding_service
from app.models.user import User
from app.schemas.ranking import RankResponse
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.embedding_service import EmbeddingService
from app.services.ranking_service import parse_rank_request, rank_candidates

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/rank", response_model=RankResponse)
async def post_rank(
    request: Request,
    include_llm_explanation: bool = False,
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    embedding_cache: CandidateEmbeddingCache = Depends(get_embedding_cache),
    current_user: User = Depends(get_current_user),
) -> RankResponse:
    payload, new_resumes = await parse_rank_request(request)
    return rank_candidates(
        db=db,
        recruiter_id=current_user.id,
        embedding_service=embedding_service,
        embedding_cache=embedding_cache,
        payload=payload,
        new_resumes=new_resumes,
        include_llm_explanation=include_llm_explanation,
    )
