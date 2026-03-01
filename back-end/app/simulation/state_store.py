# app/simulation/state_store.py
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.multi_llm.schemas.world import WorldState, CountryState, RelationState
from app.multi_llm.schemas.action import Action
from app.src.models.models import Country, Relationship, Turn, ActionHistory

def load_world_state(db: Session, run_id: str) -> WorldState:
    """
    Load initial world state from DB.

    Read-only sources:
      - countries (current)
      - relationships (current)

    Turn number:
      - if there are previous turns for this run_id, continue from max(turn_number)+1
      - else start at 0
    """
    # turn = next turn number for this run
    last_turn = (
        db.query(func.max(Turn.turn_number))
        .filter(Turn.run_id == run_id)
        .scalar()
    )
    turn_number = int(last_turn + 1) if last_turn is not None else 0

    # Only selected countries
    countries_db = (
        db.query(Country)
        .filter(Country.selected.is_(True))
        .order_by(Country.id.asc())
        .all()
    )

    selected_ids = {c.id for c in countries_db}

    # Only relationships between selected countries
    rels_db = (
        db.query(Relationship)
        .filter(
            Relationship.country_1.in_(selected_ids),
            Relationship.country_2.in_(selected_ids),
        )
        .order_by(Relationship.id.asc())
        .all()
    )

    countries: List[CountryState] = [
        CountryState(
            id=c.id,
            name=c.name,
            economy=c.economy,
            social=c.social,
            demography=c.demography,
            technology=c.technology,
            military_power=c.military_power,
            n_habitants=c.n_habitants,
            latitude=c.latitude,
            longitude=c.longitude,
        )
        for c in countries_db
    ]

    relations: List[RelationState] = [
        RelationState(
            id=r.id,
            country_1=r.country_1,
            country_2=r.country_2,
            relation=r.relation,
            pending_alliance_from=None,
        )
        for r in rels_db
    ]

    return WorldState(turn=turn_number, countries=countries, relations=relations)


def persist_turn_actions(
    db: Session,
    run_id: str,
    turn_number: int,
    order: Optional[list[str]],
    actions: list[Action],
) -> int:
    """
    Write-only persistence:
      - create Turn row (needed because ActionHistory.turn_id is FK + non-null)
      - insert ActionHistory rows (append-only)

    Returns turn_id.
    """
    turn = Turn(
        run_id=run_id,
        turn_number=turn_number,
        order=",".join(order) if order else None,
    )
    db.add(turn)
    db.flush()  # assigns turn.id

    for a in actions:
        db.add(
            ActionHistory(
                turn_id=turn.id,
                country_id=a.actor_id,
                action_type=a.type.value,
                target_id=getattr(a, "target_id", None),
                intensity=getattr(a, "intensity", None),
                accept=(1 if getattr(a, "accept", None) is True else 0 if getattr(a, "accept", None) is False else None),
                reason=getattr(a, "reason", None),
            )
        )

    db.commit()
    return int(turn.id)