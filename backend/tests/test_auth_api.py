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
from app.models.user import User  # noqa: F401


class MockEmbeddingService:
    def __init__(self, model_name: str, **_: object) -> None:
        self.model_name = model_name
        self.dimension = 8

    def embed_text(self, text: str) -> np.ndarray:
        vector = np.ones(self.dimension, dtype=np.float32)
        return vector / np.linalg.norm(vector)


@pytest.fixture
def auth_api_client(monkeypatch) -> Generator[TestClient, None, None]:
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
        yield client

    app.dependency_overrides.clear()


def test_register_login_and_me(auth_api_client: TestClient) -> None:
    register = auth_api_client.post(
        "/api/v1/auth/register",
        json={"email": "auth-user@example.com", "password": "securepass123"},
    )
    assert register.status_code == 201
    assert register.json()["email"] == "auth-user@example.com"

    login = auth_api_client.post(
        "/api/v1/auth/login",
        json={"email": "auth-user@example.com", "password": "securepass123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token

    me = auth_api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "auth-user@example.com"


def test_login_invalid_password(auth_api_client: TestClient) -> None:
    auth_api_client.post(
        "/api/v1/auth/register",
        json={"email": "bad-login@example.com", "password": "securepass123"},
    )
    response = auth_api_client.post(
        "/api/v1/auth/login",
        json={"email": "bad-login@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password"


def test_login_unknown_user(auth_api_client: TestClient) -> None:
    response = auth_api_client.post(
        "/api/v1/auth/login",
        json={"email": "missing-user@example.com", "password": "securepass123"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_me_requires_auth(auth_api_client: TestClient) -> None:
    assert auth_api_client.get("/api/v1/auth/me").status_code == 401
