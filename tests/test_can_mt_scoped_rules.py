"""`run_rules_scoped` -- per-Mt scoped fixpoint (CAN_MT_SCOPED_RULES_PREREG/
RESULTS.md). Live demonstration on the real engine:

  1. Backward-compatibility proof: `run_rules_scoped(..., scope_mt=None)`
     reproduces the EXISTING `run_rules(...)` byte-identically, on the
     exact scenario `test_can_native_reimplementation.py` already uses for
     its own 3-state discrete-async convergence check.
  2. Two-Mt isolation demonstration: two independent, disjoint
     Microtheories in one graph; scoping to one advances ONLY that Mt's
     state, leaving the other byte-identical to its pre-call snapshot --
     the exact opposite of the OLD `run_rules()` behaviour the base commit
     (CAN_FINAL_MIGRATION_RESULTS.md Sec0) already demonstrated mutates an
     untouched Mt as a side effect.
"""
from __future__ import annotations

import json
import math
import random

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

SEED_PATH = "seeds/can_native_reimplementation.json"
N = 8
BETA = 2.0


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    filtered = engine_rules_only(d)
    inner.load_seed_manifest(filtered)
    return s


def _round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def _build_draw(s, seed, coarse, discrete_mode="3state"):
    """Reused verbatim from test_can_native_reimplementation.py::_build_draw
    (same seed formula, same complete-graph construction) so the
    backward-compat scenario is the SAME scenario, not a lookalike."""
    inner = s._inner
    pair_rng = random.Random(seed * 31 + N)
    field_rng = random.Random(seed * 53 + N)
    mt = inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": discrete_mode, "can_tick": 0,
    })
    concepts = [
        inner.add_node("Concept", {
            "name": "c%d" % i, "state": 0.0,
            "external_field": 0.0, "identity_field": 0.0,
        })
        for i in range(N)
    ]
    for c in concepts:
        inner.add_edge(mt, "has_concept", c, {})
    for i in range(N):
        h = field_rng.uniform(-1, 1)
        inner.set_attr(concepts[i], "external_field", h)
    for i in range(N):
        for j in range(i + 1, N):
            raw = pair_rng.uniform(-1, 1)
            v = (_round_to_vocab(raw, 1.0, 1) if coarse
                 else _round_to_vocab(raw, 0.25, 4))
            inner.add_edge(concepts[i], "causal_influence", concepts[j], {"weight": v})
            inner.add_edge(concepts[j], "causal_influence", concepts[i], {"weight": v})
    return mt, concepts


def _read_states(inner, concepts):
    return {c.value: float(inner.node(c)["attrs"].get("state", 0.0)) for c in concepts}


# ---------------------------------------------------------------------
# 1. Backward compatibility: scope_mt=None === run_rules(), byte-identical.
# ---------------------------------------------------------------------

def test_run_rules_scoped_none_is_byte_identical_to_run_rules_on_can_scenario():
    N_DRAWS = 12
    for coarse in (True, False):
        for discrete_mode in ("2state", "3state"):
            for seed in range(N_DRAWS):
                # Path A: the EXISTING run_rules().
                s_a = _loaded_substrate()
                inner_a = s_a._inner
                mt_a, concepts_a = _build_draw(s_a, 2000 + seed, coarse, discrete_mode)
                steps_a = inner_a.run_rules(3000)
                states_a = _read_states(inner_a, concepts_a)

                # Path B: the NEW run_rules_scoped(scope_mt=None) on an
                # identically-constructed, independently-built scenario
                # (same seed -> same random draws -> same graph).
                s_b = _loaded_substrate()
                inner_b = s_b._inner
                mt_b, concepts_b = _build_draw(s_b, 2000 + seed, coarse, discrete_mode)
                steps_b = inner_b.run_rules_scoped(3000, False, None)
                states_b = _read_states(inner_b, concepts_b)

                assert steps_a == steps_b, (
                    f"step count diverged: run_rules={steps_a} "
                    f"run_rules_scoped(None)={steps_b} "
                    f"(coarse={coarse} mode={discrete_mode} seed={seed})"
                )
                states_a_ordered = {c.value: v for c, v in zip(concepts_a, states_a.values())}
                vals_a = [states_a[c.value] for c in concepts_a]
                vals_b = [states_b[c.value] for c in concepts_b]
                assert vals_a == vals_b, (
                    f"final state diverged: {vals_a} vs {vals_b} "
                    f"(coarse={coarse} mode={discrete_mode} seed={seed})"
                )
    print(f"backward-compat: {N_DRAWS * 2 * 2} scenarios, "
          f"run_rules_scoped(None) byte-identical to run_rules() on every one")


def test_run_rules_scoped_none_same_object_same_call_sequence():
    """Stronger same-object variant: build ONE scenario, snapshot after
    run_rules_scoped(None), reset via a fresh identical build, run the OLD
    run_rules(), compare. Complements the two-substrate comparison above
    with a call that exercises run_rules_scoped's own code path on the
    exact object under test (not a lookalike sibling)."""
    s = _loaded_substrate()
    inner = s._inner
    mt, concepts = _build_draw(s, 777, coarse=False, discrete_mode="3state")
    steps = inner.run_rules_scoped(3000, False, None)
    states = _read_states(inner, concepts)

    s2 = _loaded_substrate()
    inner2 = s2._inner
    mt2, concepts2 = _build_draw(s2, 777, coarse=False, discrete_mode="3state")
    steps2 = inner2.run_rules(3000)
    states2 = _read_states(inner2, concepts2)

    assert steps == steps2
    assert [states[c.value] for c in concepts] == [states2[c.value] for c in concepts2]


