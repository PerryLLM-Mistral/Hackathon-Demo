# app/simulation/effects.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from app.multi_llm.schemas.action import Action, ActionType


@dataclass(frozen=True)
class MetricDelta:
    """
    Base deltas (per intensity unit unless stated otherwise).
    Relation is always clamped to [-100, 100] in the engine.
    Country metrics are clamped to [0, 100] in the engine.
    """
    relation: int = 0
    economy: int = 0
    social: int = 0
    demography: int = 0
    technology: int = 0
    military_power: int = 0


# NOTE:
# - PROPOSE_ALLIANCE has no direct quantitative effect (it creates pending state in engine).
# - RESPOND_ALLIANCE is conditional (accept vs reject) so it is handled in get_effect().
EFFECTS_BY_ACTION: Dict[ActionType, MetricDelta] = {
    ActionType.DECLARE_WAR: MetricDelta(relation=-100, economy=-10, social=-8, military_power=-5),
    ActionType.SANCTION:    MetricDelta(relation=-50, economy=-12, social=-3),
    ActionType.TRADE:       MetricDelta(relation=+15, economy=+8, technology=+2),
    ActionType.PROPOSE_ALLIANCE: MetricDelta(),  # no direct delta
    ActionType.PASS:        MetricDelta(),
}


def get_effect(action: Action) -> MetricDelta:
    """
    Returns the base delta for an action.

    RESPOND_ALLIANCE is conditional:
      - accept=True  -> relation +20
      - accept=False -> relation -20
    """
    if action.type == ActionType.RESPOND_ALLIANCE:
        # If somehow accept is missing, treat as reject (safe default).
        accepted = bool(getattr(action, "accept", False))
        return MetricDelta(relation=(+20 if accepted else -20))

    return EFFECTS_BY_ACTION.get(action.type, MetricDelta())