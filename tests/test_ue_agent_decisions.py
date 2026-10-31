"""Gameplay policy contract tests with a fake endpoint; no API calls or game required."""

import asyncio
import time
from types import SimpleNamespace

import pytest

from ue_agent import decisions
from ue_agent.config import GameplaySettings, ModelSettings


def run_choice(monkeypatch, answer, *, delay=0, deadline=None):
    seen = {}

    class Client:
        decisions = None

        def __init__(self):
            self.decisions = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            seen["closed"] = True

        async def create(self, **kwargs):
            seen.update(kwargs)
            if delay:
                await asyncio.sleep(delay)
            return SimpleNamespace(answers=[SimpleNamespace(**answer)])

    monkeypatch.setattr(decisions, "get_gameplay_decision_model", lambda _: Client())
    result = asyncio.run(decisions.choose_action(
        {"health": 20}, observation_id="frame-12", legal_actions={"guard": "Block", "retreat": "Back away"},
        gameplay_settings=GameplaySettings(provider="openai"),
        settings=ModelSettings("planner-model"), deadline=deadline or time.monotonic() + 1,
    ))
    return result, seen


def test_selects_a_legal_action_with_decisions_not_chat(monkeypatch):
    result, seen = run_choice(monkeypatch, {
        "type": "choice", "name": "next_action", "choice": "guard", "confidence": .8,
    })
    assert result == decisions.GameplayChoice("guard", "frame-12", .8)
    assert seen["model"] == "gpt-6-luna"
    assert seen["questions"][0]["choices"] == [
        {"value": "guard", "description": "Block"}, {"value": "retreat", "description": "Back away"},
    ]
    assert '"observation_id": "frame-12"' in seen["input"]
    assert seen["closed"]


@pytest.mark.parametrize("change", [
    {"type": "refusal"}, {"name": "wrong"}, {"choice": "attack"},
    {"choice": True}, {"confidence": float("nan")}, {"confidence": 2},
])
def test_rejects_refusals_illegal_choices_and_invalid_confidence(monkeypatch, change):
    answer = {"type": "choice", "name": "next_action", "choice": "guard", "confidence": .8} | change
    with pytest.raises(decisions.DecisionUnavailable):
        run_choice(monkeypatch, answer)


def test_timeout_does_not_produce_an_action(monkeypatch):
    with pytest.raises(decisions.DecisionUnavailable, match="deadline"):
        run_choice(monkeypatch, {}, delay=.1, deadline=time.monotonic() + .01)


def test_expired_observation_is_rejected_before_a_request(monkeypatch):
    monkeypatch.setattr(decisions, "get_gameplay_decision_model", lambda _: pytest.fail("must not create a client"))
    with pytest.raises(decisions.DecisionUnavailable, match="expired"):
        asyncio.run(decisions.choose_action(
            {}, observation_id="old", legal_actions={"a": "A", "b": "B"},
            settings=ModelSettings("model"), deadline=time.monotonic() - 1,
        ))


def local_choice(monkeypatch, handler, *, actions=None, timeout=1):
    import httpx

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(decisions, "get_gameplay_decision_model", lambda _: pytest.fail("no cloud fallback"))
    monkeypatch.setattr(decisions, "get_gameplay_client", lambda config, timeout: httpx.AsyncClient(
        base_url=config.ollama_url, transport=httpx.MockTransport(handler), trust_env=False,
    ))
    return asyncio.run(decisions.choose_action(
        {"health": 20}, observation_id="frame-12", legal_actions=actions or {"guard": "Block", "retreat": "Back away"},
        gameplay_settings=GameplaySettings(), deadline=time.monotonic() + timeout,
    ))


def test_local_route_needs_no_openai_key_and_uses_systemone_schema(monkeypatch):
    import json

    import httpx

    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"answers": {
            "next_action": {"type": "choice", "choice": "guard", "confidence": .7},
        }})

    assert local_choice(monkeypatch, handler) == decisions.GameplayChoice("guard", "frame-12", .7)
    request = seen[0]
    assert str(request.url) == "http://127.0.0.1:11434/v1/systemone"
    assert "authorization" not in request.headers
    payload = json.loads(request.content)
    assert payload["model"] == "nimble"
    assert payload["state"]["observation_id"] == "frame-12"
    assert payload["questions"]["next_action"]["criteria"] == {"guard": "Block", "retreat": "Back away"}


