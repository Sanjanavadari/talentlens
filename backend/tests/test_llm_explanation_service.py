"""Unit tests for LLM-powered ranking explanations."""

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.schemas.ranking import ScoreBreakdown
from app.services.llm_explanation_service import generate_ranking_explanation

SAMPLE_BREAKDOWN = ScoreBreakdown(
    semantic_similarity_score=0.72,
    matched_skills=["python", "fastapi", "docker"],
    experience_score=1.0,
    education_score=0.7,
    certification_score=0.5,
    recency_score=1.0,
    skills_match_score=0.8,
    rule_score=0.85,
    final_score=0.759,
)

PARSED_FIELDS = {
    "skills": ["python", "fastapi", "postgresql", "docker"],
    "years_of_experience": 7.0,
    "education": ["B.Tech Computer Science"],
    "certifications": ["AWS Certified Developer"],
}

JD_TEXT = "Backend Engineer requiring 5+ years with Python, FastAPI, Docker, AWS."

MOCK_EXPLANATION = (
    "Ranked #1 primarily due to strong skills overlap (Python, FastAPI, Docker) "
    "and 7 years of relevant experience exceeding the 5-year requirement. "
    "Semantic similarity was high due to closely matching backend engineering language."
)

TEST_SETTINGS = Settings(
    llm_api_key="test-key",
    llm_model_name="claude-sonnet-4-20250514",
    llm_provider="anthropic",
)


def test_generate_ranking_explanation_returns_none_without_api_key() -> None:
    settings = Settings(llm_api_key=None)
    result = generate_ranking_explanation(
        SAMPLE_BREAKDOWN,
        PARSED_FIELDS,
        JD_TEXT,
        settings=settings,
    )
    assert result is None


@patch("app.services.llm_explanation_service._call_anthropic")
def test_generate_ranking_explanation_populated_on_success(mock_call: MagicMock) -> None:
    mock_call.return_value = MOCK_EXPLANATION

    result = generate_ranking_explanation(
        SAMPLE_BREAKDOWN,
        PARSED_FIELDS,
        JD_TEXT,
        rank=1,
        filename="jane_doe.pdf",
        settings=TEST_SETTINGS,
    )

    assert result == MOCK_EXPLANATION
    mock_call.assert_called_once()


@patch("app.services.llm_explanation_service._call_anthropic")
def test_generate_ranking_explanation_returns_none_on_failure(mock_call: MagicMock) -> None:
    mock_call.side_effect = RuntimeError("API timeout")

    result = generate_ranking_explanation(
        SAMPLE_BREAKDOWN,
        PARSED_FIELDS,
        JD_TEXT,
        settings=TEST_SETTINGS,
    )

    assert result is None


@patch("app.services.llm_explanation_service._call_openai")
def test_generate_ranking_explanation_uses_openai_provider(mock_call: MagicMock) -> None:
    mock_call.return_value = MOCK_EXPLANATION
    settings = Settings(
        llm_api_key="test-key",
        llm_model_name="gpt-4o-mini",
        llm_provider="openai",
    )

    result = generate_ranking_explanation(
        SAMPLE_BREAKDOWN,
        PARSED_FIELDS,
        JD_TEXT,
        settings=settings,
    )

    assert result == MOCK_EXPLANATION
    mock_call.assert_called_once()
