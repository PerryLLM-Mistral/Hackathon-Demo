# app/multi_llm/orchestrator.py

from typing import List, Optional
from dotenv import load_dotenv

from app.multi_llm.schemas.world import WorldState
from app.multi_llm.schemas.action import Action
from app.multi_llm.agents.registry import get_selected_agents
from app.multi_llm.llm.provider import MistralProvider


class Orchestrator:
    def __init__(self, use_llm: bool = True):
        load_dotenv()  # asegura env en local

        self.provider: Optional[MistralProvider] = None
        if use_llm:
            try:
                self.provider = MistralProvider()
            except Exception:
                # si no hay key o falla init, cae a heurístico sin romper el server
                self.provider = None

    async def decide_turn(self, world: WorldState) -> List[Action]:
        actions: List[Action] = []
        active_agents = get_selected_agents(world)

        for agent in active_agents:
            if self.provider is None:
                action = await agent.decide(world)
            else:
                try:
                    action = await agent.decide_llm(world, self.provider)
                except Exception:
                    action = await agent.decide(world)

            actions.append(action)

        return actions