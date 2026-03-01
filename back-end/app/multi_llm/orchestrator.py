# app/multi_llm/orchestrator.py

from typing import List, Optional
from dotenv import load_dotenv

from app.multi_llm.schemas.world import WorldState
from app.multi_llm.schemas.action import Action
from app.multi_llm.agents.registry import get_selected_agents
from app.multi_llm.llm.provider import MistralProvider


class Orchestrator:
    def __init__(self, use_llm: bool = True):
        load_dotenv()

        self.provider: Optional[MistralProvider] = None

        self.active_agents = []

        if use_llm:
            try:
                self.provider = MistralProvider()
            except Exception:
                self.provider = None

    def reload_agents(self, world: WorldState):
        self.active_agents = get_selected_agents(world)

    async def decide_turn(self, world: WorldState) -> List[Action]:
        actions: List[Action] = []

        if not self.active_agents:
            self.reload_agents(world)

        for agent in self.active_agents:
            action = await agent.decide_llm(world, self.provider)
            actions.append(action)

        return actions