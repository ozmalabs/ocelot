"""test_stopping_policy — the jabberwock DECIDES WHEN TO STOP fixing. The last step
of the self-improvement loop that was still a Python drain is now the agent's OWN
graph decision: STOP by SUFFICIENCY, not completion. There is no win condition; the
agent STOPS when what REMAINS is not salient enough to be worth fixing, deliberately
leaving low-salience gaps UNFIXED ("sufficient -- move on; yeah yeah, the rest").
(donkey=0, DISCRIMINATIVE.)

The decision is ONE graph Program (seeds/stopping_policy.json):

  should_continue = IfThenElse(
                      Gt( MaxOver(unfixed agenda gaps, by norm_salience, default -1),
                          SufficiencyPolicy.threshold ),
                      1.0,   # CONTINUE
                      0.0 )  # STOP

evaluated in Rust; Python only reads the boolean and breaks. Each gate would FAIL if
the mechanism were fake:

  · STOP BY SUFFICIENCY (headline) — mixed salience (1 high efficiency + 2 low
    understanding, low < threshold): the cycle fixes the high gap and STOPS, leaving
    the low gaps UNFIXED (verbatim fixed-vs-left). (Fails if it drained the queue.)
  · DATA-DRIVEN — RAISE a left gap's salience above the threshold and the SAME
    Program CONTINUES and fixes it; LOWER it and the SAME Program STOPS and leaves it.
    Same Program, different salience, different stop point. (Fails if the stop were a
    count.)
  · ALL-HIGH vs ALL-LOW — all-high fixes ALL (no early stop); all-low fixes NONE
    (stops immediately). (Fails if the stop ignored salience.)
  · NOT-A-COUNT — two runs, SAME number of gaps, different salience distribution,
    DIFFERENT stop counts. (Fails if the stop were 'after N'.)
  · STILL FIXES IN ORDER + VERIFIES — the fixed gaps stay salience-ordered and each
    #2-verifies (no regression to the prior layer). (Fails if the stop broke ordering.)
  · AUTONOMOUS — no hardcoded 'stop after N', no `while gaps:`/`len(...)` deciding
    termination, no threshold literal in Python; the stop verdict is the Program's
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

COLD_MS = 1400.0
WARM_PER_ITEM = 0.4
N_ITEMS = 20


def _require():
    pytest.importorskip("substrate_rs")


def _fresh_agent():
    """A booted agent HOLDING a real cold-init load timing, so the efficiency
    perceiver mints a real performance gap (salience = the ~1.4s excess) alongside the
    two understanding gaps."""
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


def _perceived(a):
    """perceive + normalize; return the agenda ids."""
    from domains import gap_prioritization as gp
    agenda = gp.perceive_gaps(a)
    gp.normalize_all(a, agenda)
    return agenda


def _set_raw(a, gap, raw):
    a.s.set_attr(gap, "salience", float(raw))


def _norm(a, gap):
    return a.s.node(gap)["attrs"].get("norm_salience")


def _u_gaps(a, agenda):
    from domains import gap_prioritization as gp
    return [g for g in agenda if gp.gap_salience(a, g)[0] == "understanding"]


def _p_gap(a, agenda):
    from domains import gap_prioritization as gp
    return [g for g in agenda if gp.gap_salience(a, g)[0] == "performance"][0]


# ===========================================================================
# STOP BY SUFFICIENCY (headline) — fix the high gap, LEAVE the low gaps unfixed.
# ===========================================================================
def test_stop_by_sufficiency_leaves_low_salience_unfixed():
    _require()
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp
    a = _fresh_agent()
    agenda = _perceived(a)

    # MIXED salience: 1 HIGH efficiency (~1.4) + 2 LOW understanding (0.2 < threshold).
    for g in _u_gaps(a, agenda):
        _set_raw(a, g, 0.2)
    sp.set_sufficiency_threshold(a, 0.5)          # POLICY: leave residual < 0.5

    order = gp.prioritize(a, agenda)
    ledger, left = gp.enact_in_order_with_stopping(a, order)

    fixed_kinds = [r["kind"] for r in ledger]
    left_kinds = [gp.gap_salience(a, g)[0] for g in left]
    fixed_ids = [r["gap_str"] for r in ledger]
    left_ids = [str(g) for g in left]
    print("\nSTOP BY SUFFICIENCY (threshold=%.2f):" % sp.sufficiency_threshold(a))
    print("  FIXED:", [(r["kind"], round(_norm(a, r["gap"]), 3)) for r in ledger])
    print("  LEFT :", [(gp.gap_salience(a, g)[0], round(_norm(a, g), 3)) for g in left])

    # the high efficiency gap is FIXED; the two low understanding gaps are LEFT UNFIXED.
    assert fixed_kinds == ["performance"], f"only the high gap fixed: {fixed_kinds}"
    assert left_kinds == ["understanding", "understanding"], f"low gaps left: {left_kinds}"
    # verbatim: the low gaps are NOT in the fixed set (deliberately unfixed).
    for g in _u_gaps(a, agenda):
        assert str(g) not in fixed_ids, f"low-salience gap {g} must be LEFT unfixed"
        assert str(g) in left_ids, f"low-salience gap {g} must be in the left set"
    # sufficiency reached before draining the order.
    assert len(ledger) < len(order), "the cycle STOPPED (did not drain the agenda)"


# ===========================================================================
# DATA-DRIVEN — RAISE a left gap's salience -> continues + fixes; LOWER -> stops +
# leaves. SAME Program, DIFFERENT salience, DIFFERENT stop point.
# ===========================================================================
def test_data_driven_stop_point_moves_with_salience():
    _require()
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp

    # LOWER: understanding gaps below the threshold -> STOP leaves them.
    a = _fresh_agent()
    agenda = _perceived(a)
    for g in _u_gaps(a, agenda):
        _set_raw(a, g, 0.2)
    sp.set_sufficiency_threshold(a, 0.5)
    led_lo, left_lo = gp.enact_in_order_with_stopping(a, gp.prioritize(a, agenda))
    print("\nDATA-DRIVEN:")
    print("  LOWERED  -> fixed:", [r["kind"] for r in led_lo],
          "left:", [gp.gap_salience(a, g)[0] for g in left_lo])
    assert [r["kind"] for r in led_lo] == ["performance"]
    assert len(left_lo) == 2

    # RAISE one understanding gap ABOVE the threshold -> the SAME Program CONTINUES and
    # fixes it. Different salience DATA, same Program, different stop point.
    a2 = _fresh_agent()
    agenda2 = _perceived(a2)
    us = _u_gaps(a2, agenda2)
    _set_raw(a2, us[0], 0.9)                       # RAISED above 0.5
    _set_raw(a2, us[1], 0.2)                       # still below
    sp.set_sufficiency_threshold(a2, 0.5)
    led_hi, left_hi = gp.enact_in_order_with_stopping(a2, gp.prioritize(a2, agenda2))
    fixed_hi = [r["kind"] for r in led_hi]
    print("  RAISED   -> fixed:", fixed_hi,
          "left:", [gp.gap_salience(a2, g)[0] for g in left_hi])

    # now performance AND the raised understanding gap are fixed; the still-low one left.
    assert fixed_hi == ["performance", "understanding"], f"raised gap now fixed: {fixed_hi}"
    assert [str(g) for g in left_hi] == [str(us[1])], "the still-low gap is left"
    # THE STOP POINT MOVED: lowered fixed 1, raised fixed 2 -- same Program, same
    # threshold, different salience.
    assert len(led_hi) == len(led_lo) + 1, "raising a salience moved the stop point"


# ===========================================================================
# ALL-HIGH vs ALL-LOW — all-high fixes ALL; all-low fixes NONE.
# ===========================================================================
def test_all_high_fixes_all_all_low_fixes_none():
    _require()
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp

    # ALL-HIGH: every gap above the threshold -> fix ALL, no early stop.
    a = _fresh_agent()
    agenda = _perceived(a)
    for g in _u_gaps(a, agenda):
        _set_raw(a, g, 0.9)                        # all high
    sp.set_sufficiency_threshold(a, 0.5)
    led_all, left_all = gp.enact_in_order_with_stopping(a, gp.prioritize(a, agenda))
    print("\nALL-HIGH -> fixed:", [r["kind"] for r in led_all], "left:", len(left_all))
    assert len(led_all) == len(agenda), "all-high fixes ALL"
    assert left_all == [], "all-high leaves NONE"

    # ALL-LOW: every gap below the threshold -> STOP immediately, fix NONE.
    a2 = _fresh_agent()
    agenda2 = _perceived(a2)
    _set_raw(a2, _p_gap(a2, agenda2), 0.1)         # even the perf gap low (raw)
    for g in _u_gaps(a2, agenda2):
        _set_raw(a2, g, 0.1)
    gp.normalize_all(a2, agenda2)                  # re-normalize the lowered raws
    sp.set_sufficiency_threshold(a2, 0.5)
    led_none, left_none = gp.enact_in_order_with_stopping(a2, gp.prioritize(a2, agenda2))
    print("ALL-LOW  -> fixed:", [r["kind"] for r in led_none], "left:", len(left_none))
    assert led_none == [], "all-low fixes NONE (stops immediately)"
    assert len(left_none) == len(agenda2), "all-low leaves ALL"


# ===========================================================================
# NOT-A-COUNT — same #gaps, different distribution, different stop counts.
# ===========================================================================
def test_not_a_count_same_gaps_different_stop():
    _require()
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp

    # run A: perf high, both understanding LOW -> stops after 1.
    a = _fresh_agent()
    ag = _perceived(a)
    for g in _u_gaps(a, ag):
        _set_raw(a, g, 0.2)
    sp.set_sufficiency_threshold(a, 0.5)
    led_a, _ = gp.enact_in_order_with_stopping(a, gp.prioritize(a, ag))

    # run B: SAME number of gaps (3), one understanding HIGH -> stops after 2.
    b = _fresh_agent()
    bg = _perceived(b)
    ub = _u_gaps(b, bg)
    _set_raw(b, ub[0], 0.7); _set_raw(b, ub[1], 0.2)
    sp.set_sufficiency_threshold(b, 0.5)
    led_b, _ = gp.enact_in_order_with_stopping(b, gp.prioritize(b, bg))

    print("\nNOT-A-COUNT (both have %d gaps):" % len(ag))
    print("  run A distribution [1.4, 0.2, 0.2] -> stopped after", len(led_a))
    print("  run B distribution [1.4, 0.7, 0.2] -> stopped after", len(led_b))
    assert len(ag) == len(bg) == 3, "same number of gaps"
    assert len(led_a) == 1 and len(led_b) == 2, \
        f"SAME #gaps, DIFFERENT stop counts: A={len(led_a)} B={len(led_b)}"
    assert len(led_a) != len(led_b), "the stop is by salience, not a count"


# ===========================================================================
# STILL FIXES IN ORDER + VERIFIES — the fixed gaps stay salience-ordered and each
# #2-verifies (no regression to the prior layer).
# ===========================================================================
def test_still_fixes_in_order_and_verifies():
    _require()
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp
    a = _fresh_agent()
    # default threshold 0.5; real gaps (1.4, 1.0, 1.0) all clear -> full cycle, none left.
    led = gp.run_cycle(a)
    print("\nIN-ORDER + VERIFIES:")
    print("  threshold:", led["sufficiency_threshold"], "stopped:", led["stopped"])
    for r in led["enacted"]:
        print(f"    kind={r['kind']:<13} norm={round(_norm(a, r['gap']), 3)} "
              f"accepted={r.get('accepted')}")

    # enactment order == graph order (identity), stopped only at drain (all real gaps
    # clear the default policy).
    assert [str(g) for g in led["order"]] == [r["gap_str"] for r in led["enacted"]], \
        "enactment follows the graph-decided order exactly"
    # fixed gaps are salience-descending (the prior layer's ordering intact).
    norms = [_norm(a, r["gap"]) for r in led["enacted"]]
    assert norms == sorted(norms, reverse=True), f"fixed gaps stay salience-ordered: {norms}"
    # each fix #2-verifies + accepts (the real drivers, called as-is).
    for r in led["enacted"]:
        assert r.get("accepted") is True, f"each fix #2-verifies + accepts: {r}"
        assert r.get("verify") is not None, "the driver's #2 verdict is recorded"


# ===========================================================================
# AUTONOMOUS — the stop verdict is the graph Program's output, not hardcoded Python.
# ===========================================================================
def test_autonomous_source_audit():
    from domains import stopping_policy as sp
    from domains import gap_prioritization as gp
    sp_src = inspect.getsource(sp)
    gp_src = inspect.getsource(gp)

    # the STOP decision goes through the seeded should_continue Program, evaluated in Rust.
    assert "should_continue" in sp_src and "evaluate" in sp_src, \
        "the stop verdict is the Program's evaluate output"
    assert "_load_program" in sp_src, "the Program is read from the graph"

    # the should_continue reader must NOT itself decide by count / while / threshold.
    sc_src = sp_src[sp_src.index("def should_continue("):sp_src.index("def mark_fixed(")]
    for banned in ("while ", "for ", "len(", "sorted(", ".sort(", " > 0.5", "< 0.5"):
        assert banned not in sc_src, f"should_continue must not decide in Python: {banned!r}"

    # the ENACTMENT loop breaks on the Program's verdict -- no count/while-queue governs it.
    enact_src = gp_src[gp_src.index("def enact_in_order_with_stopping("):
                       gp_src.index("def run_cycle(")]
    assert "sp.should_continue(agent)" in enact_src, "the loop guard reads the Program"
    assert "while " not in enact_src, "no while-queue-not-empty termination"
    # no 'stop after N' count literal deciding termination.
    for banned in ("iterations", "max_iters", "count", "== 3", ">= 3", "> 2"):
        assert banned not in enact_src, f"termination must not be a count: {banned!r}"

    # the sufficiency THRESHOLD is graph data, not a Python literal compared to salience.
    # (0.5 appears only as the seed default / a test policy value -- never in the module.)
    assert "0.5" not in sp_src, "the threshold is graph POLICY, not a Python literal"
    assert "threshold" in sp_src  # only READ/WRITE the graph attr, never compare in Python
    # the salience-vs-threshold comparison is NOT a Python operator on the two values --
    # should_continue only decodes the Program's own 0/1 output.
    for banned in (">= ", "<= ", "salience >", "salience <", "> threshold", "< threshold"):
        assert banned not in sc_src, f"no Python salience/threshold comparison: {banned!r}"

    # no LLM / no training in the stopping decision.
    for banned in (".fit(", ".backward(", "import torch", "openai", "anthropic", "gemini"):
        assert banned not in sp_src, banned


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-s", "-p", "no:randomly"]))
