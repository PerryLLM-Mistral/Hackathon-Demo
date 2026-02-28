from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ActionType(str, Enum):
    DECLARE_WAR = "DECLARE_WAR"
    PROPOSE_ALLIANCE = "PROPOSE_ALLIANCE"
    RESPOND_ALLIANCE = "RESPOND_ALLIANCE"
    TRADE = "TRADE"
    SANCTION = "SANCTION"
    PASS = "PASS"


class Action(BaseModel):
    actor_id: str
    type: ActionType
    target_id: Optional[str] = None
    reason: str
    intensity: int = Field(default=1, ge=1, le=3)

    accept: Optional[bool] = None

    @model_validator(mode="after")
    def validate_action(self):
        requires_target = self.type in {
            ActionType.DECLARE_WAR,
            ActionType.PROPOSE_ALLIANCE,
            ActionType.RESPOND_ALLIANCE,
            ActionType.TRADE,
            ActionType.SANCTION,
        }

        if requires_target and self.target_id is None:
            raise ValueError(f"{self.type} requires a target_id")

        if self.type == ActionType.PASS and self.target_id is not None:
            raise ValueError(f"{self.type} should not include a target_id")

        if self.type == ActionType.RESPOND_ALLIANCE and self.accept is None:
            raise ValueError("RESPOND_ALLIANCE requires accept=true/false")

        if self.type != ActionType.RESPOND_ALLIANCE and self.accept is not None:
            raise ValueError("accept is only valid for RESPOND_ALLIANCE")

        if self.target_id == self.actor_id:
            raise ValueError("A country cannot target itself")

        return self