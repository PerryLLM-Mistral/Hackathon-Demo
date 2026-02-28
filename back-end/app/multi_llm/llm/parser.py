from __future__ import annotations

import json
from typing import Any

from app.multi_llm.schemas.action import Action


def parse_action_from_text(text: str) -> Action:
    """
    Parse raw LLM output into an Action.

    Expectation:
    - LLM returns a single JSON object matching Action fields.
    - If parsing fails, raise ValueError (orchestrator/guardrails can fallback).
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM output is not valid JSON: {e}")

    if not isinstance(data, dict):
        raise ValueError("LLM output must be a JSON object")

    # actor_id may be missing/hallucinated; orchestrator overwrites it anyway
    # but we keep it required by schema, so provide a placeholder if absent.
    if "actor_id" not in data:
        data["actor_id"] = -1

    return Action.model_validate(data)