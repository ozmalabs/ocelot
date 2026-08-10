"""test_running_session_acts — the RUNNING loop doesn't just NOTICE a reopened
deferred gap, it FIXES it. issue_reopen passed a deferred gap through into the live
session (a ReopenedConcern the seeded `reopened_concern_pursue` reflex trips on); the
OLD response only marked it pursued=1.0. This gate proves the running loop now RUNS
THE REAL REPAIR on the reopened gap and CLOSES the concern — the defect is CLEANED in
the live fire_reflexes loop, not the batch queue. (donkey=0, discriminative.)

The ACT is `issue_reopen._reopened_concern_pursue_advance`, the reflex's RESPONSE,
shaped EXACTLY like `_question_pursue_advance` / `_enact_advance`: for each active
ReopenedConcern the running loop surfaces, it recovers the gap the concern TARGETS,
dispatches it to the KIND-keyed driver (gap_prioritization._DRIVER_REGISTRY — the
SAME performance/understanding diagnose->select->#2->apply path enact_in_order uses),
and RESOLVES the concern (resolved=1, gap fixed=1) IFF the driver's fix #2-verifies.
It EVALUATES the driver result + APPLIES it; it never branches on graph state to
decide the repair (the diagnose/select decisions are the driver's graph Programs; the
routing is the registry keyed on kind).

  · ACTS-IN-THE-LIVE-LOOP (headline) — defer a gap by sufficiency -> re-measure high
    -> reopen (pass-through) -> the RUNNING loop's fire_reflexes trips
    reopened_concern_pursue -> its executor RUNS THE FIX -> the DEFECT IS CLEANED: a
    reopened UNDERSTANDING gap has its fragment DROPPED (nominal_filter authored +
    applied); a reopened EFFICIENCY gap has warm_once APPLIED (WordNet resident). The
    reopened gap goes deferred -> reopened -> FIXED via the running loop; the concern
    resolved; #2 accepted.
  · REAL, NOT A MARKER — the actual defect-cleaning is measured (the fragment absent
    from the kept set / WordNet warm), not merely pursued=1.0.
  · DISCRIMINATIVE — a STILL-DEFERRED gap (below the reopen bar, never reopened) is
    NOT fixed by the running loop (no ReopenedConcern -> the executor does nothing for
    it). A reopened gap whose fix FAILS #2 is NOT marked resolved (stays open).
  · MECHANICAL / PRECEDENT — source audit: the executor mirrors
    _question_pursue_advance (evaluate + apply; no if/else over graph state deciding
    the repair; routing is the kind-keyed registry).
"""
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


def _deferred_run(a, low=0.2, suff=0.5, reopen=0.7):
    """Run the scheduling cycle so it STOPS by sufficiency, leaving the understanding
    gaps DEFERRED (the `left` set). Returns (agenda, left)."""
    from domains import gap_prioritization as gp
    from domains import stopping_policy as sp
    from domains import issue_reopen as ir
    agenda = gp.perceive_gaps(a)
    gp.normalize_all(a, agenda)
    for g in _u_gaps(a, agenda):
        a.s.set_attr(g, "salience", float(low))
    gp.normalize_all(a, agenda)
    sp.set_sufficiency_threshold(a, suff)
    ir.set_reopen_threshold(a, reopen)
    _led, left = gp.enact_in_order_with_stopping(a, gp.prioritize(a, agenda))
    return agenda, left


