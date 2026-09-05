"""The final CAN consumer migration — wiring the three now-closed primitives
(Blocker A: `domains/can_counterfactual.py`; Blocker B:
`domains/can_native_hebbian_bridge.py`; decay/identity:
`seeds/can_decay_identity.json`) into the six consumers
`CAN_CONSUMER_MIGRATION_RESULTS.md` originally left blocked.

See `docs/research/engine_substrate/CAN_FINAL_MIGRATION_PREREG.md` /
`_RESULTS.md` for the full per-consumer plan and the two investigation
findings (`run_rules()` is graph-global; every native CAN rule's match
pattern is Mt-unscoped) that shape it. This file proves, with real numbers
on real scenarios, the TWO consumers that DID migrate
(`drive_curiosity.py::probe_via_what_if`,
`insight_seeking.py::predict_perturbation_impact` + its `seek_insights`
relax-guard) — both GATED by `Mt.discrete_mode`, both preserving the
existing continuous path byte-for-byte for an un-upgraded Mt.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

import domains.can_counterfactual as cf
from domains.drive_curiosity import probe_via_what_if, run_curiosity
from domains.insight_seeking import (
    find_hot_nodes,
    predict_perturbation_impact,
    seek_insights,
)

_NODE_TYPES = ("Microtheory", "Concept")
_EDGE_TYPES = ("has_concept", "causal_influence")


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


def _build_discrete_mt(s, mode="3state", temperature=2.0):
    """A real 4-Concept discrete-mode network, already at a committed
    (not necessarily equilibrium) state — the precondition every native
    path in this rung assumes: `state` is kept current by whatever
    externally drives run_rules(), never by these consumer functions."""
    mt = s.add_node("Microtheory", {"temperature": temperature,
                                    "discrete_mode": mode})
    specs = [
        ("hub", 1.0, 0.3, 0.0),
        ("n1", 1.0, 0.1, 0.0),
        ("n2", -1.0, -0.2, 0.0),
        ("n3", 0.0, 0.0, 0.0),
    ]
    concepts = {}
    for name, state, h, hid in specs:
        c = s.add_node("Concept", {
            "name": name, "state": state,
            "external_field": h, "identity_field": hid,
        })
        concepts[name] = c
        s.add_edge(mt, "has_concept", c, {})
    s.add_edge(concepts["hub"], "causal_influence", concepts["n1"], {"weight": 0.6})
    s.add_edge(concepts["n1"], "causal_influence", concepts["hub"], {"weight": 0.6})
    s.add_edge(concepts["hub"], "causal_influence", concepts["n2"], {"weight": -0.8})
    s.add_edge(concepts["n2"], "causal_influence", concepts["hub"], {"weight": -0.8})
    s.add_edge(concepts["hub"], "causal_influence", concepts["n3"], {"weight": 0.4})
    s.add_edge(concepts["n3"], "causal_influence", concepts["hub"], {"weight": 0.4})
    return mt, concepts


# PHASE A (native-backend cutover): _build_continuous_mt was REMOVED. It
# built a no-discrete_mode Mt used ONLY by the three continuous-branch
# byte-identity tests that were deleted below (the continuous engine they
# pinned no longer exists). All surviving tests build native discrete Mts
# via _build_discrete_mt.


def _snapshot(s, nodes):
    return {n.value: dict(s.node(n)["attrs"]) for n in nodes}


# ---------------------------------------------------------------------
# 1. drive_curiosity.py::probe_via_what_if — native branch wired correctly.
# ---------------------------------------------------------------------

def test_probe_via_what_if_native_branch_matches_can_counterfactual_directly():
    """The migrated function's native branch must return EXACTLY what
    calling domains/can_counterfactual.py::predicted_info_gain directly
    would — this proves the WIRING, not just that the function runs."""
    s = _fresh_substrate()
    mt, concepts = _build_discrete_mt(s, mode="3state")
    hub = concepts["hub"]
    h_delta = 0.5

    result = probe_via_what_if(s, mt, hub, h_delta=h_delta)

    current_h = float(s.node(hub)["attrs"]["external_field"])
    direct = cf.predicted_info_gain(s, mt, hub, current_h + h_delta, mode="3state")

    assert result["info_gain_total_change"] == pytest.approx(
        direct["info_gain_total_change"])
    assert result["info_gain_max_node_change"] == pytest.approx(
        direct["info_gain_max_node_change"])
    assert result["predicted_flipped_count"] == direct["predicted_flipped_count"]
    print(f"native probe_via_what_if: total_change={result['info_gain_total_change']:.4f} "
          f"max_change={result['info_gain_max_node_change']:.4f} "
          f"flipped={result['predicted_flipped_count']}")


def test_probe_via_what_if_native_branch_never_mutates_graph():
    s = _fresh_substrate()
    mt, concepts = _build_discrete_mt(s, mode="3state")
    all_nodes = [mt] + list(concepts.values())
    before = _snapshot(s, all_nodes)
    probe_via_what_if(s, mt, concepts["hub"], h_delta=1.5)
    after = _snapshot(s, all_nodes)
    assert after == before, "native probe_via_what_if must not mutate the graph"


# PHASE A (native-backend cutover): test_probe_via_what_if_continuous_branch_
# is_byte_identical_to_pre_migration was REMOVED. It pinned the removed
# continuous branch (mt_mean_field_marginal/mt_mean_field_with_h_override)
# byte-for-byte on a no-discrete_mode Mt. That branch no longer exists;
# probe_via_what_if is native-only. The native path is already covered by
# test_probe_via_what_if_native_branch_matches_can_counterfactual_directly
# above. No surviving behaviour is left uncovered.


def test_run_curiosity_still_works_end_to_end_on_a_native_mt():
    """The unmigrated caller (run_curiosity/find_ambivalent_nodes) composes
    transparently with the migrated probe — no caller-side changes needed."""
    s = _fresh_substrate()
    mt, concepts = _build_discrete_mt(s, mode="3state")
    # n3 has state=0.0 -- ambivalent by construction.
    probes = run_curiosity(s, mt, top_k=3)
    assert probes, "expected at least one probe on the ambivalent node"
    assert probes[0]["concept_id"] == concepts["n3"].value


# ---------------------------------------------------------------------
# 2. insight_seeking.py::predict_perturbation_impact — native branch,
#    including the claimed SIMPLIFICATION (no field-correction hack
#    needed).
# ---------------------------------------------------------------------

def test_predict_perturbation_impact_native_branch_needs_no_correction_hack():
    """The whole point of the migration per the PREREG: predicted_energy
    computed via the native path must equal a DIRECT, uncorrected
    mt_energy(mt, predicted_marginal) call — i.e. no field-correction term
    is needed, unlike the continuous branch's own hand-written one."""
    s = _fresh_substrate()
    mt, concepts = _build_discrete_mt(s, mode="3state")
    hub = concepts["hub"]
    new_h = 4.0

    result = predict_perturbation_impact(s, mt, hub, new_h)

    from domains.can_counterfactual import predict_ripple
    ripple = predict_ripple(s, mt, hub, new_h, mode="3state")
    direct_energy = s.mt_energy(mt, ripple["predicted_state"])
    assert result["predicted_energy"] == pytest.approx(direct_energy), (
        "native predicted_energy must equal an UNCORRECTED mt_energy call "
        "on the predicted marginal -- confirming the field-correction hack "
        "genuinely isn't needed on this branch"
    )
    print(f"native predict_perturbation_impact: predicted_energy={result['predicted_energy']:.4f} "
          f"(== direct uncorrected mt_energy={direct_energy:.4f}) "
          f"predicted_delta_F={result['predicted_delta_F']:.4f}")


