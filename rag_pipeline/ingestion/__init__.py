"""
Document Ingestion Module

This module provides comprehensive document ingestion capabilities, including PDF
processing, OCR text extraction, metadata extraction, and document chunking
strategies optimized for RAG system performance.

Features:
- PDF document processing
- OCR text extraction
- Metadata extraction and enrichment
- Intelligent document chunking
- Text normalization and cleaning
- Batch processing support
- Error handling and recovery
- Session isolation capabilities

Components:
- PDF OCR pipeline for text extraction
- Metadata extractor for document enrichment
- Document chunking strategies
- Pipeline orchestration

Usage:
    from rag_pipeline.ingestion import DocumentProcessor
    processor = DocumentProcessor()
    chunks = processor.process_pdf('document.pdf')
"""
