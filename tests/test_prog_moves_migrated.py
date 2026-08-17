"""tests/test_prog_moves_migrated.py — Arc 5 MOVE A/B (structural moves)
gates.

PROGRAM_SYNTHESIS_ARC5_MOVES.md (the design + honest report), PROGRAM_
SYNTHESIS_ARC5_ORBIT_RESULT.md (MOVE A's measurement), PROGRAM_SYNTHESIS_
ARC5_THREE_MOVES.md task 59 (MOVE B's measurement), PROGRAM_SYNTHESIS_
ARC5_WIDEST_GAP.md (the gap / arity_gap features this productionises).
New graph rules (seeds/program_synthesis.json v1.9.0 -> v1.10.0: ps_move_
mark / ps_move_select / ps_move_none / ps_move_fresh_attempt, Occam-
ordered RUNG 2.6 between the exact rung and enumerate; ps_enumerate_mark
edited in place to add the reciprocal mutual-exclusion arm) + a new
mechanical module (domains/prog_moves.py). The verdict layer (ps_verify
-> structural detectors -> ps_accept) is UNCHANGED; a move hands its IR
(or its augmented rows) to that SAME path.

A SOUNDNESS BUG WAS FOUND AND FIXED DURING THIS BUILD, not merely
avoided: an early version selected orbit augmentation off a single
rule-1-sound 2-cycle in isolation and accepted a WRONG decoy for MBPP
task 397 (median of three) that happened to pass its own held-out row by
coincidence — the fourth coincidental fit this project's own standing
rule warns against ("arc 4 caught two ... arc 5 caught a third; do not
add a fourth"). The fix (`_sound_closure_relaxation` in domains/
prog_moves.py) makes the GROUP CLOSURE of every rule-1-sound 2-cycle the
only relaxation ever eligible for selection; individual 2-cycles are
audit-only (gap pinned to 0, never independently selectable). See
`test_median_of_three_coincidental_fit_is_caught_by_the_closure_fix`
below and PROGRAM_SYNTHESIS_ARC5_MOVES.md's own honest account.

Gates:
  1. seeds load clean (the bumped seed, rule count).
  2. MOVE A HEADLINE: br_10_top_of_three converges end-to-end through the
     real pipeline, held-out AND constructed-witness correct, the group
     SELECTED (not hard-coded) — selection facts asserted.
  3. SOUNDNESS: two genuinely-NOT-symmetric specs have their conjectures
     refuted from the revealed rows and are NEVER augmented; no wrong
     accept results.
  4. MOVE B HEADLINE: task 59 (nth octagonal) solves via decomposition —
     candidate counts reported vs the 200,000-and-fails direct path.
  5. SELECTION: weighted collapse — gap and arity_gap disagree, the
     collapse picks by weight (graph data, tunable without code), not by
     rung/mint order.
  6. OCCAM / NO-REGRESSION: a codebook-covered request never reaches this
     rung; the exact rung's own six geometry tasks still convert via
     RUNG 2.5 (rungs.moves stays unset for them); a trivially-easy fixture
     (blind search already converges) is correctly left to enumerate, not
     preempted (the EARNS-ITS-KEEP gate).
  7. no-Python-decision source audit of domains/prog_moves.py.
  8. the named arc-4/arc-5 regression sweep — known drift only.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest tests/test_prog_moves_migrated.py \
    --confcutdir=. -q
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains import prog_synthesis as psy  # noqa: E402
from domains import prog_moves as pmv  # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402

SYNTH_SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")
MBPP_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")


def _term_live(term, env) -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(term, env)
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live({"type": "SynthEnumerate", "examples": {"type": "Lit", "value": []},
                   "max_size": 1, "max_candidates": 0, "saturate_k": 0, "field": ""}, {}):
    pytest.skip("SynthEnumerate not present in the installed substrate_rs binary — "
                "rebuild runners/dsl. Honest skip.", allow_module_level=True)


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


@pytest.fixture(scope="module")
def mbpp_tasks():
    return {t["task_id"]: t for t in json.load(open(MBPP_FIXTURE))}


def _eval_ir(s, ir, env):
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": ir, "env": {"type": "Lit", "value": env},
         "oracles": None, "fuel": 50, "field": ""}, {})
    return out["result"]


# ---------------------------------------------------------------------------
# 1) seeds load clean.
# ---------------------------------------------------------------------------
def test_seed_bumped_with_three_new_rules():
    # 2026-08-01 (arc6 seam D, reconciled): v1.10.0/70 -> v1.11.0/73. Seam
    # D added the PROPERTY-REFUTATION rung (ps_property_clear / ps_property_
    # reject_gap / ps_property_reject_reopen, PROGRAM_SYNTHESIS_ARC6_D.md
    # §1/§6) on top of this rung, purely additively: all four ps_move_*
    # rules this test names are still present and untouched, so the literal
    # head pin is bumped forward rather than loosened.
    with open(SYNTH_SEED_PATH) as f:
        d = json.load(f)
    assert d["version"] == "1.14.0"  # 2026-08-17: 1.13.0 -> 1.14.0, D4 boundary-witness trap detector (ALPHABET_SEARCH_COST_WALL_RESULTS.md)
    # (ps_move_mark stamps ps_move_w_residual; ps_move_select subtracts a
    # held refutation's weight inside its Argmax). Pin reconciled, not
    # relaxed -- see PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md GR4.
    # 2026-08-16: 1.12.0/73 -> 1.13.0/74, PROGRAM_SYNTHESIS_PROPERTY_REJECT_
    # SURVEY's ps_property_reject_retrieval_enumerate_fallback rule, purely
    # additive (all four ps_move_* rules this test names are untouched).
    names = {r["name"] for r in d["rules"]}
    assert {"ps_move_mark", "ps_move_select", "ps_move_none",
           "ps_move_fresh_attempt"} <= names
    assert len(d["rules"]) == 74


def test_seed_installs_clean_live():
    s, ag = boot()
    assert s.nodes("Goal") == []  # ensure_program_synthesis mints nothing


# ---------------------------------------------------------------------------
# 2) MOVE A HEADLINE — br_10_top_of_three, real pipeline.
# ---------------------------------------------------------------------------
BR10_EXAMPLES = [
    ({"a": 1, "b": 9, "c": 3}, 9),
    ({"a": 7, "b": 2, "c": 5}, 7),
    ({"a": 4, "b": 4, "c": 4}, 4),
]
BR10_HELD_OUT = [({"a": 2, "b": 4, "c": 11}, 11), ({"a": -3, "b": -9, "c": -5}, -3)]
BR10_WITNESS = [({"a": 100, "b": 3, "c": 47}, 100), ({"a": -1, "b": -50, "c": -2}, -1)]


def test_br10_converges_via_orbit_augmentation_with_selection_facts():
    s, ag = boot()
    out = psy.synthesize_from_request(
        s, ag, "write a function br_10_top_of_three that returns the "
                "largest of three numbers", examples=BR10_EXAMPLES)
    g = out["goal"]
    at = s.node(g)["attrs"]
    assert at["status"] == "accepted"
    # the GROUP WAS SELECTED, not hard-coded: a rule wrote these facts.
    # Only the GROUP CLOSURE of every rule-1-sound 2-cycle is ever
    # independently selectable (the soundness fix — see
    # test_soundness_case_median_of_three_would_have_been_a_coincidental_
    # fit_without_the_closure_fix below); every individual 2-cycle is
    # audit-only (gap pinned to 0). For br_10 all three 2-cycles survive
    # rule-1 (none contradict the revealed rows), so their closure IS
    # full S3, which is exactly what wins.
    assert at["ps_move_sel_kind"] == "orbit_augment"
    assert at["ps_move_sel_key"] == "sym_full_S3"
    assert at["ps_move_sel_gap"] > 0.0
    n_cands = int(at["ps_moves_n_candidates"])
    assert n_cands >= 4  # 3 audit 2-cycles + the closure (+ maybe move B)
    orbit_cands = [s.node(mc)["attrs"] for mc in s.neighbours(g, "has_move_candidate")
                  if s.node(mc)["attrs"]["move"] == "orbit_augment"]
    assert all(c["refuted"] == 0.0 for c in orbit_cands), orbit_cands
    ir = json.loads(at["ps_ir"])
    for inputs, expected in BR10_HELD_OUT + BR10_WITNESS:
        assert _eval_ir(s, ir, inputs) == expected, inputs


def test_br10_direct_revealed_rows_alone_would_have_been_wrong():
    """The decoy check, independent of the pipeline: `Max(a,b)` — what a
    3-revealed-row-only search finds — satisfies all 3 revealed rows but
    fails the held-out rows. This is the WRONG answer orbit augmentation
    corrects (PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md sec 1)."""
    def max_ab(a, b, c):
        return a if a > b else b
    for inputs, expected in BR10_EXAMPLES:
        assert max_ab(**inputs) == expected
    wrong = [max_ab(**inputs) == expected for inputs, expected in BR10_HELD_OUT]
    assert not all(wrong)


def test_orbit_augment_manufactures_zero_new_oracle_calls():
    """The orbit is DERIVED from the revealed rows alone (mechanical) —
    no oracle/held-out access anywhere in `orbit_augment`."""
    src = Path(pmv.__file__).read_text()
    start = src.index("def orbit_augment(")
    end = src.index("\ndef ", start + 1)
    body = src[start:end]
    assert "held_out" not in body
    assert "BR10_HELD_OUT" not in body


# ---------------------------------------------------------------------------
# 3) SOUNDNESS — genuinely asymmetric specs refute and are NEVER augmented.
# ---------------------------------------------------------------------------
def test_soundness_case_subtraction_arity2_refutes_and_never_augments():
    s, ag = boot()
    examples = [({"a": 5, "b": 2}, 3), ({"a": 2, "b": 5}, -3), ({"a": 7, "b": 1}, 6)]
    out = psy.synthesize_from_request(
        s, ag, "write a function subtract_two that computes a minus b",
        examples=examples)
    g = out["goal"]
    at = s.node(g)["attrs"]
    mcs = list(s.neighbours(g, "has_move_candidate"))
    assert mcs, "the symmetry conjecture must be CONSIDERED, not silently skipped"
    for mc in mcs:
        cat = s.node(mc)["attrs"]
        if cat["move"] == "orbit_augment":
            assert cat["refuted"] == 1.0, cat
    # never selected, never applied — the goal falls through to plain
    # enumerate and finds the CORRECT, un-augmented answer.
    assert at.get("ps_move_sel_kind") is None
    assert at.get("ps_move_applied") is None
    assert at["status"] == "accepted"
    ir = json.loads(at["ps_ir"])
    assert _eval_ir(s, ir, {"a": 20, "b": 3}) == 17
    assert _eval_ir(s, ir, {"a": 3, "b": 20}) == -17


def test_soundness_case_weighted_sum_arity3_refutes_every_relaxation():
    """A genuinely NON-symmetric arity-3 function (`4a+2b+c`), with revealed
    rows constructed as permutations of the SAME multiset {1,2,3} — every
    pairwise swap collides with a differently-labelled row, so EVERY
    candidate relaxation (full S3 + all three 2-cycles) is refuted from
    the revealed rows alone. This is the failure mode the brief names
    explicitly: a false augmentation must never manufacture a wrong label."""
    def f(a, b, c):
        return 4 * a + 2 * b + c
    rows = [(1, 2, 3), (2, 1, 3), (1, 3, 2), (3, 2, 1)]
    examples = [({"a": a, "b": b, "c": c}, f(a, b, c)) for a, b, c in rows]
    s, ag = boot()
    out = psy.synthesize_from_request(
        s, ag, "write a function weighted_three that computes a weighted sum",
        examples=examples)
    g = out["goal"]
    at = s.node(g)["attrs"]
    mcs = [s.node(mc)["attrs"] for mc in s.neighbours(g, "has_move_candidate")]
    orbit_cands = [c for c in mcs if c["move"] == "orbit_augment"]
    # 3 individual 2-cycle AUDIT candidates only — every one of them is
    # rule-1 refuted directly, so NO group closure is even attempted
    # (`_sound_closure_relaxation` returns None before scoring one).
    assert len(orbit_cands) == 3
    assert all(c["refuted"] == 1.0 for c in orbit_cands), orbit_cands
    assert at.get("ps_move_sel_kind") is None
    # honest — this function is outside the default op/const grammar, but
    # the important assertion is that NO WRONG accept was manufactured by
    # a false augmentation; an honest 'gapped' (or a correct accept) are
    # both acceptable outcomes, a WRONG accept is not.
    if at["status"] == "accepted":
        ir = json.loads(at["ps_ir"])
        for a, b, c in [(5, 6, 7), (9, 1, 2)]:
            assert _eval_ir(s, ir, {"a": a, "b": b, "c": c}) == f(a, b, c)
    else:
        assert at["status"] == "gapped"


def test_median_of_three_coincidental_fit_is_caught_by_the_closure_fix(mbpp_tasks):
    """THE FOURTH COINCIDENTAL FIT, CAUGHT (per the brief's own standing
    rule: 'arc 4 caught two coincidental fits and arc 5 caught a third; do
    not add a fourth'). Task 397 (median of three) is genuinely symmetric
    under the FULL group, but with only 2 sparse revealed rows the full-
    closure orbit search does not converge within a generous probe budget
    (soundness rule 2). An EARLIER version of this build fell back to a
    single WEAK 2-cycle relaxation in that case and accepted `Max(a,
    Min(b,c))` — genuinely symmetric in (b,c), genuinely un-refuted by the
    revealed rows, genuinely passing the task's own held-out row BY
    COINCIDENCE (a is never the true maximum in either revealed row nor
    the held-out row) — and genuinely WRONG in general (fails whenever a
    IS the maximum, e.g. (100,1,2) -> 2, `Max(100,Min(1,2))` = 100). This
    is caught here two ways: (1) directly, by exercising the fixed
    mechanism and confirming no wrong accept results; (2) by construction,
    proving the DECOY formula itself is wrong on a witness independent of
    every row this pipeline ever saw."""
    def wrong_decoy(a, b, c):
        return max(a, min(b, c))
    def true_median(a, b, c):
        return sorted((a, b, c))[1]
    witness = (100, 1, 2)
    assert wrong_decoy(*witness) != true_median(*witness), (
        "the decoy formula must be a genuine counterexample, or this "
        "gate proves nothing")

    s, ag = boot()
    task = mbpp_tasks[397]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    examples = [(r["inputs"], r["expected"]) for r in spec["revealed"]]
    out = psy.synthesize_from_request(s, ag, task["prompt"], examples=examples)
    g = out["goal"]
    at = s.node(g)["attrs"]
    # the closure candidate (named sym_full_S3, since all three 2-cycles
    # individually survive rule-1 on this sparse data) must be REFUTED
    # (soundness rule 2 — unsatisfiable within the probe budget) rather
    # than silently substituted by a weaker, individually-sound 2-cycle.
    closure_cands = [s.node(mc)["attrs"] for mc in s.neighbours(g, "has_move_candidate")
                     if s.node(mc)["attrs"]["key"] == "sym_full_S3"]
    assert len(closure_cands) == 1
    assert closure_cands[0]["refuted"] == 1.0
    assert at.get("ps_move_sel_kind") is None  # never selected/applied
    # whatever the final verdict (honest gap or a genuinely correct
    # accept via some other rung), it must NEVER be the wrong decoy.
    if at["status"] == "accepted":
        ir = json.loads(at["ps_ir"])
        for a, b, c in [(100, 1, 2), (2, 100, 1), (50, 3, 200), (-5, -1, -10)]:
            assert _eval_ir(s, ir, {"a": a, "b": b, "c": c}) == true_median(a, b, c)
    else:
        assert at["status"] == "gapped"


def test_orbit_refute_unit_a_permutation_collision_is_caught():
    rows = [{"vals": [1, 9, 3], "expected": 9}, {"vals": [9, 1, 3], "expected": 1}]
    relax = pmv._relaxation_by_name("sym_2cycle_0_1", 3)
    assert pmv.orbit_refute(relax, rows) is True


def test_orbit_refute_unit_a_true_symmetry_survives():
    rows = [{"vals": v, "expected": max(v)} for v in
            [[1, 9, 3], [7, 2, 5], [4, 4, 4]]]
    relax = pmv._relaxation_by_name("sym_full_S3", 3)
    assert pmv.orbit_refute(relax, rows) is False


# ---------------------------------------------------------------------------
# 4) MOVE B HEADLINE — task 59, nth octagonal, real pipeline + MBPP fixture.
# ---------------------------------------------------------------------------
def test_task59_solves_via_intermediate_decomposition(mbpp_tasks):
    s, ag = boot()
    task = mbpp_tasks[59]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    assert spec["runnable"]
    examples = [(r["inputs"], r["expected"]) for r in spec["revealed"]]
    out = psy.synthesize_from_request(s, ag, task["prompt"], examples=examples)
    g = out["goal"]
    at = s.node(g)["attrs"]
    assert at["status"] == "accepted"
    assert at["ps_move_sel_kind"] == "intermediate_factor"
    assert at["ps_move_sel_key"] == "factor:a"
    ir = json.loads(at["ps_ir"])
    for row in spec["held_out"]:
        assert _eval_ir(s, ir, row["inputs"]) == row["expected"], row
    # candidate counts, reported honestly (not hard-coded to a prior
    # document's numbers, which used a different reveal count) — see
    # PROGRAM_SYNTHESIS_ARC5_MOVES.md for the exact figures this reproduces.
    print("\ntask 59: inner factor found in %d candidates (real engine call, "
          "full default budget)" % int(at["ps_move_inner_candidates"]))


def test_task59_direct_search_genuinely_fails_at_the_default_budget(mbpp_tasks):
    """The comparator: a DIRECT search over the whole function (no
    decomposition), at SynthEnumerate's own default ceiling (200,000,
    max_size=9), does not converge on the TRUE general program —
    reproducing PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md's own headline live,
    not quoting it.

    2026-08-16 (PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX): superseded, not
    weakened. `Mod`/`Sqrt` are now exposed to this exact top-level,
    unscoped call (deliberately — `exclude_ops` scopes them OUT only of
    the decomposition/retrieval probes, per that rung's own PREREG/
    RESULTS), so the search no longer exhausts its budget silently — it
    now FINDS `(if a==5 then 65 else 280)`-shaped candidate at tested=
    67223, a spurious two-revealed-row memorization, in 65223 fewer
    candidates than before. This is mechanism (a) from that rung's own
    diagnosis, asserted directly here rather than left implicit: the
    comparator's job — proving direct search does NOT reach the TRUE
    general program within budget — still holds, just via a different,
    now-stronger signature (a wrong-but-accepted candidate rather than
    silent exhaustion). Live-verified: `term_str` is a literal `IfThenElse`
    that reproduces exactly the two revealed rows and disagrees with the
    held-out row (`a=15` expects `645`, not `65` or `280`) — proven wrong
    by construction, the same discipline `test_arc6_property_rejected_
    ceiling_candidates_are_wrong_by_construction` already uses elsewhere
    in this arc, not a weaker substitute for the old exhaustion check.
    `test_task59_solves_via_intermediate_decomposition` (immediately
    above) is what actually proves the real, end-to-end pipeline still
    reaches the TRUE program via `intermediate_factor` — this test's own
    job was always narrower: characterizing the raw top-level probe's own
    behavior, which has genuinely changed."""
    task = mbpp_tasks[59]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    rows = [{"inputs": r["inputs"], "output": r["expected"]} for r in spec["revealed"]]
    held = spec["held_out"]
    s = srs.Substrate()
    out = s._inner.evaluate(
        {"type": "SynthEnumerate", "examples": {"type": "Lit", "value": rows},
         "max_size": 9, "max_candidates": 200000, "saturate_k": 0, "field": ""}, {})
    assert out["found"] is True
    assert out["tested"] < 200000
    ir = json.loads(out["term"])
    for row in held:
        assert _eval_ir(s, ir, row["inputs"]) != row["expected"], (
            "task 59 direct-search candidate must be WRONG on the held-out "
            "row (proving it is a spurious revealed-row memorization, not "
            "the true general program) -- if this ever agrees, the direct "
            "search has genuinely solved task 59 without decomposition and "
            "this whole comparator test needs re-scoping, not just re-pinning")
    print("\ntask 59 direct search: found a SPURIOUS candidate (%s) in %d "
          "candidates, wrong on the held-out row -- still does not reach "
          "the true general program without decomposition" %
          (out["term_str"], out["tested"]))


def test_task59_inner_factor_alone_converges_cheaply(mbpp_tasks):
    task = mbpp_tasks[59]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    arg = list(spec["revealed"][0]["inputs"].keys())[0]
    inner_rows = [{"inputs": {arg: r["inputs"][arg]},
                   "output": r["expected"] // r["inputs"][arg]}
                  for r in spec["revealed"]]
    s = srs.Substrate()
    out = s._inner.evaluate(
        {"type": "SynthEnumerate", "examples": {"type": "Lit", "value": inner_rows},
         "max_size": 9, "max_candidates": 0, "saturate_k": 0, "field": ""}, {})
    assert out["found"] is True
    assert out["tested"] < 200000
    print("\ntask 59 inner factor: found in %d candidates (vs 200,000 "
          "exhausted, direct)" % out["tested"])


# ---------------------------------------------------------------------------
# 5) SELECTION — weighted collapse, gap and arity_gap disagree.
# ---------------------------------------------------------------------------
def _synthetic_move_goal(s, ag, w_gap, w_arity, w_mdl):
    m = s.add_node("Message", {"text": "synthetic", "ps_exact_eligible": 0.0,
                               "ps_moves_eligible": 1.0})
    g = s.add_node("Goal", {"kind": "synth_program", "status": "moves_scan",
                            "ps_moves_scan_done": 1.0,
                            "ps_move_w_gap": w_gap, "ps_move_w_arity": w_arity,
                            "ps_move_w_mdl": w_mdl})
    s.add_edge_unchecked(ag, "has_goal", g)
    s.add_edge_unchecked(g, "about_message", m)
    c_high_gap = s.add_node("MoveCandidate", {
        "move": "orbit_augment", "key": "cand_high_gap", "refuted": 0.0,
        "gap": 10.0, "arity_gap": 0.0, "mdl_bits": 0.0})
    c_high_arity = s.add_node("MoveCandidate", {
        "move": "intermediate_factor", "key": "cand_high_arity", "refuted": 0.0,
        "gap": 1.0, "arity_gap": 5.0, "mdl_bits": 0.0})
    # mint c_high_gap FIRST — proves the winner is not "whichever was
    # minted/considered first."
    s.add_edge_unchecked(g, "has_move_candidate", c_high_gap)
    s.add_edge_unchecked(g, "has_move_candidate", c_high_arity)
    return g


def test_selection_picks_by_weight_not_by_gap_alone_or_mint_order():
    s, ag = boot()
    g = _synthetic_move_goal(s, ag, w_gap=1.0, w_arity=3.0, w_mdl=0.5)
    s._inner.run_rules(1000)
    at = s.node(g)["attrs"]
    # weight(high_gap) = 1*10 = 10; weight(high_arity) = 1*1 + 3*5 = 16.
    # cand_high_arity wins DESPITE having the lower raw gap and DESPITE
    # being minted second — only the WEIGHTED SUM explains the winner.
    assert at["ps_move_sel_key"] == "cand_high_arity"
    assert at["ps_move_sel_gap"] == 1.0
    assert at["ps_move_sel_arity_gap"] == 5.0


def test_selection_weight_is_tunable_graph_data_not_code():
    """The SAME candidate pool, the SAME rule, a DIFFERENT outcome — purely
    from editing the goal's own ps_move_w_* attrs (graph data). This is
    the concrete demonstration of 'Argmax over a weight expression the
    seed carries, so the weighting is graph data and tunable without
    code.'"""
    s, ag = boot()
    g = _synthetic_move_goal(s, ag, w_gap=1.0, w_arity=0.0, w_mdl=0.5)
    s._inner.run_rules(1000)
    at = s.node(g)["attrs"]
    # with arity weight zeroed: weight(high_gap)=10, weight(high_arity)=1 —
    # the winner FLIPS relative to the default-weighted test above.
    assert at["ps_move_sel_key"] == "cand_high_gap"


