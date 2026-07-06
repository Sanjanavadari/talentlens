"""Natural-language ranking explanations via Anthropic or OpenAI."""

from __future__ import annotations

import logging
from typing import Any, Literal

from app.core.config import Settings, get_settings
from app.schemas.ranking import ScoreBreakdown

logger = logging.getLogger(__name__)

LLMProvider = Literal["anthropic", "openai"]


def _resolve_provider(settings: Settings) -> LLMProvider | None:
    if settings.llm_provider:
        return settings.llm_provider  # type: ignore[return-value]

    model = settings.llm_model_name.lower()
    if "claude" in model:
        return "anthropic"
    if model.startswith("gpt") or "o1" in model or "o3" in model:
        return "openai"
    return None


def _build_prompt(
    breakdown: ScoreBreakdown,
    parsed_fields: dict[str, Any],
    jd_text: str,
    *,
    rank: int | None = None,
    filename: str | None = None,
) -> str:
    skills = parsed_fields.get("skills") or []
    years = parsed_fields.get("years_of_experience")
    education = parsed_fields.get("education") or []
    certifications = parsed_fields.get("certifications") or []

    rank_line = f"Rank: #{rank}" if rank is not None else "Rank: (not provided)"
    name_line = f"Candidate file: {filename}" if filename else ""

    return f"""You are a recruiting assistant explaining why a candidate received their ranking score.
Write exactly 2-3 sentences of plain English. Be specific about skills overlap, experience, semantic fit, and rule-based factors.
Do not invent facts not present in the data. Do not mention JSON or scores by decimal — use qualitative language (strong/moderate/low).

{rank_line}
{name_line}

Job description:
{jd_text.strip()[:2000]}

Candidate parsed profile:
- Skills: {", ".join(skills) if skills else "none detected"}
- Years of experience: {years if years is not None else "unknown"}
- Education: {"; ".join(education) if education else "none detected"}
- Certifications: {"; ".join(certifications) if certifications else "none"}

Score breakdown (0.0–1.0 scale):
- Semantic similarity: {breakdown.semantic_similarity_score:.2f}
- Matched JD skills: {", ".join(breakdown.matched_skills) if breakdown.matched_skills else "none"}
- Experience score: {breakdown.experience_score:.2f}
- Skills match score: {breakdown.skills_match_score:.2f}
- Education score: {breakdown.education_score:.2f}
- Certification score: {breakdown.certification_score:.2f}
- Recency score: {breakdown.recency_score:.2f}
- Rule-based composite: {breakdown.rule_score:.2f}
- Final weighted score: {breakdown.final_score:.2f} (70% semantic + 30% rule-based)

Write the explanation only — no bullet points or preamble."""


def _call_anthropic(prompt: str, settings: Settings) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.llm_api_key, timeout=settings.llm_timeout_seconds)
    response = client.messages.create(
        model=settings.llm_model_name,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    return " ".join(text_blocks).strip()


def _call_openai(prompt: str, settings: Settings) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.llm_api_key, timeout=settings.llm_timeout_seconds)
    response = client.chat.completions.create(
        model=settings.llm_model_name,
        max_tokens=256,
        messages=[
            {
                "role": "system",
                "content": "You write concise recruiter-facing ranking explanations.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def generate_ranking_explanation(
    breakdown: ScoreBreakdown,
    parsed_fields: dict[str, Any],
    jd_text: str,
    *,
    rank: int | None = None,
    filename: str | None = None,
    settings: Settings | None = None,
) -> str | None:
    """Return a 2–3 sentence explanation, or None if unavailable or on failure."""
    settings = settings or get_settings()

    if not settings.llm_api_key:
        logger.warning("LLM explanation skipped: LLM_API_KEY is not configured.")
        return None

    provider = _resolve_provider(settings)
    if provider is None:
        logger.warning(
            "LLM explanation skipped: could not determine provider from LLM_PROVIDER or LLM_MODEL_NAME."
        )
        return None

    prompt = _build_prompt(
        breakdown,
        parsed_fields,
        jd_text,
        rank=rank,
        filename=filename,
    )

    try:
        if provider == "anthropic":
            explanation = _call_anthropic(prompt, settings)
        else:
            explanation = _call_openai(prompt, settings)

        if not explanation:
            logger.warning("LLM explanation skipped: provider returned empty text.")
            return None

        return explanation
    except Exception:
        logger.warning("LLM explanation failed", exc_info=True)
        return None
