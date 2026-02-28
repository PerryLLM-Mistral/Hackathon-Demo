# multi-llm/app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from app.schemas.world import WorldState
from app.schemas.action import Action

class DecideRequest(BaseModel):
    actor_id: str
    world: WorldState

class DecideResponse(BaseModel):
    action: Action
    raw_text: str | None = None

app = FastAPI()

@app.post("/decide", response_model=DecideResponse)
def decide(req: DecideRequest):
    # 1) Create prompt: actor_id + world
    # 2) Call LLM
    # 3) Action parsing and return
    action = Action(actor=req.actor_id, type="PASS", reason="No action")
    return DecideResponse(action=action, raw_text=None)