"""TRIPWIRE REPAIR — L1b's structural audits become AST-based.

Gates `VISION_TRIPWIRE_REPAIR_PREREG.md` / `VISION_TRIPWIRE_REPAIR_RESULTS.md`.

The defect acted on (found by the k=1 rung, `VISION_COLOUR_BOUND_K1_RESULTS.md`): L1b
asserted `'"type": "Lte"' not in blob` with the note *"if a bound was added, re-run the
audit"*. A bound WAS added, composed as `Lt` inside `Not(Exists(...))`, and the tripwire
did not trip.

THE CONJUNCTION IS THE DESIGN CONSTRAINT (§1.1, process rule 5). Two arms pull in
OPPOSITE directions and neither alone is a gate:

  * a DETECT-NOTHING detector scores a PERFECT false-positive arm;
  * a DETECT-EVERYTHING detector scores a PERFECT evasion arm.

`test_EVADE_*` and `test_FP_*` are the pair; passing both is the claim. Both were
positive-controlled by injecting exactly those two defects (see the results file).
"""
from __future__ import annotations

import json
import os

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEEDS = os.path.join(_ROOT, "seeds")

import sys  # noqa: E402
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from tools.term_ast_audit import (  # noqa: E402
    audit_seed_file, comparisons_in, legacy_string_test,
)
import tripwire_repair_measure as trm  # noqa: E402


# ---------------- BLIND — the premise reproduces --------------------------------

def test_BLIND_the_current_string_tripwire_does_NOT_trip_on_a_real_bound():
    """The k=1 rung's finding, reproduced: `ci_assign` DOES contain an admission
    bound, and the old assertion passes anyway (passing == failing to trip)."""
    r = trm.arm_BLIND()
    assert r["old_test_says_no_Lte"] is True, "the blindness must reproduce"
    assert r["actual_comparators"]["Lte"] == 0
    assert r["actual_comparators"]["Lt"] > 0, "there IS a comparator, spelled Lt"
    # doubly blind: the sibling spelling is missed too
    assert r["old_test_says_no_Gte"] is True
    assert r["actual_comparators"]["Gt"] > 0


# ---------------- SEES — the repaired detector finds it -------------------------

def test_SEES_the_AST_detector_finds_the_Lt_inside_Not_Exists_bound():
    """The repair: the bound is found, and found AS NEGATED — polarity is reported,
    not merely counted."""
    a = audit_seed_file(os.path.join(_SEEDS, "vision_colour_identity.json"),
                        "ci_assign")
    assert a["T1_bound_like"] >= 1, "the AST detector must see the landed bound"
    negated = [d for d in a["T1_detail"] if d["not_depth"] > 0]
    assert negated, "the landed bound sits inside Not(Exists(...)) and must read so"
    d = negated[0]
    assert d["op"] == "Lt"
    # a bound compares a computed MAGNITUDE against a computed THRESHOLD
    assert set(d["operands"]) == {"Sqrt", "Times"}


# ---------------- EVADE — the RISKED arm ----------------------------------------

@pytest.mark.parametrize("case", [c[0] for c in trm.evasion_battery()])
def test_EVADE_every_equivalent_bound_composition_is_caught(case):
    """Seven spellings of ONE predicate. Structure-reading must be invariant to all
    of them: re-spelling, negation, nesting, operand reversal, position."""
    tree = [t for n, _, t in trm.evasion_battery() if n == case][0]
    found = comparisons_in(tree)
    assert any(c.bound_like for c in found), f"{case} evaded the AST detector"


def test_EVADE_the_OLD_string_test_misses_at_least_one_of_them():
    """The control that makes the repair meaningful: the old instrument is not
    merely weaker in principle, it MEASURABLY misses these compositions. E1 is the
    positive control proving the old test is not simply broken."""
    r = trm.arm_EVADE()
    assert r["ast_detected"] == r["n"], "AST must catch ALL"
    assert r["old_detected"] >= 1, "the old test must catch its own spelling (E1)"
    assert r["old_missed"] >= 1, "if the old test caught everything there is no defect"
    by_case = {x["case"]: x for x in r["rows"]}
    assert by_case["E1_plain_Lte"]["old_string_test_detects"] is True
    for case in ("E2_strict_Lt", "E3_Lt_inside_Not_Exists", "E4_reversed_Gte",
                 "E5_reversed_Gt", "E6_double_negation", "E7_in_a_where_clause"):
        assert by_case[case]["old_string_test_detects"] is False, case
        assert by_case[case]["ast_detects"] is True, case


# ---------------- FP — THE CONJUNCTION ------------------------------------------

@pytest.mark.parametrize("case", [c[0] for c in trm.nonbound_battery()])
def test_FP_a_genuine_non_bound_is_NOT_flagged(case):
    """A detector that flags everything is useless. Flag reads, cardinality tests and
    epoch comparisons are NOT admission bounds and must not be reported as such."""
    tree = [t for n, _, t in trm.nonbound_battery() if n == case][0]
    found = comparisons_in(tree)
    assert found, "the case must contain a comparator at all (non-vacuous)"
    assert not any(c.bound_like for c in found), f"{case} is a FALSE POSITIVE"


