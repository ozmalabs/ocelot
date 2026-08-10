"""test_prog_descent_migrated — P7-A gates: RECURSIVE ShapeDecode descent
(seed v1.2.0, PROGRAM_SYNTHESIS_P7_PREREG.md H7a).

The governing insight, gated: "shapedecode will tell you what is going on" —
the decode's coverage assignment IS the plan; partial cover is
segmentation-by-recognition; each residual span becomes a sub-goal one grain
finer; only a residual that survives every grain reaches the enumerator;
execution verdict at every level.

Gates (prereg §2):
  1. HEADLINE: three real battery ids frozen `gapped:enumerate_failed`
     (la_20_double_each_total, ms_09_count_then_double, ms_04_avg_by_parts)
     now accept via descent — held-out rows correct, rung provenance shows
     descend + hole solve and NOT whole-goal enumerate;
  2. derived-row correctness: la_20's fold_step hole derives EXACTLY the
     hand-computed one-iteration unroll (acc=0, x=5) → 10; the [] and
     [1,2,3] rows are counted non-determinable, never guessed;
  3. boundaries-from-decode: the goal's cover/residual facts equal an
     independently evaluated ShapeDecode; the hole sub-spec's tokens ARE
     the decode residual (no Python cut);
  4. depth budget honest: ps_depth ≥ ps_max_depth never descends;
  5. sub-goal failure → the outer goal falls to the next rung honestly
     (descend → whole-goal enumerate → gap), and a descent sub-goal's gap
     files NO SelfConcern (the outer goal files its own);
  6. Occam guards: codebook-covered requests never descend; scalar-row
     requests never descend (the whole-goal enumerator keeps them —
     byte-compat with the P6.5 paths);
  7. paired identity: a sample of currently-passing battery rows reproduces
     its frozen MAIN-POSTFIX outcome under the descent seed.

Run (worktree engine discipline):
    pytest tests/test_prog_descent_migrated.py --confcutdir=. -q
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains import prog_synthesis as psy  # noqa: E402


def _term_live(term, env) -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(term, env)
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live({"type": "ShapeDecode", "goal": {"type": "Var", "name": "g"},
                   "beam": 1, "max_steps": 2, "cand_k": 1, "field": "",
                   "wild_objects": False}, {"g": [["p", "x"]]}) or \
   not _term_live({"type": "ProgEval",
                   "prog": {"type": "ProgSeq", "stmts": []},
                   "env": None, "oracles": None, "fuel": 5, "field": ""}, {}):
    pytest.skip("ShapeDecode/ProgEval not present in the installed "
                "substrate_rs binary — rebuild runners/dsl. Honest skip.",
                allow_module_level=True)

_TASKS_PATH = os.path.join(ROOT, "tests", "fixtures",
                           "prog_synthesis_battery", "tasks.json")
_ARTIFACT_PATH = os.path.join(ROOT, "results", "prog_synthesis_battery.json")

with open(_TASKS_PATH) as _f:
    _TASKS = {t["id"]: t for t in json.load(_f)["tasks"]}
with open(_ARTIFACT_PATH) as _f:
    _ART = json.load(_f)
_FROZEN = {r["task_id"]: r for r in _ART["arms"]["main_postfix"]["rows"]}


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


def run_task(tid):
    t = _TASKS[tid]
    s, ag = boot()
    ex = [(r["inputs"], r["expected"]) for r in t["example_rows"]]
    m = psy.ingest_spec(s, ag, t["request_text"], ex)
    psy.pump(s, ag)
    goals = s.in_neighbours(m, "about_message")
    assert len(goals) == 1
    return s, ag, psy.read_goal(s, goals[0]), t


def eval_accepted(s, r, env):
    roots = s.neighbours(r["program"], "ir_subgraph")
    assert roots, "accepted Program must point at its reflected IR"
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
         "env": {"type": "Var", "name": "e"}, "oracles": None,
         "fuel": 10000, "field": ""},
        {"e": env, "p": roots[-1]})
    assert out["trap"] is None and out["halted"] is True, out
    return out["result"]


# the cited targets (prereg H7a secondary; chosen from the artifact BEFORE
# implementation) — all three frozen gapped:enumerate_failed.
CITED = ("la_20_double_each_total", "ms_09_count_then_double",
         "ms_04_avg_by_parts")


# ---------------------------------------------------------------------------
# 1) HEADLINE — battery-gapped tasks now accept via descent
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tid", CITED)
def test_headline_battery_gapped_task_accepts_via_descent(tid):
    fr = _FROZEN[tid]
    assert fr["status"] == "gapped" and \
        fr["gap_reason"] == "enumerate_failed", \
        "the cited id must be a REAL frozen gap (baseline = list of ids)"
    s, ag, r, t = run_task(tid)
    assert r["status"] == "accepted", (tid, r["gap_reason"])
    # rung provenance: descent solved it; whole-goal enumerate NEVER ran.
    assert r["rungs"]["descend"] == 1.0
    assert r["rungs"]["enumerate"] is None
    assert r["descend_kind"] == "final_expr"
    # the skeleton instantiated a COVERED construction (provenance).
    assert r["construction"] in r["cover_parts"]
    # held-out rows (never shown to the pipeline) — execution verdict.
    for ho in t["held_out_rows"]:
        assert eval_accepted(s, r, ho["inputs"]) == ho["expected"], (tid, ho)
    # the hole's sub-goal minted its own Program; the OUTER goal exactly one.
    progs = s.neighbours(r["goal"], "accepted_program")
    assert len(progs) == 1


def test_headline_solved_hole_ran_the_same_ladder_one_grain_finer():
    """The recursion is literal: the hole is a Goal{kind:synth_program}
    with its OWN integer counters (collision-free by construction) whose
    spec rows are the DERIVED rows, solved by hole-scoped enumeration."""
    s, ag, r, t = run_task("ms_09_count_then_double")
    holes = [h for h in r["holes"] if h.get("kind") == "final_expr"]
    assert len(holes) == 1 and holes[0]["hole_status"] == "folded"
    # walk the FOLDED hole → sub_message → sub_goal (the fold_step hole's
    # sub-goal may ALSO have accepted on its weak derived rows — fold-up
    # refused it; only the folded hole's solve reached the outer accept).
    folded = [h for h in s.neighbours(r["goal"], "has_hole")
              if s.node(h)["attrs"].get("hole_status") == "folded"]
    assert len(folded) == 1
    sub_goals = []
    for m2 in s.neighbours(folded[0], "sub_message"):
        sub_goals.extend(s.in_neighbours(m2, "about_message"))
    assert len(sub_goals) == 1
    g2a = s.node(sub_goals[0])["attrs"]
    assert g2a["status"] == "accepted"
    assert g2a["kind"] == "synth_program"
    assert g2a["ps_depth"] == 1.0, "one grain finer"
    assert g2a["ps_rung_enumerate"] == 1.0, "hole-scoped enumeration"
    # fresh counters: the sub-goal's attempts are its own, inside its budget.
    assert g2a["ps_attempts"] <= g2a["ps_budget"]


# ---------------------------------------------------------------------------
# 2) derived-row correctness (pinned hand-computed truth)
# ---------------------------------------------------------------------------
def test_fold_step_derived_rows_equal_hand_computed_truth():
    """la_20 examples: [1,2,3]→12, [5]→10, []→0. The fold_step hole
    (total_of_list: Fold init 0) derives EXACTLY the one-iteration unroll
    (acc=0, x=5)→10; [] (zero iterations) and [1,2,3] (unpinned
    intermediate states) are counted non-determinable — never guessed."""
    s, ag, r, t = run_task("la_20_double_each_total")
    fold_holes = [h for h in r["holes"] if h.get("kind") == "fold_step"]
    assert len(fold_holes) == 1, "the fold_step plan ran first (finest grain)"
    h = fold_holes[0]
    assert h["n_derived"] == 1.0
    assert json.loads(h["derived_rows_json"]) == [
        {"inputs": {"acc": 0, "x": 5}, "expected": 10}]
    assert h["derive_note"].startswith("ok")
    assert "non_determinable=2" in h["derive_note"]
    # and the outer rows had the final say: the weak 1-row sub-solve
    # (Lit 10 fits the derived row) was REFUSED by fold-up on [1,2,3].
    assert h["hole_status"] == "foldup_failed"


# ---------------------------------------------------------------------------
# 3) boundaries come from the decode (never a Python cut)
# ---------------------------------------------------------------------------
def test_hole_boundaries_are_the_decode_assignment():
    s, ag, r, t = run_task("la_20_double_each_total")
    # independent evaluation of the SAME decode the rules bind.
    goal_attrs = s.node(r["goal"])["attrs"]
    skel = [list(x) for x in goal_attrs["skeleton"]]
    out = s._inner.evaluate(
        {"type": "ShapeDecode", "goal": {"type": "Lit", "value": skel},
         "beam": 3, "max_steps": 8, "cand_k": 3, "field": "",
         "wild_objects": False}, {})
    want_parts = [str(p) for p in out["ordered_parts"]]
    want_residual = [str(x) for rel in out["residual"] for x in rel]
    assert r["cover_parts"] == want_parts == ["total_of_list"]
    assert r["residual_tokens"] == want_residual
    # the sub-spec's tokens ARE the residual spans — assert the plan facts.
    for h in s.neighbours(r["goal"], "has_hole"):
        for m2 in s.neighbours(h, "sub_message"):
            toks = [str(x) for x in s.node(m2)["attrs"]["ps_tokens"]]
            assert toks == want_residual


# ---------------------------------------------------------------------------
# 4) depth budget honest
# ---------------------------------------------------------------------------
def test_depth_budget_blocks_descent_honestly():
    """2026-08-01 arc4 S4 reconciliation: the MECHANISM this gate proves is
    depth-budget honesty — at `ps_depth >= max_depth`, descent must never
    fire, and the goal must fall through to whole-goal enumerate instead.
    That mechanism is unchanged and re-verified below (`rungs["descend"] is
    None` + `rungs["enumerate"] == 1.0`, the latter newly asserted here to
    make the fall-through itself, not just its outcome, a checked fact).
    What DID change: `la_20_double_each_total` ("double each item then
    total") used to gap at the whole-goal enumerate stage (no iteration
    primitive existed at all); S4 added `SumList` (class A, list-reduction:
    `Sum{source,item,Var(item)}`, PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md §2), and
    doubling-then-summing is algebraically `2 * sum(items)` — directly
    expressible as `Times(2, SumList(items))` with NO descent needed at all.
    This is a genuine capability gain (verified against held-out rows below,
    so it is a real solve, not an overfit) — the outcome pin moves from
    `gapped` to `accepted` to match it."""
    t = _TASKS["la_20_double_each_total"]
    s, ag = boot()
    ex = [(r["inputs"], r["expected"]) for r in t["example_rows"]]
    m = psy.ingest_spec(s, ag, t["request_text"], ex)
    s.set_attr(m, "ps_depth", 2.0)   # at the integer budget (max_depth 2)
    psy.pump(s, ag)
    g = s.in_neighbours(m, "about_message")[0]
    r = psy.read_goal(s, g)
    assert r["rungs"]["descend"] is None, "no descent at exhausted depth"
    assert r["rungs"]["enumerate"] == 1.0, \
        "blocked descent must fall through to whole-goal enumerate"
    assert r["status"] == "accepted"
    for ho in t["held_out_rows"]:
        assert eval_accepted(s, r, ho["inputs"]) == ho["expected"]


# ---------------------------------------------------------------------------
# 5) sub-goal failure → honest fall-through; no sub-goal SelfConcern
# ---------------------------------------------------------------------------
def test_failed_descent_falls_to_enumerate_then_gap():
    """2026-08-01 arc4 S4 reconciliation — RE-PINNED off the frozen
    `la_06_product_all` fixture (3 example rows) to an equivalent synthetic
    spec with more rows, same request shape. Why: S4 widened the whole-goal
    enumerator with list-reduction ops (`SumList`/`MaxList`/`MinList`, see
    PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md §2), and on the ORIGINAL 3-row
    `la_06_product_all` fixture this incidentally lets whole-goal enumerate
    find `Last(items) * Min(2, Count(items))` — a candidate that fits those
    3 rows by COINCIDENCE (verified: it disagrees with `la_06`'s own
    held-out rows) but is not the correct "product of a list" function.
    Product-of-a-list needs a multiply-reduce primitive S4 did NOT add (only
    Sum/Max/Min reductions landed — S4 Notes' own honest-residuals §4.1 names
    exactly this open sub-case of class A: "task 98's product-then-divide").
    Rather than assert on that coincidental fit (which would silently start
    pinning a wrong accept as this gate's expected behaviour), the row set
    below is widened (varied lengths/signs) so NO accidental fit remains
    reachable and the true mechanism under test — "a bad decomposition
    (`product_of_two`, an a/b template that matches the trigger word
    'product' but not the list-shaped request) dies at the cheapest level;
    the ladder honestly falls through descend -> enumerate -> gap" — is
    exercised exactly as PROGRAM_SYNTHESIS_P7A.md's original la_06 gate
    intended. Verified live: descent still tries `product_of_two` and its
    hole still fails on contradictory derived rows (v1=1 maps to every
    different expected output) — the SAME bad-decomposition mechanism,
    unaffected by S4; only the top-level fixture needed widening."""
    REQUEST = ("Write a function product_all that returns the product of a "
              "list of numbers.")
    ROWS = [({"items": [1, 2, 3]}, 6), ({"items": [2, 5]}, 10),
            ({"items": [4]}, 4), ({"items": [1, 1, 1, 1, 1]}, 1),
            ({"items": [3, 3]}, 9), ({"items": [2, 2, 2]}, 8),
            ({"items": [5, -1]}, -5)]
    s, ag = boot()
    m = psy.ingest_spec(s, ag, REQUEST, ROWS)
    psy.pump(s, ag)
    g = s.in_neighbours(m, "about_message")[0]
    r = psy.read_goal(s, g)
    assert r["rungs"]["descend"] == 1.0, "descent was tried"
    assert r["rungs"]["enumerate"] == 1.0, "then fell to whole-goal enumerate"
    # 2026-08-02 (ARC 6 TIER 0, reconciled — IMPROVEMENT DIRECTION).
    # This gate used to end `gapped:enumerate_failed`, and its own docstring
    # above says exactly why: *"Product-of-a-list needs a multiply-reduce
    # primitive S4 did NOT add (only Sum/Max/Min reductions landed — S4
    # Notes' own honest-residuals §4.1 names exactly this open sub-case of
    # class A: 'task 98's product-then-divide')."*
    #
    # `op:ProdList` (arc-6 tier 0 — the shipped `Prod` Term exposed as the
    # `SumList` twin, ZERO new `TermNode` variants) IS that primitive.  The
    # whole-goal enumerate rung now SOLVES this spec, so the terminal status
    # moves `gapped` -> `accepted`.
    #
    # THE MECHANISM THIS GATE ACTUALLY TESTS IS UNCHANGED and is still
    # asserted above and below: the bad `product_of_two` decomposition still
    # dies at the cheapest level (its `final_expr` hole still fails on
    # contradictory derived rows) and the ladder still falls through
    # descend -> whole-goal enumerate.  Only what enumerate then FINDS
    # changed.
    #
    # The accept is proven CORRECT rather than assumed — the docstring's own
    # warning ("which would silently start pinning a wrong accept as this
    # gate's expected behaviour") applies to this reconciliation too, so the
    # program is swept on CONSTRUCTED inputs that are not in `ROWS`.
    assert r["status"] == "accepted"
    assert r["construction"] == "product_of_two", \
        "the same bad decomposition (trigger word 'product') as the " \
        "original la_06 gate"
    hole_status = {h["kind"]: h["hole_status"] for h in r["holes"]}
    assert hole_status.get("final_expr") == "failed"
    ret = r["ir"]["stmts"][-1]["value"]
    assert ret["type"] == "Prod", ret
    for probe in ([7, 8], [2, 3, 4], [10], [1, -2, 3], [0, 5], [6, 6, 6]):
        want = 1
        for x in probe:
            want *= x
        got = s._inner.evaluate(ret, {"items": probe})
        assert got == want, "accepted program is wrong on %r: %r != %r" % (
            probe, got, want)
    # No SelfConcern is filed for a goal that ACCEPTS — the outer goal no
    # longer gaps.  (Pre-arc6 this asserted exactly one, the outer goal's;
    # the descent sub-goal's gap is internal working state either way,
    # per the ps_gap_file depth guard.)
    assert len(s.nodes("SelfConcern")) == 0


def test_weak_derived_rows_are_caught_by_the_outer_verdict_terminally():
    """la_10_count_positives: the derived rows underdetermine the hole
    (one singleton). Whatever the ladder does, the goal must land on a
    TERMINAL status — an accept is judged by the held-out rows downstream
    (the §2.2 class at descent grain), a refusal gaps; a park is a defect."""
    s, ag, r, t = run_task("la_10_count_positives")
    assert r["status"] in ("accepted", "gapped"), r["status"]
    assert r["rungs"]["descend"] == 1.0


# ---------------------------------------------------------------------------
# 6) Occam guards
# ---------------------------------------------------------------------------
def test_covered_requests_never_descend():
    s, ag = boot()
    m = psy.ingest_spec(
        s, ag,
        "write a function sum_of_list that returns the tally of a list of "
        "numbers",
        [({"items": [1, 2, 3, 4]}, 10), ({"items": [5]}, 5),
         ({"items": []}, 0)])
    psy.pump(s, ag)
    r = psy.read_goal(s, s.in_neighbours(m, "about_message")[0])
    assert r["status"] == "accepted"
    assert r["rungs"]["descend"] is None, \
        "a codebook-covered request must never descend"
    assert r["holes"] == []


def test_scalar_row_requests_never_descend():
    """la_15_sum_to_n: scalar rows (the whole-goal enumerator's admissible
    domain) — descent must not touch it; the P6.5 decoy→enumerate path
    reproduces its frozen MAIN-POSTFIX outcome."""
    fr = _FROZEN["la_15_sum_to_n"]
    s, ag, r, t = run_task("la_15_sum_to_n")
    assert r["rungs"]["descend"] is None
    assert r["status"] == "accepted"
    assert fr["outcome"] == "accepted_holdout_ok"
    for ho in t["held_out_rows"]:
        assert eval_accepted(s, r, ho["inputs"]) == ho["expected"]


# ---------------------------------------------------------------------------
# 7) paired identity on currently-passing rows
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tid", ("ex_01_pick_larger", "la_03_running_sum",
                                 "br_01_top_pick", "ms_03_sum_then_square"))
def test_paired_identity_currently_passing_row_reproduces(tid):
    fr = _FROZEN[tid]
    assert fr["outcome"] == "accepted_holdout_ok"
    s, ag, r, t = run_task(tid)
    assert r["status"] == fr["status"] == "accepted"
    assert r["rungs"]["descend"] is None
    for ho in t["held_out_rows"]:
        assert eval_accepted(s, r, ho["inputs"]) == ho["expected"]


# ---------------------------------------------------------------------------
# 8) Arc2-Q4 — the widened scope guard (additive; the headline scalar-loop/
#    branch-arm gates live in tests/test_descent_widening_migrated.py)
# ---------------------------------------------------------------------------
def test_scalar_and_branch_structural_marks_are_stamped_correctly():
    """`_normalise_fold_marks` (Arc2-Q4) stamps tmpl_scalar_fold/tmpl_branch
    alongside the P7-A tmpl_fold, from the SAME structural parse. Every
    PRE-Q4 codebook entry gets 0.0 for both new attrs (never absent, never
    accidentally true) — this is what makes ps_descend_mark's widened Or
    byte-identical for them."""
    s, ag = boot()
    marks = {}
    for n in s.nodes("ShapeSignature"):
        at = s.node(n)["attrs"]
        if at.get("kind") == "code_write_construction":
            marks[at["name"]] = (at.get("tmpl_fold"), at.get("tmpl_scalar_fold"),
                                 at.get("tmpl_branch"))
    assert marks["factorial_of_n_spine"] == (1.0, 1.0, 0.0)
    assert marks["range_sum_spine"] == (1.0, 1.0, 0.0)
    assert marks["max_of_two"] == (0.0, 0.0, 1.0)
    assert marks["min_of_two"] == (0.0, 0.0, 1.0)
    # every PRE-Q4 fold/plain-expression construction: the new attrs are
    # false, never true — the widened Or's right arm never fires for them.
    for name in ("total_of_list", "count_of_list", "sum_of_two",
                 "product_of_two", "abs_value", "average_of_two"):
        _, scalar_fold, branch = marks[name]
        assert scalar_fold == 0.0 and branch == 0.0, name


def test_a_plain_scalar_cover_without_either_mark_still_never_descends():
    """Occam safety: a request covered ONLY by a plain scalar-expression
    construction (sum_of_two — neither tmpl_scalar_fold nor tmpl_branch)
    must still fall to the whole-goal enumerator, exactly as pre-Q4 — the
    widened guard's new Or-arm must not admit constructions it wasn't
    built for."""
    s, ag = boot()
    m = psy.ingest_spec(s, ag, "write a function combine that returns the "
                                "sum of a and b",
                        [({"a": 2, "b": 9}, 11), ({"a": 7, "b": 3}, 10)])
    psy.pump(s, ag)
    r = psy.read_goal(s, s.in_neighbours(m, "about_message")[0])
    assert r["status"] == "accepted"
    assert r["construction"] == "sum_of_two"
    assert r["rungs"]["descend"] is None
    assert r["holes"] == []
