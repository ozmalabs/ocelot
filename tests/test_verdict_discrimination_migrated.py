"""tests/test_verdict_discrimination_migrated.py — Arc 4 Phase S2: VERDICT
DISCRIMINATION landed as seed rules (seeds/program_synthesis.json v1.7.0,
domains/prog_synthesis.py's `compute_structural_facts`).

PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md measured seven structural
detectors OFFLINE, on a frozen JSON dict (`scripts/arc4_structural_
verdicts.py` / `results/arc4_structural_verdicts.json`): three had
non-zero recall AND held precision (D1 memo_lookup_table 1.00, D2
dead_code_free_vars 1.00, D3 unread_declared_param 0.88 — its 3 "false
positives" are label noise, hand-verified genuine defects). This suite
gates the LIVE landing of those same three decisions as GRAPH-NATIVE
rules: the accepted candidate IS a reflected Term subgraph already
sitting in the substrate (`Term.<Variant>` nodes, `child.<field>` edges),
so `compute_structural_facts` (domains/prog_synthesis.py) WALKS THAT
GRAPH (never re-parses the `ps_ir` JSON string) to record D1/D2/D3's raw
facts, and `ps_structural_reject`/`ps_structural_clear`
(seeds/program_synthesis.json v1.7.0) READ those facts and decide —
facts in, rules decide, the CLAUDE.md discipline this whole codebase is
built on.

Gates:
  1. RE-DERIVATION — the live graph-native walk reproduces the frozen
     measurement's own per-detector trap/false-positive id lists EXACTLY,
     over the SAME frozen 76-trap/21-correct population
     (`results/mbpp_arc3_endgame.json`'s `full_r3` rows), for D1/D2/D3.
  2. PRECISION — each detector's live-recomputed precision matches or
     exceeds the frozen measurement (1.00/1.00/0.88); the 3 D3 false
     positives (397, 404, 433) are independently re-verified as GENUINE
     defects via a hand-constructed witness (never a held-out row),
     exactly as PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md §2.2 recorded.
  3. REJECT-BEFORE-ACCEPT / NO PARK — a detector-fired candidate never
     mints an accepted Program node; the goal reaches the honest terminal
     'gapped' (ps_gap_reason := 'structural_verdict_reject') directly —
     never a park at 'verified'/'pending'/'counterexample'.
  4. EXPLAINABILITY — every rejection mints a `Rejection` node naming
     WHICH detector(s) fired.
  5. SCOPE DISCIPLINE — a descend-hole's own fold-up accept (P7-A/P7-B,
     `ps_rung_descend == 1.0`) is left completely untouched (no facts
     computed, `ps_accept` unblocked) — the measured catalogue was taken
     over FULL-R3's FLAT top-level accepts only.
  6. HELD-OUT ISOLATION — a mechanical source-text audit: no new
     structural-fact function's source contains the substring "held_out".
  7. NO-PYTHON-DECISION audit on the new code (the ink-suite pattern,
     reused from tests/test_program_synthesis_migrated.py).
  8. Seed version / rule-count pin (v1.7.0, +2 rules over v1.6.0's 58).

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_verdict_discrimination_migrated.py
"""
from __future__ import annotations

import inspect
import json
import os
import re
import sys
from pathlib import Path
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
import mbpp_arc3_battery as bat  # noqa: E402
import arc4_failure_anatomy as afa  # noqa: E402

from domains import prog_synthesis as psy  # noqa: E402

FROZEN_R3_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")
STRUCT_ARTIFACT_PATH = os.path.join(ROOT, "results", "arc4_structural_verdicts.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")

