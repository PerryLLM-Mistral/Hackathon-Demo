# tools/deal_tool.py
from pydantic import BaseModel, Field
from typing import Optional

class DealTool:
    name = "deal_action"
    description = "Negotiate a trade or strategic deal."

    class Schema(BaseModel):
        source_country: str
        target_country: str
        deal_value: int = Field(..., gt=0)
        deal_type: str = Field(..., description="Type of deal, e.g., trade, military, energy, technology")
        justification: Optional[str] = None

    def generate_output(self, action: Schema) -> dict:
        """
        Generates the output that the agent returns.
        """
        return {
            "action_type": "deal",
            "source_country": action.source_country,
            "target_country": action.target_country,
            "deal_value": action.deal_value,
            "deal_type": action.deal_type,
            "justification": action.justification or "No justification provided."
        }