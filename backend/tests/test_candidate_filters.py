from app.models.candidate import Candidate
from app.models.user import User
from app.services.candidate_service import list_candidates
from tests.conftest import create_test_user


def _add_candidate(
    db_session,
    *,
    recruiter_id: int,
    filename: str,
    raw_text: str,
    skills: list[str],
    years: float,
) -> Candidate:
    candidate = Candidate(
        recruiter_id=recruiter_id,
        filename=filename,
        raw_text=raw_text,
        parsed_fields={
            "skills": skills,
            "years_of_experience": years,
            "education": [],
            "projects": [],
            "certifications": [],
            "recent_experience_end": None,
        },
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    return candidate


def _seed_candidates(db_session, recruiter_id: int) -> dict[str, Candidate]:
    return {
        "alice": _add_candidate(
            db_session,
            recruiter_id=recruiter_id,
            filename="alice_backend.pdf",
            raw_text="Alice builds FastAPI services with Python and Postgres.",
            skills=["python", "fastapi", "postgres"],
            years=5.0,
        ),
        "bob": _add_candidate(
            db_session,
            recruiter_id=recruiter_id,
            filename="bob_frontend.pdf",
            raw_text="Bob ships React dashboards and TypeScript UI kits.",
            skills=["react", "typescript", "css"],
            years=2.0,
        ),
        "cara": _add_candidate(
            db_session,
            recruiter_id=recruiter_id,
            filename="cara_ml_engineer.pdf",
            raw_text="Cara trains NLP models with Python and PyTorch.",
            skills=["python", "pytorch", "nlp"],
            years=7.0,
        ),
    }


def test_list_candidates_skill_filter(db_session) -> None:
    user = create_test_user(db_session)
    seeded = _seed_candidates(db_session, user.id)

    results = list_candidates(db_session, user.id, skill="python")
    ids = {candidate.id for candidate in results}

    assert ids == {seeded["alice"].id, seeded["cara"].id}


def test_list_candidates_skill_filter_case_insensitive(db_session) -> None:
    user = create_test_user(db_session)
    seeded = _seed_candidates(db_session, user.id)

    results = list_candidates(db_session, user.id, skill="ReAcT")
    assert [candidate.id for candidate in results] == [seeded["bob"].id]


def test_list_candidates_min_experience_years(db_session) -> None:
    user = create_test_user(db_session)
    seeded = _seed_candidates(db_session, user.id)

    results = list_candidates(db_session, user.id, min_experience_years=5)
    ids = {candidate.id for candidate in results}

    assert ids == {seeded["alice"].id, seeded["cara"].id}


def test_list_candidates_search_filename(db_session) -> None:
    user = create_test_user(db_session)
    seeded = _seed_candidates(db_session, user.id)

    results = list_candidates(db_session, user.id, search="frontend")
    assert [candidate.id for candidate in results] == [seeded["bob"].id]


def test_list_candidates_search_raw_text(db_session) -> None:
    user = create_test_user(db_session)
    seeded = _seed_candidates(db_session, user.id)

    results = list_candidates(db_session, user.id, search="FastAPI")
    assert [candidate.id for candidate in results] == [seeded["alice"].id]


def test_list_candidates_combined_filters(db_session) -> None:
    user = create_test_user(db_session)
    seeded = _seed_candidates(db_session, user.id)

    results = list_candidates(
        db_session,
        user.id,
        skill="python",
        min_experience_years=6,
        search="ml",
    )
    assert [candidate.id for candidate in results] == [seeded["cara"].id]


def test_list_candidates_combined_filters_no_match(db_session) -> None:
    user = create_test_user(db_session)
    _seed_candidates(db_session, user.id)

    results = list_candidates(
        db_session,
        user.id,
        skill="python",
        min_experience_years=10,
        search="backend",
    )
    assert results == []


def test_list_candidates_without_filters_returns_all(db_session) -> None:
    user = create_test_user(db_session)
    seeded = _seed_candidates(db_session, user.id)

    results = list_candidates(db_session, user.id)
    assert {candidate.id for candidate in results} == {
        seeded["alice"].id,
        seeded["bob"].id,
        seeded["cara"].id,
    }


def test_list_candidates_scoped_to_recruiter(db_session) -> None:
    owner = create_test_user(db_session, email="owner@example.com")
    other = create_test_user(db_session, email="other@example.com")
    _seed_candidates(db_session, owner.id)
    _add_candidate(
        db_session,
        recruiter_id=other.id,
        filename="other_only.pdf",
        raw_text="Other recruiter candidate",
        skills=["go"],
        years=1.0,
    )

    results = list_candidates(db_session, owner.id)
    assert all(item.filename != "other_only.pdf" for item in results)
    assert len(results) == 3