DETECTOR_KEY = {
    "d1": "d1_memo_lookup_table",
    "d2": "d2_dead_code_free_vars",
    "d3": "d3_unread_declared_param",
}


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
def frozen_r3():
    with open(FROZEN_R3_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def struct_artifact():
    with open(STRUCT_ARTIFACT_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def tasks_by_id():
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = bat.q0_split_tasks(all_tasks)
    return {t["task_id"]: t for t in splits["test"]}


@pytest.fixture(scope="module")
def seed_manifest():
    with open(SEED_PATH) as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
#  a fresh, minimal synthetic goal — enough graph state for
#  `compute_structural_facts` to run, without going through the whole
#  propose/lattice/screen machinery (that machinery is exercised by
#  tests/test_program_synthesis_migrated.py already; this file's job is
#  the STRUCTURAL DETECTOR + verdict-routing layer itself).
# --------------------------------------------------------------------------- #
def _fresh_goal(*, depth: float = 0.0, rung_descend=None,
               construction: str = "probe", attempts: float = 1.0,
               budget: float = 5.0):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    attrs: Dict[str, Any] = {
        "kind": "synth_program", "status": "evaluated",
        "ps_attempts": attempts, "ps_budget": budget,
        "ps_depth": depth, "ps_construction": construction,
        "ps_reflect_ok": 1.0,
    }
    if rung_descend is not None:
        attrs["ps_rung_descend"] = rung_descend
    g = s.add_node("Goal", attrs)
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
    """Mirror `eval_and_record`'s own reflect step (mechanical, the exact
    same `add_term_subgraph` call the real adapter uses) and set the goal
    to 'evaluated' so ps_row_pass/ps_verified can run — a MINIMAL stand-in
    for the full propose/bind/eval chain, using the SAME reflection
    primitive."""
    root = s._inner.add_term_subgraph(ir)
    s.add_edge_unchecked(g, "ps_ir_reflected", root)
    s.set_attr(g, "ps_ir", json.dumps(ir))
    s.set_attr(g, "ps_attempts", attempt)
    return root


def _fired_detectors_for(ir: Dict[str, Any], revealed_rows: List[Dict[str, Any]]
                         ) -> tuple:
    """The re-derivation primitive: build a throwaway goal carrying
    `revealed_rows` as ExampleRow nodes (never a held-out row — this
    function's own parameter list proves it), reflect `ir`, and call the
    SAME `compute_structural_facts` the live seed rules gate on. Returns
    the sorted tuple of fired detector names."""
    s, ag, g, m = _fresh_goal()
    for rr in revealed_rows:
        _add_row(s, m, rr["inputs"], rr["expected"])
    root = s._inner.add_term_subgraph(ir)
    s.add_edge_unchecked(g, "ps_ir_reflected", root)
    psy.compute_structural_facts(s, ag, g)
    at = s.node(g)["attrs"]
    return tuple(sorted(psy._plain(at.get("ps_st_fired_detectors")) or ()))


# --------------------------------------------------------------------------- #
#  1. RE-DERIVATION vs the frozen measurement, over the SAME 76/21
#     population (never re-run — read from the frozen artifacts, exactly
#     the pattern `scripts/arc4_structural_verdicts.py` itself uses).
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def live_rederivation(frozen_r3, tasks_by_id):
    rows = frozen_r3["arms"]["full_r3"]["runnable_rows"]
    ahf_rows = [r for r in rows if r["outcome"] == "accepted_holdout_fail"]
    pass_rows = [r for r in rows if r["outcome"] == "pass"]
    out = {"d1": {"trap": [], "fp": []}, "d2": {"trap": [], "fp": []},
           "d3": {"trap": [], "fp": []}}
    for r in ahf_rows:
        revealed = afa._revealed_rows_for_task(r["task_id"], tasks_by_id)  # noqa: SLF001
        fired = _fired_detectors_for(r["ir"], revealed)
        for k, dname in DETECTOR_KEY.items():
            if dname in fired:
                out[k]["trap"].append(r["task_id"])
    for r in pass_rows:
        revealed = afa._revealed_rows_for_task(r["task_id"], tasks_by_id)  # noqa: SLF001
        fired = _fired_detectors_for(r["ir"], revealed)
        for k, dname in DETECTOR_KEY.items():
            if dname in fired:
                out[k]["fp"].append(r["task_id"])
    for k in out:
        out[k]["trap"].sort()
        out[k]["fp"].sort()
    return out


@pytest.mark.parametrize("key", ["d1", "d2", "d3"])
def test_rederivation_trap_ids_match_frozen_measurement(
        key, live_rederivation, struct_artifact):
    dname = DETECTOR_KEY[key]
    expect = struct_artifact["per_detector"][dname]["trap_task_ids"]
    assert live_rederivation[key]["trap"] == expect, (
        "%s trap-id divergence vs the frozen measurement" % dname)


@pytest.mark.parametrize("key", ["d1", "d2", "d3"])
def test_rederivation_false_positive_ids_match_frozen_measurement(
        key, live_rederivation, struct_artifact):
    dname = DETECTOR_KEY[key]
    expect = struct_artifact["per_detector"][dname]["false_positive_task_ids"]
    assert live_rederivation[key]["fp"] == expect, (
        "%s false-positive-id divergence vs the frozen measurement" % dname)


def test_task_267_fires_d1_and_d2_live(frozen_r3, tasks_by_id):
    """The headline pinned shape: `return (35 if (a - 2) else 10)` preceded
    by dead-code statements referencing free vars `n`/`b`."""
    rows = {r["task_id"]: r for r in frozen_r3["arms"]["full_r3"]["runnable_rows"]}
    revealed = afa._revealed_rows_for_task(267, tasks_by_id)  # noqa: SLF001
    fired = _fired_detectors_for(rows[267]["ir"], revealed)
    assert "d1_memo_lookup_table" in fired
    assert "d2_dead_code_free_vars" in fired


# --------------------------------------------------------------------------- #
#  2. PRECISION — matches/exceeds the frozen measurement; the 3 D3 false
#     positives are hand-verified GENUINE defects, not detector error.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("key,frozen_precision", [
    ("d1", 1.00), ("d2", 1.00), ("d3", 0.88)])
