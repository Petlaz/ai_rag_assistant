"""Adapters that allow the rest of the codebase to talk to Ollama easily."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from .client import OllamaClient, OllamaConfig


@dataclass
class OllamaChatAdapter:
    """Simple helper to wrap chat-style calls to Ollama."""

    client: OllamaClient

    @classmethod
    def from_env(
        cls,
        base_url: str,
        model: str,
        timeout: float = 30.0,
        fallback_model: Optional[str] = None,
    ) -> "OllamaChatAdapter":
        """Convenience constructor for callers that only have env vars."""

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
        """Send a pre-built message list to the Ollama client."""

        return self.client.generate(messages=messages, stream=False, options=options)
