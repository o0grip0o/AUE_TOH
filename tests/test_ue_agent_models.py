"""Provider construction stays centralized and does not perform requests on import."""

import ast
from pathlib import Path

import pytest

from ue_agent.config import ModelSettings
from ue_agent.llm import openai_models


def test_getters_use_configured_roles_and_official_openai_endpoint(monkeypatch):
    import langchain_openai

    seen = []
    monkeypatch.setenv("OPENAI_API_KEY", "private-test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://unapproved-provider.invalid/v1")
    monkeypatch.setattr(langchain_openai, "ChatOpenAI", lambda **kwargs: seen.append(kwargs) or kwargs)
    settings = ModelSettings("default-model", {"supervisor": "planner-model", "behavior": "behavior-model"})
    openai_models.get_supervisor_model(settings)
    openai_models.get_specialist_model("behavior", settings)
    openai_models.get_vision_model(settings)
    assert [r["model"] for r in seen] == ["planner-model", "behavior-model", "default-model"]
    assert all(r["base_url"] == "https://api.openai.com/v1" for r in seen)
    assert all(r["api_key"] == "private-test-key" for r in seen)
    assert "private-test-key" not in repr(settings)


def test_image_audio_and_embedding_construction_uses_the_same_boundary(monkeypatch):
    import langchain_openai
    import openai

    monkeypatch.setenv("OPENAI_API_KEY", "private-test-key")
    monkeypatch.setattr(openai, "AsyncOpenAI", lambda **kwargs: kwargs)
    monkeypatch.setattr(langchain_openai, "OpenAIEmbeddings", lambda **kwargs: kwargs)
    settings = ModelSettings("model", embedding_model="embedding-model")
    decision = openai_models.get_gameplay_decision_model(settings)
    assert decision["max_retries"] == 0
    assert decision["base_url"] == openai_models.OPENAI_URL
    assert openai_models.get_image_client(settings)["base_url"] == openai_models.OPENAI_URL
    assert openai_models.get_audio_client(settings)["base_url"] == openai_models.OPENAI_URL
    assert openai_models.get_embedding_model(settings)["model"] == "embedding-model"


def test_missing_configuration_fails_before_a_provider_request(monkeypatch):
    monkeypatch.delenv("UE_AGENT_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="UE_AGENT_MODEL"):
        ModelSettings.from_env()
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        openai_models.get_supervisor_model(ModelSettings("model"))
    with pytest.raises(ValueError, match="EMBEDDING_MODEL"):
        openai_models.get_embedding_model(ModelSettings("model"))


def test_real_sdk_objects_construct_offline_with_test_credentials(monkeypatch):
    import asyncio

    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    # This test never sends a request; host proxy configuration must not add optional transport requirements.
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-offline-foundation-test-not-a-real-key")
    settings = ModelSettings("offline-model", embedding_model="offline-embedding")
    assert isinstance(openai_models.get_supervisor_model(settings), ChatOpenAI)
    assert isinstance(openai_models.get_embedding_model(settings), OpenAIEmbeddings)
    client = openai_models.get_audio_client(settings)
    assert str(client.base_url) == openai_models.OPENAI_URL + "/"
    asyncio.run(client.close())


def test_provider_constructors_and_legacy_imports_are_not_scattered():
    root = Path(__file__).resolve().parents[1] / "ue_agent"
    constructor_names = {"ChatOpenAI", "OpenAIEmbeddings", "OpenAI", "AsyncOpenAI"}
    violations = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                assert not any(n == "autopilot" or n.startswith("autopilot.") for n in names)
            if isinstance(node, ast.Call) and path.name != "openai_models.py":
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if name in constructor_names:
                    violations.append(str(path.relative_to(root)))
    assert violations == []
