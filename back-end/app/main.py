from fastapi import FastAPI, WebSocket
from app.multi_llm.orchestrator import Orchestrator
from app.simulation.engine import SimulationEngine
from app.database import engine as db_engine
from app.src.models import models
from app.src.routes import countries, relationships, simulation, ws, events
from fastapi.middleware.cors import CORSMiddleware

# Create the database tables
models.Base.metadata.create_all(bind=db_engine)

app = FastAPI()

# CORS
origins = [
    "http://172.24.0.3:5173/",          # using local
    "http://react_frontend:3000/"            # using Docker Compose
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=[""],
)

orchestrator = Orchestrator()
sim_engine = SimulationEngine()

# Include models routes
app.include_router(countries.router)
app.include_router(relationships.router)
app.include_router(simulation.router)
app.include_router(ws.router)
app.include_router(events.router)