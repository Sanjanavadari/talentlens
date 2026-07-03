import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Wraps sentence-transformers; load once at application startup."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._dimension = int(self._model.get_embedding_dimension())

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            return np.zeros(self._dimension, dtype=np.float32)

        vector = self._model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vector, dtype=np.float32)
