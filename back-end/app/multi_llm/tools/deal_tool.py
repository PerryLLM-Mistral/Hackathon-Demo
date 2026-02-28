from pydantic import BaseModel, Field
from app.multi_llm.schemas.world import WorldState

TOOL_NAME = "TRADE"
TOOL_DESCRIPTION = "Propose trade. Improves relations moderately."

class TradeArgs(BaseModel):
    target_id: str = Field(min_length=3, max_length=3)
    intensity: int = Field(default=1, ge=1, le=3)
    reason: str = Field(min_length=1, max_length=280)

def validate(args: TradeArgs, world: WorldState, actor_id: str) -> None:
    ids = {c.id for c in world.countries}
    if actor_id not in ids:
        raise ValueError("Invalid actor_id")
    if args.target_id not in ids:
        raise ValueError("Invalid target_id")
    if args.target_id == actor_id:
        raise ValueError("Cannot trade with self")