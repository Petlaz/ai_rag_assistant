"""Unit tests for ingestion utilities."""

from pathlib import Path

import pytest

from rag_pipeline.ingestion.pdf_ocr_pipeline import (
    build_document_chunks,
    chunk_text,
    normalize_text,
    DocumentChunk,
)


def test_normalize_text_removes_extra_whitespace():
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
    text = " ".join(str(i) for i in range(10))
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    assert len(chunks) == len(expected_lengths)
    for chunk, expected_len in zip(chunks, expected_lengths):
        assert len(chunk.split()) == expected_len


def test_build_document_chunks_attaches_metadata(tmp_path: Path):
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
