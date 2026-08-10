"""RUN 54 -- unit gate for the MULTI-GRAIN PREDICTIVE-CODING VERDICT
(`domains/compositional_verdict.py`).

Covers (launch brief's own list): per-stroke residual on synthetics (aligned identical strokes
-> ~0, mismatched -> large); precision-weighting (tight-relation mismatch penalized more than an
equal loose-relation mismatch); the GUARD-reduction invariant (`w_whole=1, w_stroke=0, w_rel=0`
-> the verdict is BYTE-IDENTICAL to the whole-shape argmin); the greedy-matcher falsy-zero fix;
`spread_match_weights` freeze mechanics; a no-Python-decision source audit; and the seed-guard
md5 (this module never writes `seeds/stroke_shapes.json`).

Runs under `.venv` (needs `substrate_rs`) -- the gate script's `unit_sanity` stage invokes it via
`sys.executable`, mirroring run 50/52's own suite discipline.
"""
from __future__ import annotations

import hashlib
import os
import sys

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import substrate_rs as srs
from domains import compositional_verdict as cv
from scripts import jabberwock_omniglot_run39_motorplan as run39

STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")


def _native():
    return srs.Substrate()._inner


def _md5(path):
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _hline(n=12):
    return np.stack([np.linspace(0, 1, n), np.zeros(n)], axis=1)


def _vline(n=12):
    return np.stack([np.ones(n), np.linspace(0, 1, n)], axis=1)


def _circle(n=16, r=0.5):
    t = np.linspace(0, 2 * np.pi, n)
    return np.stack([0.5 + r * np.cos(t), 0.5 + r * np.sin(t)], axis=1)


# ------------------------------------------------------------------------------------------- #
def test_per_stroke_residual_identical_is_small_mismatched_is_large():
    native = _native()
    query = [_hline(), _vline()]              # an L-shaped 2-stroke glyph.
    cand_same = [_hline().copy(), _vline().copy()]
    cand_diff = [_circle(), _vline().copy()]  # first stroke swapped for a very different shape.
    r_same = cv.per_stroke_residual(native, query, cand_same)
    r_diff = cv.per_stroke_residual(native, query, cand_diff)
    assert r_same >= 0.0 and r_diff >= 0.0
    assert r_diff > r_same, f"mismatched stroke should cost more: same={r_same} diff={r_diff}"


def test_per_stroke_residual_single_stroke_is_finite():
    native = _native()
    r = cv.per_stroke_residual(native, [_hline()], [_hline().copy()])
    assert np.isfinite(r) and r >= 0.0


# ------------------------------------------------------------------------------------------- #
def test_precision_weighting_tight_costs_more_than_loose():
    """A mismatch on a TIGHT (high-precision) relation slot must cost more than an equal-magnitude
    mismatch on a LOOSE (low-precision) slot. Built directly on `relation_residual` with a
    hand-made two-stroke composed signature and a weights map that is tight on `rel_x`, loose on
    `rel_y` -- the precision term IS the run-50 tightness weight."""
    native = _native()
    weights = {"rel_x": 4.0, "rel_y": 0.25, "rel_o": 1.0, "rel_s": 1.0,
               "cpose_x": 1.0, "cpose_y": 1.0, "cpose_o": 1.0, "cpose_s": 1.0}
    # Two aligned strokes; query rel bins (k: x,y,o,s).
    q_sig = [["rel", 0, 2, 2, 0, 1], ["rel", 1, 3, 3, 0, 1]]
    # Candidate A differs from query ONLY on the TIGHT slot (rel_x) of stroke 0.
    cand_tight = [["rel", 0, 9, 2, 0, 1], ["rel", 1, 3, 3, 0, 1]]
    # Candidate B differs ONLY on the LOOSE slot (rel_y) of stroke 0, same magnitude of change.
    cand_loose = [["rel", 0, 2, 9, 0, 1], ["rel", 1, 3, 3, 0, 1]]
    # One-stroke-each point sets so the greedy aligner pairs k=0<->0, k=1<->1 trivially.
    q_pts = [(_hline(), None), (_vline(), None)]
    c_pts = [(_hline(), None), (_vline(), None)]
    r_tight = cv.relation_residual(native, q_pts, q_sig, c_pts, cand_tight, weights)
    r_loose = cv.relation_residual(native, q_pts, q_sig, c_pts, cand_loose, weights)
    assert r_tight > r_loose, f"tight mismatch must cost more: tight={r_tight} loose={r_loose}"


