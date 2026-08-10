"""Identity-formation signal — order-1-time of h_id detects sustained
commitment forming on a node.

When identity_field on a Concept grows (or shrinks) by more than a small
threshold for K consecutive steps, the substrate flags an
IdentityFormationEvent. 'I'm becoming committed to this' — a
queryable, structural marker that the substrate is acquiring a new
identity-level position.

Mechanism uses the same order_n_concepts machinery the agent already
owns:
  Δh_id = order-1-time-of-h_id over a 2-sample window
        = Var("current_h_id") - Attr(Var("mt"), "previous_identity_<cid>")
Composed by nth_order_terms, evaluated by the substrate's native
evaluator — Python doesn't compute the derivative.

Streak tracking lives on the Mt (per-Concept attrs):
  formation_streak_<cid>     — consecutive steps with same direction
  formation_direction_<cid>  — +1 (growing positive), -1 (negative), 0 (idle)

The event fires when streak crosses IDENTITY_FORMATION_STREAK_REQUIRED.
Only one step has streak == K, so no need for separate dedup —
each formation phase fires exactly once.
"""
from __future__ import annotations

from typing import Any

from domains.windowed_filter import (
    attr_sample,
    compose_and_evaluate,
    order_n_kernel,
    var_sample,
)


IDENTITY_FORMATION_DRIFT_THRESHOLD = 0.005
"""Min |Δh_id| per step to count as drift in a direction. Smaller →
more sensitive but more noise. With α=0.02, β=0.001 and σ=+1 starting
from h_id=0, Δh_id = 0.02 per step well above this threshold."""

IDENTITY_FORMATION_STREAK_REQUIRED = 10
"""How many consecutive same-direction steps to count as formation.
At α=0.02 per step this is ~10 steps of meaningful drift = ~0.2
identity-field accumulated, structurally substantial."""


def _delta_identity_samples(concept_id: int):
    """Sample window for Δh_id on a specific concept:
    [previous_identity_<cid> (Attr), current_h_id (Var)]."""
    return [
        attr_sample("mt", f"previous_identity_{concept_id}"),
        var_sample("current_h_id"),
    ]


def compose_delta_identity_term(concept_id: int):
    """Compose Δh_id = order-1-time of identity_field over a 2-sample
    window. Built via the shared windowed_filter primitive."""
    return order_n_kernel(_delta_identity_samples(concept_id), 1)


def compute_delta_identity(
    substrate, mt, concept_id: int, current_h_id: float,
) -> float:
    """Evaluate Δh_id via the substrate's evaluator. Returns 0.0 if
    no previous_identity attr exists yet for this concept."""
    result = compose_and_evaluate(
        substrate, mt, _delta_identity_samples(concept_id), order=1,
        env={"mt": mt, "current_h_id": current_h_id},
        required_attrs=[f"previous_identity_{concept_id}"],
    )
    return result if result is not None else 0.0


def detect_identity_formation(
    substrate, mt,
    threshold: float = IDENTITY_FORMATION_DRIFT_THRESHOLD,
    required_streak: int = IDENTITY_FORMATION_STREAK_REQUIRED,
) -> list[dict[str, Any]]:
    """For each Concept owned by Mt, compute Δh_id via Term-tree,
    update streak attr, fire IdentityFormationEvent when streak first
    crosses required_streak (this gives one event per formation
    'phase' — when streak resets to 0 and re-climbs, another fires).

    Returns list of event dicts (one per formation that crystallised
    this step; usually 0 or 1)."""
    events: list[dict[str, Any]] = []
    mt_attrs = substrate.node(mt)["attrs"]

    for c in substrate.neighbours(mt, "has_concept"):
        cid = c.value if hasattr(c, "value") else int(c)
        current_h_id = float(substrate.node(c)["attrs"].get(
            "identity_field", 0.0))
        prev_key = f"previous_identity_{cid}"
        streak_key = f"formation_streak_{cid}"
        direction_key = f"formation_direction_{cid}"

        if prev_key not in mt_attrs:
            # No history yet — can't compute Δ.
            continue

        delta = compute_delta_identity(substrate, mt, cid, current_h_id)
        if delta > threshold:
            current_direction = 1
        elif delta < -threshold:
            current_direction = -1
        else:
            current_direction = 0

        prev_streak = int(mt_attrs.get(streak_key, 0))
        prev_direction = int(mt_attrs.get(direction_key, 0))

        if current_direction == 0:
            new_streak = 0
            new_direction = 0
        elif current_direction == prev_direction:
            new_streak = prev_streak + 1
            new_direction = current_direction
        else:
            new_streak = 1
            new_direction = current_direction

        substrate.set_attr(mt, streak_key, new_streak)
        substrate.set_attr(mt, direction_key, new_direction)

        # Fire when streak crosses required_streak (only one step has
        # streak == K), so each formation phase fires exactly once.
        if new_streak == required_streak:
            attrs = substrate.node(c)["attrs"]
            name = str(attrs.get("name", f"node_{cid}"))
            events.append({
                "concept_id": cid,
                "concept_name": name,
                "current_h_id": current_h_id,
                "delta_h_id": delta,
                "direction": new_direction,
                "streak": new_streak,
            })

    return events


def record_identity_formation(
    substrate, mt, event: dict[str, Any],
) -> Any | None:
    """Create an IdentityFormationEvent node + link from Mt via
    has_formation. Returns the new node or None if productions aren't
    configured."""
    attrs = {
        "concept_id": int(event["concept_id"]),
        "concept_name": str(event["concept_name"]),
        "current_h_id": float(event["current_h_id"]),
        "delta_h_id": float(event["delta_h_id"]),
        "direction": int(event["direction"]),
        "streak": int(event["streak"]),
    }
    try:
        node = substrate.add_node("IdentityFormationEvent", attrs)
    except Exception:
        return None
    try:
        substrate.add_edge(mt, "has_formation", node, {})
    except Exception:
        pass
    return node


def list_formations(substrate, mt) -> list[dict[str, Any]]:
    """Walk Mt → has_formation → IdentityFormationEvent. Return
    summary list."""
    out: list[dict[str, Any]] = []
    for n in substrate.neighbours(mt, "has_formation"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node_id": nid,
            "concept_id": int(attrs.get("concept_id", -1)),
            "concept_name": str(attrs.get("concept_name", "")),
            "current_h_id": float(attrs.get("current_h_id", 0.0)),
            "delta_h_id": float(attrs.get("delta_h_id", 0.0)),
            "direction": int(attrs.get("direction", 0)),
            "streak": int(attrs.get("streak", 0)),
        })
    return out


__all__ = [
    "IDENTITY_FORMATION_DRIFT_THRESHOLD",
    "IDENTITY_FORMATION_STREAK_REQUIRED",
    "compose_delta_identity_term",
    "compute_delta_identity",
    "detect_identity_formation",
    "record_identity_formation",
    "list_formations",
]
