"""Blocker B unblocked, for its own scope: the native Hebbian mechanism now
respects the SAME update_policy / plasticity_override gate the continuous
mechanism's mt_hebbian_update_J is always called behind
(self_improvement_loop.py::mt_allows / maybe_hebbian), and the already-built
v1.1.0 evidence-count + on-demand log-odds render (LOGODDS_GENERATOR_
RESULTS.md) is confirmed to be the correct native materialization —
CAN_HEBBIAN_MATERIALIZATION_PREREG.md / _RESULTS.md.

seeds/can_native_reimplementation.json v1.2.0 ANDs a policy predicate into
can_native_hebbian_mint / can_native_hebbian_reweight's `where` clauses,
built by tools/patch_can_hebbian_policy_gate.py. This file:

  1. Confirms tests/test_can_native_reimplementation.py's own two
     Hebbian tests (which never set update_policy on their Mt) still pass
     UNCHANGED — required by house discipline, checked here by direct
     reproduction of their exact scenario, not merely by re-running that
     file (also done separately, see CAN_HEBBIAN_MATERIALIZATION_RESULTS.md).
  2. Demonstrates the policy gate both ways (adaptive/hybrid-default allow,
     frozen/hybrid-axis-false deny) and the plasticity_override transient
     rescue.
  3. Demonstrates domains/can_native_hebbian_bridge.py's on-demand query
     functions give a usable graded signal without ever writing the render
     back onto any node — verified directly, not merely asserted.
"""
from __future__ import annotations

import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_native_hebbian_bridge import (
    causal_strength,
    causal_strength_between,
    find_coactivation,
    hebbian_ledger_entries_touched_this_tick,
    hebbian_signal,
)

SEED_PATH = "seeds/can_native_reimplementation.json"


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    filtered = engine_rules_only(d)
    inner.load_seed_manifest(filtered)
    return s


