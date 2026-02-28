from pydantic import BaseModel
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
    reason: str