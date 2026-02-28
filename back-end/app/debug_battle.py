# app/debug_battle_llm.py
#
# Run:
#   python -m app.debug_battle_llm

from __future__ import annotations

import asyncio
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


async def run_turn(world: WorldState, agents: dict[str, CountryAgent], provider: MistralProvider, order: list[str]) -> None:
    for cid in order:
        agent = agents[cid]
        action = await agent.decide_llm(world, provider)

        section(f"Turn {world.turn} | {cid} decides")
        print(f"Action: {action.type} target={action.target_id} intensity={action.intensity} accept={getattr(action, 'accept', None)}")
        print(f"Reason: {action.reason}")

        apply_action(world, action)

        print_all_relations(world)
        print_all_countries(world)


async def main() -> None:
    load_dotenv()

    world = WorldState(
        turn=0,
        countries=[
            CountryState(
                id="USA", name="United States",
                economy=80, social=60, demography=50,
                technology=90, military_power=85,
                n_habitants=330, latitude=38.0, longitude=-97.0,
            ),
            CountryState(
                id="CHI", name="China",
                economy=85, social=55, demography=60,
                technology=80, military_power=75,
                n_habitants=1400, latitude=35.0, longitude=103.0,
            ),
            CountryState(
                id="RUS", name="Russia",
                economy=70, social=50, demography=55,
                technology=75, military_power=80,
                n_habitants=145, latitude=55.0, longitude=37.0,
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

    section("Initial state")
    print_all_relations(world)
    print_all_countries(world)

    # Run 3 turns
    for _ in range(3):
        await run_turn(world, agents, provider, order=["USA", "CHI", "RUS"])
        world.turn += 1


if __name__ == "__main__":
    asyncio.run(main())