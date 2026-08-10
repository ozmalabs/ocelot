"""test_prog_repair_migrated — P7-B gates: TRACE-GUIDED LOCAL REPAIR
(seed v1.3.0, PROGRAM_SYNTHESIS_P7_PREREG.md H7b).

The governing insight, applied to DIAGNOSIS: "ShapeDecode tells you what is
going on" — a failing row's trace, compared against expectations DERIVED by
descent's own row-derivation machinery, localizes the fault to a
statement/hole; repair re-opens ONLY that hole (the counterexample propagates
INTO the hole's derived row set — this is what kills first-fit overfitting,
P7-A residual 1) instead of re-proposing the whole plan.

Protocol note (eval-subset coverage is part of every claim, §0): the verify
loop below is the standard CEGIS oracle protocol — after an accept, held-out
rows are checked and the FIRST failing one is fed back to the loop as a
counterexample (`ingest_counterexample`, mechanical). "Converts to
accepted_holdout_ok" therefore means: with k failing rows revealed one at a
time, the final accept passes ALL held-out rows INCLUDING those never
revealed (for la_10, held-out row 2 is never fed and passes).

Gates (task spec, P7-B):
  1. HEADLINE: P7-A's 4 holdout_fail ids re-run end-to-end — la_10 converts
     to accepted_holdout_ok via repair (skeleton never re-proposed); la_11 /
     la_21 / la_29 reach HONEST documented terminals (gapped:
     enumerate_failed) — the live-var abstraction provably cannot fit their
     held-out rows (measured in-gate: two held-out rows share live-var
     inputs with different outputs, or conflict with an example row), and
     the needed fold bodies are outside the enumerator's op/const reach
     (parity has no op; 10 is not a reachable const) — gate what IS;
  2. LOCALITY: the repair provenance proves the skeleton was NOT re-proposed
     (covered statements' IR canonically identical on the old vs new
     Program; only the localized hole's sub-IR differs; ps_attempts and the
     exclusion set untouched; the decode ran once);
  3. counterexample-into-hole: the repair hole's derived rows include the
     propagated row with pinned values;
  4. localization honesty: a goal with NO derivable expectation split (a
     rung-1 codebook accept — no skeleton/hole) refuses localization and the
     UNTOUCHED global CEGIS path completes the repair (fresh attempt →
     CounterExample → exclusion → re-proposal → accept);
  5. fold_step repair: a SINGLETON counterexample row localizes INTO a fold
     body via the one-iteration unroll (descent's derivation, reused); the
     second derived row kills the Lit-constant first-fit; ExcludedSub +
     enumerator input-shift facts recorded (the multi-candidate closure);
  6. budget honesty: integer repair budget on its own counter lane;
     exhaustion falls back to the global path then an honest terminal;
     ZERO parks in every scenario (the P6.5 regression class);
  7. attempts accounting (H7b evidence): post-failure work under repair <
     what global re-proposal needs, both measured;
  8. repair lane inert without a counterexample (paired identity).

Run (worktree engine discipline):
    pytest tests/test_prog_repair_migrated.py --confcutdir=. -q
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

# P7-A's 4 descent-era holdout_fail ids (PROGRAM_SYNTHESIS_P7A.md §4) — all
# frozen gapped:enumerate_failed in MAIN-POSTFIX (descent flipped them to
# accepted_holdout_fail; this track's primary targets).
CONVERTS = "la_10_count_positives"
# 2026-08-01 arc4 S4 reconciliation: `la_21_count_zeros` REMOVED from this
# tuple. P7-B proved it unreachable at live-var grain (no function of v1 fits
# the contradictory rows) -- that proof is unaffected -- but S4 landed
# `FilterList`/`Count` (class B, list-filter) as new enumerable ops, and the
# hole re-solve now expresses "count of zeros" directly as
# `Count(FilterList(items, x, x==0))`, a shape that did not exist in the
# enumerator's reach when P7-B was gated. Verified live: la_21 now converts
# to accepted_holdout_ok via the SAME repair mechanism as la_10 (two
# counterexample rounds; see
# test_headline_la21_converts_to_holdout_ok_via_s4_capability_gain below) --
# a genuine capability gain, not a mechanism regression. la_11/la_29 remain
# genuinely unreachable (parity has no op; the constant 10 is unreachable),
# reconfirmed live.
HONEST_TERMINALS = ("la_11_count_evens", "la_29_count_above_ten")


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
    return s, ag, goals[0], t


def eval_accepted(s, r, env):
    roots = s.neighbours(r["program"], "ir_subgraph")
    assert roots, "accepted Program must point at its reflected IR"
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
         "env": {"type": "Var", "name": "e"}, "oracles": None,
         "fuel": 10000, "field": ""},
        {"e": env, "p": roots[-1]})
    return out["result"], (out["trap"] is None and out["halted"] is True)


def verify_loop(s, ag, g, t, max_rounds=3):
    """The CEGIS oracle protocol: check held-out rows against the accepted
    program; feed the FIRST failing one back as a counterexample; repeat.
    Returns (final read_goal, fed rows)."""
    fed = []
    for _ in range(max_rounds):
        r = psy.read_goal(s, g)
        if r["status"] != "accepted":
            return r, fed
        fail = None
        for ho in t["held_out_rows"]:
            got, ok = eval_accepted(s, r, ho["inputs"])
            if not ok or got != ho["expected"]:
                fail = ho
                break
        if fail is None:
            return r, fed
        psy.ingest_counterexample(s, ag, g, fail["inputs"], fail["expected"])
        fed.append(fail)
        psy.pump(s, ag)
    return psy.read_goal(s, g), fed


def assert_zero_parks(s):
    """The P6.5 discipline at repair grain: every synth_program goal —
    outer, descent sub, repair sub — ends on a TERMINAL status."""
    bad = []
    for g in s.nodes("Goal"):
        at = s.node(g)["attrs"]
        if at.get("kind") != "synth_program":
            continue
        if at.get("status") not in ("accepted", "gapped"):
            bad.append((g, at.get("status")))
    assert not bad, "parked goals: %r" % (bad,)


def synth_goals(s):
    return [g for g in s.nodes("Goal")
            if s.node(g)["attrs"].get("kind") == "synth_program"]


# ---------------------------------------------------------------------------
# 1) HEADLINE — the 4 P7-A holdout_fail ids
# ---------------------------------------------------------------------------
def test_headline_la10_converts_to_holdout_ok_via_repair():
    """The Lit/len-overfit class converts: ONE failing held-out row fed back
    localizes to the folded final_expr hole, the row enters the hole's
    derived set, the re-solve fits all four, and the OTHER held-out row —
    never revealed to the loop — passes too. No global re-proposal."""
    fr = _FROZEN[CONVERTS]
    assert fr["status"] == "gapped" and fr["gap_reason"] == "enumerate_failed"
    s, ag, g, t = run_task(CONVERTS)
    r0 = psy.read_goal(s, g)
    assert r0["status"] == "accepted", "P7-A descent accepts (then holdout-fails)"
    r, fed = verify_loop(s, ag, g, t)
    assert r["status"] == "accepted"
    assert len(fed) == 1, "exactly one counterexample round"
    # accepted_holdout_ok: ALL held-out rows pass, including the unfed one.
    for ho in t["held_out_rows"]:
        assert eval_accepted(s, r, ho["inputs"]) == (ho["expected"], True)
    # repair provenance: localized to the final_expr hole, one repair
    # attempt on the SEPARATE integer lane; global lane untouched.
    assert r["repair"]["localized"] == 1.0
    assert r["repair"]["kind"] == "final_expr"
    assert r["repair"]["attempts"] == 1.0
    assert r["attempts"] == 1.0, "no global re-proposal: ps_attempts unchanged"
    assert r["rungs"]["enumerate"] is None, "whole-goal enumerate never ran"
    assert_zero_parks(s)


@pytest.mark.parametrize("tid", HONEST_TERMINALS)
def test_headline_unreachable_ids_reach_honest_terminals(tid):
    """Gate what IS: for these three the fix is NOT determinable at any
    grain this loop holds — proven in-gate below — so repair engages,
    honestly fails, and the goal falls through the UNTOUCHED global path to
    the standard terminal (gapped:enumerate_failed), never a park and never
    a standing wrong accept."""
    fr = _FROZEN[tid]
    assert fr["status"] == "gapped" and fr["gap_reason"] == "enumerate_failed"
    t = _TASKS[tid]
    # THE UNREACHABILITY FACT (live-var grain): the covered construction is
    # count_of_list, so the only live var is v1 = len(items); some held-out
    # row shares its v1 with another (held-out or example) row of DIFFERENT
    # expected output — no function of the live vars can pass both.
    seen = {}
    for row in t["example_rows"] + t["held_out_rows"]:
        v1 = len(row["inputs"]["items"])
        seen.setdefault(v1, set()).add(row["expected"])
    assert any(len(outs) > 1 for outs in seen.values()), \
        "the live-var abstraction must be provably lossy for this gate"
    s, ag, g, t = run_task(tid)
    r, fed = verify_loop(s, ag, g, t)
    # repair ENGAGED (localization succeeded — the trace pinned the folded
    # hole) but the re-solve honestly failed on the contradictory rows.
    assert r["repair"]["localized"] is not None and \
        r["repair"]["localized"] >= 1.0
    assert len(fed) >= 1
    # honest terminal via the untouched global path.
    assert r["status"] == "gapped"
    assert r["gap_reason"] == "enumerate_failed"
    assert r["program"] is None, "no wrong accept left standing"
    assert_zero_parks(s)


def test_headline_la21_converts_to_holdout_ok_via_s4_capability_gain():
    """2026-08-01 arc4 S4 capability gain: `la_21_count_zeros` was one of
    P7-B's three PROVEN-unreachable ids (gate above, pre-S4). S4 landed
    `FilterList`/`Count` (class B, list-filter) as new SynthEnumerate ops,
    composed from pre-existing pure DSL Terms
    (PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md §2) -- the hole's re-solve can now
    express "count of zeros" as `Count(FilterList(items, x, x==0))`, a shape
    that did not exist in the enumerator's reach when P7-B proved this id
    unreachable. This converts via the EXACT SAME repair mechanism as la_10
    (P7-B's headline convert): counterexamples localize into the final_expr
    hole, the hole's derived row set grows, and the re-solve finds a program
    that genuinely generalizes -- verified against BOTH held-out rows,
    including whatever the loop never explicitly fed."""
    tid = "la_21_count_zeros"
    fr = _FROZEN[tid]
    assert fr["status"] == "gapped" and fr["gap_reason"] == "enumerate_failed", \
        "the frozen P7-B baseline (pre-S4) is untouched"
    s, ag, g, t = run_task(tid)
    r, fed = verify_loop(s, ag, g, t)
    assert r["status"] == "accepted"
    assert len(fed) >= 1, "at least one counterexample round was needed"
    for ho in t["held_out_rows"]:
        assert eval_accepted(s, r, ho["inputs"]) == (ho["expected"], True)
    assert r["repair"]["localized"] is not None and r["repair"]["localized"] >= 1.0
    assert r["repair"]["kind"] == "final_expr"
    assert_zero_parks(s)


# ---------------------------------------------------------------------------
# 2) LOCALITY — the skeleton is never re-proposed
# ---------------------------------------------------------------------------
def test_locality_skeleton_ir_unchanged_only_the_hole_differs():
    s, ag, g, t = run_task(CONVERTS)
    r0 = psy.read_goal(s, g)
    old_prog = r0["program"]
    old_ir = json.loads(s.node(old_prog)["attrs"]["program"])
    excluded_before = list(r0["excluded"])
    cover_before = s.node(g)["attrs"].get("ps_cover_json")
    r, fed = verify_loop(s, ag, g, t)
    assert r["status"] == "accepted"
    new_prog = r["program"]
    assert new_prog != old_prog
    # the refuted Program keeps its provenance, marked.
    assert s.node(old_prog)["attrs"].get("refuted") == 1.0
    new_ir = json.loads(s.node(new_prog)["attrs"]["program"])
    old_stmts, new_stmts = old_ir["stmts"], new_ir["stmts"]
    assert len(old_stmts) == len(new_stmts)
    # canonical compare: every covered-span statement byte-identical;
    # ONLY the final (hole) statement differs.
    for a, b in zip(old_stmts[:-1], new_stmts[:-1]):
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert old_stmts[-1]["type"] == new_stmts[-1]["type"] == "ProgReturn"
    assert json.dumps(old_stmts[-1], sort_keys=True) != \
        json.dumps(new_stmts[-1], sort_keys=True)
    # no re-proposal artifacts: attempts, exclusions, cover facts, rungs all
    # untouched; the ShapeDecode ran ONCE (the decode marker is still the
    # original pass's).
    assert r["attempts"] == r0["attempts"] == 1.0
    assert r["excluded"] == excluded_before
    assert s.node(g)["attrs"].get("ps_cover_json") == cover_before
    assert s.node(g)["attrs"].get("ps_descent_decoded") == 1.0
    assert r["rungs"]["codebook"] == 1.0
    assert r["rungs"]["descend"] == 1.0
    assert r["rungs"]["enumerate"] is None
    assert r["construction"] == r0["construction"] == "count_of_list"


# ---------------------------------------------------------------------------
# 3) counterexample-into-hole — the propagated row, pinned
# ---------------------------------------------------------------------------
def test_counterexample_propagates_into_the_hole_row_set():
    s, ag, g, t = run_task(CONVERTS)
    r0 = psy.read_goal(s, g)
    refuted_expr = r0["ir"]["stmts"][-1]["value"]     # the overfit candidate
    r, fed = verify_loop(s, ag, g, t)
    assert len(fed) == 1
    rep_holes = [h for h in r["holes"] if h.get("repair") == 1.0]
    assert len(rep_holes) == 1, "repair re-opened exactly ONE hole"
    h = rep_holes[0]
    assert h["kind"] == "final_expr" and h["hole_status"] == "folded"
    rows = json.loads(h["derived_rows_json"])
    # the original three rows AND the propagated counterexample, with the
    # live-var value derived from the failing row's own inputs (pinned):
    # v1 = len([2, -4, 6, -8, 10]) = 5 → expected 3.
    assert len(rows) == 4.0 == h["n_derived"]
    assert rows[-1] == {"inputs": {"v1": len(fed[0]["inputs"]["items"])},
                        "expected": fed[0]["expected"]}
    assert rows[-1]["inputs"]["v1"] == 5 and rows[-1]["expected"] == 3
    # the refuted candidate is an ExcludedSub at hole scope (provenance for
    # the multi-candidate iteration; the GROWN ROW SET is the enumerator
    # input shift that retires it — and by construction the excluded term
    # cannot fit the grown rows, so the re-solve cannot return it).
    assert len(r["sub_excluded"]) == 1
    assert r["sub_excluded"][0]["kind"] == "final_expr"
    assert json.loads(r["sub_excluded"][0]["term"]) == refuted_expr


# ---------------------------------------------------------------------------
# 4) localization honesty — refusal → the untouched global CEGIS path
# ---------------------------------------------------------------------------
def _teach_decoy(s, name, triggers, term, args):
    s.add_node("ShapeSignature", {
        "name": name, "kind": "code_write_construction",
        "signature": json.dumps([[t] for t in triggers]),
        "trigger_tokens": list(triggers),
        "ground_template": json.dumps(
            {"desc": "gate decoy", "term": term, "args": list(args),
             "mode": "code_write"})})


def test_refused_localization_falls_to_global_cegis_unchanged():
    """A rung-1 codebook accept has no skeleton/hole split — NO derivable
    boundary expectation exists, so localization honestly refuses and the
    EXISTING global machinery completes the repair: fresh attempt →
    CounterExample → exclusion → re-proposal → correct accept.

    2026-08-01 (arc4 S2 reconciliation): the decoy was originally a bare
    `Var a` (ignoring `b` entirely) — byte-for-byte D3's own target shape
    (`unread_declared_param`, PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md):
    a declared param never read, proven a genuine defect because `b` varies
    across the revealed rows. S2's structural-verdict rules now correctly
    reject that shape before it can ever be "accepted", so this gate's own
    mechanism (localization refusing, then the untouched global CEGIS path
    completing the repair) never got a turn. Per the reconciliation rule
    ("fix the fixture, never the detector"), the decoy is rewritten to
    genuinely READ both declared params and compute the WRONG function — a
    sign check (`a > 0`) standing in for the intended magnitude comparison
    — which is exactly the "plausible-but-wrong" repair scenario this gate
    was always meant to exercise."""
    s, ag = boot()
    # a MORE SPECIFIC decoy that is correct on the initial rows (both rows
    # have a > 0, so the sign check picks `a`, which happens to be the
    # larger of the two) but wrong in general — it reads BOTH a and b.
    _teach_decoy(s, "grab_first_decoy", ["LARGER", "DUO"],
                 {"type": "IfThenElse",
                  "cond": {"type": "Gt", "a": {"type": "Var", "name": "a"},
                           "b": {"type": "Lit", "value": 0}},
                  "then": {"type": "Var", "name": "a"},
                  "other": {"type": "Var", "name": "b"}}, ["a", "b"])
    m = psy.ingest_spec(
        s, ag, "write a function pick_of_duo that returns the larger of the duo",
        [({"a": 9, "b": 2}, 9), ({"a": 7, "b": 1}, 7)])
    psy.pump(s, ag)
    g = s.in_neighbours(m, "about_message")[0]
    r0 = psy.read_goal(s, g)
    assert r0["status"] == "accepted"
    assert r0["construction"] == "grab_first_decoy"
    assert r0["attempts"] == 1.0 and r0["holes"] == []
    psy.ingest_counterexample(s, ag, g, {"a": 2, "b": 8}, 8)
    psy.pump(s, ag)
    r = psy.read_goal(s, g)
    # refusal recorded; NO repair hole was minted.
    assert r["repair"]["refused"] == 1.0
    assert r["repair"]["localized"] is None
    assert r["repair"]["attempts"] == 0.0
    assert all(h.get("repair") != 1.0 for h in r["holes"])
    # the global lane did the work, exactly as pre-P7B: the counterexample
    # row failed at the FRESH attempt, the decoy was excluded, re-proposal
    # found the correct construction inside the integer budget.
    assert r["status"] == "accepted"
    assert r["construction"] == "max_of_two"
    assert r["attempts"] == 3.0 and r["attempts"] <= r["budget"]
    assert r["excluded"] == ["grab_first_decoy"]
    assert [(c["construction"], c["attempt"]) for c in r["counterexamples"]] \
        == [("grab_first_decoy", 2.0)]
    # the refuted Program is retracted-but-kept; the new one is correct.
    progs = {psy._text(s.node(p)["attrs"].get("construction")):
             s.node(p)["attrs"].get("refuted") for p in s.nodes("Program")}
    assert progs == {"grab_first_decoy": 1.0, "max_of_two": None}
    assert eval_accepted(s, r, {"a": 1, "b": 5}) == (5, True)
    assert_zero_parks(s)


# ---------------------------------------------------------------------------
# 5) fold_step repair — the singleton unroll localizes INTO the fold
# ---------------------------------------------------------------------------
def test_fold_step_repair_second_row_kills_the_lit_constant():
    """The la-class first-fit failure and its cure, at fold grain: weak rows
    let the fold body accept a Lit constant; a SINGLETON counterexample row
    is derivable through the one-iteration unroll (descent's own machinery,
    reused for the trace), localizes INSIDE the fold, and the propagated
    second row makes the Lit unfittable — the re-solve finds a real step.
    The multi-candidate facts are recorded: ExcludedSub{Lit 10} at hole
    scope, and the sub-spec carries the enumerator input-shift facts."""
    s, ag = boot()
    m = psy.ingest_spec(
        s, ag,
        "write a function tote_up that returns the total of a list of numbers",
        [({"items": [5]}, 10), ({"items": []}, 0)])
    psy.pump(s, ag)
    g = s.in_neighbours(m, "about_message")[0]
    r0 = psy.read_goal(s, g)
    assert r0["status"] == "accepted"
    assert r0["descend_kind"] == "fold_step"
    old_fold = r0["ir"]["stmts"][-1]["value"]
    assert old_fold["type"] == "Fold"
    assert old_fold["body"] == {"type": "Lit", "value": 10}, \
        "the weak-row first-fit IS the Lit constant"
    psy.ingest_counterexample(s, ag, g, {"items": [3]}, 6)
    psy.pump(s, ag)
    r = psy.read_goal(s, g)
    assert r["status"] == "accepted"
    assert r["repair"]["localized"] == 1.0
    assert r["repair"]["kind"] == "fold_step"
    # counterexample-into-hole at fold grain: the unroll-derived second row.
    rep = [h for h in r["holes"] if h.get("repair") == 1.0]
    assert len(rep) == 1 and rep[0]["hole_status"] == "folded"
    assert json.loads(rep[0]["derived_rows_json"]) == [
        {"inputs": {"acc": 0, "x": 5}, "expected": 10},
        {"inputs": {"acc": 0, "x": 3}, "expected": 6}]
    # the refuted candidate recorded at hole scope; the sub-spec carried the
    # input-shift facts (excluded term + droppable const — note the honest
    # contract boundary: an excluded Lit that is also an integer spec OUTPUT
    # is re-appended by SynthEnumerate, so the ROW GROWTH is what kills it;
    # the drop facts are still recorded and passed).
    assert [json.loads(x["term"]) for x in r["sub_excluded"]] == \
        [{"type": "Lit", "value": 10}]
    sub_msgs = [m2 for h in s.neighbours(g, "has_hole")
                if s.node(h)["attrs"].get("repair") == 1.0
                for m2 in s.neighbours(h, "sub_message")]
    assert len(sub_msgs) == 1
    m2at = s.node(sub_msgs[0])["attrs"]
    assert list(psy._plain(m2at.get("ps_enum_drop_consts"))) == [10]
    assert [json.loads(x) for x in
            psy._plain(m2at.get("ps_enum_excluded"))] == \
        [{"type": "Lit", "value": 10}]
    # locality at fold grain: init/source unchanged, ONLY the body differs.
    new_fold = r["ir"]["stmts"][-1]["value"]
    for k in ("type", "source", "var_name", "acc_name", "init"):
        assert new_fold[k] == old_fold[k]
    assert new_fold["body"] != old_fold["body"]
    assert eval_accepted(s, r, {"items": [7]}) == (14, True)
    assert eval_accepted(s, r, {"items": []}) == (0, True)
    assert_zero_parks(s)


# ---------------------------------------------------------------------------
# 6) budget honesty
# ---------------------------------------------------------------------------
def test_repair_budget_is_integer_and_exhaustion_falls_to_global():
    """The MECHANISM this gate proves: the repair budget is a real integer
    counter on its OWN lane, and forcing it to zero makes repair honestly
    give up (never minting a repair hole, never spending a repair attempt)
    and fall through to the untouched global CEGIS path. 2026-08-01 arc4 S4:
    the OUTCOME this test originally pinned ("falls through to an honest
    gap") is no longer what happens on `la_10_count_positives` -- S4's
    widened enumerator now lets the GLOBAL re-proposal itself (fresh
    codebook attempt -> whole-goal enumerate) find `Count(FilterList(items,
    x, x>0))` for "count of positives" from scratch, which is a genuine,
    verified-holdout-ok solve, not an overfit (contrast with the la_06
    re-pin in test_prog_descent_migrated.py, which IS a spurious fit and was
    NOT adopted as a pass). The budget-honesty mechanism itself
    (gaveup/attempts/no-repair-hole) is unchanged and re-verified below; only
    the terminal status pin moves to match the new, genuinely-generalizing
    outcome."""
    s, ag, g, t = run_task(CONVERTS)
    at = s.node(g)["attrs"]
    assert at["ps_repair_budget"] == 2.0 and \
        float(at["ps_repair_budget"]).is_integer()
    assert at["ps_repair_attempts"] == 0.0
    # force the budget to zero: localizable, but no repair round is allowed.
    s.set_attr(g, "ps_repair_budget", 0.0)
    psy.ingest_counterexample(s, ag, g, {"items": [2, -4, 6, -8, 10]}, 3)
    psy.pump(s, ag)
    r = psy.read_goal(s, g)
    assert r["repair"]["gaveup"] == 1.0
    assert r["repair"]["attempts"] == 0.0, "never repair round N+1"
    assert all(h.get("repair") != 1.0 for h in r["holes"]), \
        "no repair hole minted past the budget"
    # the untouched global path ran (fresh codebook attempt, then whole-goal
    # enumerate) — the fall-through itself is the thing being proven here.
    assert r["rungs"]["enumerate"] == 1.0, \
        "exhausted repair budget must still fall through to whole-goal enumerate"
    # 2026-08-01 arc4 S4: this fall-through now genuinely succeeds (verified
    # against BOTH held-out rows, i.e. not merely fitting the fed
    # counterexample) rather than gapping — a real capability gain, not a
    # mechanism regression.
    assert r["status"] == "accepted"
    for ho in t["held_out_rows"]:
        assert eval_accepted(s, r, ho["inputs"]) == (ho["expected"], True)
    assert_zero_parks(s)


# ---------------------------------------------------------------------------
# 7) attempts accounting — H7b's per-task evidence, both numbers measured
# ---------------------------------------------------------------------------
def test_attempts_accounting_repair_cheaper_than_global_reproposal():
    """Post-failure work, measured on the converted task:
    REPAIR: 0 additional outer attempts + 1 hole re-solve (one sub-goal).
    GLOBAL RE-PROPOSAL (counterfactual: the same knowledge — spec rows plus
    the counterexample — re-run from scratch): 1 codebook attempt + 2 hole
    solves (fold_step retried and refused again, final_expr re-derived).
    1 unit < 3 units; the skeleton work is never repeated under repair."""
    t = _TASKS[CONVERTS]
    ex = [(r["inputs"], r["expected"]) for r in t["example_rows"]]
    ce_inputs, ce_expected = {"items": [2, -4, 6, -8, 10]}, 3

    # arm A: repair.
    s, ag, g, _t = run_task(CONVERTS)
    pre = set(synth_goals(s))
    pre_attempts = s.node(g)["attrs"]["ps_attempts"]
    psy.ingest_counterexample(s, ag, g, ce_inputs, ce_expected)
    psy.pump(s, ag)
    r = psy.read_goal(s, g)
    assert r["status"] == "accepted"
    repair_outer_delta = r["attempts"] - pre_attempts
    repair_subgoals = len(set(synth_goals(s)) - pre)
    assert repair_outer_delta == 0.0
    assert repair_subgoals == 1

    # arm B: global re-proposal with identical knowledge.
    s2, ag2 = boot()
    m2 = psy.ingest_spec(s2, ag2, t["request_text"],
                         ex + [(ce_inputs, ce_expected)])
    psy.pump(s2, ag2)
    g2 = s2.in_neighbours(m2, "about_message")[0]
    r2 = psy.read_goal(s2, g2)
    assert r2["status"] == "accepted", "the counterfactual also solves it"
    cf_outer_attempts = r2["attempts"]
    cf_subgoals = len(synth_goals(s2)) - 1
    assert cf_outer_attempts == 1.0
    assert cf_subgoals == 2, "fold_step + final_expr both re-solved"

    # H7b: attempts-per-accept falls — repair's post-failure work is
    # strictly less than the re-proposal's.
    assert repair_outer_delta + repair_subgoals < \
        cf_outer_attempts + cf_subgoals, \
        "repair(%s) must beat re-proposal(%s)" % (
            repair_outer_delta + repair_subgoals,
            cf_outer_attempts + cf_subgoals)


# ---------------------------------------------------------------------------
# 8) paired identity — the repair lane is inert without a counterexample
# ---------------------------------------------------------------------------
def test_repair_lane_inert_without_counterexample():
    """No ce ingest → the repair rules never fire: seq/attempt counters stay
    at their minted zeros, no ExcludedSub exists, and the P7-A accept shape
    (including its Program count) is untouched."""
    s, ag, g, t = run_task(CONVERTS)
    r = psy.read_goal(s, g)
    assert r["status"] == "accepted"
    psy.pump(s, ag)     # idle fixpoint: nothing re-fires
    r = psy.read_goal(s, g)
    assert r["repair"]["seq"] == 0.0
    assert r["repair"]["attempts"] == 0.0
    assert r["repair"]["trace_seq"] == -1.0
    assert r["repair"]["localized"] is None and r["repair"]["refused"] is None
    assert r["sub_excluded"] == []
    assert s.nodes("ExcludedSub") == []
    assert len(s.neighbours(g, "accepted_program")) == 1


# ---------------------------------------------------------------------------
# 9) Arc2-Q4 — exclude-powered iteration (additive; the top-level round-
#    bounded lever's full headline lives in tests/test_descent_widening_
#    migrated.py). This gate closes the P7-B-named residual directly at the
#    hole-scope wiring: `run_enumerate` now passes `ps_enum_excluded` as the
#    engine's `exclude` param, not merely the coarse const-drop heuristic.
# ---------------------------------------------------------------------------
def test_run_enumerate_threads_hole_scope_exclude_into_the_engine():
    """The Q1-cited scenario (test_exclude_blocks_const_resurrection,
    tests/test_synth_enumerate_migrated.py): a spec whose ONLY size-1 fit
    is a bare `Lit` that is ALSO an output value (the Term re-appends
    output-valued consts regardless of any dropped consts — the honest
    contract boundary P7-B named and could not close without Rust).
    Exercised THROUGH the adapter: excluding that Lit via `ps_enum_excluded`
    (exactly spawn_subgoal's own repair-provenance shape) and re-running
    `run_enumerate` over the SAME single row (no row growth to do the work
    instead) must produce something OTHER than the excluded Lit — proof the
    wiring reaches the engine's `exclude` contract, not just the const-drop
    path."""
    s, ag = boot()
    m = psy.ingest_spec(s, ag, "write a function xten that returns ten",
                        [({"x": 5}, 10)])
    psy.pump(s, ag)
    g = s.in_neighbours(m, "about_message")[0]
    r0 = psy.read_goal(s, g)
    assert r0["status"] == "accepted"
    lit10 = {"type": "Lit", "value": 10}
    assert r0["ir"]["stmts"][-1]["value"] == lit10, \
        "the ONLY size-1 fit for this one-row spec is Lit(10)"
    s.set_attr(m, "ps_enum_excluded", [json.dumps(lit10)])
    s.set_attr(g, "ps_enum_round", 1.0)   # force run_enumerate's round guard
    assert psy.run_enumerate(s, ag, g) is True
    r1 = psy.read_goal(s, g)
    assert r1["enumerate_outcome"] == "ok"
    assert r1["ir"]["stmts"][-1]["value"] != lit10, \
        "excluded via the engine `exclude` contract, not rediscovered "\
        "despite the identical single row"


# ---------------------------------------------------------------------------
# 10) Arc2-Q4 — row-verdict widening (tol / unordered), pinned at the
#     mechanism grain (the full headline lives in test_descent_widening).
# ---------------------------------------------------------------------------
def test_row_cmp_ok_fixed_formula_pinned():
    """The fixed-formula comparator eval_and_record records (cmp_ok):
    tol -> float-within-tolerance; unordered -> set/duplicate-insensitive
    equality (never multiset/bag); neither -> plain equality. Pinned
    directly, both pass and fail cases."""
    assert psy._row_cmp_ok(3.0, 3.001, 0.01, False) == 1.0
    assert psy._row_cmp_ok(3.0, 3.5, 0.01, False) == 0.0
    assert psy._row_cmp_ok([2, 1], [1, 2], None, True) == 1.0
    assert psy._row_cmp_ok([1, 1, 2], [1, 2], None, True) == 1.0, \
        "duplicate-insensitive, never multiset/bag equality"
    assert psy._row_cmp_ok([1, 2], [1, 3], None, True) == 0.0
    assert psy._row_cmp_ok(5, 5, None, False) == 1.0
    assert psy._row_cmp_ok(5, 6, None, False) == 0.0
