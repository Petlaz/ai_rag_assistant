"""CLI for ingesting PDFs into the Quest Analytics RAG pipeline."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, Optional

from rag_pipeline.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from rag_pipeline.indexing.opensearch_client import (
    OpenSearchConfig,
    create_client,
    ensure_index,
)
from rag_pipeline.ingestion.pipeline import ingest_and_index_document

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "rag_pipeline" / "indexing" / "schema.json"


def _ensure_client(index_name: str):
    host = os.getenv("OPENSEARCH_HOST")
    if not host:
        raise RuntimeError("OPENSEARCH_HOST is not set. Unable to connect to OpenSearch.")

    username = os.getenv("OPENSEARCH_USERNAME", "")
    password = os.getenv("OPENSEARCH_PASSWORD", "")
    tls_verify_env = os.getenv("OPENSEARCH_TLS_VERIFY", "true").lower()
    tls_verify = tls_verify_env not in {"false", "0"}

    config = OpenSearchConfig(
        host=host,
        username=username,
        password=password,
        index_name=index_name,
        tls_verify=tls_verify,
    )
    client = create_client(config)
    if SCHEMA_PATH.exists():
        schema = json.loads(SCHEMA_PATH.read_text())
        ensure_index(client, index_name, schema)
    return client


def ingest_paths(paths: Iterable[Path], index_name: str) -> None:
    """Ingest each provided PDF path into OpenSearch for retrieval."""

    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    embedding_model = SentenceTransformerEmbeddings(model_name=embedding_model_name)
    client = _ensure_client(index_name=index_name)

    for path in paths:
        if not path.exists():
            print(f"[skip] {path} does not exist.")
            continue
        try:
            ingest_and_index_document(
                path=path,
                embedding_model=embedding_model,
                opensearch_client=client,
                index_name=index_name,
            )
            print(f"[ok] Ingested {path}")
        except Exception as exc:  # pragma: no cover - CLI surface
            print(f"[error] Failed to ingest {path}: {exc}")


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Parse CLI arguments and kick off ingestion for provided PDFs."""

    parser = argparse.ArgumentParser(description="Ingest PDFs into OpenSearch.")
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="One or more PDF files to ingest.",
    )
    parser.add_argument(
        "--index",
        default=os.getenv("OPENSEARCH_INDEX", "quest-research"),
        help="Target OpenSearch index (defaults to OPENSEARCH_INDEX).",
    )
    args = parser.parse_args(argv)
    ingest_paths(args.paths, index_name=args.index)


if __name__ == "__main__":
    main()
