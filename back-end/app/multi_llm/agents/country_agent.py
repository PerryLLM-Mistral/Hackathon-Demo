from __future__ import annotations

import json
import random
import requests
from math import exp
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

    - decide: heuristic fallback (no model call), stochastic + constraints
    - decide_llm: model-based tool decision with constraints:
        * MUST RESPOND to pending alliance proposals
        * dynamic tool restrictions (cooldowns / no-spam)
        * nonce in prompt to reduce repeated outputs
        * higher temperature for diversity

    Additionally:
    - Notifies FastAPI bridge (/events/broadcast) with AGENT_LOG / AGENT_ACTION events.
    """

    def __init__(self, country_id: str, country_name: str, prompt_path: Optional[str] = None):
        super().__init__(country_id=country_id, country_name=country_name)
        self.prompt_text = self._load_prompt(prompt_path) if prompt_path else ""
        # in-memory cooldown
        self._last_action: Optional[tuple[ActionType, Optional[str], int]] = None

    def _load_prompt(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    # -------------------------
    # Bridge notifications (FROM v1)
    # -------------------------
    def _notify_bridge(self, payload: dict):
        """
        Helper to send event data to the FastAPI bridge.
        """
        try:
            # We target localhost:8000 because it is the Docker mapped port
            requests.post(
                "http://127.0.0.1:8000/events/broadcast",
                json={"data": payload},
                timeout=1,
            )
        except Exception as e:
            print(f"DEBUG [Bridge Error]: Could not send to browser. {e}")

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

    def _pending_requesters_for_me(self, world: WorldState) -> list[str]:
        """
        A pending alliance directed to THIS agent happens when:
        - relation involves self.country_id
        - relation.pending_alliance_from equals the other side of that relation
        """
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
        """
        Stochastic target choice: prefer extreme relations slightly + noise.
        Avoid deterministic "always pick same target".
        """
        targets = [c.id for c in world.countries if c.id != self.country_id]
        if not targets:
            return None

        weights = []
        for tid in targets:
            rel = self._get_relation(world, tid)
            w = 0.8 + abs(rel) / 70.0 + random.uniform(-0.15, 0.15)
            weights.append(max(0.01, w))

        total = sum(weights)
        r = random.random() * total
        acc = 0.0
        for tid, w in zip(targets, weights):
            acc += w
            if r <= acc:
                return tid
        return targets[-1]

    def _tools_block_for(self, tool_specs: dict[str, dict]) -> str:
        """
        Build a tools block that only lists the currently allowed tools.
        This prevents the model from picking a disallowed option and causing PASS.
        """
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

        if "target_id" not in args and "target" in args:
            args["target_id"] = args["target"]

        if "reason" not in args or not args.get("reason"):
            args["reason"] = f"{tool_name} selected by model"

        # intensity used by war/trade/propose; harmless default elsewhere
        if "intensity" not in args:
            args["intensity"] = 1

        return args

    # -------------------------
    # Heuristic fallback policy (no LLM)
    # -------------------------
    async def decide(self, world: WorldState) -> Action:
        # MUST RESPOND
        pending = self._pending_requesters_for_me(world)
        if pending:
            requester = pending[0]
            rel = self._get_relation(world, requester)
            p_accept = 1.0 / (1.0 + exp(-(rel / 20.0)))
            accept = random.random() < p_accept
            action = Action(
                actor_id=self.country_id,
                type=ActionType.RESPOND_ALLIANCE,
                target_id=requester,
                accept=accept,
                reason=("Accept alliance proposal" if accept else "Reject alliance proposal"),
                intensity=1,
            )
            self._last_action = (action.type, action.target_id, world.turn)

            # NOTIFY (v1 behavior, adapted)
            self._notify_bridge(
                {
                    "type": "AGENT_ACTION",
                    "agent": self.country_id,
                    "action_type": action.type.value,
                    "target": action.target_id,
                    "intensity": action.intensity,
                    "reason": action.reason,
                    "accept": action.accept,
                    "message": f"{self.country_id} performs {action.type.value} on {action.target_id} (Accept: {action.accept})",
                }
            )
            return action

        # stochastic pass
        if random.random() < 0.08:
            action = Action(actor_id=self.country_id, type=ActionType.PASS, reason="Strategic pause", intensity=1)
            self._last_action = (action.type, action.target_id, world.turn)

            # NOTIFY
            self._notify_bridge(
                {
                    "type": "AGENT_ACTION",
                    "agent": self.country_id,
                    "action_type": action.type.value,
                    "target": None,
                    "intensity": action.intensity,
                    "reason": action.reason,
                    "accept": None,
                    "message": f"{self.country_id} performs PASS",
                }
            )
            return action

        target_id = self._choose_target_stochastic(world)
        if target_id is None:
            action = Action(actor_id=self.country_id, type=ActionType.PASS, reason="No targets", intensity=1)
            self._last_action = (action.type, action.target_id, world.turn)

            # NOTIFY
            self._notify_bridge(
                {
                    "type": "AGENT_ACTION",
                    "agent": self.country_id,
                    "action_type": action.type.value,
                    "target": None,
                    "intensity": action.intensity,
                    "reason": action.reason,
                    "accept": None,
                    "message": f"{self.country_id} performs PASS (no targets)",
                }
            )
            return action

        rel = self._get_relation(world, target_id)
        rel_state = self._get_relation_state(world, target_id)
        has_pending = bool(getattr(rel_state, "pending_alliance_from", None)) if rel_state else False

        # weighted choice among actions
        candidates: list[tuple[ActionType, float]] = [
            (ActionType.TRADE, 0.6 + (0.4 if rel >= -20 else 0.0)),
            (ActionType.SANCTION, 0.2 + max(0, -rel) / 120.0),
            (ActionType.DECLARE_WAR, 0.05 + (0.35 if rel <= -50 else 0.0)),
            (ActionType.PROPOSE_ALLIANCE, 0.2 + (0.3 if rel >= -10 else 0.0)),
        ]

        if has_pending:
            # cannot propose if already pending in that pair
            candidates = [(a, w) for a, w in candidates if a != ActionType.PROPOSE_ALLIANCE]

        # cooldown: reduce probability of repeating exact same (type,target)
        if self._last_action is not None:
            last_type, last_target, last_turn = self._last_action
            if last_turn == world.turn - 1 and last_target == target_id:
                candidates = [(a, w * (0.2 if a == last_type else 1.0)) for a, w in candidates]

        total = sum(w for _, w in candidates)
        r = random.random() * total
        acc = 0.0
        chosen = candidates[-1][0]
        for a, w in candidates:
            acc += w
            if r <= acc:
                chosen = a
                break

        if chosen == ActionType.DECLARE_WAR:
            intensity = 2 if random.random() < 0.6 else 3
        elif chosen in {ActionType.SANCTION, ActionType.TRADE, ActionType.PROPOSE_ALLIANCE}:
            intensity = 1 if random.random() < 0.65 else 2
        else:
            intensity = 1

        action = Action(
            actor_id=self.country_id,
            type=chosen,
            target_id=target_id,
            reason=f"Fallback stochastic policy: {chosen.value}",
            intensity=intensity,
        )

        self._last_action = (action.type, action.target_id, world.turn)

        # NOTIFY
        self._notify_bridge(
            {
                "type": "AGENT_ACTION",
                "agent": self.country_id,
                "action_type": action.type.value,
                "target": action.target_id,
                "intensity": action.intensity,
                "reason": action.reason,
                "accept": getattr(action, "accept", None),
                "message": f"{self.country_id} performs {action.type.value} on {action.target_id} (Intensity: {action.intensity})",
            }
        )

        return action

    # -------------------------
    # LLM tool-based decision
    # -------------------------
    async def decide_llm(self, world: WorldState, provider: "MistralProvider") -> Action:
        # MUST RESPOND detection
        pending_requesters = self._pending_requesters_for_me(world)
        forced_mode = bool(pending_requesters)
        forced_requester = pending_requesters[0] if forced_mode else None

        # payload includes pending_alliance_from so model can see it
        world_payload = {
            "turn": world.turn,
            "self": self.country_id,
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

        # Dynamic tool restriction
        nonce = random.randint(1, 1_000_000)

        if forced_mode:
            allowed_tools = {"RESPOND_ALLIANCE"}
            tool_specs = {k: v for k, v in TOOL_SPECS.items() if k in allowed_tools}
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
                "Output JSON with this schema:\n"
                '{ "tool": "RESPOND_ALLIANCE", "arguments": { ... } }\n'
            )
            temperature = 0.6
        else:
            allowed = set(TOOL_SPECS.keys())

            # cooldown: avoid exact repeat tool from previous turn (regardless of target)
            last = getattr(self, "_last_action", None)
            if last is not None:
                last_type, last_target, last_turn = last
                if last_turn == world.turn - 1:
                    allowed.discard(last_type.value)

            # anti-war-loop: if already extremely hostile somewhere, often remove DECLARE_WAR
            very_bad_exists = any(
                r.relation <= -90 for r in world.relations if self.country_id in (r.country_1, r.country_2)
            )
            if very_bad_exists and random.random() < 0.7:
                allowed.discard("DECLARE_WAR")

            tool_specs = {k: v for k, v in TOOL_SPECS.items() if k in allowed}
            tools_block = self._tools_block_for(tool_specs)

            system_prompt = (
                f"You are {self.country_name} ({self.country_id}).\n"
                "Choose exactly ONE tool that best serves your interests this turn.\n"
                "Rules:\n"
                "- Do NOT repeat the same tool in consecutive turns.\n"
                "- Do NOT choose DECLARE_WAR against a country if relation <= -80.\n"
                "- If a relation already has pending_alliance_from set, do NOT choose PROPOSE_ALLIANCE for that same pair.\n\n"
                f"(Decision nonce: {nonce})\n\n"
                f"{self.prompt_text}\n\n"
                f"{tools_block}\n"
                "Output JSON with this schema:\n"
                '{ "tool": "DECLARE_WAR|PROPOSE_ALLIANCE|RESPOND_ALLIANCE|TRADE|SANCTION|PASS", "arguments": { ... } }\n'
            )
            temperature = 0.75

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "WORLD:\n" + json.dumps(world_payload, indent=2)},
        ]

        tool_call = await provider.complete_json(messages=messages, schema=ToolCall, temperature=temperature)

        # If model picked a disallowed tool, fallback instead of PASS
        if tool_call.tool not in tool_specs:
            action = await self.decide(world)  # stochastic heuristic fallback

            # NOTIFY
            self._notify_bridge(
                {
                    "type": "AGENT_LOG",
                    "agent": self.country_id,
                    "message": f"Model selected disallowed tool '{tool_call.tool}', used heuristic fallback '{action.type.value}'.",
                }
            )
            return action

        args_model = tool_specs[tool_call.tool]["args_model"]
        validate_fn = tool_specs[tool_call.tool]["validate"]

        normalized_args = self._normalize_tool_arguments(tool_call.arguments, tool_call.tool)

        # forced respond: ensure target_id is requester to prevent deadlock
        if forced_mode and tool_call.tool == "RESPOND_ALLIANCE":
            normalized_args.setdefault("target_id", forced_requester)

        try:
            args = args_model.model_validate(normalized_args)
            validate_fn(args, world, self.country_id)
        except (ValidationError, ValueError) as exc:
            # forced fallback: always respond
            if forced_mode:
                rel_score = self._get_relation(world, forced_requester)
                p_accept = 1.0 / (1.0 + exp(-(rel_score / 20.0)))
                accept = random.random() < p_accept
                action = Action(
                    actor_id=self.country_id,
                    type=ActionType.RESPOND_ALLIANCE,
                    target_id=forced_requester,
                    accept=accept,
                    reason=("Accept (fallback)" if accept else "Reject (fallback)"),
                    intensity=1,
                )
                self._last_action = (action.type, action.target_id, world.turn)

                # NOTIFY
                self._notify_bridge(
                    {
                        "type": "AGENT_ACTION",
                        "agent": self.country_id,
                        "action_type": action.type.value,
                        "target": action.target_id,
                        "intensity": action.intensity,
                        "reason": action.reason,
                        "accept": action.accept,
                        "message": f"{self.country_id} performs RESPOND_ALLIANCE on {action.target_id} (fallback; Accept: {action.accept})",
                    }
                )
                return action

            # normal fallback
            action = await self.decide(world)
            self._notify_bridge(
                {
                    "type": "AGENT_LOG",
                    "agent": self.country_id,
                    "message": f"Invalid tool arguments from model: {exc}. Using heuristic fallback '{action.type.value}'.",
                }
            )
            return action

        action = Action(
            actor_id=self.country_id,
            type=ActionType(tool_call.tool),
            target_id=getattr(args, "target_id", None),
            reason=getattr(args, "reason", "No reason"),
            intensity=getattr(args, "intensity", 1),
            accept=getattr(args, "accept", None),
        )

        self._last_action = (action.type, action.target_id, world.turn)

        # NOTIFY success (v1 behavior brought in)
        self._notify_bridge(
            {
                "type": "AGENT_ACTION",
                "agent": self.country_id,
                "action_type": action.type.value,
                "target": action.target_id,
                "intensity": action.intensity,
                "reason": action.reason,
                "accept": action.accept,
                "message": f"{self.country_id} performs {action.type.value} on {action.target_id or 'themselves'} "
                f"(Intensity: {action.intensity}, Accept: {action.accept})",
            }
        )

        return action