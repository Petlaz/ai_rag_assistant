"""Lightweight Ollama HTTP client used by the Quest Analytics RAG stack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests


@dataclass
class OllamaConfig:
    """Configuration required to talk to the local Ollama runtime."""

    base_url: str
    model: str
    timeout: float = 30.0


class OllamaClient:
    """Thin wrapper around the Ollama REST API."""

    def __init__(self, config: OllamaConfig):
        self.config = config

    def _post(self, endpoint: str, payload: dict) -> dict:
        """Send a POST request and surface HTTP errors with context."""

        url = f"{self.config.base_url.rstrip('/')}{endpoint}"
        try:
            response = requests.post(url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama request to {endpoint} failed: {exc}") from exc
        return response.json()

    def health_check(self) -> bool:
        """Ping the Ollama server; return True when reachable."""

        try:
            response = requests.get(
                f"{self.config.base_url.rstrip('/')}/api/tags",
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def generate(
        self,
        messages: List[dict],
        stream: bool = False,
        options: Optional[dict] = None,
    ) -> str:
        """Invoke Ollama's chat endpoint and concatenate the response."""

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": stream,
        }
        if options:
            payload["options"] = options

        response = self._post("/api/chat", payload)

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
