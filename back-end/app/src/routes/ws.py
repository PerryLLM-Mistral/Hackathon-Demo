# app/src/routes/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            print("Received message from front-end:", data)

            await manager.broadcast({
                "event": "front_action",
                "payload": data
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")

        await manager.broadcast({
            "event": "info",
            "payload": "A client has disconnected"
        })