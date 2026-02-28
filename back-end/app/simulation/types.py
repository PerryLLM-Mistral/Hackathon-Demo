from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

RelationLabel = Literal["WAR", "NEUTRAL", "ALLY"]


class RelationDelta(BaseModel):
    """
    Represents a single changed relation (delta only).
    """
    relation_id: int
    country_1: int
    country_2: int
    old_value: int = Field(ge=-100, le=100)
    new_value: int = Field(ge=-100, le=100)
    label: RelationLabel


class TurnDelta(BaseModel):
    """
    Payload returned by /turns/next and/or broadcast over WS.
    """
    turn: int
    actions: list[dict]  # serialized Action objects
    relation_deltas: List[RelationDelta]
    message: Optional[str] = None