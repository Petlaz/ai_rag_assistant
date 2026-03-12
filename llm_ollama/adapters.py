"""
Ollama Integration Adapters

This module provides high-level adapters and convenience wrappers for integrating
the Ollama local LLM runtime into RAG applications, offering simplified chat interfaces
and environment-based configuration management.

Features:
- Chat-style message interface for Ollama
- Environment variable configuration
- Automatic fallback model management
- Simple message formatting and handling
- Integration with OllamaClient for low-level operations
- Error handling and recovery mechanisms
- Production-ready chat adapters
- Flexible configuration options

Usage:
    # Create adapter from environment
    adapter = OllamaChatAdapter.from_env(
        base_url="http://localhost:11434",
        model="llama3:8b",
        fallback_model="gemma3:1b"
    )
    
    # Send chat messages
    response = adapter.invoke_messages([
        {"role": "user", "content": "What is machine learning?"}
    ])
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from .client import OllamaClient, OllamaConfig


@dataclass
class OllamaChatAdapter:
    """
    High-Level Chat Interface for Ollama Integration
    
    Provides a simplified chat-style interface for interacting with Ollama models,
    handling message formatting, response processing, and error management with
    automatic fallback support.
    
    Features:
    - Chat message list processing
    - Environment-based configuration
    - Automatic fallback model support
    - Error handling and recovery
    - Options passing for model parameters
    - Streaming and non-streaming modes
    
    Attributes:
        client: Underlying OllamaClient for API communication
    """

    client: OllamaClient

    @classmethod
    def from_env(
        cls,
        base_url: str,
        model: str,
        timeout: float = 30.0,
        fallback_model: Optional[str] = None,
    ) -> "OllamaChatAdapter":
        """
        Create OllamaChatAdapter from environment configuration.
        
        Convenience constructor that builds adapter configuration from
        environment variables with sensible defaults and fallback handling.
        
        Args:
            base_url: Ollama server base URL
            model: Primary model name to use
            timeout: Request timeout in seconds
            fallback_model: Optional fallback model (defaults to env var)
            
        Returns:
            Configured OllamaChatAdapter instance
        """

        fallback = (
            fallback_model
            if fallback_model is not None
            else os.getenv("OLLAMA_FALLBACK_MODEL", "gemma3:1b") or None
        )
        config = OllamaConfig(
            base_url=base_url,
            model=model,
            timeout=timeout,
            fallback_model=fallback,
        )
        return cls(client=OllamaClient(config))

    def invoke_messages(
        self,
        messages: List[Dict[str, str]],
        options: Optional[Dict] = None,
    ) -> str:
        """
        Send chat messages to Ollama and get response.
        
        Processes a list of chat messages through the Ollama client,
        handling formatting, options, and error recovery automatically.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            options: Optional model parameters (temperature, top_p, etc.)
            
        Returns:
            Generated response text from Ollama
            
        Raises:
            RuntimeError: If generation fails and fallback is unavailable
            ModelNotFoundError: If specified model is not found
        """

        return self.client.generate(messages=messages, stream=False, options=options)
