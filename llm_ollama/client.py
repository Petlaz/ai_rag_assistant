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
    fallback_model: Optional[str] = "gemma3:1b"


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
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 500:
                raise RuntimeError(
                    "Ollama request failed with HTTP 500. The selected model may exceed available "
                    "system memory. Try pulling a smaller model such as 'mistral' or 'llama3:8b'."
                ) from exc
            raise RuntimeError(f"Ollama request to {endpoint} failed: {exc}") from exc
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

        models_to_try = [self.config.model]
        fallback = self.config.fallback_model
        if fallback and fallback not in models_to_try:
            models_to_try.append(fallback)

        last_error: Optional[RuntimeError] = None
        response: Optional[dict] = None

        for idx, model_name in enumerate(models_to_try):
            payload = {
                "model": model_name,
                "messages": messages,
                "stream": stream,
            }
            if options:
                payload["options"] = options

            try:
                response = self._post("/api/chat", payload)
                break
            except RuntimeError as exc:
                last_error = exc
                is_last_attempt = idx == len(models_to_try) - 1
                if is_last_attempt:
                    raise
                print(
                    f"[warn] Ollama model '{model_name}' failed ({exc}). "
                    f"Falling back to '{models_to_try[idx + 1]}'."
                )
                continue

        if response is None:
            # Should only happen if every attempt raised and last attempt raised
            raise last_error  # type: ignore[misc]

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