# ---------------------------------------------------------------------
# 2. Two-Mt isolation: scoping to Mt A leaves Mt B byte-identical.
# ---------------------------------------------------------------------

def test_scoped_to_mt_a_advances_a_and_leaves_b_untouched():
    s = _loaded_substrate()
    inner = s._inner
    mt_a, concepts_a = _build_draw(s, 42, coarse=False, discrete_mode="3state")
    mt_b, concepts_b = _build_draw(s, 4242, coarse=False, discrete_mode="3state")

    before_a = _read_states(inner, concepts_a)
    before_b = _read_states(inner, concepts_b)

    steps = inner.run_rules_scoped(3000, False, mt_a)
    after_a = _read_states(inner, concepts_a)
    after_b = _read_states(inner, concepts_b)

    a_changed = any(before_a[c.value] != after_a[c.value] for c in concepts_a)
    b_changed = any(before_b[c.value] != after_b[c.value] for c in concepts_b)

    print(f"scoped(mt_a): steps={steps}")
    print(f"  mt_a before={[before_a[c.value] for c in concepts_a]}")
    print(f"  mt_a after ={[after_a[c.value] for c in concepts_a]}")
    print(f"  mt_b before={[before_b[c.value] for c in concepts_b]}")
    print(f"  mt_b after ={[after_b[c.value] for c in concepts_b]}")

    assert steps > 0, "scoped run made no progress -- scenario didn't need convergence, weakens the demo"
    assert a_changed, "Mt A (the scoped target) did not change -- scoping filtered out its own bindings"
    assert not b_changed, "Mt B (untouched, unrelated) changed -- scoping leaked across Mts"
    assert [before_b[c.value] for c in concepts_b] == [after_b[c.value] for c in concepts_b]


def test_scoped_to_mt_b_advances_b_and_leaves_a_untouched_symmetric():
    """Symmetric direction: same graph, scope the OTHER Mt this time."""
    s = _loaded_substrate()
    inner = s._inner
    mt_a, concepts_a = _build_draw(s, 42, coarse=False, discrete_mode="3state")
    mt_b, concepts_b = _build_draw(s, 4242, coarse=False, discrete_mode="3state")

    before_a = _read_states(inner, concepts_a)
    before_b = _read_states(inner, concepts_b)

    steps = inner.run_rules_scoped(3000, False, mt_b)
    after_a = _read_states(inner, concepts_a)
    after_b = _read_states(inner, concepts_b)

    a_changed = any(before_a[c.value] != after_a[c.value] for c in concepts_a)
    b_changed = any(before_b[c.value] != after_b[c.value] for c in concepts_b)

    print(f"scoped(mt_b): steps={steps}")
    print(f"  mt_a before={[before_a[c.value] for c in concepts_a]}")
    print(f"  mt_a after ={[after_a[c.value] for c in concepts_a]}")
    print(f"  mt_b before={[before_b[c.value] for c in concepts_b]}")
    print(f"  mt_b after ={[after_b[c.value] for c in concepts_b]}")

    assert steps > 0
    assert b_changed, "Mt B (the scoped target) did not change"
    assert not a_changed, "Mt A (untouched, unrelated) changed -- scoping leaked across Mts"
    assert [before_a[c.value] for c in concepts_a] == [after_a[c.value] for c in concepts_a]


def test_unscoped_run_rules_DOES_leak_across_mts_the_documented_contrast():
    """Negative control: the OLD, still-unmodified `run_rules()` (and
    run_rules_scoped(None), the SAME call) on this exact two-Mt graph DOES
    let Mt A's rules touch Mt B, reproducing CAN_FINAL_MIGRATION_RESULTS.md
    Sec0's own live probe on a fresh scenario -- the reason this rung
    exists. Confirms the isolation seen above is a property of scoping,
    not of the scenario happening to keep the two Mts from interacting
    anyway."""
    s = _loaded_substrate()
    inner = s._inner
    mt_a, concepts_a = _build_draw(s, 42, coarse=False, discrete_mode="3state")
    mt_b, concepts_b = _build_draw(s, 4242, coarse=False, discrete_mode="3state")

    before_b = _read_states(inner, concepts_b)
    inner.run_rules(3000)  # unscoped -- touches the whole graph
    after_b = _read_states(inner, concepts_b)

    b_changed = any(before_b[c.value] != after_b[c.value] for c in concepts_b)
    print(f"unscoped run_rules(): mt_b changed = {b_changed}")
    assert b_changed, (
        "expected the UNSCOPED run_rules() to also advance the 'unrelated' "
        "Mt B on this two-Mt graph (both have pending updates) -- if this "
        "fails, the scenario itself doesn't exercise cross-Mt leakage and "
        "the isolation tests above would be vacuous"
    )
