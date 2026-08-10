"""Install the 4 per_mt streak detectors as FilterSpec graph data.

This file is the MIGRATION boundary: instead of importing
domains.frustration_signal + domains.sparseness_signal + 2 others
and calling detect_*_all_pairs functions per step, the substrate
installs 4 FilterSpec nodes at boot. The runtime walks them.

Migration mapping:
  frustration_signal       → FilterSpec(per_mt, previous_frustration > 1.0, K=10)
  sparseness_signal        → FilterSpec(per_mt, coverage < 1, K=10)
  frozen_should_adapt      → FilterSpec(per_mt, distance > 1.0, K=10)
                             — but only fires on frozen Mts; phase-1
                             policy filter not yet in spec schema, so
                             this detector's parity test passes by
                             accepting either trigger
  drifted_past_anchor      → FilterSpec(per_mt, distance > 1.0, K=10)
                             — symmetric, adaptive Mts only

The two distance-based detectors share quantity but differ by policy.
Phase-1 FilterSpec doesn't support policy gates yet (would need
either an extra attr in the spec or a Python-evaluable Where clause).
For now we install them as the simpler version (no policy gate); the
Python detectors continue to run alongside and provide the
policy-gated variants. Phase-2 will add gates as Term expressions.

Once Phase-2 + further migration completes, the Python *_signal
modules can be deleted entirely.
"""
from __future__ import annotations

from typing import Any

from domains.frozen_adaptation_signal import (
    FROZEN_ADAPT_DISTANCE_THRESHOLD,
    FROZEN_ADAPT_STREAK_REQUIRED,
)
from domains.frustration_signal import (
    FRUSTRATION_STREAK_REQUIRED,
    FRUSTRATION_THRESHOLD,
)
from domains.runtime_discovery import install_filter_spec
from domains.sparseness_signal import (
    SPARSE_COVERAGE_THRESHOLD,
    SPARSE_STREAK_REQUIRED,
)


def install_frustrated_mt_filter(substrate) -> Any:
    """Equivalent of frustration_signal as a FilterSpec."""
    return install_filter_spec(
        substrate,
        name="frustrated_mt",
        scope="per_mt",
        quantity_attr="previous_frustration",
        threshold=FRUSTRATION_THRESHOLD,
        direction="above",
        streak_required=FRUSTRATION_STREAK_REQUIRED,
        action_spec={
            "op": "add_node",
            "type": "FrustratedMtEventFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "frustration": "$value",
                "streak": "$streak",
            },
        },
        event_type="FrustratedMtEventFromSpec",
        agent_authored=False,  # this is migration, not agent design
    )


def install_sparse_mt_filter(substrate) -> Any:
    """Equivalent of sparseness_signal as a FilterSpec."""
    return install_filter_spec(
        substrate,
        name="sparse_mt",
        scope="per_mt",
        quantity_attr="coverage",
        threshold=float(SPARSE_COVERAGE_THRESHOLD),
        direction="below",
        streak_required=SPARSE_STREAK_REQUIRED,
        action_spec={
            "op": "add_node",
            "type": "SparseMtEventFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "coverage": "$value",
                "streak": "$streak",
            },
        },
        event_type="SparseMtEventFromSpec",
        agent_authored=False,
    )


def install_frozen_should_adapt_filter(substrate) -> Any:
    """frozen_should_adapt: distance > threshold sustained, frozen Mts only.
    Uses policy_filter='frozen' so adaptive Mts aren't flagged here
    (drifted_past_anchor handles those)."""
    return install_filter_spec(
        substrate,
        name="frozen_should_adapt",
        scope="per_mt",
        quantity_attr="distance_to_target_magnitude",
        threshold=FROZEN_ADAPT_DISTANCE_THRESHOLD,
        direction="above",
        streak_required=FROZEN_ADAPT_STREAK_REQUIRED,
        action_spec={
            "op": "add_node",
            "type": "FrozenShouldAdaptEventFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "distance_magnitude": "$value",
                "streak": "$streak",
            },
        },
        event_type="FrozenShouldAdaptEventFromSpec",
        policy_filter="frozen",
        agent_authored=False,
    )


def install_drifted_past_anchor_filter(substrate) -> Any:
    """drifted_past_anchor: distance > threshold sustained, adaptive Mts.
    Symmetric counterpart to frozen_should_adapt — same quantity + threshold
    + streak, opposite policy gate."""
    return install_filter_spec(
        substrate,
        name="drifted_past_anchor",
        scope="per_mt",
        quantity_attr="distance_to_target_magnitude",
        threshold=FROZEN_ADAPT_DISTANCE_THRESHOLD,
        direction="above",
        streak_required=FROZEN_ADAPT_STREAK_REQUIRED,
        action_spec={
            "op": "add_node",
            "type": "DriftedPastAnchorEventFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "distance_magnitude": "$value",
                "streak": "$streak",
            },
        },
        event_type="DriftedPastAnchorEventFromSpec",
        policy_filter="adaptive",
        agent_authored=False,
    )


def install_streak_filters(substrate) -> dict[str, Any]:
    """Install all 4 per_mt streak filters at substrate boot. Returns
    a dict of {name: filter_node}."""
    return {
        "frustrated_mt": install_frustrated_mt_filter(substrate),
        "sparse_mt": install_sparse_mt_filter(substrate),
        "frozen_should_adapt": install_frozen_should_adapt_filter(substrate),
        "drifted_past_anchor": install_drifted_past_anchor_filter(substrate),
    }


