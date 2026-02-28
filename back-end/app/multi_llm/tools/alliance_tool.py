# tools/alliance_tool.py
from pydantic import BaseModel, Field
from typing import Optional

class AllianceTool:
    name = "alliance_action"
    description = "Propose an alliance with another country."

    class Schema(BaseModel):
        source_country: str
        target_country: str
        duration_turns: int = Field(..., gt=0)
        justification: Optional[str] = None

    def generate_output(self, action: Schema) -> dict:
        """
        Generates the output that the agent returns.
        """
        return {
            "action_type": "alliance",
            "source_country": action.source_country,
            "target_country": action.target_country,
            "duration_turns": action.duration_turns,
            "justification": action.justification or "No justification provided."
        }