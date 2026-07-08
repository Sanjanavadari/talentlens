from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token, get_user_by_id
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import CandidateVectorIndex

_bearer_scheme = HTTPBearer(auto_error=False)


def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service


def get_candidate_index(request: Request) -> CandidateVectorIndex:
    return request.app.state.candidate_index


def get_embedding_cache(request: Request) -> CandidateEmbeddingCache:
    return request.app.state.embedding_cache


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(credentials.credentials)
    return get_user_by_id(db, user_id)
