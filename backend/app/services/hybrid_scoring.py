"""Combine semantic similarity with rule-based scoring."""

from __future__ import annotations

from typing import Any

from app.schemas.ranking import ScoreBreakdown
from app.services.scoring_service import JobRequirements, compute_rule_score

SEMANTIC_WEIGHT = 0.7
RULE_WEIGHT = 0.3


def _clamp(score: float) -> float:
    return max(0.0, min(1.0, float(score)))


def compute_final_score(semantic_score: float, rule_score: float) -> float:
    return _clamp(SEMANTIC_WEIGHT * semantic_score + RULE_WEIGHT * rule_score)


def compute_hybrid_breakdown(
    candidate: dict[str, Any],
    jd: JobRequirements,
    semantic_score: float,
) -> ScoreBreakdown:
    """Produce a full explainability breakdown for one candidate."""
    semantic = _clamp(semantic_score)
    rule_score, skills_result, components = compute_rule_score(candidate, jd)
    final_score = compute_final_score(semantic, rule_score)

    return ScoreBreakdown(
        semantic_similarity_score=semantic,
        matched_skills=skills_result.matched_skills,
        experience_score=components["experience_score"],
        education_score=components["education_score"],
        certification_score=components["certification_score"],
        recency_score=components["recency_score"],
        skills_match_score=components["skills_match_score"],
        rule_score=rule_score,
        final_score=final_score,
    )
