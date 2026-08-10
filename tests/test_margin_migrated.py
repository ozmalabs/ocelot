"""RUNG L1c gate — THE DERIVED ADMISSION BOUND (a derived NEGATIVE on the margin) and
the T1 RECORD CORRECTION.

Pins VISION_MARGIN_PREREG.md's arms against the committed
`results/margin_measure.json`, and re-derives the load-bearing claims LIVE against the
graph so the gate is not merely reading its own runner's output back.

The gate is designed to be reddened by the three defects the prereg names (§5):
REFUSE-EVERYTHING must redden the NO-REGRESSION arm; ADMIT-EVERYTHING must redden the
ambiguous-refusal arm; and `eta -> sqrt(2)/2` must redden the PART-A/PART-B arms.
"""
from __future__ import annotations
import ast
import json
import math
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

BOUND = math.sqrt(2) / 2
_RESULTS = os.path.join(_ROOT, "results", "margin_measure.json")
_SEED = os.path.join(_ROOT, "seeds", "vision_margin.json")


@pytest.fixture(scope="module")
def R():
    with open(_RESULTS) as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def seed():
    with open(_SEED) as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def live():
    """A LIVE s=4 instrument graph — eta derived by the seed rule, not by the runner."""
    import margin_measure as mm
    s, ag, native = mm._boot(4)
    return mm, s, ag, native


# ----------------------------- PART A — the derivation -----------------------------
def test_PART_A_every_rival_MARGIN_bound_is_rejected_BY_MEASUREMENT(R):
    """The rung's headline NEGATIVE: no margin bound falls out, and each rival dies to a
    measurement rather than an argument."""
    A = R["PART_A_derivation"]
    for k, a in A.items():
        # M1 — sqrt(2)/2 as a MARGIN refuses everything, at EVERY resolution
        assert a["M1_rows_surviving_margin_sqrt2_2"] == 0, k
        # M3 — a tie-only margin is vacuous
        assert a["M3_exact_ties"] == 0, k
        # M4 — the angle-grid jitter is orders of magnitude below the margin it must separate
        assert a["M4_max_anglegrid_jitter"] < 0.1 * a["M2_median_margin"], k
    # M2 — the margin SCALES with resolution, so no ABSOLUTE value can transfer (§13)
    assert (A["s=1"]["M2_median_margin"] < A["s=2"]["M2_median_margin"]
            < A["s=4"]["M2_median_margin"])
    # M5 — the packing radius is UNSOUND at the aliasing floor and near-vacuous above it
    assert A["s=1"]["M5_certified_AND_WRONG"] > 0, "M5 must be shown UNSOUND at s=1"
    assert A["s=4"]["M5_rows_certified"] <= 10, "M5 must be shown near-vacuous at s=4"


def test_PART_A_the_bound_that_DOES_fall_out_BINDS_where_T1s_does_not(R):
    """A7 — the substance. Inside sqrt(2)/2 the median row carries FOUR candidates;
    inside the derived eta it carries ONE. That is the bound becoming load-bearing."""
    a4 = R["PART_A_derivation"]["s=4"]
    assert a4["A7_ncand_in_sqrt2_2_min_med_max"][1] >= 2, "T1's bound must NOT bind"
    assert a4["A7_ncand_in_eta_min_med_max"][1] == 1, "the derived bound must bind"
    assert (a4["A7_ncand_in_eta_min_med_max"][1]
            < a4["A7_ncand_in_sqrt2_2_min_med_max"][1])


def test_the_derived_bound_can_ONLY_SHRINK_the_admission_set(R):
    """§8 — eta_c <= sqrt(2)/2 for every shape, so this instrument can never widen an
    invariance class. Checked at every resolution."""
    for k, a in R["PART_A_derivation"].items():
        assert a["A7_eta_le_sqrt2_2_for_every_shape"] is True, k
        assert a["A7_eta_max_overall"] <= BOUND + 1e-12, k


