"""Simple ingestion worker that watches a directory for PDFs and indexes them."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Set

from dotenv import load_dotenv

from rag_pipeline.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from rag_pipeline.indexing.opensearch_client import (
    OpenSearchConfig,
    create_client,
    ensure_index,
)
from rag_pipeline.ingestion.pipeline import ingest_and_index_document


def ensure_opensearch(index_name: str) -> any:
    host = os.getenv("OPENSEARCH_HOST")
    if not host:
        raise RuntimeError("OPENSEARCH_HOST environment variable is required.")

    config = OpenSearchConfig(
        host=host,
        username=os.getenv("OPENSEARCH_USERNAME", ""),
        password=os.getenv("OPENSEARCH_PASSWORD", ""),
        index_name=index_name,
        tls_verify=os.getenv("OPENSEARCH_TLS_VERIFY", "true").lower()
        not in {"false", "0"},
    )
    client = create_client(config)

    schema_path = Path(__file__).resolve().parents[1] / "rag_pipeline" / "indexing" / "schema.json"
    if schema_path.exists():
        schema = json.loads(schema_path.read_text())
        ensure_index(client, index_name, schema)

    return client


def ingest_directory(
    directory: Path,
    pattern: str,
    index_name: str,
    sleep_interval: int,
) -> None:
    seen: Set[Path] = set()
    embedder_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    embedder = SentenceTransformerEmbeddings(model_name=embedder_name)
    client = ensure_opensearch(index_name)

    directory = directory.expanduser().resolve()
    print(f"Watching {directory} for pattern '{pattern}'...")

    try:
        while True:
            for path in directory.glob(pattern):
                if path in seen:
                    continue
                try:
                    ingest_and_index_document(
                        path=path,
                        embedding_model=embedder,
                        opensearch_client=client,
                        index_name=index_name,
                    )
                    seen.add(path)
                    print(f"[ok] Ingested {path.name}")
                except Exception as exc:  # pragma: no cover - runtime logging only
                    print(f"[error] Failed to ingest {path}: {exc}")
            time.sleep(sleep_interval)
    except KeyboardInterrupt:
        print("Interrupted; stopping watcher.")


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Watch a directory and ingest PDFs")
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path(os.getenv("INGESTION_INPUT_DIR", "data/raw")),
        help="Directory to watch for new documents",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.pdf",
        help="Glob pattern for files to ingest",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("INGESTION_POLL_INTERVAL", "30")),
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--index",
        type=str,
        default=os.getenv("OPENSEARCH_INDEX", "quest-research"),
        help="Target OpenSearch index",
    )
    args = parser.parse_args()

    ingest_directory(
        directory=args.directory,
        pattern=args.pattern,
        index_name=args.index,
        sleep_interval=args.interval,
    )


if __name__ == "__main__":
    main()
