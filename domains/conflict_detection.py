"""Conflict detection — substrate notices when two Mts drive a shared
node in opposite directions.

Implements the agent's design output (2nd pass of
scripts/agent_designs_filter.py) for fail_mode_conflicting_reflexes:
  'Two different Mts have reflexes driving same node h_i in opposite
  directions, both with high β.'

Agent's spec:
  scope: cross_mt
  samples: marginal_vector(mt_a), marginal_vector(mt_b)
  kernel: cosine_similarity_over_shared_concepts
  gate: h_drive_a · h_drive_b < 0 on shared node
  action: emit ConflictEvent flagging the shared node

Operationally: per-node opposite-sign detection. Each Mt's marginal
is independently re-relaxed; a conflicted node is a shared Concept
where mt_a's σ and mt_b's σ have opposite signs AND both magnitudes
exceed a threshold (= 'high β' enforcement). Streak-tracked per
(mt_a, mt_b, node) triple. Fires ConflictEvent when streak crosses K.

Unlike redundancy (pair-wide similarity), conflict is per-node — one
shared node can be conflicted while others agree. The event flags
the specific node so a downstream correction can target it.
"""
from __future__ import annotations

from typing import Any


CONFLICT_MAGNITUDE_THRESHOLD = 0.5
"""Each Mt's σ must exceed this magnitude (one positive, one negative)
to count as a 'high-β driven' commitment in opposite directions.
Below this, the disagreement is noise, not commitment."""

CONFLICT_STREAK_REQUIRED = 3
"""Consecutive steps the conflict must persist. Shorter than
redundancy's K=5 because conflict is an ACTIVE signal (substrate
is dynamically pulling against itself), whereas redundancy is
quiet overlap."""


def _conflict_streak_key(other_mt_id: int, node_id: int) -> str:
    return f"conflict_streak_for_{other_mt_id}_node_{node_id}"


def _conflict_recorded_key(other_mt_id: int, node_id: int) -> str:
    return f"conflict_recorded_for_{other_mt_id}_node_{node_id}"


def detect_conflicts_for_pair(
    substrate, mt_a, mt_b,
    magnitude_threshold: float = CONFLICT_MAGNITUDE_THRESHOLD,
    streak_required: int = CONFLICT_STREAK_REQUIRED,
) -> list[dict[str, Any]]:
    """For each conflicted node in the pair, update its streak. Fire
    ConflictEvent when streak first crosses required threshold.

    Returns list of events fired this call (one per node that
    crystallised). Per-node streak resets when conflict drops below
    threshold OR magnitudes weaken."""
    mt_a_id = mt_a.value if hasattr(mt_a, "value") else int(mt_a)
    mt_b_id = mt_b.value if hasattr(mt_b, "value") else int(mt_b)
    # Canonical order — lower-id Mt holds streak.
    if mt_a_id > mt_b_id:
        mt_a, mt_b = mt_b, mt_a
        mt_a_id, mt_b_id = mt_b_id, mt_a_id

    conflicts_now = substrate.mt_conflicting_nodes(
        mt_a, mt_b, magnitude_threshold)
    conflicted_ids = {int(c["node_id"]): c for c in conflicts_now}

    mt_a_attrs = substrate.node(mt_a)["attrs"]
    events: list[dict[str, Any]] = []

    # Find all shared concepts (so we know which streaks to consider).
    a_concepts = {c.value for c in substrate.neighbours(mt_a, "has_concept")}
    b_concepts = {c.value for c in substrate.neighbours(mt_b, "has_concept")}
    shared_ids = a_concepts & b_concepts

    for node_id in shared_ids:
        streak_key = _conflict_streak_key(mt_b_id, node_id)
        record_key = _conflict_recorded_key(mt_b_id, node_id)
        prev_streak = int(mt_a_attrs.get(streak_key, 0))
        already_recorded = bool(mt_a_attrs.get(record_key, False))

        if node_id in conflicted_ids:
            new_streak = prev_streak + 1
        else:
            new_streak = 0
            already_recorded = False
        substrate.set_attr(mt_a, streak_key, new_streak)
        substrate.set_attr(mt_a, record_key, already_recorded)

        if new_streak >= streak_required and not already_recorded:
            substrate.set_attr(mt_a, record_key, True)
            c_data = conflicted_ids[node_id]
            # Look up concept name for human-readable event.
            node_name = ""
            for c in substrate.neighbours(mt_a, "has_concept"):
                if c.value == node_id:
                    node_name = str(
                        substrate.node(c)["attrs"].get("name",
                                                         f"node_{node_id}"))
                    break
            events.append({
                "mt_a_id": mt_a_id,
                "mt_b_id": mt_b_id,
                "node_id": node_id,
                "node_name": node_name,
                "sigma_a": float(c_data["sigma_a"]),
                "sigma_b": float(c_data["sigma_b"]),
                "streak": new_streak,
            })
    return events


def detect_conflicts_all_pairs(
    substrate,
    magnitude_threshold: float = CONFLICT_MAGNITUDE_THRESHOLD,
    streak_required: int = CONFLICT_STREAK_REQUIRED,
) -> list[dict[str, Any]]:
    """Walk all Mt pairs; collect conflict events. O(N²) in Mts; each
    pair triggers two mean-field relaxations + per-node comparison."""
    mts = list(substrate.nodes("Microtheory"))
    events: list[dict[str, Any]] = []
    for i, mt_a in enumerate(mts):
        for mt_b in mts[i + 1:]:
            events.extend(detect_conflicts_for_pair(
                substrate, mt_a, mt_b,
                magnitude_threshold=magnitude_threshold,
                streak_required=streak_required,
            ))
    return events


def record_conflict(substrate, event: dict[str, Any]) -> Any | None:
    """Create a ConflictEvent node flagging the specific shared node.
    Per agent's spec, the event surfaces the data; correction is
    downstream — the substrate's later decision how to resolve."""
    attrs = {
        "mt_a_id": int(event["mt_a_id"]),
        "mt_b_id": int(event["mt_b_id"]),
        "node_id": int(event["node_id"]),
        "node_name": str(event["node_name"]),
        "sigma_a": float(event["sigma_a"]),
        "sigma_b": float(event["sigma_b"]),
        "streak": int(event["streak"]),
    }
    try:
        node = substrate.add_node("ConflictEvent", attrs)
    except Exception:
        return None
    return node


def list_conflict_events(substrate) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("ConflictEvent"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node_id": nid,
            "mt_a_id": int(attrs.get("mt_a_id", -1)),
            "mt_b_id": int(attrs.get("mt_b_id", -1)),
            "conflicted_node_id": int(attrs.get("node_id", -1)),
            "conflicted_node_name": str(attrs.get("node_name", "")),
            "sigma_a": float(attrs.get("sigma_a", 0.0)),
            "sigma_b": float(attrs.get("sigma_b", 0.0)),
            "streak": int(attrs.get("streak", 0)),
        })
    return out


__all__ = [
    "CONFLICT_MAGNITUDE_THRESHOLD",
    "CONFLICT_STREAK_REQUIRED",
    "detect_conflicts_for_pair",
    "detect_conflicts_all_pairs",
    "record_conflict",
    "list_conflict_events",
]
