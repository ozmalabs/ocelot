"""RUN 50 GATE 0 -- unit gates for `domains/relational_variation.py` (the AMORTIZED
RELATIONAL-VARIATION prior: background-learned per-slot tightness weights + a weighted
arrangement-mismatch distance, tested for orthogonality against SC+TPS by the run script).

All synthetic (no real Omniglot files needed), deterministic, no seed writes (this module mints
nothing -- source-audited below).

Covers (per the RUN 50 launch brief):
  1. TIGHT vs LOOSE recovery -- a synthetic population where one relation slot is FIXED across
     "drawers" and another varies widely must recover LOW variance / HIGH weight for the fixed
     slot and the reverse for the varying one.
  2. `relational_distance` is LARGER for a mismatch on a TIGHT slot than an EQUAL-magnitude
     (one-bin) mismatch on a LOOSE slot, given the SAME learned weights.
  3. Determinism -- repeated calls with identical inputs are byte-identical.
  4. The greedy matcher's falsy-zero fix, exercised through this module's own reuse (a genuine
     ZERO-cost stroke match -- two point-for-point-identical strokes -- must not be dropped/
     mis-sorted; regression guard on the REUSE of `run39.greedy_match`, not a new fix, mirroring
     `tests/test_motor_verdict_migrated.py`'s own precedent).
  5. Zero-index / zero-bin values are never dropped by a truthiness check (the launch brief's
     own named pitfall).
"""
from __future__ import annotations

import inspect
import os

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

from domains import relational_variation as rv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")


