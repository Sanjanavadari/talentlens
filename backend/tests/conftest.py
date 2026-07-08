import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models.candidate import Candidate  # noqa: F401 — register model
from app.models.candidate_note import CandidateNote  # noqa: F401 — register model
from app.models.job_description import JobDescription  # noqa: F401 — register model
from app.models.ranking_result import RankingResult  # noqa: F401 — register model
from app.models.user import User  # noqa: F401 — register model
from app.services.auth_service import hash_password


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_test_user(
    db: Session,
    *,
    email: str = "recruiter@example.com",
    password: str = "testpass123",
) -> User:
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register_and_login(
    client: TestClient,
    *,
    email: str = "recruiter@example.com",
    password: str = "testpass123",
) -> dict[str, str]:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    if register_response.status_code not in (201, 400):
        assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def auth_headers(
    client: TestClient,
    *,
    email: str = "recruiter@example.com",
    password: str = "testpass123",
) -> dict[str, str]:
    return register_and_login(client, email=email, password=password)
