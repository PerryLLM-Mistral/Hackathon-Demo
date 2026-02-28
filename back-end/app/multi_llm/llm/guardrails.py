from __future__ import annotations

from app.multi_llm.schemas.action import Action, ActionType
from app.multi_llm.schemas.world import WorldState


def enforce_action_guardrails(action: Action, world: WorldState) -> Action:
    """
    Enforces additional runtime constraints beyond Pydantic validation.

    Example:
    - target_id must exist in world
    - actor_id must exist in world
    - if invalid, fallback to PASS
    """
    country_ids = {c.id for c in world.countries}

    # Actor must exist
    if action.actor_id not in country_ids:
        return Action(actor_id=action.actor_id, type=ActionType.PASS, reason="Invalid actor_id", intensity=1)

    # If action requires a target, it must exist
    if action.target_id is not None and action.target_id not in country_ids:
        return Action(actor_id=action.actor_id, type=ActionType.PASS, reason="Invalid target_id", intensity=1)

    # Prevent self-targeting (also handled by schema validator, but keep safe)
    if action.target_id is not None and action.target_id == action.actor_id:
        return Action(actor_id=action.actor_id, type=ActionType.PASS, reason="Self-targeting blocked", intensity=1)

    return action