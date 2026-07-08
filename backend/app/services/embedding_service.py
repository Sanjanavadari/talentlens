import threading

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Wraps sentence-transformers with lazy model loading.

    The transformer is loaded on first embed_text() call, not at construction
    time. This keeps process startup light so /health can respond on small
    hosts (e.g. Render 512MB) before torch + weights are pulled into memory.
    """

    def __init__(self, model_name: str, *, expected_dimension: int) -> None:
        self.model_name = model_name
        self._expected_dimension = expected_dimension
        self._model: SentenceTransformer | None = None
        self._dimension = expected_dimension
        self._lock = threading.Lock()

    @property
    def dimension(self) -> int:
        return self._dimension

    def _get_model(self) -> SentenceTransformer:
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                self._model = SentenceTransformer(self.model_name)
                self._dimension = int(self._model.get_embedding_dimension())
            return self._model

    def embed_text(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            return np.zeros(self._dimension, dtype=np.float32)

        vector = self._get_model().encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vector, dtype=np.float32)
