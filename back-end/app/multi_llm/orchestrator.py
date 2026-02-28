from app.multi_llm.agents.country_agent import CountryAgent

class Orchestrator:

    def __init__(self):
        self.agents = [
            CountryAgent("A"),
            CountryAgent("B"),
            CountryAgent("C"),
        ]

    async def decide_turn(self, world_state):
        actions = []
        for agent in self.agents:
            action = await agent.decide(world_state)
            actions.append(action)
        return actions