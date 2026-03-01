# app/debug_battle.py
#
# Run (inside the backend container so "db" hostname resolves):
#   python -m app.debug_battle
#
# What it does:
# - loads initial WorldState from Postgres (countries + relationships)
# - builds agents dynamically from Countries table (no hardcode)
# - runs LLM decisions per agent
# - applies actions in-memory
# - optionally persists Turn + ActionHistory each turn (toggle with a boolean)
# - optionally notifies the FastAPI bridge (/events/broadcast) so the websocket UI updates

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
WRITE_ACTION_HISTORY = False

# Optional: notify FastAPI bridge (websocket UI) via /events/broadcast
NOTIFY_BRIDGE = True

# Optional: seed DB if empty (this writes to countries/relationships)
# Keep False if you want a pure read-only run
SEED_IF_EMPTY = True

# How many turns to run
N_TURNS = 3


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
    # dynamic pairs: no hardcode
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
    """
    Seed current-state tables if empty:
      - countries
      - relationships

    NOTE: Your Relationship model in the project does NOT include pending_alliance_from,
    so we don't try to set it here.
    """
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
            ),
            Country(
                id="CHI",
                name="China",
                economy=85,
                social=55,
                demography=60,
                technology=80,
                military_power=75,
                n_habitants=1400,
                latitude=35.0,
                longitude=103.0,
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
            ),
        ]
    )
    db.flush()

    db.add_all(
        [
            Relationship(country_1="USA", country_2="CHI", relation=0),
            Relationship(country_1="USA", country_2="RUS", relation=0),
            Relationship(country_1="CHI", country_2="RUS", relation=0),
        ]
    )
    db.commit()


def build_agents_from_db(db: Session) -> dict[str, CountryAgent]:
    """
    Build agents dynamically from Countries table (no hardcode).
    """
    rows = db.query(Country).order_by(Country.id.asc()).all()
    if not rows:
        raise RuntimeError("No countries found in DB. Seed or insert into countries table first.")
    return {c.id: CountryAgent(country_id=c.id, country_name=c.name) for c in rows}


# -----------------------------------------------------------------------------
# Bridge notifications
# -----------------------------------------------------------------------------
def _notify(payload: dict) -> None:
    """
    Best-effort notify bridge -> websocket UI.
    If FastAPI isn't running, it won't crash the debug script.
    """
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
    world: WorldState,
    agents: dict[str, CountryAgent],
    provider: MistralProvider,
    base_order: list[str],
    run_id: str,
) -> None:
    """
    One full turn:
      - randomize order
      - get actions (LLM)
      - apply_action in memory
      - optionally persist Turn + ActionHistory (append-only) [WRITE_ACTION_HISTORY]
      - notify bridge start/end
    """
    t = world.turn
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
        action = await agent.decide_llm(world, provider)
        actions.append(action)

        section(f"Turn {world.turn} | {cid} decides")
        print(
            f"Action: {action.type} target={action.target_id} intensity={action.intensity} "
            f"accept={getattr(action, 'accept', None)}"
        )
        print(f"Reason: {action.reason}")

        apply_action(world, action)

        print_all_relations(world)
        print_all_countries(world)

    turn_id = None
    if WRITE_ACTION_HISTORY:
        # Persist ONLY the action stream (+ required Turn row)
        # NOTE: this will fail if turns/action_history tables don't exist yet.
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
            for r in world.relations
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

        # Load initial state from DB
        world = load_world_state(db, run_id=RUN_ID)

        # Build agents dynamically from Countries table (no hardcode)
        agents = build_agents_from_db(db)
        base_order = list(agents.keys())

        provider = MistralProvider()

        section(f"Initial state (run={RUN_ID})")
        print_all_relations(world)
        print_all_countries(world)

        # Run N_TURNS turns
        for _ in range(N_TURNS):
            await run_turn(db, world, agents, provider, base_order=base_order, run_id=RUN_ID)

            # advance in memory
            world.turn += 1

            # IMPORTANT:
            # If WRITE_ACTION_HISTORY is False, do NOT reload from DB each turn
            # because it would reset state (since DB isn't being updated).
            if WRITE_ACTION_HISTORY:
                world = load_world_state(db, run_id=RUN_ID)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())