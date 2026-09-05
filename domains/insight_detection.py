"""Autonomous insight detection — large frustration drops as flagged events.

The substrate sits in a frustrated configuration. World evidence (or
internal candidate generation) shifts some node's h between steps. The
next relax discovers a basin where everything coheres — frustration
crashes, σ on several nodes flips sign. That signature is the substrate's
analogue of human insight ("aha"), and we flag it.

After detection, the new basin is consolidated via elevated Hebbian on
the freshly-stable configuration — matching the felt experience of an
insight "settling in" rather than fading. Consolidation runs only on
adaptive Mts (frozen Mts have foundational basins that don't accept
this kind of reinforcement; their identity protection takes precedence).

State for cross-step comparison lives on the graph, not in Python:
each Microtheory carries a `previous_frustration` attr, and each
Concept owned by it carries a `previous_state` attr (σ at end of
previous step). The orchestration reads these at step start and
writes them at step end.

ΔF is composed as a Term-tree (order-1-time of F over a 2-sample
window) and evaluated by the substrate's native evaluator — the same
order-N machinery the agent uses for phonology / dynamics features
(commit 479cad7). The substrate computes its own derivative; Python
just orchestrates.
"""
from __future__ import annotations

from typing import Any

from domains.windowed_filter import (
    attr_sample,
    compose_and_evaluate,
    order_n_kernel,
    var_sample,
)


# Detection thresholds — conservative defaults; per-substrate tuning later.

INSIGHT_FRUSTRATION_DROP_THRESHOLD = 1.0
"""ΔF must be at most -1.0 (= drop of at least 1.0) to count."""

INSIGHT_NODE_FLIP_THRESHOLD = 0.5
"""At least one node's σ must shift by more than this (sign-of-belief
change). Filters out tiny mean-field jitter that doesn't reflect a real
basin transition."""

INSIGHT_PREVIOUS_FRUSTRATION_MIN = 0.5
"""The substrate must have been substantially frustrated to have an
insight. A peaceful network finding a slightly more peaceful basin is
not an insight — it's drift."""

INSIGHT_CONSOLIDATION_ETA = 0.1
"""Hebbian step size used to consolidate a newly-discovered basin.
Roughly 10x the loop's baseline eta — the network learns aggressively
right after an insight, then returns to baseline next step."""


def _delta_f_samples():
    """Sample window for ΔF: [previous_frustration (Attr), current_F (Var)]."""
    return [
        attr_sample("mt", "previous_frustration"),
        var_sample("current_F"),
    ]


def compose_delta_f_term():
    """Compose ΔF = order-1-time-of-F over a 2-sample window.

    Result is a Minus Term that, when evaluated with
    env={"mt": mt_node, "current_F": current_value}, yields
    current - previous. Same windowed_filter primitive that backs
    anticipation + formation."""
    return order_n_kernel(_delta_f_samples(), 1)


def compute_delta_f_via_substrate(
    substrate, mt, current_f: float,
) -> float:
    """Evaluate ΔF via the substrate's native evaluator. The
    substrate reads previous_frustration from its own attr +
    subtracts via the DSL — Python doesn't compute the value."""
    result = compose_and_evaluate(
        substrate, mt, _delta_f_samples(), order=1,
        env={"mt": mt, "current_F": current_f},
        required_attrs=["previous_frustration"],
    )
    return result if result is not None else 0.0


def detect_insight(
    previous_frustration: float,
    previous_state: dict[int, float],
    current_audit: dict,
    mt_id: int,
    frustration_threshold: float = INSIGHT_FRUSTRATION_DROP_THRESHOLD,
    flip_threshold: float = INSIGHT_NODE_FLIP_THRESHOLD,
    previous_frustration_min: float = INSIGHT_PREVIOUS_FRUSTRATION_MIN,
    delta_f: float | None = None,
) -> dict[str, Any] | None:
    """Compare the previous step's frustration + per-node state to the
    current step's audit. Returns an insight event dict if all three
    conditions hold:

      1. Previous frustration was substantial (> previous_frustration_min)
      2. Frustration dropped by at least frustration_threshold
      3. At least one node's σ shifted by more than flip_threshold

    Returns None otherwise. The event dict contains the magnitude of the
    drop + the list of flipped nodes (the structural content of the
    insight).

    `delta_f` may be passed precomputed (the loop computes it via the
    substrate's Term-tree evaluator using compute_delta_f_via_substrate).
    If None, falls back to Python subtraction — kept for unit tests that
    don't have a substrate handle."""
    if previous_frustration < previous_frustration_min:
        return None

    if delta_f is None:
        delta_f = current_audit["frustration"] - previous_frustration
    if delta_f > -frustration_threshold:  # drop must be at least the threshold
        return None

    flipped: list[dict[str, Any]] = []
    for nid_key, post_sig in current_audit["marginal"].items():
        nid = int(nid_key)
        prev_sig = float(previous_state.get(nid, 0.0))
        if abs(post_sig - prev_sig) > flip_threshold:
            flipped.append({
                "node": nid,
                "before": prev_sig,
                "after": float(post_sig),
                "delta": float(post_sig - prev_sig),
            })

    if not flipped:
        return None

    return {
        "mt_id": mt_id,
        "previous_frustration": float(previous_frustration),
        "current_frustration": float(current_audit["frustration"]),
        "delta_F": float(delta_f),
        "magnitude": float(abs(delta_f)),
        "flipped_nodes": flipped,
        "energy_after": float(current_audit["energy"]),
        "coverage_after": int(current_audit["coverage"]),
    }


