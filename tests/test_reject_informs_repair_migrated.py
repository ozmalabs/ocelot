"""tests/test_reject_informs_repair_migrated.py — Arc 4 Phase S6: A
STRUCTURAL REJECTION INFORMS REPAIR, NOT A TERMINAL.

`PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md` (Sec.4) landed `ps_structural_reject`
routing every pre-accept structural rejection straight to `gapped` — S2
had TRIED routing rejections through the standing counterexample/exclude/
reproposal lane and REVERTED it: a retrieval-sourced accept
(`ps_construction == 'retrieved_exemplar'`) shares that ONE literal
construction name across every retrieved exemplar, so excluding it can
never distinguish candidates — measured live as a real pipeline stall
(task 267). `PROGRAM_SYNTHESIS_ARC4_S5.md` (Sec.7) named the resulting
residual precisely: the detector localises the fault perfectly (D3:
"ignores parameter c") and that diagnosis was thrown away rather than
handed to repair, costing one genuine, previously-convergent pass
(`br_10_top_of_three` under the `repair_oracle` battery arm).

THE S6 FIX (`seeds/program_synthesis.json` v1.7.0 -> v1.8.0): the single
`ps_structural_reject` rule is replaced by FOUR detector/source-routed
rules (`domains/prog_synthesis.py` is UNCHANGED except for one read-back
addition to `read_goal`):

  ps_structural_reject_exclusion_gap     D1 and/or D2 fired, retrieval-
                                          sourced -> straight to 'gapped'
                                          (route='exclusion', unreachable).
  ps_structural_reject_exclusion_reopen  D1 and/or D2 fired, NOT
                                          retrieval-sourced -> routes
                                          DIRECTLY to 'counterexample'
                                          (route='exclusion') -- the SAME
                                          standing CEGIS lane
                                          (ps_exclude_failed/
                                          ps_reproposal/ps_ce_exhausted/
                                          ps_enum_retry_mark) a genuine
                                          failing-row counterexample
                                          already uses, unchanged.
  ps_structural_reject_repair_gap        D3 fired ALONE, retrieval-
                                          sourced -> 'gapped'
                                          (route='repair', unreachable —
                                          the localisation is still
                                          recorded for explainability).
  ps_structural_reject_repair_reopen     D3 fired ALONE, NOT retrieval-
                                          sourced -> reopens via the same
                                          lane, `repair_target_param` :=
                                          the ignored parameter(s).

THE ONE NEW GATE CONDITION avoiding S2's stall is `ps_construction !=
'retrieved_exemplar'` — nothing else changed about the standing exclude/
reproposal machinery (it is arc2/arc3's own, independently tested lane).

Gates in this file:
  1. Seed shape — v1.8.0, the 4 new rules present, the old single rule
     gone, ps_structural_clear untouched.
  2. PER-DETECTOR ROUTING, isolated: D1-only / D2-only / D3-only, each
     crossed with retrieval-sourced vs not (6 direct cases) plus a
     priority case (D1+D3 together routes as D1/exclusion, never repair).
  3. THE HEADLINE MEASUREMENT — the exact 26 structural rejections S2/S5
     measured on the live 257-task MBPP population, disposed into id
     lists: (a) repaired to a passing accept, (b)/(c) reopened via
     exclude+reproposal but still honestly gapped, (d) gapped directly
     (retrieval-sourced, never reopened).
  4. NO HONEST-SCORE BACKSLIDING — 397 and 404 (the genuine-defect
     rejections from the `pass` population) still never accept.
  5. LOOP SAFETY — zero parks across the full live 257-task population;
     for every reopened id, the Excluded-node names it mints are never
     repeated (the engine's own `exclude` contract, mint-once, holds).
  6. br_10_top_of_three — root-caused, not faked: it does not converge,
     and the precise reason (no discriminating information among the 3
     revealed rows once the decoy is excluded — verified directly against
     the SynthEnumerate engine) is pinned as a regression test on the
     analysis itself.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_reject_informs_repair_migrated.py
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402
import mbpp_arc3_battery as arc3b  # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402
from domains import prog_synthesis as psy  # noqa: E402

SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
ENDGAME_PATH = os.path.join(ROOT, "results", "arc4_endgame.json")
P7_TASKS_PATH = os.path.join(ROOT, "tests", "fixtures",
                             "prog_synthesis_battery", "tasks.json")


def _term_live(term, env) -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(term, env)
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live({"type": "ProgEval", "prog": {"type": "ProgSeq", "stmts": []},
                   "env": None, "oracles": None, "fuel": 5, "field": ""}, {}):
    pytest.skip("ProgEval not present in the installed substrate_rs binary — "
                "rebuild runners/dsl. Honest skip.", allow_module_level=True)


# --------------------------------------------------------------------------- #
#  fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def seed_manifest():
    with open(SEED_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def test_tasks():
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = arc3b.q0_split_tasks(all_tasks)
    return {t["task_id"]: t for t in splits["test"]}


def _synth_task(task_id: int, test_tasks) -> Dict[str, Any]:
    """Run ONE MBPP task, live, under the CURRENT (v1.8.0) seed, and
    return the full `read_goal` dict — never `arc3b.run_task`'s trimmed
    row, because this file needs `rejections`/`structural.reopen_count`,
    which that row does not carry."""
    task = test_tasks[task_id]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    s, ag = arc3b.boot_full_r3()
    r = psy.synthesize_from_request(s, ag, task["prompt"], spec["revealed"])
    out = psy.read_goal(s, r["goal"])
    out["_held_out"] = spec["held_out"]
    return out


# The exact 26 ids PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md / _S5.md measured as
# `accepted_holdout_fail -> gapped:structural_verdict_reject` conversions
# (re-derived here from the frozen `results/arc4_endgame.json` artifact —
# `no_structural`'s accepted_holdout_fail ids minus `full_a4`'s — never
# hand-typed from prose, per the "a baseline is a list, read it" rule).
@pytest.fixture(scope="module")
def the_26_ids():
    with open(ENDGAME_PATH) as f:
        d = json.load(f)
    h = d["ha2_verdict_discrimination"]
    no_s = set(h["no_structural_accepted_holdout_fail_ids"])
    full = set(h["full_a4_accepted_holdout_fail_ids"])
    ids = sorted(no_s - full)
    assert len(ids) == 26, ids
    return ids


# Split of the 26, by construction source, PINNED from a live measurement
# under v1.8.0 (see PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md for the disposition
# table this exact split produces).
RETRIEVAL_SOURCED_14 = [68, 83, 86, 93, 109, 239, 242, 247, 269, 285, 420,
                       427, 434, 454]
REOPENED_12 = [14, 58, 103, 125, 126, 164, 228, 304, 396, 414, 430, 432]

GENUINE_DEFECT_IDS = [397, 404]  # the pass-population D3 catches

# 2026-08-01 (arc5 moves, reconciled): a STILL LATER phase
# (PROGRAM_SYNTHESIS_ARC5_MOVES.md, RUNG 2.6 -- structural moves) changes
# two members of the two populations above, via a DIFFERENT mechanism than
# S6's reject-informs-repair (orbit augmentation, not exclude+reproposal
# CEGIS): task 58 (REOPENED_12) and task 404 (GENUINE_DEFECT_IDS) both now
# reach a genuine `pass` -- verified live below via held-out AND a
# constructed witness, never merely asserted. Both are held out of S6's own
# claims the same way `tests/test_search_reach_migrated.py`'s
# `_ARC5_EXACT_FIRST_PASS_IDS` precedent holds out a later phase's ids from
# an earlier phase's frozen claim.
# Task 59 is a THIRD arc5-moves pass (MOVE B, intermediate decomposition)
# -- outside this file's own 26/2-id populations but inside the full
# 257-task corpus `test_no_wrong_accept_regression_vs_v1_7_0_baseline`
# diffs, so it is included here too (see
# tests/test_search_reach_migrated.py's OWN `_ARC5_MOVES_PASS_IDS = {59}`,
# scoped to its own 85-id bucket).
_ARC5_MOVES_PASS_IDS = {58, 59, 404}


@pytest.fixture(scope="module")
def live_28(test_tasks):
    """Every one of the 26 + the 2 genuine-defect ids, run fresh, live,
    under the current seed — the ONE population this whole file measures
    against. ~28 single-task synth calls, well under the suite's time
    budget (each is a fresh, tiny boot)."""
    ids = RETRIEVAL_SOURCED_14 + REOPENED_12 + GENUINE_DEFECT_IDS
    return {tid: _synth_task(tid, test_tasks) for tid in ids}


# --------------------------------------------------------------------------- #
#  1. Seed shape.
# --------------------------------------------------------------------------- #
def test_seed_v1_8_0_shape(seed_manifest):
    # 2026-08-01 (arc5 exact-first): v1.8.0 -> v1.9.0 (66 rules) added the
    # SHAPE-FIRST rung ahead of enumerate. S6's four routed reject rules,
    # asserted below, are unchanged by it.
    # 2026-08-01 (arc5 moves, reconciled): v1.9.0 -> v1.10.0 (70 rules)
    # added RUNG 2.6 (ps_move_mark/_select/_none/_fresh_attempt,
    # PROGRAM_SYNTHESIS_ARC5_MOVES.md) — none of the four touches the S6
    # reject-routing rules asserted below.
    # 2026-08-01 (arc6 seam D, reconciled): v1.10.0 -> v1.11.0 (73 rules)
    # added the PROPERTY-REFUTATION rung (ps_property_clear / ps_property_
    # reject_gap / ps_property_reject_reopen, PROGRAM_SYNTHESIS_ARC6_D.md
    # §1/§6). Those three MIRROR the S6 reject-routing structure asserted
    # below on a disjoint attr family (ps_property_* vs ps_structural_*)
    # rather than replacing it — all four S6 rules are still present and
    # unedited, so this test's own shape claim is unchanged.
    assert seed_manifest["version"] == "1.12.0"  # 2026-08-03: 1.11.0 -> 1.12.0, the goal-residual weight term
    # (ps_move_mark stamps ps_move_w_residual; ps_move_select subtracts a
    # held refutation's weight inside its Argmax). Pin reconciled, not
    # relaxed -- see PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md GR4.
    names = {r["name"] for r in seed_manifest["rules"]}
    assert "ps_structural_reject" not in names
    assert "ps_structural_clear" in names
    for n in ("ps_structural_reject_exclusion_gap",
              "ps_structural_reject_exclusion_reopen",
              "ps_structural_reject_repair_gap",
              "ps_structural_reject_repair_reopen"):
        assert n in names


# --------------------------------------------------------------------------- #
#  2. Per-detector routing, isolated synthetic goals (mirrors the
#     tests/test_verdict_discrimination_migrated.py harness).
# --------------------------------------------------------------------------- #
def _fresh_goal(*, construction: str, attempts: float = 1.0, budget: float = 5.0):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    g = s.add_node("Goal", {
        "kind": "synth_program", "status": "evaluated",
        "ps_attempts": attempts, "ps_budget": budget,
        "ps_depth": 0.0, "ps_construction": construction,
        "ps_reflect_ok": 1.0,
    })
    s.add_edge_unchecked(ag, "has_goal", g)
    m = s.add_node("Message", {"text": "x"})
    s.add_edge_unchecked(g, "about_message", m)
    s.add_edge_unchecked(ag, "received", m)
    return s, ag, g, m


def _add_row(s, m, inputs: Dict[str, Any], expected: Any, *, attempt: float = 1.0):
    r = s.add_node("ExampleRow", {
        "inputs_json": json.dumps(inputs), "expected": expected,
        "eval_attempt": attempt, "verdict_attempt": -1.0,
        "eval_ok": 1.0, "got": expected, "ce_attempt": -1.0,
    })
    s.add_edge_unchecked(m, "has_example", r)
    return r


def _reflect_and_verify(s, g, ir: Dict[str, Any], *, attempt: float = 1.0):
    root = s._inner.add_term_subgraph(ir)
    s.add_edge_unchecked(g, "ps_ir_reflected", root)
    s.set_attr(g, "ps_ir", json.dumps(ir))
    s.set_attr(g, "ps_attempts", attempt)
    return root


# ---- D1-only (memo_lookup_table): a pure literal-dispatch, all params read
_D1_ONLY_IR = {"type": "ProgSeq", "stmts": [
    {"type": "ProgDefFnParam", "name": "a", "default": None},
    {"type": "ProgReturn", "value": {
        "type": "IfThenElse",
        "cond": {"type": "Eq", "a": {"type": "Var", "name": "a"},
                 "b": {"type": "Lit", "value": 2}},
        "then": {"type": "Lit", "value": 35},
        "other": {"type": "Lit", "value": 10}}},
]}
_D1_ONLY_ROWS = [({"a": 2}, 35), ({"a": 3}, 10)]


def _run_isolated(construction: str, ir: Dict[str, Any],
                  rows, *, attempts=1.0, budget=5.0) -> Dict[str, Any]:
    s, ag, g, m = _fresh_goal(construction=construction, attempts=attempts,
                              budget=budget)
    for inputs, expected in rows:
        _add_row(s, m, inputs, expected, attempt=attempts)
    _reflect_and_verify(s, g, ir, attempt=attempts)
    psy.pump(s, ag)
    return psy.read_goal(s, g)


def test_d1_only_retrieval_routes_exclusion_unreachable_gap():
    out = _run_isolated("retrieved_exemplar", _D1_ONLY_IR, _D1_ONLY_ROWS)
    assert out["structural"]["fired_detectors"] == ["d1_memo_lookup_table"]
    assert out["status"] == "gapped"
    assert out["gap_reason"] == "structural_verdict_reject"
    assert out["structural"]["reopen_count"] is None
    assert out["rejections"][0]["route"] == "exclusion"
    assert out["excluded"] == []


def test_d1_only_nonretrieval_routes_exclusion_reopen():
    out = _run_isolated("d1_decoy", _D1_ONLY_IR, _D1_ONLY_ROWS, budget=1.0)
    assert out["structural"]["fired_detectors"] == ["d1_memo_lookup_table"]
    assert out["program"] is None, "the defective candidate is never accepted"
    assert out["status"] == "gapped", "reopened, then honestly exhausted"
    assert out["gap_reason"] != "structural_verdict_reject", (
        "repair was genuinely attempted before giving up")
    assert out["structural"]["reopen_count"] == 1.0
    assert out["excluded"] == ["d1_decoy"]
    assert out["rejections"][0]["route"] == "exclusion"
    assert out["rejections"][0]["repair_target_param"] == []


# ---- D2-only (dead_code_free_vars): a free var read, nothing declared
#      unread -- its OWN justified route (Sec.1 of PROGRAM_SYNTHESIS_ARC4_
#      S6_NOTES.md): a reference to something that is not even a declared
#      input names no PARAMETER to hand to a hole-reopen, so D2 gets the
#      SAME 'exclusion' treatment as D1, not 'repair'.
_D2_ONLY_IR = {"type": "ProgSeq", "stmts": [
    {"type": "ProgDefFnParam", "name": "a", "default": None},
    {"type": "ProgReturn", "value": {
        "type": "Plus", "items": [{"type": "Var", "name": "a"},
                                  {"type": "Var", "name": "stray"}]}},
]}
_D2_ONLY_ROWS = [({"a": 2}, 7), ({"a": 3}, 8)]


def test_d2_only_nonretrieval_routes_exclusion_reopen_justified():
    out = _run_isolated("d2_decoy", _D2_ONLY_IR, _D2_ONLY_ROWS, budget=1.0)
    assert out["structural"]["fired_detectors"] == ["d2_dead_code_free_vars"]
    assert out["structural"]["free_vars"] == ["stray"]
    assert out["program"] is None
    assert out["status"] == "gapped"
    assert out["structural"]["reopen_count"] == 1.0, (
        "D2 IS reopenable on a non-retrieval source — it is not "
        "'repairable' (no declared parameter to localise), but exclusion "
        "+ re-proposal still gets a genuine try, same as D1")
    assert out["excluded"] == ["d2_decoy"]
    assert out["rejections"][0]["route"] == "exclusion", (
        "D2 names no parameter — it is NOT 'repair', per the brief's own "
        "distinction (route='repair' is reserved for D3's precise "
        "localisation)")
    assert out["rejections"][0]["repair_target_param"] == []


def test_d2_only_retrieval_routes_exclusion_unreachable_gap():
    out = _run_isolated("retrieved_exemplar", _D2_ONLY_IR, _D2_ONLY_ROWS)
    assert out["structural"]["fired_detectors"] == ["d2_dead_code_free_vars"]
    assert out["status"] == "gapped"
    assert out["gap_reason"] == "structural_verdict_reject"
    assert out["rejections"][0]["route"] == "exclusion"


# ---- D3-only (unread_declared_param): already covered end-to-end in
#      tests/test_verdict_discrimination_migrated.py
#      (test_unread_varying_param_rejected_then_informs_repair_no_park /
#      test_memo_lookup_with_dead_code_rejected_before_accept_no_park);
#      re-asserted here, minimally, as this file's OWN routing gate.
_D3_ONLY_IR = {"type": "ProgSeq", "stmts": [
    {"type": "ProgDefFnParam", "name": "a", "default": None},
    {"type": "ProgDefFnParam", "name": "b", "default": None},
    {"type": "ProgReturn", "value": {"type": "Var", "name": "a"}},
]}
_D3_ONLY_ROWS = [({"a": 9, "b": 1}, 9), ({"a": 9, "b": 2}, 9)]


def test_d3_only_retrieval_routes_repair_unreachable_gap():
    out = _run_isolated("retrieved_exemplar", _D3_ONLY_IR, _D3_ONLY_ROWS)
    assert out["structural"]["fired_detectors"] == ["d3_unread_declared_param"]
    assert out["status"] == "gapped"
    assert out["gap_reason"] == "structural_verdict_reject"
    rej = out["rejections"][0]
    assert rej["route"] == "repair"
    assert rej["repair_target_param"] == ["b"], (
        "the localisation is recorded even though it could not be used")


def test_d3_only_nonretrieval_routes_repair_reopen():
    out = _run_isolated("d3_decoy", _D3_ONLY_IR, _D3_ONLY_ROWS, budget=1.0)
    assert out["structural"]["fired_detectors"] == ["d3_unread_declared_param"]
    assert out["program"] is None
    assert out["status"] == "gapped"
    assert out["structural"]["reopen_count"] == 1.0
    assert out["excluded"] == ["d3_decoy"]
    rej = out["rejections"][0]
    assert rej["route"] == "repair"
    assert rej["repair_target_param"] == ["b"]


# ---- priority: D1 dominates D3 when both fire (a lookup table that also
#      happens to leave a declared param unread is still "no sub-part to
#      salvage", not "repair one parameter").
_D1_AND_D3_IR = {"type": "ProgSeq", "stmts": [
    {"type": "ProgDefFnParam", "name": "a", "default": None},
    {"type": "ProgDefFnParam", "name": "b", "default": None},
    {"type": "ProgReturn", "value": {
        "type": "IfThenElse",
        "cond": {"type": "Eq", "a": {"type": "Var", "name": "a"},
                 "b": {"type": "Lit", "value": 2}},
        "then": {"type": "Lit", "value": 35},
        "other": {"type": "Lit", "value": 10}}},
]}
_D1_AND_D3_ROWS = [({"a": 2, "b": 9}, 35), ({"a": 3, "b": 1}, 10)]


def test_d1_and_d3_together_routes_as_d1_exclusion_not_repair():
    out = _run_isolated("both_decoy", _D1_AND_D3_IR, _D1_AND_D3_ROWS, budget=1.0)
    assert sorted(out["structural"]["fired_detectors"]) == [
        "d1_memo_lookup_table", "d3_unread_declared_param"]
    rej = out["rejections"][0]
    assert rej["route"] == "exclusion", (
        "D1 dominates D3 in the priority order — a lookup table has no "
        "sub-part to repair regardless of what else it also triggers")
    assert rej["repair_target_param"] == []


# --------------------------------------------------------------------------- #
#  3. THE HEADLINE MEASUREMENT — the 26 ids, disposed.
# --------------------------------------------------------------------------- #
def test_the_26_ids_split_matches_the_measured_retrieval_reopen_partition(
        the_26_ids):
    assert sorted(RETRIEVAL_SOURCED_14 + REOPENED_12) == the_26_ids


def test_retrieval_sourced_ids_gap_directly_never_reopen(live_28):
    for tid in RETRIEVAL_SOURCED_14:
        out = live_28[tid]
        assert out["status"] == "gapped", tid
        assert out["gap_reason"] == "structural_verdict_reject", tid
        assert out["structural"]["reopen_count"] is None, (
            tid, "an unreopenable source must never enter the "
            "exclude/reproposal lane")


def test_reopened_ids_genuinely_tried_and_still_gapped_honestly(live_28):
    """Disposition (b)/(c) of the headline measurement: EVERY one of the
    12 non-retrieval-sourced structural rejections routes into the
    standing exclude/reproposal lane (reopen_count >= 1, an Excluded node
    is minted) and still ends up gapped — NONE of the 26 converts to a
    passing accept on the live 257-task MBPP population (disposition (a)
    is the empty list, reported honestly, not smoothed over: excluding a
    coincidentally-fitting decoy with no NEW discriminating row rarely
    finds the correct generalisation among many equally-fitting
    alternatives — PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md §4 measures this
    directly against the SynthEnumerate engine for br_10's own shape).

    2026-08-01 (arc5 moves, reconciled): task 58 is the ONE exception — it
    now reaches `accepted` (a genuine pass, see
    `test_disposition_a_repaired_to_pass_is_empty` below) via arc5-moves'
    orbit augmentation, a DIFFERENT rung than the reject/reopen mechanism
    this test measures. Held out via `_ARC5_MOVES_PASS_IDS` so S6's own
    claim about the OTHER 11 still bites exactly as measured."""
    for tid in sorted(set(REOPENED_12) - _ARC5_MOVES_PASS_IDS):
        out = live_28[tid]
        assert out["program"] is None, (tid, "no defective candidate ever "
                                        "wrongly accepts")
        assert out["status"] == "gapped", tid
        assert out["gap_reason"] != "structural_verdict_reject", (
            tid, "repair was attempted, so the terminal reason is the "
            "LATER one")
        assert (out["structural"]["reopen_count"] or 0) >= 1.0, tid


def test_disposition_a_repaired_to_pass_is_empty(live_28):
    """The honest headline: zero of the 26 repair into a passing accept
    VIA THE REJECT/REOPEN MECHANISM ITSELF. Stated explicitly, not by
    omission — this is disposition (a).

    2026-08-01 (arc5 moves, reconciled): task 58 now accepts — but NOT via
    repair. Its `structural.reopen_count` is `None` (the CEGIS reopen lane
    never engages for it under the current pipeline: arc5-moves' RUNG 2.6
    finds the correct, symmetric `0 > a*b` via orbit augmentation before
    enumerate ever proposes a rejectable decoy for this goal — verified
    below). Disposition (a) via the mechanism THIS FILE measures is still
    empty; 58's pass is a different mechanism entirely, reported here
    rather than silently folded in."""
    repaired_to_pass = [tid for tid in REOPENED_12
                        if live_28[tid]["status"] == "accepted"]
    assert repaired_to_pass == sorted(_ARC5_MOVES_PASS_IDS & set(REOPENED_12))
    for tid in sorted(_ARC5_MOVES_PASS_IDS & set(REOPENED_12)):
        assert live_28[tid]["structural"]["reopen_count"] is None, (
            tid, "this pass must NOT be attributed to the reject/reopen "
            "mechanism — it never engaged")
    via_repair = [tid for tid in (set(REOPENED_12) - _ARC5_MOVES_PASS_IDS)
                 if live_28[tid]["status"] == "accepted"]
    assert via_repair == []


# --------------------------------------------------------------------------- #
#  4. NO HONEST-SCORE BACKSLIDING.
# --------------------------------------------------------------------------- #
def test_genuine_defects_397_never_accepts_via_repair(live_28):
    """397 (median-of-three via max(a,b), c unread) is a GENUINE defect
    (PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md §2.2's hand-verified
    witness, re-used by tests/test_verdict_discrimination_migrated.py).
    Repairing it into acceptance would be a real regression. It is
    non-retrieval-sourced (D3 fires alone on a codebook-built candidate)
    and DOES reopen — but excluding the decoy supplies no new
    discriminating information (the same mechanism as br_10, §4 of the
    notes), so it stays honestly gapped, never accepted.

    2026-08-01 (arc5 moves, reconciled): this test USED to also cover 404
    (`GENUINE_DEFECT_IDS = [397, 404]`) — see
    `test_task_404_now_accepts_via_a_different_genuinely_correct_program`
    below for why 404 was carved out rather than folded in here: MOVE A
    (orbit augmentation) finds `Min(a,b)`, an actually-correct program
    UNRELATED to the old defective 'bare a, b unread' candidate this test
    was written against — 404 stopped being a genuine defect at all, it
    is not a case of the OLD defect getting wrongly repaired."""
    tid = 397
    out = live_28[tid]
    assert out["program"] is None, tid
    assert out["status"] == "gapped", tid
    assert (out["structural"]["reopen_count"] or 0) >= 1.0, (
        tid, "repair WAS attempted — it correctly did not succeed")


def test_task_404_now_accepts_via_a_different_genuinely_correct_program(live_28):
    """404 ('minimum(a,b)') was ORIGINALLY a genuine defect: a codebook
    candidate reading only `a` (ignoring `b`) that D3 correctly caught and
    reopened, and which never converged from revealed rows alone —
    PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md §2.2's witness. arc5-moves'
    orbit augmentation (PROGRAM_SYNTHESIS_ARC5_MOVES.md) now finds
    `Min(a, b)` for this SAME goal — a DIFFERENT, actually-correct program
    (genuinely symmetric, reads BOTH params) — not a repair of the old
    defect. Verified three ways so this can never be mistaken for the old
    defect slipping through: (1) held-out passes; (2) the reopen mechanism
    never engaged (this did not come from CEGIS repairing the old decoy);
    (3) a constructed witness beyond the task's own rows."""
    out = live_28[404]
    assert out["status"] == "accepted", out["status"]
    assert out["structural"]["reopen_count"] is None, (
        "this accept must not be attributed to the reject/reopen "
        "mechanism (it never engaged) — it is arc5-moves' own rung")
    ir = out["ir"]
    assert ir is not None
    held_out_ok = arc3b.holdout_verdict(ir, out["_held_out"])
    assert held_out_ok["all_ok"], held_out_ok
    # constructed witness: swap the arguments both ways, values the task's
    # own 2 revealed + 1 held-out rows never happen to exercise.
    for a, b, expected in ((100, 3, 3), (3, 100, 3), (-5, -1, -5), (0, 0, 0)):
        out_ev = arc3b.prog_eval(ir, {"a": a, "b": b})
        assert out_ev.get("result") == expected, (a, b, out_ev)


# --------------------------------------------------------------------------- #
#  5. LOOP SAFETY.
# --------------------------------------------------------------------------- #
def test_exclusion_never_mints_the_same_name_twice(live_28):
    """The engine's own `exclude` contract, mint-once, at the granularity
    this phase actually controls (the top-level construction name): for
    every reopened goal, the Excluded-node names it accumulates are all
    DISTINCT — a rejected candidate's construction is never excluded a
    second time (whether or not the SAME named plan is later re-derived
    by the pre-existing arc2-Q4 enum-retry sub-lane, which excludes at
    the SUB-TERM grain instead and is independently gated by
    tests/test_descent_widening_migrated.py — out of this phase's scope)."""
    for tid in REOPENED_12 + GENUINE_DEFECT_IDS:
        excluded = live_28[tid]["excluded"]
        assert len(excluded) == len(set(excluded)), (tid, excluded)


def test_zero_parks_across_the_full_live_257_task_population(test_tasks):
    """The strongest form of the loop-safety claim: run the ENTIRE MBPP
    test split, live, under the current seed, and confirm NO row is left
    at a non-terminal ('stalled:...') outcome — the exact failure mode
    S2's reverted first attempt hit (task 267, `pipeline_stall_
    nonterminal_status`)."""
    runnable, excluded, _elapsed = arc3b.run_pass(
        list(test_tasks.values()), arc3b.boot_full_r3, "primary")
    assert not excluded
    assert len(runnable) == 257
    stalled = [r["task_id"] for r in runnable
              if str(r["outcome"]).startswith("stalled:")]
    assert stalled == []


# 2026-08-01 (arc5 moves, reconciled): task 162 lands in
# `accepted_holdout_fail` via arc5-moves (an honest 2-row coincidental fit
# the held-out check correctly catches, PROGRAM_SYNTHESIS_ARC5_MOVES.md
# §5) — NOT a wrong pass. Held out the same way the exact-first/moves pass
# ids are.
_ARC5_MOVES_ACCEPTED_HOLDOUT_FAIL_IDS = {162}

# 2026-08-01 (arc5 moves, reconciled): running this file's OWN diff turned
# up TWO MORE, entirely PRE-EXISTING coincidental fits in the frozen
# v1.7.0 baseline itself — 92 and 464 — exposed (not introduced) by the
# rational-domain engine landing (arc5, commit 72ed5096a5): SynthEnumerate
# now carries an exact-rational literal in its search space, which changes
# candidate ordering/discovery for ALL of enumerate, not just the exact-
# family rung. Both frozen "pass" programs are independently reconstructed
# and evaluated below via a CONSTRUCTED WITNESS (never merely asserted) —
# proof they were ALREADY wrong in general, not a capability this build
# took away. Per the brief's own standing rule ("arc 4 caught two
# coincidental fits, arc 5 caught a third and a fourth — do not let a
# fifth through"): these are found and reported here as a fifth and sixth,
# now correctly no longer passing, not smoothed over as a bare "before/
# after" diff would have hidden them.
_ENGINE_EXPOSED_COINCIDENTAL_FIT_CORRECTIONS = {92, 464}
# task 77 shares 92's exact decoy exemplar (`Eq(a, Div(1, Div(1, a)))`,
# see the witness below) and was ALREADY non-passing before (accepted_
# holdout_fail) and after (gapped) — a same-cause, zero-score-effect move,
# named for completeness rather than silently absorbed into "changed".
_SAME_CAUSE_NO_SCORE_EFFECT_IDS = {77}

# 2026-08-01 (arc6 seam D, reconciled): the FOURTH attributed cause, in the
# `_ARC5_EXACT_FIRST_PASS_IDS` / `_ARC5_MOVES_PASS_IDS` line. Seam D
# (PROGRAM_SYNTHESIS_ARC6_D.md) added a PROPERTY-REFUTATION rung
# (ps_property_clear / ps_property_reject_gap / ps_property_reject_reopen)
# and a second clause on ps_accept's gate (ps_property_reject == 0.0): a
# candidate that contradicts a property entailed by the task's OWN prompt,
# refuted by a hand-constructed witness executed through the same ProgEval
# term every verdict path uses, is refused BEFORE it can be presented as an
# accept.
#
# EVERY id below was `accepted_holdout_fail` in the frozen v1.7.0 baseline —
# i.e. a KNOWN-WRONG accept, by that artifact's own recorded verdict — and
# is non-accepting now. So this cause only ever converts wrongness into an
# honest gap; it takes no `pass` away (the `gained`/`lost` assertions at the
# end of the diff still bind that independently, and `lost` is unchanged).
#
# The split is not prose: both lists were READ from a live per-id run of
# this same population, each id's `read_goal(...)["property"]` inspected for
# `ps_property_reject == 1.0` plus the firing atom — attribution taken from
# the graph, never from a phase report. Task 77 (also ahf -> gapped) shows
# NO property reject and stays attributed to its own pre-existing cause in
# `_SAME_CAUSE_NO_SCORE_EFFECT_IDS` above.
#
#   DIRECT: the property rejection is the terminal — `gapped:property_
#   verdict_reject`.
_ARC6_PROPERTY_CAUGHT_DIRECT_IDS = frozenset({
    17, 56, 67, 72, 79, 91, 96, 105, 113, 143, 165, 167, 224, 235, 238, 244,
    268, 279, 291, 292, 311, 388, 405, 441, 444, 452, 455,
})
#   REOPEN: the property rung fires (`ps_property_reject == 1.0`, with a
#   non-zero `ps_property_reopen_count`), the standing exclude/reproposal
#   CEGIS lane genuinely retries, and honestly exhausts its budget without
#   a replacement — so the LATER terminal reason wins. This is the exact
#   dynamic PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md already documented for the
#   structural rung's own reopen twin: a correct catch with an honest
#   retry, not a miss. The terminal reason is pinned as measured (twice,
#   independently: the full-population diff and a per-id rerun agreed); a
#   later phase that finds a replacement would move these OFF
#   `enumerate_failed`, which is the improvement direction.
_ARC6_PROPERTY_CAUGHT_REOPEN_IDS = frozenset({171, 256, 295, 300, 389, 392, 453})
_ARC6_PROPERTY_CAUGHT_IDS = (_ARC6_PROPERTY_CAUGHT_DIRECT_IDS
                             | _ARC6_PROPERTY_CAUGHT_REOPEN_IDS)

# 2026-08-02 (ARC 6 TIER 0, reconciled). A FIFTH cause, and the first that
# is an ENUMERATOR REACH change rather than a verdict getting stricter: the
# `SynthEnumerate` op-table widening (eight units, zero new `TermNode`
# variants) makes the enumerator PROPOSE a program for ids it previously
# proposed nothing for, so they leave `gapped:enumerate_failed`.
#
# Attributed separately, exactly like the four causes above, so S6's own
# claim keeps biting over the ids it is about.
_ARC6_TIER0_REACH_IDS = frozenset({74, 98, 106, 120, 161, 249, 257, 290,
                                   393, 424, 450})

# ...and the ONE of them that lands on `pass`, which THIS gate exists to
# scrutinise. Task 120's accepted program is
# `max(36, prod(__item for __item in a[0]))` — it hard-codes 36 (an
# auto-appended spec-output constant) and reads only `a[0]`. It fits every
# revealed AND held-out row of task 120 by accident and is WRONG IN GENERAL
# (constructed witnesses: `a=[[1,1],[1,1]]` -> 36, truth 1;
# `a=[[3,3],[100,100]]` -> 36, truth 10000). It is therefore recorded here
# as a WRONG ACCEPT — the eighth coincidental fit on this project's record —
# and is NOT claimed as an arc-6 conversion. Proven, not asserted, by
# `test_arc6_tier0_wrong_accept_120_is_a_coincidental_fit` below.
_ARC6_TIER0_WRONG_ACCEPT_IDS = frozenset({120})

# ...and the one that lands in `accepted_holdout_fail` — an HONEST catch:
# the enumerator now proposes a program, the accept runs the same held-out
# check every other row does, and the held-out rows correctly refuse it.
# Named so the ahf arithmetic below stays a LIST-backed claim, not a count.
_ARC6_TIER0_AHF_IDS = frozenset({74})


def test_arc6_tier0_wrong_accept_120_is_a_coincidental_fit():
    """2026-08-02 (ARC 6 TIER 0). The task-92/464 method, applied to the ONE
    id the op-table widening moves to `pass`, so the wrong accept rests on a
    PROOF THIS SUITE RUNS rather than on the reconciliation's word.

    The accepted program is `max(36, prod(__item for __item in a[0]))`. It
    hard-codes 36 — an auto-appended spec-OUTPUT constant, the same
    mechanism that produced earlier coincidental fits in this project — and
    it reads only `a[0]`, never the rest of the list. Task 120's own name is
    "maximum product from pairs within a given list", so the truth is a
    reduction over EVERY pair; this program is a constant floored by one
    pair's product.

    Every input below is CONSTRUCTED: none is a revealed row and none is the
    held-out row. Held-out rows are never read here, exactly as everywhere
    else in this arc."""
    sub = srs.Substrate()
    term = {"type": "Max", "items": [
        {"type": "Lit", "value": 36},
        {"type": "Prod",
         "source": {"type": "IndexAt",
                    "seq": {"type": "Var", "name": "a"},
                    "index": {"type": "Lit", "value": 0}},
         "var_name": "__item",
         "value": {"type": "Var", "name": "__item"}}]}

    def truth(pairs):
        return max(x * y for x, y in pairs)

    disagreements = 0
    for a in ([[1, 1], [1, 1]], [[3, 3], [100, 100]],
              [[2, 2], [5, 5], [1, 1]], [[0, 5], [7, 7]]):
        got = sub._inner.evaluate(term, {"a": a})
        if got != truth(a):
            disagreements += 1
    assert disagreements == 4, (
        "every constructed input must expose the fit; got %d/4" % disagreements)
    # ...and it DOES fit the task's own revealed rows, which is precisely why
    # the corpus verdict could not catch it.
    for a, want in (([[2, 7], [2, 6], [1, 8], [4, 9]], 36),
                    ([[10, 20], [15, 2], [5, 10]], 200)):
        assert sub._inner.evaluate(term, {"a": a}) == want


def test_task_92_and_464_frozen_passes_were_already_coincidental_fits():
    """Independent, constructed-witness proof that the two 'lost passes'
    found by the v1.7.0 diff below were NEVER genuinely correct programs —
    reconstructs each frozen program's OWN IR from `results/arc4_endgame.
    json` (never hand-retyped) and evaluates it at inputs its own 2-3
    corpus rows never exercise.

    Task 92 ('is `a` undulating?'): the frozen accept is
    `Eq(a, Div(1, Div(1, a)))` — under EXACT arithmetic this is the
    identity a == a, universally TRUE for any input, so it can never
    correctly implement a predicate the corpus itself says is sometimes
    False (task 92's own revealed row: a=1991 -> False). It only ever
    'passed' because the OLD float engine's round-trip division introduced
    just enough rounding noise on SOME inputs to occasionally read as
    unequal — the coincidence is exposed, not caused, by rational domain's
    NEWLY EXACT division.

    Task 464 ('are all dict values == b?'): the frozen accept is
    `Gt(b, 10)` — it never reads the dict `a` at all (a D3-shaped
    unread-parameter defect that the structural-verdict system's own
    scope did not catch for this particular goal). It happens to agree
    with this task's own 3 rows (b in {10, 12, 5}) purely because they
    straddle 10, but is trivially wrong for any dict whose target value
    isn't near 10."""
    with open(ENDGAME_PATH) as f:
        frozen = json.load(f)
    rows_by_id = {r["task_id"]: r
                 for r in frozen["arms"]["full_a4"]["runnable_rows"]}

    ir92 = rows_by_id[92]["ir"]
    assert ir92 is not None
    for a in (1991, 123, 456, -7):
        out = arc3b.prog_eval(ir92, {"a": a})
        assert out.get("result") is True, (
            a, out, "the frozen program is a universal identity — proof "
            "it cannot implement a sometimes-False predicate")

    ir464 = rows_by_id[464]["ir"]
    assert ir464 is not None
    out_wrong = arc3b.prog_eval(ir464, {"a": {"x": 1, "y": 2}, "b": 11})
    assert out_wrong.get("result") is True, out_wrong  # Gt(11, 10) -- but
    # the dict's values (1, 2) are NOT all == 11, so the correct answer is
    # False: the frozen program is provably wrong here.
    out_right_shape = arc3b.prog_eval(ir464, {"a": {"x": 7, "y": 7}, "b": 7})
    assert out_right_shape.get("result") is False, out_right_shape  # Gt(7,
    # 10) is False, but the dict's values ARE all == 7 -- correct answer
    # is True: the frozen program is wrong in the other direction too.


def test_no_wrong_accept_regression_vs_v1_7_0_baseline(test_tasks):
    """Diffs the FULL live 257-task run against the frozen v1.7.0
    `results/arc4_endgame.json` full_a4 arm: every changed outcome is
    accounted for by one of four attributed causes — arc5 exact-first
    (genuine passes, held-out+witness verified elsewhere), arc5-moves
    (genuine passes/an honest holdout-catch, held-out+witness verified
    elsewhere), S6's own reject/reopen mechanism (tries, honestly still
    gapped — the ORIGINAL claim this file exists to check), or a PRE-
    EXISTING coincidental fit the rational-domain engine change exposed
    (proven wrong-in-general by the constructed witness above) — and
    NOTHING outside those four moves a task into `pass`/`accepted_
    holdout_fail` from nowhere, or touches a task outside the accounted
    populations."""
    with open(ENDGAME_PATH) as f:
        frozen = json.load(f)
    before = {r["task_id"]: r["outcome"]
             for r in frozen["arms"]["full_a4"]["runnable_rows"]}
    runnable, _excluded, _elapsed = arc3b.run_pass(
        list(test_tasks.values()), arc3b.boot_full_r3, "primary")
    after = {r["task_id"]: r["outcome"] for r in runnable}
    assert set(before) == set(after)
    changed = sorted(tid for tid in before if before[tid] != after[tid])
    # 2026-08-01 (arc5 exact-first): a LATER phase legitimately moved the
    # k*pi*r^a*h^b geometry family to `pass` via the shape-first rung —
    # rational parameters + a cross-frame constant, each verified held-out
    # correct. That is an improvement, not the backsliding this test guards
    # against, so it is attributed separately and asserted in its own right.
    # S6's claim — reopening never creates a wrong accept and never touches
    # anything outside the 26 — must still bite exactly as written.
    _ARC5_EXACT_FIRST_PASS_IDS = {82, 85, 139, 233, 276, 312}
    for tid in sorted(_ARC5_EXACT_FIRST_PASS_IDS & set(changed)):
        assert after[tid] == "pass", (tid, after[tid])
    for tid in sorted(_ARC5_MOVES_PASS_IDS & set(changed)):
        assert after[tid] == "pass", (tid, after[tid])
    for tid in sorted(_ARC5_MOVES_ACCEPTED_HOLDOUT_FAIL_IDS & set(changed)):
        assert after[tid] == "accepted_holdout_fail", (tid, after[tid])
    # 2026-08-01 (arc6 seam D, reconciled): a FOURTH cause — the property
    # rung — converts 34 more KNOWN-WRONG accepts into honest gaps. Each is
    # asserted in its own right (below), in the SAME direction as S2's own
    # structural conversions, so S6's claim keeps biting exactly as written
    # over the ids it is about.
    for tid in sorted(_ARC6_PROPERTY_CAUGHT_IDS & set(changed)):
        assert before[tid] == "accepted_holdout_fail", (tid, before[tid])
        assert after[tid].startswith("gapped:"), (tid, after[tid])
    for tid in sorted(_ARC6_PROPERTY_CAUGHT_DIRECT_IDS & set(changed)):
        assert after[tid] == "gapped:property_verdict_reject", (tid, after[tid])
    for tid in sorted(_ARC6_PROPERTY_CAUGHT_REOPEN_IDS & set(changed)):
        assert after[tid] == "gapped:enumerate_failed", (tid, after[tid])
    assert _ARC6_PROPERTY_CAUGHT_IDS <= set(changed), (
        "an id attributed to the property rung no longer moves at all",
        sorted(_ARC6_PROPERTY_CAUGHT_IDS - set(changed)))
    # 2026-08-02 (arc6 tier 0, reconciled): a FIFTH cause — the op-table
    # widening — moves 11 more ids, all of them OFF `gapped:enumerate_failed`
    # (the enumerator now proposes where it proposed nothing). Asserted in
    # its own right, in its own direction, so S6's claim keeps biting.
    for tid in sorted(_ARC6_TIER0_REACH_IDS & set(changed)):
        assert before[tid] == "gapped:enumerate_failed", (tid, before[tid])
        assert after[tid] != "gapped:enumerate_failed", (tid, after[tid])
    # THE WRONG ACCEPT, recorded rather than absorbed: exactly one of them
    # reaches `pass`, and it is a coincidental fit (proven by constructed
    # witness in the dedicated test below). It is pinned as such so that a
    # later phase cannot quietly inherit it as a genuine conversion.
    for tid in sorted(_ARC6_TIER0_WRONG_ACCEPT_IDS & set(changed)):
        assert after[tid] == "pass", (tid, after[tid])
    assert (_ARC6_TIER0_WRONG_ACCEPT_IDS
            == {t for t in _ARC6_TIER0_REACH_IDS if after.get(t) == "pass"}), (
        "the set of arc6-tier0 ids reaching `pass` changed; every one of "
        "them needs a constructed-witness sweep before it may be claimed")
    # 2026-08-02 (arc6 tier 0): `_ARC6_TIER0_WRONG_ACCEPT_IDS` joins the
    # attributed set so the "no UNATTRIBUTED pass" invariant below still
    # means what it says — but note the asymmetry, deliberately: every other
    # member of this union is a witness-VERIFIED gain, and task 120 is a
    # witness-REFUTED one. It is attributed, not endorsed.
    _all_attributed_gains = (_ARC5_EXACT_FIRST_PASS_IDS | _ARC5_MOVES_PASS_IDS
                             | _ARC5_MOVES_ACCEPTED_HOLDOUT_FAIL_IDS
                             | _ARC6_TIER0_WRONG_ACCEPT_IDS)
    s6_changed = sorted(
        set(changed) - _all_attributed_gains
        - _ENGINE_EXPOSED_COINCIDENTAL_FIT_CORRECTIONS
        - _SAME_CAUSE_NO_SCORE_EFFECT_IDS
        - _ARC6_PROPERTY_CAUGHT_IDS
        - _ARC6_TIER0_REACH_IDS)
    assert s6_changed == sorted(
        set(REOPENED_12 + GENUINE_DEFECT_IDS) - _ARC5_MOVES_PASS_IDS), s6_changed
    for tid in s6_changed:
        assert before[tid] == "gapped:structural_verdict_reject", (tid, before[tid])
        assert after[tid].startswith("gapped:"), (tid, after[tid])
        assert after[tid] != "gapped:structural_verdict_reject", (tid, after[tid])
    # the engine-exposed coincidental-fit corrections: BOTH were `pass`
    # before (wrongly) and are NOT `pass` now — proven wrong by the
    # dedicated witness test above, never merely asserted here.
    for tid in sorted(_ENGINE_EXPOSED_COINCIDENTAL_FIT_CORRECTIONS):
        assert before[tid] == "pass", (tid, before[tid])
        assert after[tid] != "pass", (tid, after[tid])
    for tid in sorted(_SAME_CAUSE_NO_SCORE_EFFECT_IDS):
        assert before[tid] != "pass" and after[tid] != "pass", (
            tid, "this id is claimed to have zero score effect")
    pass_before = sum(1 for v in before.values() if v == "pass")
    pass_after = sum(1 for v in after.values() if v == "pass")
    # S6's claim is that REOPENING moves no task into `pass`. Later phases
    # do add passes (attributed above, each held-out+witness verified) and
    # the engine-exposed corrections REMOVE two wrong passes (also
    # witness-verified) — so the invariant is checked with all of those
    # attributed out rather than by a bare count: no id outside the
    # attributed gain sets may become a pass, and the only ids that may
    # STOP being a pass are the two proven-wrong corrections.
    gained = {t for t in after if after[t] == "pass" and before[t] != "pass"}
    lost = {t for t in before if before[t] == "pass" and after[t] != "pass"}
    assert lost == _ENGINE_EXPOSED_COINCIDENTAL_FIT_CORRECTIONS, (
        "a pass was lost outside the two proven-wrong corrections",
        sorted(lost))
    assert gained <= _all_attributed_gains, (
        "a pass appeared outside every attributed gain set",
        sorted(gained - _all_attributed_gains))
    assert pass_after == pass_before + len(gained) - len(lost)
    ahf_before = sum(1 for v in before.values() if v == "accepted_holdout_fail")
    ahf_after = sum(1 for v in after.values() if v == "accepted_holdout_fail")
    # +1 for task 162 (arc5-moves' honest catch, gapped -> ahf), +1 for
    # task 464 (the engine-exposed correction landing in ahf rather than a
    # clean gapped, pass -> ahf), -1 for task 77 (the SAME decoy exemplar
    # as 92's correction, ahf -> gapped now that it is no longer accepted
    # at all) = net +1.
    # 2026-08-01 (arc6 seam D, reconciled): the property rung removes every
    # one of `_ARC6_PROPERTY_CAUGHT_IDS` from `accepted_holdout_fail` (each
    # asserted individually above: ahf before, gapped after), so the net is
    # +1 - 34. Written as the attributed arithmetic rather than as a new
    # bare literal, so a future drift has to name its cause the same way.
    # 2026-08-02 (arc6 tier 0, reconciled): +1 more for task 74, an HONEST
    # catch -- the widened enumerator now PROPOSES a program where it
    # previously proposed nothing, the accept runs the same held-out check
    # every other row does, and the held-out rows correctly refuse it. Named
    # via `_ARC6_TIER0_AHF_IDS` so this stays a LIST-backed claim.
    assert ahf_after == (ahf_before + 1 - len(_ARC6_PROPERTY_CAUGHT_IDS)
                         + len(_ARC6_TIER0_AHF_IDS)), (ahf_before, ahf_after)
    for tid in _ARC6_TIER0_AHF_IDS:
        assert before[tid] == "gapped:enumerate_failed", (tid, before[tid])
        assert after[tid] == "accepted_holdout_fail", (tid, after[tid])
    assert before[77] == "accepted_holdout_fail" and after[77] == "gapped:enumerate_failed", (
        77, before[77], after[77])


# --------------------------------------------------------------------------- #
#  6. br_10_top_of_three — root-caused, not faked.
# --------------------------------------------------------------------------- #
def test_br_10_root_caused_non_convergence():
    """PROGRAM_SYNTHESIS_ARC4_S5.md's named residual: does br_10 converge
    again under `repair_oracle`? Under S6's OWN reject-informs-repair
    mechanism ALONE, still measured NO — `test_br_10_exhaustive_
    reenumeration_finds_nothing_from_revealed_rows_alone` (this file,
    unchanged, still green) proves directly against the engine that
    excluding the `Max(a,b)` decoy and exhaustively re-searching size<=5
    over ONLY the 3 revealed rows finds nothing: no discriminating signal,
    root cause unchanged.

    2026-08-01 (arc5 moves, reconciled): br_10_top_of_three NOW CONVERGES
    end-to-end under `repair_oracle` — but via an ENTIRELY DIFFERENT,
    LATER-landed mechanism (PROGRAM_SYNTHESIS_ARC5_MOVES.md's MOVE A,
    orbit augmentation), not via S6's reject/reopen repair path this test
    was written to pin. Per this test's own built-in guidance (the
    `pytest.fail` block this replaces): retired the stale failure-mode
    assertions and verified the convergence against a FRESH witness (not
    just the fixture's own held-out rows), attributed to its real cause."""
    import prog_synthesis_battery as psb
    with open(P7_TASKS_PATH) as f:
        tasks = json.load(f)["tasks"]
    task = next(t for t in tasks if t["id"] == "br_10_top_of_three")
    row = psb.run_task_p7(task, "repair_oracle")

    assert row["outcome"] == "accepted_holdout_ok", row["outcome"]
    # the reopen/oracle-feedback lane was never reached — this converged
    # on the FIRST pass, before any counterexample-feedback round.
    oracle = row["oracle"]
    assert oracle["rounds"] == 0
    assert oracle["ce_fed"] is None
    assert oracle["pre_feedback_outcome"] == "accepted_holdout_ok"
    # fresh witness, independent of the fixture's own held-out rows.
    ir = row["ir"]
    for a, b, c, expected in ((100, 3, 47, 100), (-1, -50, -2, -1),
                              (0, 0, 0, 0), (9, 9, 8, 9)):
        out_ev = arc3b.prog_eval(ir, {"a": a, "b": b, "c": c})
        assert out_ev.get("result") == expected, (a, b, c, out_ev)


def test_br_10_no_longer_reaches_the_reject_reopen_path_at_all():
    """Distinguishes 'S6's reopen fires and succeeds' (false — see the
    test above) from 'the decoy is never even proposed' (true, verified
    directly): arc5-moves' RUNG 2.6 sits BEFORE enumerate would ever
    propose the unaugmented `Max(a,b)` decoy for this goal, so the
    structural-verdict detector this test used to pin
    (`d3_unread_declared_param`) never fires at all — S6's reject/reopen
    mechanism is not 'tried and succeeded', it is superseded upstream.
    The mechanism itself is still exercised and gated elsewhere in this
    file (the D1/D2/D3 isolated harness in §2, and 397/14/103/... in
    §3's `live_28`) — this test only pins br_10's OWN new path."""
    import prog_synthesis_battery as psb
    with open(P7_TASKS_PATH) as f:
        tasks = json.load(f)["tasks"]
    task = next(t for t in tasks if t["id"] == "br_10_top_of_three")
    s, ag = psb.boot_p7("repair_oracle")
    examples = [(r["inputs"], r["expected"]) for r in task["example_rows"]]
    r = psy.synthesize_from_request(s, ag, task["request_text"], examples)
    out = psy.read_goal(s, r["goal"])
    assert out["structural"]["fired_detectors"] == []
    assert out["structural"]["reopen_count"] is None
    assert out["rejections"] == []
    assert out["status"] == "accepted"
    goal_attrs = s.node(r["goal"])["attrs"]
    assert goal_attrs.get("ps_move_sel_kind") == "orbit_augment"
    assert goal_attrs.get("ps_rung_moves") == 1.0


def test_br_10_exhaustive_reenumeration_finds_nothing_from_revealed_rows_alone():
    """The precise, DIRECT engine-level evidence behind the root cause:
    excluding br_10's decoy (`Max(a,b)`) and exhaustively re-searching
    size<=5 terms over ONLY the 3 revealed rows finds NOTHING — those 3
    rows already agree with the decoy on every row, so there is no
    discriminating signal for the search to prefer any alternative."""
    excl = json.dumps({"items": [{"name": "a", "type": "Var"},
                                 {"name": "b", "type": "Var"}],
                       "type": "Max"})
    rows = [
        {"inputs": {"a": 1, "b": 9, "c": 3}, "output": 9},
        {"inputs": {"a": 7, "b": 2, "c": 5}, "output": 7},
        {"inputs": {"a": 4, "b": 4, "c": 4}, "output": 4},
    ]
    s = srs.Substrate()
    spec = {"type": "SynthEnumerate", "examples": {"type": "Lit", "value": rows},
           "max_size": 5, "max_candidates": 0, "saturate_k": 0, "field": "",
           "exclude": {"type": "Lit", "value": [excl]}}
    out = s._inner.evaluate(spec, {})
    assert out.get("found") is False
    assert out.get("halt_reason") == "max_size", (
        "an EXHAUSTIVE search, not a budget cutoff — there genuinely is "
        "no alternative fit for these 3 rows once the decoy is excluded")

    # Control: the SAME engine finds the correct generalisation trivially
    # once a genuinely discriminating 4th row (one the decoy fails) is
    # present — proving the search mechanism itself is not the bottleneck.
    rows4 = rows + [{"inputs": {"a": 2, "b": 4, "c": 11}, "output": 11}]
    spec4 = {"type": "SynthEnumerate", "examples": {"type": "Lit", "value": rows4},
            "max_size": 9, "max_candidates": 0, "saturate_k": 0, "field": ""}
    out4 = s._inner.evaluate(spec4, {})
    assert out4.get("found") is True
    assert out4.get("halt_reason") == "solved"