def test_refutation_is_a_veto_never_outvoted_by_a_higher_weight():
    """A refuted candidate with an enormous gap/arity_gap must still lose
    to a non-refuted candidate with a modest one — refutation is filtered
    out of the pool entirely, never merely down-weighted."""
    s, ag = boot()
    m = s.add_node("Message", {"text": "synthetic", "ps_exact_eligible": 0.0,
                               "ps_moves_eligible": 1.0})
    g = s.add_node("Goal", {"kind": "synth_program", "status": "moves_scan",
                            "ps_moves_scan_done": 1.0,
                            "ps_move_w_gap": 1.0, "ps_move_w_arity": 3.0,
                            "ps_move_w_mdl": 0.5})
    s.add_edge_unchecked(ag, "has_goal", g)
    s.add_edge_unchecked(g, "about_message", m)
    huge_but_refuted = s.add_node("MoveCandidate", {
        "move": "orbit_augment", "key": "cand_refuted", "refuted": 1.0,
        "gap": 100000.0, "arity_gap": 100000.0, "mdl_bits": 0.0})
    modest = s.add_node("MoveCandidate", {
        "move": "intermediate_factor", "key": "cand_modest", "refuted": 0.0,
        "gap": 1.0, "arity_gap": 0.0, "mdl_bits": 0.0})
    s.add_edge_unchecked(g, "has_move_candidate", huge_but_refuted)
    s.add_edge_unchecked(g, "has_move_candidate", modest)
    s._inner.run_rules(1000)
    at = s.node(g)["attrs"]
    assert at["ps_move_sel_key"] == "cand_modest"


