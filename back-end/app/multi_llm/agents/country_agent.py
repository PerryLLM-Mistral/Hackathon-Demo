from __future__ import annotations

import json
import secrets
from math import exp
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from pydantic import ValidationError

from app.multi_llm.agents.base import BaseAgent
from app.multi_llm.schemas.action import Action, ActionType
from app.multi_llm.schemas.tool_call import ToolCall
from app.multi_llm.schemas.world import WorldState
from app.multi_llm.tools.registry import TOOL_SPECS

if TYPE_CHECKING:
    from app.multi_llm.llm.provider import MistralProvider


class CountryAgent(BaseAgent):
    """
    Agent for a single country.

    - decide_llm: tool-based LLM decision + exploration:
        * MUST RESPOND to pending alliances
        * sometimes "conflict explore" to force SANCTION/WAR consideration
        * nonce embedded in WORLD payload to reduce repeated outputs

    Also:
    - Notifies FastAPI bridge (/events/broadcast) with AGENT_LOG / AGENT_ACTION events.
    """

    def __init__(self, country_id: str, country_name: str, prompt_path: Optional[str] = None):
        super().__init__(country_id=country_id, country_name=country_name)
        self.prompt_text = self._load_prompt(prompt_path) if prompt_path else ""

        self._rng = secrets.SystemRandom()

        # last action cooldown
        self._last_action: Optional[tuple[ActionType, Optional[str], int]] = None

        # exploration knobs (tune)
        self.conflict_explore_prob = 0.18   # 18% of normal turns: bias towards SANCTION/WAR
        self.min_econ_for_alliance = 30    # Do not accept poor alliates
        self.min_social_for_war = 40          # A country with bad social status does not want wars

    def _load_prompt(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    # -------------------------
    # World helpers
    # -------------------------
    def _get_relation_state(self, world: WorldState, other_id: str):
        for r in world.relations:
            if (r.country_1 == self.country_id and r.country_2 == other_id) or (
                r.country_2 == self.country_id and r.country_1 == other_id
            ):
                return r
        return None

    def _get_relation(self, world: WorldState, other_id: str) -> int:
        rel = self._get_relation_state(world, other_id)
        return int(rel.relation) if rel is not None else 0

    def _get_country(self, world: WorldState, cid: str):
        for c in world.countries:
            if c.id == cid:
                return c
        return None

    def _get_stat(self, world: WorldState, cid: str, stat: str) -> int:
        c = next((x for x in world.countries if x.id == cid), None)
        return int(getattr(c, stat, 0) or 0) if c else 0

    def _military(self, world: WorldState, cid: str) -> int:
        c = self._get_country(world, cid)
        return int(getattr(c, "military_power", 0) or 0) if c else 0

    def _pending_requesters_for_me(self, world: WorldState) -> list[str]:
        reqs: list[str] = []
        for r in world.relations:
            requester = getattr(r, "pending_alliance_from", None)
            if not requester:
                continue
            if self.country_id not in (r.country_1, r.country_2):
                continue
            other = r.country_2 if r.country_1 == self.country_id else r.country_1
            if requester == other:
                reqs.append(requester)
        return reqs

    def _choose_target_stochastic(self, world: WorldState) -> Optional[str]:
        targets = [c.id for c in world.countries if c.id != self.country_id]
        if not targets:
            return None

        weights = []
        for tid in targets:
            rel = self._get_relation(world, tid)
            w = 0.8 + abs(rel) / 60.0 + self._rng.uniform(-0.20, 0.20)
            weights.append(max(0.01, w))

        total = sum(weights)
        r = self._rng.random() * total
        acc = 0.0
        for tid, w in zip(targets, weights):
            acc += w
            if r <= acc:
                return tid
        return targets[-1]

    def _tools_block_for(self, tool_specs: dict[str, dict]) -> str:
        lines = ["Available tools:"]
        if "DECLARE_WAR" in tool_specs:
            lines.append('- DECLARE_WAR: {"target_id": "AAA", "intensity": 1-3, "reason": "..."}')
        if "PROPOSE_ALLIANCE" in tool_specs:
            lines.append('- PROPOSE_ALLIANCE: {"target_id": "AAA", "intensity": 1-3, "reason": "..."}')
        if "RESPOND_ALLIANCE" in tool_specs:
            lines.append('- RESPOND_ALLIANCE: {"target_id": "AAA", "accept": true|false, "reason": "..."}')
        if "TRADE" in tool_specs:
            lines.append('- TRADE: {"target_id": "AAA", "intensity": 1-3, "reason": "..."}')
        if "SANCTION" in tool_specs:
            lines.append('- SANCTION: {"target_id": "AAA", "intensity": 1-3, "reason": "..."}')
        if "PASS" in tool_specs:
            lines.append('- PASS: {"reason": "..."}')
        lines.append("IMPORTANT: Use the key 'target_id'.")
        return "\n".join(lines) + "\n"

    # -------------------------
    # Tool argument normalization
    # -------------------------
    def _normalize_tool_arguments(self, raw_arguments: object, tool_name: str) -> dict:
        if not isinstance(raw_arguments, dict):
            return {}

        args = dict(raw_arguments)

        # normalize target_id
        if "target_id" not in args and "target" in args:
            args["target_id"] = args["target"]

        # ensure reason exists
        if "reason" not in args or not args.get("reason"):
            args["reason"] = f"{tool_name} selected by model"

        # enforce max length
        MAX_REASON = 280
        reason = str(args.get("reason", ""))
        if len(reason) > MAX_REASON:
            args["reason"] = reason[: MAX_REASON - 3].rstrip() + "..."

        # default intensity
        if "intensity" not in args:
            args["intensity"] = 1

        return args
    
        # -------------------------
    # Match guards (hard constraints)
    # -------------------------
    def _match_country_ids(self, world: WorldState) -> set[str]:
        return {c.id for c in world.countries}

    def _assert_actor_in_match(self, world: WorldState) -> None:
        ids = self._match_country_ids(world)
        if self.country_id not in ids:
            raise ValueError(f"Actor {self.country_id} is not in match countries: {sorted(ids)}")

    def _assert_target_in_match(self, world: WorldState, target_id: Optional[str], tool_name: str) -> None:
        # Tools without target are allowed (e.g., PASS if ever enabled)
        if not target_id:
            return
        ids = self._match_country_ids(world)
        if target_id not in ids:
            raise ValueError(
                f"Invalid target_id '{target_id}' for tool {tool_name}. "
                f"Allowed target_ids: {sorted(ids)}"
            )
        if target_id == self.country_id:
            raise ValueError(f"Invalid target_id '{target_id}': cannot target self for tool {tool_name}")


    # -------------------------
    # LLM tool-based decision
    # -------------------------
    async def decide_llm(self, world: WorldState, provider: "MistralProvider") -> Action:
        pending_requesters = self._pending_requesters_for_me(world)
        forced_mode = bool(pending_requesters)
        forced_requester = pending_requesters[0] if forced_mode else None

        # Hard invariant: the agent itself must be one of the match countries
        self._assert_actor_in_match(world)

        # If forced requester exists, it must also be in the match countries
        if forced_requester is not None:
            self._assert_target_in_match(world, forced_requester, "RESPOND_ALLIANCE(forced)")

        nonce = self._rng.randint(1, 1_000_000)
        payload_nonce = self._rng.randint(1, 1_000_000)

        world_payload = {
            "turn": world.turn,
            "self": self.country_id,
            "nonce": payload_nonce,
            "countries": [
                {"id": c.id, "name": c.name, "economy": c.economy, "military_power": c.military_power}
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

        explore_conflict = (not forced_mode) and (self._rng.random() < self.conflict_explore_prob)

        if forced_mode:
            tool_specs = {k: v for k, v in TOOL_SPECS.items() if k == "RESPOND_ALLIANCE"}
            tools_block = self._tools_block_for(tool_specs)
            rel_score = self._get_relation(world, forced_requester)

            system_prompt = (
                f"You are {self.country_name} ({self.country_id}).\n"
                f"You have a PENDING alliance proposal from {forced_requester}.\n"
                f"Current relation score with {forced_requester}: {rel_score} (range -100..100).\n"
                "You MUST choose RESPOND_ALLIANCE now.\n"
                f"(Decision nonce: {nonce})\n\n"
                f"{self.prompt_text}\n\n"
                f"{tools_block}\n"
                'Output JSON: { "tool": "RESPOND_ALLIANCE", "arguments": { ... } }\n'
            )
            temperature = 0.6
            top_p = 0.9
        else:
            allowed = set(TOOL_SPECS.keys())
            allowed.discard("PASS")

            if self._last_action is not None:
                last_type, _, last_turn = self._last_action
                if last_turn == world.turn - 1:
                    allowed.discard(getattr(last_type, "name", str(last_type)))

            if explore_conflict:
                allowed = allowed.intersection({"SANCTION", "DECLARE_WAR", "TRADE"})

            tool_specs = {k: v for k, v in TOOL_SPECS.items() if k in allowed}
            tools_block = self._tools_block_for(tool_specs)

            system_prompt = (
                f"You are {self.country_name} ({self.country_id}).\n"
                "Choose exactly ONE tool that best serves your interests this turn.\n"
                "CRITICAL: Your 'reason' must be a unique, context-aware sentence.\n"
                "Rules:\n"
                "- Do NOT repeat the same tool in consecutive turns.\n"
                "- Only choose DECLARE_WAR if relation <= -30.\n"
                "- Consider SANCTION if relation <= -10 and war is not justified.\n"
                "- If a relation already has pending_alliance_from set, do NOT choose PROPOSE_ALLIANCE for that same pair.\n"
                "- Do NOT ally with 'poor' countries (economy < 30).\n"
                "- If your economy is low, prioritize TRADE to recover funds.\n"
                "- Avoid DECLARE_WAR if the target has much higher military_power than you.\n"
                "- Keep \"reason\" <= 200 characters (hard limit 280).\n"
                f"- Exploration mode: {explore_conflict}.\n\n"
                f"(Decision nonce: {nonce})\n\n"
                f"{self.prompt_text}\n\n"
                f"{tools_block}\n"
                'Output JSON: { "tool": "DECLARE_WAR|PROPOSE_ALLIANCE|RESPOND_ALLIANCE|TRADE|SANCTION", "arguments": { ... } }\n'
            )
            temperature = 0.95
            top_p = 0.95

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "WORLD:\n" + json.dumps(world_payload, indent=2)},
        ]

        async def _call_and_normalize(msgs, temp, tp) -> tuple[str, ToolCall]:
            tc = await provider.complete_json(
                messages=msgs,
                schema=ToolCall,
                temperature=temp,
                top_p=tp,
            )
            raw_tool = tc.tool
            tool_name = raw_tool.value if isinstance(raw_tool, ActionType) else str(raw_tool)
            tool_name = tool_name.strip().upper()
            return tool_name, tc

        tool_name, tool_call = await _call_and_normalize(messages, temperature, top_p)
        
        # Tools = Actions
        if tool_name not in tool_specs:
            fix_messages = messages + [
                {
                    "role": "system",
                    "content": (
                        "Your previous tool choice was INVALID for this turn. "
                        f"You MUST choose one of: {sorted(tool_specs.keys())}. "
                        "Return ONLY valid JSON with keys: tool, arguments."
                    ),
                }
            ]
            tool_name2, tool_call2 = await _call_and_normalize(fix_messages, 0.2, 0.9)

            if tool_name2 in tool_specs:
                tool_name, tool_call = tool_name2, tool_call2
            else:
                priority = ["TRADE", "SANCTION", "PROPOSE_ALLIANCE", "DECLARE_WAR", "RESPOND_ALLIANCE"]
                tool_name = next((t for t in priority if t in tool_specs), next(iter(tool_specs.keys())))

        args_model = tool_specs[tool_name]["args_model"]
        validate_fn = tool_specs[tool_name]["validate"]
        normalized_args = self._normalize_tool_arguments(tool_call.arguments, tool_name)
        # Hard constraint BEFORE pydantic/validate_fn: target (if any) must be in match
        self._assert_target_in_match(world, normalized_args.get("target_id"), tool_name)

        if forced_mode and tool_name == "RESPOND_ALLIANCE":
            normalized_args.setdefault("target_id", forced_requester)
            self._assert_target_in_match(world, normalized_args.get("target_id"), tool_name)

        # Validate args
        try:
            args = args_model.model_validate(normalized_args)
            validate_fn(args, world, self.country_id)
        except (ValidationError, ValueError) as exc:
            fix_messages = messages + [
                {
                    "role": "system",
                    "content": (
                        "Your JSON arguments were INVALID for the chosen tool. "
                        f"Tool: {tool_name}. Error: {str(exc)}. "
                        "Fix your JSON and return ONLY valid JSON."
                    ),
                }
            ]
            tool_name2, tool_call2 = await _call_and_normalize(fix_messages, 0.2, 0.9)

            # If tool changed, it must still be allowed
            if tool_name2 not in tool_specs:
                priority = ["TRADE", "SANCTION", "PROPOSE_ALLIANCE", "DECLARE_WAR", "RESPOND_ALLIANCE"]
                tool_name2 = next((t for t in priority if t in tool_specs), next(iter(tool_specs.keys())))

            tool_name, tool_call = tool_name2, tool_call2

            args_model = tool_specs[tool_name]["args_model"]
            validate_fn = tool_specs[tool_name]["validate"]
            normalized_args = self._normalize_tool_arguments(tool_call.arguments, tool_name)
            self._assert_target_in_match(world, normalized_args.get("target_id"), tool_name)

            if forced_mode and tool_name == "RESPOND_ALLIANCE":
                normalized_args.setdefault("target_id", forced_requester)
                self._assert_target_in_match(world, normalized_args.get("target_id"), tool_name)

            args = args_model.model_validate(normalized_args)
            validate_fn(args, world, self.country_id)

        action = Action(
            actor_id=self.country_id,
            type=ActionType(tool_name),
            target_id=getattr(args, "target_id", None),
            reason=getattr(args, "reason", "No reason"),
            intensity=getattr(args, "intensity", 1),
            accept=getattr(args, "accept", None),
        )

        self._last_action = (action.type, action.target_id, world.turn)
        return action