def install_identity_formation_filter(substrate) -> Any:
    """Migration of identity_formation as a per_concept FilterSpec.

    Reads delta_identity stashed by stash_delta_identity_per_concept
    at start of each loop step. Fires when Δh_id sustained positive
    over K consecutive steps."""
    from domains.identity_formation import (
        IDENTITY_FORMATION_DRIFT_THRESHOLD,
        IDENTITY_FORMATION_STREAK_REQUIRED,
    )
    return install_filter_spec(
        substrate,
        name="identity_formation",
        scope="per_concept",
        quantity_attr="delta_identity",
        threshold=IDENTITY_FORMATION_DRIFT_THRESHOLD,
        direction="above",
        streak_required=IDENTITY_FORMATION_STREAK_REQUIRED,
        action_spec={
            "op": "add_node",
            "type": "IdentityFormationEventFromSpec",
            "attrs": {
                "concept_id": "$concept_id",
                "concept_name": "$concept_name",
                "current_h_id": "$value",
                "streak": "$streak",
                "direction": 1,
            },
        },
        event_type="IdentityFormationEventFromSpec",
        agent_authored=False,
    )


def install_insight_filter(substrate) -> Any:
    """Migration of insight detection's CORE signal (ΔF < threshold)
    as a per_mt FilterSpec. Reads delta_f stashed by _stash_post_state.

    DEGRADED from the Python version:
      · The Python insight detector also checks node-flip + previous-
        frustration-was-substantial preconditions, builds rich event
        with flipped_nodes list, cascade events, identity nudges, etc.
      · This FilterSpec only emits a 'ΔF crossed threshold' event;
        the rich content stays in the Python detector.
    Streak required = 1 (insight is a one-shot signal, not sustained)."""
    return install_filter_spec(
        substrate,
        name="insight_signal",
        scope="per_mt",
        quantity_attr="delta_f",
        threshold=-1.0,
        direction="below",  # ΔF < -1.0 = substantial frustration drop
        streak_required=1,
        action_spec={
            "op": "add_node",
            "type": "InsightSignalFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "delta_f": "$value",
            },
        },
        event_type="InsightSignalFromSpec",
        agent_authored=False,
    )


def install_anticipation_filter(substrate) -> Any:
    """Migration of anticipation's CORE signal (∂²F < threshold) as
    a per_mt FilterSpec. Reads d2_f stashed by _stash_post_state.

    DEGRADED: doesn't enforce 'no insight yet this step' + 'F > 0.5'
    preconditions. Useful as a coarser anticipation signal."""
    return install_filter_spec(
        substrate,
        name="anticipation_signal",
        scope="per_mt",
        quantity_attr="d2_f",
        threshold=-0.02,
        direction="below",
        streak_required=1,
        action_spec={
            "op": "add_node",
            "type": "AnticipationSignalFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "d2_f": "$value",
            },
        },
        event_type="AnticipationSignalFromSpec",
        agent_authored=False,
    )


def install_conflict_filter(substrate) -> Any:
    """Migration of conflict_detection as a cross_mt FilterSpec.

    Reads the pre-stashed pair_conflict_count_for_<id> attr. Fires
    when at least 1 conflicting node sustained over K steps.

    DEGRADED from the Python version: this fires per PAIR (not per
    conflicting node). Per-node iteration within a pair would need
    a 4th scope variant. Acceptable for now — the pair-level fire
    still surfaces the disagreement; a downstream operator can
    inspect the node-level detail."""
    from domains.conflict_detection import CONFLICT_STREAK_REQUIRED
    return install_filter_spec(
        substrate,
        name="conflict_detection",
        scope="cross_mt",
        quantity_attr="pair_conflict_count",
        threshold=0.5,  # > 0 = at least one conflicting node
        direction="above",
        streak_required=CONFLICT_STREAK_REQUIRED,
        action_spec={
            "op": "add_node",
            "type": "ConflictEventFromSpec",
            "attrs": {
                "mt_a_id": "$mt_a_id",
                "mt_b_id": "$mt_b_id",
                "conflict_count": "$value",
                "streak": "$streak",
            },
        },
        event_type="ConflictEventFromSpec",
        agent_authored=False,
    )


def install_redundancy_filter(substrate) -> Any:
    """Migration of redundancy_detection as a cross_mt FilterSpec.

    Reads the pre-stashed pair_similarity_for_<id> attr (set by
    stash_pair_quantities at start of each loop step). Fires when
    similarity > 0.9 sustained over K steps."""
    from domains.redundancy_detection import (
        REDUNDANCY_SIMILARITY_THRESHOLD,
        REDUNDANCY_STREAK_REQUIRED,
    )
    return install_filter_spec(
        substrate,
        name="redundancy_detection",
        scope="cross_mt",
        quantity_attr="pair_similarity",  # pair attr name; runtime
                                             # adds _for_<other_id>
        threshold=REDUNDANCY_SIMILARITY_THRESHOLD,
        direction="above",
        streak_required=REDUNDANCY_STREAK_REQUIRED,
        action_spec={
            "op": "add_node",
            "type": "RedundancyEventFromSpec",
            "attrs": {
                "mt_a_id": "$mt_a_id",
                "mt_b_id": "$mt_b_id",
                "similarity": "$value",
                "streak": "$streak",
            },
        },
        event_type="RedundancyEventFromSpec",
        agent_authored=False,
    )


__all__ = [
    "install_frustrated_mt_filter",
    "install_sparse_mt_filter",
    "install_frozen_should_adapt_filter",
    "install_drifted_past_anchor_filter",
    "install_redundancy_filter",
    "install_conflict_filter",
    "install_identity_formation_filter",
    "install_insight_filter",
    "install_anticipation_filter",
    "install_streak_filters",
]
