from app.models.candidate import Candidate
from app.services.candidate_service import list_candidates


def _add_candidate(
    db_session,
    *,
    filename: str,
    raw_text: str,
    skills: list[str],
    years: float,
) -> Candidate:
    candidate = Candidate(
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


def _seed_candidates(db_session) -> dict[str, Candidate]:
    return {
        "alice": _add_candidate(
            db_session,
            filename="alice_backend.pdf",
            raw_text="Alice builds FastAPI services with Python and Postgres.",
            skills=["python", "fastapi", "postgres"],
            years=5.0,
        ),
        "bob": _add_candidate(
            db_session,
            filename="bob_frontend.pdf",
            raw_text="Bob ships React dashboards and TypeScript UI kits.",
            skills=["react", "typescript", "css"],
            years=2.0,
        ),
        "cara": _add_candidate(
            db_session,
            filename="cara_ml_engineer.pdf",
            raw_text="Cara trains NLP models with Python and PyTorch.",
            skills=["python", "pytorch", "nlp"],
            years=7.0,
        ),
    }


def test_list_candidates_skill_filter(db_session) -> None:
    seeded = _seed_candidates(db_session)

    results = list_candidates(db_session, skill="python")
    ids = {candidate.id for candidate in results}

    assert ids == {seeded["alice"].id, seeded["cara"].id}


def test_list_candidates_skill_filter_case_insensitive(db_session) -> None:
    seeded = _seed_candidates(db_session)

    results = list_candidates(db_session, skill="ReAcT")
    assert [candidate.id for candidate in results] == [seeded["bob"].id]


def test_list_candidates_min_experience_years(db_session) -> None:
    seeded = _seed_candidates(db_session)

    results = list_candidates(db_session, min_experience_years=5)
    ids = {candidate.id for candidate in results}

    assert ids == {seeded["alice"].id, seeded["cara"].id}


def test_list_candidates_search_filename(db_session) -> None:
    seeded = _seed_candidates(db_session)

    results = list_candidates(db_session, search="frontend")
    assert [candidate.id for candidate in results] == [seeded["bob"].id]


def test_list_candidates_search_raw_text(db_session) -> None:
    seeded = _seed_candidates(db_session)

    results = list_candidates(db_session, search="FastAPI")
    assert [candidate.id for candidate in results] == [seeded["alice"].id]


def test_list_candidates_combined_filters(db_session) -> None:
    seeded = _seed_candidates(db_session)

    results = list_candidates(
        db_session,
        skill="python",
        min_experience_years=6,
        search="ml",
    )
    assert [candidate.id for candidate in results] == [seeded["cara"].id]


def test_list_candidates_combined_filters_no_match(db_session) -> None:
    _seed_candidates(db_session)

    results = list_candidates(
        db_session,
        skill="python",
        min_experience_years=10,
        search="backend",
    )
    assert results == []


def test_list_candidates_without_filters_returns_all(db_session) -> None:
    seeded = _seed_candidates(db_session)

    results = list_candidates(db_session)
    assert {candidate.id for candidate in results} == {
        seeded["alice"].id,
        seeded["bob"].id,
        seeded["cara"].id,
    }
