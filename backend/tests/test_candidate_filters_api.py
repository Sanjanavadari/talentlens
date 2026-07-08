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
from app.models.candidate_note import CandidateNote  # noqa: F401
from app.models.job_description import JobDescription  # noqa: F401
from app.models.ranking_result import RankingResult  # noqa: F401


class MockEmbeddingService:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.dimension = 8

    def embed_text(self, text: str) -> np.ndarray:
        vector = np.ones(self.dimension, dtype=np.float32)
        return vector / np.linalg.norm(vector)


@pytest.fixture
def filter_api_client(monkeypatch) -> Generator[TestClient, None, None]:
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

    monkeypatch.setattr("app.main.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.main.engine", engine)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        db = TestingSessionLocal()
        db.add_all(
            [
                Candidate(
                    filename="alice_backend.pdf",
                    raw_text="Alice builds FastAPI services with Python.",
                    parsed_fields={
                        "skills": ["python", "fastapi"],
                        "years_of_experience": 5.0,
                    },
                ),
                Candidate(
                    filename="bob_frontend.pdf",
                    raw_text="Bob ships React dashboards.",
                    parsed_fields={
                        "skills": ["react", "typescript"],
                        "years_of_experience": 2.0,
                    },
                ),
                Candidate(
                    filename="cara_ml_engineer.pdf",
                    raw_text="Cara trains NLP models with Python.",
                    parsed_fields={
                        "skills": ["python", "pytorch"],
                        "years_of_experience": 7.0,
                    },
                ),
            ]
        )
        db.commit()
        db.close()
        yield client

    app.dependency_overrides.clear()


def test_get_candidates_skill_query_param(filter_api_client: TestClient) -> None:
    response = filter_api_client.get("/api/v1/candidates", params={"skill": "python"})
    assert response.status_code == 200
    filenames = {item["filename"] for item in response.json()}
    assert filenames == {"alice_backend.pdf", "cara_ml_engineer.pdf"}


def test_get_candidates_min_experience_query_param(
    filter_api_client: TestClient,
) -> None:
    response = filter_api_client.get(
        "/api/v1/candidates",
        params={"min_experience_years": 5},
    )
    assert response.status_code == 200
    filenames = {item["filename"] for item in response.json()}
    assert filenames == {"alice_backend.pdf", "cara_ml_engineer.pdf"}


def test_get_candidates_search_query_param(filter_api_client: TestClient) -> None:
    response = filter_api_client.get(
        "/api/v1/candidates",
        params={"search": "frontend"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["filename"] == "bob_frontend.pdf"


def test_get_candidates_combined_query_params(filter_api_client: TestClient) -> None:
    response = filter_api_client.get(
        "/api/v1/candidates",
        params={
            "skill": "python",
            "min_experience_years": 6,
            "search": "ml",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["filename"] == "cara_ml_engineer.pdf"
