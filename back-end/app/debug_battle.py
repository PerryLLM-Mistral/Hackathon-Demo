import asyncio
from dotenv import load_dotenv

from app.multi_llm.agents.registry import AGENTS
from app.multi_llm.schemas.world import WorldState, CountryState, RelationState
from app.multi_llm.llm.provider import MistralProvider


def _find_relation(world: WorldState, a: str, b: str) -> RelationState | None:
    """Find a relation regardless of stored order (a,b) or (b,a)."""
    for r in world.relations:
        if (r.country_1 == a and r.country_2 == b) or (r.country_1 == b and r.country_2 == a):
            return r
    return None


def _apply_action_to_world(world: WorldState, action) -> None:
    """
    Very small local simulation (no DB) to create real interactions:
    updates relation scores based on ActionType + intensity.
    """
    if action.type in {"PASS", "MESSAGE"}:
        return
    if not action.target_id:
        return

    rel = _find_relation(world, action.actor_id, action.target_id)
    if rel is None:
        # Create relation if missing (store in actor->target order)
        new_id = max((r.id for r in world.relations), default=0) + 1
        rel = RelationState(
            id=new_id,
            country_1=action.actor_id,
            country_2=action.target_id,
            relation=0,
        )
        world.relations.append(rel)

    # Simple deterministic deltas (tune later in simulation/rules.py)
    if action.type == "DECLARE_WAR":
        delta = -35 * action.intensity
    elif action.type == "ALLY":
        delta = +30 * action.intensity
    elif action.type == "TRADE":
        delta = +15 * action.intensity
    elif action.type == "SANCTION":
        delta = -20 * action.intensity
    else:
        delta = 0

    rel.relation = max(-100, min(100, rel.relation + delta))


async def main():
    load_dotenv()  # loads MISTRAL_API_KEY from .env for local runs

    world = WorldState(
        turn=0,
        countries=[
            CountryState(id="USA", name="United States", economy=80, social=60, demography=50,
                         technology=90, military_power=85, n_habitants=330, latitude=38.0, longitude=-97.0),
            CountryState(id="CHI", name="China", economy=85, social=55, demography=60,
                         technology=80, military_power=75, n_habitants=1400, latitude=35.0, longitude=103.0),
            CountryState(id="RUS", name="Russia", economy=60, social=50, demography=50,
                         technology=65, military_power=80, n_habitants=145, latitude=60.0, longitude=90.0),
        ],
        relations=[
            RelationState(id=1, country_1="USA", country_2="CHI", relation=-70),
            RelationState(id=2, country_1="CHI", country_2="RUS", relation=10),
            RelationState(id=3, country_1="USA", country_2="RUS", relation=0),
        ],
    )

    provider = MistralProvider(model="mistral-small-latest")

    # Run multiple turns, each turn: every agent acts once, then world updates.
    n_turns = 5

    for t in range(n_turns):
        world.turn = t
        print(f"\n=== TURN {t} ===")

        # Option A: sequential (clearer logs, less API parallelism)
        for agent in AGENTS:
            action = await agent.decide_llm(world, provider)
            print(f"{agent.country_id} -> {action.model_dump()}")
            _apply_action_to_world(world, action)

        # Print resulting relations after the turn
        print("Relations after turn:")
        for r in world.relations:
            print(f"  {r.country_1}-{r.country_2}: {r.relation} ({r.label()})")


if __name__ == "__main__":
    asyncio.run(main())