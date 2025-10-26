"""Simple PDF/OCR ingestion scaffolding for the Quest Analytics RAG assistant.

This module keeps the ingestion workflow intentionally lightweight so we can
explain each moving part to new team members.  The real OCR + parsing code will
replace the placeholders once the dependencies (e.g. pdfminer.six, pytesseract,
PaddleOCR) are selected and validated.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dependency during scaffolding
    PdfReader = None


@dataclass
class DocumentChunk:
    """Container for the text and metadata that eventually land in OpenSearch."""

    text: str
    page_numbers: List[int]
    source_path: Path
    title: Optional[str] = None
    metadata: Optional[dict] = None


def load_pdf(path: Path) -> bytes:
    """Read the raw PDF bytes so downstream extractors can operate on memory."""

    return path.read_bytes()


def extract_text_from_pdf(pdf_bytes: bytes) -> List[str]:
    """Return the text per page using a lightweight PDF text extractor."""

    if PdfReader is None:
        raise NotImplementedError(
            "pypdf is required for text extraction. Install dependencies first."
        )

    reader = PdfReader(BytesIO(pdf_bytes))
    page_text: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        page_text.append(text)
    return page_text


def run_ocr_on_pages(pages: Iterable[bytes]) -> List[str]:
    """Fallback to OCR when a page does not expose embedded text (stubbed)."""

    # TODO: integrate Tesseract/PaddleOCR; for now signal the missing feature.
    raise NotImplementedError("OCR extraction not implemented yet.")


def normalize_text(text: str) -> str:
    """Clean whitespace, normalize unicode, and collapse blank lines."""

    normalized = " ".join(text.split())
    return normalized


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split large passages into overlapping chunks suitable for embeddings."""

    tokens: List[str] = text.split()
    chunks: List[str] = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk = " ".join(tokens[start:end])
        chunks.append(chunk)
        if end == len(tokens):
            break
        start = max(end - overlap, 0)

    return chunks


def build_document_chunks(
    source_path: Path,
    title: str,
    page_text: List[str],
    chunk_size: int = 1000,
    overlap: int = 200,
    metadata: Optional[dict] = None,
) -> List[DocumentChunk]:
    """Produce chunk objects with metadata ready for embedding + indexing."""

    chunks: List[DocumentChunk] = []
    for page_idx, raw_text in enumerate(page_text, start=1):
        normalized = normalize_text(raw_text)
        if not normalized:
            continue
        for chunk in chunk_text(normalized, chunk_size, overlap):
            chunks.append(
                DocumentChunk(
                    text=chunk,
                    page_numbers=[page_idx],
                    source_path=source_path,
                    title=title,
                    metadata=metadata,
                )
            )
    return chunks


def ingest_pdf(path: Path, title: Optional[str] = None) -> List[DocumentChunk]:
    """High-level ingestion entry point: load, extract, chunk, and annotate."""

    pdf_bytes = load_pdf(path)
    try:
        page_text = extract_text_from_pdf(pdf_bytes)
    except NotImplementedError:
        # In the scaffold phase we simply propagate the error upward; production
        # code will attempt OCR and merge results back into a page list.
        raise

    title = title or path.stem
    return build_document_chunks(source_path=path, title=title, page_text=page_text)