def test_eta_is_DERIVED_BY_THE_GRAPH_and_matches_the_committed_values(R, live):
    """§0 — the derivation is the `mg_eta` SEED RULE's, not the adapter's. Read the value
    back off the graph and compare to the committed result."""
    mm, s, ag, native = live
    import continuous_pose_measure as cpm
    committed = R["PART_A_derivation"]["s=4"]["A7_eta_per_shape"]
    for c in cpm.NAMES:
        assert mm.mw.eta_of(s, c) == pytest.approx(committed[c], abs=1e-4)
    # and it is genuinely per-shape, not one constant wearing seven hats
    assert len(set(round(v, 4) for v in committed.values())) >= 5


# ------------------------ PART B — the T1 record correction ------------------------
def test_PART_B_T1s_LANDED_result_is_RANKING_BASED_not_bound_based(R):
    """THE RECORD CORRECTION. Under T1's OWN sqrt(2)/2 bound, ZERO of its 63 headline
    rows are bound-determined — every one of them is decided by the Argmin ranking.
    T1's 63/63 and its exact-0 discrimination STAND as measured; the MECHANISM
    ATTRIBUTION is what this corrects (§13.2 applied to a threshold)."""
    for k, b in R["PART_B_T1_attribution"].items():
        assert b["B1_rows_bound_determined_under_T1s_OWN_sqrt2_2"] == 0, k


def test_PART_B_the_derived_bound_makes_a_MAJORITY_of_T1_bound_determined(R):
    """B2 — pinned at its MEASURED value, not a convenient one."""
    b4 = R["PART_B_T1_attribution"]["s=4"]
    assert b4["n"] == 63
    assert b4["B2_bound_determined_under_derived_eta"] == 38
    assert b4["B2_ranking_only_under_derived_eta"] == 25
    assert (b4["B2_bound_determined_under_derived_eta"]
            + b4["B2_ranking_only_under_derived_eta"]
            + b4["B2_none_under_derived_eta"]) == 63
    # the correction is a strict improvement over T1's own bound
    assert b4["B2_bound_determined_under_derived_eta"] > b4[
        "B1_rows_bound_determined_under_T1s_OWN_sqrt2_2"]


# ------------------------------ PART C — the instrument ------------------------------
def test_C1_no_admitted_row_is_EVER_WRONG_including_at_the_aliasing_floor(R):
    """The reason to exist. At s=1 T1 returns 22 CONFIDENT WRONG identities; every one
    of them must land in the ambiguous set, never admitted. The failing input is present
    in the stimulus set, so this arm CAN fail."""
    c1 = R["PART_C_instrument"]["C1_C2_C3_s=1"]
    c4 = R["PART_C_instrument"]["C1_C2_C3_s=4"]
    assert c1["C1_admitted_AND_WRONG"] == 0
    assert c4["C1_admitted_AND_WRONG"] == 0
    assert c1["ambiguous"] > 0, "the s=1 arm must be ALIVE (§1.1: a dead arm scores a floor)"


def test_C2_NO_REGRESSION_the_conjunction(R):
    """THE ARM A REFUSE-EVERYTHING BUILD MUST BREAK (process rule 5). T1's unambiguous
    cases are still recognised, and every admitted identity is byte-identical to T1's
    own Argmin answer."""
    c4 = R["PART_C_instrument"]["C1_C2_C3_s=4"]
    assert c4["admitted"] == 38, "T1's unambiguous headline cases must still be admitted"
    assert c4["C2_admitted_id_MISMATCH_vs_T1"] == 0
    assert c4["C2_admitted_id_byte_identical_to_T1"] == c4["admitted"]


def test_C3_DISCRIMINATION_exact_0_HOLDS_but_MY_RECALL_PREDICTION_BROKE(R):
    """C3 SPLIT. The exact-0 DISCRIMINATION claim HOLDS — no admitted row anywhere is
    wrong. My pre-registered RECALL prediction ("untransformed 7/7 admitted") BROKE: only
    **2 of 7** untransformed objects are admitted, because an EXACT match (residual 0)
    still sits inside a RIVAL's eta — most visibly X's, which saturates at sqrt(2)/2.

    Pinned at the MEASURED 2, never at the convenient 7 (§3.7 / §5). This is the same
    exchange L1b measured: the instrument buys honesty with RECALL, and the price is
    higher than I predicted."""
    u = R["PART_C_instrument"]["C3_untransformed_admitted"]
    assert u["total"] == 7
    assert u["admitted"] == 2, "the BROKEN prediction, pinned at its real value"
    for k in ("C1_C2_C3_s=1", "C1_C2_C3_s=4"):
        assert R["PART_C_instrument"][k]["C1_admitted_AND_WRONG"] == 0


