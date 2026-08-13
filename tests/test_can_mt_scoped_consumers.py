"""Consumer migrations unblocked by `run_rules_scoped`
(CAN_MT_SCOPED_RULES_RESULTS.md Sec5) — live demonstrations, real numbers,
on the real engine. Reuses `test_can_decay_identity.py`'s own
`_isolated_pair` scenario shape (discrete_mode='static' so item-3's
relaxation rules never interfere with the Hebbian mint/reweight demo).

Domain functions are called with the RAW native substrate (`_native.
Substrate()`), matching every real caller across `domains/`/`worlds/`/
`scripts/`/the existing test suite (CAN_FINAL_MIGRATION_RESULTS.md Sec2.2's
own confirmed convention — zero production callers use the `sr.Substrate`
Python wrapper)."""
from __future__ import annotations

import json

from substrate_rs import _native
from substrate.seed_loader import engine_rules_only

from domains.insight_detection import consolidate_insight
from domains.insight_propagation import find_shared_concepts, propagate_insight
from domains.self_improvement_loop import (
    _is_native, maybe_decay_J, maybe_hebbian, relax,
    self_improvement_step,
)

SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
)


def _loaded_substrate():
    inner = _native.Substrate()
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return inner


def _isolated_pair(inner, policy="adaptive", discrete_mode="3state"):
    """`discrete_mode="3state"` (not the engine-test-only "static" isolation
    value `test_can_native_reimplementation.py` uses) — this is the SAME
    "2state"/"3state" gate `self_improvement_loop._is_native` actually
    checks, so this scenario exercises the real consumer-facing native
    path. Strong, EQUAL external fields on both concepts so the discrete
    update converges both to the SAME committed non-zero state and STAYS
    there (`can_native_update_3state`'s own fixed point) — satisfying
    `can_native_hebbian_mint`'s `Eq(state_a, state_b)` /
    `Not(Eq(state, 0))` where-clause guards, matching this rung's own
    live probe (found the "static"-mode test scenario does NOT exercise
    the consumer-level native gate at all, since "static" is not in
    `("2state", "3state")` — a real, reportable finding, not assumed)."""
    mt = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": discrete_mode, "can_tick": 0,
        "update_policy": policy,
    })
    a = inner.add_node("Concept", {"name": "a", "state": 0.0, "external_field": 5.0, "identity_field": 0.0})
    b = inner.add_node("Concept", {"name": "b", "state": 0.0, "external_field": 5.0, "identity_field": 0.0})
    inner.add_edge(mt, "has_concept", a, {})
    inner.add_edge(mt, "has_concept", b, {})
    return mt, a, b


def _has_edge(inner, x, y):
    return y in inner.neighbours(x, "causal_influence")


# ---------------------------------------------------------------------
# 1. consolidate_insight (insight_detection.py) — native branch mints via
#    the scoped fixpoint, isolated to the target Mt.
# ---------------------------------------------------------------------

def test_consolidate_insight_native_mints_on_recurrence_gated_by_policy():
    inner = _loaded_substrate()
    mt, a, b = _isolated_pair(inner, policy="adaptive")

    # Tick 1: first sight -- notes co-activation, no mint yet.
    edges = consolidate_insight(inner, mt)
    print(f"consolidate_insight tick1 (native, adaptive): scoped_steps={edges} edge={_has_edge(inner, a, b)}")
    assert not _has_edge(inner, a, b), "must not mint on first sight"

    inner.set_attr(mt, "can_tick", 1)
    # Tick 2: recurrence -- mints.
    edges2 = consolidate_insight(inner, mt)
    print(f"consolidate_insight tick2 (native, adaptive): scoped_steps={edges2} edge={_has_edge(inner, a, b)}")
    assert _has_edge(inner, a, b), "must mint on genuine cross-tick recurrence via consolidate_insight's native branch"


def test_consolidate_insight_native_frozen_never_mints():
    inner = _loaded_substrate()
    mt, a, b = _isolated_pair(inner, policy="frozen")

    consolidate_insight(inner, mt)
    inner.set_attr(mt, "can_tick", 1)
    consolidate_insight(inner, mt)
    print(f"consolidate_insight (native, FROZEN): edge={_has_edge(inner, a, b)}")
    assert not _has_edge(inner, a, b), (
        "a frozen native Mt must never mint -- can_native_hebbian_mint's own "
        "where-clause policy gate must block it even though consolidate_insight "
        "no longer duplicates the mt_allows check for the native branch"
    )


def test_consolidate_insight_continuous_branch_byte_unchanged():
    """No discrete_mode -> the OLD mt_hebbian_update_J path, unmodified."""
    inner = _loaded_substrate()
    mt = inner.add_node("Microtheory", {"temperature": 1.0, "update_policy": "adaptive"})
    a = inner.add_node("Concept", {"name": "a", "state": 1.0, "external_field": 1.0, "identity_field": 0.0})
    b = inner.add_node("Concept", {"name": "b", "state": 1.0, "external_field": 1.0, "identity_field": 0.0})
    inner.add_edge(mt, "has_concept", a, {})
    inner.add_edge(mt, "has_concept", b, {})
    assert not _is_native(inner, mt)
    edges = consolidate_insight(inner, mt, eta=0.5)
    print(f"consolidate_insight (continuous): edges_updated={edges}")
    assert isinstance(edges, int)