def test_precision_no_worse_than_frozen_measurement(
        key, frozen_precision, live_rederivation):
    tp = len(live_rederivation[key]["trap"])
    fp = len(live_rederivation[key]["fp"])
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    assert precision >= frozen_precision - 1e-6, (
        "%s precision regressed: %.4f < frozen %.4f" % (key, precision, frozen_precision))


def test_d3_false_positives_are_the_three_known_label_noise_ids(live_rederivation):
    """PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md §2.2's own three ids —
    recorded here as EXPECTED-AND-CORRECT rejections, not FPs to explain
    away."""
    assert live_rederivation["d3"]["fp"] == [397, 404, 433]


def test_d3_known_false_positives_are_genuine_defects_on_a_fresh_witness(frozen_r3):
    """Independently re-verifies each of the 3 `pass`-labelled-but-
    structurally-flagged tasks is a GENUINE defect: a hand-constructed
    witness input — never a held-out row, never revealed to the detector —
    disagrees with the obvious true relation the prompt names. This is
    the honest-score instruction's own evidentiary basis: rejecting these
    RAISES correctness even though it LOWERS the raw pass-rate metric."""
    rows = {r["task_id"]: r for r in frozen_r3["arms"]["full_r3"]["runnable_rows"]}

    ir397 = rows[397]["ir"]
    witness = {"a": 1, "b": 5, "c": 3}
    out = bat.prog_eval(ir397, dict(witness))
    assert out.get("result") != sorted(witness.values())[1]  # true median is 3, program returns 5

    ir404 = rows[404]["ir"]
    witness = {"a": 5, "b": 1}
    out = bat.prog_eval(ir404, dict(witness))
    assert out.get("result") != min(witness.values())  # true min is 1, program returns 5

    ir433 = rows[433]["ir"]
    witness = {"b": 3, "a": [1, 2]}
    out = bat.prog_eval(ir433, dict(witness))
    true_answer = all(witness["b"] > x for x in witness["a"])
    assert out.get("result") != true_answer  # 3 IS greater than every element of [1, 2]


