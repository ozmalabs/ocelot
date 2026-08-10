"""Sparse-Mt signal — Mt is structurally inactive.

Implements the agent's design (6th pass of
scripts/agent_designs_filter.py) for fail_mode_sparse_Mt from
self_improvement_dynamics:
  'Mt constrains few nodes; J nearly all zero; not engaged for many
  cycles.'

This is the INVERSE-DIRECTION streak detector. Previous detectors
fire when a quantity stays ABOVE threshold; this one fires when
coverage stays BELOW threshold. The substrate notices an Mt that's
declared but not active — candidate for pruning per the corrections
category.

Coverage is computed by mt_audit_basin (count of concepts with
|σ| > 0.05) and stashed per step by self_improvement_loop. This
detector just adds the streak.

Closes the failure-mode coverage: with sparse_Mt installed, every
named failure mode in self_improvement_dynamics has a filter that
detects it.
"""
from __future__ import annotations

from typing import Any


SPARSE_COVERAGE_THRESHOLD = 1
"""coverage < this counts as sparse. ≤1 engaged concept = the Mt isn't
really doing anything."""

SPARSE_STREAK_REQUIRED = 10
"""Sustained over this many steps to count as 'not engaged for many
cycles.'"""


def detect_sparse_mt(
    substrate, mt,
    coverage_threshold: int = SPARSE_COVERAGE_THRESHOLD,
    streak_required: int = SPARSE_STREAK_REQUIRED,
) -> dict[str, Any] | None:
    """Detect sustained low coverage. All Mts considered — sparseness
    is a failure regardless of policy."""
    attrs = substrate.node(mt)["attrs"]
    if "coverage" not in attrs:
        return None
    coverage = int(attrs["coverage"])

    prev_streak = int(attrs.get("sparse_streak", 0))
    already_recorded = bool(attrs.get("sparse_recorded", False))

    # INVERSE direction: streak grows when BELOW threshold.
    if coverage < coverage_threshold:
        new_streak = prev_streak + 1
    else:
        new_streak = 0
        already_recorded = False

    substrate.set_attr(mt, "sparse_streak", new_streak)
    substrate.set_attr(mt, "sparse_recorded", already_recorded)

    if new_streak >= streak_required and not already_recorded:
        substrate.set_attr(mt, "sparse_recorded", True)
        return {
            "mt_id": mt.value if hasattr(mt, "value") else int(mt),
            "mt_name": str(attrs.get("name", "")),
            "coverage": coverage,
            "streak": new_streak,
        }
    return None


def detect_sparse_mt_all(
    substrate,
    coverage_threshold: int = SPARSE_COVERAGE_THRESHOLD,
    streak_required: int = SPARSE_STREAK_REQUIRED,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for mt in substrate.nodes("Microtheory"):
        event = detect_sparse_mt(
            substrate, mt,
            coverage_threshold=coverage_threshold,
            streak_required=streak_required,
        )
        if event is not None:
            events.append(event)
    return events


def record_sparse_mt(
    substrate, event: dict[str, Any],
) -> Any | None:
    """Create SparseMtEvent. Correction implication: prune_Mt (set
    β = 0 or remove)."""
    attrs = {
        "mt_id": int(event["mt_id"]),
        "mt_name": str(event["mt_name"]),
        "coverage": int(event["coverage"]),
        "streak": int(event["streak"]),
    }
    try:
        node = substrate.add_node("SparseMtEvent", attrs)
    except Exception:
        return None
    return node


def list_sparse_mt_events(substrate) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("SparseMtEvent"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node_id": nid,
            "mt_id": int(attrs.get("mt_id", -1)),
            "mt_name": str(attrs.get("mt_name", "")),
            "coverage": int(attrs.get("coverage", 0)),
            "streak": int(attrs.get("streak", 0)),
        })
    return out


__all__ = [
    "SPARSE_COVERAGE_THRESHOLD",
    "SPARSE_STREAK_REQUIRED",
    "detect_sparse_mt",
    "detect_sparse_mt_all",
    "record_sparse_mt",
    "list_sparse_mt_events",
]
