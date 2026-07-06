from collections.abc import Generator
from unittest.mock import MagicMock, patch

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
    """Isolated in-memory DB + mocked embeddings (no real model download)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Lifespan hydrates from SessionLocal — point it at the test DB, not talentlens.db.
    monkeypatch.setattr("app.main.EmbeddingService", MockEmbeddingService)
    monkeypatch.setattr("app.main.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.main.engine", engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

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


BREAKDOWN_KEYS = (
    "semantic_similarity_score",
    "matched_skills",
    "experience_score",
    "education_score",
    "certification_score",
    "recency_score",
    "skills_match_score",
    "rule_score",
    "final_score",
)


def test_ranking_api_round_trip(api_client: TestClient) -> None:
    """Integration: upload 2–3 resumes, submit JD, rank, assert sorted breakdowns."""
    uploaded_ids: list[int] = []
    for pdf_path in api_client.test_pdf_paths[:3]:
        with pdf_path.open("rb") as handle:
            response = api_client.post(
                "/api/v1/candidates/upload",
                files={"files": (pdf_path.name, handle, "application/pdf")},
            )
        assert response.status_code == 201, response.text
        uploaded_ids.append(response.json()[0]["id"])

    assert len(uploaded_ids) == 3

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
    assert [item["rank"] for item in payload["ranked_candidates"]] == [1, 2, 3]

    for item in payload["ranked_candidates"]:
        breakdown = item["breakdown"]
        for key in BREAKDOWN_KEYS:
            assert key in breakdown, f"missing breakdown field: {key}"

        assert isinstance(breakdown["matched_skills"], list)
        for score_key in BREAKDOWN_KEYS:
            if score_key == "matched_skills":
                continue
            assert 0.0 <= breakdown[score_key] <= 1.0

        assert breakdown["final_score"] == pytest.approx(
            0.7 * breakdown["semantic_similarity_score"] + 0.3 * breakdown["rule_score"],
            rel=1e-4,
        )
        assert item["final_score"] == breakdown["final_score"]
        assert item["semantic_score"] == breakdown["semantic_similarity_score"]
        assert item["rule_score"] == breakdown["rule_score"]

    top = payload["ranked_candidates"][0]
    assert "python" in top["breakdown"]["matched_skills"]
    assert top["filename"] == "backend_engineer.pdf"


@patch("app.services.ranking_service.generate_ranking_explanation")
def test_rank_without_llm_explanation_flag(
    mock_generate: MagicMock,
    api_client: TestClient,
) -> None:
    uploaded_ids = _upload_sample_candidates(api_client, count=2)
    jd_id = _create_jd(api_client)

    response = api_client.post(
        "/api/v1/rank",
        json={
            "job_description_text": BACKEND_JD["text"],
            "job_description_title": BACKEND_JD["title"],
            "candidate_ids": uploaded_ids,
            "job_description_id": jd_id,
        },
    )
    assert response.status_code == 200
    mock_generate.assert_not_called()

    for item in response.json()["ranked_candidates"]:
        assert item["breakdown"].get("llm_explanation") is None


@patch("app.services.ranking_service.generate_ranking_explanation")
def test_rank_with_llm_explanation_flag_populates_field(
    mock_generate: MagicMock,
    api_client: TestClient,
) -> None:
    mock_generate.return_value = (
        "Ranked #1 due to strong Python and FastAPI overlap with 6+ years of experience."
    )
    uploaded_ids = _upload_sample_candidates(api_client, count=2)
    jd_id = _create_jd(api_client)

    response = api_client.post(
        "/api/v1/rank?include_llm_explanation=true",
        json={
            "job_description_text": BACKEND_JD["text"],
            "job_description_title": BACKEND_JD["title"],
            "candidate_ids": uploaded_ids,
            "job_description_id": jd_id,
        },
    )
    assert response.status_code == 200
    assert mock_generate.call_count == 2

    for item in response.json()["ranked_candidates"]:
        assert item["breakdown"]["llm_explanation"] == mock_generate.return_value


@patch("app.services.ranking_service.generate_ranking_explanation")
def test_rank_with_llm_explanation_failure_returns_none(
    mock_generate: MagicMock,
    api_client: TestClient,
) -> None:
    mock_generate.return_value = None
    uploaded_ids = _upload_sample_candidates(api_client, count=2)
    jd_id = _create_jd(api_client)

    response = api_client.post(
        "/api/v1/rank?include_llm_explanation=true",
        json={
            "job_description_text": BACKEND_JD["text"],
            "job_description_title": BACKEND_JD["title"],
            "candidate_ids": uploaded_ids,
            "job_description_id": jd_id,
        },
    )
    assert response.status_code == 200

    for item in response.json()["ranked_candidates"]:
        assert item["breakdown"]["llm_explanation"] is None


def _upload_sample_candidates(api_client: TestClient, count: int) -> list[int]:
    uploaded_ids: list[int] = []
    for pdf_path in api_client.test_pdf_paths[:count]:
        with pdf_path.open("rb") as handle:
            response = api_client.post(
                "/api/v1/candidates/upload",
                files={"files": (pdf_path.name, handle, "application/pdf")},
            )
        assert response.status_code == 201
        uploaded_ids.append(response.json()[0]["id"])
    return uploaded_ids


def _create_jd(api_client: TestClient) -> int:
    response = api_client.post("/api/v1/job-descriptions", json=BACKEND_JD)
    assert response.status_code == 201
    return response.json()["id"]


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
