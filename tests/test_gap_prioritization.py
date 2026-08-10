"""test_gap_prioritization — the jabberwock SCHEDULES its own fixes: when MULTIPLE
gaps are perceived, it ORDERS them by SALIENCE and fixes most-salient-first — and
the ORDER comes OUT of the graph, not from hardcoded Python (donkey=0,
DISCRIMINATIVE).

The jabberwock already DRIVES its fixes on BOTH dimensions — efficiency
(performance_self_improvement) and understanding (understanding_self_improvement).
This is the SCHEDULING layer on top: perceive the multi-dimensional gap queue,
NORMALIZE each gap's measured salience per a graph-data POLICY, ORDER them via a
graph Program (the gap_priority Argmax, applied repeatedly), and FIX in that order by
dispatching to the existing drivers.

Each gate would FAIL if the mechanism were fake:

  · SALIENCE — 3 gaps perceived (2 understanding + 1 efficiency), each carrying a
    MEASURED salience; the efficiency one-time-init (cold ~1.4s) is the MOST salient.
    (Fails if a gap lacks a measured salience or the perf excess isn't dominant.)
  · PRIORITIZE (graph, DATA-DRIVEN) — the gap_priority Program orders the gaps
    most-salient-first -> the efficiency gap FIRST; and BOOSTING an understanding
    gap's salience above the efficiency gap's REORDERS it (same Program, different
    data, different order). (Fails if the order were a Python constant.)
  · REVERSE control — reversing the salience signal reverses the order; a
    ZERO-salience gap sorts last. (Fails if salience didn't drive the order.)
  · FIX-IN-ORDER — the combined cycle fixes the gaps in the graph-decided order,
    dispatching to the perf/understanding drivers; each fix #2-verifies; the
    enactment order == the graph order. (Fails if enactment ignored the graph order.)
  · AUTONOMOUS — no hardcoded gap order / no 'efficiency-first' literal; no
    sorted(gaps, key=...) / .sort() over gaps; the order is the Program's Argmax
    output. (Source audit.)
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# the 7f6ff15a numbers' shape: a ~1.4s one-time WordNet init, ~0.4 ms/concept warm.
COLD_MS = 1400.0
WARM_PER_ITEM = 0.4
N_ITEMS = 20


def _require():
    pytest.importorskip("substrate_rs")


def _fresh_agent():
    """A booted agent that HOLDS the perceived load timing (recorded via the real
    LoadTimer sensor — the same graph-mint a real timed load makes), so the efficiency
    perceiver mints a real cold-init performance gap."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import load_timing as lt
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    timer = lt.LoadTimer(a)
    timer.record("read_source", 40.0, article="A1")
    timer.record("ground_lexeme", COLD_MS, article="A1", n_items=N_ITEMS, phase="cold")
    timer.record("ground_lexeme", WARM_PER_ITEM * N_ITEMS, article="A2",
                 n_items=N_ITEMS, phase="warm")
    return a


def _kinds(view):
    return [v["kind"] for v in view]


# ===========================================================================
# SALIENCE — 3 gaps, each carrying a MEASURED salience; efficiency the most salient.
# ===========================================================================
def test_salience_measured_per_gap_efficiency_most_salient():
    _require()
    from domains import gap_prioritization as gp
    a = _fresh_agent()
    agenda = gp.perceive_gaps(a)
    assert len(agenda) == 3, f"3 gaps (2 understanding + 1 efficiency): {agenda}"

    print("\nSALIENCE — each perceived gap carries a MEASURED salience:")
    by_kind = {}
    for g in agenda:
        kind, raw = gp.gap_salience(a, g)
        norm = gp.normalize_salience(a, g)
        by_kind.setdefault(kind, []).append((raw, norm))
        print(f"  gap={str(g):<8} kind={kind:<13} raw_salience={raw} norm={norm}")

    assert set(by_kind) == {"performance", "understanding"}
    assert len(by_kind["understanding"]) == 2 and len(by_kind["performance"]) == 1
    # each gap carries a measured salience.
    for g in agenda:
        _kind, raw = gp.gap_salience(a, g)
        assert raw is not None and float(raw) >= 0.0

    perf_raw = by_kind["performance"][0][0]
    perf_norm = by_kind["performance"][0][1]
    # the efficiency latency-excess is HUGE raw (~cold - warm) and, normalized, still
    # the MOST salient of the three.
    assert perf_raw > 1000.0, f"efficiency raw salience is the cold-init excess: {perf_raw}"
    for raw, norm in by_kind["understanding"]:
        assert perf_norm > norm, f"efficiency ({perf_norm}) must be the most salient (> {norm})"


