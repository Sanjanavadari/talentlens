"""Unit tests for rule-based scoring components."""

import pytest

from app.services.scoring_service import (
    CERTIFICATION_WEIGHT,
    EDUCATION_WEIGHT,
    EXPERIENCE_WEIGHT,
    RECENCY_WEIGHT,
    SKILLS_WEIGHT,
    JobRequirements,
    compute_rule_score,
    extract_job_requirements,
    score_certifications,
    score_education,
    score_experience,
    score_recency,
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


def test_extract_job_requirements_ambiguous_year_range() -> None:
    jd = extract_job_requirements("Looking for 3-5 years of experience with Python.")
    assert jd.min_years_experience == 3.0
    assert "python" in jd.required_skills


# --- score_experience ---


def test_score_experience_meets_requirement(job_requirements: JobRequirements) -> None:
    assert score_experience(MOCK_CANDIDATE, job_requirements) == pytest.approx(1.0)


def test_score_experience_partial_match(job_requirements: JobRequirements) -> None:
    candidate = {"parsed_fields": {"years_of_experience": 2.5}}
    assert score_experience(candidate, job_requirements) == pytest.approx(0.5)


def test_score_experience_no_jd_requirement() -> None:
    jd = JobRequirements(text="", required_skills=[], min_years_experience=0.0)
    with_years = {"parsed_fields": {"years_of_experience": 3.0}}
    without_years = {"parsed_fields": {"years_of_experience": 0.0}}
    assert score_experience(with_years, jd) == 1.0
    assert score_experience(without_years, jd) == 0.5


def test_score_experience_clamps_above_one(job_requirements: JobRequirements) -> None:
    overqualified = {"parsed_fields": {"years_of_experience": 20.0}}
    assert score_experience(overqualified, job_requirements) == 1.0


# --- score_skills_match ---


def test_score_skills_match_returns_matched_list() -> None:
    result = score_skills_match(
        ["python", "react", "docker"],
        ["python", "fastapi", "docker"],
    )
    assert result.score == pytest.approx(2 / 3)
    assert set(result.matched_skills) == {"python", "docker"}


def test_score_skills_match_full_overlap() -> None:
    result = score_skills_match(["python", "docker"], ["python", "docker"])
    assert result.score == 1.0
    assert result.matched_skills == ["python", "docker"]


def test_score_skills_match_no_overlap() -> None:
    result = score_skills_match(["react"], ["python", "fastapi"])
    assert result.score == 0.0
    assert result.matched_skills == []


def test_score_skills_match_empty_jd_skills() -> None:
    result = score_skills_match(["python"], [])
    assert result.score == 0.5
    assert result.matched_skills == []


# --- score_education ---


def test_score_education_btech() -> None:
    candidate = {"parsed_fields": {"education": ["B.Tech Computer Science"]}}
    assert score_education(candidate) == pytest.approx(0.7)


def test_score_education_phd_highest() -> None:
    candidate = {
        "parsed_fields": {
            "education": [
                "B.S. Mathematics",
                "M.S. Artificial Intelligence",
                "Ph.D. Computer Science",
            ]
        }
    }
    assert score_education(candidate) == pytest.approx(1.0)


def test_score_education_empty() -> None:
    assert score_education({"parsed_fields": {"education": []}}) == 0.0


# --- score_certifications ---


def test_score_certifications_none() -> None:
    assert score_certifications({"parsed_fields": {"certifications": []}}) == 0.0


def test_score_certifications_partial() -> None:
    candidate = {"parsed_fields": {"certifications": ["AWS Certified Developer"]}}
    assert score_certifications(candidate) == pytest.approx(0.5)


def test_score_certifications_full() -> None:
    candidate = {
        "parsed_fields": {
            "certifications": ["AWS Certified Developer", "Kubernetes Administrator"]
        }
    }
    assert score_certifications(candidate) == 1.0


def test_score_certifications_clamps_above_cap() -> None:
    candidate = {
        "parsed_fields": {
            "certifications": ["A", "B", "C", "D"],
        }
    }
    assert score_certifications(candidate) == 1.0


# --- score_recency ---


def test_score_recency_present() -> None:
    assert score_recency({"parsed_fields": {"recent_experience_end": "Present"}}) == 1.0


def test_score_recency_missing() -> None:
    assert score_recency({"parsed_fields": {}}) == 0.5


def test_score_recency_old_year() -> None:
    assert score_recency({"parsed_fields": {"recent_experience_end": "2015"}}) == 0.3


# --- compute_rule_score ---


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
        + components["education_score"] * EDUCATION_WEIGHT
        + components["certification_score"] * CERTIFICATION_WEIGHT
        + components["recency_score"] * RECENCY_WEIGHT
    )
    assert rule_score == pytest.approx(expected_rule)


def test_compute_rule_score_weights_sum_to_one() -> None:
    total = (
        EXPERIENCE_WEIGHT
        + SKILLS_WEIGHT
        + EDUCATION_WEIGHT
        + CERTIFICATION_WEIGHT
        + RECENCY_WEIGHT
    )
    assert total == pytest.approx(1.0)


def test_compute_rule_score_weak_candidate(job_requirements: JobRequirements) -> None:
    weak = {
        "parsed_fields": {
            "skills": ["javascript"],
            "years_of_experience": 1.0,
            "education": [],
            "certifications": [],
            "recent_experience_end": "2015",
        }
    }
    strong_score, _, _ = compute_rule_score(MOCK_CANDIDATE, job_requirements)
    weak_score, _, weak_components = compute_rule_score(weak, job_requirements)

    assert weak_score < strong_score
    assert weak_components["experience_score"] < 1.0
    assert weak_components["education_score"] == 0.0
    assert weak_components["certification_score"] == 0.0
