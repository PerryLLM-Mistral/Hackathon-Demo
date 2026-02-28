import asyncio

class AIEventObservable:
    def __init__(self):
        # List to store all subscriber callback functions
        self._subscribers = []

    def subscribe(self, callback):
        # Registers a new subscriber
        self._subscribers.append(callback)

    async def notify(self, data: dict):
        # Iterates through all subscribers and executes their callbacks
        # It is triggered by an AI agent action
        for callback in self._subscribers:
            await callback(data)

# Singleton instance
ai_events = AIEventObservable()