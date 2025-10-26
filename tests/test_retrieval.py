"""Unit tests for hybrid retriever behavior."""

from typing import Any, Dict

import pytest

from rag_pipeline.retrieval.retriever import HybridRetriever, RetrievedDocument
from rag_pipeline.retrieval.reranker import PassThroughReranker


class DummyQueryEmbedder:
    def embed_query(self, text: str):
        return [0.1, 0.2, 0.3]


class DummySearchClient:
    def __init__(self, hits: Dict[str, Any]):
        self._hits = hits

    def search(self, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
        self.last_index = index  # type: ignore[attr-defined]
        self.last_body = body  # type: ignore[attr-defined]
        return self._hits


def build_hits() -> Dict[str, Any]:
    return {
        "hits": {
            "hits": [
                {
                    "_score": 1.5,
                    "_source": {
                        "text": "Transformer models use attention.",
                        "metadata": {"title": "Attention Is All You Need"},
                        "page_numbers": [5],
                        "title": "Attention Is All You Need",
                    },
                },
                {
                    "_score": 1.2,
                    "_source": {
                        "text": "BERT pre-training uses masked language modeling.",
                        "metadata": {"title": "BERT"},
                        "page_numbers": [10],
                        "title": "BERT",
                    },
                },
            ]
        }
    }


def test_retrieve_returns_documents_with_metadata():
    client = DummySearchClient(build_hits())
    retriever = HybridRetriever(
        client=client,
        index_name="quest-research",
        query_embedder=DummyQueryEmbedder(),
        reranker=PassThroughReranker(),
    )

    docs = retriever.retrieve("What is attention?", top_k=2)
    assert len(docs) == 2
    assert isinstance(docs[0], RetrievedDocument)
    assert docs[0].metadata["title"] == "Attention Is All You Need"
    assert docs[0].metadata["page_numbers"] == [5]
    assert client.last_body["query"]["hybrid"]["queries"][1]["knn"]["embedding"]["k"] == 20


def test_retrieve_as_dicts_formats_langchain_documents():
    client = DummySearchClient(build_hits())
    retriever = HybridRetriever(
        client=client,
        index_name="quest-research",
        query_embedder=DummyQueryEmbedder(),
        reranker=PassThroughReranker(),
    )

    docs = retriever.retrieve_as_dicts("Explain BERT", top_k=1)
    assert len(docs) == 1
    doc = docs[0]
    assert "page_content" in doc
    assert doc["metadata"]["title"] == "Attention Is All You Need" or doc["metadata"]["title"] == "BERT"
