"""
Hybrid Indexing Module

This module provides hybrid indexing capabilities combining BM25 sparse retrieval
with dense vector search using OpenSearch, enabling efficient and accurate
document retrieval for RAG systems.

Features:
- Hybrid BM25 + vector index management
- OpenSearch cluster integration
- Bulk document indexing
- Index schema management
- Document clearing and updates
- Connection health monitoring
- Graceful degradation for offline mode
- Production-ready error handling

Components:
- OpenSearch client utilities
- Hybrid indexer for dual-mode storage
- Index schema definition and management
- Bulk operations optimization

Usage:
    from rag_pipeline.indexing import HybridIndexer
    indexer = HybridIndexer(embedding_model, opensearch_client)
    indexer.add_documents(document_chunks, index_name)
"""
