from fastapi import WebSocket
from app.events import ai_events

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast(self, message):
        for connection in self.active_connections:
            await connection.send_json(message)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    # Callback for the AI Observable
    async def handle_ai_notification(self, data: dict):
        payload = {
            "event": "ai_action",
            "payload": data
        }
        # Forward the notification to all connected users
        await self.broadcast(payload)

manager = ConnectionManager()

# Subscribe the manager to the AI event bridge
ai_events.subscribe(manager.handle_ai_notification)