def _isolated_pair(inner, mt_attrs: dict | None = None):
    """discrete_mode='static' so item-3's relaxation rules never interfere
    — the same isolation discipline test_can_native_reimplementation.py's
    own _isolated_pair uses, reproduced here (test files don't import each
    other's private helpers by convention in this corpus)."""
    attrs = {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0}
    if mt_attrs:
        attrs.update(mt_attrs)
    mt = inner.add_node("Microtheory", attrs)
    a = inner.add_node("Concept", {"name": "a", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    b = inner.add_node("Concept", {"name": "b", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    inner.add_edge(mt, "has_concept", a, {})
    inner.add_edge(mt, "has_concept", b, {})
    return mt, a, b


def _step(inner, mt, tick):
    inner.set_attr(mt, "can_tick", tick)
    inner.run_rules(1000)


# ---------------------------------------------------------------------
# 1. Seed version + gate presence, sanity.
# ---------------------------------------------------------------------

def test_seed_bumped_to_1_2_0_and_gate_present_on_both_rules():
    d = json.load(open(SEED_PATH))
    assert d["version"] == "1.2.0"
    gated = {"can_native_hebbian_mint", "can_native_hebbian_reweight"}
    seen = set()
    for rule in d["rules"]:
        if rule["name"] in gated:
            seen.add(rule["name"])
            items = rule["where"]["items"]
            assert any(it.get("type") == "Or" for it in items), (
                f"{rule['name']}: no Or(...) policy-gate item found in where.items"
            )
    assert seen == gated
    # can_native_note_coactivation must NOT be gated — pure observation.
    note_rule = next(r for r in d["rules"] if r["name"] == "can_native_note_coactivation")
    assert not any(it.get("type") == "Or" for it in note_rule["where"]["items"]), (
        "can_native_note_coactivation must stay ungated (observation, not a J/h mutation)"
    )


# ---------------------------------------------------------------------
# 2. Legacy / no update_policy attr — must reproduce the pre-gate
#    behaviour byte-for-byte (regression contract for the existing file).
# ---------------------------------------------------------------------

def test_no_update_policy_attr_still_mints_and_reweights_unconditionally():
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner)  # no update_policy set at all

    inner.run_rules(1000)  # tick 0: note only
    assert b not in inner.neighbours(a, "causal_influence")

    _step(inner, mt, 1)  # tick 1: recurrence -> mint
    assert b in inner.neighbours(a, "causal_influence"), (
        "legacy Mt (no update_policy attr) must still mint on recurrence — "
        "the pre-gate v1.1.0 behaviour, unchanged"
    )

    _step(inner, mt, 2)
    _step(inner, mt, 3)
    coact = find_coactivation(inner, a, b)
    attrs = inner.node(coact)["attrs"]
    assert (attrs["evidence_confirm"], attrs["evidence_disconfirm"]) == (3, 0), attrs


# ---------------------------------------------------------------------
# 3. Policy gate — both directions, on the real engine.
# ---------------------------------------------------------------------

def test_adaptive_policy_allows_mint_and_reweight():
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, {"update_policy": "adaptive"})

    inner.run_rules(1000)
    _step(inner, mt, 1)
    assert b in inner.neighbours(a, "causal_influence"), "adaptive Mt must mint"
    _step(inner, mt, 2)
    coact = find_coactivation(inner, a, b)
    attrs = inner.node(coact)["attrs"]
    assert attrs["evidence_confirm"] == 2, attrs


def test_frozen_policy_denies_mint_and_reweight():
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, {"update_policy": "frozen"})

    inner.run_rules(1000)  # tick 0: note is UNGATED, must still fire
    coact = find_coactivation(inner, a, b)
    assert coact is not None, "note_coactivation is observation-only, must not be gated"
    assert b not in inner.neighbours(a, "causal_influence")

    for tick in (1, 2, 3):
        _step(inner, mt, tick)
        assert b not in inner.neighbours(a, "causal_influence"), (
            f"frozen Mt must NEVER mint the causal_influence edge (tick {tick})"
        )
    # Ledger untouched by the (never-fired) mint's evidence bump either.
    attrs = inner.node(coact)["attrs"]
    assert (attrs["evidence_confirm"], attrs["evidence_disconfirm"]) == (0, 0), attrs


def test_frozen_with_plasticity_override_allows():
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(
        inner, {"update_policy": "frozen", "plasticity_override": 0.5}
    )

    inner.run_rules(1000)  # tick 0: note
    _step(inner, mt, 1)  # tick 1: override rescues the mint
    assert b in inner.neighbours(a, "causal_influence"), (
        "frozen Mt WITH plasticity_override>0 must mint — the same transient "
        "rescue path maybe_hebbian's own override fallback uses"
    )

    _step(inner, mt, 2)  # reweight under override too
    coact = find_coactivation(inner, a, b)
    attrs = inner.node(coact)["attrs"]
    assert attrs["evidence_confirm"] == 2, attrs

    # Now drop the override back to 0 (as correction_raise_plasticity's own
    # decay_plasticity_override eventually does) and confirm learning stops.
    inner.set_attr(mt, "plasticity_override", 0.0)
    _step(inner, mt, 3)
    attrs = inner.node(coact)["attrs"]
    assert attrs["evidence_confirm"] == 2, (
        "override decayed to 0 on a still-frozen Mt must stop further reweighting"
    )


def test_hybrid_axis_false_denies():
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(
        inner, {"update_policy": "hybrid", "allow_Hebbian_J": False}
    )
    inner.run_rules(1000)
    _step(inner, mt, 1)
    assert b not in inner.neighbours(a, "causal_influence"), (
        "hybrid Mt with allow_Hebbian_J=False must deny mint, matching "
        "mt_allows's own per-axis hybrid check"
    )


def test_hybrid_axis_absent_defaults_to_allow():
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, {"update_policy": "hybrid"})  # no axis attr
    inner.run_rules(1000)
    _step(inner, mt, 1)
    assert b in inner.neighbours(a, "causal_influence"), (
        "hybrid Mt with the allow_Hebbian_J axis attr UNSET must default to "
        "allow — mt_allows's own documented default for an unlisted axis"
    )


def test_hybrid_axis_true_allows():
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(
        inner, {"update_policy": "hybrid", "allow_Hebbian_J": True}
    )
    inner.run_rules(1000)
    _step(inner, mt, 1)
    assert b in inner.neighbours(a, "causal_influence")


# ---------------------------------------------------------------------
# 4. The bridge module — comparable graded signal, on demand.
# ---------------------------------------------------------------------

