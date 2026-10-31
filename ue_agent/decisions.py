"""Bounded gameplay choices through OpenAI Decisions; no engine actions are executed here."""

import asyncio
import json
import math
import time
from dataclasses import dataclass
from typing import Any

from ue_agent.config import ModelSettings
from ue_agent.llm.openai_models import get_gameplay_decision_model

DECISION_MODEL = "gpt-6-luna"


class DecisionUnavailable(RuntimeError):
    """The controller must use its local fallback rather than execute this decision."""


@dataclass(frozen=True)
class GameplayChoice:
    action: str
    observation_id: str
    confidence: float


async def choose_action(
    observation: dict[str, Any],
    *,
    observation_id: str,
    legal_actions: dict[str, str],
    settings: ModelSettings,
    deadline: float,
) -> GameplayChoice:
    """Select a legal action before a monotonic deadline; never send or time controller inputs.

    The caller must recheck observation freshness and action legality immediately before execution.
    No fallback action is guessed here: the local controller owns safe fallback behavior.
    """
    if not observation_id.strip():
        raise ValueError("An observation ID is required")
    if not 2 <= len(legal_actions) <= 255 or any(not a.strip() for a in legal_actions):
        raise ValueError("Provide 2–255 distinct nonempty legal action IDs")
    remaining = deadline - time.monotonic()
    if not math.isfinite(remaining) or remaining <= 0:
        raise DecisionUnavailable("Gameplay decision deadline has expired")
    evidence = json.dumps({"observation_id": observation_id, "observation": observation}, allow_nan=False)
    client = get_gameplay_decision_model(settings)
    try:
        async with client:
            async with asyncio.timeout(remaining):
                response = await client.decisions.create(
                    model=DECISION_MODEL,
                    input=evidence,
                    questions=[{
                        "name": "next_action", "type": "choice",
                        "instructions": "Select the best currently legal action using the observed game state.",
                        "choices": [{"value": a, "description": d} for a, d in legal_actions.items()],
                    }],
                    timeout=remaining,
                )
    except TimeoutError:
        raise DecisionUnavailable("Gameplay decision exceeded its deadline") from None
    # Also reject an endpoint or mock that returned after the deadline without cancellation.
    if time.monotonic() >= deadline:
        raise DecisionUnavailable("Gameplay decision arrived too late")
    if len(response.answers) != 1:
        raise DecisionUnavailable("Expected exactly one gameplay decision")
    answer = response.answers[0]
    if answer.type != "choice" or answer.name != "next_action":
        raise DecisionUnavailable("Gameplay decision was refused or malformed")
    if not isinstance(answer.choice, str) or answer.choice not in legal_actions:
        raise DecisionUnavailable("Gameplay decision selected an unavailable action")
    if not math.isfinite(answer.confidence) or not 0 <= answer.confidence <= 1:
        raise DecisionUnavailable("Gameplay decision confidence is invalid")
    return GameplayChoice(answer.choice, observation_id, answer.confidence)
