from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ActionType(str, Enum):
    """
    Enumeration of all diplomatic actions that an agent can perform.
    These represent the only allowed tools in the system.
    """
    DECLARE_WAR = "DECLARE_WAR"
    ALLY = "ALLY"
    TRADE = "TRADE"
    SANCTION = "SANCTION"
    MESSAGE = "MESSAGE"
    PASS = "PASS"


class Action(BaseModel):
    """
    Structured diplomatic action proposed by an agent.
    """

    actor_id: str  # e.g., "USA"
    type: ActionType
    target_id: Optional[str] = None  # e.g., "CHI"
    reason: str
    intensity: int = Field(default=1, ge=1, le=3)

    @model_validator(mode="after")
    def validate_action(self):
        """
        Ensures logical consistency between action type and target.
        """

        requires_target = self.type in {
            ActionType.DECLARE_WAR,
            ActionType.ALLY,
            ActionType.TRADE,
            ActionType.SANCTION,
        }

        if requires_target and self.target_id is None:
            raise ValueError(f"{self.type} requires a target_id")

        if self.type in {ActionType.PASS, ActionType.MESSAGE} and self.target_id is not None:
            raise ValueError(f"{self.type} should not include a target_id")

        if self.target_id == self.actor_id:
            raise ValueError("A country cannot target itself")

        return self