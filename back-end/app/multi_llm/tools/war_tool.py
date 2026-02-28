# tools/war_tool.py
from pydantic import BaseModel, Field
from typing import Optional

class WarTool:
    name = "war_action"
    description = "Launch a military attack against another country."

    class Schema(BaseModel):
        source_country: str
        target_country: str
        intensity: float = Field(..., ge=0.0, le=1.0)
        justification: Optional[str] = None

    def generate_output(self, action: Schema) -> dict:
        """
        Generates the output that the agent returns.
        """
        return {
            "action_type": "war",
            "source_country": action.source_country,
            "target_country": action.target_country,
            "intensity": action.intensity,
            "justification": action.justification or "No justification provided."
        }