def _md5(path: str):
    import hashlib
    if not os.path.exists(path):
        return None
    return hashlib.md5(open(path, "rb").read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def _seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after, "seeds/stroke_shapes.json changed across test_relational_variation_migrated.py"


@pytest.fixture(scope="module")
def native():
    return srs.Substrate()._inner


# --------------------------------------------------------------------------------------------- #
# Synthetic composed-signature builder -- a 2-stroke "character": stroke 0 is a short segment
# near the origin, stroke 1 a segment further along -- distinct enough that the greedy matcher
# aligns stroke 0 <-> stroke 0 and stroke 1 <-> stroke 1 by point-set geometry alone.
# --------------------------------------------------------------------------------------------- #
_STROKE0_PTS = [[0.0, 0.0], [0.1, 0.0], [0.2, 0.0]]
_STROKE1_PTS = [[1.0, 1.0], [1.1, 1.0], [1.2, 1.0]]


def _stroke_points(stroke0=_STROKE0_PTS, stroke1=_STROKE1_PTS):
    return [(stroke0, "q0", None, None), (stroke1, "q1", None, None)]


def _sig(rel0, rel1, cpose):
    """`rel0`/`rel1`: (x_q, y_q, o_q, s_q) for stroke 0 / stroke 1. `cpose`: (x, y, o, s)."""
    sig = [["strokeq", 0, "q0"], ["strokeq", 1, "q1"],
           ["rel", 0, *rel0], ["rel", 1, *rel1]]
    for pred, v in zip(rv.CPOSE_SLOTS, cpose):
        sig.append([pred, v])
    return sig


UNIFORM_WEIGHTS = {slot: 1.0 for slot in rv.ALL_SLOTS}


# ===================================================================================== #
# GATE 1 -- tight vs loose recovery from a synthetic drawer population.
# ===================================================================================== #
def test_tight_vs_loose_recovery(native):
    """rel:0:x (stroke 0's x bin) is FIXED at 3 across every "drawer"; rel:0:y varies widely
    (0, 4, 8, 2, 6). Pooled variance must recover x << y, and the weight must invert that
    (weight[rel_x] > weight[rel_y])."""
    ref_pts = _stroke_points()
    ref_sig = _sig(rel0=(3, 0, 0, 3), rel1=(7, 7, 0, 3), cpose=(0, 0, 0, 3))
    y_values = [0, 4, 8, 2, 6]
    others = []
    for y in y_values:
        others.append((_stroke_points(), _sig(rel0=(3, y, 0, 3), rel1=(7, 7, 0, 3),
                                                cpose=(0, 0, 0, 3))))
    variances = rv.class_slot_variances(native, ref_pts, ref_sig, others, turn_bins=12)
    assert variances is not None
    assert variances["rel_x"] < variances["rel_y"], variances
    assert variances["rel_x"] == pytest.approx(0.0, abs=1e-9)
    assert variances["rel_y"] > 1.0

    weights = rv.slot_weights(rv.pool_variation([variances]))
    assert weights["rel_x"] > weights["rel_y"]

    split = rv.tight_loose_split(rv.pool_variation([variances]))
    assert "rel_x" in split["tight"]
    assert "rel_y" in split["loose"]


# ===================================================================================== #
# GATE 2 -- relational_distance weights a tight-slot mismatch more than an equal loose one.
# ===================================================================================== #
def test_distance_penalizes_tight_slot_mismatch_more(native):
    weights = dict(UNIFORM_WEIGHTS)
    weights["rel_x"] = 4.0   # TIGHT (learned)
    weights["rel_y"] = 0.25  # LOOSE (learned)

    query_pts = _stroke_points()
    query_sig = _sig(rel0=(3, 3, 0, 3), rel1=(7, 7, 0, 3), cpose=(0, 0, 0, 3))

    # Candidate A: mismatches ONLY the TIGHT slot (rel_x off by one bin).
    cand_a_pts = _stroke_points()
    cand_a_sig = _sig(rel0=(4, 3, 0, 3), rel1=(7, 7, 0, 3), cpose=(0, 0, 0, 3))
    # Candidate B: mismatches ONLY the LOOSE slot (rel_y off by one bin) -- same magnitude.
    cand_b_pts = _stroke_points()
    cand_b_sig = _sig(rel0=(3, 4, 0, 3), rel1=(7, 7, 0, 3), cpose=(0, 0, 0, 3))

    r_a = rv.relational_distance(native, query_pts, query_sig, cand_a_pts, cand_a_sig, weights)
    r_b = rv.relational_distance(native, query_pts, query_sig, cand_b_pts, cand_b_sig, weights)
    assert r_a["r"] > r_b["r"], (r_a, r_b)

    # And a mismatch-free candidate scores strictly lowest.
    cand_same_sig = _sig(rel0=(3, 3, 0, 3), rel1=(7, 7, 0, 3), cpose=(0, 0, 0, 3))
    r_same = rv.relational_distance(native, query_pts, query_sig, query_pts, cand_same_sig, weights)
    assert r_same["r"] == pytest.approx(0.0, abs=1e-9)
    assert r_same["r"] < r_b["r"] < r_a["r"]


# ===================================================================================== #
# GATE 3 -- determinism.
# ===================================================================================== #
def test_determinism(native):
    query_pts = _stroke_points()
    query_sig = _sig(rel0=(3, 3, 0, 3), rel1=(7, 7, 0, 3), cpose=(0, 0, 0, 3))
    cand_sig = _sig(rel0=(4, 5, 1, 3), rel1=(7, 6, 0, 4), cpose=(1, 0, 0, 3))
    r1 = rv.relational_distance(native, query_pts, query_sig, query_pts, cand_sig, UNIFORM_WEIGHTS)
    r2 = rv.relational_distance(native, query_pts, query_sig, query_pts, cand_sig, UNIFORM_WEIGHTS)
    assert r1 == r2


# ===================================================================================== #
# GATE 4 -- the greedy matcher's falsy-zero fix, exercised through this module's own reuse.
# ===================================================================================== #
def test_greedy_matcher_keeps_a_genuine_zero_cost_match(native):
    """Two point-for-point IDENTICAL strokes must match to each other with a genuine ZERO cost
    -- the falsy-zero bug (`v or nan`) would coerce that zero to NaN and could mis-sort/drop it.
    `align_stroke_points` reuses `run39.greedy_match` (already fixed) rather than run36's own
    buggy `_greedy_stroke_match` -- this is a regression guard on the REUSE, not a new fix."""
    pts = [_STROKE0_PTS, _STROKE1_PTS]
    gm = rv.align_stroke_points(native, pts, pts)
    assert gm["n_true"] == gm["n_pred"] == 2
    assert not gm["unmatched_true"] and not gm["unmatched_pred"]
    matched_pairs = {(i, j) for (i, j, _c) in gm["matched"]}
    assert matched_pairs == {(0, 0), (1, 1)}, matched_pairs


# ===================================================================================== #
# GATE 5 -- zero index / zero bin values are never dropped by a truthiness check.
# ===================================================================================== #
def test_zero_index_and_zero_bin_not_dropped(native):
    """Stroke k=0 with an all-zero rel tuple `(0, 0, 0, 0)` must still contribute to the pooled
    variance/mismatch -- a `.get(k)`/`if value` truthiness bug would silently treat `k=0` or a
    `0` bin as absent."""
    ref_pts = _stroke_points()
    ref_sig = _sig(rel0=(0, 0, 0, 0), rel1=(7, 7, 0, 3), cpose=(0, 0, 0, 0))
    rel_map = rv.rel_by_k(ref_sig)
    assert 0 in rel_map and rel_map[0] == (0, 0, 0, 0)
    cpose = rv.cpose_values(ref_sig)
    assert cpose["cpose_x"] == 0

    other_sig = _sig(rel0=(1, 0, 0, 0), rel1=(7, 7, 0, 3), cpose=(0, 0, 0, 0))
    weights = dict(UNIFORM_WEIGHTS)
    r = rv.relational_distance(native, ref_pts, ref_sig, ref_pts, other_sig, weights)
    assert r["rel_component"] > 0.0     # the k=0, x_q=0 -> 1 mismatch was counted, not dropped.


# ===================================================================================== #
# GATE 6 -- source audit: no Python argmin/argmax/sort-by-score deciding a CLASSIFICATION
# result inside this module (it computes distances/statistics only; the run script's own
# episode loop does any argmin over candidates).
# ===================================================================================== #
def test_no_python_decision_source_audit():
    src = inspect.getsource(rv)
    for banned in ("np.argmin(", "np.argmax(", ".sort(key=", "min(costs", "max(costs"):
        assert banned not in src, f"found banned decision idiom {banned!r} in relational_variation.py"
