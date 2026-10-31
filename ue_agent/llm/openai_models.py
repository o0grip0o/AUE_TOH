"""The sole construction boundary for OpenAI models and clients.

Getters create clients lazily. Importing the package, inspecting a job, and the offline
demo do not need credentials. No key is retained in configuration or persisted state.
"""

import os

from ue_agent.config import ModelSettings

OPENAI_URL = "https://api.openai.com/v1"


def _client_settings(settings):
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("Set OPENAI_API_KEY before using an OpenAI-backed agent")
    return {"api_key": key, "base_url": OPENAI_URL,
            "timeout": settings.timeout, "max_retries": settings.max_retries}


def get_specialist_model(role: str, settings: ModelSettings):
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=settings.for_role(role), **_client_settings(settings))


def get_supervisor_model(settings: ModelSettings):
    return get_specialist_model("supervisor", settings)


def get_gameplay_decision_model(settings: ModelSettings):
    """Return the dedicated AsyncOpenAI client used by the gameplay decision policy."""
    # Decisions uses a dedicated endpoint, not LangChain chat completions.
    # No retries: stale gameplay decisions must not be replayed after a timeout.
    from openai import AsyncOpenAI

    options = _client_settings(settings)
    options["max_retries"] = 0
    return AsyncOpenAI(**options)


def get_vision_model(settings: ModelSettings):
    return get_specialist_model("vision", settings)


def get_embedding_model(settings: ModelSettings):
    from langchain_openai import OpenAIEmbeddings

    if not settings.embedding_model:
        raise ValueError("Set UE_AGENT_EMBEDDING_MODEL before enabling semantic retrieval")
    return OpenAIEmbeddings(model=settings.embedding_model, **_client_settings(settings))


def get_image_client(settings: ModelSettings):
    from openai import AsyncOpenAI

    return AsyncOpenAI(**_client_settings(settings))


def get_audio_client(settings: ModelSettings):
    from openai import AsyncOpenAI

    return AsyncOpenAI(**_client_settings(settings))
