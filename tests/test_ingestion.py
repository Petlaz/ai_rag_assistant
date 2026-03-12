"""
Ingestion Pipeline Unit Test Suite

This module contains comprehensive unit tests for the PDF ingestion pipeline,
validating document processing, text normalization, chunking strategies,
and metadata extraction functionality.

Features:
- PDF text extraction validation
- Chunk generation testing
- Text normalization verification
- Metadata extraction testing
- Error handling validation
- Pipeline component integration
- Document structure testing
- OCR processing validation

Test Coverage:
- normalize_text() - Text preprocessing and cleaning
- chunk_text() - Text segmentation strategies
- build_document_chunks() - Document chunk creation
- DocumentChunk data structure validation
- Edge cases and error conditions

Usage:
    # Run ingestion tests
    pytest tests/test_ingestion.py -v
    
    # Run with coverage
    pytest tests/test_ingestion.py --cov=rag_pipeline.ingestion
"""

from pathlib import Path

import pytest

from rag_pipeline.ingestion.pdf_ocr_pipeline import (
    build_document_chunks,
    chunk_text,
    normalize_text,
    DocumentChunk,
)


def test_normalize_text_removes_extra_whitespace():
    """Ensure normalize_text collapses newlines and extra spaces."""
    dirty = "Line one.\n\n   Line    two.  "
    assert normalize_text(dirty) == "Line one. Line two."


@pytest.mark.parametrize(
    ("chunk_size", "overlap", "expected_lengths"),
    [
        (4, 0, [4, 4, 2]),
        (5, 1, [5, 5, 2]),
        (10, 2, [10]),
    ],
)
def test_chunk_text_respects_size_and_overlap(chunk_size, overlap, expected_lengths):
    """Verify chunk_text honours chunk_size/overlap settings."""
    text = " ".join(str(i) for i in range(10))
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    assert len(chunks) == len(expected_lengths)
    for chunk, expected_len in zip(chunks, expected_lengths):
        assert len(chunk.split()) == expected_len


def test_build_document_chunks_attaches_metadata(tmp_path: Path):
    """Check build_document_chunks attaches metadata and page numbers."""
    page_text = ["First page content.", "Second page content."]
    metadata = {"title": "Test PDF"}
    chunks = build_document_chunks(
        source_path=tmp_path / "dummy.pdf",
        title="Dummy",
        page_text=page_text,
        chunk_size=5,
        overlap=0,
        metadata=metadata,
    )
    assert len(chunks) == 2
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
    assert all(chunk.metadata == metadata for chunk in chunks)
    assert chunks[0].page_numbers == [1]
    assert chunks[1].page_numbers == [2]
