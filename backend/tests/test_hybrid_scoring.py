"""Unit tests for hybrid semantic + rule scoring."""

import pytest

from app.schemas.ranking import ScoreBreakdown
from app.services.hybrid_scoring import (
    RULE_WEIGHT,
    SEMANTIC_WEIGHT,
    compute_final_score,
    compute_hybrid_breakdown,
)
from app.services.scoring_service import extract_job_requirements

MOCK_CANDIDATE = {
    "parsed_fields": {
        "skills": ["python", "fastapi", "postgresql", "docker"],
        "years_of_experience": 6.0,
        "education": ["B.Tech Computer Science, State University"],
        "certifications": ["AWS Certified Developer"],
        "recent_experience_end": "Present",
        "projects": ["Payments API"],
    }
}

MOCK_JD_TEXT = """
Backend Engineer

Requirements:
- 5+ years of experience building backend services
- Python, FastAPI, PostgreSQL, Docker, AWS
"""

SCORE_BREAKDOWN_FIELDS = (
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


def test_weights_are_seventy_thirty() -> None:
    assert SEMANTIC_WEIGHT == 0.7
    assert RULE_WEIGHT == 0.3
    assert SEMANTIC_WEIGHT + RULE_WEIGHT == pytest.approx(1.0)


def test_compute_final_score_exact_formula() -> None:
    semantic = 0.8
    rule = 0.6
    final = compute_final_score(semantic, rule)
    assert final == pytest.approx(0.7 * 0.8 + 0.3 * 0.6)
    assert final == pytest.approx(SEMANTIC_WEIGHT * semantic + RULE_WEIGHT * rule)


def test_compute_final_score_clamps_to_unit_interval() -> None:
    assert compute_final_score(1.5, 1.5) == 1.0
    assert compute_final_score(-0.2, -0.5) == 0.0


def test_compute_final_score_boundaries() -> None:
    assert compute_final_score(1.0, 1.0) == 1.0
    assert compute_final_score(0.0, 0.0) == 0.0


def test_compute_hybrid_breakdown_populates_every_field() -> None:
    jd = extract_job_requirements(MOCK_JD_TEXT)
    breakdown = compute_hybrid_breakdown(MOCK_CANDIDATE, jd, semantic_score=0.75)

    assert isinstance(breakdown, ScoreBreakdown)
    for field in SCORE_BREAKDOWN_FIELDS:
        assert hasattr(breakdown, field)
        value = getattr(breakdown, field)
        if field == "matched_skills":
            assert isinstance(value, list)
            assert value
        else:
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0


def test_compute_hybrid_breakdown_final_score_formula() -> None:
    jd = extract_job_requirements(MOCK_JD_TEXT)
    breakdown = compute_hybrid_breakdown(MOCK_CANDIDATE, jd, semantic_score=0.75)

    assert breakdown.semantic_similarity_score == pytest.approx(0.75)
    assert breakdown.final_score == pytest.approx(
        SEMANTIC_WEIGHT * breakdown.semantic_similarity_score
        + RULE_WEIGHT * breakdown.rule_score
    )


def test_compute_hybrid_breakdown_clamps_semantic_input() -> None:
    jd = extract_job_requirements(MOCK_JD_TEXT)
    breakdown = compute_hybrid_breakdown(MOCK_CANDIDATE, jd, semantic_score=1.4)
    assert breakdown.semantic_similarity_score == 1.0
    assert 0.0 <= breakdown.final_score <= 1.0


def test_compute_hybrid_breakdown_weak_vs_strong() -> None:
    jd = extract_job_requirements(MOCK_JD_TEXT)
    weak = {
        "parsed_fields": {
            "skills": ["javascript"],
            "years_of_experience": 1.0,
            "education": [],
            "certifications": [],
            "recent_experience_end": "2015",
        }
    }

    strong = compute_hybrid_breakdown(MOCK_CANDIDATE, jd, 0.7)
    weak_breakdown = compute_hybrid_breakdown(weak, jd, 0.7)

    assert weak_breakdown.final_score < strong.final_score
    assert weak_breakdown.rule_score < strong.rule_score
    for field in SCORE_BREAKDOWN_FIELDS:
        assert hasattr(weak_breakdown, field)
