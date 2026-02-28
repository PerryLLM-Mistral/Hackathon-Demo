# app/multi_llm/tools/alliance_tool.py

from pydantic import BaseModel, Field
from app.multi_llm.schemas.world import WorldState

TOOL_NAME = "ALLY"
TOOL_DESCRIPTION = "Form or strengthen an alliance. Improves relations strongly."

class AllyArgs(BaseModel):
    target_id: str = Field(min_length=3, max_length=3)
    intensity: int = Field(default=1, ge=1, le=3)
    reason: str = Field(min_length=1, max_length=280)

def validate(args: AllyArgs, world: WorldState, actor_id: str) -> None:
    """
    Validation only. No side effects, no DB calls.
    """
    ids = {c.id for c in world.countries}
    if actor_id not in ids:
        raise ValueError("Invalid actor_id")
    if args.target_id not in ids:
        raise ValueError("Invalid target_id")
    if args.target_id == actor_id:
        raise ValueError("Cannot ally with self")