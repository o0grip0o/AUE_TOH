"""Bounded gameplay choices through local Ollama or explicit OpenAI; never execute inputs."""

import asyncio
import json
import math
import time
from dataclasses import dataclass
from typing import Any

import httpx

from ue_agent.config import GameplaySettings, ModelSettings
from ue_agent.llm.ollama_models import get_gameplay_client
from ue_agent.llm.openai_models import get_gameplay_decision_model

INSTRUCTIONS = "Select the best currently legal action using the observed game state."


class DecisionUnavailable(RuntimeError):
    """The controller must use its local fallback rather than execute this decision."""


@dataclass(frozen=True)
class GameplayChoice:
    action: str
    observation_id: str
    confidence: float


async def _ollama_choice(evidence, legal_actions, config, remaining):
    body = json.dumps({
        "model": config.model_id,
        "state": evidence,
        "questions": {"next_action": {
            "type": "choice", "instructions": INSTRUCTIONS, "criteria": legal_actions,
        }},
    }, allow_nan=False, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > 64 * 1024:
        raise ValueError("Ollama decision request exceeds its 64 KiB limit")
    try:
        async with get_gameplay_client(config, timeout=remaining) as client:
            response = await client.post("/v1/systemone", content=body,
                                         headers={"Content-Type": "application/json"})
            response.raise_for_status()
            data = response.json()
        answers = data["answers"]
        if not isinstance(answers, dict) or set(answers) != {"next_action"}:
            raise ValueError("Unexpected answers")
        answer = answers["next_action"]
        if answer["type"] != "choice":
            raise ValueError("Expected a choice")
        return answer["choice"], answer["confidence"]
    except httpx.HTTPError:
        # Never include upstream bodies/URLs, which can echo observations or credentials.
        raise DecisionUnavailable("Local Ollama request failed; check service and model availability") from None
    except (ValueError, TypeError, KeyError):
        raise DecisionUnavailable("Ollama decision was malformed") from None


async def _openai_choice(evidence, legal_actions, config, settings, remaining):
    from openai import APIError

    try:
        async with get_gameplay_decision_model(settings) as client:
            response = await client.decisions.create(
                model=config.model_id,
                input=json.dumps(evidence, allow_nan=False),
                questions=[{
                    "name": "next_action", "type": "choice", "instructions": INSTRUCTIONS,
                    "choices": [{"value": a, "description": d} for a, d in legal_actions.items()],
                }],
                timeout=remaining,
            )
    except APIError:
        raise DecisionUnavailable("OpenAI decision request failed") from None
    if len(response.answers) != 1:
        raise DecisionUnavailable("Expected exactly one gameplay decision")
    answer = response.answers[0]
    if answer.type != "choice" or answer.name != "next_action":
        raise DecisionUnavailable("Gameplay decision was refused or malformed")
    return answer.choice, answer.confidence


async def choose_action(
    observation: dict[str, Any],
    *,
    observation_id: str,
    legal_actions: dict[str, str],
    deadline: float,
    settings: ModelSettings | None = None,
    gameplay_settings: GameplaySettings | None = None,
) -> GameplayChoice:
    """Choose before a monotonic deadline. Default to local Ollama; never switch providers on failure.

    The caller must recheck observation freshness and action legality immediately before execution.
    The local controller owns safe fallback behavior. Confidence is a provider-specific signal,
    not a calibrated probability of correctness or comparable across providers.
    """
    if not observation_id.strip():
        raise ValueError("An observation ID is required")
    remaining = deadline - time.monotonic()
    if not math.isfinite(remaining) or remaining <= 0:
        raise DecisionUnavailable("Gameplay decision deadline has expired")
    config = gameplay_settings or GameplaySettings.from_env()
    max_actions = 26 if config.provider == "ollama" else 255
    if not 2 <= len(legal_actions) <= max_actions or any(not a.strip() for a in legal_actions):
        raise ValueError(f"Provide 2–{max_actions} distinct nonempty legal action IDs")
    evidence = {"observation_id": observation_id, "observation": observation}
    json.dumps(evidence, allow_nan=False)  # Validate before creating a transport client.
    try:
        async with asyncio.timeout(remaining):
            if config.provider == "ollama":
                action, confidence = await _ollama_choice(evidence, legal_actions, config, remaining)
            else:
                action, confidence = await _openai_choice(
                    evidence, legal_actions, config, settings or ModelSettings.from_env(), remaining,
                )
    except TimeoutError:
        raise DecisionUnavailable("Gameplay decision exceeded its deadline") from None
    if time.monotonic() >= deadline:
        raise DecisionUnavailable("Gameplay decision arrived too late")
    if not isinstance(action, str) or action not in legal_actions:
        raise DecisionUnavailable("Gameplay decision selected an unavailable action")
    if (isinstance(confidence, bool) or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence) or not 0 <= confidence <= 1):
        raise DecisionUnavailable("Gameplay decision confidence is invalid")
    return GameplayChoice(action, observation_id, confidence)
