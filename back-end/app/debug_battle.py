# app/debug_battle.py
#
# Run (inside the backend container so "db" hostname resolves):
#   python -m app.debug_battle
#
# What it does:
# - loads initial WorldState from Postgres (countries + relationships)
# - builds agents dynamically from Countries table (no hardcode)
# - picks ONLY 5 countries for the game (random sample from DB)
# - runs LLM decisions per agent using ONLY the 5-country slice (prevents token explosion)
# - applies actions in-memory to the full world (or just the slice; here we apply to the slice)
# - optionally persists Turn + ActionHistory each turn (toggle with a boolean)
# - optionally notifies the FastAPI bridge (/events/broadcast)

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()  # MUST be before importing app.database

import asyncio
import secrets
import requests

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.multi_llm.schemas.world import WorldState
from app.multi_llm.agents.country_agent import CountryAgent
from app.multi_llm.llm.provider import MistralProvider
from app.simulation.engine import apply_action, ensure_relation
from app.simulation.state_store import load_world_state, persist_turn_actions

from app.src.models.models import Country, Relationship


# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
RUN_ID = "demo"  # stable run id for debugging (or use secrets.token_hex(4))

# Toggle DB writes to Turn + ActionHistory (via persist_turn_actions)
WRITE_ACTION_HISTORY = True

# Optional: notify FastAPI bridge (websocket UI) via /events/broadcast
NOTIFY_BRIDGE = True

# Optional: seed DB if empty (this writes to countries/relationships)
# Keep False if you want a pure read-only run
SEED_IF_EMPTY = True

# How many turns to run
N_TURNS = 3

# How many countries in the match
N_COUNTRIES_IN_MATCH = 5

# If True, sample only from countries.selected == True
USE_SELECTED_ONLY = False


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
# DB helpers
# -----------------------------------------------------------------------------
def seed_if_empty(db: Session) -> None:
    if db.query(Country).first() is not None:
        return

    db.add_all(
        [
            Country(
                id="USA",
                name="United States",
                economy=80,
                social=60,
                demography=50,
                technology=90,
                military_power=85,
                n_habitants=330,
                latitude=38.0,
                longitude=-97.0,
                selected=True,
            ),
            Country(
                id="CHN",
                name="China",
                economy=85,
                social=55,
                demography=60,
                technology=80,
                military_power=75,
                n_habitants=1400,
                latitude=35.0,
                longitude=103.0,
                selected=True,
            ),
            Country(
                id="RUS",
                name="Russia",
                economy=70,
                social=50,
                demography=55,
                technology=75,
                military_power=80,
                n_habitants=145,
                latitude=55.0,
                longitude=37.0,
                selected=True,
            ),
            Country(
                id="ESP",
                name="Spain",
                economy=70,
                social=70,
                demography=45,
                technology=70,
                military_power=45,
                n_habitants=47,
                latitude=40.0,
                longitude=-3.7,
                selected=True,
            ),
            Country(
                id="FRA",
                name="France",
                economy=75,
                social=70,
                demography=45,
                technology=75,
                military_power=55,
                n_habitants=68,
                latitude=46.2,
                longitude=2.2,
                selected=True,
            ),
        ]
    )
    db.flush()

    db.add_all(
        [
            Relationship(country_1="USA", country_2="CHN", relation=0),
            Relationship(country_1="USA", country_2="RUS", relation=0),
            Relationship(country_1="CHN", country_2="RUS", relation=0),
            Relationship(country_1="ESP", country_2="FRA", relation=0),
            Relationship(country_1="USA", country_2="FRA", relation=0),
        ]
    )
    db.commit()


def pick_match_country_ids(db: Session) -> list[str]:
    q = db.query(Country.id)
    if USE_SELECTED_ONLY:
        q = q.filter(Country.selected.is_(True))

    ids = [r[0] for r in q.all()]
    if len(ids) < N_COUNTRIES_IN_MATCH:
        raise RuntimeError(
            f"Not enough countries in DB to start a match of {N_COUNTRIES_IN_MATCH}. "
            f"Found {len(ids)}."
        )

    rng = secrets.SystemRandom()
    return rng.sample(ids, k=N_COUNTRIES_IN_MATCH)


def build_agents_from_db(db: Session, match_ids: set[str]) -> dict[str, CountryAgent]:
    rows = (
        db.query(Country)
        .filter(Country.id.in_(match_ids))
        .order_by(Country.id.asc())
        .all()
    )
    if not rows:
        raise RuntimeError("No countries found for the selected match ids.")
    return {c.id: CountryAgent(country_id=c.id, country_name=c.name) for c in rows}


def slice_world(world: WorldState, match_ids: set[str]) -> WorldState:
    countries = [c for c in world.countries if c.id in match_ids]
    relations = [
        r for r in world.relations
        if (r.country_1 in match_ids and r.country_2 in match_ids)
    ]
    return WorldState(turn=world.turn, countries=countries, relations=relations)


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

        # IMPORTANT: the LLM sees ONLY the 5-country match world
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
        if SEED_IF_EMPTY:
            seed_if_empty(db)

        # Load full state (may contain many countries)
        world_full = load_world_state(db, run_id=RUN_ID)

        # Pick exactly 5 countries for the match
        match_ids = set(pick_match_country_ids(db))

        # Slice world down to match
        world_match = slice_world(world_full, match_ids)

        # Build agents only for match countries
        agents = build_agents_from_db(db, match_ids=match_ids)
        base_order = list(agents.keys())

        provider = MistralProvider()

        section(f"Initial match state (run={RUN_ID}) | countries={len(base_order)} | ids={base_order}")
        print_all_relations(world_match)
        print_all_countries(world_match)

        for _ in range(N_TURNS):
            await run_turn(db, world_match, agents, provider, base_order=base_order, run_id=RUN_ID)
            world_match.turn += 1

            # Only reload from DB if we're writing; otherwise DB doesn't reflect changes
            if WRITE_ACTION_HISTORY:
                world_full = load_world_state(db, run_id=RUN_ID)
                world_match = slice_world(world_full, match_ids)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())