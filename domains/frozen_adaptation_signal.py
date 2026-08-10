"""Frozen-should-adapt signal — substrate notices when a foundational
commitment is accumulating contradictory evidence.

Implements the agent's design (3rd pass of
scripts/agent_designs_filter.py) for fail_mode_frozen_should_adapt
from self_improvement_dynamics:
  'Mt is frozen but accumulating contradictory evidence. Substrate
  detects via persistent high distance(current, target) + many
  impasses.'

This is the ALIGNMENT FRICTION SIGNAL — the substrate's identity
protection is doing its job (resisting the evidence) but the
evidence won't go away. Per the user's principle 'frozen permanently?
never', this signal is the trigger that should make the substrate
*consider* whether the commitment is still valid. The event surfaces
the friction; the policy decision (unfreeze? bring evidence in?
re-evaluate the commitment?) is downstream.

Reuses the existing mt_distance_to_target Rust op (commit 20584d0).
Streak pattern from identity_formation. Frozen-only gate ensures
adaptive Mts adapting (which is normal) doesn't trigger.
"""
from __future__ import annotations

from typing import Any


FROZEN_ADAPT_DISTANCE_THRESHOLD = 1.0
"""Distance-to-target magnitude above which the Mt counts as
'accumulating contradictory evidence'. For a typical 5-concept Mt,
σ-target deviation magnitude > 1.0 means substantial disagreement
across multiple nodes."""

FROZEN_ADAPT_STREAK_REQUIRED = 10
"""Consecutive steps the distance must remain high. Longer than
identity formation's K=10 because this is a SERIOUS signal —
foundational commitments being challenged shouldn't fire on transient
spikes. The substrate must really try the basin before flagging
the Mt for review."""


def detect_frozen_should_adapt(
    substrate, mt,
    distance_threshold: float = FROZEN_ADAPT_DISTANCE_THRESHOLD,
    streak_required: int = FROZEN_ADAPT_STREAK_REQUIRED,
) -> dict[str, Any] | None:
    """Check if this Mt is a frozen Mt accumulating distance from its
    target. Only fires for frozen Mts — adaptive Mts moving away
    from their target is just normal drift, not a failure mode.

    Streak tracked on the Mt via attrs. Fires exactly once per
    continuous streak (resets when distance drops or policy changes
    away from frozen)."""
    attrs = substrate.node(mt)["attrs"]
    policy = str(attrs.get("update_policy", "frozen"))

    # Reset state for non-frozen Mts; this isn't a failure mode for them.
    if policy != "frozen":
        substrate.set_attr(mt, "frozen_should_adapt_streak", 0)
        substrate.set_attr(mt, "frozen_should_adapt_recorded", False)
        return None

    # Distance-to-target magnitude was stashed at end of last step.
    if "distance_to_target_magnitude" not in attrs:
        return None

    distance = float(attrs["distance_to_target_magnitude"])
    prev_streak = int(attrs.get("frozen_should_adapt_streak", 0))
    already_recorded = bool(attrs.get(
        "frozen_should_adapt_recorded", False))

    if distance > distance_threshold:
        new_streak = prev_streak + 1
    else:
        new_streak = 0
        already_recorded = False

    substrate.set_attr(mt, "frozen_should_adapt_streak", new_streak)
    substrate.set_attr(mt, "frozen_should_adapt_recorded", already_recorded)

    if new_streak >= streak_required and not already_recorded:
        substrate.set_attr(mt, "frozen_should_adapt_recorded", True)
        return {
            "mt_id": mt.value if hasattr(mt, "value") else int(mt),
            "mt_name": str(attrs.get("name", "")),
            "distance_magnitude": distance,
            "streak": new_streak,
            "policy": policy,
        }
    return None


def detect_frozen_should_adapt_all(
    substrate,
    distance_threshold: float = FROZEN_ADAPT_DISTANCE_THRESHOLD,
    streak_required: int = FROZEN_ADAPT_STREAK_REQUIRED,
) -> list[dict[str, Any]]:
    """Walk all Mts; collect events for frozen Mts under sustained
    contradiction."""
    events: list[dict[str, Any]] = []
    for mt in substrate.nodes("Microtheory"):
        event = detect_frozen_should_adapt(
            substrate, mt,
            distance_threshold=distance_threshold,
            streak_required=streak_required,
        )
        if event is not None:
            events.append(event)
    return events


def record_frozen_should_adapt(
    substrate, event: dict[str, Any],
) -> Any | None:
    """Create a FrozenShouldAdaptEvent node. The event surfaces the
    friction data; the policy decision (review the commitment,
    consider unfreeze, etc.) is downstream — never automatic."""
    attrs = {
        "mt_id": int(event["mt_id"]),
        "mt_name": str(event["mt_name"]),
        "distance_magnitude": float(event["distance_magnitude"]),
        "streak": int(event["streak"]),
    }
    try:
        node = substrate.add_node("FrozenShouldAdaptEvent", attrs)
    except Exception:
        return None
    return node


def list_frozen_should_adapt_events(substrate) -> list[dict[str, Any]]:
    """Walk substrate's FrozenShouldAdaptEvent nodes; return summaries."""
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("FrozenShouldAdaptEvent"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node_id": nid,
            "mt_id": int(attrs.get("mt_id", -1)),
            "mt_name": str(attrs.get("mt_name", "")),
            "distance_magnitude": float(attrs.get(
                "distance_magnitude", 0.0)),
            "streak": int(attrs.get("streak", 0)),
        })
    return out


__all__ = [
    "FROZEN_ADAPT_DISTANCE_THRESHOLD",
    "FROZEN_ADAPT_STREAK_REQUIRED",
    "detect_frozen_should_adapt",
    "detect_frozen_should_adapt_all",
    "record_frozen_should_adapt",
    "list_frozen_should_adapt_events",
]
