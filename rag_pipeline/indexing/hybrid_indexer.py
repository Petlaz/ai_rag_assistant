"""Hybrid index writer that combines sparse text and dense embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol

from .opensearch_client import bulk_index_documents, clear_index_documents
from ..ingestion.pdf_ocr_pipeline import DocumentChunk


class EmbeddingModel(Protocol):
    """Protocol describing the minimal surface we expect from embed models."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        ...


@dataclass
class IndexedDocument:
    """Prepared document ready for OpenSearch bulk indexing."""

    id: str
    body: dict


def prepare_documents(
    chunks: Iterable[DocumentChunk], embeddings: Iterable[List[float]]
) -> List[IndexedDocument]:
    """Pair chunk text with embedding vectors and metadata for indexing."""

    indexed_docs: List[IndexedDocument] = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        doc_id = f"{chunk.source_path.name}-{idx}"
        body = {
            "text": chunk.text,
            "embedding": embedding,
            "metadata": chunk.metadata or {},
            "page_numbers": chunk.page_numbers,
            "title": chunk.title,
        }
        indexed_docs.append(IndexedDocument(id=doc_id, body=body))
    return indexed_docs


def index_chunks(
    client,
    index_name: str,
    chunks: Iterable[DocumentChunk],
    embedding_model: EmbeddingModel,
    clear_previous: bool = False,
) -> None:
    """Embed the chunks and dispatch them to OpenSearch via the bulk API.
    
    Args:
        clear_previous: If True, clear all previous documents from the index before adding new ones.
    """
    
    if clear_previous:
        clear_index_documents(client, index_name)

    texts = [chunk.text for chunk in chunks]
    embeddings = embedding_model.embed_documents(texts)
    documents = prepare_documents(chunks, embeddings)
    payload = ({"_id": doc.id, "_source": doc.body} for doc in documents)
    bulk_index_documents(client=client, index_name=index_name, documents=payload)
