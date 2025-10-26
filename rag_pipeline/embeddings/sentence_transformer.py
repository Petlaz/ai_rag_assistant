"""Sentence-transformer based embedding helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - handled during runtime
    SentenceTransformer = None  # type: ignore[assignment]


@dataclass
class SentenceTransformerEmbeddings:
    """Wraps a sentence-transformer model for document + query embeddings."""

    model_name: str = "all-MiniLM-L6-v2"
    _model: SentenceTransformer | None = None

    def _ensure_model(self) -> SentenceTransformer:
        """Lazy-load the transformer so import time stays light."""

        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers must be installed to use embedding features."
            )

        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for multiple documents."""

        if not texts:
            return []
        model = self._ensure_model()
        vectors = model.encode(
            texts,
            batch_size=16,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Return an embedding suitable for hybrid search queries."""

        model = self._ensure_model()
        vector = model.encode(
            text,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return vector.tolist()