# --------------------------------------------------------------------------- #
#  3. REJECT-BEFORE-ACCEPT / NO PARK — end to end, through the REAL
#     seed rules (psy.pump), not just the fact-computation primitive.
# --------------------------------------------------------------------------- #
def test_memo_lookup_with_dead_code_rejected_before_accept_no_park():
    """Task-267-shaped: a lookup-table dispatch with a dead-code free var.
    Task 267 is RETRIEVAL-sourced in the real population (`pr_ladder_
    accept` — no codebook trigger ever matched it, which is WHY it fell to
    retrieval) — `construction='retrieved_exemplar'` here matches that
    fact precisely (Arc4-S6: since S6, that is exactly the ONE condition
    under which D1/D2 route straight to 'gapped' instead of reopening —
    see PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md; a retrieval accept has no
    OTHER exemplar a named exclusion can distinguish, so reopening it was
    the measured S2 stall, PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md Sec.4).
    Rejected BEFORE accept — no Program node is ever minted — and the
    goal reaches the honest terminal 'gapped' directly (never a
    counterexample/exclude/reproposal park)."""
    s, ag, g, m = _fresh_goal(construction="retrieved_exemplar",
                              attempts=1.0, budget=5.0)
    _add_row(s, m, {"a": 2}, 10, attempt=1.0)
    _add_row(s, m, {"a": 3}, 35, attempt=1.0)
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgAssignVar", "name": "v2",
         "value": {"type": "Plus", "items": [{"type": "Var", "name": "a"},
                                             {"type": "Var", "name": "b"}]}},
        {"type": "ProgReturn", "value": {
            "type": "IfThenElse",
            "cond": {"type": "Minus", "a": {"type": "Var", "name": "a"},
                     "b": {"type": "Lit", "value": 2}},
            "then": {"type": "Lit", "value": 35},
            "other": {"type": "Lit", "value": 10}}},
    ]}
    _reflect_and_verify(s, g, ir, attempt=1.0)
    psy.pump(s, ag)
    out = psy.read_goal(s, g)
    assert out["structural"]["any_fired"] == 1.0
    assert sorted(out["structural"]["fired_detectors"]) == [
        "d1_memo_lookup_table", "d2_dead_code_free_vars"]
    assert out["program"] is None, "no Program node was ever minted"
    assert out["status"] == "gapped", "the honest terminal — not a park"
    assert out["gap_reason"] == "structural_verdict_reject"
    assert out["structural"]["reopen_count"] is None, (
        "an unreopenable (retrieval) source must never enter the "
        "counterexample/exclude lane")
    assert out["rejections"][0]["route"] == "exclusion"
    assert out["excluded"] == [], "nothing was ever excluded — no reopen"


def test_unread_varying_param_rejected_then_informs_repair_no_park():
    """Task-397-shaped: median(a,b,c) implemented as max(a,b) — `c` is
    declared, never read, and varies across the revealed rows. Task 397
    is CODEBOOK-sourced in the real population (construction
    'mck_prog_assign_var_n2_q9', never 'retrieved_exemplar') — Arc4-S6
    routes a D3-only rejection on a non-retrieval source into the
    STANDING exclude/reproposal lane instead of straight to 'gapped'
    (PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md): the Rejection still names the
    ignored parameter ('repair_target_param' == ('c',)) and an Excluded
    node retires this exact construction name (loop safety — it can never
    be re-proposed identically) before the goal reaches its terminal.
    `budget == attempts` here so the SAME firing that mints the exclusion
    ALSO finds the integer budget already spent (`ps_ce_exhausted`) —
    an honest, immediate exhaustion that exercises the reopen-then-give-up
    path without needing a real codebook/enumerate rig in this minimal
    fixture (the full 257-task live MBPP battery, run separately, proves
    the same lane converges to a DIFFERENT candidate for goals that do
    have search budget left — see PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md's own
    disposition table). The terminal gap_reason is 'exhausted', not
    'structural_verdict_reject' — informing repair genuinely tries again
    before giving up, so the ORIGINAL diagnosis is preserved on the
    Rejection node, not on the final gap_reason string."""
    s, ag, g, m = _fresh_goal(construction="median_via_max", attempts=1.0, budget=1.0)
    _add_row(s, m, {"a": 1, "b": 5, "c": 3}, 5, attempt=1.0)
    _add_row(s, m, {"a": 2, "b": 4, "c": 9}, 4, attempt=1.0)
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgDefFnParam", "name": "b", "default": None},
        {"type": "ProgDefFnParam", "name": "c", "default": None},
        {"type": "ProgReturn", "value": {
            "type": "IfThenElse",
            "cond": {"type": "Gt", "a": {"type": "Var", "name": "a"},
                     "b": {"type": "Var", "name": "b"}},
            "then": {"type": "Var", "name": "a"},
            "other": {"type": "Var", "name": "b"}}},
    ]}
    _reflect_and_verify(s, g, ir, attempt=1.0)
    psy.pump(s, ag)
    out = psy.read_goal(s, g)
    assert out["structural"]["fired_detectors"] == ["d3_unread_declared_param"]
    assert out["program"] is None, "the genuine defect is never accepted"
    assert out["status"] == "gapped", "the honest terminal — not a park"
    assert out["gap_reason"] == "exhausted", (
        "repair was genuinely attempted (exclude+reopen) before honestly "
        "giving up, so the terminal reason is the LATER one, not the "
        "original structural diagnosis")
    assert out["structural"]["reopen_count"] == 1.0
    assert out["excluded"] == ["median_via_max"], (
        "exclusion bites: this exact construction can never be "
        "re-proposed identically")
    assert len(out["rejections"]) == 1
    rej = out["rejections"][0]
    assert rej["route"] == "repair"
    assert rej["repair_target_param"] == ["c"], (
        "the ignored parameter IS the localization handed to repair — "
        "preserved on the Rejection even though the goal later exhausts")


