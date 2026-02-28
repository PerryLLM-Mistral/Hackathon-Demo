# app/simulation/rules.py

from __future__ import annotations

from app.multi_llm.schemas.action import Action, ActionType


def clamp_relation(value: int) -> int:
    return max(-100, min(100, value))


def clamp_metric(value: int) -> int:
    return max(0, min(100, value))


def relation_delta_for_action(action: Action) -> int:
    """
    Central place to define relation deltas.

    IMPORTANT:
    - PROPOSE_ALLIANCE: 0 (it only creates pending state)
    - RESPOND_ALLIANCE: +/-20 independent of intensity
    - SANCTION: -50 * intensity
    - DECLARE_WAR: -100 (directly clamps to -100 in engine)
    - TRADE: +15 * intensity
    """
    if action.type == ActionType.PROPOSE_ALLIANCE:
        return 0

    if action.type == ActionType.RESPOND_ALLIANCE:
        accepted = bool(getattr(action, "accept", False))
        return +20 if accepted else -20

    if action.type == ActionType.SANCTION:
        return -50 * action.intensity

    if action.type == ActionType.DECLARE_WAR:
        # relation will be clamped to -100 anyway
        return -100

    if action.type == ActionType.TRADE:
        return +15 * action.intensity

    # PASS has no effect
    return 0