"""Redundancy detection — substrate notices when two Mts have converged
to the same content.

This module IMPLEMENTS the design output by scripts/agent_designs_filter.py.
The substrate's own self_improvement_dynamics Mt names
`fail_mode_redundant_Mt` as 'Two Mts with > 90% identical target
equilibria. Coupling overlap > threshold.' The agent's introspection
specified:

    scope: cross_mt
    samples: marginal_vector(mt_a), marginal_vector(mt_b)
    kernel: cosine_similarity_over_shared_concepts
    gate: similarity > 0.9 sustained for N steps + shared_concept_count > 2
    action: emit RedundancyEvent linking the two Mts; trigger merge
            correction

This file emits the structure the agent designed. The merge correction
itself is a downstream operator (RedundancyEvent provides the data;
how to act on it is a separate decision per the user's principle that
the substrate decides).
"""
from __future__ import annotations

from typing import Any


REDUNDANCY_SIMILARITY_THRESHOLD = 0.9
"""Cosine similarity above this counts as 'agreeing on the shared
nodes'. Matches the Mt's own definition (>90%)."""

REDUNDANCY_STREAK_REQUIRED = 5
"""Consecutive steps the similarity must remain high. Filters out
transient coincidence (e.g., both Mts in resting state)."""

REDUNDANCY_MIN_SHARED = 3
"""Must share at least this many Concepts. Below this, similarity
isn't meaningful — two unrelated Mts that share a couple of nodes
shouldn't be flagged."""


def _pair_streak_key(other_mt_id: int) -> str:
    """Per-pair streak attr key, stashed on the lower-id Mt. The key
    encodes which other-Mt this pair targets so a single Mt can be in
    many pairs without collision."""
    return f"redundancy_streak_for_{other_mt_id}"


def _pair_record_key(other_mt_id: int) -> str:
    """Tracks whether a RedundancyEvent has been recorded for this
    pair (so we don't fire twice from the same continuous streak)."""
    return f"redundancy_recorded_for_{other_mt_id}"


def detect_redundancy_for_pair(
    substrate, mt_a, mt_b,
    similarity_threshold: float = REDUNDANCY_SIMILARITY_THRESHOLD,
    streak_required: int = REDUNDANCY_STREAK_REQUIRED,
    min_shared: int = REDUNDANCY_MIN_SHARED,
) -> dict[str, Any] | None:
    """Check if the (mt_a, mt_b) pair is currently redundant. Updates
    the streak counter on the canonical (lower-id) Mt. Returns an
    event dict iff:
      · shared_concept_count > min_shared
      · similarity > similarity_threshold (this step)
      · streak == streak_required (first crossing — fires exactly once
        per continuous streak)"""
    mt_a_id = mt_a.value if hasattr(mt_a, "value") else int(mt_a)
    mt_b_id = mt_b.value if hasattr(mt_b, "value") else int(mt_b)
    # Canonical ordering — lower id holds the pair-streak.
    if mt_a_id > mt_b_id:
        mt_a, mt_b = mt_b, mt_a
        mt_a_id, mt_b_id = mt_b_id, mt_a_id

    sim_result = substrate.mt_pairwise_similarity(mt_a, mt_b)
    similarity = float(sim_result["similarity"])
    shared_count = int(sim_result["shared_count"])

    if shared_count < min_shared:
        # Reset streak — pair doesn't qualify.
        substrate.set_attr(mt_a, _pair_streak_key(mt_b_id), 0)
        substrate.set_attr(mt_a, _pair_record_key(mt_b_id), False)
        return None

    mt_a_attrs = substrate.node(mt_a)["attrs"]
    prev_streak = int(mt_a_attrs.get(_pair_streak_key(mt_b_id), 0))
    already_recorded = bool(mt_a_attrs.get(_pair_record_key(mt_b_id), False))

    if similarity > similarity_threshold:
        new_streak = prev_streak + 1
    else:
        new_streak = 0
        already_recorded = False
    substrate.set_attr(mt_a, _pair_streak_key(mt_b_id), new_streak)
    substrate.set_attr(mt_a, _pair_record_key(mt_b_id), already_recorded)

    # Fire on streak crossing required, exactly once per continuous run.
    if new_streak >= streak_required and not already_recorded:
        substrate.set_attr(mt_a, _pair_record_key(mt_b_id), True)
        return {
            "mt_a_id": mt_a_id,
            "mt_b_id": mt_b_id,
            "similarity": similarity,
            "shared_concept_count": shared_count,
            "streak": new_streak,
        }
    return None


def detect_redundancy_all_pairs(
    substrate,
    similarity_threshold: float = REDUNDANCY_SIMILARITY_THRESHOLD,
    streak_required: int = REDUNDANCY_STREAK_REQUIRED,
    min_shared: int = REDUNDANCY_MIN_SHARED,
) -> list[dict[str, Any]]:
    """Walk all Microtheory pairs; detect redundancy events.

    O(N²) in number of Mts. Each pair's similarity computation runs
    two mean-field relaxations (one per Mt). For substrates with many
    Mts a smarter scheduler (only pairs sharing > min_shared concepts)
    would help; for now the direct iteration is sufficient."""
    mts = list(substrate.nodes("Microtheory"))
    events: list[dict[str, Any]] = []
    for i, mt_a in enumerate(mts):
        for mt_b in mts[i + 1:]:
            event = detect_redundancy_for_pair(
                substrate, mt_a, mt_b,
                similarity_threshold=similarity_threshold,
                streak_required=streak_required,
                min_shared=min_shared,
            )
            if event is not None:
                events.append(event)
    return events


def record_redundancy(substrate, event: dict[str, Any]) -> Any | None:
    """Create a RedundancyEvent node carrying the pair + similarity
    + shared count. The action 'trigger merge correction' is left
    to a downstream operator — the event surfaces the data; what to
    do with it is the substrate's later decision."""
    attrs = {
        "mt_a_id": int(event["mt_a_id"]),
        "mt_b_id": int(event["mt_b_id"]),
        "similarity": float(event["similarity"]),
        "shared_concept_count": int(event["shared_concept_count"]),
        "streak": int(event["streak"]),
    }
    try:
        node = substrate.add_node("RedundancyEvent", attrs)
    except Exception:
        return None
    return node


def list_redundancy_events(substrate) -> list[dict[str, Any]]:
    """Return all RedundancyEvent nodes currently in the graph."""
    out: list[dict[str, Any]] = []
    for n in substrate.nodes("RedundancyEvent"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node_id": nid,
            "mt_a_id": int(attrs.get("mt_a_id", -1)),
            "mt_b_id": int(attrs.get("mt_b_id", -1)),
            "similarity": float(attrs.get("similarity", 0.0)),
            "shared_concept_count": int(attrs.get(
                "shared_concept_count", 0)),
            "streak": int(attrs.get("streak", 0)),
        })
    return out


__all__ = [
    "REDUNDANCY_SIMILARITY_THRESHOLD",
    "REDUNDANCY_STREAK_REQUIRED",
    "REDUNDANCY_MIN_SHARED",
    "detect_redundancy_for_pair",
    "detect_redundancy_all_pairs",
    "record_redundancy",
    "list_redundancy_events",
]