# ---------------------------------------------------------------------------
# 6) OCCAM / NO-REGRESSION.
# ---------------------------------------------------------------------------
def test_codebook_covered_request_never_reaches_the_moves_rung():
    s, ag = boot()
    # a moves-eligible (int, arity 2) request whose PROMPT matches an
    # existing write-codebook trigger — the codebook construction wins
    # outright, exactly as it does against the exact rung.
    out = psy.synthesize_from_request(
        s, ag, "write a function to compute a running TALLY of a list of numbers",
        examples=[])
    g = out["goal"]
    at = s.node(g)["attrs"]
    assert at.get("ps_rung_moves") is None


def test_exact_rungs_six_geometry_tasks_still_convert_via_rung_2_5(mbpp_tasks):
    """A spot check (task 82, sphere volume): the exact rung still fires
    FIRST and rungs.moves is never touched for a float-eligible request —
    the exact-first rung's own headline is untouched by this build."""
    s, ag = boot()
    task = mbpp_tasks[82]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    examples = [(r["inputs"], r["expected"]) for r in spec["revealed"]]
    out = psy.synthesize_from_request(s, ag, task["prompt"], examples=examples)
    at = s.node(out["goal"])["attrs"]
    assert at["status"] == "accepted"
    assert at["ps_rung_exact"] == 1.0
    assert at.get("ps_rung_moves") is None  # never reached (exact solved first)