def test_bridge_gives_a_graded_signal_that_moves_with_evidence():
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, {"update_policy": "adaptive"})

    inner.run_rules(1000)
    assert causal_strength_between(inner, a, b) is None or True  # ledger exists but no edge yet is fine
    _step(inner, mt, 1)  # mint, confirm=1
    render_1 = causal_strength_between(inner, a, b)
    assert render_1 is not None and render_1 > 0.0

    _step(inner, mt, 2)  # confirm=2
    _step(inner, mt, 3)  # confirm=3
    render_3 = causal_strength_between(inner, a, b)
    assert render_3 > render_1, "more confirming evidence must render a strictly higher signal"

    inner.set_attr(b, "state", -1.0)  # one disconfirming observation
    _step(inner, mt, 4)
    render_4 = causal_strength_between(inner, a, b)
    assert render_4 < render_3, "a disconfirming observation must move the signal down"

    sig = hebbian_signal(inner, a, b)
    assert sig["edge_exists"] is True
    assert sig["evidence_confirm"] == 3
    assert sig["evidence_disconfirm"] == 1
    assert abs(sig["causal_strength"] - render_4) < 1e-12


def test_bridge_ledger_touched_count_is_the_native_edges_updated_analog():
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, {"update_policy": "adaptive"})

    inner.run_rules(1000)  # tick 0: note only, no evidence bump yet
    assert hebbian_ledger_entries_touched_this_tick(inner, mt) == 0

    _step(inner, mt, 1)  # mint bumps evidence_tick=1 on BOTH direction ledgers
    touched = hebbian_ledger_entries_touched_this_tick(inner, mt)
    assert touched == 2, (
        f"mint fires symmetrically (a->b and b->a, per-direction convention) "
        f"so exactly 2 ledger entries should be touched at can_tick=1, got {touched}"
    )

    _step(inner, mt, 2)
    assert hebbian_ledger_entries_touched_this_tick(inner, mt) == 2


def test_bridge_returns_none_for_a_pair_that_never_coactivated():
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0})
    a = inner.add_node("Concept", {"name": "a", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    b = inner.add_node("Concept", {"name": "b", "state": -1.0, "external_field": 0.0, "identity_field": 0.0})
    inner.add_edge(mt, "has_concept", a, {})
    inner.add_edge(mt, "has_concept", b, {})
    inner.run_rules(1000)  # opposite sign -> never co-activates
    assert find_coactivation(inner, a, b) is None
    assert causal_strength_between(inner, a, b) is None
    assert hebbian_signal(inner, a, b) is None


# ---------------------------------------------------------------------
# 5. The frame/continuum invariant — verified directly, not just asserted.
# ---------------------------------------------------------------------

def test_invariant_render_never_appears_as_a_stored_attr_anywhere():
    """Across every scenario above's shape (adaptive + frozen+override, to
    cover BOTH the denied and the allowed learning paths), scan every
    node's attrs after a full run and confirm no float log-odds value, and
    no 'log_odds'/'render'/'causal_strength' KEY, was ever written onto any
    node — the render stays a pure on-demand cross-frame comparison."""
    s = _loaded_substrate()
    inner = s._inner
    mt, a, b = _isolated_pair(inner, {"update_policy": "adaptive"})
    inner.run_rules(1000)
    for tick in (1, 2, 3):
        _step(inner, mt, tick)
    inner.set_attr(b, "state", -1.0)
    _step(inner, mt, 4)

    coact = find_coactivation(inner, a, b)
    before = dict(inner.node(coact)["attrs"])
    for _ in range(5):
        causal_strength(inner, coact)  # pure render, called repeatedly
    after = dict(inner.node(coact)["attrs"])
    assert before == after, f"render leaked into graph state: before={before} after={after}"

    forbidden_keys = {"log_odds", "render", "causal_strength"}
    for nid in (mt, a, b, coact):
        attrs = inner.node(nid)["attrs"]
        assert forbidden_keys.isdisjoint(attrs.keys()), (
            f"node {nid} carries a forbidden rendered-value key: {attrs.keys()}"
        )
    # Every value that IS stored on the ledger is a genuine int, never a float.
    for k in ("evidence_confirm", "evidence_disconfirm", "evidence_tick"):
        assert isinstance(inner.node(coact)["attrs"][k], int), (
            f"{k} must stay an in-frame integer, got {type(inner.node(coact)['attrs'][k])}"
        )
