# app/src/routes/simulation.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.multi_llm.orchestrator import Orchestrator
from app.simulation.engine import SimulationEngine
from app.ws import manager

router = APIRouter(prefix="/simulation", tags=["Simulation"])

orchestrator = Orchestrator()
sim_engine = SimulationEngine()

RUN_ID = "demo"


@router.post("/step")
async def step(db: Session = Depends(get_db)):
    """
    Advance one simulation step:
      - lazy-load initial state from DB (countries + relationships)
      - decide actions
      - apply in memory
      - persist Turn + ActionHistory
      - broadcast delta via websocket
    """
    sim_engine.ensure_loaded(db, RUN_ID)

    world = sim_engine.get_state()
    actions = await orchestrator.decide_turn(world)

    # order
    order = [a.actor_id for a in actions]

    delta = sim_engine.apply(db=db, run_id=RUN_ID, actions=actions, order=order)

    await manager.broadcast({"event": "step_update", "payload": delta})
    return delta