# ===========================================================================
# PRIORITIZE (graph, DATA-DRIVEN) — the gap_priority Program orders most-salient
# first; boosting a gap's salience REORDERS it. SAME Program, DIFFERENT data.
# ===========================================================================
def test_prioritize_is_graph_program_efficiency_first():
    _require()
    from domains import gap_prioritization as gp
    from domains import reflective_faculty as rf
    a = _fresh_agent()
    agenda = gp.perceive_gaps(a)
    gp.normalize_all(a, agenda)

    # the Program itself (verbatim).
    prog = rf._load_program(a.s, "gap_priority")
    assert prog is not None, "gap_priority Program must be held (seeded)"
    print("\nPRIORITIZE — the gap_priority Program (graph data):")
    print("  ", a.s.node(_prog_node(a, "gap_priority"))["attrs"]["program"])

    order = gp.prioritize(a, agenda)
    view = gp.order_view(a, order)
    print("  ORDER (graph-decided):")
    for v in view:
        print("    ", v)
    # the efficiency gap is FIRST — the biggest measured residual.
    assert view[0]["kind"] == "performance", f"efficiency first: {_kinds(view)}"


def test_prioritize_data_driven_boost_reorders():
    _require()
    from domains import gap_prioritization as gp
    a = _fresh_agent()
    agenda = gp.perceive_gaps(a)

    order_before = gp.order_view(a, gp.prioritize(a, agenda))
    assert order_before[0]["kind"] == "performance"

    # BOOST an understanding gap's RAW salience above the efficiency gap's — in the
    # GRAPH. Then re-run the SAME Program.
    u_gaps = [g for g in agenda if gp.gap_salience(a, g)[0] == "understanding"]
    boost = u_gaps[0]
    a.s.set_attr(boost, "salience", 5000.0)
    gp.reset_order(a, agenda)
    order_after = gp.prioritize(a, agenda)
    view_after = gp.order_view(a, order_after)

    print("\nDATA-DRIVEN PROOF — SAME Program, boosted salience, DIFFERENT order:")
    print("  before:", [(v["kind"], v["norm_salience"]) for v in order_before])
    print("  after :", [(v["kind"], v["norm_salience"]) for v in view_after])
    # the boosted understanding gap is now FIRST — the order followed the data.
    assert str(order_after[0]) == str(boost), "boosted gap must sort first"
    assert view_after[0]["kind"] == "understanding"


# ===========================================================================
# REVERSE control — reversing the salience signal reverses the order; a
# ZERO-salience gap sorts last.
# ===========================================================================
def test_reverse_and_zero_controls():
    _require()
    from domains import gap_prioritization as gp
    a = _fresh_agent()
    agenda = gp.perceive_gaps(a)

    base = gp.order_view(a, gp.prioritize(a, agenda))
    base_kinds = _kinds(base)
    print("\nREVERSE control — base order:", base_kinds)

    # REVERSE the salience signal: set each gap's raw salience to -1 * a rank so the
    # ORDER inverts (the least-salient becomes most). The SAME Program re-orders.
    n = len(agenda)
    # give each gap a distinct raw salience matching the base order, then negate.
    for rank, v in enumerate(base):
        g = _gap_by_str(agenda, v["gap"])
        a.s.set_attr(g, "salience", float(n - rank))    # base: descending
    gp.reset_order(a, agenda)
    forward = gp.order_view(a, gp.prioritize(a, agenda))
    for rank, v in enumerate(forward):
        g = _gap_by_str(agenda, v["gap"])
        a.s.set_attr(g, "salience", -float(a.s.node(g)["attrs"]["salience"]))  # reverse signal
    gp.reset_order(a, agenda)
    reversed_view = gp.order_view(a, gp.prioritize(a, agenda))
    print("  forward :", [v["gap"] for v in forward])
    print("  reversed:", [v["gap"] for v in reversed_view])
    assert [v["gap"] for v in reversed_view] == [v["gap"] for v in forward][::-1], \
        "reversing the salience signal reverses the order"

    # ZERO-salience gap sorts LAST.
    a2 = _fresh_agent()
    agenda2 = gp.perceive_gaps(a2)
    zero_gap = agenda2[0]
    a2.s.set_attr(zero_gap, "salience", 0.0)
    gp.reset_order(a2, agenda2)
    zview = gp.order_view(a2, gp.prioritize(a2, agenda2))
    print("  zero-salience gap ->", zview[-1]["gap"], "(last)")
    assert str(zview[-1]["gap"]) == str(zero_gap), "a zero-salience gap sorts last"


