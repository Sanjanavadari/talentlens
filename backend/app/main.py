from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.exceptions import register_exception_handlers
from app.api import auth, candidate_notes, candidates, job_descriptions, ranking
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import CandidateVectorIndex
from app.schemas.errors import ErrorResponse
import app.models  # noqa: F401 — register ORM models with Base.metadata

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    # Embedding model loads lazily on first rank/upload — not here — so startup
    # stays within low-memory limits and /health can respond before torch loads.
    embedding_service = EmbeddingService(
        settings.embedding_model_name,
        expected_dimension=settings.embedding_dimension,
    )
    candidate_index = CandidateVectorIndex(embedding_service.dimension)
    embedding_cache = CandidateEmbeddingCache(embedding_service, candidate_index)

    with SessionLocal() as db:
        hydrated = embedding_cache.hydrate_index_from_db(db)

    app.state.embedding_service = embedding_service
    app.state.candidate_index = candidate_index
    app.state.embedding_cache = embedding_cache
    app.state.hydrated_candidate_count = hydrated

    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        payload = ErrorResponse(
            detail="Database unavailable.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)

    return {"status": "ok", "database": "connected"}


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["candidates"])
app.include_router(
    candidate_notes.candidate_scoped_router,
    prefix="/api/v1/candidates",
    tags=["candidate-notes"],
)
app.include_router(
    candidate_notes.note_scoped_router,
    prefix="/api/v1/candidate_notes",
    tags=["candidate-notes"],
)
app.include_router(
    job_descriptions.router,
    prefix="/api/v1/job-descriptions",
    tags=["job-descriptions"],
)
app.include_router(ranking.router, prefix="/api/v1", tags=["ranking"])
