"""Quick manual check: embed two strings and print similarity scores."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import compute_similarity
from app.utils.embed_text import build_candidate_embed_text, build_job_description_embed_text


def main() -> None:
    service = EmbeddingService(
        "sentence-transformers/all-MiniLM-L6-v2",
        expected_dimension=384,
    )

    jd_text = build_job_description_embed_text(
        "Backend Engineer",
        "We need a Python developer with FastAPI, PostgreSQL, and Docker experience.",
    )
    candidate_text = build_candidate_embed_text(
        {
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "years_of_experience": 5,
            "projects": ["Payments microservice"],
        },
        raw_text="ignored when parsed fields exist",
    )
    unrelated_text = build_candidate_embed_text(
        {
            "skills": ["illustrator", "photoshop"],
            "years_of_experience": 4,
            "projects": ["Brand identity redesign"],
        },
        raw_text="ignored",
    )

    jd_vec = service.embed_text(jd_text)
    match_vec = service.embed_text(candidate_text)
    miss_vec = service.embed_text(unrelated_text)

    match_score = compute_similarity(jd_vec, match_vec)
    miss_score = compute_similarity(jd_vec, miss_vec)

    print(f"JD vs matching candidate: {match_score:.4f}")
    print(f"JD vs unrelated candidate: {miss_score:.4f}")
    assert 0.0 <= match_score <= 1.0
    assert 0.0 <= miss_score <= 1.0
    assert match_score > miss_score


if __name__ == "__main__":
    main()
