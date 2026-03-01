# app/debug_agents_from_db.py
#
# Run INSIDE backend container:
#   docker compose exec backend bash
#   python -m app.debug_agents_from_db
#
# What it does:
# - Ensures schema exists
# - Loads countries from Postgres
# - Creates CountryAgent per row
# - Loads relationships and builds WorldState
# - Runs a few LLM turns and appends Turn + ActionHistory

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()  # IMPORTANT: before importing app.database

import asyncio
import secrets
import requests

from sqlalchemy.orm import Session

from app.database import SessionLocal, Base, engine
import app.src.models.models  # register models
from app.src.models.models import Country, Relationship, Turn, ActionHistory

from app.multi_llm.schemas.world import WorldState, CountryState, RelationState
from app.multi_llm.agents.country_agent import CountryAgent
from app.multi_llm.llm.provider import MistralProvider
from app.simulation.engine import apply_action


RUN_ID = "demo"


def ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)


def _notify(payload: dict) -> None:
    try:
        requests.post(
            "http://127.0.0.1:8000/events/broadcast",
            json={"data": payload},
            timeout=1,
        )
    except Exception as e:
        print(f"DEBUG: Bridge not reachable: {e}")


def seed_if_empty(db: Session) -> None:
    if db.query(Country).first() is not None:
        return

    # db.add_all(
    #     [
    #         Country(
    #             id="USA", name="United States",
    #             economy=80, social=60, demography=50,
    #             technology=90, military_power=85,
    #             n_habitants=330, latitude=38.0, longitude=-97.0,
    #         ),
    #         Country(
    #             id="CHI", name="China",
    #             economy=85, social=55, demography=60,
    #             technology=80, military_power=75,
    #             n_habitants=1400, latitude=35.0, longitude=103.0,
    #         ),
    #         Country(
    #             id="RUS", name="Russia",
    #             economy=70, social=50, demography=55,
    #             technology=75, military_power=80,
    #             n_habitants=145, latitude=55.0, longitude=37.0,
    #         ),
    #     ]
    # )
    # db.flush()

    # db.add_all(
    #     [
    #         Relationship(country_1="USA", country_2="CHI", relation=0),
    #         Relationship(country_1="USA", country_2="RUS", relation=0),
    #         Relationship(country_1="CHI", country_2="RUS", relation=0),
    #     ]
    # )
    # db.commit()


def build_world_from_db(db: Session, run_id: str) -> WorldState:
    countries_db = db.query(Country).order_by(Country.id.asc()).all()
    rels_db = db.query(Relationship).order_by(Relationship.id.asc()).all()

    last_turn = (
        db.query(Turn.turn_number)
        .filter(Turn.run_id == run_id)
        .order_by(Turn.turn_number.desc())
        .limit(1)
        .scalar()
    )
    turn_number = int(last_turn) + 1 if last_turn is not None else 0

    countries = [
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

    relations = [
        RelationState(
            id=r.id,
            country_1=r.country_1,
            country_2=r.country_2,
            relation=r.relation,
            pending_alliance_from=None,  # current-state table doesn't track it
        )
        for r in rels_db
    ]

    return WorldState(turn=turn_number, countries=countries, relations=relations)


def build_agents_from_db(db: Session) -> dict[str, CountryAgent]:
    """
    Creates one CountryAgent per row in countries table.
    """
    rows = db.query(Country).order_by(Country.id.asc()).all()
    agents: dict[str, CountryAgent] = {}
    for c in rows:
        agents[c.id] = CountryAgent(country_id=c.id, country_name=c.name)
    return agents


def persist_turn_and_actions(
    db: Session,
    run_id: str,
    turn_number: int,
    order: list[str],
    actions: list,
) -> int:
    turn_row = Turn(run_id=run_id, turn_number=turn_number, order=",".join(order))
    db.add(turn_row)
    db.flush()

    for a in actions:
        db.add(
            ActionHistory(
                turn_id=turn_row.id,
                country_id=a.actor_id,
                action_type=a.type.value,
                target_id=a.target_id,
                intensity=getattr(a, "intensity", None),
                accept=(1 if getattr(a, "accept", None) is True else 0 if getattr(a, "accept", None) is False else None),
                reason=getattr(a, "reason", None),
            )
        )

    db.commit()
    return int(turn_row.id)


async def run_turn(
    db: Session,
    world: WorldState,
    agents: dict[str, CountryAgent],
    provider: MistralProvider,
    run_id: str,
) -> None:
    t = world.turn
    rng = secrets.SystemRandom()

    order = list(agents.keys())
    rng.shuffle(order)

    _notify({"type": "TURN_START", "turn": t, "run_id": run_id, "order": order, "nonce": rng.randint(1, 1_000_000)})

    actions = []
    for cid in order:
        a = await agents[cid].decide_llm(world, provider)
        actions.append(a)
        apply_action(world, a)

    turn_id = persist_turn_and_actions(db, run_id=run_id, turn_number=t, order=order, actions=actions)

    _notify({"type": "TURN_END", "turn": t, "turn_id": turn_id, "run_id": run_id})


async def main() -> None:
    ensure_schema()

    db = SessionLocal()
    try:
        seed_if_empty(db)

        world = build_world_from_db(db, run_id=RUN_ID)
        agents = build_agents_from_db(db)
        provider = MistralProvider()

        print(f"Loaded {len(agents)} agents from DB: {list(agents.keys())}")
        print(f"Starting at turn={world.turn}, run_id={RUN_ID}")

        for _ in range(3):
            await run_turn(db, world, agents, provider, run_id=RUN_ID)
            world.turn += 1
            world = build_world_from_db(db, run_id=RUN_ID)  # refresh snapshot if you want
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())