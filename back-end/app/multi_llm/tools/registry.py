# app/multi_llm/tools/registry.py

from __future__ import annotations

from typing import Callable
from pydantic import BaseModel

from app.multi_llm.tools.war_tool import (
    TOOL_NAME as WAR,
    TOOL_DESCRIPTION as WAR_DESC,
    DeclareWarArgs,
    validate as validate_war,
)

from app.multi_llm.tools.alliance_tool import (
    TOOL_NAME as PROPOSE_ALLIANCE,
    TOOL_DESCRIPTION as PROPOSE_ALLIANCE_DESC,
    ProposeAllianceArgs,
    validate as validate_propose_alliance,
)

from app.multi_llm.tools.respond_alliance_tool import (
    TOOL_NAME as RESPOND_ALLIANCE,
    TOOL_DESCRIPTION as RESPOND_ALLIANCE_DESC,
    RespondAllianceArgs,
    validate as validate_respond_alliance,
)

from app.multi_llm.tools.deal_tool import (
    TOOL_NAME as TRADE,
    TOOL_DESCRIPTION as TRADE_DESC,
    TradeArgs,
    validate as validate_trade,
)

ToolValidator = Callable[[BaseModel, object, str], None]


TOOL_SPECS: dict[str, dict] = {
    WAR: {
        "description": WAR_DESC,
        "args_model": DeclareWarArgs,
        "validate": validate_war,
    },
    PROPOSE_ALLIANCE: {
        "description": PROPOSE_ALLIANCE_DESC,
        "args_model": ProposeAllianceArgs,
        "validate": validate_propose_alliance,
    },
    RESPOND_ALLIANCE: {
        "description": RESPOND_ALLIANCE_DESC,
        "args_model": RespondAllianceArgs,
        "validate": validate_respond_alliance,
    },
    TRADE: {
        "description": TRADE_DESC,
        "args_model": TradeArgs,
        "validate": validate_trade,
    },
}


def tools_prompt_block() -> str:
    return (
        "Available tools:\n"
        "- DECLARE_WAR: {\"target_id\": \"AAA\", \"intensity\": 1-3, \"reason\": \"...\"}\n"
        "- PROPOSE_ALLIANCE: {\"target_id\": \"AAA\", \"intensity\": 1-3, \"reason\": \"...\"}\n"
        "- RESPOND_ALLIANCE: {\"target_id\": \"AAA\", \"accept\": true|false, \"reason\": \"...\"}\n"
        "- TRADE: {\"target_id\": \"AAA\", \"intensity\": 1-3, \"reason\": \"...\"}\n"
        "IMPORTANT: Use the key 'target_id'.\n"
    )