def test_FP_a_real_seed_with_no_verdict_bound_is_still_reported_unbounded():
    """`shape_decode_loop` admits by EXACT equality — L1b's verdict. It contains 19
    comparators, so this arm is NOT passing on an empty set: they are all cardinality
    or flag reads, and a naive any-comparator detector would flip L1b's row wrongly."""
    a = audit_seed_file(os.path.join(_SEEDS, "shape_decode_loop.json"))
    assert a["T0_any_comparator"] > 0, "non-vacuous: there ARE comparators to misjudge"
    assert a["T1_bound_like"] == 0, "L1b's similarity verdict must HOLD"
    reasons = {d["reason"] for d in a["T0_non_bound_detail"]}
    assert reasons <= {"cardinality", "atomic-vs-atomic (flag/epoch read)"}


def test_the_two_tiers_DISAGREE_which_is_why_both_are_reported():
    """T0 and T1 are not redundant. On `shape_decode_loop` T0 says 'bound present'
    and T1 says 'none' — the disagreement IS the discrimination, and reporting only
    T0 would have silently corrected L1b's similarity row in the WRONG direction."""
    a = audit_seed_file(os.path.join(_SEEDS, "shape_decode_loop.json"))
    assert a["T0_any_comparator"] > 0 and a["T1_bound_like"] == 0


# ---------------- TABLE — L1b's audit re-run ------------------------------------

def test_TABLE_exactly_one_L1b_verdict_CHANGES_and_it_is_colour_identity():
    """The reported CORRECTION. L1b recorded 'ci_assign has NO admission bound at
    all'. Since the colour-bound rungs landed, that is no longer true. This is a
    correction to a STRUCTURAL claim; L1b's MEASURED numbers are untouched, because
    the k=1 rung already pinned `bound=0.0` in `audit_colour_identity`."""
    t = trm.arm_TABLE()
    assert t["n_changed"] == 1, t["changed"]
    assert t["changed"] == ["colour identity (ci_assign)"]


def test_TABLE_the_deformation_row_is_UNCHANGED():
    """Its bound is spelled `Lte`, so both the old and the new instrument see it."""
    t = trm.arm_TABLE()
    row = [r for r in t["rows"] if r["seed"] == "vision_deformation.json"][0]
    assert row["AST_has_bound"] is True
    assert row["old_test_says_no_bound_Lte"] is False
    assert row["VERDICT_CHANGES"] is False


def test_TABLE_the_similarity_row_HOLDS():
    """Proviso 1 of the pre-registration: if T1 flipped this row too, the
    `Count`-exclusion would be wrong and the row would need re-deriving — the
    detector would NOT be re-tuned to rescue it (§5)."""
    t = trm.arm_TABLE()
    row = [r for r in t["rows"] if r["seed"] == "shape_decode_loop.json"][0]
    assert row["AST_has_bound"] is False
    assert row["VERDICT_CHANGES"] is False


# ---------------- the repair is REAL: L1b's own file no longer substring-scans ----

def test_L1bs_gate_no_longer_asserts_on_a_SERIALIZED_blob():
    """The repair, gated on L1b's own source. No assertion in L1b's gate may test a
    Term type by substring any more. Checked on the Python AST, not by grepping —
    the same lesson, applied to the repair itself."""
    import ast
    src = open(os.path.join(_ROOT, "tests", "test_uniqueness_migrated.py")).read()
    tree = ast.parse(src)
    bad = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and any(
                isinstance(o, (ast.In, ast.NotIn)) for o in n.ops):
            if (isinstance(n.left, ast.Constant)
                    and isinstance(n.left.value, str)
                    and '"type":' in n.left.value):
                bad.append(n.lineno)
    assert not bad, f"serialized-blob Term-type assertions remain at lines {bad}"


def test_the_repair_module_holds_no_agent_state_and_makes_no_agent_decision():
    """CLAUDE.md: this is audit tooling over committed JSON — static analysis, no
    graph, no substrate, no agent state."""
    src = open(os.path.join(_ROOT, "tools", "term_ast_audit.py")).read()
    for banned in ("boot_core", "substrate_rs", "add_node", "add_edge", "tick("):
        assert banned not in src, f"audit tooling must not touch the substrate: {banned}"


def test_this_rung_consumed_NO_seed_block():
    """53000-53999 was allocated and is NOT needed: every arm is deterministic static
    analysis. Recorded so the ledger does not lose the block."""
    res = json.load(open(os.path.join(_ROOT, "results", "tripwire_repair.json")))
    assert "NONE" in res["seeds_consumed"]
    src = open(os.path.join(_ROOT, "scripts", "tripwire_repair_measure.py")).read()
    assert "random" not in src, "no sampling ⇒ no seed to burn"
