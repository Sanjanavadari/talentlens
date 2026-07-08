from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app
from app.models.candidate import Candidate  # noqa: F401
from app.models.candidate_note import CandidateNote  # noqa: F401
from app.models.job_description import JobDescription  # noqa: F401
from app.models.ranking_result import RankingResult  # noqa: F401
from app.models.user import User  # noqa: F401
from tests.conftest import auth_headers


@pytest.fixture
def deployment_client(monkeypatch) -> Generator[TestClient, None, None]:
    import numpy as np

    class MockEmbeddingService:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name
            self.dimension = 8

        def embed_text(self, text: str) -> np.ndarray:
            vector = np.ones(self.dimension, dtype=np.float32)
            return vector / np.linalg.norm(vector)

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

    with TestClient(app, raise_server_exceptions=False) as client:
        client.auth_headers = auth_headers(client, email="deploy@example.com")
        yield client

    app.dependency_overrides.clear()


def test_health_reports_database_connected(deployment_client: TestClient) -> None:
    response = deployment_client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "connected"


def test_health_returns_503_when_database_unavailable(
    deployment_client: TestClient,
    monkeypatch,
) -> None:
    class BrokenSession:
        def __enter__(self):
            raise RuntimeError("database down")

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr("app.main.SessionLocal", lambda: BrokenSession())
    response = deployment_client.get("/health")
    assert response.status_code == 503
    payload = response.json()
    assert payload["detail"] == "Database unavailable."
    assert payload["status_code"] == 503


def test_upload_rejects_non_pdf_extension(deployment_client: TestClient) -> None:
    response = deployment_client.post(
        "/api/v1/candidates/upload",
        files={"files": ("resume.txt", b"not a pdf", "text/plain")},
        headers=deployment_client.auth_headers,
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["status_code"] == 400
    assert "Only PDF resumes are supported" in payload["detail"]


def test_upload_rejects_invalid_pdf_bytes(deployment_client: TestClient) -> None:
    response = deployment_client.post(
        "/api/v1/candidates/upload",
        files={"files": ("resume.pdf", b"not-really-pdf", "application/pdf")},
        headers=deployment_client.auth_headers,
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["status_code"] == 400
    assert "not a valid PDF" in payload["detail"]


def test_upload_rejects_too_many_files(deployment_client: TestClient, monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "max_resumes_per_request", 1)

    files = [
        ("files", ("a.pdf", b"%PDF-1.4 fake", "application/pdf")),
        ("files", ("b.pdf", b"%PDF-1.4 fake", "application/pdf")),
    ]
    response = deployment_client.post(
        "/api/v1/candidates/upload",
        files=files,
        headers=deployment_client.auth_headers,
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["status_code"] == 400
    assert "Maximum 1 resumes per request" in payload["detail"]


def test_http_exception_uses_consistent_error_shape(deployment_client: TestClient) -> None:
    response = deployment_client.get("/api/v1/candidates")
    assert response.status_code == 401
    payload = response.json()
    assert payload["status_code"] == 401
    assert "detail" in payload


def test_cors_origins_parses_comma_separated(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example.com,https://b.example.com")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.cors_origin_list == [
        "https://a.example.com",
        "https://b.example.com",
    ]
    assert settings.cors_allow_credentials is True
    get_settings.cache_clear()