# ------------------------------------------------------------------------------------------- #
def test_guard_reduction_invariant():
    """`w_whole=1, w_stroke=0, w_rel=0` -> the multi-grain verdict is BYTE-IDENTICAL to the
    whole-shape argmin, candidate-for-candidate, regardless of the stroke/rel values."""
    native = _native()
    per_cand = [
        dict(whole=0.9, stroke=0.1, rel=5.0),
        dict(whole=0.3, stroke=9.0, rel=9.0),   # lowest whole -> must win under GUARD reduction.
        dict(whole=0.7, stroke=0.0, rel=0.0),
    ]
    pred = cv.verdict_pred(native, per_cand, w_whole=1.0, w_stroke=0.0, w_rel=0.0)
    expected = min(range(len(per_cand)), key=lambda i: per_cand[i]["whole"])
    assert pred == expected == 1
    # total_error_term at the reduction weights evaluates to `whole` exactly.
    for c in per_cand:
        t = cv.total_error_term(c["whole"], c["stroke"], c["rel"],
                                w_whole=1.0, w_stroke=0.0, w_rel=0.0)
        assert float(native.evaluate(t, {})) == c["whole"]


def test_multigrain_can_flip_the_whole_shape_pick():
    """A sanity check that the added levels DO enter: when the whole-shape term ties/mis-ranks but
    a heavily-weighted stroke level clearly separates, the multi-grain verdict follows the stroke
    level (the whole-shape term is not able to veto an orthogonal grain)."""
    native = _native()
    per_cand = [dict(whole=0.50, stroke=9.0, rel=0.0),
                dict(whole=0.51, stroke=0.1, rel=0.0)]   # barely-worse whole, far-better stroke.
    pred = cv.verdict_pred(native, per_cand, w_whole=1.0, w_stroke=1.0, w_rel=0.0)
    assert pred == 1


# ------------------------------------------------------------------------------------------- #
def test_greedy_matcher_keeps_a_genuine_zero_cost_match():
    """The FIXED matcher (`run39.greedy_match`) pairs identical strokes at zero cost rather than
    dropping them as falsy-`nan` -- the run36 `v or nan` bug's regression guard."""
    native = _native()
    strokes = [_hline(), _vline()]
    mapping = run39.greedy_match(native, strokes, [s.copy() for s in strokes])
    assert len(mapping) == 2, f"expected a full bijection, got {mapping}"
    assert mapping == {0: 0, 1: 1}, f"identical strokes should map index-for-index: {mapping}"


# ------------------------------------------------------------------------------------------- #
def test_spread_match_weights_freeze():
    w = cv.spread_match_weights(spread_whole=0.4, spread_stroke=2.0, spread_rel=0.1)
    assert w["w_whole"] == 1.0
    assert abs(w["w_stroke"] - 0.4 / 2.0) < 1e-12
    assert abs(w["w_rel"] - 0.4 / 0.1) < 1e-12
    # zero spread -> honest 0.0 weight, never a divide-by-zero.
    w0 = cv.spread_match_weights(spread_whole=0.4, spread_stroke=0.0, spread_rel=0.0)
    assert w0["w_stroke"] == 0.0 and w0["w_rel"] == 0.0


# ------------------------------------------------------------------------------------------- #
def test_compositional_verdict_no_python_decisions():
    """Source audit: the ranking decision is the held `Argmin`; there is no Python-level
    min/max/sort/argmin over candidate scores anywhere in the module."""
    import re
    src = open(os.path.join(ROOT, "domains", "compositional_verdict.py")).read()
    for banned in ("np.argmin", "np.argmax", "sorted(", ".sort("):
        assert banned not in src, f"banned Python decision primitive {banned!r} found in module"
    # word-boundary min(/max( so prose like "argmin(" (a Term type) does not false-match.
    for banned in (r"\bmin\(", r"\bmax\("):
        assert not re.search(banned, src), f"banned Python decision primitive {banned!r} in module"


def test_seed_guard_md5_unchanged():
    """Importing and exercising the module never writes the parallel-session-owned stroke seed."""
    before = _md5(STROKE_SHAPES_SEED)
    native = _native()
    cv.per_stroke_residual(native, [_hline(), _vline()], [_hline(), _vline()])
    cv.verdict_pred(native, [dict(whole=1.0, stroke=1.0, rel=1.0)],
                    w_whole=1.0, w_stroke=1.0, w_rel=1.0)
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after, "seeds/stroke_shapes.json md5 changed -- a write leaked"