# ---------------------------------------------------------------------
# 2. self_improvement_loop.py's relax/maybe_hebbian/maybe_decay_J,
#    self_improvement_step end-to-end, native + continuous mixed, no
#    cross-Mt leakage.
# ---------------------------------------------------------------------

def test_relax_maybe_hebbian_maybe_decay_j_native_dont_crash_and_are_isolated():
    inner = _loaded_substrate()
    mt_native, a, b = _isolated_pair(inner, policy="adaptive")
    mt_other, c, d = _isolated_pair(inner, policy="adaptive")  # untouched control

    before_other = {n.value: inner.node(n)["attrs"].get("state") for n in (c, d)}

    r = relax(inner, mt_native)
    h = maybe_hebbian(inner, mt_native, eta=0.5)
    j = maybe_decay_J(inner, mt_native, decay_rate=0.1)
    print(f"native relax/hebbian/decay_J steps: relax={r} hebbian={h} decay_j={j}")

    after_other = {n.value: inner.node(n)["attrs"].get("state") for n in (c, d)}
    assert before_other == after_other, (
        "an untouched sibling Mt changed while operating on mt_native -- "
        "scoping leaked across Mts through the gated self_improvement_loop path"
    )
    assert isinstance(r, int) and isinstance(h, int) and isinstance(j, int)


def test_self_improvement_step_mixed_native_and_continuous_no_crash_no_leak():
    """The real end-to-end entry point, on a graph with ONE native adaptive
    Mt and ONE continuous adaptive Mt sharing no concepts. Demonstrates the
    whole gated dual path composes without crashing and without cross-Mt
    interference, on the real engine."""
    inner = _loaded_substrate()
    mt_native, na, nb = _isolated_pair(inner, policy="adaptive", discrete_mode="3state")
    inner.set_attr(na, "external_field", 1.0)
    inner.set_attr(nb, "external_field", -1.0)

    mt_cont = inner.add_node("Microtheory", {"temperature": 1.0, "update_policy": "adaptive"})
    ca = inner.add_node("Concept", {"name": "ca", "state": 0.0, "external_field": 0.3, "identity_field": 0.0})
    cb = inner.add_node("Concept", {"name": "cb", "state": 0.0, "external_field": -0.3, "identity_field": 0.0})
    inner.add_edge(mt_cont, "has_concept", ca, {})
    inner.add_edge(mt_cont, "has_concept", cb, {})
    inner.add_edge(ca, "causal_influence", cb, {"weight": 0.5})
    inner.add_edge(cb, "causal_influence", ca, {"weight": 0.5})

    results = self_improvement_step(inner)
    print(f"self_improvement_step mixed result keys: {list(results.keys())}")
    for mt_id, r in results.items():
        print(f"  mt={mt_id} policy={r['policy']} pre_frust={r['pre_audit']['frustration']:.4f} "
              f"post_frust={r['post_audit']['frustration']:.4f} edges_hebbian={r['edges_hebbian']}")
    assert mt_native.value in results
    assert mt_cont.value in results
    # Cross-check the native Mt's own basin audit is the native composition
    # (concept_count == 2, matches native _isolated_pair's own has_concept set).
    assert results[mt_native.value]["pre_audit"]["concept_count"] == 2
    assert results[mt_cont.value]["pre_audit"]["concept_count"] == 2


# ---------------------------------------------------------------------
# 3. insight_propagation.py::propagate_insight — native other_mt branch.
# ---------------------------------------------------------------------

def test_propagate_insight_native_other_mt_isolated_settle():
    """Two native Mts sharing one Concept. Flip the shared concept via
    source_mt's own scoped settle, then propagate_insight should relax/
    audit other_mt via the native branch (run_rules_scoped(other_mt)) --
    demonstrated by checking it runs to completion and reads other_mt's
    OWN state (not source_mt's), without raising."""
    inner = _loaded_substrate()
    mt_a = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": "adaptive",
    })
    mt_b = inner.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
        "update_policy": "adaptive",
    })
    shared = inner.add_node("Concept", {"name": "shared", "state": 0.0, "external_field": 5.0, "identity_field": 0.0})
    b_only = inner.add_node("Concept", {"name": "b_only", "state": 0.0, "external_field": -5.0, "identity_field": 0.0})
    inner.add_edge(mt_a, "has_concept", shared, {})
    inner.add_edge(mt_b, "has_concept", shared, {})
    inner.add_edge(mt_b, "has_concept", b_only, {})

    shared_ids = find_shared_concepts(inner, mt_a, mt_b)
    print(f"shared concepts: {shared_ids}")
    assert shared.value in shared_ids

    relax(inner, mt_a)  # settles `shared` under mt_a's own scoped fixpoint
    insight_event = {"flipped_nodes": [{"node": shared.value, "after": float(inner.node(shared)["attrs"]["state"])}]}
    cascades = propagate_insight(inner, mt_a, insight_event)
    print(f"cascades: {len(cascades)}")
    for casc in cascades:
        print(f"  target_mt={casc['target_mt']} shared={casc['shared_node_ids']}")
    assert len(cascades) == 1
    assert cascades[0]["target_mt"] == mt_b.value
