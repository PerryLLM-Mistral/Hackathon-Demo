# app/multi_llm/orchestrator.py

from typing import List
from app.multi_llm.schemas.world import WorldState
from app.multi_llm.schemas.action import Action
from app.multi_llm.agents.registry import get_selected_agents

class Orchestrator:
    """
    Turn manager. Uses a fixed list of agents.
    """

    def __init__(self):
        pass

    async def decide_turn(self, world: WorldState) -> List[Action]:
        actions: List[Action] = []
        
        active_agents = get_selected_agents(world)
        
        for agent in active_agents:
            action = await agent.decide(world)
            actions.append(action)
            
        return actions