# ===========================================================================
# FIX-IN-ORDER — the combined cycle fixes gaps in the graph order, dispatching to
# the existing drivers; each fix #2-verifies; enactment order == graph order.
# ===========================================================================
def test_fix_in_graph_decided_order():
    _require()
    from domains import gap_prioritization as gp
    a = _fresh_agent()
    led = gp.run_cycle(a)

    graph_order = [v["kind"] for v in led["order_view"]]
    enact_order = [r["kind"] for r in led["enacted"]]
    print("\nFIX-IN-ORDER:")
    print("  graph order   :", graph_order)
    print("  enact order   :", enact_order)
    for r in led["enacted"]:
        print(f"    kind={r['kind']:<13} fix={r.get('fix')} accepted={r.get('accepted')}")

    # enactment order == graph order (node identity, not just kind).
    assert [str(g) for g in led["order"]] == [r["gap_str"] for r in led["enacted"]], \
        "enactment must follow the graph-decided order exactly"
    # the efficiency gap is fixed FIRST.
    assert enact_order[0] == "performance"
    # each fix #2-verifies and is accepted (the real fixes, called as-is).
    for r in led["enacted"]:
        assert r.get("accepted") is True, f"each fix #2-verifies + accepts: {r}"
        assert r.get("verify") is not None, "the driver's #2 verdict is recorded"


# ===========================================================================
# AUTONOMOUS — the order is the graph Program's output, not hardcoded Python.
# ===========================================================================
def test_autonomous_source_audit():
    from domains import gap_prioritization as gp
    src = inspect.getsource(gp)

    # the order goes through the seeded Program, evaluated in Rust, applied repeatedly.
    for reused in ("gap_priority", "salience_normalize", "_load_program",
                   "performance_self_improvement", "understanding_self_improvement",
                   "Argmax"):
        assert reused in src, reused

    # the ORDERING function (prioritize) must NOT bake the policy into Python: no
    # sorted(...key=...), no .sort( over gaps, no max( over saliences, no kind literal
    # that fixes the order.
    prio_src = src[src.index("def prioritize("):src.index("def reset_order(")]
    for banned in ("sorted(", ".sort(", "key=", "max(", "min("):
        assert banned not in prio_src, f"prioritize must not sort/rank in Python: {banned!r}"
    # no 'efficiency-first' / kind-order literal governing the order anywhere.
    for banned_literal in ('"efficiency"', "'efficiency'", "== \"performance\":",
                           "performance_first", "efficiency_first"):
        assert banned_literal not in src, banned_literal
    # the pick is the graph Program's Argmax output.
    pick_src = src[src.index("def _pick_most_salient("):src.index("def prioritize(")]
    assert "gap_priority" in pick_src and "evaluate" in pick_src

    # the driver dispatch is a name-keyed registry (marshal), the twin of
    # research_agenda._FILLER_REGISTRY — the kind names appear only as registry keys.
    assert "_DRIVER_REGISTRY" in src
    assert "PERFORMANCE: _enact_performance" in src
    assert "UNDERSTANDING: _enact_understanding" in src

    # no LLM / no training in the scheduler.
    for banned in (".fit(", ".backward(", "import torch", "openai", "anthropic", "gemini"):
        assert banned not in src, banned


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _prog_node(a, name):
    for n in a.s.nodes("Program"):
        if a.s.node(n)["attrs"].get("name") == name:
            return n
    return None


def _gap_by_str(gaps, s):
    for g in gaps:
        if str(g) == str(s):
            return g
    raise KeyError(s)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-s", "-p", "no:randomly"]))
