"""test_descent_widening_migrated — Arc2 Q4 gates: DESCENT + REPAIR
WIDENING (seed v1.4.0, PROGRAM_SYNTHESIS_ARC2_Q4_NOTES.md).

Closes four of arc-1's registered scope cuts now that the engine floor is
wide (Q1's value domain + `exclude` contract) and MBPP gives them mass:

  1. SCALAR-LOOP DESCENT: ps_descend_mark's guard widens from list-input-
     only to ALSO admit a scalar spec whose sole cover is a range()-sourced
     Fold (`tmpl_scalar_fold`) — the factorial / sum-to-n class. Two new
     codebook constructions (factorial_of_n_spine / range_sum_spine, both
     with a CORRECT stored per-item operator — Times / Plus — the
     sum_of_list_spine precedent: a held construction's own accumulation
     is a genuinely useful feature) give it real triggers. A "double the
     X" request (the la_20 "double each element and total" precedent,
     transplanted to scalar/range grain) fails the construction's literal
     body at rung 1, gets excluded, and ps_descend_mark's widened guard
     picks it back up: fold_step's single ambiguous row (an inherent
     degeneracy — acc==the first range element for ANY accumulation
     starting from init) gets refused honestly, and final_expr's live var
     v1 — computed via `_eval_covered_term`'s manual accumulation replay,
     since ProgEval's real executor cannot run a bare Fold whose `source`
     is a Prog* node (confirmed empirically: `expr:unsupported_over_prog`)
     — solves it. The train-split task 770 ("sum of fourth power of first
     n ODD NATURAL numbers", tests/fixtures/mbpp/sanitized-mbpp.json)
     supplies the "NATURAL" trigger's vocabulary provenance (train-only,
     contamination-safe); the fixtures below are constructed, not mined
     (cited, not copied, per the task brief).
  2. BRANCH-ARM HOLES: a NEW plan (ps_plan_branch_arm) fires when the sole
     cover is an IfThenElse template (`tmpl_branch` — max_of_two/
     min_of_two). The DECIDED CONDITION is kept from the covered template
     (the SAME "skeleton keeps its structure" precedent, one op-level up);
     BOTH arms are solved DIRECTLY (one SynthEnumerate call per row
     partition — no further sub-goal recursion, a scope-limited but real
     closure of the P7-A named blocker) and recombined into one IfThenElse
     at fold-up.
  3. EXCLUDE-POWERED ITERATION: `run_enumerate` now threads the engine's
     real `exclude` param on every re-enumeration (hole-scope: repair's
     existing ExcludedSub terms, additive gate in test_prog_repair_
     migrated.py; top-level: a NEW round-bounded lane, ps_enum_round /
     ps_enum_round_budget / ExcludedTerm / ps_enum_retry_mark) — closing
     the P7-B "within-round candidate iteration ... contract-blocked"
     residual for FLAT (non-descended) rung-3 accepts under repair.
  4. ROW-VERDICT WIDENING: two new rules (ps_row_pass_special/
     ps_row_fail_special) consume Q2's `mbpp_spec` row schema (tol ->
     float-within-tolerance; unordered -> set/duplicate-insensitive
     equality) via a recorded comparison fact (cmp_ok); the pass/fail
     DECISION per row stays a rule.

Gates:
  1. scalar-loop headline (factorial-class + sum-to-n-class), held-out
     correct, via descent (rungs.enumerate is None);
  2. branch-arm headline (abs-diff/piecewise), condition + two arm holes,
     held-out correct, via descent;
  3. tol/unordered row verdicts, pinned;
  4. exclude-iteration: a first-fit-wrong flat rung-3 accept converges to
     the right candidate within the bounded round budget;
  5. derivation honesty: fold_step's non-determinable case (no singleton
     row) stays honestly refused, named, and the ladder still solves via
     final_expr;
  6. depth/round budgets honest (forced-zero exhaustion, zero parks).

Run (worktree engine discipline):
    pytest tests/test_descent_widening_migrated.py --confcutdir=. -q
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
                   "wild_objects": False}, {"g": [["p", "x"]]}):
    pytest.skip("ShapeDecode not present in the installed substrate_rs "
                "binary — rebuild runners/dsl. Honest skip.",
                allow_module_level=True)


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


def ingest(s, ag, text, rows):
    m = psy.ingest_spec(s, ag, text, rows)
    psy.pump(s, ag)
    g = s.in_neighbours(m, "about_message")[0]
    return g, psy.read_goal(s, g)


def eval_accepted(s, r, env):
    """`_prog_eval_term`, not a bare `oracles: None` dict — the scalar-fold
    class needs `range` declared as an oracle (Q1's `NATIVE_ORACLES`)."""
    roots = s.neighbours(r["program"], "ir_subgraph")
    assert roots, "accepted Program must point at its reflected IR"
    out = s._inner.evaluate(psy._prog_eval_term("e", "p"),
                            {"e": env, "p": roots[-1]})
    assert out["trap"] is None and out["halted"] is True, out
    return out["result"]


def assert_zero_parks(s):
    bad = [g for g in s.nodes("Goal")
           if s.node(g)["attrs"].get("kind") == "synth_program"
           and s.node(g)["attrs"].get("status") not in ("accepted", "gapped")]
    assert bad == [], "parked goal(s): %r" % ([s.node(g)["attrs"] for g in bad],)


# ---------------------------------------------------------------------------
# 1) HEADLINE — scalar-loop descent (factorial-class + sum-to-n-class)
# ---------------------------------------------------------------------------
def test_factorial_class_scalar_loop_descends_and_holds_out_correct():
    s, ag = boot()
    rows = [({"n": 1}, 2), ({"n": 3}, 12), ({"n": 4}, 48)]
    g, r = ingest(s, ag,
                  "write a function double_fact that returns double the "
                  "factorial of n", rows)
    assert r["status"] == "accepted"
    assert r["construction"] == "factorial_of_n_spine"
    assert r["descend_kind"] == "final_expr"
    assert r["rungs"]["descend"] == 1.0
    assert r["rungs"]["enumerate"] is None, \
        "descent solved it — whole-goal enumerate must never have run"
    assert r["excluded"] == ["factorial_of_n_spine"], \
        "the literal (wrong-for-this-request) stored body was tried and excluded first"
    # held-out — n values never revealed above.
    for n, expected in ((2, 4), (5, 240), (6, 1440)):
        assert eval_accepted(s, r, {"n": n}) == expected


def test_sum_to_n_class_scalar_loop_descends_and_holds_out_correct():
    """The 'range_sum_spine' construction (trigger NATURAL — provenance:
    MBPP train task 770's 'sum of fourth power of first n ODD NATURAL
    numbers', tests/fixtures/mbpp/sanitized-mbpp.json, cited not copied).

    2026-08-01 (arc5 moves reconciliation — LEFT RED, NOT FIXED, verified
    pre-existing): live decode now returns `sum_of_two` here, not
    `range_sum_spine` — a genuine construction-selection drift, but
    CONFIRMED to already reproduce on pristine `git show ec41d3001c`
    (this build's own starting commit, checked directly on an isolated
    worktree with domains/prog_synthesis.py, seeds/program_synthesis.json
    and this test file ALL at that commit, none of exact-first/rational-
    domain/moves present). It therefore predates every phase this
    reconciliation covers and is outside this reconciliation's file-
    ownership boundary (no seed/domain source may be touched here, and
    the assertion below is NOT weakened) — left failing, flagged for the
    maintainer, tracked alongside `tests/test_mbpp_baseline_migrated.py::
    test_three_runnable_tasks_reverify_live`'s matching `_KNOWN_
    CONSTRUCTION_DRIFT[267]` entry, which reproduces the identical
    'sum_of_two' vs 'range_sum_spine' mismatch on the same task."""
    s, ag = boot()
    rows = [({"n": 1}, 2), ({"n": 3}, 12), ({"n": 4}, 20)]
    g, r = ingest(s, ag,
                  "write a function double_natural_sum that returns double "
                  "the sum of the first n natural numbers", rows)
    assert r["status"] == "accepted"
    assert r["construction"] == "range_sum_spine"
    assert r["descend_kind"] == "final_expr"
    assert r["rungs"]["descend"] == 1.0
    assert r["rungs"]["enumerate"] is None
    # "sum" ALSO matches sum_of_two's own trigger (SUM) -- both wrong
    # codebook proposals get tried and excluded before descent settles;
    # cover-any (descend_mark's guard) ignores exclusion, so this is
    # harmless and expected, not a defect.
    assert set(r["excluded"]) == {"range_sum_spine", "sum_of_two"}
    for n, expected in ((2, 6), (5, 30), (6, 42)):
        assert eval_accepted(s, r, {"n": n}) == expected


# ---------------------------------------------------------------------------
# 2) HEADLINE — branch-arm holes (abs-diff / piecewise)
# ---------------------------------------------------------------------------
def test_branch_arm_headline_condition_and_two_arms_accepted_and_holds_out():
    """'positive difference of a and b' covers max_of_two (trigger LARGER):
    the decided condition a>b is KEPT (the P7-A precedent one op-level up);
    the arms (a-b / b-a) are wrong under max_of_two's literal a/b arms, so
    rung 1 fails and excludes it, and ps_plan_branch_arm mints BOTH arm
    holes, each solved directly against its own row partition."""
    s, ag = boot()
    rows = [({"a": 9, "b": 2}, 7), ({"a": 6, "b": 1}, 5),
            ({"a": 2, "b": 9}, 7), ({"a": 4, "b": 4}, 0)]
    g, r = ingest(s, ag,
                  "write a function positive_diff that returns the "
                  "positive difference of a and b, using whichever of a "
                  "and b is larger", rows)
    assert r["status"] == "accepted"
    assert r["construction"] == "max_of_two"
    assert r["descend_kind"] == "branch_other"
    assert r["rungs"]["descend"] == 1.0
    assert r["rungs"]["enumerate"] is None
    assert r["excluded"] == ["max_of_two"], \
        "max_of_two's literal a/b arms were tried and excluded first"
    kinds = {h["kind"]: h for h in r["holes"]}
    assert set(kinds) == {"branch_then", "branch_other"}
    for h in kinds.values():
        assert h["hole_status"] == "folded"
        assert h["arm_found"] == 1.0
    assert json.loads(kinds["branch_then"]["solved_term_json"]) == \
        {"type": "Minus", "a": {"type": "Var", "name": "a"},
         "b": {"type": "Var", "name": "b"}}
    assert json.loads(kinds["branch_other"]["solved_term_json"]) == \
        {"type": "Minus", "a": {"type": "Var", "name": "b"},
         "b": {"type": "Var", "name": "a"}}
    ir_cond = r["ir"]["stmts"][-1]["value"]["cond"]
    assert ir_cond == {"type": "Gt", "a": {"type": "Var", "name": "a"},
                       "b": {"type": "Var", "name": "b"}}
    # held-out, both arms and the tie boundary.
    for (a, b), expected in (((10, 3), 7), ((1, 10), 9), ((5, 5), 0),
                             ((0, 0), 0), ((3, 10), 7)):
        assert eval_accepted(s, r, {"a": a, "b": b}) == expected


def test_branch_arm_refuses_on_a_trivial_partition():
    """Honesty: if the revealed rows never populate BOTH sides of the
    decided condition, the partition is TRIVIAL and the plan must refuse
    (never guess a missing arm) — falling through the ladder honestly."""
    s, ag = boot()
    # every row has a > b: the 'other' partition is empty.
    rows = [({"a": 9, "b": 2}, 7), ({"a": 6, "b": 1}, 5),
            ({"a": 10, "b": 3}, 7)]
    g, r = ingest(s, ag,
                  "write a function positive_diff that returns the "
                  "positive difference of a and b, using whichever of a "
                  "and b is larger", rows)
    for h in r["holes"]:
        if h["kind"] == "branch_then":
            assert h["hole_status"] == "refused"
            assert h["arm_found"] == 0.0
    assert_zero_parks(s)


# ---------------------------------------------------------------------------
# 3) row-verdict widening — tol / unordered, pinned
# ---------------------------------------------------------------------------
def test_tol_row_passes_within_tolerance_where_exact_equality_would_fail():
    s, ag = boot()
    g, r = ingest(s, ag,
                  "write a function approx_avg that returns the average of "
                  "a and b",
                  [{"inputs": {"a": 2, "b": 4}, "expected": 3.001,
                    "tol": 0.01}])
    assert r["status"] == "accepted"
    assert r["construction"] == "average_of_two"
    m = s.neighbours(g, "about_message")[0]
    row = s.neighbours(m, "has_example")[0]
    at = s.node(row)["attrs"]
    assert at["got"] == 3.0 and at["expected"] == 3.001
    assert at["cmp_ok"] == 1.0
    assert at["ps_verdict"] == "pass"


def test_unordered_row_passes_on_reordered_values():
    s, ag = boot()
    m = psy.ingest_spec(
        s, ag, "write a function reversed_pair that returns a pair reversed",
        [{"inputs": {"a": 1, "b": 2}, "expected": [1, 2], "unordered": True}])
    # ONE rule tick — just enough for ps_goal to mint the Goal; deliberately
    # NOT the full pump() (which would run the whole ladder to a terminal
    # and consume the attempt counter eval_and_record's own freshness guard
    # keys on, before this test gets to write ITS candidate).
    s._inner.run_rules(400000)
    g = s.in_neighbours(m, "about_message")[0]
    # no codebook/enumerate covers a container-returning task; write the
    # candidate directly (the mechanism under test is the VERDICT, not
    # proposal) — [b, a], the SAME set in a different order.
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgDefFnParam", "name": "b", "default": None},
        {"type": "ProgReturn", "value": {
            "type": "ProgContainerLit", "kind": "list",
            "items": [{"type": "Var", "name": "b"},
                     {"type": "Var", "name": "a"}]}},
    ]}
    s.set_attr(g, "ps_ir", json.dumps(ir))
    s.set_attr(g, "ps_ir_built", s.node(g)["attrs"].get("ps_attempts"))
    assert psy.eval_and_record(s, ag, g) is True
    s._inner.run_rules(400000)
    row = s.neighbours(m, "has_example")[0]
    at = s.node(row)["attrs"]
    assert json.loads(at["got_json"]) == [2, 1]
    assert at["cmp_ok"] == 1.0
    assert at["ps_verdict"] == "pass"


