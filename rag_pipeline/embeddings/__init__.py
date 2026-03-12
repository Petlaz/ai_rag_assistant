"""
Embedding Generation Module

This module provides embedding utilities for converting text into dense vector
representations using state-of-the-art sentence transformer models, supporting
both query and document embedding for semantic search.

Features:
- Sentence transformer model integration
- Batch processing for efficiency
- GPU acceleration support
- Model caching and optimization
- Consistent vector dimensions
- Error handling for model loading

Supported Models:
- all-MiniLM-L6-v2 (384 dims, fast)
- all-mpnet-base-v2 (768 dims, quality)
- multi-qa-MiniLM-L6-cos-v1 (384 dims, QA optimized)

Usage:
    from rag_pipeline.embeddings import SentenceTransformerEmbeddings
    embedder = SentenceTransformerEmbeddings('all-MiniLM-L6-v2')
    vectors = embedder.embed_documents(['text1', 'text2'])
"""
