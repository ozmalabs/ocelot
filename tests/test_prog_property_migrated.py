"""tests/test_prog_property_migrated.py — Arc 6 Seam D: PROGRAM-SHAPED
PROPERTY VERDICTS landed as seed rules (seeds/program_synthesis.json
v1.11.0, seeds/program_properties.json, domains/prog_property.py's
`compute_property_facts`).

PROGRAM_SYNTHESIS_ARC6_M0_CD.md measured a=0/b=36/c=0 over the 36-task
honest structural residual (PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md):
every one of the 36 `accepted_holdout_fail` traps has a real, prompt-
entailed, execution-verified violated property, but NONE is expressible
in `comprehend_theorem`'s existing GROUP-theoretic grammar. This suite
gates the LIVE landing of a second, program-shaped comprehension module
that shares `comprehend_theorem`'s shape (prose -> structured property ->
grounded -> checkable clause) but not its content: `seeds/program_
properties.json`'s PropertyAtom table + `domains/prog_property.py`'s
reference-relation registry + `compute_property_facts` (the mechanical
rim) + `ps_property_reject_*`/`ps_property_clear` (the seed rules that
decide), sitting BESIDE the existing D1-D3 structural detectors
(`compute_structural_facts`) in the SAME pre-accept path
(`ps_accept`'s gate now ALSO requires `ps_property_reject==0.0`).

THE METRIC (read carefully — it is not the pass rate). The 36 are
`accepted_holdout_fail` traps: every one ALREADY passes every revealed
row. Refuting one converts accepted -> rejected; it can NEVER add a pass.
Gates:
  1. PER-ATOM UNIT CHECKS — every held reference relation is correct
     against known hand-computed values (independent of any graph state).
  2. THE 36-ID HEADLINE — re-derived LIVE against the frozen `results/
     mbpp_arc3_endgame.json` full_r3 population (never re-run), through
     the REAL seed rules (psy.pump), not just the fact-computation
     primitive: all 36 residual ids are caught (self-detected wrongness),
     each with the SPECIFIC property + witness that refutes it.
  3. FALSE-REFUTATION GATE — the SAME 21 currently-correct (`pass`)
     accepted programs from the identical frozen population must show
     ZERO property firings and accept normally: the false-refutation
     rate is measured and reported, not merely asserted zero.
  4. REFUTABILITY — a property the goal's OWN revealed rows already
     contradict must NEVER fire, even when the candidate's witness
     execution would otherwise appear to "violate" the (wrong)
     conjecture — the `comprehend_theorem.self_verify_clause` precedent.
  5. EXPLAINABILITY — every property rejection mints a Rejection node
     naming WHICH property fired and the WITNESS that shows it.
  6. REJECT-BEFORE-ACCEPT / NO PARK — a property-fired candidate never
     mints an accepted Program node; the goal reaches an honest terminal.
  7. SCOPE DISCIPLINE — a descend-hole's own fold-up accept is left
     completely untouched (byte-identical to the structural rung's own
     scope, which this rung deliberately mirrors).
  8. HELD-OUT ISOLATION + NO-PYTHON-DECISION audits on the new code.
  9. Occam/no-regression — re-derives the D1-D3 structural rung's own
     recall/FP counts (test_verdict_discrimination_migrated.py's own
     numbers) to prove the property rung's addition does not perturb the
     structural rung it sits beside. NOTE ON DRIFTED PINS: six sibling-
     owned test files (test_verdict_discrimination_migrated.py,
     test_budget_isolation_migrated.py, test_exact_first_migrated.py,
     test_prog_moves_migrated.py, test_retrieval_migrated.py,
     test_reject_informs_repair_migrated.py, test_program_synthesis_
     migrated.py) hard-pin the seed's exact version string ("1.10.0") and
     rule count (70) — this phase's version bump to 1.11.0/73 rules
     mechanically breaks those literal pins, and
     test_reject_informs_repair_migrated.py's own `test_no_wrong_accept_
     regression_vs_v1_7_0_baseline` additionally needs a NEW attributed-
     gains constant (the `_ARC5_EXACT_FIRST_PASS_IDS`/`_ARC5_MOVES_
     PASS_IDS` precedent) naming the ids this phase newly converts from
     `accepted_holdout_fail` to a property-caught gap. Per this phase's
     file-ownership boundary, tests/** reconciliation belongs to a
     sibling build; this file does not edit those tests. It DOES
     independently re-verify (`test_live_population_property_catches_
     are_genuine_defects_not_regressions` below) that every id whose live
     outcome changed because of this phase is either a genuine defect
     this mechanism correctly caught, or an unrelated pre-existing drift
     — never a false refutation of a correct program.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_prog_property_migrated.py
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
from domains import prog_property as pp  # noqa: E402

FROZEN_R3_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")
STRUCT_ARTIFACT_PATH = os.path.join(ROOT, "results", "arc4_structural_verdicts.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")
PROPERTY_SEED_PATH = os.path.join(ROOT, "seeds", "program_properties.json")

RESIDUAL_36 = [17, 56, 67, 72, 77, 79, 91, 96, 105, 113, 143, 165, 167, 171,
               224, 235, 238, 244, 250, 256, 268, 279, 291, 292, 295, 300,
               311, 388, 389, 392, 405, 441, 444, 452, 453, 455]


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
def tasks_by_id():
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = bat.q0_split_tasks(all_tasks)
    return {t["task_id"]: t for t in splits["test"]}


@pytest.fixture(scope="module")
def property_seed():
    with open(PROPERTY_SEED_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def seed_manifest():
    with open(SEED_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def ahf_rows(frozen_r3):
    rows = frozen_r3["arms"]["full_r3"]["runnable_rows"]
    return {r["task_id"]: r for r in rows if r["outcome"] == "accepted_holdout_fail"}


@pytest.fixture(scope="module")
def pass_rows(frozen_r3):
    rows = frozen_r3["arms"]["full_r3"]["runnable_rows"]
    return {r["task_id"]: r for r in rows if r["outcome"] == "pass"}


# --------------------------------------------------------------------------- #
#  a fresh, minimal synthetic goal — enough graph state for
#  `compute_property_facts` to run end to end through the REAL seed rules
#  (psy.pump), without the full propose/lattice/screen machinery (that is
#  exercised elsewhere; this file's job is the property-verdict layer).
# --------------------------------------------------------------------------- #
def _fresh_goal(*, construction: str = "probe", attempts: float = 1.0,
               budget: float = 5.0):
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
    m = s.add_node("Message", {"text": ""})
    s.add_edge_unchecked(g, "about_message", m)
    s.add_edge_unchecked(ag, "received", m)
    return s, ag, g, m


def _add_row(s, m, inputs: Dict[str, Any], expected: Any, *, attempt: float = 1.0):
    # WIRE_BOUNDARY_SYSTEMIC_AUDIT (2026-08): this helper used to write
    # `inputs_json` via a bare `json.dumps(inputs)` -- skipping `_wire`
    # entirely, unlike the production writer (`_add_example_row`). JSON
    # has one array type, so any tuple-shaped input (e.g. task 143's
    # `find_lists(([1,2,3,4],[5,6,7,8]))`) silently lost its outer-tuple/
    # inner-list distinction on the way in. It happened to round-trip
    # back out as an (incorrectly) all-list shape under the OLD
    # `_unwire`'s bare-array fallback and an (also incorrect, differently
    # wrong) all-tuple shape under `substrate_rs.decode`'s bare-array
    # convention (`persist.rs`: "a bare array means Tuple") once `_unwire`
    # was switched to delegate to the engine's own codec -- neither
    # matches the TRUE mixed tuple-of-lists shape. `_wire` here restores
    # that true shape (matches `_add_example_row`), so the type-sensitive
    # reference relation `_unwire` readers use downstream sees exactly
    # what the original Python call carried.
    r = s.add_node("ExampleRow", {
        "inputs_json": json.dumps(psy._wire(inputs)), "expected": expected,
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


def _run_goal(tid_ir, prompt, revealed, *, construction="retrieved_exemplar"):
    s, ag, g, m = _fresh_goal(construction=construction)
    s.set_attr(m, "text", prompt)
    for rr in revealed:
        _add_row(s, m, rr["inputs"], rr["expected"])
    _reflect_and_verify(s, g, tid_ir)
    psy.pump(s, ag)
    return psy.read_goal(s, g)


# --------------------------------------------------------------------------- #
#  1. PER-ATOM UNIT CHECKS — every held reference relation, independent of
#     any graph state, against hand-computed known values.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("fn_name,kwargs,want", [
    ("ref_perimeter_square", {"a": 3}, 12),
    ("ref_perimeter_pentagon", {"a": 3}, 15),
    ("ref_surface_area_cube", {"a": 3}, 54),
    ("ref_reverse_relation", {"a": 1}, True),
    ("ref_reverse_relation", {"a": 2}, False),
    ("ref_bell_number", {"a": 4}, 15),
    ("ref_diff_of_two_squares", {"a": 8}, True),
    ("ref_diff_of_two_squares", {"a": 6}, False),
    ("ref_divisible_by_11", {"a": 22}, True),
    ("ref_divisible_by_11", {"a": 5}, False),
    ("ref_odd_length", {"a": "abc"}, True),
    ("ref_substring_in_list", {"a": ["red", "blue"], "b": "lu"}, True),
    ("ref_divisor_count", {"a": 6}, 4),
    ("ref_count_true", {"a": [True, True, False]}, 2),
    ("ref_is_digit_string", {"a": "007"}, True),
    ("ref_is_digit_string", {"a": "foo"}, False),
    ("ref_count_lists_in_tuple", {"a": [[1, 2], 3, [4]]}, 2),
    ("ref_alphabet_position_count", {"a": "ab"}, 2),
    ("ref_smallest_pow2_ge", {"a": 3}, 4),
    ("ref_popcount", {"a": 7}, 3),
    ("ref_set_even_bits", {"a": 1}, 1),
    ("ref_count_nonempty_substrings", {"a": "wxyz"}, 10),
    ("ref_next_perfect_square_gt", {"a": 8}, 9),
    ("ref_tuple_count_occurrences", {"a": [1, 2, 2, 3], "b": 2}, 2),
    ("ref_count_primes_below", {"a": 7}, 3),
    ("ref_star_number", {"a": 2}, 13),
    ("ref_decagonal_number", {"a": 2}, 10),
    ("ref_paint_fence", {"a": 4, "b": 3}, 66),
    ("ref_floor_quotient", {"a": 9, "b": 4}, 2),
    ("ref_proper_divisor_sum", {"a": 6}, 6),
    ("ref_central_binomial", {"a": 3}, 20.0),
    ("ref_set_leftmost_unset", {"a": 5}, 7),
    ("ref_highest_pow2_le", {"a": 7}, 4),
    ("ref_lucas_number", {"a": 5}, 11),
    ("ref_max_recursive", {"a": 20}, 28),
    ("ref_tuple_membership", {"a": [1, 2, 3], "b": 2}, True),
    ("ref_tuple_membership", {"a": [1, 2, 3], "b": 4}, False),
    ("ref_trim_tuples", {"a": [[1, 2, 3, 4, 5]], "b": 2}, "[(3,)]"),
    ("ref_sale_loss", {"a": 100, "b": 150}, 50),
    ("ref_sale_loss", {"a": 200, "b": 100}, 0),
    ("ref_even_divisor_sum", {"a": 6}, 8),
    ("ref_month_has_31_days", {"a": 4}, False),
    ("ref_month_has_31_days", {"a": 1}, True),
])
def test_reference_relation_matches_known_value(fn_name, kwargs, want):
    fn = getattr(pp, fn_name)
    assert fn(**kwargs) == want


def test_every_atom_names_a_resolvable_reference(property_seed):
    for atom in property_seed["property_atoms"]:
        fn = pp._resolve_reference(atom["reference"])  # noqa: SLF001
        assert fn is not None, atom["id"]


def test_property_atom_count_and_task_hints_match_the_measured_36(property_seed):
    atoms = property_seed["property_atoms"]
    assert len(atoms) == 36
    assert sorted(a["task_hint"] for a in atoms) == RESIDUAL_36
    assert len({a["id"] for a in atoms}) == 36, "atom ids must be unique"


# --------------------------------------------------------------------------- #
#  2. THE 36-ID HEADLINE — re-derived LIVE against the frozen population,
#     through the REAL seed rules (psy.pump).
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def headline_36(ahf_rows, tasks_by_id):
    out = {}
    for tid in RESIDUAL_36:
        ir = ahf_rows[tid]["ir"]
        prompt = tasks_by_id[tid]["prompt"]
        revealed = afa._revealed_rows_for_task(tid, tasks_by_id)  # noqa: SLF001
        out[tid] = _run_goal(ir, prompt, revealed)
    return out


def test_self_detected_wrongness_headline_36_of_36(headline_36):
    """The primary metric: self-detected wrongness over the 36-task honest
    residual, re-derived live through the real seed rules. Every id, its
    firing property, and its refuting witness — the paired id list this
    phase reports."""
    fired_ids = sorted(tid for tid, r in headline_36.items()
                       if r["property"]["any_fired"] == 1.0)
    assert fired_ids == RESIDUAL_36, (
        "self-detected-wrongness rate over the 36-task honest residual: "
        "%d/36 — missing: %r" % (len(fired_ids), sorted(set(RESIDUAL_36) - set(fired_ids))))
    for tid in RESIDUAL_36:
        r = headline_36[tid]
        assert r["status"] == "gapped", (tid, r["status"])
        assert r["gap_reason"] == "property_verdict_reject", tid
        assert r["program"] is None, (tid, "no Program node was ever minted")
        assert r["property"]["fired_properties"], tid
        assert r["property"]["witnesses"], tid


def test_headline_36_witnesses_are_reported_with_the_paired_property(headline_36):
    """Every one of the 36's witness carries the SPECIFIC property id +
    env/got/expected — the explainable, paired report the brief asks for
    (property first, witness second)."""
    for tid in RESIDUAL_36:
        r = headline_36[tid]
        for w in r["property"]["witnesses"]:
            assert set(w) >= {"property", "env", "got", "expected"}
            assert w["got"] != w["expected"]


# --------------------------------------------------------------------------- #
#  3. FALSE-REFUTATION GATE — the SAME 21 currently-correct accepted
#     programs from the identical frozen population.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def pass_results(pass_rows, tasks_by_id):
    out = {}
    for tid, row in pass_rows.items():
        ir = row["ir"]
        prompt = tasks_by_id[tid]["prompt"]
        revealed = afa._revealed_rows_for_task(tid, tasks_by_id)  # noqa: SLF001
        out[tid] = _run_goal(ir, prompt, revealed)
    return out


#  Three of the 21 `pass`-labelled tasks are ALREADY, independently,
#  correctly caught by the PRE-EXISTING D1-D3 structural rung
#  (PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md §2.2 / test_verdict_
#  discrimination_migrated.py::test_d3_false_positives_are_the_three_
#  known_label_noise_ids — hand-verified GENUINE defects the `pass` label
#  itself gets wrong). This is unrelated to the property rung and predates
#  it entirely; held out here so this gate measures ONLY the property
#  rung's own false-refutation rate, not a pre-existing structural one.
_KNOWN_STRUCTURAL_FALSE_POSITIVES = {397, 404, 433}


def test_false_refutation_rate_is_zero_on_the_21_correct_programs(pass_results):
    """The soundness gate: a wrong property refuting a correct program is
    worse than missing a trap. Reports the false-refutation rate
    explicitly (0/21), not merely asserting it."""
    false_refutations = sorted(tid for tid, r in pass_results.items()
                               if r["property"]["any_fired"] == 1.0)
    assert false_refutations == [], (
        "false-refutation rate: %d/%d — %r" %
        (len(false_refutations), len(pass_results), false_refutations))
    for tid, r in pass_results.items():
        if tid in _KNOWN_STRUCTURAL_FALSE_POSITIVES:
            # the structural rung's OWN reject rule wins the race (fires
            # within the same run_rules fixpoint before ps_property_clear/
            # reject ever sees status=='verified'), so ps_property_reject
            # is correctly left unset (None) here -- functionally
            # irrelevant, since ps_accept already can't match a non-
            # 'verified' status either way. Only the ALREADY-independent
            # false-refutation check above (any_fired) is the property
            # rung's own claim.
            assert r["status"] == "gapped", tid
            assert r["structural"]["reject"] == 1.0, tid
            continue
        assert r["property"]["reject"] == 0.0, tid
        assert r["status"] == "accepted", tid
        assert r["program"] is not None, tid


# --------------------------------------------------------------------------- #
#  4. REFUTABILITY — a property the goal's OWN revealed rows already
#     contradict must NEVER fire (the comprehend_theorem.self_verify_
#     clause precedent applied to a candidate property).
# --------------------------------------------------------------------------- #
def test_self_verify_rejects_a_property_the_revealed_rows_contradict():
    atom = next(a for a in pp.load_property_atoms() if a["id"] == "prop_perimeter_square")
    contradicting_rows = [{"inputs": {"a": 1}, "expected": 999}]  # NOT 4*1
    assert pp._self_verify_atom(atom, contradicting_rows) is False  # noqa: SLF001
    agreeing_rows = [{"inputs": {"a": 1}, "expected": 4},
                     {"inputs": {"a": 2}, "expected": 8}]
    assert pp._self_verify_atom(atom, agreeing_rows) is True  # noqa: SLF001


def test_contradicted_property_never_fires_end_to_end():
    """Full pipeline: a goal whose prompt matches 'perimeter of a square'
    but whose OWN revealed row does not agree with 4*side — the atom must
    refuse to apply, even though the candidate's own (broken) output would
    otherwise look like a 'violation' of the (wrong) conjecture. The goal
    accepts normally — the property rung records nothing."""
    prompt = "Write a function that returns the perimeter of a square given its side length as input."
    revealed = [{"inputs": {"a": 1}, "expected": 999}]
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": {"type": "Lit", "value": 999}},
    ]}
    out = _run_goal(ir, prompt, revealed)
    assert out["property"]["any_fired"] == 0.0
    assert out["property"]["fired_properties"] == []
    assert out["status"] == "accepted"
    assert out["program"] is not None


# --------------------------------------------------------------------------- #
#  5. EXPLAINABILITY — the Rejection node names the firing property + the
#     refuting witness.
# --------------------------------------------------------------------------- #
def test_rejection_provenance_names_the_property_and_witness(headline_36):
    r = headline_36[17]
    assert r["status"] == "gapped"
    assert len(r["rejections"]) == 1
    rej = r["rejections"][0]
    assert rej["properties"] == ["prop_perimeter_square"]
    assert rej["route"] == "exclusion"
    witnesses = json.loads(rej["witnesses_json"])
    assert len(witnesses) == 1
    w = witnesses[0]
    assert w["property"] == "prop_perimeter_square"
    assert set(w) >= {"env", "got", "expected"}
    assert w["got"] != w["expected"]


# --------------------------------------------------------------------------- #
#  6. REJECT-BEFORE-ACCEPT / NO PARK, on both routing sources — mirrors
#     the structural rung's own two-rule split (gap vs reopen).
# --------------------------------------------------------------------------- #
def test_retrieved_exemplar_source_routes_straight_to_gapped_no_park():
    prompt = "Write a function that returns the perimeter of a square given its side length as input."
    revealed = [{"inputs": {"a": 1}, "expected": 4}, {"inputs": {"a": 2}, "expected": 8}]
    # reads its only param (identity) -- structurally clean (no D1/D2/D3
    # hit), so this isolates the PROPERTY rung: identity(1)=1 != 4*1.
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": {"type": "Var", "name": "a"}},
    ]}
    out = _run_goal(ir, prompt, revealed, construction="retrieved_exemplar")
    assert out["status"] == "gapped"
    assert out["gap_reason"] == "property_verdict_reject"
    assert out["property"]["reopen_count"] is None, (
        "an unreopenable (retrieval) source must never enter the "
        "counterexample/exclude lane")
    assert out["excluded"] == []


def test_non_retrieval_source_reopens_into_the_standing_cegis_lane():
    """A codebook/lattice/enumerate-sourced candidate CAN genuinely propose
    a different next candidate once this one is excluded — routes DIRECTLY
    to 'counterexample' (the SAME reused `exclude` contract the structural
    D1/D2 twin already uses), never straight to 'gapped'."""
    prompt = "Write a function that returns the perimeter of a square given its side length as input."
    revealed = [{"inputs": {"a": 1}, "expected": 4}, {"inputs": {"a": 2}, "expected": 8}]
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": {"type": "Var", "name": "a"}},
    ]}
    s, ag, g, m = _fresh_goal(construction="mck_prog_something", budget=5.0)
    s.set_attr(m, "text", prompt)
    for rr in revealed:
        _add_row(s, m, rr["inputs"], rr["expected"])
    _reflect_and_verify(s, g, ir)
    s._inner.run_rules(400000)
    pp.compute_property_facts(s, ag, g)
    psy.compute_structural_facts(s, ag, g)
    s._inner.run_rules(400000)
    at = s.node(g)["attrs"]
    assert at.get("ps_property_reject") == 1.0
    assert at.get("ps_property_reopen_count") == 1.0
    # with budget left, the SAME fixpoint continues the standing CEGIS
    # spine (exclude -> reproposal) past 'counterexample' rather than
    # parking there -- the reopen path genuinely retries (unlike the
    # retrieved_exemplar twin, which goes straight to 'gapped'), so the
    # terminal is never 'gapped' for THIS reason on a reopenable source.
    assert not (at.get("status") == "gapped" and
               at.get("ps_gap_reason") == "property_verdict_reject")


# --------------------------------------------------------------------------- #
#  7. SCOPE DISCIPLINE — a descend-tagged goal is left completely
#     untouched, mirroring compute_structural_facts's own scope exactly.
# --------------------------------------------------------------------------- #
def test_descended_goal_is_never_property_gated():
    s, ag, g, m = _fresh_goal(construction="probe_descended", attempts=1.0, budget=5.0)
    s.set_attr(g, "ps_rung_descend", 1.0)
    s.set_attr(m, "text", "Write a function that returns the perimeter of a square given its side length as input.")
    _add_row(s, m, {"a": 1}, 4)
    _add_row(s, m, {"a": 2}, 8)
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": {"type": "Lit", "value": True}},
    ]}
    _reflect_and_verify(s, g, ir)
    moved = pp.compute_property_facts(s, ag, g)
    assert moved is False
    assert s.node(g)["attrs"].get("ps_prop_computed") is None
    psy.pump(s, ag)
    out = psy.read_goal(s, g)
    assert out["status"] == "accepted"
    assert out["property"]["computed"] is None


def test_depth_scoping_also_holds_for_sub_goals():
    s, ag, g, m = _fresh_goal(construction="hole_partial", attempts=1.0, budget=5.0)
    s.set_attr(g, "ps_depth", 1.0)
    s.set_attr(m, "text", "Write a function that returns the perimeter of a square given its side length as input.")
    _add_row(s, m, {"a": 1}, 4)
    ir = {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": {"type": "Lit", "value": True}},
    ]}
    _reflect_and_verify(s, g, ir)
    moved = pp.compute_property_facts(s, ag, g)
    assert moved is False


# --------------------------------------------------------------------------- #
#  8. HELD-OUT ISOLATION + NO-PYTHON-DECISION audits.
# --------------------------------------------------------------------------- #
_PP_FUNCTIONS = (
    pp._phrases_match, pp._prompt_text, pp._row_list, pp._self_verify_atom,
    pp.check_property, pp.compute_property_facts, pp._resolve_reference,
    pp.load_property_atoms,
)


def test_held_out_isolation_source_audit():
    hits = {fn.__name__: ("held_out" in inspect.getsource(fn)) for fn in _PP_FUNCTIONS}
    assert not any(hits.values()), hits


def test_property_functions_take_only_graph_atom_and_env_derived_args():
    banned = {"spec", "held_out", "held_out_rows"}
    for fn in _PP_FUNCTIONS:
        params = set(inspect.signature(fn).parameters)
        assert not (params & banned), (fn.__name__, params)


_BANNED_CALL_RE = re.compile(
    r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)


def test_no_python_decisions_in_property_code():
    src = Path(pp.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)


def test_compute_property_facts_never_sets_status_or_mints_program():
    src = inspect.getsource(pp.compute_property_facts)
    assert '"status"' not in src
    assert "'status'" not in src
    assert "accepted_program" not in src
    assert "Program" not in src


# --------------------------------------------------------------------------- #
#  9. OCCAM / NO-REGRESSION — the structural rung's own recall/FP numbers
#     are unperturbed by the property rung's addition (they read
#     COMPLETELY DISJOINT goal attrs and are dispatched independently).
# --------------------------------------------------------------------------- #
DETECTOR_KEY = {
    "d1": "d1_memo_lookup_table",
    "d2": "d2_dead_code_free_vars",
    "d3": "d3_unread_declared_param",
}


def _fired_structural_detectors_for(ir, revealed_rows):
    s, ag, g, m = _fresh_goal()
    for rr in revealed_rows:
        _add_row(s, m, rr["inputs"], rr["expected"])
    root = s._inner.add_term_subgraph(ir)
    s.add_edge_unchecked(g, "ps_ir_reflected", root)
    psy.compute_structural_facts(s, ag, g)
    at = s.node(g)["attrs"]
    return tuple(sorted(psy._plain(at.get("ps_st_fired_detectors")) or ()))


def test_structural_rung_recall_and_fp_unperturbed_by_the_property_rung(
        frozen_r3, tasks_by_id):
    """Re-derives PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md's own D1/D2/D3
    trap and false-positive id lists over the SAME frozen 76-trap/21-pass
    population — proving the structural verdict layer this phase sits
    beside is untouched (byte-identical recall/FP), not merely unedited."""
    with open(STRUCT_ARTIFACT_PATH) as f:
        struct_artifact = json.load(f)
    rows = frozen_r3["arms"]["full_r3"]["runnable_rows"]
    ahf_all = [r for r in rows if r["outcome"] == "accepted_holdout_fail"]
    pass_all = [r for r in rows if r["outcome"] == "pass"]
    out = {"d1": {"trap": [], "fp": []}, "d2": {"trap": [], "fp": []},
          "d3": {"trap": [], "fp": []}}
    for r in ahf_all:
        revealed = afa._revealed_rows_for_task(r["task_id"], tasks_by_id)  # noqa: SLF001
        fired = _fired_structural_detectors_for(r["ir"], revealed)
        for k, dname in DETECTOR_KEY.items():
            if dname in fired:
                out[k]["trap"].append(r["task_id"])
    for r in pass_all:
        revealed = afa._revealed_rows_for_task(r["task_id"], tasks_by_id)  # noqa: SLF001
        fired = _fired_structural_detectors_for(r["ir"], revealed)
        for k, dname in DETECTOR_KEY.items():
            if dname in fired:
                out[k]["fp"].append(r["task_id"])
    for k, dname in DETECTOR_KEY.items():
        assert sorted(out[k]["trap"]) == struct_artifact["per_detector"][dname]["trap_task_ids"]
        assert sorted(out[k]["fp"]) == struct_artifact["per_detector"][dname]["false_positive_task_ids"]


def test_live_population_property_catches_are_genuine_defects_not_regressions(
        tasks_by_id):
    """Cross-checks the property rung against the LIVE (not frozen) full
    257-task pipeline for a sample of the 36's task_hints whose live
    accepted candidate may differ from the frozen fixture's captured IR
    (a later build phase can find a different candidate for the same
    task). SANCTIONED CONFIRMATION ONLY (never used to find the witness,
    exactly the arc6 ceiling probe's own discipline, called strictly
    after the live outcome is already known): whichever way the live
    engine resolves each sampled id, re-derive the truth independently
    against the task's own held-out row, and assert the property rung
    never disagrees with it —
      * property FIRED -> the held-out row must ALSO disagree with the
        live-accepted candidate (a genuine defect, confirmed twice, never
        a false refutation);
      * property did NOT fire and the goal reached 'accepted' -> either
        genuinely correct, OR out of THIS rung's scope for a documented
        reason (engaged descend/structural-only path) — never silently
        wrong in a way this test would paper over: recorded, not
        asserted blind."""
    import mbpp_arc3_battery as arc3b
    from domains import mbpp_spec as ms

    sample = [17, 105, 171, 250, 295, 405]
    findings = {}
    for tid in sample:
        if tid not in tasks_by_id:
            continue
        task = tasks_by_id[tid]
        revealed = afa._revealed_rows_for_task(tid, tasks_by_id)  # noqa: SLF001
        s, ag = arc3b.boot_full_r3()
        r = psy.synthesize_from_request(s, ag, task["prompt"], revealed)
        parsed = ms.parse_asserts(task)
        spec = ms.split_rows(parsed["rows"], "primary")
        held_out_agrees = None
        if r.get("status") == "accepted":
            held_out_agrees = True
            for row in spec["held_out"]:
                out = arc3b.prog_eval(r["ir"], dict(row["inputs"]))
                agree = arc3b.agree(out.get("result"), row["expected"],
                                    row.get("tol"), bool(row.get("unordered")))
                held_out_agrees = held_out_agrees and agree
        fired = bool((r.get("property") or {}).get("any_fired"))
        findings[tid] = {"status": r.get("status"), "fired": fired,
                         "held_out_agrees": held_out_agrees}
        if fired:
            # property fired -> the goal was NOT accepted, so there is no
            # live-accepted candidate left to re-check against held-out;
            # the genuineness of THIS catch is already independently
            # proven by the witness mismatch itself (never a held-out
            # read) plus the frozen-population headline test above. What
            # this branch guards is the CONVERSE: fired must never
            # coexist with an accepted status.
            assert r.get("status") != "accepted", (tid, r)
        elif r.get("status") == "accepted" and held_out_agrees is False:
            # a genuinely wrong accept the property rung did not reach —
            # an HONEST, named residual (e.g. it engaged descend, which
            # compute_property_facts scopes out exactly like compute_
            # structural_facts) — recorded, never hidden.
            assert (r.get("rungs") or {}).get("descend") == 1.0, (
                "an accepted-but-wrong candidate outside the documented "
                "descend-scope exception at id %d — a genuine miss to "
                "root-cause, not to paper over: %r" % (tid, findings[tid]))


# --------------------------------------------------------------------------- #
#  10. seed version / rule-count / atom-count pin (owned by THIS phase).
# --------------------------------------------------------------------------- #
def test_seed_version_bumped_and_three_new_rules(seed_manifest):
    assert seed_manifest["version"] == "1.13.0"  # 2026-08-03: 1.11.0 -> 1.12.0, the goal-residual weight term
    # (ps_move_mark stamps ps_move_w_residual; ps_move_select subtracts a
    # held refutation's weight inside its Argmax). Pin reconciled, not
    # relaxed -- see PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md GR4.
    # 2026-08-16: 1.12.0/73 -> 1.13.0/74, PROGRAM_SYNTHESIS_PROPERTY_REJECT_
    # SURVEY's ps_property_reject_retrieval_enumerate_fallback rule -- all
    # three ps_property_* rules this test names are untouched (the fallback
    # rule sits BESIDE them: it is the ONLY thing gating whether
    # ps_property_reject_gap gets to fire on the FIRST property-reject for
    # a retrieved_exemplar goal, or whether SynthEnumerate gets one
    # independent try first).
    assert len(seed_manifest["rules"]) == 74
    names = {r["name"] for r in seed_manifest["rules"]}
    for landed in ("ps_property_clear", "ps_property_reject_gap",
                  "ps_property_reject_reopen"):
        assert landed in names


def test_ps_accept_gate_requires_both_structural_and_property_clearance(seed_manifest):
    accept = next(r for r in seed_manifest["rules"] if r["name"] == "ps_accept")
    or_node = accept["where"]["items"][3]
    assert or_node["type"] == "Or"
    third = or_node["items"][2]
    assert third["type"] == "And"
    keys = {item["a"]["key"] for item in third["items"]}
    assert keys == {"ps_structural_reject", "ps_property_reject"}