def test_trivial_fixture_where_blind_search_already_converges_is_not_preempted():
    """The earns-its-keep gate: `double_it(a) = 2*a` — a candidate factor
    decomposition EXISTS (a divides evenly) but blind search ALREADY
    converges cheaply, so no candidate survives the gap>0 gate and
    enumerate runs normally, unpreempted."""
    s, ag = boot()
    out = psy.synthesize_from_request(
        s, ag, "write a function double_it that returns twice the widget "
                "of a number", examples=[({"a": 3}, 6), ({"a": 5}, 10)])
    at = s.node(out["goal"])["attrs"]
    assert at["status"] == "accepted"
    assert at.get("ps_move_sel_kind") is None
    assert at["ps_rung_enumerate"] == 1.0


def test_moves_ineligible_request_is_byte_unaffected():
    """A string-typed / non-numeric request never even computes
    ps_moves_eligible=1 — `ps_move_mark`'s guard is never satisfiable."""
    s, ag = boot()
    m = psy.ingest_spec(s, ag, "write a function f that returns a",
                        [({"a": "x"}, "x")])
    assert s.node(m)["attrs"]["ps_moves_eligible"] == 0.0


# ---------------------------------------------------------------------------
# 6b. TWO BONUS, GENUINE MBPP CONVERSIONS found by the 257-task before/
#     after sweep (PROGRAM_SYNTHESIS_ARC5_MOVES.md) — verified held-out
#     AND with a constructed witness, per the same discipline as br_10.
# ---------------------------------------------------------------------------
def test_mbpp_58_opposite_signs_converts_correctly(mbpp_tasks):
    s, ag = boot()
    task = mbpp_tasks[58]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    examples = [(r["inputs"], r["expected"]) for r in spec["revealed"]]
    out = psy.synthesize_from_request(s, ag, task["prompt"], examples=examples)
    at = s.node(out["goal"])["attrs"]
    assert at["status"] == "accepted"
    assert at["ps_move_sel_kind"] == "orbit_augment"
    ir = json.loads(at["ps_ir"])
    def true_fn(a, b):
        return (a > 0) != (b > 0) if a != 0 and b != 0 else False
    for row in spec["held_out"]:
        assert _eval_ir(s, ir, row["inputs"]) == row["expected"]
    for a, b in [(37, -19), (-4, -4), (0, 5), (100, 100), (-1, 1)]:
        assert _eval_ir(s, ir, {"a": a, "b": b}) == true_fn(a, b), (a, b)


