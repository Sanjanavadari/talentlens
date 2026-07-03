"""Rule-based scoring components for candidate–JD matching."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.services.info_extractor import extract_skills
from app.utils.skills_keywords import DEGREE_KEYWORDS

# Sub-weights for the rule-based composite (must sum to 1.0)
EXPERIENCE_WEIGHT = 0.30
SKILLS_WEIGHT = 0.35
EDUCATION_WEIGHT = 0.15
CERTIFICATION_WEIGHT = 0.10
RECENCY_WEIGHT = 0.10

JD_MIN_YEARS_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:of\s+)?experience",
    re.IGNORECASE,
)
JD_YEARS_RANGE_PATTERN = re.compile(
    r"(\d+)\s*[-–—]\s*(\d+)\s*(?:years?|yrs?)",
    re.IGNORECASE,
)

DEGREE_LEVEL_SCORES: list[tuple[str, float]] = [
    ("ph.d", 1.0),
    ("phd", 1.0),
    ("doctorate", 1.0),
    ("m.s.", 0.85),
    ("m.s", 0.85),
    ("master", 0.85),
    ("mba", 0.85),
    ("b.tech", 0.7),
    ("btech", 0.7),
    ("b.e.", 0.7),
    ("bachelor", 0.7),
    ("b.s.", 0.7),
    ("b.s", 0.7),
    ("b.a.", 0.65),
    ("associate", 0.5),
]

MAX_CERTIFICATIONS_FOR_FULL_SCORE = 2
NEUTRAL_SCORE_WHEN_JD_SKILL_LIST_EMPTY = 0.5
DEFAULT_MIN_YEARS_WHEN_UNSPECIFIED = 0.0


@dataclass(frozen=True)
class JobRequirements:
    text: str
    required_skills: list[str]
    min_years_experience: float


@dataclass(frozen=True)
class SkillsMatchResult:
    score: float
    matched_skills: list[str]


def _clamp(score: float) -> float:
    return max(0.0, min(1.0, float(score)))


def extract_job_requirements(jd_text: str) -> JobRequirements:
    text = jd_text.strip()
    required_skills = extract_skills(text)
    min_years = _extract_min_years_from_jd(text)
    return JobRequirements(
        text=text,
        required_skills=required_skills,
        min_years_experience=min_years,
    )


def _extract_min_years_from_jd(jd_text: str) -> float:
    range_match = JD_YEARS_RANGE_PATTERN.search(jd_text)
    if range_match:
        return float(range_match.group(1))

    min_match = JD_MIN_YEARS_PATTERN.search(jd_text)
    if min_match:
        return float(min_match.group(1))

    return DEFAULT_MIN_YEARS_WHEN_UNSPECIFIED


def _parsed(candidate: dict[str, Any]) -> dict[str, Any]:
    if "parsed_fields" in candidate:
        return candidate["parsed_fields"] or {}
    return candidate


def score_experience(candidate: dict[str, Any], jd: JobRequirements) -> float:
    fields = _parsed(candidate)
    candidate_years = float(fields.get("years_of_experience") or 0.0)
    required_years = jd.min_years_experience

    if required_years <= 0:
        return 1.0 if candidate_years > 0 else 0.5

    return _clamp(candidate_years / required_years)


def score_skills_match(
    candidate_skills: list[str],
    jd_skills: list[str],
) -> SkillsMatchResult:
    normalized_candidate = {_normalize_skill(s) for s in candidate_skills}
    normalized_jd = [_normalize_skill(s) for s in jd_skills]

    if not normalized_jd:
        return SkillsMatchResult(
            score=NEUTRAL_SCORE_WHEN_JD_SKILL_LIST_EMPTY,
            matched_skills=[],
        )

    matched = [skill for skill in normalized_jd if skill in normalized_candidate]
    score = _clamp(len(matched) / len(normalized_jd))
    return SkillsMatchResult(score=score, matched_skills=matched)


def score_education(candidate: dict[str, Any]) -> float:
    fields = _parsed(candidate)
    education_entries = fields.get("education") or []
    if not education_entries:
        return 0.0

    best = 0.0
    for entry in education_entries:
        lowered = entry.lower()
        for keyword, value in DEGREE_LEVEL_SCORES:
            if keyword in lowered:
                best = max(best, value)
                break
        else:
            if any(degree in lowered for degree in DEGREE_KEYWORDS):
                best = max(best, 0.6)

    return _clamp(best)


def score_certifications(candidate: dict[str, Any]) -> float:
    fields = _parsed(candidate)
    certifications = fields.get("certifications") or []
    if not certifications:
        return 0.0
    return _clamp(len(certifications) / MAX_CERTIFICATIONS_FOR_FULL_SCORE)


def score_recency(candidate: dict[str, Any]) -> float:
    fields = _parsed(candidate)
    recent_end = fields.get("recent_experience_end")
    if not recent_end:
        return 0.5

    if re.search(r"present|current", str(recent_end), re.IGNORECASE):
        return 1.0

    year_match = re.search(r"\b(19|20)\d{2}\b", str(recent_end))
    if not year_match:
        return 0.5

    end_year = int(year_match.group(0))
    years_ago = datetime.now(UTC).year - end_year

    if years_ago <= 0:
        return 1.0
    if years_ago == 1:
        return 0.85
    if years_ago == 2:
        return 0.7
    if years_ago <= 4:
        return 0.5
    return 0.3


def _normalize_skill(skill: str) -> str:
    return skill.strip().lower()


def compute_rule_score(
    candidate: dict[str, Any],
    jd: JobRequirements,
) -> tuple[float, SkillsMatchResult, dict[str, float]]:
    fields = _parsed(candidate)
    candidate_skills = fields.get("skills") or []

    experience_score = score_experience(candidate, jd)
    skills_result = score_skills_match(candidate_skills, jd.required_skills)
    education_score = score_education(candidate)
    certification_score = score_certifications(candidate)
    recency_score = score_recency(candidate)

    component_scores = {
        "experience_score": experience_score,
        "skills_match_score": skills_result.score,
        "education_score": education_score,
        "certification_score": certification_score,
        "recency_score": recency_score,
    }

    rule_score = _clamp(
        experience_score * EXPERIENCE_WEIGHT
        + skills_result.score * SKILLS_WEIGHT
        + education_score * EDUCATION_WEIGHT
        + certification_score * CERTIFICATION_WEIGHT
        + recency_score * RECENCY_WEIGHT
    )

    return rule_score, skills_result, component_scores