def test_correct_candidate_accepts_normally_zero_false_positive():
    """A genuinely correct max(a,b) (both params read) must NOT be
    structurally flagged — the precision-first control for the two tests
    above."""
    s, ag, g, m = _fresh_goal(construction="real_max", attempts=1.0, budget=5.0)
    _add_row(s, m, {"a": 1, "b": 5}, 5)
    _add_row(s, m, {"a": 7, "b": 2}, 7)
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgDefFnParam", "name": "b", "default": None},
        {"type": "ProgReturn", "value": {
            "type": "IfThenElse",
            "cond": {"type": "Gt", "a": {"type": "Var", "name": "a"},
                     "b": {"type": "Var", "name": "b"}},
            "then": {"type": "Var", "name": "a"},
            "other": {"type": "Var", "name": "b"}}},
    ]}
    _reflect_and_verify(s, g, ir, attempt=1.0)
    psy.pump(s, ag)
    out = psy.read_goal(s, g)
    assert out["structural"]["any_fired"] == 0.0
    assert out["structural"]["reject"] == 0.0
    assert out["status"] == "accepted"
    assert out["program"] is not None


# --------------------------------------------------------------------------- #
#  4. EXPLAINABILITY — the Rejection node names the firing detector(s).
# --------------------------------------------------------------------------- #
def test_rejection_provenance_names_the_firing_detectors():
    s, ag, g, m = _fresh_goal(construction="lookup_decoy2", attempts=1.0, budget=1.0)
    _add_row(s, m, {"a": 2}, 10)
    _add_row(s, m, {"a": 3}, 35)
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": {
            "type": "IfThenElse",
            "cond": {"type": "Minus", "a": {"type": "Var", "name": "a"},
                     "b": {"type": "Lit", "value": 2}},
            "then": {"type": "Lit", "value": 35},
            "other": {"type": "Lit", "value": 10}}},
    ]}
    _reflect_and_verify(s, g, ir, attempt=1.0)
    psy.pump(s, ag)
    out = psy.read_goal(s, g)
    assert out["status"] == "gapped"
    assert len(out["rejections"]) == 1
    rej = out["rejections"][0]
    assert rej["detectors"] == ["d1_memo_lookup_table"]
    assert rej["construction"] == "lookup_decoy2"
    assert rej["attempt"] == 1.0