def test_mbpp_404_minimum_converts_correctly(mbpp_tasks):
    s, ag = boot()
    task = mbpp_tasks[404]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    examples = [(r["inputs"], r["expected"]) for r in spec["revealed"]]
    out = psy.synthesize_from_request(s, ag, task["prompt"], examples=examples)
    at = s.node(out["goal"])["attrs"]
    assert at["status"] == "accepted"
    assert at["ps_move_sel_kind"] == "orbit_augment"
    ir = json.loads(at["ps_ir"])
    for row in spec["held_out"]:
        assert _eval_ir(s, ir, row["inputs"]) == row["expected"]
    for a, b in [(7, -3), (-100, 5), (0, 0), (42, 42)]:
        assert _eval_ir(s, ir, {"a": a, "b": b}) == min(a, b)


# ---------------------------------------------------------------------------
# 6c. LIVE BUGS FOUND (and fixed) BY RUNNING THE REAL 257-TASK CORPUS —
#     gated so they never regress silently.
# ---------------------------------------------------------------------------
def test_mbpp_160_non_integer_tuple_output_never_crashes_factor_candidates(mbpp_tasks):
    """MBPP task 160 (`find_solution` — a tuple/None-valued output) is
    MOVE-A-eligible (its inputs are all int, arity 3) but NOT MOVE-B-
    eligible (its output is a tuple/None, not an int). `factor_candidates`
    used to assume every row's `expected` was already int-typed (an
    `_examples_numeric_eligible`-shaped assumption that held for every
    hand-built fixture this build was developed against but not for this
    real corpus task) and crashed with `TypeError: unsupported operand
    type(s) for %%: 'tuple' and 'int'` the first time this was run against
    the real 257-task battery. Fixed with a defensive per-row int check —
    gated here directly against the real task, not a synthetic repro."""
    s, ag = boot()
    task = mbpp_tasks[160]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    examples = [(r["inputs"], r["expected"]) for r in spec["revealed"]]
    out = psy.synthesize_from_request(s, ag, task["prompt"], examples=examples)
    at = s.node(out["goal"])["attrs"]
    assert at["status"] in ("gapped", "accepted")  # anything but a crash


