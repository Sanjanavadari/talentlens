import pytest

from app.services.hybrid_scoring import (
    RULE_WEIGHT,
    SEMANTIC_WEIGHT,
    compute_final_score,
    compute_hybrid_breakdown,
)
from app.services.scoring_service import (
    EXPERIENCE_WEIGHT,
    SKILLS_WEIGHT,
    JobRequirements,
    compute_rule_score,
    extract_job_requirements,
    score_skills_match,
)


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
- B.Tech or equivalent degree
"""


@pytest.fixture
def job_requirements() -> JobRequirements:
    return extract_job_requirements(MOCK_JD_TEXT)


def test_extract_job_requirements(job_requirements: JobRequirements) -> None:
    assert job_requirements.min_years_experience == 5.0
    assert "python" in job_requirements.required_skills
    assert "fastapi" in job_requirements.required_skills


def test_score_skills_match_returns_matched_list() -> None:
    result = score_skills_match(
        ["python", "react", "docker"],
        ["python", "fastapi", "docker"],
    )
    assert result.score == pytest.approx(2 / 3)
    assert set(result.matched_skills) == {"python", "docker"}


def test_compute_rule_score_populates_components(job_requirements: JobRequirements) -> None:
    rule_score, skills_result, components = compute_rule_score(MOCK_CANDIDATE, job_requirements)

    assert 0.0 <= rule_score <= 1.0
    assert "python" in skills_result.matched_skills
    assert components["experience_score"] == pytest.approx(1.0)
    assert components["education_score"] > 0
    assert components["certification_score"] > 0
    assert components["recency_score"] == 1.0

    expected_rule = (
        components["experience_score"] * EXPERIENCE_WEIGHT
        + components["skills_match_score"] * SKILLS_WEIGHT
        + components["education_score"] * 0.15
        + components["certification_score"] * 0.10
        + components["recency_score"] * 0.10
    )
    assert rule_score == pytest.approx(expected_rule)


def test_compute_final_score_weighted_sum() -> None:
    semantic = 0.8
    rule = 0.6
    final = compute_final_score(semantic, rule)
    assert final == pytest.approx(SEMANTIC_WEIGHT * semantic + RULE_WEIGHT * rule)


def test_compute_hybrid_breakdown_all_fields(job_requirements: JobRequirements) -> None:
    semantic_score = 0.75
    breakdown = compute_hybrid_breakdown(MOCK_CANDIDATE, job_requirements, semantic_score)

    assert breakdown.semantic_similarity_score == pytest.approx(0.75)
    assert breakdown.matched_skills
    assert breakdown.experience_score > 0
    assert breakdown.education_score > 0
    assert breakdown.certification_score > 0
    assert breakdown.recency_score > 0
    assert breakdown.skills_match_score > 0
    assert breakdown.rule_score > 0
    assert breakdown.final_score == pytest.approx(
        SEMANTIC_WEIGHT * breakdown.semantic_similarity_score
        + RULE_WEIGHT * breakdown.rule_score
    )


def test_underqualified_candidate_scores_lower(job_requirements: JobRequirements) -> None:
    weak_candidate = {
        "parsed_fields": {
            "skills": ["javascript"],
            "years_of_experience": 1.0,
            "education": [],
            "certifications": [],
            "recent_experience_end": "2019",
        }
    }

    strong_breakdown = compute_hybrid_breakdown(MOCK_CANDIDATE, job_requirements, 0.7)
    weak_breakdown = compute_hybrid_breakdown(weak_candidate, job_requirements, 0.7)

    assert weak_breakdown.final_score < strong_breakdown.final_score
    assert weak_breakdown.rule_score < strong_breakdown.rule_score
