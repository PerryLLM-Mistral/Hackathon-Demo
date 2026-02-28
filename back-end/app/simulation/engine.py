from __future__ import annotations

from typing import Dict, Tuple, List

from app.multi_llm.schemas.world import WorldState, relation_label
from app.multi_llm.schemas.action import Action, ActionType
from app.simulation.rules import relation_delta_for_action, clamp_relation
from app.simulation.types import TurnDelta, RelationDelta


class SimulationEngine:
    """
    Deterministic simulation engine.

    IMPORTANT:
    - This engine does not talk to Postgres.
    - It operates on in-memory WorldState.
    - The DB layer must persist the resulting relation updates.
    """

    def __init__(self):
        self.turn = 0  # In-memory turn counter (NOT in DB)

    def next_turn_number(self) -> int:
        self.turn += 1
        return self.turn

    def apply_actions(self, world: WorldState, actions: List[Action]) -> Tuple[TurnDelta, Dict[int, int]]:
        """
        Apply actions to the world relations.

        Returns:
        - TurnDelta: delta payload for API/WS
        - relation_updates: dict {relation_id: new_value} to persist in DB
        """
        turn = self.next_turn_number()

        # Index relations for quick lookup by unordered pair (min,max)
        pair_to_relation = {}
        for r in world.relations:
            a, b = sorted([r.country_1, r.country_2])
            pair_to_relation[(a, b)] = r

        relation_deltas: List[RelationDelta] = []
        relation_updates: Dict[int, int] = {}

        for action in actions:
            # Only actions that target another country can affect relations
            if action.target_id is None:
                continue

            a, b = sorted([action.actor_id, action.target_id])
            relation_row = pair_to_relation.get((a, b))

            # If relation doesn't exist, the DB layer should create it via /relations
            # For hackathon simplicity, we skip if missing.
            if relation_row is None:
                continue

            old_val = relation_row.value
            delta = relation_delta_for_action(action)
            new_val = clamp_relation(old_val + delta)

            # If no actual change, skip
            if new_val == old_val:
                continue

            # Update in-memory relation row
            relation_row.value = new_val

            # Collect delta for UI/clients
            relation_deltas.append(
                RelationDelta(
                    relation_id=relation_row.id,
                    country_1=relation_row.country_1,
                    country_2=relation_row.country_2,
                    old_value=old_val,
                    new_value=new_val,
                    label=relation_label(new_val),
                )
            )

            # Record update for DB persistence
            relation_updates[relation_row.id] = new_val

        turn_delta = TurnDelta(
            turn=turn,
            actions=[a.model_dump() for a in actions],
            relation_deltas=relation_deltas,
            message="Turn applied",
        )

        return turn_delta, relation_updates