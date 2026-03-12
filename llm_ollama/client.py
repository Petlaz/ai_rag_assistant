"""
Ollama HTTP Client for Local LLM Integration

This module provides a lightweight, production-ready HTTP client for communicating
with the local Ollama runtime, supporting model management, health monitoring,
and robust error handling with fallback mechanisms.

Features:
- Lightweight REST API client for Ollama
- Model availability checking and management
- Health monitoring and status reporting
- Automatic fallback model support
- Comprehensive error handling with context
- Request timeout and retry logic
- Model listing and introspection
- Production-ready logging and debugging

Components:
- OllamaClient: Core HTTP client for API communication
- OllamaConfig: Configuration management for client setup
- OllamaHealth: Health check results and monitoring
- ModelNotFoundError: Custom exception for missing models

Usage:
    # Configure and create client
    config = OllamaConfig(
        base_url="http://localhost:11434",
        model="llama3:8b",
        fallback_model="gemma3:1b"
    )
    client = OllamaClient(config)
    
    # Check health
    health = client.health_check()
    
    # Generate responses
    response = client.generate(messages=messages)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests


logger = logging.getLogger(__name__)


class ModelNotFoundError(RuntimeError):
    """
    Custom Exception for Missing Ollama Models
    
    Raised when a requested Ollama model cannot be located or accessed,
    providing clear error context for model availability issues.
    """
    pass


@dataclass
class OllamaHealth:
    """
    Ollama Service Health Status Information
    
    Represents comprehensive health check results for the Ollama service,
    including connectivity status, performance metrics, and error details.
    
    Attributes:
        healthy: Boolean indicating overall service health
        status_code: HTTP status code from health check
        latency_ms: Response latency in milliseconds
        error: Error message if health check failed
    """

    healthy: bool
    status_code: Optional[int]
    latency_ms: Optional[float]
    error: Optional[str] = None


@dataclass
class OllamaConfig:
    """
    Ollama Client Configuration Settings
    
    Comprehensive configuration for Ollama client connections, including
    connection parameters, model selection, and fallback strategies.
    
    Attributes:
        base_url: Ollama server base URL (e.g., http://localhost:11434)
        model: Primary model name to use for generation
        timeout: Request timeout in seconds
        fallback_model: Fallback model name for error recovery
    """

    base_url: str
    model: str
    timeout: float = 30.0
    fallback_model: Optional[str] = "gemma3:1b"


class OllamaClient:
    """
    Production-Ready Ollama HTTP API Client
    
    Robust HTTP client for communicating with local Ollama runtime, providing
    comprehensive error handling, health monitoring, and automatic fallback
    capabilities for reliable LLM integration.
    
    Features:
    - RESTful API communication with Ollama
    - Automatic error detection and recovery
    - Model availability checking
    - Health monitoring and diagnostics
    - Fallback model support
    - Comprehensive logging and debugging
    - Request timeout and retry handling
    
    Methods:
        generate: Generate text responses from prompts/messages
        health_check: Monitor service health and availability
        list_models: Get available model information
    """

    def __init__(self, config: OllamaConfig):
        self.config = config

    def _post(self, endpoint: str, payload: dict) -> dict:
        """
        Send HTTP POST request to Ollama API with error handling.
        
        Internal method for making POST requests to Ollama endpoints with
        comprehensive error handling, context preservation, and meaningful
        error messages for debugging.
        
        Args:
            endpoint: API endpoint path (e.g., '/api/generate')
            payload: JSON payload to send in request body
            
        Returns:
            Parsed JSON response from Ollama API
            
        Raises:
            RuntimeError: For HTTP errors and connection issues
            ModelNotFoundError: For 404 model not found errors
        """

        url = f"{self.config.base_url.rstrip('/')}{endpoint}"
        try:
            response = requests.post(url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 500:
                raise RuntimeError(
                    "Ollama request failed with HTTP 500. The selected model may exceed available "
                    "system memory. Try pulling a smaller model such as 'mistral' or 'llama3:8b'."
                ) from exc
            if status == 404:
                raise ModelNotFoundError(
                    f"Ollama endpoint {endpoint} returned HTTP 404."
                ) from exc
            raise RuntimeError(f"Ollama request to {endpoint} failed: {exc}") from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama request to {endpoint} failed: {exc}") from exc
        return response.json()

    def health_check(self) -> OllamaHealth:
        """
        Perform comprehensive Ollama service health check.
        
        Checks Ollama service availability, response time, and overall health
        status by querying the models endpoint and measuring performance.
        
        Returns:
            OllamaHealth object with detailed health information including:
            - Service availability status
            - Response latency metrics
            - HTTP status codes
            - Error details if unhealthy
            
        Note:
            This method does not require model loading and provides fast
            health status suitable for monitoring and diagnostics.
        """

        start = time.perf_counter()
        try:
            response = requests.get(
                f"{self.config.base_url.rstrip('/')}/api/tags",
                timeout=self.config.timeout,
            )
            latency_ms = (time.perf_counter() - start) * 1000.0
            response.raise_for_status()
            return OllamaHealth(
                healthy=True,
                status_code=response.status_code,
                latency_ms=latency_ms,
            )
        except requests.RequestException as exc:
            latency_ms = (time.perf_counter() - start) * 1000.0
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            return OllamaHealth(
                healthy=False,
                status_code=status_code,
                latency_ms=latency_ms,
                error=str(exc),
            )

    def generate(
        self,
        messages: List[dict],
        stream: bool = False,
        options: Optional[dict] = None,
    ) -> str:
        """Invoke Ollama's chat endpoint and concatenate the response."""

        def _invoke(model_name: str, allow_pull: bool = True) -> dict:
            payload = {
                "model": model_name,
                "messages": messages,
                "stream": stream,
            }
            if options:
                payload["options"] = options
            try:
                return self._post("/api/chat", payload)
            except ModelNotFoundError as not_found:
                if not allow_pull:
                    raise
                if model_name == "mistral":
                    logger.warning(
                        "mistral manifest missing — attempting auto-pull before fallback."
                    )
                else:
                    logger.warning(
                        "Ollama model '%s' missing — attempting auto-pull before fallback.",
                        model_name,
                    )
                try:
                    self._pull_model(model_name)
                except Exception as pull_exc:
                    logger.error(
                        "Auto-pull for model '%s' failed: %s",
                        model_name,
                        pull_exc,
                    )
                    raise not_found from pull_exc
                return _invoke(model_name, allow_pull=False)

        primary_model = self.config.model
        fallback_model = (
            self.config.fallback_model
            if self.config.fallback_model and self.config.fallback_model != primary_model
            else None
        )

        try:
            response = _invoke(primary_model)
        except RuntimeError as exc:
            if not fallback_model:
                raise
            logger.warning(
                "Primary Ollama model '%s' failed (%s). Trying fallback '%s'.",
                primary_model,
                exc,
                fallback_model,
            )
            response = _invoke(fallback_model)
            # Promote fallback to become the active model for subsequent calls.
            self.config.model = fallback_model

        if stream:
            raise NotImplementedError("Streaming responses are not handled yet.")

        message = response.get("message", {})
        return message.get("content", "")

    def embed(self, texts: Iterable[str], options: Optional[dict] = None) -> List[List[float]]:
        """Call the embeddings endpoint to obtain vectors for each text."""

        vectors: List[List[float]] = []
        for text in texts:
            payload = {
                "model": self.config.model,
                "prompt": text,
            }
            if options:
                payload["options"] = options

            response = self._post("/api/embeddings", payload)
            embedding = response.get("embedding")
            if embedding is None:
                raise ValueError("Ollama embedding response missing 'embedding' key.")
            vectors.append(embedding)
        return vectors

    def _pull_model(self, model_name: str) -> None:
        """Attempt to pull a model via the Ollama HTTP API."""

        url = f"{self.config.base_url.rstrip('/')}/api/pull"
        timeout = max(self.config.timeout, 120.0)
        with requests.post(
            url,
            json={"model": model_name},
            timeout=timeout,
            stream=True,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                if data.get("error"):
                    raise RuntimeError(data["error"])
                status = data.get("status", "").lower()
                if status in {"success", "exists", "already exists"}:
                    logger.info("Auto-pull for model '%s' completed.", model_name)
                    return
        raise RuntimeError(f"Ollama pull for model '{model_name}' did not complete successfully.")