def test_C4_the_noise_FLOOR_is_ENTAILED_and_reported_NOT_banked(R):
    """Declared ENTAILED in advance: eta <= sqrt(2)/2 makes the admission set a SUBSET of
    T1's, and T1 already refuses 100/100. Reported as consistency, never as evidence."""
    f = R["PART_C_instrument"]["C4_floor"]
    assert f["admitted"] == 0 and f["total"] == 100
    assert f["seeds"] == [51000, 51099]


def test_C5_IS_A_DEAD_ARM_and_is_recorded_as_such_NOT_banked_as_a_floor(R):
    """§1.1, APPLIED TO MYSELF. C5 reports **0 disagreements — out of 0 OPPORTUNITIES.**
    All 100 fresh random 5-cell shapes are REFUSED BY T1 (`status !=
    recognized_continuous`), so the instrument's rules never fire on any of them and every
    row returns an EMPTY `mg_status`. A dead arm scores a perfect floor, and this one did.

    Recorded as the rung's own instrument failure; it supports NO claim. Prereg proviso 1
    anticipated a lopsided split — the reality is worse, the arm is INERT. The
    verification C5 was meant to provide is instead carried by
    `test_the_graph_count_matches_an_INDEPENDENT_recount_on_LIVE_rows`, added AFTER this
    arm was measured dead (stated plainly in the results file)."""
    c5 = R["PART_C_instrument"]["C5_disagreement"]
    assert c5["seeds"] == [51100, 51199]
    assert c5["status_histogram"] == {"": 100}, \
        "if this arm ever comes ALIVE, re-derive what it measures before trusting it"
    assert c5["disagreements"] == 0


def test_the_graph_count_matches_an_INDEPENDENT_recount_on_LIVE_rows(live):
    """What the DEAD C5 arm was meant to do, done on rows where the instrument actually
    FIRES. Added after C5 was measured inert; uses T1's own already-burned deterministic
    stimuli, so it consumes NO seed."""
    mm, s, ag, native = live
    import continuous_pose_measure as cpm
    eta = {c: mm.mw.eta_of(s, c) for c in cpm.NAMES}
    live_rows = 0
    for nm in cpm.NAMES:
        for deg in (5, 45, 85):
            obs = cpm.observe(cpm.OBJ[nm], 4, deg)
            _, _, v = mm._drive(s, ag, native, obs)
            k = sum(1 for d, c in mm._ranked(native, 4, obs) if d <= eta[c])
            assert v["mg_status"] != "", "the arm must be ALIVE (§1.1)"
            assert v["mg_ncand"] == k, (nm, deg, v["mg_ncand"], k)
            live_rows += 1
    assert live_rows == 21


# --------------------------------- §9 / §13 / §0 ---------------------------------
def test_X_the_flag_is_OFF_by_default_and_the_seed_is_INERT(R, seed):
    x = R["X_off_day"]
    assert x["OFF_DAY_CLEAN"] is True
    assert x["mg_attributes_written"] == []
    assert x["mg_eta_derived_anywhere"] == []
    assert x["T1_status"] == "recognized_continuous" and x["T1_covered_by"] == "F"
    assert seed["nodes"][0]["attrs"]["margin"] == 0.0


def test_the_flag_read_is_ABSENCE_TOLERANT_and_never_PickUnique(seed):
    blob = json.dumps(seed)
    assert "PickUnique" not in blob, "§12.3 / process rule 3"
    assert '"MaxOver"' in blob and '"MarginParams"' in blob