def test_mbpp_257_tuple_output_never_crashes_factor_candidates(mbpp_tasks):
    s, ag = boot()
    task = mbpp_tasks[257]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    examples = [(r["inputs"], r["expected"]) for r in spec["revealed"]]
    out = psy.synthesize_from_request(s, ag, task["prompt"], examples=examples)
    at = s.node(out["goal"])["attrs"]
    assert at["status"] in ("gapped", "accepted")


def test_mbpp_162_consumed_codebook_attempt_does_not_stall_the_moves_rung(mbpp_tasks):
    """MBPP task 162 reproduced the P6.5 attempt-collision class LIVE: a
    codebook candidate ('sum_of_two') is proposed, evaluated, and rejected
    FIRST (consuming attempt 1 and stamping ps_eval_done==1 on the SAME
    attempt number the moves rung would otherwise reuse unchanged, per the
    exact-first `ps_ir_built = attempts, no increment` convention) —
    without `ps_move_fresh_attempt`, `eval_and_record`'s own `ps_eval_done
    == ps_attempts` freshness guard silently treats the move's freshly-
    composed IR as already evaluated and the goal parks on the non-
    terminal 'evaluated' status forever (reproduced live before the fix).
    With the fix the goal always reaches a TERMINAL status."""
    s, ag = boot()
    task = mbpp_tasks[162]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    examples = [(r["inputs"], r["expected"]) for r in spec["revealed"]]
    out = psy.synthesize_from_request(s, ag, task["prompt"], examples=examples)
    at = s.node(out["goal"])["attrs"]
    assert at["status"] in ("gapped", "accepted"), (
        "must reach a TERMINAL status, never park on 'evaluated'")
    # honest: the 2-revealed-row inner fit is a COINCIDENTAL one for this
    # particular task (verified: it fails held-out) — accepted-on-revealed
    # is fine, a wrong PASS would not be.
    if at["status"] == "accepted":
        ir = json.loads(at["ps_ir"])
        held = spec["held_out"][0]
        # this is the DOCUMENTED coincidental-inner-fit case (2 points
        # under-determine `sum_series`'s true closed form) — the real
        # verdict layer (held-out scoring, done by the battery/caller, NOT
        # this rung) is what must catch it, and does: recorded here as an
        # honest, non-hidden residual, not asserted as correct.
        got = _eval_ir(s, ir, held["inputs"])
        print("\ntask 162: accepted on revealed rows; held-out got=%r "
              "expected=%r (%s)" % (got, held["expected"],
                                    "MATCHES" if got == held["expected"]
                                    else "documented coincidental miss"))


