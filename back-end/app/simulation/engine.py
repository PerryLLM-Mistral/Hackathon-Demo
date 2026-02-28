# app/simulation/engine.py

from __future__ import annotations

from typing import Optional

from app.multi_llm.schemas.world import WorldState, RelationState
from app.multi_llm.schemas.action import Action, ActionType
from app.simulation.effects import get_effect


def clamp_int(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def find_relation(world: WorldState, a: str, b: str) -> Optional[RelationState]:
    for r in world.relations:
        if (r.country_1 == a and r.country_2 == b) or (r.country_1 == b and r.country_2 == a):
            return r
    return None


def ensure_relation(world: WorldState, a: str, b: str) -> RelationState:
    rel = find_relation(world, a, b)
    if rel is not None:
        return rel

    new_id = max((r.id for r in world.relations), default=0) + 1
    # pending_alliance_from is expected to exist in RelationState after your schema change.
    rel = RelationState(id=new_id, country_1=a, country_2=b, relation=0, pending_alliance_from=None)
    world.relations.append(rel)
    return rel


def find_country(world: WorldState, country_id: str):
    for c in world.countries:
        if c.id == country_id:
            return c
    return None


def apply_action(world: WorldState, action: Action) -> None:
    """
    Applies quantitative actions to the world.

    Quantitative-only policy:
    - PASS: no-op
    - PROPOSE_ALLIANCE: creates pending alliance request state (no direct numeric deltas)
    - RESPOND_ALLIANCE: applies +/- relation delta and clears pending
    - Others: apply effects from effects.py, scaled by intensity when appropriate
    """
    if action.type == ActionType.PASS:
        return

    # For anything but PASS we expect a target (PROPOSE/RESPOND/WAR/TRADE/SANCTION)
    if not action.target_id:
        return

    rel = ensure_relation(world, action.actor_id, action.target_id)

    # 1) Proposal: only sets pending state, no numeric effects
    if action.type == ActionType.PROPOSE_ALLIANCE:
        # No permitir spam: si ya hay una petición pendiente en este par, no haces nada.
        if getattr(rel, "pending_alliance_from", None) is not None:
            return

        rel.pending_alliance_from = action.actor_id
        if hasattr(rel, "pending_alliance_turn"):
            rel.pending_alliance_turn = world.turn
        return

    # 2) Response: apply +/-20 and clear pending
    if action.type == ActionType.RESPOND_ALLIANCE:
        eff = get_effect(action)
        rel.relation = clamp_int(rel.relation + eff.relation, -100, 100)
        rel.pending_alliance_from = None
        return

    # 3) Other actions: apply base effects scaled by intensity
    eff = get_effect(action)

    # Relation change
    rel.relation = clamp_int(rel.relation + eff.relation * action.intensity, -100, 100)

    # Country metric deltas (simple symmetric application for demo)
    actor = find_country(world, action.actor_id)
    target = find_country(world, action.target_id)
    if actor is None or target is None:
        return

    for entity in (actor, target):
        entity.economy = clamp_int(entity.economy + eff.economy * action.intensity, 0, 100)
        entity.social = clamp_int(entity.social + eff.social * action.intensity, 0, 100)
        entity.demography = clamp_int(entity.demography + eff.demography * action.intensity, 0, 100)
        entity.technology = clamp_int(entity.technology + eff.technology * action.intensity, 0, 100)
        entity.military_power = clamp_int(entity.military_power + eff.military_power * action.intensity, 0, 100)