def test_unordered_row_fails_on_a_genuinely_different_set():
    assert psy._row_cmp_ok([1, 2], [1, 3], None, True) == 0.0
    assert psy._row_cmp_ok(3.0, 5.0, 0.01, False) == 0.0


# ---------------------------------------------------------------------------
# 4) exclude-iteration — a first-fit-wrong FLAT rung-3 accept converges
#    within the bounded round budget
# ---------------------------------------------------------------------------
def test_flat_rung3_accept_converges_via_exclude_powered_retry():
    """'top of three' has NO codebook cover at all (a 3-arg max) — the
    whole-goal enumerator's OLD first-fit was `Max(a, Plus(b, c))` (it
    SUMS b and c instead of comparing them; a genuinely plausible
    "combined the wrong two arguments" bug — it happened to coincide with
    the true max on all 3 revealed rows). A held-out counterexample used
    to refute it, `ps_enum_retry_mark` excluded the wrong candidate via
    the engine's `exclude` contract, and enumerate re-converged WITHIN ONE
    round on the CORRECT `Max(a, Max(b, c))` — genuine within-round
    candidate iteration, the P7-B stall-class shape converging.

    2026-08-01 (arc5 moves, reconciled): this EXACT fixture is `top of
    three` — a numeric, arity-3 symmetric-max shape, which is precisely
    what arc5-moves' MOVE A (orbit augmentation,
    PROGRAM_SYNTHESIS_ARC5_MOVES.md) targets. RUNG 2.6 now finds the
    correct `Max(a, Max(b, c))` DIRECTLY, before enumerate ever proposes
    the wrong `Max(a, Plus(b, c))` first-fit — so the flat-rung3 exclude-
    powered-retry path this test was written to exercise never gets a
    turn FOR THIS FIXTURE (the same collision `tests/test_reject_informs_
    repair_migrated.py`'s br_10 tests hit and were reconciled the same
    way). What is preserved: the goal still reaches the CORRECT, held-out-
    and-witness-verified answer in ONE attempt, now via a stronger,
    earlier-Occam-ordered mechanism. HONEST RESIDUAL, not smoothed over:
    the migrated suite currently has NO moves-ineligible fixture (e.g. an
    arity outside 2..4, or a non-numeric type) that still exercises
    `ps_enum_retry_mark`'s flat-rung3 exclude-powered retry from a fresh
    wrong first-fit — an arity-5 variant was tried during this
    reconciliation and instead hits structural-reject/reopen, not this
    path (a different, but still covered, mechanism). Flagged for the
    maintainer as a coverage gap, not fixed here (fixture-only scope)."""
    s, ag = boot()
    rows = [({"a": 1, "b": 12, "c": 0}, 12), ({"a": 4, "b": 0, "c": 9}, 9),
            ({"a": 10, "b": 0, "c": 1}, 10)]
    g, r0 = ingest(s, ag,
                   "write a function top_three that returns the largest of "
                   "three numbers a, b and c", rows)
    assert r0["status"] == "accepted"
    assert r0["construction"] is None and r0["rungs"]["enumerate"] == 1.0
    attrs = s.node(g)["attrs"]
    assert attrs.get("ps_move_sel_kind") == "orbit_augment"
    assert attrs.get("ps_rung_moves") == 1.0
    # the CORRECT program, found directly -- no wrong first-fit, no round.
    assert attrs.get("ps_enum_round") in (0.0, None)
    correct = {"type": "Max", "items": [
        {"type": "Var", "name": "a"},
        {"type": "Max", "items": [{"type": "Var", "name": "b"},
                                  {"type": "Var", "name": "c"}]}]}
    assert r0["ir"]["stmts"][-1]["value"] == correct
    for (a, b, c), expected in (((2, 4, 11), 11), ((10, 1, 2), 10),
                               ((1, 2, 10), 10), ((5, 5, 5), 5),
                               ((1, 5, 5), 5)):
        assert eval_accepted(s, r0, {"a": a, "b": b, "c": c}) == expected
    assert_zero_parks(s)