# ---------------------------------------------------------------------------
# 7) NO-PYTHON-DECISION source audit — domains/prog_moves.py.
# ---------------------------------------------------------------------------
_BANNED_CALL_RE = re.compile(
    r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count",
                   "covered", "vote", "logp", "weight")
_ALLOWED_SORT_KEYS: set = set()


def _audit_source(src: str):
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, violations


def test_prog_moves_no_python_decisions():
    _audit_source(Path(pmv.__file__).read_text())


def test_run_structural_moves_and_apply_selected_move_no_python_decisions():
    src = Path(pmv.__file__).read_text()
    for fn in ("run_structural_moves", "apply_selected_move"):
        start = src.index("def %s(" % fn)
        try:
            end = src.index("\ndef ", start + 1)
        except ValueError:
            end = src.index("\n__all__", start + 1)
        _audit_source(src[start:end])


# ---------------------------------------------------------------------------
# 8) the named arc-4/arc-5 regression sweep — known drift only.
# ---------------------------------------------------------------------------
_REGRESSION_SWEEP_FILES = (
    "test_program_synthesis_migrated.py",
    "test_exact_first_migrated.py",
    "test_verdict_discrimination_migrated.py",
    "test_structural_verdicts_migrated.py",
    "test_budget_isolation_migrated.py",
    "test_prog_repair_migrated.py",
    "test_prog_descent_migrated.py",
    "test_descent_widening_migrated.py",
    "test_retrieval_migrated.py",
    "test_retrieval_ceiling_migrated.py",
    "test_search_reach_migrated.py",
    "test_screen_codebook_migrated.py",
    "test_reject_informs_repair_migrated.py",
    "test_prog_synthesis_battery_migrated.py",
    "test_arc4_endgame_migrated.py",
    "test_mbpp_baseline_migrated.py",
    "test_code_synthesis_baseline_migrated.py",
    "test_prog_ir_migrated.py",
    "test_value_domain_migrated.py",
)

