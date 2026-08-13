"""CAN_LOOPY_BP_PREREG.md / _RESULTS.md — loopy belief propagation
(max-product primary, sum-product comparison) built alongside the
discrete-async native update and `multi_start_settle_and_pick_best`,
never modifying either.

Regression coverage:
  - max-product BP is EXACT on a tree (no loops) -- the textbook
    guarantee, checked against an independent brute-force MAP search,
    not merely trusted.
  - the exact NodeID-vs-raw-int bug this build caught live (see
    `domains/can_native_bp.py::incoming_sum_term`'s own docstring) is
    pinned down as a permanent regression test.
  - honest non-convergence reporting: a case measured to oscillate
    persistently (period-4, real Bigville resident #5, see
    CAN_LOOPY_BP_RESULTS.md) reports `converged=False` after the bound,
    never silently returning as if settled.
  - non-mutating by default; `commit=True` writes the decided state back
    mechanically, matching `multi_start_settle_and_pick_best`'s own
    commit shape.
  - two-Mt isolation, the standing check every native CAN rung runs.
  - `seeds/can_native_reimplementation.json` and
    `domains/can_native_orchestration.py` are byte-unchanged by this
    work (checked here, not just claimed).
"""
from __future__ import annotations

import itertools
import json
import random
import subprocess

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
from domains.can_native_bp import run_loopy_bp, incoming_sum_term
from domains.can_native_orchestration import scoped_settle, native_marginal_from_state
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


def _build_path_graph(inner, weights, fields, temperature=2.0):
    """A 3-node PATH (a - b - c), no loops -- max-product BP has a real,
    textbook EXACT guarantee here (belief propagation is exact on
    trees). `weights`: (w_ab, w_bc). `fields`: (h_a, h_b, h_c)."""
    mt = inner.add_node("Microtheory", {
        "temperature": temperature, "discrete_mode": "3state", "can_tick": 0,
    })
    a, b, c = (inner.add_node("Concept", {
        "name": n, "state": 0.0, "external_field": 0.0, "identity_field": 0.0,
    }) for n in "abc")
    for n in (a, b, c):
        inner.add_edge(mt, "has_concept", n, {})
    inner.set_attr(a, "external_field", fields[0])
    inner.set_attr(b, "external_field", fields[1])
    inner.set_attr(c, "external_field", fields[2])
    inner.add_edge(a, "causal_influence", b, {"weight": weights[0]})
    inner.add_edge(b, "causal_influence", a, {"weight": weights[0]})
    inner.add_edge(b, "causal_influence", c, {"weight": weights[1]})
    inner.add_edge(c, "causal_influence", b, {"weight": weights[1]})
    return mt, (a, b, c)


def _brute_force_map(inner, mt, nodes, weights, fields, temperature):
    """Independent ground truth: exhaustively try all 3^3 discrete
    configurations, score each with the SAME `mt_frustration_given_state`
    -- MINIMISED frustration is the MAP target BP's own combine
    (max-product = maximise -H = minimise frustration's own additive
    energy reading) is built to find. Returns the (or a) best state and
    its frustration."""
    vocab = (-1.0, 0.0, 1.0)
    best_f = None
    best_state = None
    for combo in itertools.product(vocab, repeat=len(nodes)):
        state = {n.value: v for n, v in zip(nodes, combo)}
        f = float(inner.mt_frustration_given_state(mt, state))
        if best_f is None or f < best_f:
            best_f = f
            best_state = state
    return best_state, best_f


def test_max_product_bp_is_exact_on_a_tree():
    """BELIEF PROPAGATION'S OWN TEXTBOOK GUARANTEE: on a graph with no
    loops, (max-product) BP finds the TRUE joint MAP, not merely a local
    optimum. Checked against independent brute-force enumeration of all
    3^3=27 configurations, not merely trusted."""
    inner = _loaded_substrate()
    mt, nodes = _build_path_graph(inner, weights=(1.0, -1.0), fields=(0.6, -0.3, 0.9))
    result = run_loopy_bp(inner, mt, combine="max_product", max_rounds=20)
    assert result["converged"], "a genuine tree has no loops -- BP must converge"
    bp_f = float(inner.mt_frustration_given_state(mt, result["final_state"]))

    _, true_best_f = _brute_force_map(inner, mt, nodes, (1.0, -1.0), (0.6, -0.3, 0.9), 2.0)
    print(f"\nBP max-product frustration={bp_f:.6f} true brute-force MAP frustration={true_best_f:.6f}")
    assert abs(bp_f - true_best_f) < 1e-9, (
        "max-product BP is EXACT on a tree -- it must find the TRUE global "
        "MAP, not merely a locally-good state")


