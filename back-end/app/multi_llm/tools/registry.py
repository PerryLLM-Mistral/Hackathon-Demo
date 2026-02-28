from __future__ import annotations

from typing import Callable, Type
from pydantic import BaseModel

from app.multi_llm.tools.war_tool import TOOL_NAME as WAR, TOOL_DESCRIPTION as WAR_DESC, DeclareWarArgs, validate as validate_war
from app.multi_llm.tools.alliance_tool import TOOL_NAME as ALLY, TOOL_DESCRIPTION as ALLY_DESC, AllyArgs, validate as validate_ally
from app.multi_llm.tools.deal_tool import TOOL_NAME as TRADE, TOOL_DESCRIPTION as TRADE_DESC, TradeArgs, validate as validate_trade

ToolValidator = Callable[[BaseModel, object, str], None]

TOOL_SPECS: dict[str, dict] = {
    WAR:   {"description": WAR_DESC,   "args_model": DeclareWarArgs, "validate": validate_war},
    ALLY:  {"description": ALLY_DESC,  "args_model": AllyArgs,       "validate": validate_ally},
    TRADE: {"description": TRADE_DESC, "args_model": TradeArgs,      "validate": validate_trade},
}

def tools_prompt_block() -> str:
    return (
        "Available tools:\n"
        "- DECLARE_WAR: arguments must be {\"target_id\": \"AAA\", \"intensity\": 1-3, \"reason\": \"...\"}\n"
        "- ALLY: arguments must be {\"target_id\": \"AAA\", \"intensity\": 1-3, \"reason\": \"...\"}\n"
        "- TRADE: arguments must be {\"target_id\": \"AAA\", \"intensity\": 1-3, \"reason\": \"...\"}\n"
        "IMPORTANT: Use the key 'target_id' (not 'country', not 'target').\n"
    )