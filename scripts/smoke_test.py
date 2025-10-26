"""Smoke test for the Quest Analytics AI RAG assistant."""

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
from rag_pipeline.retrieval.retriever import HybridRetriever
from rag_pipeline.retrieval.reranker import PassThroughReranker

from llm_ollama.adapters import OllamaChatAdapter

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "rag_pipeline" / "indexing" / "schema.json"


def ensure_opensearch(index_name: str):
    """Connect to OpenSearch and ensure the hybrid index schema exists."""

    host = os.getenv("OPENSEARCH_HOST")
    if not host:
        raise RuntimeError("OPENSEARCH_HOST environment variable is required.")

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


def ensure_chat_adapter() -> OllamaChatAdapter:
    """Instantiate the Ollama chat adapter using environment configuration."""

    base_url = os.getenv("OLLAMA_BASE_URL")
    model = os.getenv("OLLAMA_MODEL")
    if not base_url or not model:
        raise RuntimeError("OLLAMA_BASE_URL and OLLAMA_MODEL must be configured.")
    timeout = float(os.getenv("OLLAMA_TIMEOUT", "30"))
    return OllamaChatAdapter.from_env(base_url=base_url, model=model, timeout=timeout)


def smoke_test(pdf_path: Optional[Path], question: Optional[str], index_name: str) -> None:
    """Run ingestion + retrieval + LLM generation to validate dependencies."""

    embedding_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    embedder = SentenceTransformerEmbeddings(model_name=embedding_name)

    opensearch_client = ensure_opensearch(index_name)
    chat_adapter = ensure_chat_adapter()

    retriever = HybridRetriever(
        client=opensearch_client,
        index_name=index_name,
        query_embedder=embedder,
        reranker=PassThroughReranker(),
    )

    if pdf_path:
        print(f"[info] ingesting {pdf_path} ...")
        ingest_and_index_document(
            path=pdf_path,
            embedding_model=embedder,
            opensearch_client=opensearch_client,
            index_name=index_name,
        )
        print("[ok] ingestion completed")

    query = question or "Summarize the key findings."
    print(f"[info] running retrieval for: {query}")
    documents = retriever.retrieve(query, top_k=3)
    if not documents:
        raise RuntimeError("No documents retrieved; ensure the index has data.")

    context = []
    for idx, doc in enumerate(documents, start=1):
        pages = doc.metadata.get("page_numbers", []) if doc.metadata else []
        context.append(f"[Doc {idx}] pages={pages} -> {doc.text[:120]}...")
    print("[ok] retrieved documents:\n" + "\n".join(context))

    messages = [
        {"role": "system", "content": "You are a helpful research assistant."},
        {
            "role": "user",
            "content": f"Question: {query}\n\nContext:\n" + "\n\n".join([doc.text for doc in documents]),
        },
    ]
    response = chat_adapter.invoke_messages(messages)
    print("[ok] LLM response:\n" + response)


def main(argv: Optional[Iterable[str]] = None) -> None:
    """CLI wrapper for running the smoke test with optional overrides."""

    parser = argparse.ArgumentParser(description="Run smoke test for AI RAG assistant")
    parser.add_argument("--pdf", type=Path, help="Optional PDF file to ingest during the test")
    parser.add_argument("--question", type=str, help="Optional question for retrieval")
    parser.add_argument("--index", type=str, default=os.getenv("OPENSEARCH_INDEX", "quest-research"))
    args = parser.parse_args(argv)

    smoke_test(pdf_path=args.pdf, question=args.question, index_name=args.index)


if __name__ == "__main__":
    main()
