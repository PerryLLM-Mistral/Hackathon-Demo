# app/multi_llm/tools/respond_alliance_tool.py

from __future__ import annotations

from pydantic import BaseModel, Field, AliasChoices

from app.multi_llm.schemas.world import WorldState


TOOL_NAME = "RESPOND_ALLIANCE"
TOOL_DESCRIPTION = "Accept or reject an alliance proposal. Produces a quantitative relation delta."


class RespondAllianceArgs(BaseModel):
    target_id: str = Field(
        validation_alias=AliasChoices("target_id", "country", "target"),
        min_length=3,
        max_length=3,
        description="3-letter country id of the proposer you respond to, e.g. 'USA'",
    )
    accept: bool = Field(
        validation_alias=AliasChoices("accept", "accepted", "approve", "agree"),
        description="true to accept, false to reject",
    )
    reason: str = Field(
        validation_alias=AliasChoices("reason", "because", "motivation"),
        min_length=1,
        max_length=280,
    )


def validate(args: RespondAllianceArgs, world: WorldState, actor_id: str) -> None:
    ids = {c.id for c in world.countries}

    if actor_id not in ids:
        raise ValueError(f"Invalid actor_id: {actor_id}")

    if args.target_id not in ids:
        raise ValueError(f"Invalid target_id: {args.target_id}")

    if args.target_id == actor_id:
        raise ValueError("Cannot respond to self")