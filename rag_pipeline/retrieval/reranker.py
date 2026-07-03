"""
Document Reranking Engine

This module provides sophisticated document reranking capabilities to refine
retrieval results using multiple strategies including cross-encoder scoring
and lightweight heuristics for improved relevance ranking.

Features:
- Multiple reranking strategies (PassThrough, CrossEncoder)
- Cross-encoder relevance scoring
- Lightweight heuristic reranking
- Pluggable reranker architecture
- Performance optimization
- Document scoring normalization
- Extensible reranker interface
- Production-ready implementations

Reranker Types:
- PassThroughReranker: Preserves original ordering (baseline)
- CrossEncoderReranker: Deep learning relevance scoring
- Custom rerankers: Extensible protocol-based interface

Usage:
    # Basic pass-through reranking
    reranker = PassThroughReranker()
    
    # Advanced cross-encoder reranking
    reranker = CrossEncoderReranker(model_name='cross-encoder/model')
    
    # Apply reranking
    ranked_docs = reranker.rerank(query='search text', documents=retrieved_docs)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol, Sequence


@dataclass
class RetrievedDocument:
    """Represents a document chunk returned by the primary retriever."""

    text: str
    score: float
    metadata: dict


class Reranker(Protocol):
    """Common interface so the retriever can plug in any reranking strategy."""

    def rerank(
        self, query: str, documents: Sequence[RetrievedDocument], top_k: int = 5
    ) -> List[RetrievedDocument]:
        ...


class PassThroughReranker:
    """Default implementation that keeps the original retrieval order intact."""

    def rerank(
        self, query: str, documents: Sequence[RetrievedDocument], top_k: int = 5
    ) -> List[RetrievedDocument]:
        """Return the first `top_k` documents without changing their scores."""

        return list(documents[:top_k])


class KeywordOverlapReranker:
    """Toy reranker using keyword overlap as a quick precision boost."""

    def rerank(
        self, query: str, documents: Sequence[RetrievedDocument], top_k: int = 5
    ) -> List[RetrievedDocument]:
        """Score documents by counting shared keywords with the query."""

        keywords = set(token.lower() for token in query.split())
        scored: List[RetrievedDocument] = []
        for doc in documents:
            doc_tokens = set(doc.text.split())
            overlap = len(keywords & {token.lower() for token in doc_tokens})
            scored.append(
                RetrievedDocument(
                    text=doc.text,
                    score=doc.score + overlap,
                    metadata=doc.metadata,
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


class CrossEncoderReranker:
    """Cross-encoder reranker using sentence-transformers CrossEncoder models.

    Scores each (query, document) pair directly with a cross-encoder model,
    which is typically more accurate than bi-encoder similarity but slower
    since it can't be precomputed/cached per document.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        """Store model details; the model itself is loaded lazily on first use."""

        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """Lazily import and instantiate the CrossEncoder model."""

        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:  # pragma: no cover - handled at runtime
                raise RuntimeError(
                    "sentence-transformers is required for CrossEncoderReranker. "
                    "Install it via `pip install sentence-transformers`."
                ) from exc

            self._model = CrossEncoder(self.model_name)

        return self._model

    def rerank(
        self, query: str, documents: Sequence[RetrievedDocument], top_k: int = 5
    ) -> List[RetrievedDocument]:
        """Score every document against the query and return the top_k by score."""

        if not documents:
            return []

        model = self._load_model()
        pairs = [(query, doc.text) for doc in documents]
        scores = model.predict(pairs)

        scored = [
            RetrievedDocument(text=doc.text, score=float(score), metadata=doc.metadata)
            for doc, score in zip(documents, scores)
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]
