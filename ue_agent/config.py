"""Configuration without credentials or import-time provider initialization."""

import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit


@dataclass(frozen=True)
class GameplaySettings:
    """Local gameplay decisions are the only exception to the OpenAI provider policy."""

    provider: str = "ollama"
    model: str | None = None
    ollama_url: str = "http://127.0.0.1:11434"

    def __post_init__(self):
        if self.provider not in {"ollama", "openai"}:
            raise ValueError("Gameplay provider must be ollama or openai")
        if self.model is not None and not self.model.strip():
            raise ValueError("Gameplay model ID must not be empty")
        if self.provider == "openai" and self.model_id != "gpt-6-luna":
            raise ValueError("OpenAI Decisions currently requires gpt-6-luna")
        url = urlsplit(self.ollama_url)
        if (url.scheme != "http" or url.hostname not in {"localhost", "127.0.0.1", "::1"}
                or url.username is not None or url.password is not None
                or url.path not in {"", "/"} or url.query or url.fragment):
            raise ValueError("Ollama must use a loopback HTTP URL without credentials or a path")
        _ = url.port  # Validate port syntax before any request.

    @property
    def model_id(self):
        return self.model or ("nimble" if self.provider == "ollama" else "gpt-6-luna")

    @classmethod
    def from_env(cls):
        return cls(
            provider=os.environ.get("UE_AGENT_GAMEPLAY_PROVIDER", "ollama").strip(),
            model=os.environ.get("UE_AGENT_GAMEPLAY_MODEL", "").strip() or None,
            ollama_url=os.environ.get("UE_AGENT_OLLAMA_URL", "http://127.0.0.1:11434").strip(),
        )


@dataclass(frozen=True)
class ModelSettings:
    model: str
    role_models: dict[str, str] = field(default_factory=dict)
    embedding_model: str | None = None
    timeout: float = 60.0
    max_retries: int = 2

    def __post_init__(self):
        if not self.model.strip():
            raise ValueError("An OpenAI model ID is required")
        if self.timeout <= 0 or self.max_retries < 0:
            raise ValueError("Model timeout must be positive and retries nonnegative")

    def for_role(self, role):
        return self.role_models.get(role, self.model)

    @classmethod
    def from_env(cls):
        model = os.environ.get("UE_AGENT_MODEL", "").strip()
        if not model:
            raise ValueError("Set UE_AGENT_MODEL to the OpenAI model you want to use")
        roles = {}
        for role in ("supervisor", "vision"):
            value = os.environ.get(f"UE_AGENT_{role.upper()}_MODEL", "").strip()
            if value:
                roles[role] = value
        return cls(model=model, role_models=roles,
                   embedding_model=os.environ.get("UE_AGENT_EMBEDDING_MODEL") or None)
