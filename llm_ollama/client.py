"""Lightweight Ollama HTTP client used by the Quest Analytics RAG stack."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests


logger = logging.getLogger(__name__)


class ModelNotFoundError(RuntimeError):
    """Raised when the requested Ollama model cannot be located."""


@dataclass
class OllamaHealth:
    """Represents the outcome of a lightweight Ollama health probe."""

    healthy: bool
    status_code: Optional[int]
    latency_ms: Optional[float]
    error: Optional[str] = None


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
            if status == 404:
                raise ModelNotFoundError(
                    f"Ollama endpoint {endpoint} returned HTTP 404."
                ) from exc
            raise RuntimeError(f"Ollama request to {endpoint} failed: {exc}") from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama request to {endpoint} failed: {exc}") from exc
        return response.json()

    def health_check(self) -> OllamaHealth:
        """Ping the Ollama server; return structured health metadata."""

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
