from abc import ABC, abstractmethod
from app.multi_llm.schemas.world import WorldState
from app.multi_llm.schemas.action import Action


class BaseAgent(ABC):
    """
    Abstract base class for all country agents.
    Country IDs are 3-letter strings, matching the DB primary key.
    """

    def __init__(self, country_id: str, country_name: str):
        self.country_id = country_id
        self.country_name = country_name

    @abstractmethod
    async def decide(self, world: WorldState) -> Action:
        """Must return a valid Action object."""
        raise NotImplementedError