# --------------------------------------------------------------------------- #
#  5. SCOPE DISCIPLINE — a descend-tagged goal (ps_rung_descend == 1.0) is
#     left completely untouched: no facts computed, ps_accept unblocked.
#     The measured catalogue was taken over FULL-R3's FLAT top-level
#     accepts (PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md); a descend
#     hole's own fold-up accept — and the P7-B repair lane that corrects
#     it via a LOCALIZED counterexample, a strictly more targeted fix —
#     is out of scope for this rung by design.
# --------------------------------------------------------------------------- #
def test_descended_goal_is_never_structurally_gated():
    """The SAME structurally-flagged shape (unread, varying param) that
    test_unread_varying_param_rejected... catches at ps_depth==0 must NOT
    be touched when ps_rung_descend==1.0 -- compute_structural_facts
    returns False (no-op) and the goal accepts exactly as it would with
    v1.6.0 (pre-Arc4-S2)."""
    s, ag, g, m = _fresh_goal(construction="median_via_max_descended",
                              attempts=1.0, budget=5.0, rung_descend=1.0)
    _add_row(s, m, {"a": 1, "b": 5, "c": 3}, 5)
    _add_row(s, m, {"a": 2, "b": 4, "c": 9}, 4)
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgDefFnParam", "name": "b", "default": None},
        {"type": "ProgDefFnParam", "name": "c", "default": None},
        {"type": "ProgReturn", "value": {
            "type": "IfThenElse",
            "cond": {"type": "Gt", "a": {"type": "Var", "name": "a"},
                     "b": {"type": "Var", "name": "b"}},
            "then": {"type": "Var", "name": "a"},
            "other": {"type": "Var", "name": "b"}}},
    ]}
    _reflect_and_verify(s, g, ir, attempt=1.0)
    moved = psy.compute_structural_facts(s, ag, g)
    assert moved is False
    assert s.node(g)["attrs"].get("ps_st_computed") is None
    psy.pump(s, ag)
    out = psy.read_goal(s, g)
    assert out["status"] == "accepted"
    assert out["structural"]["computed"] is None


def test_depth_scoping_also_holds_for_sub_goals():
    """A P7-A sub-goal (ps_depth >= 1) is likewise never gated, regardless
    of ps_rung_descend — the OTHER half of the same OR-guard in ps_accept."""
    s, ag, g, m = _fresh_goal(construction="hole_partial", attempts=1.0,
                              budget=5.0, depth=1.0)
    _add_row(s, m, {"a": 2}, 10)
    _add_row(s, m, {"a": 3}, 35)
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": {
            "type": "IfThenElse",
            "cond": {"type": "Minus", "a": {"type": "Var", "name": "a"},
                     "b": {"type": "Lit", "value": 2}},
            "then": {"type": "Lit", "value": 35},
            "other": {"type": "Lit", "value": 10}}},
    ]}
    _reflect_and_verify(s, g, ir, attempt=1.0)
    moved = psy.compute_structural_facts(s, ag, g)
    assert moved is False
    psy.pump(s, ag)
    out = psy.read_goal(s, g)
    assert out["status"] == "accepted"


# --------------------------------------------------------------------------- #
#  6. HELD-OUT ISOLATION — mechanical source-text audit of every new
#     structural-fact function.
# --------------------------------------------------------------------------- #
_ST_FUNCTIONS = (
    psy._st_hashable, psy._st_walk, psy._st_has_type, psy._st_var_refs,
    psy._st_bound_names, psy._st_returns, psy._st_single_child,
    psy._st_is_equality_like_literal_test, psy._st_literal_dispatch,
    psy._st_params, psy.compute_structural_facts,
)


def test_held_out_isolation_source_audit():
    hits = {fn.__name__: ("held_out" in inspect.getsource(fn))
            for fn in _ST_FUNCTIONS}
    assert not any(hits.values()), hits


def test_structural_functions_take_only_graph_and_ir_derived_args():
    """None of the new functions accept a parameter literally named
    `spec`/`held_out` — the isolation guard the rest of this codebase
    already enforces at the signature level (test_structural_verdicts_
    migrated.py's own `test_detector_functions_take_only_ir_and_
    revealed_rows` precedent)."""
    banned = {"spec", "held_out", "held_out_rows"}
    for fn in _ST_FUNCTIONS:
        params = set(inspect.signature(fn).parameters)
        assert not (params & banned), (fn.__name__, params)


