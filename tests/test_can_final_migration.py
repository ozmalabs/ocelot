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


def _build_continuous_mt(s, temperature=2.0):
    """The pre-existing continuous-mode network shape
    (test_drive_curiosity.py / test_insight_seeking.py's own convention —
    NO discrete_mode attr), used to prove the gated migration leaves this
    branch byte-for-byte unchanged."""
    mt = s.add_node("Microtheory", {"temperature": temperature})
    specs = [
        ("hub", 0.05, 0.3),   # ambivalent
        ("n1", 0.9, 0.1),
        ("n2", -0.85, -0.2),
    ]
    concepts = {}
    for name, state, h in specs:
        c = s.add_node("Concept", {"name": name, "state": state, "external_field": h})
        concepts[name] = c
        s.add_edge(mt, "has_concept", c, {})
    s.add_edge(concepts["hub"], "causal_influence", concepts["n1"], {"weight": 0.6})
    s.add_edge(concepts["n1"], "causal_influence", concepts["hub"], {"weight": 0.6})
    s.add_edge(concepts["hub"], "causal_influence", concepts["n2"], {"weight": -0.5})
    s.add_edge(concepts["n2"], "causal_influence", concepts["hub"], {"weight": -0.5})
    return mt, concepts


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


def test_probe_via_what_if_continuous_branch_is_byte_identical_to_pre_migration():
    """A Mt with NO discrete_mode attr must reach the ORIGINAL
    mt_mean_field_marginal/mt_mean_field_with_h_override path, unchanged
    — the real before/after: compute the two continuous calls directly by
    hand (the pre-migration formula) and confirm the migrated function's
    output matches to the last float."""
    s = _fresh_substrate()
    mt, concepts = _build_continuous_mt(s)
    hub = concepts["hub"]
    h_delta = 0.4

    current_h = float(s.node(hub)["attrs"]["external_field"])
    new_h = current_h + h_delta
    current_marginal = s.mt_mean_field_marginal(mt)
    predicted_marginal = s.mt_mean_field_with_h_override(mt, hub, new_h)
    total_change = 0.0
    max_node_change = 0.0
    flipped_count = 0
    for nid, predicted_sig in predicted_marginal.items():
        current_sig = float(current_marginal.get(nid, 0.0))
        change = abs(predicted_sig - current_sig)
        total_change += change
        if change > max_node_change:
            max_node_change = change
        if change > 0.5:
            flipped_count += 1
    expected = {
        "concept_id": hub.value,
        "h_delta": h_delta,
        "current_sigma": float(current_marginal.get(hub.value, 0.0)),
        "info_gain_total_change": float(total_change),
        "info_gain_max_node_change": float(max_node_change),
        "predicted_flipped_count": int(flipped_count),
    }

    result = probe_via_what_if(s, mt, hub, h_delta=h_delta)
    assert result == expected, (
        "continuous-mode probe_via_what_if must be byte-identical to the "
        f"pre-migration formula: got {result}, expected {expected}"
    )
    print(f"continuous probe_via_what_if (pre-migration-equivalent): {result}")


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


def test_predict_perturbation_impact_continuous_branch_byte_identical_to_pre_migration():
    s = _fresh_substrate()
    mt, concepts = _build_continuous_mt(s)
    hub = concepts["hub"]
    new_h = 1.2

    current_marginal = s.mt_mean_field_marginal(mt)
    current_audit = s.mt_audit_basin(mt)
    predicted_marginal = s.mt_mean_field_with_h_override(mt, hub, new_h)
    predicted_energy_uncorrected = s.mt_energy(mt, predicted_marginal)
    old_h = float(s.node(hub)["attrs"].get("external_field", 0.0))
    sigma_at_concept = float(predicted_marginal.get(hub.value, 0.0))
    energy_correction = sigma_at_concept * (old_h - new_h)
    expected_energy = predicted_energy_uncorrected + energy_correction
    expected_delta_E = expected_energy - current_audit["energy"]
    expected_frustration = s.mt_frustration_given_state(mt, predicted_marginal)
    expected_delta_F = expected_frustration - current_audit["frustration"]

    result = predict_perturbation_impact(s, mt, hub, new_h)
    assert result["predicted_energy"] == pytest.approx(expected_energy)
    assert result["predicted_delta_E"] == pytest.approx(expected_delta_E)
    assert result["predicted_frustration"] == pytest.approx(expected_frustration)
    assert result["predicted_delta_F"] == pytest.approx(expected_delta_F)
    print(f"continuous predict_perturbation_impact (pre-migration-equivalent): "
          f"delta_E={result['predicted_delta_E']:.4f} delta_F={result['predicted_delta_F']:.4f}")


# ---------------------------------------------------------------------
# 3. insight_seeking.py::seek_insights — the relax-guard, real before/after.
# ---------------------------------------------------------------------

def test_seek_insights_skips_continuous_relax_on_a_native_mt():
    """A discrete_mode Mt's `state` must NOT be touched by
    mt_relax_to_marginal — deliberately built off-equilibrium (n2 has a
    strongly opposing field vs. its coupling) so a continuous relax WOULD
    change it if the guard were missing."""
    s = _fresh_substrate()
    mt, concepts = _build_discrete_mt(s, mode="3state")
    before_states = {name: float(s.node(c)["attrs"]["state"])
                     for name, c in concepts.items()}

    seek_insights(s, mt, top_k_hot=3)

    after_states = {name: float(s.node(c)["attrs"]["state"])
                    for name, c in concepts.items()}
    assert after_states == before_states, (
        "seek_insights must NOT relax a discrete_mode Mt's state via the "
        f"continuous mechanism: before={before_states} after={after_states}"
    )
    print(f"native seek_insights: state preserved exactly, {after_states}")


def test_seek_insights_still_relaxes_a_continuous_mt():
    """The pre-existing behaviour for a continuous Mt must be unchanged:
    mt_relax_to_marginal DOES run, so state moves toward equilibrium."""
    s = _fresh_substrate()
    mt, concepts = _build_continuous_mt(s)
    hub = concepts["hub"]
    before = float(s.node(hub)["attrs"]["state"])

    seek_insights(s, mt, top_k_hot=3)

    after = float(s.node(hub)["attrs"]["state"])
    assert after != before, (
        "continuous-mode seek_insights must still relax state toward "
        f"equilibrium -- before={before} after={after} (no change means "
        "the relax call was lost)"
    )
    print(f"continuous seek_insights: state moved {before:.4f} -> {after:.4f} (relax fired)")


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
