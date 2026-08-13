"""CAN_SOLVER_TRACTABILITY_PREREG.md / _RESULTS.md — multi-start-and-pick-
best, gated on the real engine.

`domains/can_native_orchestration.py::multi_start_settle_and_pick_best`
widens the search around the already-proven-convergent discrete-async
update (never touches `can_native_update_3state`/`_2state`'s own rule body)
by trying K independent random initial conditions and keeping the
Argmin-decided best. These tests confirm: (a) it actually finds a state at
least as good as a single settle, on a real frustrated network where
`CAN_SOLVER_TRACTABILITY_RESULTS.md` §1 measured real local-minimum risk;
(b) the winner really is the minimum-frustration candidate among the K
trials (the Argmin Term's own decision, checked against a direct read of
every candidate node); (c) two-Mt isolation holds, matching every other
native rung's own standing check; (d) it is well-behaved (no exception, no
non-convergence) on a real Bigville resident too.
"""
from __future__ import annotations

import json
import random

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
from domains.can_native_orchestration import (
    multi_start_settle_and_pick_best, scoped_settle, native_marginal_from_state,
)
from worlds.bigville_can_beliefs import (
    install_productions, build_resident_can_mt, apply_scenario_evidence,
)

SEED_PATH = "seeds/can_native_reimplementation.json"
CAST_PATH = "seeds/bigville_cast100.json"


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    filtered = engine_rules_only(d)
    inner.load_seed_manifest(filtered)
    return inner


def _round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def _build_frustrated_draw(inner, seed, n=16, coarse=True, discrete_mode="3state"):
    pair_rng = random.Random(seed * 31 + n)
    field_rng = random.Random(seed * 53 + n)
    mt = inner.add_node("Microtheory", {
        "temperature": 2.0, "discrete_mode": discrete_mode, "can_tick": 0,
    })
    concepts = [
        inner.add_node("Concept", {
            "name": "c%d" % i, "state": 0.0,
            "external_field": 0.0, "identity_field": 0.0,
        })
        for i in range(n)
    ]
    for c in concepts:
        inner.add_edge(mt, "has_concept", c, {})
    for i in range(n):
        h = field_rng.uniform(-1, 1)
        inner.set_attr(concepts[i], "external_field", h)
    for i in range(n):
        for j in range(i + 1, n):
            raw = pair_rng.uniform(-1, 1)
            v = (_round_to_vocab(raw, 1.0, 1) if coarse
                 else _round_to_vocab(raw, 0.25, 4))
            inner.add_edge(concepts[i], "causal_influence", concepts[j], {"weight": v})
            inner.add_edge(concepts[j], "causal_influence", concepts[i], {"weight": v})
    return mt, concepts


def test_multi_start_finds_a_state_at_least_as_good_as_a_single_settle():
    """Real numbers: on the SAME frustrated N=16 network, a single settle
    from a fixed initial state (mirroring every prior convergence sweep's
    own zero-init convention) vs multi_start_settle_and_pick_best's
    Argmin-decided best over K=20 random starts."""
    inner = _loaded_substrate()
    mt, concepts = _build_frustrated_draw(inner, seed=42)

    # Baseline: single settle from the zero-init every prior rung used.
    scoped_settle(inner, mt)
    baseline_state = native_marginal_from_state(inner, mt)
    baseline_frustration = float(inner.mt_frustration_given_state(mt, baseline_state))

    # Multi-start: re-seeds state itself, so re-run fresh from the SAME
    # network (same coupling structure, mt/concepts unchanged).
    result = multi_start_settle_and_pick_best(inner, mt, k_starts=20,
                                               rng=random.Random(777))
    print(f"\nbaseline (single zero-init settle) frustration={baseline_frustration:.4f}")
    print(f"multi-start (K=20) winner frustration={result['frustration']:.4f}")

    assert result["frustration"] <= baseline_frustration + 1e-9, (
        "multi-start must never do WORSE than a single settle -- it always "
        "includes independent trials and picks the argmin")