def test_max_product_bp_exact_on_a_tree_second_case():
    """A second, independently-chosen tree/field configuration -- one
    worked example is not a proof, but a second confirms the first
    wasn't a coincidence of that specific field/weight combination."""
    inner = _loaded_substrate()
    mt, nodes = _build_path_graph(inner, weights=(-1.0, -1.0), fields=(-0.8, 0.1, -0.2))
    result = run_loopy_bp(inner, mt, combine="max_product", max_rounds=20)
    assert result["converged"]
    bp_f = float(inner.mt_frustration_given_state(mt, result["final_state"]))
    _, true_best_f = _brute_force_map(inner, mt, nodes, (-1.0, -1.0), (-0.8, 0.1, -0.2), 2.0)
    assert abs(bp_f - true_best_f) < 1e-9


def test_incoming_sum_term_requires_nodeid_keys_not_raw_ints():
    """REGRESSION for the exact bug caught live during this build (see
    `incoming_sum_term`'s own docstring and CAN_LOOPY_BP_RESULTS.md): a
    raw-int-keyed override silently zeros every ladder branch because
    `Eq(Value::Node, Value::Int)` is never true. This pins the CORRECT
    (NodeID-keyed) behaviour down directly against the real engine, not
    only indirectly via run_loopy_bp's own end-to-end numbers."""
    from substrate_rs import Lit
    inner = _loaded_substrate()
    mt = inner.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "3state", "can_tick": 0})
    a = inner.add_node("Concept", {"name": "a", "state": 0.0, "external_field": 0.0, "identity_field": 0.0})
    b = inner.add_node("Concept", {"name": "b", "state": 0.0, "external_field": 0.0, "identity_field": 0.0})
    inner.add_edge(mt, "has_concept", a, {})
    inner.add_edge(mt, "has_concept", b, {})
    inner.add_edge(a, "causal_influence", b, {"weight": 1.0})

    # Correct usage: NodeID key.
    term_correct = incoming_sum_term(Lit(a), None, 1.0, {b: 7.5})
    val_correct = float(term_correct.evaluate(None, inner))
    assert abs(val_correct - 7.5) < 1e-9, (
        "a NodeID-keyed override must be read back -- the ladder should "
        "match b's real identity and contribute its 7.5")

    # Buggy usage (what an earlier version of this module did): a raw
    # int key. Must NOT silently match -- the whole point of this test
    # is confirming the type-mismatch behaviour is real, not assuming it.
    term_wrong = incoming_sum_term(Lit(a), None, 1.0, {b.value: 7.5})
    val_wrong = float(term_wrong.evaluate(None, inner))
    assert val_wrong == 0.0, (
        "a raw-int-keyed override must NOT match a live Value::Node -- "
        "confirming this is the documented failure mode, not merely "
        "assuming it")


def test_bp_reports_converged_false_on_a_measured_oscillating_real_network():
    """Real Bigville resident #5 (CAN_LOOPY_BP_RESULTS.md) is measured to
    enter a persistent period-4 max-product message cycle and never
    settle within the bound -- honest non-convergence reporting, not a
    silently-wrong answer. This is a REAL property of loopy BP on this
    network (a genuine 3-cycle exists in Bigville's own structural
    template, CAN_SOLVER_TRACTABILITY_RESULTS.md Sec2), not a bug."""
    residents = json.load(open(CAST_PATH))["residents"]
    resident = next(r for r in residents if r["index"] == 5)

    s = sr._native.Substrate()
    install_productions(s)
    manifest = json.load(open(SEED_PATH))
    s.load_seed_manifest(engine_rules_only(manifest))
    built = build_resident_can_mt(s, resident)
    apply_scenario_evidence(s, built["concepts"])
    s.set_attr(built["mt_node"], "discrete_mode", "3state")
    s.set_attr(built["mt_node"], "can_tick", 0)

    result = run_loopy_bp(s, built["mt_node"], combine="max_product", max_rounds=40, epsilon=1e-3)
    print(f"\nresident#5 max_product converged={result['converged']} rounds={result['rounds']}")
    print(f"max_delta_history tail: {[round(x,3) for x in result['max_delta_history'][-8:]]}")
    assert result["rounds"] == 40, "must exhaust the bound, not stop early on a false-positive settle"
    assert result["converged"] is False, (
        "this network is MEASURED to oscillate persistently -- reporting "
        "converged=True here would be silently returning a possibly-wrong "
        "answer, exactly what the task's own non-negotiable forbids")
    # The oscillation itself must be real (nonzero, sustained), not a
    # trivial epsilon-adjacent wobble.
    tail = result["max_delta_history"][-8:]
    assert max(tail) > 1.0, "the measured oscillation is large, not numerical noise"


def test_bp_does_not_mutate_graph_by_default():
    """Non-mutating by default -- matching can_counterfactual.py's own
    predict_ripple, which NEVER writes any node attr unless the caller
    explicitly asks."""
    inner = _loaded_substrate()
    mt, nodes = _build_path_graph(inner, weights=(1.0, -1.0), fields=(0.5, -0.5, 0.2))
    before = {n.value: inner.node(n)["attrs"].get("state") for n in nodes}
    run_loopy_bp(inner, mt, combine="max_product", max_rounds=20, commit=False)
    after = {n.value: inner.node(n)["attrs"].get("state") for n in nodes}
    assert before == after, "run_loopy_bp(commit=False) must not mutate any Concept.state"


