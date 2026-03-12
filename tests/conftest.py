"""
Pytest Configuration and Test Environment Setup

This module provides centralized pytest configuration for the AI RAG Assistant test suite,
including path setup, fixtures, and common test utilities to ensure consistent
test execution across all test modules.

Features:
- Project root path configuration
- Python path setup for module imports
- Common test fixtures and utilities
- Test environment standardization
- Import path resolution
- Shared test constants
- Test data management
- Cross-module test support

Usage:
    # Automatically loaded by pytest
    pytest tests/
    
    # Run specific test modules
    pytest tests/test_retrieval.py -v
    
    # Run with coverage
    pytest tests/ --cov=rag_pipeline --cov-report=html
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