def test_predict_perturbation_impact_native_branch_never_mutates_graph():
    s = _fresh_substrate()
    mt, concepts = _build_discrete_mt(s, mode="3state")
    all_nodes = [mt] + list(concepts.values())
    before = _snapshot(s, all_nodes)
    predict_perturbation_impact(s, mt, concepts["hub"], -2.0)
    after = _snapshot(s, all_nodes)
    assert after == before, "native predict_perturbation_impact must not mutate the graph"


# PHASE A (native-backend cutover): test_predict_perturbation_impact_
# continuous_branch_byte_identical_to_pre_migration was REMOVED. It pinned
# the removed continuous branch (mt_mean_field_marginal /
# mt_mean_field_with_h_override / mt_audit_basin + the hand-written
# field-correction hack) byte-for-byte. The native path is covered by
# test_predict_perturbation_impact_native_branch_needs_no_correction_hack.


# ---------------------------------------------------------------------
# 3. insight_seeking.py::seek_insights — the relax-guard, real before/after.
# ---------------------------------------------------------------------

def test_seek_insights_skips_continuous_relax_on_a_native_mt():
    """A discrete_mode Mt's `state` must NOT be touched by seek_insights.
    PHASE A (native-backend cutover): seek_insights is native-only and no
    longer relaxes state at all (the continuous mt_relax_to_marginal
    fallback was removed); this pins that a native Mt's committed state
    survives a seek_insights call untouched."""
    s = _fresh_substrate()
    mt, concepts = _build_discrete_mt(s, mode="3state")
    before_states = {name: float(s.node(c)["attrs"]["state"])
                     for name, c in concepts.items()}

    seek_insights(s, mt, top_k_hot=3)

    after_states = {name: float(s.node(c)["attrs"]["state"])
                    for name, c in concepts.items()}
    assert after_states == before_states, (
        "seek_insights must NOT relax a discrete_mode Mt's state: "
        f"before={before_states} after={after_states}"
    )
    print(f"native seek_insights: state preserved exactly, {after_states}")


# PHASE A (native-backend cutover): test_seek_insights_still_relaxes_a_
# continuous_mt was REMOVED. It asserted the removed continuous relax path
# (mt_relax_to_marginal) still fires for a no-discrete_mode Mt. seek_insights
# is now native-only and deliberately does NOT relax state — the inverse
# behaviour, already asserted by test_seek_insights_skips_continuous_relax_
# on_a_native_mt above.


# ---------------------------------------------------------------------
# 4. insight_seeking.py::find_hot_nodes — confirmed UNCHANGED, works
#    identically for both representations (node_local_frustration is
#    already representation-agnostic; no native twin needed or built).
# ---------------------------------------------------------------------

def test_find_hot_nodes_works_unmodified_on_a_native_mt():
    s = _fresh_substrate()
    mt, concepts = _build_discrete_mt(s, mode="3state")
    hot = find_hot_nodes(s, mt, top_k=5, min_frustration=0.01)
    hot_ids = {row["node_id"] for row in hot}
    # hub is coupled +0.6 to n1 (state +1, satisfied) and -0.8 to n2
    # (state -1, satisfied) and +0.4 to n3 (state 0, no contribution) --
    # so hub itself should show near-zero LOCAL frustration; the point of
    # this test is only that the function runs correctly on discrete
    # state (±1/0) with no code change, not any particular topology.
    assert isinstance(hot, list)
    for row in hot:
        assert row["current_sigma"] in (-1.0, 0.0, 1.0), (
            "find_hot_nodes read discrete state correctly with zero "
            f"migration needed: {row}"
        )
    print(f"find_hot_nodes on a native Mt (unmigrated, unmodified): {hot_ids}")
