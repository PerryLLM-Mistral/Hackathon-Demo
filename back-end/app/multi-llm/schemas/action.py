# multi-llm/app/schemas/action.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class ActionType(str, Enum):
    DECLARE_WAR = "DECLARE_WAR"
    ALLY = "ALLY"
    TRADE = "TRADE"
    SANCTION = "SANCTION"
    MESSAGE = "MESSAGE"
    PASS = "PASS"

class Action(BaseModel):
    actor: str
    type: ActionType
    target: Optional[str] = None
    reason: str = Field(min_length=1, max_length=280)
    intensity: Optional[int] = Field(default=None, ge=1, le=3)