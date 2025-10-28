"""Tests for Ollama client fallback behaviour."""

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
