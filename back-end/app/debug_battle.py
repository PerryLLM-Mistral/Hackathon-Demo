# app/debug_battle_llm.py
#
# Run:
#   python -m app.debug_battle_llm

from __future__ import annotations

import asyncio
import secrets
import requests
from dotenv import load_dotenv

from app.multi_llm.schemas.world import WorldState, CountryState, RelationState
from app.multi_llm.agents.country_agent import CountryAgent
from app.multi_llm.llm.provider import MistralProvider
from app.simulation.engine import apply_action, ensure_relation


def section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_relation(world: WorldState, a: str, b: str) -> None:
    rel = ensure_relation(world, a, b)
    pending = getattr(rel, "pending_alliance_from", None)
    print(f"Relation {a}<->{b}: {rel.relation:>4} | pending_alliance_from={pending}")


def print_all_relations(world: WorldState):
    print_relation(world, "USA", "CHI")
    print_relation(world, "USA", "RUS")
    print_relation(world, "CHI", "RUS")


def print_country(world: WorldState, cid: str) -> None:
    c = next(x for x in world.countries if x.id == cid)
    print(
        f"{c.id} | econ={c.economy:>3} soc={c.social:>3} demo={c.demography:>3} "
        f"tech={c.technology:>3} mil={c.military_power:>3}"
    )


def print_all_countries(world: WorldState):
    for cid in ["USA", "CHI", "RUS"]:
        print_country(world, cid)


async def run_turn(
    world: WorldState,
    agents: dict[str, CountryAgent],
    provider: MistralProvider,
    base_order: list[str],
    run_id: str,
) -> None:
    """
    Run one full turn (each country acts once). We randomize order each turn to reduce
    deterministic loops and keep the LLM from always seeing the same agent sequence.
    """
    t = world.turn
    rng = secrets.SystemRandom()

    # Randomize order per turn (breaks stable openings)
    order = list(base_order)
    rng.shuffle(order)

    # NOTIFY TURN START
    try:
        requests.post(
            "http://127.0.0.1:8000/events/broadcast",
            json={
                "data": {
                    "type": "TURN_START",
                    "turn": t,
                    "run_id": run_id,
                    "order": order,
                    "nonce": rng.randint(1, 1_000_000),
                    "message": f"Turn {t} has started (run={run_id})",
                }
            },
            timeout=1,
        )
    except Exception as e:
        print(f"DEBUG: Bridge not reachable at turn start: {e}")

    section(f"Turn {t} | Order: {order} | run={run_id}")

    for cid in order:
        agent = agents[cid]

        # Add per-call variability visible to LLM via the agent (if your CountryAgent
        # already injects nonce into WORLD payload, this still helps via ordering/logs).
        action = await agent.decide_llm(world, provider)

        section(f"Turn {world.turn} | {cid} decides")
        print(
            f"Action: {action.type} target={action.target_id} intensity={action.intensity} "
            f"accept={getattr(action, 'accept', None)}"
        )
        print(f"Reason: {action.reason}")

        apply_action(world, action)

        print_all_relations(world)
        print_all_countries(world)

    # NOTIFY TURN END
    try:
        requests.post(
            "http://127.0.0.1:8000/events/broadcast",
            json={
                "data": {
                    "type": "TURN_END",
                    "turn": t,
                    "run_id": run_id,
                    "relations": [
                        {"id": r.id, "pair": f"{r.country_1}-{r.country_2}", "value": r.relation}
                        for r in world.relations
                    ],
                }
            },
            timeout=1,
        )
    except Exception as e:
        print(f"DEBUG: Bridge not reachable at turn end: {e}")


async def main() -> None:
    load_dotenv()

    # per-execution run id to make logs/prompt context vary across runs
    run_id = secrets.token_hex(4)

    world = WorldState(
        turn=0,
        countries=[
            CountryState(
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
            CountryState(
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
            CountryState(
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
        ],
        relations=[
            RelationState(id=1, country_1="USA", country_2="CHI", relation=0, pending_alliance_from=None),
            RelationState(id=2, country_1="USA", country_2="RUS", relation=0, pending_alliance_from=None),
            RelationState(id=3, country_1="CHI", country_2="RUS", relation=0, pending_alliance_from=None),
        ],
    )

    provider = MistralProvider()

    agents = {
        "USA": CountryAgent(country_id="USA", country_name="United States"),
        "CHI": CountryAgent(country_id="CHI", country_name="China"),
        "RUS": CountryAgent(country_id="RUS", country_name="Russia"),
    }

    section(f"Initial state (run={run_id})")
    print_all_relations(world)
    print_all_countries(world)

    base_order = ["USA", "CHI", "RUS"]

    # Run 3 turns
    for _ in range(3):
        await run_turn(world, agents, provider, base_order=base_order, run_id=run_id)
        world.turn += 1


if __name__ == "__main__":
    asyncio.run(main())