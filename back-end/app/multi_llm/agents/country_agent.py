from __future__ import annotations

import json
import random
import requests
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from pydantic import ValidationError

from app.multi_llm.agents.base import BaseAgent
from app.multi_llm.schemas.action import Action, ActionType
from app.multi_llm.schemas.tool_call import ToolCall
from app.multi_llm.schemas.world import WorldState
from app.multi_llm.tools.registry import TOOL_SPECS, tools_prompt_block

if TYPE_CHECKING:
    from app.multi_llm.llm.provider import MistralProvider


class CountryAgent(BaseAgent):
    """
    Agent for a single country.

    - `decide`: lightweight heuristic fallback (no model call)
    - `decide_llm`: tool-based structured model decision
    """

    def __init__(self, country_id: str, country_name: str, prompt_path: Optional[str] = None):
        super().__init__(country_id=country_id, country_name=country_name)
        self.prompt_text = self._load_prompt(prompt_path) if prompt_path else ""

    def _load_prompt(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def _choose_target(self, world: WorldState) -> Optional[str]:
        candidates = [c.id for c in world.countries if c.id != self.country_id]
        return random.choice(candidates) if candidates else None

    def _get_relation(self, world: WorldState, target_id: str) -> Optional[int]:
        a, b = sorted([self.country_id, target_id])
        for rel in world.relations:
            x, y = sorted([rel.country_1, rel.country_2])
            if x == a and y == b:
                return rel.relation
        return None

    def _normalize_tool_arguments(self, raw_arguments: object, tool_name: str) -> dict:
        """
        Normalize common LLM argument shape mismatches before schema validation.
        """
        if not isinstance(raw_arguments, dict):
            return {}

        args = dict(raw_arguments)

        # Common alias from model outputs.
        if "target_id" not in args and "target" in args:
            args["target_id"] = args["target"]

        if "reason" not in args or not args.get("reason"):
            args["reason"] = f"{tool_name} selected by model"

        if "intensity" not in args:
            args["intensity"] = 1

        return args

    async def decide(self, world: WorldState) -> Action:
        # Small chance to pass to create non-deterministic behavior.
        if random.random() < 0.1:
            return Action(
                actor_id=self.country_id,
                type=ActionType.PASS,
                reason="Strategic pause this turn",
                intensity=1,
            )

        target_id = self._choose_target(world)
        if target_id is None:
            return Action(
                actor_id=self.country_id,
                type=ActionType.PASS,
                reason="No available targets",
                intensity=1,
            )

        relation = self._get_relation(world, target_id)
        if relation is None:
            return Action(
                actor_id=self.country_id,
                type=ActionType.TRADE,
                target_id=target_id,
                reason="Establish initial cooperation",
                intensity=1,
            )

        if relation <= -60:
            return Action(
                actor_id=self.country_id,
                type=ActionType.DECLARE_WAR,
                target_id=target_id,
                reason="Escalating hostile relationship",
                intensity=2,
            )

        if relation >= 60:
            return Action(
                actor_id=self.country_id,
                type=ActionType.ALLY,
                target_id=target_id,
                reason="Strengthen strategic alliance",
                intensity=1,
            )

        return Action(
            actor_id=self.country_id,
            type=ActionType.TRADE,
            target_id=target_id,
            reason="Improve neutral relations",
            intensity=1,
        )

    def _notify_bridge(self, payload: dict):
        """
        Helper to send event data to the FastAPI bridge.
        """
        try:
            # We target localhost:8000 because it is the Docker mapped port
            requests.post(
                "http://localhost:8000/events/broadcast", 
                json={"data": payload},
                timeout=1
            )
        except Exception as e:
            print(f"DEBUG [Bridge Error]: Could not send to browser. {e}")

    async def decide_llm(self, world: WorldState, provider: "MistralProvider") -> Action:
        world_payload = {
            "turn": world.turn,
            "self": self.country_id,
            "countries": [
                {
                    "id": c.id,
                    "name": c.name,
                    "economy": c.economy,
                    "military_power": c.military_power,
                }
                for c in world.countries
            ],
            "relations": [
                {
                    "country_1": r.country_1,
                    "country_2": r.country_2,
                    "relation": r.relation,
                }
                for r in world.relations
            ],
        }

        system_prompt = (
            f"You are {self.country_name} ({self.country_id}).\n"
            "Choose exactly ONE tool that best serves your interests this turn.\n"
            "Be aggressive if relations are bad and you have high military_power.\n\n"
            f"{self.prompt_text}\n\n"
            f"{tools_prompt_block()}\n\n"
            "Output JSON with this schema:\n"
            '{ "tool": "DECLARE_WAR|ALLY|TRADE", "arguments": { ... } }\n'
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "WORLD:\n" + json.dumps(world_payload, indent=2)},
        ]

        tool_call = await provider.complete_json(messages=messages, schema=ToolCall)

        if tool_call.tool not in TOOL_SPECS:
            action = Action(
                actor_id=self.country_id,
                type=ActionType.PASS,
                reason="Unknown tool from model",
                intensity=1,
            )
        
            # NOTIFY: if it fails, inform the frontend
            self._notify_bridge({
                "type": "AGENT_LOG",
                "agent": self.country_id,
                "message": f"Failed to execute action: unknown tool '{tool_call.tool}'"
            })

            return action

        args_model = TOOL_SPECS[tool_call.tool]["args_model"]
        validate_fn = TOOL_SPECS[tool_call.tool]["validate"]

        normalized_args = self._normalize_tool_arguments(tool_call.arguments, tool_call.tool)

        try:
            args = args_model.model_validate(normalized_args)
            validate_fn(args, world, self.country_id)
        except (ValidationError, ValueError) as exc:
            action = Action(
                actor_id=self.country_id,
                type=ActionType.PASS,
                reason=f"Invalid tool arguments from model: {exc}",
                intensity=1,
            )

            # NOTIFY: inform a mistake in the parameters
            self._notify_bridge({
                "type": "AGENT_LOG",
                "agent": self.country_id,
                "message": f"Invalid arguments for {tool_call.tool}. Passing turn."
            })

            return action

        # Success path
        target_id = getattr(args, "target_id", None)
        reason = getattr(args, "reason", "No reason provided")
        intensity = getattr(args, "intensity", 1)

        final_action = Action(
            actor_id=self.country_id,
            type=ActionType(tool_call.tool),
            target_id=target_id,
            reason=reason,
            intensity=intensity,
        )

        # NOTIFY: broadcast the successful action
        self._notify_bridge({
            "type": "AGENT_ACTION",
            "agent": self.country_id,
            "action_type": final_action.type.value,
            "target": target_id,
            "intensity": intensity,
            "reason": reason,
            "message": f"{self.country_id} performs {final_action.type.value} on {target_id or 'themselves'} (Intensity: {intensity})"
        })

        return final_action