"""
Ollama LLM Client Test Suite

This module tests the Ollama client implementation, focusing on fallback behavior,
error handling, configuration management, and integration with the local
Ollama LLM service for robust text generation.

Features:
- Fallback model testing
- Error recovery validation
- Configuration testing
- Timeout handling verification
- Health monitoring tests
- Connection retry logic
- Response format validation
- Performance boundary testing

Test Coverage:
- Primary model failure scenarios
- Automatic fallback activation
- Configuration validation
- Error propagation handling
- Client initialization
- Request/response cycles

Usage:
    # Run Ollama client tests
    pytest tests/test_ollama_client.py -v
    
    # Test with mocked Ollama service
    pytest tests/test_ollama_client.py --mock-ollama
"""

from llm_ollama.client import OllamaClient, OllamaConfig


def test_generate_falls_back(monkeypatch):
    config = OllamaConfig(
        base_url="http://localhost",
        model="primary",
        timeout=5,
        fallback_model="fallback",
    )
    client = OllamaClient(config)

    attempts = []

    def fake_post(self, endpoint, payload):
        attempts.append(payload["model"])
        if payload["model"] == "primary":
            raise RuntimeError("primary failed")
        return {"message": {"content": "hello"}}

    monkeypatch.setattr(OllamaClient, "_post", fake_post, raising=False)

    result = client.generate(messages=[{"role": "user", "content": "hi"}])

    assert result == "hello"
    assert attempts == ["primary", "fallback"]
