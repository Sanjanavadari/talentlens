from collections.abc import Generator

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.candidate import Candidate  # noqa: F401
from app.models.job_description import JobDescription  # noqa: F401
from app.models.ranking_result import RankingResult  # noqa: F401
from app.services.embedding_service import EmbeddingService
from tests.fixtures.generate_test_pdfs import generate_test_pdfs


class MockEmbeddingService:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.dimension = 8

    def embed_text(self, text: str) -> np.ndarray:
        return _embedding_for_text(text, self.dimension)


def _embedding_for_text(text: str, dimension: int = 8) -> np.ndarray:
    lowered = text.lower()
    if "backend" in lowered or "fastapi" in lowered or "python" in lowered:
        base = np.array([1.0, 0.8, 0.2, 0.0, 0.1, 0.0, 0.0, 0.0], dtype=np.float32)
    elif "machine learning" in lowered or "pytorch" in lowered:
        base = np.array([0.2, 1.0, 0.1, 0.0, 0.0, 0.2, 0.0, 0.0], dtype=np.float32)
    else:
        base = np.array([0.0, 0.2, 1.0, 0.1, 0.0, 0.0, 0.2, 0.0], dtype=np.float32)
    base = base[:dimension]
    if len(base) < dimension:
        base = np.pad(base, (0, dimension - len(base)))
    return base / np.linalg.norm(base)


@pytest.fixture
def api_client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr("app.main.EmbeddingService", MockEmbeddingService)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    mock_service = MockEmbeddingService("test-model")

    from app.services.candidate_embedding_cache import CandidateEmbeddingCache
    from app.services.similarity_service import CandidateVectorIndex

    candidate_index = CandidateVectorIndex(dimension=mock_service.dimension)
    embedding_cache = CandidateEmbeddingCache(mock_service, candidate_index)

    app.dependency_overrides[get_db] = override_get_db

    pdf_dir = tmp_path / "pdfs"
    generate_test_pdfs(pdf_dir)
    pdf_paths = [
        pdf_dir / "backend_engineer.pdf",
        pdf_dir / "ml_engineer.pdf",
        pdf_dir / "frontend_dev.pdf",
    ]

    with TestClient(app) as client:
        client.test_pdf_paths = pdf_paths
        yield client

    app.dependency_overrides.clear()


BACKEND_JD = {
    "title": "Backend Engineer",
    "text": """
Backend Engineer

Requirements:
5+ years of experience building backend services.
Must have Python, FastAPI, PostgreSQL, Docker, and AWS experience.
B.Tech or equivalent required.
""",
}


def test_ranking_api_round_trip(api_client: TestClient) -> None:
    uploaded_ids: list[int] = []
    for pdf_path in api_client.test_pdf_paths:
        with pdf_path.open("rb") as handle:
            response = api_client.post(
                "/api/v1/candidates/upload",
                files={"files": (pdf_path.name, handle, "application/pdf")},
            )
        assert response.status_code == 201, response.text
        uploaded_ids.append(response.json()[0]["id"])

    jd_response = api_client.post("/api/v1/job-descriptions", json=BACKEND_JD)
    assert jd_response.status_code == 201
    jd_id = jd_response.json()["id"]

    rank_response = api_client.post(
        "/api/v1/rank",
        json={
            "job_description_text": BACKEND_JD["text"],
            "job_description_title": BACKEND_JD["title"],
            "candidate_ids": uploaded_ids,
            "job_description_id": jd_id,
        },
    )
    assert rank_response.status_code == 200, rank_response.text
    payload = rank_response.json()

    assert payload["job_description_id"] == jd_id
    assert len(payload["ranked_candidates"]) == 3

    scores = [item["final_score"] for item in payload["ranked_candidates"]]
    assert scores == sorted(scores, reverse=True)

    for item in payload["ranked_candidates"]:
        breakdown = item["breakdown"]
        assert breakdown["semantic_similarity_score"] >= 0
        assert breakdown["experience_score"] >= 0
        assert breakdown["education_score"] >= 0
        assert breakdown["certification_score"] >= 0
        assert breakdown["recency_score"] >= 0
        assert breakdown["skills_match_score"] >= 0
        assert breakdown["rule_score"] >= 0
        assert breakdown["final_score"] == pytest.approx(
            0.7 * breakdown["semantic_similarity_score"] + 0.3 * breakdown["rule_score"],
            rel=1e-4,
        )
        assert item["rank"] >= 1

    top = payload["ranked_candidates"][0]
    assert "python" in top["breakdown"]["matched_skills"]


def test_list_endpoints(api_client: TestClient) -> None:
    with api_client.test_pdf_paths[0].open("rb") as handle:
        api_client.post(
            "/api/v1/candidates/upload",
            files={"files": (api_client.test_pdf_paths[0].name, handle, "application/pdf")},
        )

    candidates = api_client.get("/api/v1/candidates")
    assert candidates.status_code == 200
    assert len(candidates.json()) >= 1

    jd = api_client.post("/api/v1/job-descriptions", json=BACKEND_JD)
    listings = api_client.get("/api/v1/job-descriptions")
    assert listings.status_code == 200
    assert any(item["id"] == jd.json()["id"] for item in listings.json())
