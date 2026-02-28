from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.multi_llm.orchestrator import Orchestrator
from app.simulation.engine import SimulationEngine
from app.ws import manager
from app.database import engine as db_engine, Base
from app.src.models import models
from app.src.routes import countries, relationships

# Create the database tables
models.Base.metadata.create_all(bind=db_engine)

app = FastAPI()

orchestrator = Orchestrator()
sim_engine = SimulationEngine()

# Include models routes
app.include_router(countries.router)
app.include_router(relationships.router)

@app.post("/step")
async def step():
    """
    Advance one step and broadcast the changes to all clients
    """
    world = sim_engine.get_state()
    actions = await orchestrator.decide_turn(world)
    delta = sim_engine.apply(actions)

    # Broadcast to all connected clients
    await manager.broadcast({
        "event": "step_update",
        "payload": delta
    })
    return delta

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication with front-end clients
    """
    # Connect the client
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

        # Notify remaining clients
        await manager.broadcast({
            "event": "info",
            "payload": "A client has disconnected"
        })