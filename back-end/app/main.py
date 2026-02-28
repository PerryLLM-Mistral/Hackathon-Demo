from fastapi import FastAPI, WebSocket
from app.multi_llm.orchestrator import Orchestrator
from app.simulation.engine import SimulationEngine
from app.ws import manager

app = FastAPI()

orchestrator = Orchestrator()
engine = SimulationEngine()

@app.post("/step")
async def step():
    world = engine.get_state()
    actions = await orchestrator.decide_turn(world)
    delta = engine.apply(actions)
    await manager.broadcast(delta)
    return delta

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)