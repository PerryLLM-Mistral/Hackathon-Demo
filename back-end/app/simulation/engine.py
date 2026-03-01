# app/simulation/engine.py
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.multi_llm.schemas.world import WorldState, RelationState
from app.multi_llm.schemas.action import Action, ActionType
from app.simulation.effects import get_effect
from app.simulation.state_store import load_world_state, persist_turn_actions


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
    rel = RelationState(id=new_id, country_1=a, country_2=b, relation=0, pending_alliance_from=None)
    world.relations.append(rel)
    return rel


def find_country(world: WorldState, country_id: str):
    for c in world.countries:
        if c.id == country_id:
            return c
    return None


def apply_action(world: WorldState, action: Action) -> None:
    if action.type == ActionType.PASS:
        return

    if not action.target_id:
        return

    rel = ensure_relation(world, action.actor_id, action.target_id)

    if action.type == ActionType.PROPOSE_ALLIANCE:
        if getattr(rel, "pending_alliance_from", None) is not None:
            return
        rel.pending_alliance_from = action.actor_id
        if hasattr(rel, "pending_alliance_turn"):
            rel.pending_alliance_turn = world.turn
        return

    if action.type == ActionType.RESPOND_ALLIANCE:
        eff = get_effect(action)
        rel.relation = clamp_int(rel.relation + eff.relation, -100, 100)
        rel.pending_alliance_from = None
        if hasattr(rel, "pending_alliance_turn"):
            rel.pending_alliance_turn = None
        return

    eff = get_effect(action)
    rel.relation = clamp_int(rel.relation + eff.relation * action.intensity, -100, 100)

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


class SimulationEngine:
    """
    Stateful engine for FastAPI:

    - Holds in-memory WorldState (good for websocket live view)
    - Loads initial state from DB once (countries + relationships)
    - Writes Turn + ActionHistory every step (append-only action stream)
    """

    def __init__(self):
        self._world: Optional[WorldState] = None

    def ensure_loaded(self, db: Session, run_id: str) -> None:
        if self._world is None:
            self._world = load_world_state(db, run_id=run_id)

    def get_state(self) -> WorldState:
        if self._world is None:
            # caller should have called ensure_loaded
            return WorldState(turn=0, countries=[], relations=[])
        return self._world

    def apply(self, db: Session, run_id: str, actions: list[Action], order: Optional[list[str]] = None):
        """
        Apply actions in-memory + persist action stream.

        Returns:
          delta payload for websocket/UI
        """
        world = self.get_state()

        # apply in memory
        for action in actions:
            apply_action(world, action)

        # persist Turn + ActionHistory (write-only stream)
        turn_id = persist_turn_actions(
            db=db,
            run_id=run_id,
            turn_number=world.turn,
            order=order,
            actions=actions,
        )

        # advance in-memory turn
        world.turn += 1

        return {
            "run_id": run_id,
            "turn_id": turn_id,
            "turn": world.turn,
            "actions": [a.model_dump() for a in actions],
            "world": world,
        }