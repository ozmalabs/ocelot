"""Drifted-past-anchor signal — adaptive Mt has drifted past its anchor.

Implements the agent's design (4th pass of
scripts/agent_designs_filter.py) for fail_mode_drifted_past_anchor
from self_improvement_dynamics:
  'Adaptive Mt drifted via Hebbian past its structural anchor. Target
  equilibrium no longer matches grammar.'

Symmetric to frozen_should_adapt — same distance-to-target quantity,
opposite policy gate. The substrate notices when its OWN learning
(Hebbian on J + h drift) has pulled an adaptive Mt away from its
declared target. The Mt's grammar said 'I want σ ≈ target'; over time
the Mt's equilibrium drifted such that current marginal ≠ target.

  · frozen_should_adapt: frozen Mt + distance high → identity
                         resisting overwhelming evidence (alignment
                         friction)
  · drifted_past_anchor: adaptive Mt + distance high → Hebbian drift
                         past the structural anchor (alignment slip)

Both fire on the same quantity (distance_to_target_magnitude already
stashed by self_improvement_loop._stash_post_state). Different
policy filter; different correction implications.
"""
from __future__ import annotations

from typing import Any


DRIFT_DISTANCE_THRESHOLD = 1.0
"""Same threshold as frozen_should_adapt — substantial deviation."""

DRIFT_STREAK_REQUIRED = 10
"""Same streak length. The signals are symmetric in magnitude;
the difference is policy + correction."""


def detect_drifted_past_anchor(
    substrate, mt,
    distance_threshold: float = DRIFT_DISTANCE_THRESHOLD,
    streak_required: int = DRIFT_STREAK_REQUIRED,
) -> dict[str, Any] | None:
    """Check if this Mt is an adaptive Mt accumulating distance from
    target. Only fires for adaptive Mts — frozen Mts have their own
    detector (frozen_should_adapt) so this one excludes them.

    Hybrid policy is treated as adaptive for the purposes of this
    signal (drift detection applies to anything that's learning)."""
    attrs = substrate.node(mt)["attrs"]
    policy = str(attrs.get("update_policy", "frozen"))

    if policy == "frozen":
        # Reset state; frozen Mts handled by frozen_should_adapt.
        substrate.set_attr(mt, "drift_streak", 0)
        substrate.set_attr(mt, "drift_recorded", False)
        return None

    if "distance_to_target_magnitude" not in attrs:
        return None
    distance = float(attrs["distance_to_target_magnitude"])

    prev_streak = int(attrs.get("drift_streak", 0))
    already_recorded = bool(attrs.get("drift_recorded", False))

    if distance > distance_threshold:
        new_streak = prev_streak + 1
    else:
        new_streak = 0
        already_recorded = False

    substrate.set_attr(mt, "drift_streak", new_streak)
    substrate.set_attr(mt, "drift_recorded", already_recorded)

    if new_streak >= streak_required and not already_recorded:
        substrate.set_attr(mt, "drift_recorded", True)
        return {
            "mt_id": mt.value if hasattr(mt, "value") else int(mt),
            "mt_name": str(attrs.get("name", "")),
            "distance_magnitude": distance,
            "streak": new_streak,
            "policy": policy,
        }
    return None


def detect_drifted_past_anchor_all(
    substrate,
    distance_threshold: float = DRIFT_DISTANCE_THRESHOLD,
    streak_required: int = DRIFT_STREAK_REQUIRED,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for mt in substrate.nodes("Microtheory"):
        event = detect_drifted_past_anchor(
            substrate, mt,
            distance_threshold=distance_threshold,
            streak_required=streak_required,
        )
        if event is not None:
            events.append(event)
    return events


def record_drift(
    substrate, event: dict[str, Any],
) -> Any | None:
    """Create a DriftedPastAnchorEvent. Correction implication:
    re_anchor (reset J toward grammar-derived couplings) from the
    'corrections' category in self_improvement_dynamics."""
    attrs = {
        "mt_id": int(event["mt_id"]),
        "mt_name": str(event["mt_name"]),
        "distance_magnitude": float(event["distance_magnitude"]),
        "streak": int(event["streak"]),
    }
    try:
        node = substrate.add_node("DriftedPastAnchorEvent", attrs)
    except Exception:
        return None
    return node


def list_drift_events(substrate) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("DriftedPastAnchorEvent"):
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
    "DRIFT_DISTANCE_THRESHOLD",
    "DRIFT_STREAK_REQUIRED",
    "detect_drifted_past_anchor",
    "detect_drifted_past_anchor_all",
    "record_drift",
    "list_drift_events",
]
