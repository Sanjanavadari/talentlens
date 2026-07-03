"""Build the text payload used for candidate embeddings.

We deliberately embed a structured subset (skills, experience, projects,
education, certifications) rather than raw resume text. Raw PDFs contain
headers, contact blocks, and layout noise that dilute semantic signal for
job-description matching. Parsed fields concentrate role-relevant content.

If parsing yields almost nothing, we fall back to a truncated cleaned
excerpt of raw text so sparse resumes still produce an embedding.
"""

from app.utils.text_cleaning import clean_text

_RAW_FALLBACK_MAX_CHARS = 2000


def build_candidate_embed_text(
    parsed_fields: dict,
    raw_text: str | None = None,
) -> str:
    parts: list[str] = []

    skills = parsed_fields.get("skills") or []
    if skills:
        parts.append("Skills: " + ", ".join(skills))

    years = parsed_fields.get("years_of_experience")
    if years is not None and years > 0:
        parts.append(f"Experience: {years} years")

    recent_end = parsed_fields.get("recent_experience_end")
    if recent_end:
        parts.append(f"Most recent role end: {recent_end}")

    education = parsed_fields.get("education") or []
    if education:
        parts.append("Education: " + "; ".join(education))

    projects = parsed_fields.get("projects") or []
    if projects:
        parts.append("Projects: " + "; ".join(projects))

    certifications = parsed_fields.get("certifications") or []
    if certifications:
        parts.append("Certifications: " + "; ".join(certifications))

    if parts:
        return "\n".join(parts)

    if raw_text:
        return clean_text(raw_text)[:_RAW_FALLBACK_MAX_CHARS]

    return ""


def build_job_description_embed_text(title: str, text: str) -> str:
    """Job descriptions are embedded in full — title + body."""
    title = title.strip()
    body = clean_text(text)
    if title:
        return f"{title}\n\n{body}"
    return body
