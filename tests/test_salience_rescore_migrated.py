"""GATE — VISION_SALIENCE_RESCORE_RESULTS.md.

Pins the pre-registered verdict, the negative control, the independence
property the whole rung rests on, and the §4 diagnostic.

PROVENANCE (§12.3): every diff range in this file has BOTH ENDPOINTS FIXED as
literal shas. `HEAD` is never an endpoint of a diff, in any spelling.
"""
import json
import os
import subprocess

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")

# Both endpoints are immutable shas. BASE is this branch's base commit; RUNG is
# the commit carrying the results document and its pinned result files.
BASE_SHA = "e0b0d0e7c0640a5b75cde323d75504e575a4556a"
PREREG_SHA = "fc9215cb95c2cf7eccb3751e96a8d02c0ee53b39"
RUNG_SHA = "8c72763a168479afc4fad18876ff0d023aa991be"

OWNED = {
    "research/experiments/gamma-substrate/VISION_SALIENCE_RESCORE_PREREG.md",
    "research/experiments/gamma-substrate/VISION_SALIENCE_RESCORE_RESULTS.md",
    "research/experiments/gamma-substrate/VISION_PROTOCOL.md",
    "research/experiments/gamma-substrate/scripts/salience_rescore_frames.py",
    "research/experiments/gamma-substrate/scripts/salience_rescore_field.py",
    "research/experiments/gamma-substrate/scripts/salience_rescore_analyse.py",
    "research/experiments/gamma-substrate/scripts/salience_rescore_diagnose.py",
    "research/experiments/gamma-substrate/tests/test_salience_rescore_migrated.py",
    "research/experiments/gamma-substrate/results/salience_rescore.json",
    "research/experiments/gamma-substrate/results/salience_rescore_field.json",
    "research/experiments/gamma-substrate/results/salience_rescore_diagnose.json",
}


def _load(name):
    p = os.path.join(RESULTS, name)
    if not os.path.exists(p):
        pytest.skip(f"{name} absent")
    with open(p) as fh:
        return json.load(fh)


def _git(*args):
    return subprocess.run(("git",) + args, cwd=HERE, capture_output=True,
                          text=True, check=False).stdout


# --------------------------------------------------------------------------- #
#  The pre-registered verdict
# --------------------------------------------------------------------------- #
def test_c1_misid_is_low_concentrated_but_negligible():
    """C1 satisfies outcome 1 -- and the magnitude is what makes it a non-story."""
    d = _load("salience_rescore.json")
    p = d["corpora"]["C1"]["csal_rgb"]["pooled"]["MISID"]
    assert p["delta_sal"] < 0
    assert p["ci"][1] < 0, "C1 MISID CI must exclude 0 (outcome 1)"
    flat = p["flat"][0]
    weighted = d["corpora"]["C1"]["csal_rgb"]["salience_weighted_misid"]["value"]
    # Re-weighting by salience buys less than one percentage point.
    assert abs(flat - weighted) < 0.01
    assert flat / weighted < 1.02


def test_c2_misid_is_the_null():
    """C2 -- the corpus that motivated the rung -- returns the NULL, not rescued."""
    d = _load("salience_rescore.json")
    p = d["corpora"]["C2"]["csal_rgb"]["pooled"]["MISID"]
    lo, hi = p["ci"]
    assert lo < 0 < hi, "C2 MISID CI must include 0 (outcome 2, the null)"


def test_c2_tiebreak_IS_salience_graded_while_misid_is_not():
    """The asymmetry: salience explains the already-arbitrary mechanism only."""
    d = _load("salience_rescore.json")
    tb = d["corpora"]["C2"]["csal_rgb"]["pooled"]["TIEBREAK"]
    mis = d["corpora"]["C2"]["csal_rgb"]["pooled"]["MISID"]
    assert tb["ci"][1] < 0, "C2 TIEBREAK must be CI-separated negative"
    assert tb["LOW"][0] > 2.0 * tb["HIGH"][0]
    assert mis["ci"][0] < 0 < mis["ci"][1], "C2 MISID must remain the null"


def test_corpora_take_opposite_signs_at_the_best_powered_cells():
    """C1 and C2 differ in SIGN at d=25, with CIs excluding 0. Never pool them."""
    d = _load("salience_rescore.json")
    for cmp_name in ("Q0", "Q1"):
        c1 = d["corpora"]["C1"]["csal_rgb"]["cells"][f"MISID|{cmp_name}|d25"]
        c2 = d["corpora"]["C2"]["csal_rgb"]["cells"][f"MISID|{cmp_name}|d25"]
        assert c1["ci"][1] < 0, f"C1 {cmp_name} d25 should be CI-separated negative"
        assert c2["ci"][0] > 0, f"C2 {cmp_name} d25 should be CI-separated positive"


def test_hpe_robustness_variant_agrees():
    """No verdict turns on the RGB->LMS proxy."""
    d = _load("salience_rescore.json")
    for cid in ("C1", "C2"):
        a = d["corpora"][cid]["csal_rgb"]["pooled"]["MISID"]
        b = d["corpora"][cid]["csal_hpe"]["pooled"]["MISID"]
        assert (a["delta_sal"] < 0) == (b["delta_sal"] < 0)
        # same verdict: CI excludes 0, or does not, in both
        assert ((a["ci"][0] < 0 < a["ci"][1])
                == (b["ci"][0] < 0 < b["ci"][1]))


