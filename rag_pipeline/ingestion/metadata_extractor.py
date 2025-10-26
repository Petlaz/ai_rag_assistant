"""Metadata helpers used by the ingestion workflow.

We keep the surface area tiny for now: a single function returns a dictionary
of metadata fields derived from heuristics.  When we integrate document parsers
that expose structured fields (e.g. arXiv API, CrossRef), those values can
replace the heuristics below.
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
