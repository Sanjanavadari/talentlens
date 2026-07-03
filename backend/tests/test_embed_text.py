from app.utils.embed_text import (
    build_candidate_embed_text,
    build_job_description_embed_text,
)


def test_build_candidate_embed_text_uses_structured_subset() -> None:
    parsed = {
        "skills": ["python", "fastapi"],
        "years_of_experience": 6.0,
        "education": ["B.Tech Computer Science"],
        "projects": ["Payments API"],
        "certifications": ["AWS Certified Developer"],
        "recent_experience_end": "Present",
    }
    text = build_candidate_embed_text(parsed, raw_text="Jane Doe\njane@example.com\n...noise...")

    assert "Skills: python, fastapi" in text
    assert "Experience: 6.0 years" in text
    assert "Projects: Payments API" in text
    assert "jane@example.com" not in text


def test_build_candidate_embed_text_falls_back_to_raw() -> None:
    raw = "Contact: foo@bar.com\n" + ("x" * 3000)
    text = build_candidate_embed_text({}, raw_text=raw)

    assert "foo@bar.com" in text
    assert len(text) <= 2000


def test_build_job_description_embed_text_includes_title() -> None:
    text = build_job_description_embed_text("Backend Engineer", "Python and FastAPI required.")
    assert text.startswith("Backend Engineer")
    assert "Python and FastAPI required." in text