# ===========================================================================
# ACTS-IN-THE-LIVE-LOOP (headline, understanding) — deferred -> reopened -> FIXED
# via the running loop; the concern resolved; the fragment DROPPED.
# ===========================================================================
def test_acts_in_the_live_loop_understanding():
    _require()
    from domains import gap_prioritization as gp
    from domains import issue_reopen as ir
    from domains import understanding_self_improvement as usi
    from domains import consumption_quality as cq

    a = _fresh_agent()
    agenda, left = _deferred_run(a)
    assert len(left) == 2, f"the low understanding gaps are deferred: {len(left)}"

    # pick a DEFERRED understanding gap that carries a real defect (a non-nominal
    # fragment: head_is_nominal==0).
    g = next(x for x in left
             if usi.gap_error_features(a, x) == (0.0, 1.0))
    print("\nACTS-IN-THE-LIVE-LOOP (understanding):")
    print("  deferred gap kind:", a.s.node(g)["attrs"].get("kind"),
          "features:", usi.gap_error_features(a, g))

    # RE-MEASURE its salience above the reopen bar and REOPEN (pass-through).
    a.s.set_attr(g, "salience", 0.9)
    ir.remeasure_salience(a, g)
    assert ir.should_reopen(a, g) is True, "re-measured-high gap reopens"
    res = ir.reopen_deferred(a, left)
    assert res["reopened"] == [g], f"only the re-measured-high gap reopens: {res['reopened']}"
    concern = res["concerns"][0]
    assert concern in ir.open_concerns(a), "the reopened concern is OPEN (unresolved) before firing"
    assert a.s.node(concern)["attrs"].get("resolved") is None, "not yet resolved"
    assert a.s.node(g)["attrs"].get("fixed") in (0.0, None) or float(
        a.s.node(g)["attrs"].get("fixed", 0.0)) == 0.0, "gap not yet fixed"

    # THE RUNNING LOOP acts: fire_reflexes trips the reflex, whose executor RUNS THE FIX.
    fired = a.fire_reflexes()
    print("  running-loop fire_reflexes:", fired)
    assert ir.REOPEN_REFLEX in fired, "the running loop's fire_reflexes trips the reopened-concern reflex"

    # the DEFECT IS CLEANED in the live loop: the concern resolved, the gap fixed.
    assert a.s.node(concern)["attrs"].get("pursued") == 1.0, "the loop took the concern up"
    assert a.s.node(concern)["attrs"].get("resolved") == 1.0, "the loop RESOLVED the concern"
    assert float(a.s.node(g)["attrs"].get("fixed", 0.0)) == 1.0, "the reopened gap is FIXED"
    assert ir.open_concerns(a) == [], "the loop's unresolved inbox drained"
    assert concern in ir.resolved_concerns(a), "the concern is now resolved"
    print("  concern resolved:", a.s.node(concern)["attrs"].get("resolved"),
          "gap fixed:", a.s.node(g)["attrs"].get("fixed"))

    # REAL, NOT A MARKER: the actual defect is gone — the fragment is DROPPED, the
    # nominal KEPT (the composer-authored nominal_filter the fix installed).
    kept, dropped = cq.nominal_filter(
        [{"surface": usi.FRAGMENT_SURFACE}, {"surface": usi.NOMINAL_SURFACE}], agent=a)
    kept_s = [c.get("surface") if isinstance(c, dict) else c for c in kept]
    dropped_s = [c.get("surface") if isinstance(c, dict) else c for c in dropped]
    print("  REAL EFFECT — dropped:", dropped_s, "kept:", kept_s)
    assert usi.FRAGMENT_SURFACE in dropped_s, "the fragment is DROPPED (real defect-cleaning)"
    assert usi.FRAGMENT_SURFACE not in kept_s, "the fragment is absent from the KEPT set"
    assert usi.NOMINAL_SURFACE in kept_s, "the genuine nominal is kept"

    # the closed concern no longer trips (the inbox drained via `resolved`).
    fired2 = a.fire_reflexes()
    print("  re-fire (drained):", fired2)
    assert ir.REOPEN_REFLEX not in fired2, "a resolved concern no longer trips the reflex"


# ===========================================================================
# ACTS-IN-THE-LIVE-LOOP (efficiency) — a reopened EFFICIENCY gap gets warm_once
# APPLIED (WordNet resident) via the running loop.
# ===========================================================================
def test_acts_in_the_live_loop_efficiency():
    _require()
    from domains import gap_prioritization as gp
    from domains import issue_reopen as ir
    from domains import performance_self_improvement as psi
    from domains import dictionary_lexicon as dl

    a = _fresh_agent()
    pg = psi.perceive_performance_gap(a)["gap"]
    gp.normalize_salience(a, pg)
    assert a.s.node(pg)["attrs"].get("kind") == "performance"
    warm_before = dl.is_wordnet_warm()
    print("\nACTS-IN-THE-LIVE-LOOP (efficiency):  warm before:", warm_before)

    concern = ir.reopen(a, pg)                       # pass the perf gap through
    assert concern in ir.open_concerns(a), "the reopened perf concern is OPEN before firing"

    fired = a.fire_reflexes()                         # the RUNNING loop runs the fix
    print("  running-loop fire_reflexes:", fired,
          "| warm after:", dl.is_wordnet_warm())
    assert ir.REOPEN_REFLEX in fired, "the running loop trips the reflex on the perf concern"
    assert a.s.node(concern)["attrs"].get("resolved") == 1.0, "the perf concern RESOLVED"
    assert float(a.s.node(pg)["attrs"].get("fixed", 0.0)) == 1.0, "the perf gap is FIXED"
    # REAL, NOT A MARKER: warm_once made WordNet RESIDENT (a measured effect).
    assert dl.is_wordnet_warm() is True, "warm_once APPLIED — WordNet is resident (real effect)"
    assert ir.open_concerns(a) == [], "the perf concern drained from the inbox"


# ===========================================================================
# DISCRIMINATIVE — a still-deferred gap is NOT fixed; a failed-#2 gap stays OPEN.
# ===========================================================================
def test_discriminative_still_deferred_not_fixed():
    _require()
    from domains import issue_reopen as ir

    a = _fresh_agent()
    _agenda, left = _deferred_run(a)                 # two deferred, at salience 0.2
    h = left[0]                                       # untouched, below the reopen bar
    assert ir.should_reopen(a, h) is False, "a low-salience deferred gap does not reopen"

    # never reopened -> no ReopenedConcern exists -> the running loop has nothing to act on.
    fired = a.fire_reflexes()
    print("\nDISCRIMINATIVE (still-deferred):  fire_reflexes:", fired)
    assert ir.REOPEN_REFLEX not in fired, "no concern -> the reopen reflex does not trip"
    assert ir.active_concerns(a) == [], "a still-deferred gap produced no live concern"
    # the deferred gap is NOT fixed by the running loop.
    assert float(a.s.node(h)["attrs"].get("fixed", 0.0)) == 0.0, \
        "the still-deferred gap is left UNFIXED by the running loop"


