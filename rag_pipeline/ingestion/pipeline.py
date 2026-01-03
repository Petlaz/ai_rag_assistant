"""Glue code that connects ingestion, metadata enrichment, and indexing."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .metadata_extractor import infer_metadata
from .pdf_ocr_pipeline import DocumentChunk, ingest_pdf
from ..indexing.hybrid_indexer import EmbeddingModel, index_chunks


def ingest_and_index_document(
    path: Path,
    embedding_model: EmbeddingModel,
    opensearch_client,
    index_name: str,
    title: Optional[str] = None,
    authors: Optional[str] = None,
    published_date: Optional[str] = None,
    clear_previous: bool = False,
) -> None:
    """Orchestrate the full flow from PDF ingestion to OpenSearch indexing.
    
    Args:
        clear_previous: If True, clear all previous documents from the index before adding new ones.
    """

    chunks = ingest_pdf(path=path, title=title)

    metadata = infer_metadata(
        source_path=path, title=title or path.stem, authors=authors, published_date=published_date
    )

    for chunk in chunks:
        chunk.metadata = dict(metadata)

    index_chunks(
        client=opensearch_client,
        index_name=index_name,
        chunks=chunks,
        embedding_model=embedding_model,
        clear_previous=clear_previous,
    )
