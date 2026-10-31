"""Gameplay policy contract tests with a fake endpoint; no API calls or game required."""

import asyncio
import time
from types import SimpleNamespace

import pytest

from ue_agent import decisions
from ue_agent.config import ModelSettings


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
