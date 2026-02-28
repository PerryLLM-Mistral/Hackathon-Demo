# app/src/routes/simulation.py
from fastapi import APIRouter
from app.multi_llm.orchestrator import Orchestrator
from app.simulation.engine import SimulationEngine
from app.ws import manager

router = APIRouter(prefix="/simulation", tags=["Simulation"])

orchestrator = Orchestrator()
sim_engine = SimulationEngine()


@router.post("/step")
async def step():
    """
    Advance one simulation step and broadcast the changes to all clients
    """
    world = sim_engine.get_state()
    actions = await orchestrator.decide_turn(world)
    delta = sim_engine.apply(actions)

    await manager.broadcast({
        "event": "step_update",
        "payload": delta
    })

    return delta