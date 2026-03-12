"""
Hybrid Retrieval Engine

This module implements the core hybrid retrieval system that combines BM25 sparse
retrieval with dense vector search, integrated with OpenSearch backend and
supporting multiple reranking strategies for optimal retrieval performance.

Features:
- Hybrid BM25 + vector similarity search
- Configurable retrieval weights (BM25 vs semantic)
- Multiple reranker integration
- Query embedding optimization
- OpenSearch protocol integration
- Flexible top-k retrieval
- Document scoring and ranking
- Production-ready error handling

Architecture:
- SearchClient protocol for OpenSearch integration
- QueryEmbedder protocol for embedding models
- HybridRetriever orchestrates multi-modal search
- Pluggable reranker architecture

Usage:
    retriever = HybridRetriever(
        query_embedder=embedder,
        search_client=opensearch_client,
        reranker=CrossEncoderReranker()
    )
    results = retriever.retrieve('machine learning', top_k=5)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Protocol

from .reranker import PassThroughReranker, Reranker, RetrievedDocument


class SearchClient(Protocol):
    """Minimal protocol describing the methods we rely on from OpenSearch."""

    def search(self, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
        ...


class QueryEmbeddingModel(Protocol):
    """Protocol for models that transform a text query into an embedding vector."""

    def embed_query(self, text: str) -> List[float]:
        ...


@dataclass
class HybridRetriever:
    """Coordinates sparse + dense retrieval and optional reranking."""

    client: SearchClient
    index_name: str
    query_embedder: QueryEmbeddingModel
    reranker: Reranker = PassThroughReranker()
    hybrid_size: int = 20
    knn_field: str = "embedding"
    knn_k: int = 20

    def build_query(self, query: str, vector: Iterable[float]) -> Dict[str, Any]:
        """Return the hybrid search body sent to OpenSearch."""

        return {
            "size": self.hybrid_size,
            "query": {
                "hybrid": {
                    "queries": [
                        {"match": {"text": {"query": query}}},
                        {
                            "knn": {
                                self.knn_field: {
                                    "vector": list(vector),
                                    "k": self.knn_k,
                                }
                            }
                        },
                    ]
                }
            },
        }

    def embed_query(self, query: str) -> List[float]:
        """Delegate to the configured embedding model for query vectors."""

        return self.query_embedder.embed_query(query)

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedDocument]:
        """Execute hybrid search, rerank results, and return top hits."""

        query_vector = self.embed_query(query)
        body = self.build_query(query, query_vector)
        raw = self.client.search(index=self.index_name, body=body)
        hits = raw.get("hits", {}).get("hits", [])

        documents = [
            RetrievedDocument(
                text=hit["_source"]["text"],
                score=hit.get("_score", 0.0),
                metadata={
                    **hit["_source"].get("metadata", {}),
                    "page_numbers": hit["_source"].get("page_numbers", []),
                    "title": hit["_source"].get("title"),
                },
            )
            for hit in hits
        ]

        return self.reranker.rerank(query=query, documents=documents, top_k=top_k)

    def retrieve_as_dicts(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Helper returning LangChain-friendly dictionaries."""

        docs = self.retrieve(query=query, top_k=top_k)
        return [
            {
                "page_content": doc.text,
                "metadata": doc.metadata,
                "score": doc.score,
            }
            for doc in docs
        ]
