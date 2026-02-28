class BaseAgent:
    def __init__(self, country_id: str):
        self.country_id = country_id

    async def decide(self, world_state):
        raise NotImplementedError