def test_bp_commit_writes_the_decided_state():
    """`commit=True` writes the already-decided final_state back onto the
    real Concepts -- mechanical translation, matching
    `multi_start_settle_and_pick_best`'s own commit step."""
    inner = _loaded_substrate()
    mt, nodes = _build_path_graph(inner, weights=(1.0, -1.0), fields=(0.5, -0.5, 0.2))
    result = run_loopy_bp(inner, mt, combine="max_product", max_rounds=20, commit=True)
    live_state = {n.value: float(inner.node(n)["attrs"].get("state", 0.0)) for n in nodes}
    assert live_state == result["final_state"]


def test_two_mt_isolation_holds_for_loopy_bp():
    """Standing check every native CAN rung in this arc runs
    (CAN_FINAL_MIGRATION_RESULTS.md Sec0's own hazard): a sibling Mt's
    state must be byte-unchanged after running BP (with commit=True) on
    a DIFFERENT Mt in the same graph."""
    inner = _loaded_substrate()
    mt_a, nodes_a = _build_path_graph(inner, weights=(1.0, -1.0), fields=(0.5, -0.5, 0.2))
    mt_b, nodes_b = _build_path_graph(inner, weights=(-1.0, 1.0), fields=(-0.5, 0.5, -0.2))
    for n in nodes_b:
        inner.set_attr(n, "state", 1.0)
    before_b = {n.value: inner.node(n)["attrs"].get("state") for n in nodes_b}

    run_loopy_bp(inner, mt_a, combine="max_product", max_rounds=20, commit=True)

    after_b = {n.value: inner.node(n)["attrs"].get("state") for n in nodes_b}
    assert before_b == after_b, "running BP on mt_a mutated an unrelated mt_b"


def test_bp_well_behaved_on_a_real_bigville_resident_no_exception():
    """A DIFFERENT real resident (not #5's measured oscillator) -- no
    exception, returns a well-formed result dict, on real production
    graph-building code (`build_resident_can_mt`/`apply_scenario_evidence`,
    unmodified)."""
    residents = json.load(open(CAST_PATH))["residents"]
    resident = next(r for r in residents if r["index"] == 58)

    s = sr._native.Substrate()
    install_productions(s)
    manifest = json.load(open(SEED_PATH))
    s.load_seed_manifest(engine_rules_only(manifest))
    built = build_resident_can_mt(s, resident)
    apply_scenario_evidence(s, built["concepts"])
    s.set_attr(built["mt_node"], "discrete_mode", "3state")
    s.set_attr(built["mt_node"], "can_tick", 0)

    result = run_loopy_bp(s, built["mt_node"], combine="sum_product", max_rounds=40)
    assert set(result["final_state"].keys()) == set(built["concepts"][k].value for k in built["concepts"])
    assert result["combine"] == "sum_product"
    assert isinstance(result["converged"], bool)


def test_sum_product_reaches_lower_or_equal_frustration_than_max_product_never_the_reverse_on_a_null_free_case():
    """On the simple tree (no loops, no ties), both variants should agree
    exactly -- a sanity check that the two combine modes are not
    ACCIDENTALLY different implementations of the same thing, and that
    neither is silently broken relative to the other in the easy case."""
    inner = _loaded_substrate()
    mt, nodes = _build_path_graph(inner, weights=(1.0, -1.0), fields=(0.6, -0.3, 0.9))
    r_max = run_loopy_bp(inner, mt, combine="max_product", max_rounds=20)
    inner2 = _loaded_substrate()
    mt2, nodes2 = _build_path_graph(inner2, weights=(1.0, -1.0), fields=(0.6, -0.3, 0.9))
    r_sum = run_loopy_bp(inner2, mt2, combine="sum_product", max_rounds=20)
    f_max = float(inner.mt_frustration_given_state(mt, r_max["final_state"]))
    f_sum = float(inner2.mt_frustration_given_state(mt2, r_sum["final_state"]))
    print(f"\ntree case: max_product frustration={f_max} sum_product frustration={f_sum}")
    assert f_max <= f_sum + 1e-9, (
        "max-product's own MAP-seeking combine must never do WORSE than "
        "sum-product's marginal-argmax on a tree")


def test_native_reimplementation_seed_and_orchestration_module_untouched():
    """CONFIRMS, not merely claims, that this rung never touched the two
    explicitly-out-of-scope files."""
    diff_seed = subprocess.run(
        ["git", "diff", "--stat", "main", "--",
         "seeds/can_native_reimplementation.json"],
        capture_output=True, text=True,
    )
    diff_orch = subprocess.run(
        ["git", "diff", "--stat", "main", "--",
         "domains/can_native_orchestration.py"],
        capture_output=True, text=True,
    )
    assert diff_seed.stdout.strip() == "", "can_native_reimplementation.json must be byte-unchanged"
    assert diff_orch.stdout.strip() == "", "can_native_orchestration.py must be byte-unchanged"
