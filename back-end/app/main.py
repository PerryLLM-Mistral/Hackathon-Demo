from fastapi import FastAPI, WebSocket
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
    world = sim_engine.get_state()
    actions = await orchestrator.decide_turn(world)
    delta = sim_engine.apply(actions)
    await manager.broadcast(delta)
    return delta

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

@app.get("/debug")
async def debug():
    world = engine.get_state()
    actions = await orchestrator.decide_turn(world)
    return actions