"""
RAG Pipeline Core Module

This package provides the core RAG (Retrieval-Augmented Generation) pipeline components
for the AI Assistant, including document ingestion, embedding generation, hybrid indexing,
and intelligent retrieval with reranking capabilities.

Components:
- Ingestion: PDF processing, OCR, and document chunking
- Embeddings: Vector representation generation using sentence transformers
- Indexing: Hybrid BM25 + vector storage with OpenSearch integration
- Retrieval: Multi-stage retrieval with reranking and relevance scoring
- Prompts: Template management for research-focused query processing

Architecture:
- Modular design for component independence
- Protocol-based interfaces for extensibility
- Graceful degradation for external dependencies
- Production-ready error handling and logging

Usage:
    from rag_pipeline.ingestion import DocumentProcessor
    from rag_pipeline.retrieval import HybridRetriever
    from rag_pipeline.embeddings import SentenceTransformerEmbeddings
"""
