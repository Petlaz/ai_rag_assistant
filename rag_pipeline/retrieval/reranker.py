"""Reranking utilities used to refine the retriever output.

The initial Quest Analytics launch will rely on lightweight heuristics, and we
can swap in heavier cross-encoders once latency and infra budgets allow.  The
goal here is to provide a clear extension point for future improvements.
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
    """Placeholder for a future cross-encoder (e.g. sentence-transformers)."""

    def __init__(self, model_name: str) -> None:
        """Store model details; actual loading happens once we pick a backend."""

        self.model_name = model_name

    def rerank(
        self, query: str, documents: Sequence[RetrievedDocument], top_k: int = 5
    ) -> List[RetrievedDocument]:
        """Stub that reminds us to implement cross-encoder scoring."""

        raise NotImplementedError(
            "Cross-encoder reranking requires model integration."
        )
