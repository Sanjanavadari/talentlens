import numpy as np

from app.services.similarity_service import (
    CandidateVectorIndex,
    clamp_similarity,
    compute_similarity,
)


def _unit_vector(values: list[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float32)
    return arr / np.linalg.norm(arr)


def test_clamp_similarity_bounds() -> None:
    assert clamp_similarity(1.5) == 1.0
    assert clamp_similarity(-0.5) == 0.0
    assert clamp_similarity(0.75) == 0.75


def test_compute_similarity_identical_vectors() -> None:
    vector = _unit_vector([1.0, 0.0, 0.0])
    score = compute_similarity(vector, vector)
    assert 0.99 <= score <= 1.0


def test_compute_similarity_orthogonal_vectors() -> None:
    a = _unit_vector([1.0, 0.0, 0.0])
    b = _unit_vector([0.0, 1.0, 0.0])
    score = compute_similarity(a, b)
    assert score == 0.0


def test_compute_similarity_returns_plain_float() -> None:
    a = _unit_vector([1.0, 1.0, 0.0])
    b = _unit_vector([1.0, 0.5, 0.0])
    score = compute_similarity(a, b)
    assert isinstance(score, float)


def test_candidate_vector_index_ranking() -> None:
    index = CandidateVectorIndex(dimension=3)
    query = _unit_vector([1.0, 0.2, 0.0])

    index.rebuild(
        [
            (1, _unit_vector([1.0, 0.0, 0.0])),
            (2, _unit_vector([0.9, 0.1, 0.0])),
            (3, _unit_vector([0.0, 1.0, 0.0])),
        ]
    )

    ranked = index.rank_by_similarity(query)
    assert [candidate_id for candidate_id, _ in ranked] == [2, 1, 3]
    assert all(isinstance(score, float) for _, score in ranked)
    assert all(0.0 <= score <= 1.0 for _, score in ranked)


def test_candidate_vector_index_upsert() -> None:
    index = CandidateVectorIndex(dimension=2)
    index.upsert(10, _unit_vector([1.0, 0.0]))
    index.upsert(11, _unit_vector([0.0, 1.0]))

    assert set(index.candidate_ids) == {10, 11}
    score = index.similarity_for_candidate(10, _unit_vector([1.0, 0.0]))
    assert score is not None
    assert score > 0.99
