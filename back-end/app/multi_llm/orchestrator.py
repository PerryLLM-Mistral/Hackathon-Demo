# app/multi_llm/orchestrator.py

from typing import List
from app.multi_llm.schemas.world import WorldState
from app.multi_llm.schemas.action import Action
from app.multi_llm.agents.registry import AGENTS

class Orchestrator:
    """
    Turn manager. Uses a fixed list of agents (USA/CHI/RUS).
    """

    def __init__(self):
        self.agents = AGENTS  # fixed 3 agents

    async def decide_turn(self, world: WorldState) -> List[Action]:
        actions: List[Action] = []
        for agent in self.agents:
            action = await agent.decide(world)
            actions.append(action)
        return actions