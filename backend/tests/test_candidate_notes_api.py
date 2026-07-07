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
def notes_api_client(monkeypatch) -> Generator[TestClient, None, None]:
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
        candidate = Candidate(
            filename="backend_engineer.pdf",
            raw_text="Python FastAPI experience",
            parsed_fields={"skills": ["python", "fastapi"]},
        )
        db = TestingSessionLocal()
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        client.candidate_id = candidate.id
        db.close()
        yield client

    app.dependency_overrides.clear()


def test_create_note_endpoint(notes_api_client: TestClient) -> None:
    response = notes_api_client.post(
        f"/api/v1/candidates/{notes_api_client.candidate_id}/notes",
        json={"note_text": "Promising backend candidate."},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["candidate_id"] == notes_api_client.candidate_id
    assert payload["note_text"] == "Promising backend candidate."


def test_create_note_nonexistent_candidate(notes_api_client: TestClient) -> None:
    response = notes_api_client.post(
        "/api/v1/candidates/99999/notes",
        json={"note_text": "Should fail."},
    )
    assert response.status_code == 404


def test_list_notes_endpoint(notes_api_client: TestClient) -> None:
    candidate_id = notes_api_client.candidate_id
    notes_api_client.post(
        f"/api/v1/candidates/{candidate_id}/notes",
        json={"note_text": "Note A"},
    )
    notes_api_client.post(
        f"/api/v1/candidates/{candidate_id}/notes",
        json={"note_text": "Note B"},
    )

    response = notes_api_client.get(f"/api/v1/candidates/{candidate_id}/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 2
    assert {note["note_text"] for note in notes} == {"Note A", "Note B"}


def test_list_notes_nonexistent_candidate(notes_api_client: TestClient) -> None:
    response = notes_api_client.get("/api/v1/candidates/99999/notes")
    assert response.status_code == 404


def test_update_note_endpoint(notes_api_client: TestClient) -> None:
    candidate_id = notes_api_client.candidate_id
    created = notes_api_client.post(
        f"/api/v1/candidates/{candidate_id}/notes",
        json={"note_text": "Original"},
    ).json()

    response = notes_api_client.patch(
        f"/api/v1/candidate_notes/{created['id']}",
        json={"note_text": "Edited note"},
    )
    assert response.status_code == 200
    assert response.json()["note_text"] == "Edited note"


def test_delete_note_endpoint(notes_api_client: TestClient) -> None:
    candidate_id = notes_api_client.candidate_id
    created = notes_api_client.post(
        f"/api/v1/candidates/{candidate_id}/notes",
        json={"note_text": "Delete me"},
    ).json()

    response = notes_api_client.delete(f"/api/v1/candidate_notes/{created['id']}")
    assert response.status_code == 204

    listed = notes_api_client.get(f"/api/v1/candidates/{candidate_id}/notes").json()
    assert listed == []


def test_update_note_not_found(notes_api_client: TestClient) -> None:
    response = notes_api_client.patch(
        "/api/v1/candidate_notes/99999",
        json={"note_text": "Missing"},
    )
    assert response.status_code == 404


def test_delete_note_not_found(notes_api_client: TestClient) -> None:
    response = notes_api_client.delete("/api/v1/candidate_notes/99999")
    assert response.status_code == 404
