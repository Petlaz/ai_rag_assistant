"""Simple retrieval evaluation CLI for Quest Analytics RAG assistant."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv

# Ensure project root import path when executed as a script.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env", override=False)

from rag_pipeline.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from rag_pipeline.indexing.opensearch_client import OpenSearchConfig, create_client
from rag_pipeline.retrieval.retriever import HybridRetriever
from rag_pipeline.retrieval.reranker import PassThroughReranker


def load_queries(path: Path) -> List[Dict[str, str]]:
    """Load evaluation queries from a JSONL or JSON file."""

    if path.suffix == ".jsonl":
        lines = path.read_text().strip().splitlines()
        return [json.loads(line) for line in lines if line.strip()]
    data = json.loads(path.read_text())
    if isinstance(data, dict):
        return data.get("queries", [])
    return data


def mean_reciprocal_rank(relevances: List[bool]) -> float:
    """Compute MRR for a list where each entry marks whether a result is relevant."""

    for idx, rel in enumerate(relevances, start=1):
        if rel:
            return 1.0 / idx
    return 0.0


def precision_at_k(relevances: List[bool], k: int) -> float:
    """Compute P@k given a relevance binary vector."""

    trimmed = relevances[:k]
    if not trimmed:
        return 0.0
    return sum(trimmed) / len(trimmed)


def ensure_retriever(index_name: str) -> HybridRetriever:
    """Create a retriever using environment configuration."""

    host = os.getenv("OPENSEARCH_HOST")
    if not host:
        raise RuntimeError("OPENSEARCH_HOST not set; cannot evaluate retrieval.")

    username = os.getenv("OPENSEARCH_USERNAME", "")
    password = os.getenv("OPENSEARCH_PASSWORD", "")
    tls_verify_env = os.getenv("OPENSEARCH_TLS_VERIFY", "true").lower()
    tls_verify = tls_verify_env not in {"false", "0"}
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

    config = OpenSearchConfig(
        host=host,
        username=username,
        password=password,
        index_name=index_name,
        tls_verify=tls_verify,
    )
    client = create_client(config)
    embedder = SentenceTransformerEmbeddings(model_name=embedding_model_name)

    return HybridRetriever(
        client=client,
        index_name=index_name,
        query_embedder=embedder,
        reranker=PassThroughReranker(),
    )


def evaluate_queries(
    retriever: HybridRetriever,
    queries: Iterable[Dict[str, str]],
    top_k: int,
) -> Dict[str, float]:
    """Run retrieval evaluation across a set of labelled queries."""

    precisions: List[float] = []
    mrrs: List[float] = []
    miss_counter: Counter[str] = Counter()

    for sample in queries:
        question = sample["question"]
        expected = sample.get("expected_answer_snippet") or ""
        relevant_keywords = sample.get("keywords", [])

        docs = retriever.retrieve(question, top_k=top_k)
        relevances: List[bool] = []
        for doc in docs:
            text = doc.text.lower()
            hit = False
            if expected and expected.lower() in text:
                hit = True
            else:
                for keyword in relevant_keywords:
                    if keyword.lower() in text:
                        hit = True
                        break
            relevances.append(hit)

        if not relevances:
            miss_counter[question] += 1
            continue

        precisions.append(precision_at_k(relevances, top_k))
        mrrs.append(mean_reciprocal_rank(relevances))

    return {
        "precision@k": sum(precisions) / len(precisions) if precisions else 0.0,
        "mrr": sum(mrrs) / len(mrrs) if mrrs else 0.0,
        "samples_evaluated": len(precisions),
        "samples_skipped": miss_counter.total(),
    }


def main(argv: Optional[Iterable[str]] = None) -> None:
    """CLI entry point for evaluating retrieval metrics."""

    parser = argparse.ArgumentParser(description="Evaluate retrieval quality.")
    parser.add_argument("dataset", type=Path, help="Path to JSON or JSONL query set.")
    parser.add_argument(
        "--index",
        default=os.getenv("OPENSEARCH_INDEX", "quest-research"),
        help="Target OpenSearch index. Defaults to OPENSEARCH_INDEX env var.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of documents to retrieve for evaluation.",
    )
    args = parser.parse_args(argv)

    retriever = ensure_retriever(index_name=args.index)
    queries = load_queries(args.dataset)
    metrics = evaluate_queries(retriever, queries, top_k=args.top_k)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