@pytest.mark.parametrize("body", [
    [], {}, {"answers": []}, {"answers": {"next_action": None}},
    {"answers": {"next_action": {"type": "refusal"}}},
    {"answers": {"next_action": {"type": "choice", "choice": "attack", "confidence": .8}}},
    {"answers": {"next_action": {"type": "choice", "choice": "guard", "confidence": "0.8"}}},
])
def test_local_malformed_or_illegal_response_never_executes_or_falls_back(monkeypatch, body):
    import httpx

    with pytest.raises(decisions.DecisionUnavailable):
        local_choice(monkeypatch, lambda _: httpx.Response(200, json=body))


@pytest.mark.parametrize("status", [302, 404, 500])
def test_local_http_errors_do_not_fall_back_or_expose_upstream_details(monkeypatch, status):
    import httpx

    with pytest.raises(decisions.DecisionUnavailable) as error:
        local_choice(monkeypatch, lambda _: httpx.Response(status, text="sensitive observation"))
    assert "sensitive" not in str(error.value)


def test_local_deadline_cancels_a_slow_endpoint(monkeypatch):
    import httpx

    async def handler(request):
        await asyncio.sleep(.1)
        return httpx.Response(200, json={})

    with pytest.raises(decisions.DecisionUnavailable, match="deadline"):
        local_choice(monkeypatch, handler, timeout=.01)


def test_local_option_limit_is_enforced_before_transport(monkeypatch):
    with pytest.raises(ValueError, match="2–26"):
        local_choice(monkeypatch, lambda _: pytest.fail("no request"), actions={str(n): str(n) for n in range(27)})


def test_local_payload_limit_is_enforced_before_transport(monkeypatch):
    with pytest.raises(ValueError, match="64 KiB"):
        local_choice(monkeypatch, lambda _: pytest.fail("no request"), actions={"a": "x" * 65536, "b": "B"})


@pytest.mark.parametrize("kwargs", [
    {"provider": "unknown"}, {"model": " "}, {"provider": "openai", "model": "nimble"},
    {"ollama_url": "https://other-provider.invalid"}, {"ollama_url": "http://user:secret@localhost:11434"},
    {"ollama_url": "http://localhost:11434/path"}, {"ollama_url": "http://localhost:invalid"},
])
def test_invalid_gameplay_config_is_rejected(kwargs):
    with pytest.raises(ValueError):
        GameplaySettings(**kwargs)


def test_gameplay_configuration_and_model_selection_are_separate_from_chat(monkeypatch):
    for name in ("UE_AGENT_GAMEPLAY_PROVIDER", "UE_AGENT_GAMEPLAY_MODEL", "UE_AGENT_OLLAMA_URL", "UE_AGENT_MODEL"):
        monkeypatch.delenv(name, raising=False)
    assert GameplaySettings.from_env().model_id == "nimble"
    monkeypatch.setenv("UE_AGENT_GAMEPLAY_MODEL", "nimble:verified-local-tag")
    assert GameplaySettings.from_env().model_id == "nimble:verified-local-tag"
    monkeypatch.setenv("UE_AGENT_GAMEPLAY_PROVIDER", "openai")
    monkeypatch.delenv("UE_AGENT_GAMEPLAY_MODEL")
    assert GameplaySettings.from_env().model_id == "gpt-6-luna"


def test_local_client_ignores_proxy_and_never_inherits_openai_auth(monkeypatch):
    from ue_agent.llm.ollama_models import get_gameplay_client

    monkeypatch.setenv("ALL_PROXY", "socks5://invalid:1")
    monkeypatch.setenv("OPENAI_API_KEY", "private-test-key")
    client = get_gameplay_client(GameplaySettings(), timeout=1)
    assert client.trust_env is False
    assert client.follow_redirects is False
    assert "authorization" not in client.headers
    asyncio.run(client.aclose())
