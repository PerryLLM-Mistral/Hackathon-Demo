import random
from pathlib import Path
from typing import Optional

from app.multi_llm.schemas.world import WorldState
from app.multi_llm.schemas.action import Action, ActionType


class CountryAgent:
    """
    Represents a single country agent.

    The agent does NOT modify the database.
    It only proposes an Action.
    """

    def __init__(
        self,
        country_id: int,
        country_name: str,
        prompt_path: Optional[str] = None,
    ):
        self.country_id = country_id
        self.country_name = country_name
        self.prompt_text = self._load_prompt(prompt_path) if prompt_path else ""

    def _load_prompt(self, path: str) -> str:
        """
        Loads static personality prompt from file.
        """
        return Path(path).read_text(encoding="utf-8")

    def _choose_target(self, world: WorldState) -> Optional[int]:
        """
        Randomly selects a valid target country.
        """
        candidates = [c.id for c in world.countries if c.id != self.country_id]
        return random.choice(candidates) if candidates else None

    def _get_relation_value(self, world: WorldState, target_id: int) -> Optional[int]:
        """
        Retrieves numeric relation value between this country and target.
        """
        a, b = sorted([self.country_id, target_id])
        for r in world.relations:
            if r.country_1 == a and r.country_2 == b:
                return r.value
        return None

    async def decide(self, world: WorldState) -> Action:
        """
        Heuristic decision logic.
        Replace later with LLM provider.
        """

        # 10% probability of doing nothing
        if random.random() < 0.1:
            return Action(
                actor_id=self.country_id,
                type=ActionType.PASS,
                reason="Strategic pause this turn"
            )

        target_id = self._choose_target(world)
        if target_id is None:
            return Action(
                actor_id=self.country_id,
                type=ActionType.PASS,
                reason="No available targets"
            )

        relation_value = self._get_relation_value(world, target_id)

        if relation_value is None:
            # No existing relation → initiate trade
            return Action(
                actor_id=self.country_id,
                type=ActionType.TRADE,
                target_id=target_id,
                intensity=1,
                reason="Establish initial cooperation"
            )

        if relation_value <= -60:
            return Action(
                actor_id=self.country_id,
                type=ActionType.DECLARE_WAR,
                target_id=target_id,
                intensity=2,
                reason="Escalating hostile relationship"
            )

        if relation_value >= 60:
            return Action(
                actor_id=self.country_id,
                type=ActionType.ALLY,
                target_id=target_id,
                intensity=1,
                reason="Strengthen strategic alliance"
            )

        # Neutral zone
        return Action(
            actor_id=self.country_id,
            type=ActionType.TRADE,
            target_id=target_id,
            intensity=1,
            reason="Improve neutral relations"
        )