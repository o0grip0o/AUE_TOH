"""Local Ollama transport construction. This module never downloads or loads models."""

import httpx

from ue_agent.config import GameplaySettings


def get_gameplay_client(settings: GameplaySettings, *, timeout: float):
    # Local decisions must not use inherited proxies or follow redirects to another provider.
    return httpx.AsyncClient(base_url=settings.ollama_url.rstrip("/"), timeout=timeout,
                             trust_env=False, follow_redirects=False)