def test_discriminative_failed_verify_stays_open():
    _require()
    from domains import issue_reopen as ir

    a = _fresh_agent()
    # a reopened understanding concern whose gap has NO defect (head_is_nominal==1 AND
    # sense_fits_context==1): the driver diagnoses 'clean' -> fix None -> #2 not
    # accepted -> the fix FAILS, so the concern must stay OPEN.
    clean = a.s.add_node("CapabilityGap", {
        "kind": "understanding", "faculty": "clean_faculty",
        "head_is_nominal": 1.0, "sense_fits_context": 1.0,
        "salience": 0.9, "norm_salience": 0.9})
    concern = ir.reopen(a, clean)
    assert concern in ir.open_concerns(a), "the clean-gap concern starts OPEN"

    fired = a.fire_reflexes()
    print("\nDISCRIMINATIVE (failed-#2):  fire_reflexes:", fired,
          "resolved:", a.s.node(concern)["attrs"].get("resolved"))
    assert ir.REOPEN_REFLEX in fired, "the reflex trips (the concern is active + unresolved)"
    # the fix did NOT #2-verify -> the concern is NOT resolved -> it STAYS OPEN.
    assert a.s.node(concern)["attrs"].get("resolved") is None, "a failed fix does NOT resolve the concern"
    assert float(a.s.node(clean)["attrs"].get("fixed", 0.0)) == 0.0, "a failed fix does NOT mark the gap fixed"
    assert concern in ir.open_concerns(a), "the concern STAYS OPEN (the loop keeps pursuing it)"


# ===========================================================================
# MECHANICAL / PRECEDENT — the executor mirrors _question_pursue_advance: evaluate +
# apply, routing by the kind-keyed registry, no if/else deciding the repair.
# ===========================================================================
def test_mechanical_follows_question_pursue_precedent():
    import ast
    import textwrap
    from domains import issue_reopen as ir
    src = inspect.getsource(ir._reopened_concern_pursue_advance)

    # the routing is the kind-keyed driver registry (the twin of enact_in_order /
    # question_pursue's resolver-name lookup), NOT a Python branch that picks the fix.
    assert "_DRIVER_REGISTRY" in src, "dispatch is via the kind-keyed driver registry"
    assert "get(kind)" in src, "the driver is LOOKED UP by the gap's kind (a lookup, not a decision)"
    assert "driver(adapter, gap)" in src, "the executor CALLS the bound driver (evaluate + apply)"

    # the resolve is gated ONLY on the driver's OWN #2 verdict (accepted), not on a
    # Python decision about which fix or whether the defect is 'really' present.
    assert 'rec.get("accepted")' in src, "resolution is gated on the driver's #2 verdict, mechanically"

    # AST body audit (docstring stripped): the executable BODY must not itself name /
    # construct the repair — those decisions live in the driver's graph Programs. (The
    # docstring may describe them; the CODE must not perform them.)
    fn = ast.parse(textwrap.dedent(src)).body[0]
    if (fn.body and isinstance(fn.body[0], ast.Expr)
            and isinstance(fn.body[0].value, ast.Constant)):
        fn.body = fn.body[1:]                         # drop the docstring node
    body_src = ast.unparse(fn)
    for forbidden in ("diagnose", "select_fix", "nominal_filter", "sense_select",
                      "warm_once", "warm_wordnet"):
        assert forbidden not in body_src, \
            f"the executor BODY must not name the repair {forbidden!r} — that decision is the driver's graph Program"

    # guard-style ifs ONLY — no if/ELSE branching to decide the repair. Every `if` is
    # a continue-guard (skip-and-move-on) or the #2-verdict apply, none with an `else`
    # — the twin of _question_pursue_advance's `if fn is None: continue` /
    # `if status != 'dispatched': continue` guards. The repair CHOICE is never a Python
    # branch here; it is the driver's graph Programs, reached by the kind-keyed registry.
    ifs = [n for n in ast.walk(fn) if isinstance(n, ast.If)]
    assert ifs, "the executor uses guard-style ifs (sanity: the guards exist)"
    assert all(n.orelse == [] for n in ifs), \
        "no if/ELSE decides the repair — only continue-guards + the #2-verdict apply (no else branch)"

    # it is the reopened_concern_pursue reflex's registered response (the live-loop hook).
    reg_src = inspect.getsource(ir._ensure_seed)
    assert "_reopened_concern_pursue_advance" in reg_src and ir.REOPEN_REFLEX in reg_src, \
        "the executor is registered as the reopened-concern reflex's live-loop response"