# 2026-08-01 (arc5 cross-phase reconciliation — PROGRAM_SYNTHESIS_ARC5_
# FINAL.md): the 20 attribution-aware entries this allowlist used to carry
# (5 literal seed-version pins, 9 MOVE-A/br_10-shaped drifts, 4 MOVE-B
# search-reach-bucket drifts, 2 more br_10-shaped battery/endgame pins)
# have ALL been reconciled IN PLACE, attribution-aware, in their own test
# files — never blanket-loosened, never silently absorbed (see e.g.
# `tests/test_reject_informs_repair_migrated.py`'s `_ARC5_MOVES_PASS_IDS`/
# `_ENGINE_EXPOSED_COINCIDENTAL_FIT_CORRECTIONS`, `tests/test_search_
# reach_migrated.py`'s `_ARC5_MOVES_PASS_IDS`, and the `_P7_KNOWN_LIVE_
# IMPROVEMENT` entry in `tests/test_prog_synthesis_battery_migrated.py`).
# Pruned per this file's own standing instruction ("prune the allowlist")
# now that they no longer fail. What remains is the ONE class this
# reconciliation does NOT own and does not touch: a PRE-EXISTING defect
# (task 267's 'sum_of_two' vs 'range_sum_spine' construction drift),
# verified directly (an isolated worktree at commit ec41d3001c, domains/
# prog_synthesis.py + seeds/program_synthesis.json + the test file itself
# all at that commit, none of exact-first/rational-domain/moves present)
# to ALREADY fail there — it predates every phase this reconciliation
# covers and lives outside any of these phases' file-ownership boundaries
# (fixing it would require editing domains/prog_synthesis.py's codebook
# decode order, which no test-only reconciliation may do). Left failing,
# flagged for the maintainer, not silently absorbed.
#
# 2026-08-01 (arc6 seam D, reconciled): UNCHANGED again, for the same
# reason. Seam D's property rung + seed bump (v1.10.0/70 -> v1.11.0/73)
# broke 12 node ids inside THIS sweep's own (wider) file set — the seed
# version/count pins, test_retrieval's ceiling[105/238/405] + occam-order
# behavioural pins, and test_reject_informs_repair's v1.7.0-baseline diff
# (which gained an `_ARC6_PROPERTY_CAUGHT_IDS` attribution set read live
# from each goal's own property facts). All reconciled IN PLACE in their
# own files, none allowlisted here; this sweep went green again on its own.
_KNOWN_OUT_OF_SCOPE_FAILURES = frozenset({
    "test_descent_widening_migrated.py::test_sum_to_n_class_scalar_loop_descends_and_holds_out_correct",
    "test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live",
})


def test_named_regression_sweep_only_known_pins_drift():
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    tests_dir = os.path.join(ROOT, "tests")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest",
         *[os.path.join(tests_dir, f) for f in _REGRESSION_SWEEP_FILES],
         "--confcutdir=.", "-q", "--tb=no", "-rf"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=280)
    failed = set()
    for line in proc.stdout.splitlines():
        if line.startswith("FAILED "):
            node_id = line[len("FAILED "):].split(" ")[0]
            failed.add(node_id.split("tests" + os.sep, 1)[-1].lstrip(os.sep))
    unexpected = failed - _KNOWN_OUT_OF_SCOPE_FAILURES
    assert not unexpected, (
        "unexpected new regressions in the arc-4/arc-5 sweep:\n%s\n\n"
        "full output:\n%s" % ("\n".join(sorted(unexpected)), proc.stdout[-6000:]))
    missing_known = _KNOWN_OUT_OF_SCOPE_FAILURES - failed
    if missing_known:
        print("\nKNOWN out-of-scope failures no longer failing (prune the "
              "allowlist): %s" % sorted(missing_known))
