from pathlib import Path
from typing import List
from .country_agent import CountryAgent
from app.multi_llm.schemas.world import WorldState

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"

def get_selected_agents(world_state: WorldState) -> List[CountryAgent]:

    agents = []
    generic_prompt_path = str(PROMPTS_DIR / "generic_prompt.txt")
    
    for country in world_state.countries:
        agents.append(
            CountryAgent(
                country_id=country.id,
                country_name=country.name,
                prompt_path=generic_prompt_path
            )
        )
    
    return agents