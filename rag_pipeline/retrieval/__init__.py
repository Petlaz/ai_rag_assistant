"""
Intelligent Retrieval Module

This module provides advanced retrieval capabilities combining hybrid search
(BM25 + vector similarity) with sophisticated reranking strategies to deliver
highly relevant documents for RAG-based question answering.

Features:
- Hybrid retrieval (BM25 + semantic search)
- Multi-stage reranking strategies
- Cross-encoder relevance scoring
- Query embedding optimization
- Configurable ranking weights
- Performance monitoring
- Graceful fallback mechanisms
- Production-ready error handling

Components:
- HybridRetriever for multi-modal search
- Reranker implementations (PassThrough, CrossEncoder)
- Document scoring and ranking
- Query processing pipeline

Usage:
    from rag_pipeline.retrieval import HybridRetriever
    retriever = HybridRetriever(embedder, search_client, reranker)
    results = retriever.retrieve('query text', top_k=5)
"""
