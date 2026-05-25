#!/usr/bin/env python3
"""
Bootstrap OpenSearch indices for CI/CD workflows.

This script creates the necessary indices and mappings in OpenSearch
to prepare for integration testing and model validation workflows.

Usage:
    python scripts/bootstrap_opensearch.py [--index-name INDEX]
"""

import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_pipeline.indexing.opensearch_client import (
    OpenSearchConfig,
    create_client,
    ensure_index,
)


def load_schema(schema_path: Path) -> dict:
    """Load OpenSearch schema from JSON file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return json.load(f)


def wait_for_opensearch(config: OpenSearchConfig, max_attempts: int = 30, delay: float = 1.0) -> bool:
    """Wait for OpenSearch cluster to be ready.
    
    Args:
        config: OpenSearch connection configuration
        max_attempts: Maximum number of connection attempts
        delay: Seconds to wait between attempts
    
    Returns:
        True if cluster is ready, False if timeout occurred
    """
    print(f"Waiting for OpenSearch at {config.host}...")
    
    for attempt in range(max_attempts):
        try:
            client = create_client(config)
            # Test connection with ping
            if client.ping():
                print(f"✓ OpenSearch is ready (attempt {attempt + 1}/{max_attempts})")
                return True
        except Exception as e:
            print(f"  Attempt {attempt + 1}/{max_attempts}: {type(e).__name__}")
        
        if attempt < max_attempts - 1:
            time.sleep(delay)
    
    print(f"✗ OpenSearch did not respond after {max_attempts} attempts")
    return False


def bootstrap_indices(index_names: list[str]) -> None:
    """Bootstrap OpenSearch indices for testing.
    
    Args:
        index_names: List of index names to create
    """
    # Load configuration from environment
    host = os.getenv("OPENSEARCH_HOST", "localhost:9200")
    username = os.getenv("OPENSEARCH_USER", "admin")
    password = os.getenv("OPENSEARCH_PASSWORD", "")
    tls_verify = os.getenv("OPENSEARCH_TLS_VERIFY", "false").lower() not in {"false", "0"}
    
    config = OpenSearchConfig(
        host=host,
        username=username,
        password=password,
        index_name="",  # Will set per index
        tls_verify=tls_verify,
    )
    
    # Wait for cluster to be ready
    if not wait_for_opensearch(config):
        print("ERROR: OpenSearch cluster did not start in time")
        sys.exit(1)
    
    # Load schema
    schema_path = PROJECT_ROOT / "rag_pipeline" / "indexing" / "schema.json"
    schema = load_schema(schema_path)
    
    # Connect and create indices
    try:
        client = create_client(config)
        
        for index_name in index_names:
            print(f"Creating index: {index_name}")
            try:
                ensure_index(client, index_name, schema)
                print(f"✓ Index '{index_name}' created/verified")
            except Exception as e:
                print(f"✗ Failed to create index '{index_name}': {e}")
                sys.exit(1)
        
        print("\n✓ Bootstrap completed successfully")
        
    except Exception as e:
        print(f"ERROR: Failed to bootstrap OpenSearch: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Bootstrap OpenSearch indices for testing"
    )
    parser.add_argument(
        "--index-name",
        default=os.getenv("OPENSEARCH_INDEX", "quest-research"),
        help="OpenSearch index name (default: quest-research)"
    )
    parser.add_argument(
        "--additional-indices",
        nargs="+",
        default=[],
        help="Additional index names to create"
    )
    
    args = parser.parse_args()
    
    # Combine primary and additional indices
    indices = [args.index_name] + args.additional_indices
    
    print("=" * 60)
    print("OpenSearch Bootstrap Script")
    print("=" * 60)
    print(f"Host: {os.getenv('OPENSEARCH_HOST', 'localhost:9200')}")
    print(f"Indices to create: {', '.join(indices)}")
    print("=" * 60)
    print()
    
    bootstrap_indices(indices)


if __name__ == "__main__":
    main()
