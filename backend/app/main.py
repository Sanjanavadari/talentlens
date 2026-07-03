from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.api import candidates, job_descriptions, ranking
from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import CandidateVectorIndex
import app.models  # noqa: F401 — register ORM models with Base.metadata

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    embedding_service = EmbeddingService(settings.embedding_model_name)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["candidates"])
app.include_router(
    job_descriptions.router,
    prefix="/api/v1/job-descriptions",
    tags=["job-descriptions"],
)
app.include_router(ranking.router, prefix="/api/v1", tags=["ranking"])
