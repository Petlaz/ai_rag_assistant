"""OpenSearch client helpers centralizing connection and index utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable

try:
    from opensearchpy import OpenSearch
    from opensearchpy.helpers import bulk as opensearch_bulk
except ImportError:  # pragma: no cover - optional dependency
    OpenSearch = None  # type: ignore[assignment]
    opensearch_bulk = None  # type: ignore[assignment]


@dataclass
class OpenSearchConfig:
    """Configuration values needed to connect to the OpenSearch cluster."""

    host: str
    username: str
    password: str
    index_name: str
    tls_verify: bool = True
    use_ssl: bool | None = None


def create_client(config: OpenSearchConfig):
    """Instantiate the OpenSearch client with sensible defaults."""

    if OpenSearch is None:
        raise ImportError(
            "opensearch-py must be installed to create an OpenSearch client."
        )

    if config.host.startswith("http"):
        hosts = [config.host]
    else:
        hosts = [{"host": config.host}]

    client = OpenSearch(
        hosts=hosts,
        http_auth=(config.username, config.password) if config.username else None,
        verify_certs=config.tls_verify,
        use_ssl=config.use_ssl if config.use_ssl is not None else config.host.startswith(
            "https"
        ),
    )
    return client


def ensure_index(client: Any, index_name: str, mapping: Dict[str, Any]) -> None:
    """Create the index with the provided mapping if it does not already exist."""

    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, body=mapping)


def bulk_index_documents(
    client: Any, index_name: str, documents: Iterable[Dict[str, Any]]
) -> None:
    """Send documents to OpenSearch using the bulk API (stub)."""

    if opensearch_bulk is None:
        raise ImportError(
            "opensearch-py helpers are required for bulk indexing operations."
        )

    actions = ({"_index": index_name, **doc} for doc in documents)
    opensearch_bulk(client, actions)