def test_confounded_lsal_does_not_carry_more_signal_than_csal():
    """The mediation caveat was tested, not merely declared."""
    d = _load("salience_rescore.json")
    c1c = d["corpora"]["C1"]["csal_rgb"]["pooled"]["MISID"]["delta_sal"]
    c1l = d["corpora"]["C1"]["lsal_rgb"]["pooled"]["MISID"]["delta_sal"]
    assert abs(c1l) <= abs(c1c), "lsal must not exceed csal in magnitude on C1"


def test_salience_field_is_not_degenerate():
    """A tercile split over near-constant values would be tie-breaking by index."""
    d = _load("salience_rescore.json")
    for cid in ("C1", "C2"):
        e = d["corpora"][cid]["csal_rgb"]
        assert e["distinct_values_per_frame_mean"] > 14.0
        assert e["frames_with_fewer_than_3_distinct"] == 0
        assert e["within_frame_spread_mean"] > 10.0


# --------------------------------------------------------------------------- #
#  The negative control
# --------------------------------------------------------------------------- #
def test_c3_d0_has_zero_misidentification_for_every_comparator():
    d = _load("salience_rescore.json")
    ctrl = d["C3_d0_control"]
    assert set(ctrl) >= {"Q0", "Q1", "Q2", "Q3", "R", "H"}
    for name, v in ctrl.items():
        assert v["n"] == 384
        assert v["misid"] == 0, f"C3 d=0 {name} must never misidentify"
        assert v["tiebreak"] > 0, f"C3 d=0 {name} loss must be tie-break"


# --------------------------------------------------------------------------- #
#  The §4 diagnostic -- the failure unit is the FRAME
# --------------------------------------------------------------------------- #
def test_short_delta_misidentification_is_a_frame_event():
    d = _load("salience_rescore_diagnose.json")
    c = d["corpora"]["C1"]["cells"]["Q0|d1"]
    assert c["frames_with_any_error"] <= 3
    assert c["share_of_errors_in_top5_frames"] == 1.0
    assert c["gini_over_frames"] > 0.9
    assert c["pearson_r_with_frame_motion"] > 0.9
    assert c["share_of_errors_in_top10pct_motion_frames"] == 1.0


def test_widening_the_orbit_makes_failure_less_frame_concentrated():
    """Q0's d=1 errors are cuts; Q2's are distractor inflation."""
    d = _load("salience_rescore_diagnose.json")
    cells = d["corpora"]["C2"]["cells"]
    ginis = [cells[f"{c}|d1"]["gini_over_frames"] for c in ("Q0", "Q1", "Q2")]
    assert ginis[0] > ginis[1] > ginis[2]
    shares = [cells[f"{c}|d1"]["share_of_errors_in_top10pct_motion_frames"]
              for c in ("Q0", "Q1", "Q2")]
    assert shares[0] > shares[1] > shares[2]


# --------------------------------------------------------------------------- #
#  Adjacency
# --------------------------------------------------------------------------- #
def test_adjacency_excess_is_confined_to_edge_sharing_neighbours():
    d = _load("salience_rescore.json")
    for cid in ("C1", "C2"):
        a = d["corpora"][cid]["adjacency"]
        assert a["adj4"]["diff_ci"][0] > 0, "4-adjacency must exceed geometric chance"
        # the strong 'near-miss' reading is NOT supported
        lo, hi = a["cheb"]["diff_ci"]
        assert lo < 0 < hi, "mean Chebyshev distance must sit at chance"


# --------------------------------------------------------------------------- #
#  Provenance -- BOTH ENDPOINTS FIXED (§12.3)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(RUNG_SHA.startswith("RUNG_SHA"), reason="RUNG_SHA not yet pinned")
def test_rung_diff_touches_no_rust_and_only_owned_paths():
    out = _git("diff", "--name-only", f"{BASE_SHA}..{RUNG_SHA}")
    if not out.strip():
        pytest.skip("range unavailable in this checkout")
    files = [f for f in out.splitlines() if f.strip()]
    assert files, "diff must not be empty"
    for f in files:
        assert not f.endswith(".rs"), f"this rung adds no Rust: {f}"
        assert not f.endswith("Cargo.toml"), f"this rung touches no Cargo: {f}"
        assert f in OWNED, f"unowned path in rung diff: {f}"


@pytest.mark.skipif(RUNG_SHA.startswith("RUNG_SHA"), reason="RUNG_SHA not yet pinned")
def test_rung_adds_no_seed_and_edits_no_committed_seed():
    out = _git("diff", "--name-only", f"{BASE_SHA}..{RUNG_SHA}")
    if not out.strip():
        pytest.skip("range unavailable in this checkout")
    for f in out.splitlines():
        assert "/seeds/" not in f, f"this rung ships no seed: {f}"


def test_prereg_precedes_the_results_commit():
    """Reachability, not a diff: correctly resolved against the moving branch."""
    r = subprocess.run(("git", "merge-base", "--is-ancestor", PREREG_SHA, "HEAD"),
                       cwd=HERE, capture_output=True, check=False)
    assert r.returncode == 0, "the pre-registration must be an ancestor"
