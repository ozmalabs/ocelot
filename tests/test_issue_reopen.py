"""test_issue_reopen — the jabberwock DECIDES WHEN TO REOPEN a DEFERRED gap and
PASSES IT THROUGH into the running session. The twin of should_continue, run the
other way: stopping_policy STOPS by sufficiency and leaves low-salience gaps UNFIXED
(the deferred `left` set); this reopens one when re-measurement lifts its salience
above a strictly HIGHER reopen bar, and hands it to the LIVE loop. (donkey=0,
DISCRIMINATIVE.)

The decision is ONE graph Program (seeds/issue_reopen.json):

  should_reopen(g) = IfThenElse(
                       Gt( g.norm_salience, ReopenPolicy.threshold ),
                       1.0,   # REOPEN
                       0.0 )  # stay DEFERRED

evaluated in Rust with the gap bound as env `g`; Python reads the boolean. Each gate
would FAIL if the mechanism were fake:

  · DEFERRED THEN REOPEN (headline) — a gap deferred by sufficiency, re-measured
    ABOVE the reopen bar, reopens + is PASSED THROUGH: a live ReopenedConcern node
    exists and the running loop's fire_reflexes trips on it. (Fails if reopen were a
    print, or never fired.)
  · DATA-DRIVEN — RAISE a deferred gap above the reopen bar -> reopens + passes
    through; LEAVE it low -> stays deferred (no concern, no fire). Same Program,
    different salience, different outcome. (Fails if reopen ignored salience.)
  · HYSTERESIS — deferred at 0.2 (suff=0.5, reopen=0.7): no reopen at 0.2, no reopen
    at 0.6 (above sufficiency, below reopen bar -- the dead-band), DOES reopen at 0.8.
    (Fails if reopen were merely 'un-defer' at the sufficiency threshold.)
  · PASS-THROUGH IS REAL — the reopened issue is a LIVE node the running loop
    consumes: fire_reflexes fires the seeded reflex AND its response marks the concern
    pursued. (Fails if the hand-off were a log.)
  · AUTONOMOUS — no hardcoded reopen, no tick-count, no threshold literal in Python;
    the reopen verdict is the Program's output. (Source audit.)
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


def _u_gaps(a, agenda):
    from domains import gap_prioritization as gp
    return [g for g in agenda if gp.gap_salience(a, g)[0] == "understanding"]


def _set_raw(a, gap, raw):
    a.s.set_attr(gap, "salience", float(raw))


def _norm(a, gap):
    return a.s.node(gap)["attrs"].get("norm_salience")


def _deferred_run(a, low=0.2, suff=0.5, reopen=0.7):
    """Run the scheduling cycle so it STOPS by sufficiency, leaving the understanding
    gaps DEFERRED (the `left` set). Set the reopen policy. Returns (agenda, left)."""
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp
    from domains import issue_reopen as ir
    agenda = gp.perceive_gaps(a)
    gp.normalize_all(a, agenda)
    for g in _u_gaps(a, agenda):
        _set_raw(a, g, low)
    gp.normalize_all(a, agenda)
    sp.set_sufficiency_threshold(a, suff)
    ir.set_reopen_threshold(a, reopen)
    _led, left = gp.enact_in_order_with_stopping(a, gp.prioritize(a, agenda))
    return agenda, left


# ===========================================================================
# DEFERRED THEN REOPEN (headline) — deferred by sufficiency, re-measured high,
# reopened + passed through; the running loop sees it.
# ===========================================================================
def test_deferred_then_reopen_passes_through():
    _require()
    from domains import gap_prioritization as gp
    from domains import issue_reopen as ir
    a = _fresh_agent()
    agenda, left = _deferred_run(a)

    # the two understanding gaps were DEFERRED (left unfixed by the sufficiency stop).
    assert len(left) == 2, f"the low gaps are deferred: {len(left)}"
    g = left[0]
    # at its deferred salience (0.2) the reopen bar (0.7) is NOT cleared.
    assert ir.should_reopen(a, g) is False, "deferred gap does not reopen at low salience"

    # RE-MEASURE its salience HIGHER (raw 0.9 -> norm above the reopen bar).
    _set_raw(a, g, 0.9)
    ir.remeasure_salience(a, g)
    print("\nDEFERRED THEN REOPEN:")
    print("  deferred gap re-measured norm:", round(_norm(a, g), 3),
          "reopen_threshold:", ir.reopen_threshold(a))

    # the SAME Program now returns REOPEN.
    assert ir.should_reopen(a, g) is True, "re-measured-high gap REOPENS"

    # PASS IT THROUGH -> a live ReopenedConcern exists and the running loop sees it.
    res = ir.reopen_deferred(a, left)
    print("  reopened:", len(res["reopened"]),
          "concerns:", len(res["concerns"]),
          "still_deferred:", len(res["still_deferred"]))
    assert res["reopened"] == [g], f"only the re-measured-high gap reopens: {res['reopened']}"
    assert len(res["concerns"]) == 1, "one live concern minted"
    # the concern is a LIVE, queryable, active node attached to the running session.
    actives = ir.active_concerns(a)
    assert res["concerns"][0] in actives, "the reopened concern is an ACTIVE live node"
    # the RUNNING loop sees it: fire_reflexes on the real adapter trips the seeded reflex.
    fired = a.fire_reflexes()
    print("  running-loop fire_reflexes:", fired)
    assert ir.REOPEN_REFLEX in fired, "the running loop's fire_reflexes SEES the reopened concern"
    # and the live loop ACTED on it (the reflex response marked it pursued).
    assert a.s.node(res["concerns"][0])["attrs"].get("pursued") == 1.0, \
        "the running loop acted on the reopened concern"


# ===========================================================================
# DATA-DRIVEN — raise a deferred gap -> reopens + passes through; leave it low ->
# stays deferred. SAME Program, DIFFERENT salience, DIFFERENT outcome.
# ===========================================================================
def test_data_driven_reopen_vs_stay_deferred():
    _require()
    from domains import issue_reopen as ir

    # RAISED: re-measure a deferred gap above the reopen bar -> reopens + passes through.
    a = _fresh_agent()
    _agenda, left = _deferred_run(a)
    g = left[0]
    _set_raw(a, g, 0.9)
    ir.remeasure_salience(a, g)
    res_hi = ir.reopen_deferred(a, [g])
    fired_hi = a.fire_reflexes()
    print("\nDATA-DRIVEN:")
    print("  RAISED   norm:", round(_norm(a, g), 3),
          "-> reopened:", len(res_hi["reopened"]),
          "concerns:", len(res_hi["concerns"]), "fired:", fired_hi)
    assert res_hi["reopened"] == [g], "raised gap reopens"
    assert len(ir.active_concerns(a)) == 1, "raised gap passes through (live concern)"
    assert ir.REOPEN_REFLEX in fired_hi, "raised gap is seen by the running loop"

    # LEFT LOW: the SAME Program on a still-low deferred gap -> stays deferred.
    b = _fresh_agent()
    _agenda2, left2 = _deferred_run(b)
    h = left2[0]                                   # untouched at deferred salience 0.2
    res_lo = ir.reopen_deferred(b, [h])
    fired_lo = b.fire_reflexes()
    print("  LEFT-LOW norm:", round(_norm(b, h), 3),
          "-> reopened:", len(res_lo["reopened"]),
          "concerns:", len(res_lo["concerns"]), "fired:", fired_lo)
    assert res_lo["reopened"] == [], "low gap stays deferred (no reopen)"
    assert ir.active_concerns(b) == [], "low gap does NOT pass through (no live concern)"
    assert ir.REOPEN_REFLEX not in fired_lo, "the running loop sees NOTHING for a low gap"


# ===========================================================================
# HYSTERESIS — reopen is a distinct, HIGHER bar than un-defer (sufficiency).
# ===========================================================================
def test_hysteresis_reopen_is_a_higher_bar():
    _require()
    from domains import issue_reopen as ir
    from domains import stopping_policy as sp
    a = _fresh_agent()
    _agenda, left = _deferred_run(a, low=0.2, suff=0.5, reopen=0.7)
    g = left[0]
    print("\nHYSTERESIS (sufficiency=%.2f, reopen=%.2f):"
          % (sp.sufficiency_threshold(a), ir.reopen_threshold(a)))

    # at 0.2 (deferred): below BOTH -> no reopen.
    _set_raw(a, g, 0.2); ir.remeasure_salience(a, g)
    r02 = ir.should_reopen(a, g)
    print("  norm=0.2 (below sufficiency)     -> reopen:", r02)
    assert r02 is False, "deferred gap does not reopen at 0.2"

    # at 0.6: ABOVE the sufficiency floor (0.5) yet BELOW the reopen bar (0.7) -> the
    # dead-band. It would no longer be deferred, but it does NOT reopen.
    _set_raw(a, g, 0.6); ir.remeasure_salience(a, g)
    r06 = ir.should_reopen(a, g)
    print("  norm=0.6 (dead-band, >suff <reopen) -> reopen:", r06)
    assert r06 is False, "0.6 is above sufficiency but below the reopen bar -- no reopen"

    # at 0.8: above the reopen bar -> reopen.
    _set_raw(a, g, 0.8); ir.remeasure_salience(a, g)
    r08 = ir.should_reopen(a, g)
    print("  norm=0.8 (above reopen bar)      -> reopen:", r08)
    assert r08 is True, "0.8 clears the reopen bar -> reopen"

    # the reopen bar is strictly higher than the sufficiency bar (a real dead-band).
    assert ir.reopen_threshold(a) > sp.sufficiency_threshold(a), \
        "reopen threshold is a strictly HIGHER bar than sufficiency (hysteresis)"


# ===========================================================================
# PASS-THROUGH IS REAL — a LIVE node the running loop consumes, not a print.
# ===========================================================================
def test_pass_through_is_a_real_live_handoff():
    _require()
    from domains import issue_reopen as ir
    a = _fresh_agent()
    _agenda, left = _deferred_run(a)
    g = left[0]
    _set_raw(a, g, 0.9); ir.remeasure_salience(a, g)
    res = ir.reopen_deferred(a, [g])
    concern = res["concerns"][0]

    # (1) the concern is a real graph node, edged from the agent hub, queryable active.
    hub_concerns = a.inner.neighbours(a.agent, ir.HAS_CONCERN)
    print("\nPASS-THROUGH IS REAL:")
    print("  concern node:", concern, "attached-to-hub:", concern in hub_concerns)
    assert concern in hub_concerns, "the reopened concern is edged from the agent hub"
    assert concern in ir.active_concerns(a), "the concern is queryable as ACTIVE"

    # (2) the RUNNING loop (not this test) consumes it: fire_reflexes trips the seeded
    # reflex whose stimulus is 'an active ReopenedConcern exists', and its response acts.
    assert a.s.node(concern)["attrs"].get("pursued") is None, "not yet pursued"
    fired = a.fire_reflexes()
    print("  fire_reflexes ->", fired,
          "| pursued after:", a.s.node(concern)["attrs"].get("pursued"))
    assert ir.REOPEN_REFLEX in fired, "the live reflex loop fired on the reopened concern"
    assert a.s.node(concern)["attrs"].get("pursued") == 1.0, \
        "the live loop ACTED on the concern (marked it pursued) -- not a print"

    # (3) once no active concern remains, the live loop does NOT fire (the stimulus is
    # the graph node, not a Python flag): clear it and confirm the reflex goes quiet.
    a.s.set_attr(concern, "active", 0.0)
    fired2 = a.fire_reflexes()
    print("  after clearing active -> fire_reflexes:", fired2)
    assert ir.REOPEN_REFLEX not in fired2, "the reflex is driven by the live node, not a flag"


# ===========================================================================
# AUTONOMOUS — the reopen verdict is the graph Program's output, not hardcoded Python.
# ===========================================================================
def test_autonomous_source_audit():
    from domains import issue_reopen as ir
    src = inspect.getsource(ir)

    # the REOPEN decision goes through the seeded should_reopen Program, in Rust.
    assert "should_reopen" in src and "evaluate" in src, \
        "the reopen verdict is the Program's evaluate output"
    assert "_load_program" in src, "the Program is read from the graph"

    # the should_reopen reader must NOT itself decide by count / loop / threshold.
    sr_src = src[src.index("def should_reopen("):src.index("def reopen(")]
    for banned in ("while ", "for ", "len(", "sorted(", ".sort(",
                   " > 0.7", "< 0.7", ">= 0.7", "<= 0.7"):
        assert banned not in sr_src, f"should_reopen must not decide in Python: {banned!r}"
    # no salience-vs-threshold comparison in Python -- only the Program's own output.
    for banned in ("salience >", "salience <", "> threshold", "< threshold",
                   ">= threshold", "<= threshold", ">= ", "<= "):
        assert banned not in sr_src, f"no Python salience/threshold comparison: {banned!r}"

    # no reopen threshold literal in the module (it is graph POLICY, the ReopenPolicy
    # node). 0.7 appears only in the seed / tests, never in the module source.
    assert "0.7" not in src, "the reopen threshold is graph POLICY, not a Python literal"
    # no tick-count / 'reopen after N' termination anywhere.
    for banned in ("tick_count", "reopen_after", "n_ticks", "== 3", ">= 3", "> 2",
                   "iterations", "max_iters"):
        assert banned not in src, f"reopen must not be a count/tick: {banned!r}"

    # no LLM / no training in the reopen decision.
    for banned in (".fit(", ".backward(", "import torch", "openai", "anthropic", "gemini"):
        assert banned not in src, banned


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-s", "-p", "no:randomly"]))