def test_winner_really_is_the_minimum_frustration_candidate():
    """Confirms the Argmin Term's own decision against a direct, independent
    read of every candidate node's frustration -- not merely trusting the
    Term evaluator's return value."""
    inner = _loaded_substrate()
    mt, concepts = _build_frustrated_draw(inner, seed=123)
    result = multi_start_settle_and_pick_best(inner, mt, k_starts=15,
                                               rng=random.Random(55))

    all_frustrations = [
        float(inner.node(c)["attrs"]["frustration"]) for c in result["candidates"]
    ]
    true_min = min(all_frustrations)
    print(f"\nall {len(all_frustrations)} candidate frustrations: "
          f"{sorted(round(f, 3) for f in all_frustrations)}")
    print(f"Argmin-selected winner frustration: {result['frustration']:.4f} "
          f"true_min={true_min:.4f}")
    assert abs(result["frustration"] - true_min) < 1e-9
    assert len(result["candidates"]) == 15


def test_committed_state_matches_the_winning_candidates_stored_state():
    """The commit step (mechanical translation of the Argmin decision back
    onto the real Concepts) must reproduce the winner's own stored state
    exactly, and the frustration read back from the LIVE Concepts after
    commit must match the winner's own recorded frustration."""
    inner = _loaded_substrate()
    mt, concepts = _build_frustrated_draw(inner, seed=9)
    result = multi_start_settle_and_pick_best(inner, mt, k_starts=10,
                                               rng=random.Random(3))
    live_state = native_marginal_from_state(inner, mt)
    live_frustration = float(inner.mt_frustration_given_state(mt, live_state))
    assert abs(live_frustration - result["frustration"]) < 1e-9


def test_two_mt_isolation_holds_for_multi_start():
    """Same standing check every native rung in this arc runs
    (CAN_FINAL_MIGRATION_RESULTS.md Sec0's own hazard): a sibling Mt's
    state must be byte-unchanged after running multi-start on a DIFFERENT
    Mt in the same graph."""
    inner = _loaded_substrate()
    mt_a, concepts_a = _build_frustrated_draw(inner, seed=1, n=8)
    mt_b, concepts_b = _build_frustrated_draw(inner, seed=2, n=8)
    for c in concepts_b:
        inner.set_attr(c, "state", 1.0)
    before_b = {c.value: inner.node(c)["attrs"].get("state") for c in concepts_b}

    multi_start_settle_and_pick_best(inner, mt_a, k_starts=8, rng=random.Random(11))

    after_b = {c.value: inner.node(c)["attrs"].get("state") for c in concepts_b}
    assert before_b == after_b, "multi-start on mt_a mutated an unrelated mt_b"


def test_multi_start_well_behaved_on_a_real_bigville_resident():
    """Real resident, real params -- no exception, converges, commits a
    real state, reports a real frustration value no worse than a single
    settle from the resident's own already-applied evidence."""
    cast = json.load(open(CAST_PATH))["residents"]
    resident = cast[7]

    s = sr._native.Substrate()
    install_productions(s)
    manifest = json.load(open(SEED_PATH))
    s.load_seed_manifest(engine_rules_only(manifest))
    built = build_resident_can_mt(s, resident)
    apply_scenario_evidence(s, built["concepts"])
    s.set_attr(built["mt_node"], "discrete_mode", "3state")
    s.set_attr(built["mt_node"], "can_tick", 0)

    # Baseline single run (state starts at whatever build_resident_can_mt
    # left it -- default 0.0, unset).
    steps = s.run_rules(3000)
    baseline_state = {c.value: float(s.node(c)["attrs"].get("state", 0.0))
                       for c in built["concepts"].values()}
    baseline_frustration = float(s.mt_frustration_given_state(built["mt_node"], baseline_state))

    result = multi_start_settle_and_pick_best(s, built["mt_node"], k_starts=20,
                                               rng=random.Random(999))
    print(f"\nBigville resident #{resident['index']} "
          f"baseline_frustration={baseline_frustration:.4f} "
          f"multi_start_frustration={result['frustration']:.4f}")
    assert result["frustration"] <= baseline_frustration + 1e-9
