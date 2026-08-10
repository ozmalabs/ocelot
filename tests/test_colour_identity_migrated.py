"""COLOUR IDENTITY — categorical colour as a MINTED, MDL-GATED SIGN: the migrated
gate (VISION_COLOUR_IDENTITY_PREREG.md).

Deterministic. Pins the claim that categorical colour is a quantum minted from the
opponent-colour VALUE subspace by the sd loop's DYNAMIC-QUANTIZATION pattern
(decode -> recognize -> mint -> re-decode on codebook_epoch growth), MDL-gated, via
ONE seed (vision_colour_identity: ci_opponent / ci_mint_category / ci_assign) with
NO new Rust. Downstream of colour-salience (WHERE to look) it answers WHAT COLOUR IT
IS:

  * EMERGENCE / MDL — a scene with 3 colour clusters mints exactly 3 category
    quanta (k << N), MDL compresses (72 -> 42, 1.71x). Categories EMERGE from the
    distribution; they are NOT hand-set.
  * ASSIGNMENT — every cell's sign is its own category at dist 0; an off-prototype
    cell gets its NEAREST quantum; a NEW instance of a seen colour is RECOGNIZED,
    not re-minted (the has-guard).
  * GRADIENT FLOOR — a smooth monotone colour ramp (all shades distinct) mints
    ZERO categories (no false category per shade).
  * NOISE FLOOR — iid colour noise mints no coherent category (a small sample here;
    the 100-seed confirmatory floor lives in scripts/colour_identity_measure.py).
  * DOWNSTREAM — the flag is load-bearing (categories + signs ON, absent OFF).
  * §9 — the seed is inert with the flag OFF (default): byte-identity holds.

m_min = 3 falls out of the coordinate dimensionality d = 2 (a category pays iff
m*d > d+m, i.e. m > d/(d-1) = 2), NOT a tuned threshold (§13).
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from scripts.colour_identity_measure import (  # noqa: E402
    arm_E, arm_A, arm_G, arm_D, arm_X, arm_N)


def test_emergence_three_clusters_mint_three_categories_and_mdl_compresses():
    r = arm_E()
    assert r["pass"], r
    assert r["n_categories"] == 3                       # one quantum per cluster
    assert r["categories"] == [                          # correct opponent coords
        {"crg": -10, "cby": 0, "members": 12},
        {"crg": 0, "cby": 12, "members": 12},
        {"crg": 10, "cby": 0, "members": 12}]
    assert r["mdl_categorized"] < r["mdl_raw"]           # MDL compresses
    assert r["mdl_categorized"] == 42 and r["mdl_raw"] == 72
    assert r["mdl_ratio"] >= 1.5
    assert r["all_signs_correct"]


def test_assignment_correct_sign_nearest_quantum_and_recognize_not_remint():
    r = arm_A()
    assert r["pass"], r
    # (a) every cell recognized as its own category at dist 0
    assert r["a_all_signs_correct"]
    # (b) an off-prototype cell gets its NEAREST minted quantum
    assert tuple(r["b_probe_sign"]) == (10, 0)          # nearest = A, not B
    assert r["b_probe_dist"] == 4.0                     # dist 4 (vs B's 16)
    assert r["b_n_categories"] == 2
    # (c) a NEW instance of a seen colour is RECOGNIZED, not re-minted
    assert r["c_n_before"] == 1 and r["c_n_after"] == 1
    assert tuple(r["c_new_sign"]) == (10, 0) and r["c_new_dist"] == 0.0


def test_smooth_gradient_mints_zero_categories():
    r = arm_G()
    assert r["pass"], r
    assert r["distinct_colours"] == 36                  # every shade distinct
    assert r["n_categories"] == 0                       # no false category per shade
    assert r["n_assigned"] == 0


def test_colour_noise_mints_no_coherent_category():
    # small sample here (10 seeds); the 100-seed confirmatory floor is in the runner.
    r = arm_N(n_seeds=10, base_seed=35000)
    assert r["pass"], r
    assert r["false_mint_fields"] == 0


def test_flag_is_load_bearing_downstream():
    r = arm_D()
    assert r["pass"], r
    assert r["on_categories"] == 3 and r["off_categories"] == 0
    assert r["d_categories"] > 0 and r["d_sign_max"] > 0 and r["d_op_done_max"] > 0


def test_offday_seed_is_inert_by_default():
    r = arm_X()
    assert r["pass"], r
    assert r["n_categories"] == 0
    assert r["max_op_done"] == 0.0 and r["max_sign_rg"] == 0.0
