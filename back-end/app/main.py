from fastapi import FastAPI, WebSocket
from app.multi_llm.orchestrator import Orchestrator
from app.simulation.engine import SimulationEngine
from app.database import engine as db_engine
from app.src.models import models
from app.src.routes import countries, relationships, simulation, ws, events

# Create the database tables
models.Base.metadata.create_all(bind=db_engine)

app = FastAPI()

orchestrator = Orchestrator()
sim_engine = SimulationEngine()

# Include models routes
app.include_router(countries.router)
app.include_router(relationships.router)
app.include_router(simulation.router)
app.include_router(ws.router)
app.include_router(events.router)