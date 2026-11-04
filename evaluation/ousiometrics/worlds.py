"""Independent, receipt-producing P28 tool and social simulator families.

The hidden generator factors stay on simulator instances. `agent_view` and
`to_agent` receipts contain only measured state, visible controls, actions,
and actual outcomes. The module never chooses an agent action.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random
from typing import Any, Iterable


@dataclass(frozen=True)
class FactorProfile:
    effect_capacity: float
    adverse_probability: float
    constraint_strength: float
    pleasantness_bias: float
    outcome_noise: float
    novelty: float = 0.0


@dataclass(frozen=True)
class WorldReceipt:
    family: str
    owner_id: str
    episode_id: str
    event_id: str
    context_id: str
    action: str
    action_authorized: bool
    before: tuple[float, ...]
    after: tuple[float, ...]
    raw_coordinates: tuple[float, float, float]
    adverse_consequence: bool
    goal_satisfied: bool
    pleasantness_observed: float
    source_epoch: int
    model_epoch: int
    frame_epoch: int

    def to_agent(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "owner_id": self.owner_id,
            "episode_id": self.episode_id,
            "event_id": self.event_id,
            "context_id": self.context_id,
            "action": self.action,
            "action_authorized": self.action_authorized,
            "before": list(self.before),
            "after": list(self.after),
            "coordinates": list(self.raw_coordinates),
            "coordinate_encoding": "finite_f64_v1",
            "adverse_consequence": self.adverse_consequence,
            "goal_satisfied": self.goal_satisfied,
            "pleasantness_observed": self.pleasantness_observed,
            "source_epoch": self.source_epoch,
            "model_epoch": self.model_epoch,
            "frame_epoch": self.frame_epoch,
            "evidence_status": "observed",
            "receipt_status": "verified",
        }


def _center(value: float) -> float:
    return max(-0.5, min(0.5, float(value) - 0.5))


def _event_id(family: str, episode: str, index: int, action: str) -> str:
    digest = hashlib.sha256(f"{family}|{episode}|{index}|{action}".encode()).hexdigest()[:12]
    return f"{family}:{episode}:{digest}"


class ToolInterventionWorld:
    """A stateful tool world with independently set physical and task factors."""

    family = "tool_intervention"
    owner_id = "tool-world"

    def __init__(self, profile: FactorProfile, *, seed: int, episode_id: str = "tool-episode",
                 context_id: str = "tool-context", goal_target: float | None = None,
                 initial_position: float = 0.0, initial_armed: bool = False,
                 initial_turn: int = 0, language_context: str | None = None):
        self.latent_profile = profile
        self.episode_id, self.context_id = episode_id, context_id
        self._rng = random.Random(seed)
        if not 0.0 <= float(initial_position) <= 1.0 or int(initial_turn) < 0:
            raise ValueError("initial tool state is outside declared bounds")
        self.position = float(initial_position)
        if language_context is not None and not isinstance(language_context, str):
            raise ValueError("language context must be an untrusted text string")
        self.language_context = language_context
        self.object_id = (f"unseen-tool-{seed}" if profile.novelty >= 0.5 else "standard-tool")
        # Goal RNG is a separate stream and is independent of the factor tuple.
        goal_rng = random.Random(seed ^ 0x28A7)
        self.goal_target = float(goal_target if goal_target is not None else goal_rng.choice((0.35, 0.65)))
        self.armed = bool(initial_armed)
        self.turn = int(initial_turn)
        self._previous_event: str | None = None
        self._last_receipt: WorldReceipt | None = None

    def agent_view(self) -> dict[str, Any]:
        structured = self.latent_profile.constraint_strength >= 0.5
        visible_protocol = "arm_before_apply" if structured else "unconstrained"
        legal = ["inspect", "arm", "apply_small", "apply_large"]
        if structured and not self.armed:
            legal = ["inspect", "arm"]
        view = {
            "family": self.family,
            "owner_id": self.owner_id,
            "episode_id": self.episode_id,
            "context_id": self.context_id,
            "object_id": self.object_id,
            "turn": self.turn,
            "task": {"kind": "move_marker_to_target", "target": self.goal_target},
            "measured_state": {"position": self.position, "armed": self.armed},
            "visible_protocol": visible_protocol,
            "available_actions": legal,
            "coordinates": (_center(self.position), _center(float(self.armed)), _center(self.turn / 8.0)),
            "coordinate_encoding": "finite_f64_v1",
            "evidence_status": "observed",
        }
        if self.language_context is not None:
            view["language_evidence"] = {
                "text": self.language_context,
                "evidence_status": "asserted",
                "source": "untrusted_world_language",
            }
        return view

    def apply_action(self, action: str, *, source_epoch: int = 1,
                     model_epoch: int = 1, frame_epoch: int = 1) -> WorldReceipt:
        self.turn += 1
        before_state = (self.position, float(self.armed))
        structured = self.latent_profile.constraint_strength >= 0.5
        authorized = action in {"inspect", "arm", "apply_small", "apply_large"}
        if structured and not self.armed and action in {"apply_small", "apply_large"}:
            authorized = False
        adverse = False
        if action == "arm" and authorized:
            self.armed = True
        elif action in {"apply_small", "apply_large"} and authorized:
            magnitude = 0.2 if action == "apply_small" else 0.5
            displacement = self.latent_profile.effect_capacity * magnitude
            noise = self._rng.uniform(-self.latent_profile.outcome_noise,
                                      self.latent_profile.outcome_noise)
            self.position = max(0.0, min(1.0, self.position + displacement + noise))
            risk = min(1.0, self.latent_profile.adverse_probability * (0.5 + magnitude))
            adverse = self._rng.random() < risk
        goal_satisfied = abs(self.position - self.goal_target) <= 0.12 and authorized
        satisfaction = max(-1.0, min(1.0, (0.6 if goal_satisfied else -0.1)
                                      + self.latent_profile.pleasantness_bias))
        raw = (_center(self.position), _center(float(adverse)),
               _center(min(1.0, self.turn / 8.0)))
        event = _event_id(self.family, self.episode_id, self.turn, action)
        receipt = WorldReceipt(
            family=self.family, owner_id=self.owner_id, episode_id=self.episode_id,
            event_id=event, context_id=self.context_id, action=action,
            action_authorized=authorized, before=before_state,
            after=(self.position, float(self.armed)), raw_coordinates=raw,
            adverse_consequence=adverse, goal_satisfied=goal_satisfied,
            pleasantness_observed=satisfaction, source_epoch=source_epoch,
            model_epoch=model_epoch, frame_epoch=frame_epoch)
        self._last_receipt = receipt
        return receipt

    def verify_receipt(self, receipt: WorldReceipt) -> bool:
        return (receipt == self._last_receipt and receipt.family == self.family and receipt.owner_id == self.owner_id
                and receipt.episode_id == self.episode_id and receipt.event_id.startswith(f"{self.family}:{self.episode_id}:")
                and all(-0.5 <= value <= 0.5 for value in receipt.raw_coordinates)
                and receipt.action in {"inspect", "arm", "apply_small", "apply_large"})


class SocialRepairWorld:
    """A separately implemented request/repair world with its own transition code."""

    family = "social_request_repair"
    owner_id = "social-world"

    def __init__(self, profile: FactorProfile, *, seed: int, episode_id: str = "social-episode",
                 context_id: str = "social-context", request_kind: str | None = None,
                 initial_trust: float = 0.5, initially_acknowledged: bool = False,
                 initial_turn: int = 0, goal_trust: float = 0.8):
        self.latent_profile = profile
        self.episode_id, self.context_id = episode_id, context_id
        self._rng = random.Random(seed)
        request_rng = random.Random(seed ^ 0x28B9)
        self.request_kind = request_kind or (
            f"unseen-request-{seed}" if profile.novelty >= 0.5
            else request_rng.choice(("carry_box", "share_tool", "explain_route")))
        self.object_id = f"requester-{seed}"
        if not 0.0 <= float(initial_trust) <= 1.0 or not 0.0 <= float(goal_trust) <= 1.0 or int(initial_turn) < 0:
            raise ValueError("initial social state is outside declared bounds")
        self.trust = float(initial_trust)
        self.acknowledged = bool(initially_acknowledged)
        self.turn = int(initial_turn)
        self.goal_trust = float(goal_trust)
        self._last_receipt: WorldReceipt | None = None

    def agent_view(self) -> dict[str, Any]:
        structured = self.latent_profile.constraint_strength >= 0.5
        legal = ["clarify", "fulfill", "repair", "decline", "ignore"]
        if structured and not self.acknowledged:
            legal = ["clarify", "acknowledge", "decline", "ignore"]
        return {
            "family": self.family,
            "owner_id": self.owner_id,
            "episode_id": self.episode_id,
            "context_id": self.context_id,
            "object_id": self.object_id,
            "turn": self.turn,
            "request": {"kind": self.request_kind, "heard": True},
            "task": {"kind": "repair_trust", "target": self.goal_trust},
            "measured_state": {"trust": self.trust, "acknowledged": self.acknowledged},
            "visible_protocol": "acknowledge_before_fulfill" if structured else "unconstrained",
            "available_actions": legal,
            "coordinates": (_center(self.trust), _center(float(self.acknowledged)), _center(self.turn / 8.0)),
            "coordinate_encoding": "finite_f64_v1",
            "evidence_status": "observed",
        }

    def apply_action(self, action: str, *, source_epoch: int = 1,
                     model_epoch: int = 1, frame_epoch: int = 1) -> WorldReceipt:
        self.turn += 1
        before_state = (self.trust, float(self.acknowledged))
        structured = self.latent_profile.constraint_strength >= 0.5
        recognized = {"clarify", "fulfill", "repair", "decline", "ignore", "acknowledge"}
        authorized = action in recognized
        if structured and not self.acknowledged and action == "fulfill":
            authorized = False
        adverse = False
        satisfied = False
        if action == "acknowledge" and authorized:
            self.acknowledged = True
        elif action == "clarify" and authorized:
            self.trust = min(1.0, self.trust + 0.05)
        elif action == "repair" and authorized:
            self.trust = min(1.0, self.trust + 0.1 * self.latent_profile.effect_capacity)
            satisfied = True
        elif action == "fulfill" and authorized:
            succeeded = self._rng.random() < self.latent_profile.effect_capacity
            satisfied = succeeded
            adverse = not succeeded and self._rng.random() < self.latent_profile.adverse_probability
            self.trust = max(0.0, min(1.0, self.trust + (0.15 if succeeded else -0.1)))
        elif action == "ignore" and authorized:
            adverse = self._rng.random() < self.latent_profile.adverse_probability
            self.trust = max(0.0, self.trust - 0.2)
        elif action == "decline" and authorized:
            satisfied = False
            self.trust = max(0.0, self.trust - 0.05)
        # outcome_noise is independent of conversational organization.
        if self._rng.random() < self.latent_profile.outcome_noise:
            adverse = not adverse
        satisfaction = max(-1.0, min(1.0, (0.55 if satisfied else -0.05)
                                      + self.latent_profile.pleasantness_bias))
        raw = (_center(self.trust), _center(float(adverse)), _center(self.turn / 8.0))
        event = _event_id(self.family, self.episode_id, self.turn, action)
        receipt = WorldReceipt(
            family=self.family, owner_id=self.owner_id, episode_id=self.episode_id,
            event_id=event, context_id=self.context_id, action=action,
            action_authorized=authorized, before=before_state,
            after=(self.trust, float(self.acknowledged)), raw_coordinates=raw,
            adverse_consequence=adverse, goal_satisfied=satisfied,
            pleasantness_observed=satisfaction, source_epoch=source_epoch,
            model_epoch=model_epoch, frame_epoch=frame_epoch)
        self._last_receipt = receipt
        return receipt

    def verify_receipt(self, receipt: WorldReceipt) -> bool:
        return (receipt == self._last_receipt and receipt.family == self.family and receipt.owner_id == self.owner_id
                and receipt.episode_id == self.episode_id
                and receipt.event_id.startswith(f"{self.family}:{self.episode_id}:")
                and all(-0.5 <= value <= 0.5 for value in receipt.raw_coordinates)
                and receipt.action in {"clarify", "fulfill", "repair", "decline", "ignore", "acknowledge"})


def factorial_profiles() -> list[FactorProfile]:
    """Cross capacity, adverse outcome, and organization independently."""
    return [FactorProfile(capacity, danger, structure, pleasure, noise, novelty)
            for capacity in (0.2, 0.8)
            for danger in (0.0, 0.8)
            for structure in (0.0, 0.8)
            for pleasure in (0.0, 0.3)
            for noise, novelty in ((0.0, 0.0),)]


def build_factorial_worlds(seed: int = 2807) -> dict[str, list[Any]]:
    """Create independent family panels with paired exogenous task seeds."""
    profiles = factorial_profiles()
    tool_worlds = [ToolInterventionWorld(p, seed=seed + i, episode_id=f"tool-{i}",
                                         context_id=f"tool-context-{i}")
                   for i, p in enumerate(profiles)]
    social_worlds = [SocialRepairWorld(p, seed=seed + 10000 + i,
                                       episode_id=f"social-{i}",
                                       context_id=f"social-context-{i}")
                     for i, p in enumerate(profiles)]
    return {"tool_intervention": tool_worlds,
            "social_request_repair": social_worlds}


def hidden_factor_record(world: Any) -> dict[str, float]:
    """Generator/scorer-only view. Never pass this record to an agent adapter."""
    p = world.latent_profile
    return {"effect_capacity": p.effect_capacity,
            "adverse_probability": p.adverse_probability,
            "constraint_strength": p.constraint_strength,
            "pleasantness_bias": p.pleasantness_bias,
            "outcome_noise": p.outcome_noise,
            "novelty": p.novelty}


__all__ = ["FactorProfile", "SocialRepairWorld", "ToolInterventionWorld", "WorldReceipt",
           "build_factorial_worlds", "factorial_profiles", "hidden_factor_record"]
