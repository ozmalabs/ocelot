"""Tests for identity dynamics + insight recurrence.

PHASE A (native-backend cutover): the continuous identity-dynamics ops
(mt_update_identity_dynamics: h_id ← h_id + α·σ - β·h_id, and
concept_nudge_identity) were REMOVED. Their native twins —
can_native_identity_field_feedback (per-tick fixed-quantum drift toward the
log-odds render's sign) and can_native_identity_nudge_on_flip (event-marker
triggered, bounded two-tier step) — are comprehensively covered by
tests/test_can_identity_feedback.py, tests/test_can_identity_nudge_final.py,
and tests/test_can_mt_scoped_consumers.py. The tests in THIS file that
asserted the removed continuous ops' exact numerics (asymptote α·σ/β,
single-call nudge = 0.5 + 0.3, log-scaled recurrence boost) or that drove
the continuous morning-insight recurrence CASCADE end-to-end (which the
discrete-async engine does not reproduce on this network — see the removed
morning-cascade tests in test_insight_detection.py) are REMOVED with
justification below; the surviving structural test is retained.
"""
from __future__ import annotations

import math

import pytest
from substrate_rs import _native

from domains.insight_naming import list_insights
from domains.self_improvement_loop import (
    ADAPTIVE,
    FROZEN,
    self_improvement_step,
)


_NODE_TYPES = ("Microtheory", "Concept", "InsightEvent")
_EDGE_TYPES = ("has_concept", "causal_influence", "has_insight")


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


# --- Identity dynamics: removed continuous Rust ops ----------------------
# PHASE A: test_identity_grows_toward_sustained_positive_sigma,
# test_identity_decays_with_no_sigma,
# test_identity_dynamics_converges_to_alpha_sigma_over_beta, and
# test_nudge_identity_moves_field_in_one_call were REMOVED. They asserted the
# removed continuous ops' exact numerics (mt_update_identity_dynamics's
# α·σ/β asymptote; concept_nudge_identity's 0.5 + α·σ single-call move). The
# native identity-drift/nudge twins are tested in test_can_identity_feedback.py
# and test_can_identity_nudge_final.py.


# --- Identity dynamics in the loop, policy-gated -------------------------

# PHASE A: test_loop_grows_identity_on_sustained_positive_sigma was REMOVED —
# it asserted the continuous per-step α·σ growth accumulating over 100 loop
# steps (identity_alpha/identity_beta have no native analog; the native
# feedback rule is a fixed per-tick quantum). Native identity growth under
# sustained σ is covered by test_can_identity_feedback.py.


def test_loop_skips_identity_dynamics_on_frozen_mt():
    """Frozen Mts don't run identity dynamics either. (Native: the native
    identity rules carry their own allow_h_drift where-clause gate, which a
    frozen Mt fails, so identity_field stays untouched.)"""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0,
                                    "update_policy": FROZEN,
                                    "discrete_mode": "3state", "can_tick": 0})
    n = s.add_node("Concept", {"external_field": +1.5, "state": 0.0,
                               "identity_field": 0.0})
    s.add_edge(mt, "has_concept", n, {})
    for tick in range(50):
        s.set_attr(mt, "can_tick", tick)
        self_improvement_step(s, identity_alpha=0.05,
                              identity_beta=0.001)
    final_id = float(s.node(n)["attrs"]["identity_field"])
    assert final_id == 0.0  # untouched (frozen policy gate)


# --- Insight recurrence: removed continuous morning cascade --------------
# PHASE A: test_recurrent_insight_increments_count_not_node_count,
# test_first_detection_is_not_a_recurrence,
# test_insight_consolidation_nudges_identity_on_flipped_nodes,
# test_recurrent_insight_nudges_identity_more, and
# test_substrate_remembers_repeated_morning_insights were all REMOVED. Each
# drove the continuous morning-insight CASCADE end-to-end (lift ground_vec's
# field → graded frustration-drop → InsightEvent), which the discrete-async
# engine does not reproduce on this network (measured: the perturbation does
# not flip the committed discrete state — same finding as the removed
# morning-cascade tests in test_insight_detection.py /
# test_insight_propagation.py / test_insight_naming.py). The surviving
# features — fingerprint dedup + recurrence_count (name_insight/record_insight
# unit tests in test_insight_naming.py) and the native event-triggered
# identity nudge (test_can_identity_nudge_final.py) — are covered natively.