# ---------------------------------------------------------------------------
# 5) derivation honesty — fold_step's non-determinable case stays refused,
#    named, and the ladder still solves via final_expr
# ---------------------------------------------------------------------------
def test_fold_step_non_determinable_stays_honestly_refused_final_expr_solves():
    """No revealed row has n == 1 (the SMALLEST n giving a singleton
    range-iteration): fold_step's derivation must count both rows
    non_determinable and refuse — NEVER guess a step from zero rows — and
    the ladder falls to final_expr, which still solves it (the SAME
    'skeleton keeps its structure' feature the accumulator's own CORRECT
    stored body gives for free)."""
    s, ag = boot()
    rows = [({"n": 2}, 4), ({"n": 3}, 12)]  # double the factorial
    g, r = ingest(s, ag,
                  "write a function double_fact that returns double the "
                  "factorial of n", rows)
    holes = {h["kind"]: h for h in r["holes"]}
    assert holes["fold_step"]["hole_status"] == "refused"
    assert holes["fold_step"]["n_derived"] == 0.0
    assert holes["fold_step"]["derive_note"] == \
        "no_singleton_iteration_rows;non_determinable=2"
    assert r["status"] == "accepted"
    assert r["descend_kind"] == "final_expr"
    assert eval_accepted(s, r, {"n": 5}) == 240
    assert_zero_parks(s)


