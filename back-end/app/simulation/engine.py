class SimulationEngine:

    def __init__(self):
        self.turn = 0
        self.state = {}

    def get_state(self):
        return self.state

    def apply(self, actions):
        self.turn += 1
        # Aquí irán reglas reales
        delta = {
            "turn": self.turn,
            "actions": [a.model_dump() for a in actions]
        }
        return delta