def test_this_rung_adds_NO_new_constant(seed):
    """§13. The bound is COMPUTED, never written down. The only literals are the flag
    comparison and the counts 1 and 2 — definitions ('exactly one', 'more than one'),
    not thresholds."""
    lits = set()

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), (int, float)):
                lits.add(float(o["value"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(seed)
    assert lits == {0.0, 0.5, 1.0, 2.0}, lits
    # sqrt(2)/2 is INHERITED from T1 and must not be re-stated as a number here
    assert "0.7071" not in json.dumps(seed)


def test_this_rung_uses_NO_Times_so_the_empty_product_trap_cannot_apply(seed):
    """Process rule 4, discharged BY CONSTRUCTION and asserted."""
    assert '"Times"' not in json.dumps(seed)


def test_the_instrument_never_writes_a_continuous_pose_attribute(seed):
    """Load-bearing, not cosmetic: writing T1's own `status` would let `cp_recognize`
    re-fire forever, and `run_rules` terminates on EXACT VALUE EQUALITY (§2.1)."""
    for rule in seed["rules"]:
        for eff in rule["effects"]:
            assert eff[2] not in ("status", "covered_by"), rule["name"]
            assert eff[2].startswith("mg_"), (rule["name"], eff[2])


def test_the_residual_and_the_winner_are_EXTRACTED_VERBATIM_from_cp_recognize(seed):
    """Single source of truth — the instrument counts EXACTLY what T1 scores, and
    transcription is removed as a failure mode."""
    import tools.build_vision_margin as B
    resid = json.dumps(B._cp_residual_term(), sort_keys=True)
    blob = json.dumps(seed, sort_keys=True)
    # the extracted residual appears verbatim inside the emitted seed
    assert json.dumps(json.loads(resid), sort_keys=True)[1:-1] in blob
    for rule in seed["rules"]:
        for eff in rule["effects"]:
            if eff[2] == "mg_covered_by":
                assert eff[3]["__term__"] == B._cp_argmin_id_term()


def test_no_python_decision_in_the_adapter():
    """§0 / CLAUDE.md, audited on the AST — never by substring (§12's own defect)."""
    src = open(os.path.join(_ROOT, "domains", "margin_world.py")).read()
    tree = ast.parse(src)
    bad = [n for n in ast.walk(tree)
           if isinstance(n, (ast.If, ast.IfExp, ast.Compare, ast.BoolOp))]
    assert not bad, f"decision node(s) in the adapter: {[type(n).__name__ for n in bad]}"
    # and it must not compute the derivation it delegates
    assert "max(" not in src, "the MAX is the seed rule's, not the adapter's"


def test_the_seed_records_that_PART_A_IS_A_NEGATIVE(seed):
    """The negative must survive in the seed itself, not only in a results file."""
    d = seed["description"]
    assert "NO margin bound exists" in d
    assert "rejected" in d and "measurement" in d


def test_this_rung_adds_NO_Rust():
    """§10.1 rule 4 — pinned to THIS RUNG'S OWN DIFF (§12.3): BOTH ENDPOINTS FIXED,
    tracked files only, never base->working-tree and never a repo-wide untracked scan.

    SUPERVISOR REPAIR (2026-07-19). This test previously diffed `base..HEAD` while
    its own docstring claimed to be pinned to this rung's own diff — and `base..HEAD`
    is precisely NOT a rung's own diff, because HEAD moves the moment anything merges.
    It lay dormant only because no rung added Rust for 51 commits; the INK × VENTRAL
    rung (`EnclosedCount`) was the first to meet its trigger condition, and it fired
    a FALSE ACCUSATION against a rung whose underlying claim is TRUE and unchanged:
    the margin rung still adds no Rust. Fourth and fifth occurrence of this defect
    (see also colour-bound, colour-bound-k1, lighting-L4, lighting-L3b).

    A gate that has never been ABLE to fail has not been tested. This one had never
    met its own trigger until now, which is exactly why it shipped wrong.
    """
    import subprocess
    base = "07eeda24"
    rung = "0e93362a76ea210d61a2a6041a51ad052259e258"   # this rung's OWN final commit
    out = subprocess.run(["git", "diff", "--name-only", f"{base}..{rung}"],
                         cwd=_ROOT, capture_output=True, text=True).stdout.split()
    assert not [f for f in out if f.endswith(".rs")], [f for f in out if f.endswith(".rs")]
