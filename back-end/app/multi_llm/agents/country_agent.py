from __future__ import annotations

import json
import random
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

    async def decide_llm(self, world: WorldState, provider: "MistralProvider") -> Action:

        # ---------- helpers locales ----------
        def _pending_requesters_for_me() -> list[str]:
            reqs: list[str] = []
            for r in world.relations:
                requester = getattr(r, "pending_alliance_from", None)
                if not requester:
                    continue
                if self.country_id not in (r.country_1, r.country_2):
                    continue
                other = r.country_2 if r.country_1 == self.country_id else r.country_1
                # si el requester es el "other" del par, entonces esa petición va dirigida a mí
                if requester == other:
                    reqs.append(requester)
            return reqs

        def _relation_with(other_id: str) -> int:
            for r in world.relations:
                if (r.country_1 == self.country_id and r.country_2 == other_id) or (
                    r.country_2 == self.country_id and r.country_1 == other_id
                ):
                    return int(r.relation)
            return 0

        # ---------- MUST RESPOND ----------
        pending_requesters = _pending_requesters_for_me()
        forced_mode = bool(pending_requesters)
        forced_requester = pending_requesters[0] if forced_mode else None

        # ---------- payload: incluye pending_alliance_from ----------
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
                    "pending_alliance_from": getattr(r, "pending_alliance_from", None),
                }
                for r in world.relations
            ],
        }

        # ---------- tool restriction ----------
        if forced_mode:
            # RESPOND_ALLIANCE only allowed
            allowed_tools = {"RESPOND_ALLIANCE"}
            # limited TOOL_SPECS
            tool_specs = {k: v for k, v in TOOL_SPECS.items() if k in allowed_tools}

            rel_score = _relation_with(forced_requester)
            tools_block = (
                "Available tools:\n"
                "- RESPOND_ALLIANCE: arguments must be {\"target_id\": \"AAA\", \"accept\": true|false, \"reason\": \"...\"}\n"
                "IMPORTANT: Use the key 'target_id'.\n"
            )

            system_prompt = (
                f"You are {self.country_name} ({self.country_id}).\n"
                f"You have a PENDING alliance proposal from {forced_requester}.\n"
                f"Your current relation score with {forced_requester} is {rel_score} (range -100..100).\n"
                "You MUST choose RESPOND_ALLIANCE now.\n\n"
                f"{self.prompt_text}\n\n"
                f"{tools_block}\n\n"
                "Output JSON with this schema:\n"
                '{ "tool": "RESPOND_ALLIANCE", "arguments": { ... } }\n'
            )
        else:
            # Normal mode
            tool_specs = TOOL_SPECS

            system_prompt = (
                f"You are {self.country_name} ({self.country_id}).\n"
                "Choose exactly ONE tool that best serves your interests this turn.\n"
                "Be aggressive if relations are bad and you have high military_power.\n\n"
                f"{self.prompt_text}\n\n"
                f"{tools_prompt_block()}\n\n"
                "Output JSON with this schema:\n"
                '{ "tool": "DECLARE_WAR|PROPOSE_ALLIANCE|RESPOND_ALLIANCE|TRADE", "arguments": { ... } }\n'
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "WORLD:\n" + json.dumps(world_payload, indent=2)},
        ]

        # ---------- call model ----------
        tool_call = await provider.complete_json(messages=messages, schema=ToolCall)

        # ---------- validate tool name against allowed set ----------
        if tool_call.tool not in tool_specs:
            return Action(
                actor_id=self.country_id,
                type=ActionType.PASS,
                reason="Unknown or disallowed tool from model",
                intensity=1,
            )

        args_model = tool_specs[tool_call.tool]["args_model"]
        validate_fn = tool_specs[tool_call.tool]["validate"]

        normalized_args = self._normalize_tool_arguments(tool_call.arguments, tool_call.tool)

        # En modo forced, si el modelo no puso target_id, lo forzamos al requester para evitar bloqueos
        if forced_mode and tool_call.tool == "RESPOND_ALLIANCE":
            normalized_args.setdefault("target_id", forced_requester)

        try:
            args = args_model.model_validate(normalized_args)
            validate_fn(args, world, self.country_id)
        except (ValidationError, ValueError) as exc:
            # fallback heurístico si está en forced_mode (para que nunca se quede sin responder)
            if forced_mode:
                rel_score = _relation_with(forced_requester)
                accept = rel_score >= 10
                return Action(
                    actor_id=self.country_id,
                    type=ActionType.RESPOND_ALLIANCE,
                    target_id=forced_requester,
                    accept=accept,
                    reason=("Accept (fallback): relations sufficiently positive." if accept else "Reject (fallback): insufficient trust/benefit."),
                    intensity=1,
                )

            return Action(
                actor_id=self.country_id,
                type=ActionType.PASS,
                reason=f"Invalid tool arguments from model: {exc}",
                intensity=1,
            )

        # ---------- build Action ----------
        return Action(
            actor_id=self.country_id,
            type=ActionType(tool_call.tool),
            target_id=getattr(args, "target_id", None),
            reason=getattr(args, "reason", "No reason"),
            intensity=getattr(args, "intensity", 1),
            accept=getattr(args, "accept", None),
        )