# --------------------------------------------------------------------------- #
#  7. NO-PYTHON-DECISION audit — the ink-suite pattern, reused verbatim
#     from tests/test_program_synthesis_migrated.py's own gate (the WHOLE
#     adapter file is already covered there; this re-runs the identical
#     check here so this suite is self-contained and would independently
#     catch a regression even if run alone).
# --------------------------------------------------------------------------- #
_BANNED_CALL_RE = re.compile(
    r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)


def test_no_python_decisions_in_structural_verdict_code():
    src = Path(psy.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)


def test_compute_structural_facts_never_sets_status_or_mints_program():
    """The adapter records FACTS only — the seed rules decide the status
    transition and mint the Program/Rejection nodes. A mechanical source
    scan of just this verb (not the whole file, which legitimately sets
    status elsewhere for OTHER verbs) proves it."""
    src = inspect.getsource(psy.compute_structural_facts)
    assert '"status"' not in src
    assert "'status'" not in src
    assert "accepted_program" not in src
    assert "Program" not in src


# --------------------------------------------------------------------------- #
#  8. seed version / rule-count pin.
# --------------------------------------------------------------------------- #
def test_seed_version_bumped_and_two_new_rules(seed_manifest):
    """Retained name for git-blame continuity; the S6 body below documents
    the ACTUAL v1.8.0 shape (4 detector/source-routed rules replacing the
    single v1.7.0 ps_structural_reject — PROGRAM_SYNTHESIS_ARC4_S6_
    NOTES.md)."""
    # 2026-08-01 arc5 exact-first: shape-first rung added (v1.8.0 -> v1.9.0).
    # 2026-08-01 arc5 moves, reconciled: v1.9.0 -> v1.10.0, RUNG 2.6 added
    # (ps_move_mark/_select/_none/_fresh_attempt, PROGRAM_SYNTHESIS_ARC5_
    # MOVES.md) — none of the four is structural-reject/-clear, so this
    # file's own S6-detector assertions below are unaffected.
    # 2026-08-01 arc6 SEAM D, reconciled: v1.10.0 -> v1.11.0, 70 -> 73.
    # +3 PROPERTY-REFUTATION rules (ps_property_clear / ps_property_reject_
    # gap / ps_property_reject_reopen — the D1/D2 structural-exclusion pair
    # mirrored for prompt-entailed program properties, PROGRAM_SYNTHESIS_
    # ARC6_D.md §1) and ONE edit to ps_accept's gate (it now additionally
    # requires ps_property_reject == 0.0 beside ps_structural_reject ==
    # 0.0). The property rung reads a DISJOINT attr family (ps_prop_* /
    # ps_property_*) from this file's structural detectors (ps_st_* /
    # ps_structural_*) — PROGRAM_SYNTHESIS_ARC6_D.md §4 re-derives the
    # D1/D2/D3 trap and false-positive id lists byte-identically with the
    # property rung installed — so every S6-detector assertion below is
    # unaffected; pure version/count pin update.
    assert seed_manifest["version"] == "1.12.0"  # 2026-08-03: 1.11.0 -> 1.12.0, the goal-residual weight term
    # (ps_move_mark stamps ps_move_w_residual; ps_move_select subtracts a
    # held refutation's weight inside its Argmax). Pin reconciled, not
    # relaxed -- see PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md GR4.
    names = {r["name"] for r in seed_manifest["rules"]}
    assert "ps_structural_reject" not in names, (
        "v1.7.0's single rule was REPLACED, not kept alongside the new ones")
    assert "ps_structural_clear" in names
    for n in ("ps_structural_reject_exclusion_gap",
              "ps_structural_reject_exclusion_reopen",
              "ps_structural_reject_repair_gap",
              "ps_structural_reject_repair_reopen"):
        assert n in names
    # 66 = 60 (v1.7.0) - 1 + 4 (S6); + 4 more (arc5 moves' RUNG 2.6) = 70;
    # + 3 more (arc6 seam D's property rung) = 73.
    assert len(seed_manifest["rules"]) == 73


def test_rejection_edge_production_registered(seed_manifest):
    prods = seed_manifest["productions"]
    assert any(p["edge_type"] == "has_structural_rejection"
              and p["src"]["type"] == "Goal" and p["tgt"]["type"] == "Rejection"
              for p in prods)
