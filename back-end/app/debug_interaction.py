import asyncio
from dotenv import load_dotenv

from app.multi_llm.agents.registry import AGENTS
from app.multi_llm.schemas.world import WorldState, CountryState, RelationState
from app.multi_llm.llm.provider import MistralProvider


async def main():
    load_dotenv()  # loads MISTRAL_API_KEY from .env for local runs

    world = WorldState(
        turn=0,
        countries=[
            CountryState(id="USA", name="United States", economy=80, social=60, demography=50,
                         technology=90, military_power=85, n_habitants=330, latitude=38.0, longitude=-97.0),
            CountryState(id="CHN", name="China", economy=85, social=55, demography=60,
                         technology=80, military_power=75, n_habitants=1400, latitude=35.0, longitude=103.0),
            CountryState(id="RUS", name="Russia", economy=60, social=50, demography=50,
                         technology=65, military_power=80, n_habitants=145, latitude=60.0, longitude=90.0),
        ],
        relations=[
            RelationState(id=1, country_1="USA", country_2="CHN", relation=-70),  # make it hostile to trigger war more often
            RelationState(id=2, country_1="CHN", country_2="RUS", relation=10),
            RelationState(id=3, country_1="USA", country_2="RUS", relation=0),
        ],
    )

    provider = MistralProvider(model="mistral-small-latest")

    usa = next(a for a in AGENTS if a.country_id == "USA")
    action = await usa.decide_llm(world, provider)

    print("USA tool-based action ->", action.model_dump())


if __name__ == "__main__":
    asyncio.run(main())