from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    """
    What the LLM returns: a tool name + JSON arguments.
    """
    tool: str = Field(min_length=1)
    arguments: Dict[str, Any]