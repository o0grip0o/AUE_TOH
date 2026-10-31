"""Configuration without credentials or import-time provider initialization."""

import os
from dataclasses import dataclass, field


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
