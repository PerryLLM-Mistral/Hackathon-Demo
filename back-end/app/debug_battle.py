# app/debug_battle.py

# docker exec -it fastapi_backend /bin/bash

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()  # MUST be before importing app.database

import asyncio
import secrets
import requests
from itertools import combinations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.multi_llm.schemas.world import WorldState, CountryState, RelationState
from app.multi_llm.agents.country_agent import CountryAgent
from app.multi_llm.llm.provider import MistralProvider
from app.simulation.engine import apply_action, ensure_relation
from app.simulation.state_store import persist_turn_actions

from app.src.models.models import Turn, Country, Relationship  # ✅ add Country, Relationship


# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
RUN_ID = "demo"
WRITE_ACTION_HISTORY = False
NOTIFY_BRIDGE = True
N_TURNS = 3

# "frontend selection"
SELECTED_IDS = ["USA", "CHN", "RUS", "ESP", "FRA"]


# -----------------------------------------------------------------------------
# Pretty printing
# -----------------------------------------------------------------------------
def section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_relation(world: WorldState, a: str, b: str) -> None:
    rel = ensure_relation(world, a, b)
    pending = getattr(rel, "pending_alliance_from", None)
    print(f"Relation {a}<->{b}: {rel.relation:>4} | pending_alliance_from={pending}")


def print_all_relations(world: WorldState) -> None:
    ids = [c.id for c in world.countries]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            print_relation(world, ids[i], ids[j])


def print_country(world: WorldState, cid: str) -> None:
    c = next(x for x in world.countries if x.id == cid)
    print(
        f"{c.id} | econ={c.economy:>3} soc={c.social:>3} demo={c.demography:>3} "
        f"tech={c.technology:>3} mil={c.military_power:>3}"
    )


def print_all_countries(world: WorldState) -> None:
    for c in world.countries:
        print_country(world, c.id)


# -----------------------------------------------------------------------------
# DB-backed world builder (only for the selected IDs)
# -----------------------------------------------------------------------------
def get_start_turn_number(db: Session, run_id: str) -> int:
    if not WRITE_ACTION_HISTORY:
        return 0

    last_turn = (
        db.query(func.max(Turn.turn_number))
        .filter(Turn.run_id == run_id)
        .scalar()
    )
    return int(last_turn + 1) if last_turn is not None else 0


def build_world_from_selected_ids(db: Session, selected_ids: list[str], start_turn: int) -> WorldState:
    # Fetch only the requested countries
    rows = (
        db.query(Country)
        .filter(Country.id.in_(selected_ids))
        .order_by(Country.id.asc())
        .all()
    )

    found_ids = {c.id for c in rows}
    missing = [cid for cid in selected_ids if cid not in found_ids]

    if missing:
        section("WARNING: selected IDs not found in DB")
        print(f"Missing country IDs: {missing}")
        print("Only existing countries will be used for this debug run.")

    if not rows:
        raise RuntimeError(
            "None of the SELECTED_IDS exist in the DB. "
            "Insert countries first (or pick valid ids) and re-run."
        )

    # Build CountryState list from DB rows
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
        for c in rows
    ]

    # Build relations only among the found ids
    ids_in_match = [c.id for c in rows]

    # If Relationship table has rows, load those; otherwise default to 0 for every pair
    rel_rows = (
        db.query(Relationship)
        .filter(
            Relationship.country_1.in_(ids_in_match),
            Relationship.country_2.in_(ids_in_match),
        )
        .order_by(Relationship.id.asc())
        .all()
    )

    relations: list[RelationState] = []
    used_pairs: set[tuple[str, str]] = set()

    # Add stored relationships (if any)
    for r in rel_rows:
        a, b = r.country_1, r.country_2
        key = (a, b) if a < b else (b, a)
        if key in used_pairs:
            continue
        used_pairs.add(key)
        relations.append(
            RelationState(
                id=r.id,
                country_1=a,
                country_2=b,
                relation=r.relation,
                pending_alliance_from=None,
            )
        )

   
    return WorldState(turn=start_turn, countries=countries, relations=relations)


def build_agents_from_db_rows(rows: list[Country]) -> dict[str, CountryAgent]:
    return {c.id: CountryAgent(country_id=c.id, country_name=c.name) for c in rows}


# -----------------------------------------------------------------------------
# Bridge notifications
# -----------------------------------------------------------------------------
def _notify(payload: dict) -> None:
    if not NOTIFY_BRIDGE:
        return
    try:
        requests.post(
            "http://127.0.0.1:8000/events/broadcast",
            json={"data": payload},
            timeout=1,
        )
    except Exception as e:
        print(f"DEBUG: Bridge not reachable: {e}")


# -----------------------------------------------------------------------------
# Turn runner
# -----------------------------------------------------------------------------
async def run_turn(
    db: Session,
    world_match: WorldState,
    agents: dict[str, CountryAgent],
    provider: MistralProvider,
    base_order: list[str],
    run_id: str,
) -> None:
    t = world_match.turn
    rng = secrets.SystemRandom()

    order = list(base_order)
    rng.shuffle(order)

    _notify(
        {
            "type": "TURN_START",
            "turn": t,
            "run_id": run_id,
            "order": order,
            "nonce": rng.randint(1, 1_000_000),
            "message": f"Turn {t} has started (run={run_id})",
        }
    )

    section(f"Turn {t} | Order: {order} | run={run_id}")

    actions = []

    for cid in order:
        agent = agents[cid]

        action = await agent.decide_llm(world_match, provider)
        actions.append(action)

        section(f"Turn {world_match.turn} | {cid} decides")
        print(
            f"Action: {action.type} target={action.target_id} intensity={action.intensity} "
            f"accept={getattr(action, 'accept', None)}"
        )
        print(f"Reason: {action.reason}")

        apply_action(world_match, action)

        print_all_relations(world_match)
        print_all_countries(world_match)

    turn_id = None
    if WRITE_ACTION_HISTORY:
        turn_id = persist_turn_actions(
            db=db,
            run_id=run_id,
            turn_number=t,
            order=order,
            actions=actions,
        )

    end_payload = {
        "type": "TURN_END",
        "turn": t,
        "run_id": run_id,
        "relations": [
            {"id": r.id, "pair": f"{r.country_1}-{r.country_2}", "value": r.relation}
            for r in world_match.relations
        ],
    }
    if turn_id is not None:
        end_payload["turn_id"] = turn_id

    _notify(end_payload)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
async def main() -> None:
    db = SessionLocal()
    try:
        start_turn = get_start_turn_number(db, run_id=RUN_ID)

        # Fetch rows once (to build agents) and world from DB
        rows = (
            db.query(Country)
            .filter(Country.id.in_(SELECTED_IDS))
            .order_by(Country.id.asc())
            .all()
        )

        # Build world (also prints missing ids warning)
        world_match = build_world_from_selected_ids(db, SELECTED_IDS, start_turn=start_turn)

        # Agents only for found countries
        agents = build_agents_from_db_rows(rows)
        base_order = list(agents.keys())

        provider = MistralProvider()

        section(f"Initial match state (run={RUN_ID}) | countries={len(base_order)} | ids={base_order}")
        print_all_relations(world_match)
        print_all_countries(world_match)

        for _ in range(N_TURNS):
            await run_turn(db, world_match, agents, provider, base_order=base_order, run_id=RUN_ID)
            world_match.turn += 1

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())