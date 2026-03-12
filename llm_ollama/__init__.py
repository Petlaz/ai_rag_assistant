"""
Ollama Local LLM Integration Module

This module provides comprehensive integration with the Ollama local LLM runtime,
offering both low-level HTTP client capabilities and high-level chat adapters
for seamless integration into RAG applications.

Features:
- Local Ollama runtime integration
- HTTP client with robust error handling
- Health monitoring and status checking
- Automatic fallback model support
- Chat-style message interfaces
- Environment-based configuration
- Production-ready logging and debugging
- Model availability checking

Components:
- client.py: Core Ollama HTTP client and configuration
- adapters.py: High-level chat adapters and convenience wrappers
- OllamaClient: Low-level API communication
- OllamaChatAdapter: Simplified chat interface

Usage:
    from llm_ollama import OllamaClient, OllamaChatAdapter, OllamaConfig
    
    # Direct client usage
    config = OllamaConfig(base_url="http://localhost:11434", model="llama3:8b")
    client = OllamaClient(config)
    
    # High-level chat adapter
    adapter = OllamaChatAdapter.from_env(
        base_url="http://localhost:11434",
        model="llama3:8b"
    )
"""

# Import main classes for easy access
from .client import OllamaClient, OllamaConfig, OllamaHealth, ModelNotFoundError
from .adapters import OllamaChatAdapter

__all__ = [
    'OllamaClient',
    'OllamaConfig', 
    'OllamaHealth',
    'ModelNotFoundError',
    'OllamaChatAdapter'
]