from __future__ import annotations

from app.multi_llm.schemas.action import Action, ActionType


def clamp_relation(value: int) -> int:
    """
    Clamp relation value to [-100, 100].
    """
    return max(-100, min(100, value))


def relation_delta_for_action(action: Action) -> int:
    """
    Returns how much to change relation.value based on ActionType and intensity.

    This is the *only* place you tune diplomacy math.
    """
    base = action.intensity

    # You can tune these coefficients anytime without touching agents.
    if action.type == ActionType.DECLARE_WAR:
        return -35 * base
    if action.type == ActionType.ALLY:
        return +30 * base
    if action.type == ActionType.TRADE:
        return +15 * base
    if action.type == ActionType.SANCTION:
        return -20 * base

    # MESSAGE and PASS do not change relations
    return 0