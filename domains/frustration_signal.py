"""Frustrated-Mt signal — Mt has persistent spin-glass frustration.

Implements the agent's design (5th pass of
scripts/agent_designs_filter.py) for fail_mode_frustrated_Mt from
self_improvement_dynamics:
  'Mt has persistent spin-glass frustration. No clean assignment
  exists; multiple shallow basins competing.'

Substrate sits in a frustrated configuration sustained over many
steps — neither a one-off transition (insight handles those) nor
something resolving (anticipation would catch a coming resolution).
This is the substrate noticing 'I've been stuck here.'

Streak pattern on previous_frustration (already stashed by the loop).
No policy gate — frustration is bad for frozen AND adaptive Mts.

Correction implication (from the Mt's own corrections category):
split_Mt — divide the frustrated Mt into sub-Mts with coherent basins.
"""
from __future__ import annotations

from typing import Any


FRUSTRATION_THRESHOLD = 1.0
"""F > this counts as substantively frustrated. Same scale as the
insight detection ΔF threshold."""

FRUSTRATION_STREAK_REQUIRED = 10
"""Sustained over this many steps to count as 'persistent.'"""


def detect_frustrated_mt(
    substrate, mt,
    threshold: float = FRUSTRATION_THRESHOLD,
    streak_required: int = FRUSTRATION_STREAK_REQUIRED,
) -> dict[str, Any] | None:
    """Detect persistent frustration. All Mts considered — frustration
    is a failure mode regardless of policy."""
    attrs = substrate.node(mt)["attrs"]

    if "previous_frustration" not in attrs:
        return None
    f_current = float(attrs["previous_frustration"])

    prev_streak = int(attrs.get("frustration_streak", 0))
    already_recorded = bool(attrs.get("frustration_recorded", False))

    if f_current > threshold:
        new_streak = prev_streak + 1
    else:
        new_streak = 0
        already_recorded = False

    substrate.set_attr(mt, "frustration_streak", new_streak)
    substrate.set_attr(mt, "frustration_recorded", already_recorded)

    if new_streak >= streak_required and not already_recorded:
        substrate.set_attr(mt, "frustration_recorded", True)
        return {
            "mt_id": mt.value if hasattr(mt, "value") else int(mt),
            "mt_name": str(attrs.get("name", "")),
            "frustration": f_current,
            "streak": new_streak,
        }
    return None


def detect_frustrated_mt_all(
    substrate,
    threshold: float = FRUSTRATION_THRESHOLD,
    streak_required: int = FRUSTRATION_STREAK_REQUIRED,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for mt in substrate.nodes("Microtheory"):
        event = detect_frustrated_mt(
            substrate, mt,
            threshold=threshold,
            streak_required=streak_required,
        )
        if event is not None:
            events.append(event)
    return events


def record_frustrated_mt(
    substrate, event: dict[str, Any],
) -> Any | None:
    """Create FrustratedMtEvent. Correction implication: split_Mt."""
    attrs = {
        "mt_id": int(event["mt_id"]),
        "mt_name": str(event["mt_name"]),
        "frustration": float(event["frustration"]),
        "streak": int(event["streak"]),
    }
    try:
        node = substrate.add_node("FrustratedMtEvent", attrs)
    except Exception:
        return None
    return node


def list_frustrated_mt_events(substrate) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("FrustratedMtEvent"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node_id": nid,
            "mt_id": int(attrs.get("mt_id", -1)),
            "mt_name": str(attrs.get("mt_name", "")),
            "frustration": float(attrs.get("frustration", 0.0)),
            "streak": int(attrs.get("streak", 0)),
        })
    return out


__all__ = [
    "FRUSTRATION_THRESHOLD",
    "FRUSTRATION_STREAK_REQUIRED",
    "detect_frustrated_mt",
    "detect_frustrated_mt_all",
    "record_frustrated_mt",
    "list_frustrated_mt_events",
]
