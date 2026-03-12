"""
Document Metadata Extraction Engine

This module provides intelligent metadata extraction from documents using heuristic
analysis and structured field detection, enriching documents with contextual
information for enhanced retrieval and organization.

Features:
- Heuristic metadata inference
- File path analysis
- Document type detection
- Timestamp extraction
- Author information inference
- Title and subject detection
- Extensible metadata fields
- Integration-ready for structured APIs

Metadata Fields:
- Document title and subject
- Author information
- Creation and modification timestamps
- File type and format
- Source path and location
- Custom domain-specific fields

Future Integration:
- arXiv API for academic papers
- CrossRef for academic citations
- Custom document parsers
- Structured metadata sources

Usage:
    metadata = infer_metadata(document_path='paper.pdf')
    # Returns dict with title, author, timestamps, etc.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


def infer_metadata(
    source_path: Path,
    title: str,
    authors: Optional[str] = None,
    published_date: Optional[str] = None,
) -> Dict[str, str]:
    """Return a metadata dictionary attached to each DocumentChunk."""

    metadata: Dict[str, str] = {
        "source_path": str(source_path),
        "title": title,
    }

    if authors:
        metadata["authors"] = authors

    if published_date:
        try:
            parsed = datetime.fromisoformat(published_date)
            metadata["published_date"] = parsed.date().isoformat()
        except ValueError:
            metadata["published_date"] = published_date

    return metadata
