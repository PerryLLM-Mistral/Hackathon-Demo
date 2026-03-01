from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.multi_llm.orchestrator import Orchestrator
from app.simulation.engine import SimulationEngine
from app.database import engine as db_engine
from app.src.models import models
from app.src.routes import countries, relationships, simulation, ws, events
from app.scripts.seed_db import seed 

# Create the database tables
models.Base.metadata.create_all(bind=db_engine)

app = FastAPI()

# ===============================
# STARTUP EVENT (AUTO SEED)
# ===============================
@app.on_event("startup")
async def startup_event():
    from app.database import SessionLocal
    db = SessionLocal()
    country_count = db.query(models.Country).count()
    db.close()

    if country_count == 0:
        print("Database empty. Running initial seed...")
        await seed()
        print("Seed finished successfully")
    else:
        print("Database already initialized. Skipping seed.")
# ===============================
# CORS CONFIGURATION
# ===============================
origins = [
    "http://172.24.0.3:5173",   # Local Vite
    "http://react_frontend:3000"  # Docker Compose
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# CORE ENGINE INSTANCES
# ===============================
orchestrator = Orchestrator()
sim_engine = SimulationEngine()

# ===============================
# ROUTERS
# ===============================
app.include_router(countries.router)
app.include_router(relationships.router)
app.include_router(simulation.router)
app.include_router(ws.router)
app.include_router(events.router)