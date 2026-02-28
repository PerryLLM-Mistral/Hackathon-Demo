import asyncio

from app.multi_llm.agents.registry import AGENTS
from app.multi_llm.schemas.world import WorldState, CountryState, RelationState


async def main():
    # Minimal fake world (no DB) just to verify agents run
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
            RelationState(id=1, country_1="USA", country_2="CHI", relation=10),
            RelationState(id=2, country_1="CHI", country_2="RUS", relation=-20),
            RelationState(id=3, country_1="USA", country_2="RUS", relation=0),
        ],
    )

    for agent in AGENTS:
        action = await agent.decide(world)
        print(agent.country_id, "->", action.model_dump())


if __name__ == "__main__":
    asyncio.run(main())