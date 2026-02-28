from __future__ import annotations

import json
import secrets
import requests
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

    - decide: heuristic fallback (stochastic)
    - decide_llm: tool-based LLM decision + exploration:
        * MUST RESPOND to pending alliances
        * epsilon-greedy: sometimes bypass LLM to avoid deterministic loops
        * sometimes "conflict explore" to force SANCTION/WAR consideration
        * nonce embedded in WORLD payload to reduce repeated outputs

    Also:
    - Notifies FastAPI bridge (/events/broadcast) with AGENT_LOG / AGENT_ACTION events.
    """

    def __init__(self, country_id: str, country_name: str, prompt_path: Optional[str] = None):
        super().__init__(country_id=country_id, country_name=country_name)
        self.prompt_text = self._load_prompt(prompt_path) if prompt_path else ""

        # IMPORTANT: use independent RNG that ignores random.seed(...) in debug scripts
        self._rng = secrets.SystemRandom()

        # last action cooldown
        self._last_action: Optional[tuple[ActionType, Optional[str], int]] = None

        # exploration knobs (tune)
        self.epsilon_bypass_llm = 0.12      # 12% of the time: use heuristic even if LLM available
        self.conflict_explore_prob = 0.18   # 18% of normal turns: bias towards SANCTION/WAR
        self.min_econ_for_alliance = 30    # Do not accept poor alliates
        self.min_social_for_war = 40          # A country with bad social status does not want wars

    def _load_prompt(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    # -------------------------
    # Bridge notifications
    # -------------------------
    def _notify_bridge(self, payload: dict):
        try:
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
            # prefer extremes a bit + noise
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
        if "target_id" not in args and "target" in args:
            args["target_id"] = args["target"]
        if "reason" not in args or not args.get("reason"):
            args["reason"] = f"{tool_name} selected by model"
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

            # National interest
            req_econ = self._get_stat(world, requester, "economy")
            my_social = self._get_stat(world, self.country_id, "social")

            # If the country is poor (< 30) or if the citizens are not satisfied (social < 20), reject
            if req_econ < 30 or my_social < 20:
                accept = False
                reason = "Target economy unstable or domestic social crisis."
            else:
                p_accept = 1.0 / (1.0 + exp(-(rel / 18.0)))
                accept = self._rng.random() < p_accept
                reason = "Strategic alliance decision based on relations."

            action = Action(
                actor_id=self.country_id,
                type=ActionType.RESPOND_ALLIANCE,
                target_id=requester,
                accept=accept,
                reason=reason,
                intensity=1,
            )
            self._last_action = (action.type, action.target_id, world.turn)
            self._notify_bridge(self._action_payload(action))
            return action

        # small stochastic pass
        if self._rng.random() < 0.05:
            action = Action(actor_id=self.country_id, type=ActionType.PASS, reason="Strategic pause", intensity=1)
            self._last_action = (action.type, action.target_id, world.turn)
            self._notify_bridge(self._action_payload(action))
            return action

        target_id = self._choose_target_stochastic(world)
        if target_id is None:
            action = Action(actor_id=self.country_id, type=ActionType.PASS, reason="No targets", intensity=1)
            self._last_action = (action.type, action.target_id, world.turn)
            self._notify_bridge(self._action_payload(action))
            return action

        rel = self._get_relation(world, target_id)
        rel_state = self._get_relation_state(world, target_id)
        has_pending = bool(getattr(rel_state, "pending_alliance_from", None)) if rel_state else False

        my_mil = self._military(world, self.country_id)
        t_mil = self._military(world, target_id)
        mil_adv = my_mil - t_mil

        explore_conflict = self._rng.random() < self.conflict_explore_prob

        # weights (cooperation still likely, but conflict is reachable from neutral)
        w_trade = 0.50 + (0.20 if rel >= -10 else 0.0)
        w_alliance = 0.10 + (0.25 if rel >= 5 else 0.0)

        # sanctions: start around mild negativity
        w_sanction = 0.12 + max(0.0, (-rel) / 35.0)     # grows from 0 -> 1 as rel ~ -35
        # war: grows when hostility exists, earlier if strong military advantage
        w_war = 0.05 + max(0.0, (-rel - 15) / 35.0)     # grows from rel <= -15

        my_econ = self._get_stat(world, self.country_id, "economy")
        t_econ = self._get_stat(world, target_id, "economy")
        mil_diff = self._military(world, self.country_id) - self._military(world, target_id)

        if mil_adv >= 10:
            w_war += 0.12
            w_sanction += 0.05

        if explore_conflict:
            w_sanction += 0.18
            w_war += 0.10
            w_trade *= 0.70
            w_alliance *= 0.70

        if my_econ < 30:
            w_trade += 0.5
            w_war = 0.01     # Not enough money for war

        # If the objective is military strong, low war probability because of fear
        if mil_diff < -20:
            w_war *= 0.1
            w_sanction += 0.2

        candidates: list[tuple[ActionType, float]] = [
            (ActionType.TRADE, w_trade),
            (ActionType.PROPOSE_ALLIANCE, w_alliance),
            (ActionType.SANCTION, w_sanction),
            (ActionType.DECLARE_WAR, w_war),
        ]

        if has_pending:
            candidates = [(a, w) for a, w in candidates if a != ActionType.PROPOSE_ALLIANCE]

        # cooldown: penalize repeating same (type,target) immediately
        if self._last_action is not None:
            last_type, last_target, last_turn = self._last_action
            if last_turn == world.turn - 1 and last_target == target_id:
                candidates = [(a, w * (0.12 if a == last_type else 1.0)) for a, w in candidates]

        total = sum(w for _, w in candidates)
        r = self._rng.random() * total
        acc = 0.0
        chosen = candidates[-1][0]
        for a, w in candidates:
            acc += w
            if r <= acc:
                chosen = a
                break

        if chosen == ActionType.DECLARE_WAR:
            intensity = 3 if (mil_adv >= 10 and self._rng.random() < 0.7) else 2
        elif chosen == ActionType.SANCTION:
            intensity = 2 if self._rng.random() < 0.65 else 1
        elif chosen in {ActionType.TRADE, ActionType.PROPOSE_ALLIANCE}:
            intensity = 1 if self._rng.random() < 0.75 else 2
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
        self._notify_bridge(self._action_payload(action))
        return action

    def _action_payload(self, action: Action) -> dict:
        return {
            "type": "AGENT_ACTION",
            "agent": self.country_id,
            "action_type": action.type.value,
            "target": getattr(action, "target_id", None),
            "intensity": getattr(action, "intensity", 1),
            "reason": getattr(action, "reason", ""),
            "accept": getattr(action, "accept", None),
            "message": f"{self.country_id} performs {action.type.value} on {getattr(action, 'target_id', None) or 'N/A'}",
        }

    # -------------------------
    # LLM tool-based decision
    # -------------------------
    async def decide_llm(self, world: WorldState, provider: "MistralProvider") -> Action:
        pending_requesters = self._pending_requesters_for_me(world)
        forced_mode = bool(pending_requesters)
        forced_requester = pending_requesters[0] if forced_mode else None

        # epsilon-greedy bypass (but never bypass forced respond)
        if not forced_mode and self._rng.random() < self.epsilon_bypass_llm:
            action = await self.decide(world)
            self._notify_bridge(
                {"type": "AGENT_LOG", "agent": self.country_id, "message": "Bypassed LLM (epsilon-greedy)."}
            )
            return action

        nonce = self._rng.randint(1, 1_000_000)
        payload_nonce = self._rng.randint(1, 1_000_000)

        world_payload = {
            "turn": world.turn,
            "self": self.country_id,
            "nonce": payload_nonce,  # IMPORTANT: variation inside WORLD payload
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

        # occasionally "conflict explore" by restricting tools (only in normal mode)
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

            # cooldown: avoid same tool consecutive turn
            if self._last_action is not None:
                last_type, _, last_turn = self._last_action
                if last_turn == world.turn - 1:
                    allowed.discard(last_type.value)

            # conflict exploration: sometimes focus the model on sanction/war
            if explore_conflict:
                allowed = allowed.intersection({"SANCTION", "DECLARE_WAR", "TRADE", "PASS"})

            tool_specs = {k: v for k, v in TOOL_SPECS.items() if k in allowed}
            tools_block = self._tools_block_for(tool_specs)

            system_prompt = (
                f"You are {self.country_name} ({self.country_id}).\n"
                "Choose exactly ONE tool that best serves your interests this turn.\n"
                "CRITICAL: Your 'reason' must be a unique, context-aware sentence. "
                "Do not use generic phrases. Reference your current economy, military power or specific hostility levels in your explanation.\n"
                "Rules:\n"
                "- Do NOT repeat the same tool in consecutive turns.\n"
                "- Only choose DECLARE_WAR if relation <= -30.\n"
                "- Consider SANCTION if relation <= -10 and war is not justified.\n"
                "- If a relation already has pending_alliance_from set, do NOT choose PROPOSE_ALLIANCE for that same pair.\n"
                "- Do NOT ally with 'poor' countries (economy < 30).\n"
                "- If your economy is low, prioritize TRADE to recover funds.\n"
                "- Avoid DECLARE_WAR if the target has much higher military_power than you.\n"
                f"- Exploration mode: {explore_conflict} (if true, prefer SANCTION/DECLARE_WAR sometimes).\n\n"
                f"(Decision nonce: {nonce})\n\n"
                f"{self.prompt_text}\n\n"
                f"{tools_block}\n"
                'Output JSON: { "tool": "DECLARE_WAR|PROPOSE_ALLIANCE|RESPOND_ALLIANCE|TRADE|SANCTION|PASS", "arguments": { ... } }\n'
            )
            temperature = 0.95
            top_p = 0.95

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "WORLD:\n" + json.dumps(world_payload, indent=2)},
        ]

        tool_call = await provider.complete_json(
            messages=messages,
            schema=ToolCall,
            temperature=temperature,
            top_p=top_p,
        )

        # disallowed -> heuristic fallback
        if tool_call.tool not in tool_specs:
            action = await self.decide(world)
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

        if forced_mode and tool_call.tool == "RESPOND_ALLIANCE":
            normalized_args.setdefault("target_id", forced_requester)

        try:
            args = args_model.model_validate(normalized_args)
            validate_fn(args, world, self.country_id)
        except (ValidationError, ValueError) as exc:
            if forced_mode:
                rel_score = self._get_relation(world, forced_requester)
                p_accept = 1.0 / (1.0 + exp(-(rel_score / 18.0)))
                accept = self._rng.random() < p_accept
                action = Action(
                    actor_id=self.country_id,
                    type=ActionType.RESPOND_ALLIANCE,
                    target_id=forced_requester,
                    accept=accept,
                    reason=("Accept (fallback)" if accept else "Reject (fallback)"),
                    intensity=1,
                )
                self._last_action = (action.type, action.target_id, world.turn)
                self._notify_bridge(self._action_payload(action))
                return action

            action = await self.decide(world)
            self._notify_bridge(
                {"type": "AGENT_LOG", "agent": self.country_id, "message": f"Invalid model args: {exc}. Fallback."}
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
        self._notify_bridge(self._action_payload(action))
        return action