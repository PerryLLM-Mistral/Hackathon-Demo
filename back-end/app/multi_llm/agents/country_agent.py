from app.multi_llm.agents.base import BaseAgent
from app.multi_llm.schemas.action import Action, ActionType
import random

class CountryAgent(BaseAgent):

    async def decide(self, world_state):
        action_type = random.choice(list(ActionType))
        return Action(
            actor=self.country_id,
            type=action_type,
            target=None,
            reason="Random action"
        )