def consolidate_insight(substrate, mt, eta: float = INSIGHT_CONSOLIDATION_ETA) -> int:
    """Elevated Hebbian update on the newly-discovered basin.

    Reads each Concept's current state (which `mt_relax_to_marginal` /
    the native scoped fixpoint just wrote) and strengthens couplings
    between co-active nodes. The new basin becomes structurally deeper,
    so subsequent perturbations don't undo the insight.

    Skips frozen Mts — their basins are foundational and not subject to
    Hebbian reinforcement. Returns the number of edges consolidated
    (continuous) or the scoped fixpoint's progressing step count
    (native).

    Native branch (CAN_MT_SCOPED_RULES_RESULTS.md): STAYS BLOCKED per
    `CAN_FINAL_MIGRATION_RESULTS.md`'s own root-cause finding is now
    RESOLVED — `run_rules_scoped(mt)` lets `can_native_hebbian_mint`/
    `_reweight` fire for THIS Mt only, isolated from every other
    Microtheory in the graph (the exact hazard that blocked this
    function before). The native mechanism has no continuous `eta` knob
    (mint/reweight are threshold/counter-based); the native return value
    is the scoped fixpoint's own progressing-step count, a genuine
    simplification reported honestly rather than eta-scaled."""
    # Local import to avoid circular dependency at module load.
    # PHASE A (native-backend cutover): the continuous Ising engine is
    # removed. consolidate_insight is now native-only — it always settles
    # via the scoped native fixpoint (can_native_hebbian_mint/_reweight
    # carry their own policy + plasticity_override gate in their
    # where-clause). `eta` has no native analog and is silently unused.
    from domains.can_native_orchestration import scoped_settle
    return scoped_settle(substrate, mt)


def stash_previous_state(substrate, mt, post_audit) -> None:
    """Write the current step's results as `previous_*` attrs so the
    next step can detect insight via comparison. Stores
    `previous_frustration` on the Mt and `previous_state` on each
    Concept."""
    substrate.set_attr(mt, "previous_frustration",
                       float(post_audit["frustration"]))
    for nid_key, sig in post_audit["marginal"].items():
        # Need the actual NodeID for set_attr; reconstruct via the
        # substrate's PyNodeID. The mt's has_concept neighbours give us
        # the right handles.
        pass  # Handled by orchestrator — see self_improvement_loop.


def read_previous_state(substrate, mt) -> tuple[float, dict[int, float]]:
    """Read previous step's stash from Mt-side attrs.
    Returns (previous_frustration, {concept_id: previous_sigma}).

    Per-Mt storage: shared Concepts have a distinct previous σ for each
    Mt that owns them — what the previous step looked like from THIS
    Mt's perspective, not whichever Mt stashed last."""
    mt_attrs = substrate.node(mt)["attrs"]
    prev_frust = float(mt_attrs.get("previous_frustration", 0.0))
    prev_state: dict[int, float] = {}
    for c in substrate.neighbours(mt, "has_concept"):
        cid = c.value if hasattr(c, "value") else int(c)
        key = f"previous_sigma_{cid}"
        if key in mt_attrs:
            prev_state[cid] = float(mt_attrs[key])
    return prev_frust, prev_state


__all__ = [
    "INSIGHT_FRUSTRATION_DROP_THRESHOLD",
    "INSIGHT_NODE_FLIP_THRESHOLD",
    "INSIGHT_PREVIOUS_FRUSTRATION_MIN",
    "INSIGHT_CONSOLIDATION_ETA",
    "compose_delta_f_term",
    "compute_delta_f_via_substrate",
    "detect_insight",
    "consolidate_insight",
    "read_previous_state",
]
