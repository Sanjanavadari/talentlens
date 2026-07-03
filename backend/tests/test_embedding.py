from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.candidate_embedding_cache import CandidateEmbeddingCache
from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import CandidateVectorIndex, compute_similarity


@pytest.fixture
def mock_embedding_service() -> EmbeddingService:
    service = MagicMock(spec=EmbeddingService)
    service.model_name = "test-model"
    service.dimension = 4

    def _embed(text: str) -> np.ndarray:
        if "python" in text.lower():
            return np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        if "javascript" in text.lower():
            return np.asarray([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
        return np.asarray([0.0, 0.0, 1.0, 0.0], dtype=np.float32)

    service.embed_text.side_effect = _embed
    return service


def test_embedding_cache_skips_recompute_when_hash_matches(
    mock_embedding_service: EmbeddingService,
    db_session,
) -> None:
    from app.models.candidate import Candidate
    from app.services.candidate_embedding_cache import _hash_embed_text

    index = CandidateVectorIndex(dimension=4)
    cache = CandidateEmbeddingCache(mock_embedding_service, index)

    parsed = {"skills": ["python"], "years_of_experience": 3}
    embed_text = cache.embed_text_for_candidate(parsed, "noise")
    candidate = Candidate(
        filename="a.pdf",
        raw_text="noise",
        parsed_fields=parsed,
        embedding=[1.0, 0.0, 0.0, 0.0],
        embedding_text_hash=_hash_embed_text(embed_text),
        embedding_model="test-model",
    )
    db_session.add(candidate)
    db_session.commit()

    vector = cache.get_or_compute(db_session, candidate)
    mock_embedding_service.embed_text.assert_not_called()
    assert vector.tolist() == [1.0, 0.0, 0.0, 0.0]
    assert candidate.id in index.candidate_ids


def test_embedding_cache_computes_and_persists_on_miss(
    mock_embedding_service: EmbeddingService,
    db_session,
) -> None:
    from app.models.candidate import Candidate

    index = CandidateVectorIndex(dimension=4)
    cache = CandidateEmbeddingCache(mock_embedding_service, index)

    candidate = Candidate(
        filename="b.pdf",
        raw_text="raw",
        parsed_fields={"skills": ["javascript"]},
    )
    db_session.add(candidate)
    db_session.commit()

    vector = cache.get_or_compute(db_session, candidate)
    mock_embedding_service.embed_text.assert_called_once()
    assert vector.tolist() == [0.0, 1.0, 0.0, 0.0]
    assert candidate.embedding == [0.0, 1.0, 0.0, 0.0]
    assert candidate.embedding_model == "test-model"
    assert candidate.id in index.candidate_ids


@pytest.mark.slow
def test_real_embedding_service_similarity() -> None:
    service = EmbeddingService("sentence-transformers/all-MiniLM-L6-v2")
    python_text = "Senior Python backend engineer with FastAPI and PostgreSQL experience."
    unrelated_text = "Graphic designer specializing in print layout and typography."

    python_vec = service.embed_text(python_text)
    unrelated_vec = service.embed_text(unrelated_text)

    similar_score = compute_similarity(python_vec, python_vec)
    cross_score = compute_similarity(python_vec, unrelated_vec)

    assert 0.0 <= similar_score <= 1.0
    assert 0.0 <= cross_score <= 1.0
    assert similar_score > cross_score