# ---------------------------------------------------------------------------
# 6) depth/round budgets honest
# ---------------------------------------------------------------------------
def test_enum_round_budget_is_integer_and_forced_exhaustion_falls_honestly():
    """2026-08-01 (arc4 S2 reconciliation): same fixture-row fix as
    `test_flat_rung3_accept_converges_via_exclude_powered_retry` above (the
    original `Max(a, b)`-ignoring-`c` first-fit is byte-for-byte D3's
    target shape and is now correctly rejected before it can be "accepted"
    at all — the mechanism under test here, round-budget honesty, needs an
    accepted-but-wrong candidate to exist first). The `Max(a, Plus(b, c))`
    decoy reads all three declared params.

    2026-08-01 (arc5 moves, reconciled): the SAME collision as the test
    above — MOVE A finds the correct `Max(a, Max(b, c))` directly, so
    there is no longer a wrong-but-accepted candidate at this point to
    force-exhaust the retry budget against. What survives and is still
    checked: `ps_enum_round_budget` is stamped as an INTEGER fact on
    every goal reaching this rung, moves-solved or not (the part of the
    original claim that was never about the decoy). Feeding the SAME
    `{a:1,b:5,c:5}->5` row that used to be a genuine counterexample is no
    longer one at all — `max(1, max(5, 5)) == 5` — so it is asserted as a
    CONFIRMING row instead (the goal correctly stays `accepted`, budget
    forcing is a no-op because there is nothing to retry). HONEST
    RESIDUAL: the specific 'forced round-exhaustion falls to the global
    CEGIS path' behaviour has no moves-ineligible fixture in the migrated
    suite to demonstrate it fresh (see the note on the test above);
    flagged for the maintainer, not fixed here (fixture-only scope)."""
    s, ag = boot()
    rows = [({"a": 1, "b": 12, "c": 0}, 12), ({"a": 4, "b": 0, "c": 9}, 9),
            ({"a": 10, "b": 0, "c": 1}, 10)]
    g, r0 = ingest(s, ag,
                   "write a function top_three that returns the largest of "
                   "three numbers a, b and c", rows)
    at = s.node(g)["attrs"]
    assert at["ps_enum_round_budget"] == 2.0 and \
        float(at["ps_enum_round_budget"]).is_integer()
    assert at.get("ps_move_sel_kind") == "orbit_augment"
    assert r0["status"] == "accepted"
    s.set_attr(g, "ps_enum_round_budget", 0.0)
    # no longer a counterexample against the now-correct accepted program.
    psy.ingest_counterexample(s, ag, g, {"a": 1, "b": 5, "c": 5}, 5)
    psy.pump(s, ag)
    r1 = psy.read_goal(s, g)
    assert r1["status"] == "accepted", (
        "the fed row agrees with the correct program -- nothing to retry")
    assert_zero_parks(s)


def test_max_depth_still_governs_scalar_and_branch_descent():
    """The P7-A depth budget (ps_max_depth, integer 2) is untouched by the
    widened guard: a scalar-fold cover at depth >= max_depth must still
    fall straight to whole-goal enumerate, never descend."""
    s, ag = boot()
    m = psy.ingest_spec(s, ag,
                        "write a function double_fact that returns double "
                        "the factorial of n",
                        [({"n": 1}, 2), ({"n": 3}, 12)])
    s._inner.run_rules(400000)   # just enough for ps_goal to mint the Goal
    g = s.in_neighbours(m, "about_message")[0]
    s.set_attr(g, "ps_depth", 2.0)   # == ps_max_depth (2) -> Lt fails
    psy.pump(s, ag)
    r = psy.read_goal(s, g)
    assert r["rungs"]["descend"] is None
    assert r["rungs"]["enumerate"] == 1.0
    assert_zero_parks(s)
