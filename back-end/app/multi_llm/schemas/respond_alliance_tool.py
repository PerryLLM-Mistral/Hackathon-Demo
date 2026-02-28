from pydantic import BaseModel, Field, AliasChoices
from app.multi_llm.schemas.world import WorldState

TOOL_NAME = "RESPOND_ALLIANCE"
TOOL_DESCRIPTION = "Accept or reject an alliance proposal. Changes relation quantitatively."

class RespondAllianceArgs(BaseModel):
    target_id: str = Field(
        validation_alias=AliasChoices("target_id", "country", "target"),
        min_length=3,
        max_length=3,
    )
    accept: bool = Field(validation_alias=AliasChoices("accept", "accepted", "approve"))
    reason: str = Field(
        validation_alias=AliasChoices("reason", "because", "motivation"),
        min_length=1,
        max_length=280
    )

def validate(args: RespondAllianceArgs, world: WorldState, actor_id: str) -> None:
    ids = {c.id for c in world.countries}
    if actor_id not in ids:
        raise ValueError("Invalid actor_id")
    if args.target_id not in ids:
        raise ValueError("Invalid target_id")
    if args.target_id == actor_id:
        raise ValueError("Cannot respond to self")