"""FAISS-backed candidate similarity with plain float outputs.

Uses IndexFlatIP over L2-normalized vectors so inner product equals cosine
similarity. All public methods return Python floats in [0, 1].
"""

from __future__ import annotations

import faiss
import numpy as np


def clamp_similarity(score: float) -> float:
    """Map cosine similarity to a predictable [0, 1] range."""
    return max(0.0, min(1.0, float(score)))


def compute_similarity(query_embedding: np.ndarray, candidate_embedding: np.ndarray) -> float:
    """Cosine similarity between two embeddings as a plain float in [0, 1]."""
    query = _normalize(query_embedding)
    candidate = _normalize(candidate_embedding)
    return clamp_similarity(float(np.dot(query, candidate)))


def _normalize(vector: np.ndarray) -> np.ndarray:
    arr = np.asarray(vector, dtype=np.float32).flatten()
    norm = np.linalg.norm(arr)
    if norm == 0.0:
        return arr
    return arr / norm


class CandidateVectorIndex:
    """In-memory flat FAISS index keyed by candidate ID.

    Suitable for small pools (~20 candidates). Rebuilt wholesale on updates
    rather than using IVF/HNSW, which are unnecessary at this scale.
    """

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension
        self._candidate_ids: list[int] = []
        self._embeddings_by_id: dict[int, np.ndarray] = {}
        self._index = faiss.IndexFlatIP(dimension)

    @property
    def candidate_ids(self) -> list[int]:
        return list(self._candidate_ids)

    def __len__(self) -> int:
        return len(self._candidate_ids)

    def rebuild(self, entries: list[tuple[int, np.ndarray]]) -> None:
        self._index = faiss.IndexFlatIP(self.dimension)
        self._candidate_ids = []
        self._embeddings_by_id = {}

        if not entries:
            return

        ids: list[int] = []
        vectors: list[np.ndarray] = []
        for candidate_id, embedding in entries:
            normalized = _normalize(embedding)
            ids.append(candidate_id)
            vectors.append(normalized)
            self._embeddings_by_id[candidate_id] = normalized

        matrix = np.vstack(vectors).astype(np.float32)
        self._index.add(matrix)
        self._candidate_ids = ids

    def upsert(self, candidate_id: int, embedding: np.ndarray) -> None:
        updated = dict(self._embeddings_by_id)
        updated[candidate_id] = _normalize(embedding)
        entries = list(updated.items())
        self.rebuild(entries)

    def get_embedding(self, candidate_id: int) -> np.ndarray | None:
        return self._embeddings_by_id.get(candidate_id)

    def similarity_for_candidate(
        self,
        candidate_id: int,
        query_embedding: np.ndarray,
    ) -> float | None:
        candidate_embedding = self._embeddings_by_id.get(candidate_id)
        if candidate_embedding is None:
            return None
        return compute_similarity(query_embedding, candidate_embedding)

    def rank_by_similarity(
        self,
        query_embedding: np.ndarray,
        top_k: int | None = None,
    ) -> list[tuple[int, float]]:
        if not self._candidate_ids:
            return []

        query = _normalize(query_embedding).astype(np.float32).reshape(1, -1)
        k = min(top_k or len(self._candidate_ids), len(self._candidate_ids))
        scores, indices = self._index.search(query, k)

        results: list[tuple[int, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0:
                continue
            candidate_id = self._candidate_ids[int(idx)]
            results.append((candidate_id, clamp_similarity(float(score))))
        return results
