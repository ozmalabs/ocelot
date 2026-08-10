"""RUN 54b -- unit gate for the RELIABILITY-WEIGHTED level calibration
(`domains/compositional_verdict.reliability_weights`).

Covers: reliability-weighting gives the STRONG grain a DOMINANT weight and a chance-level (weak)
grain a ~0 weight on a synthetic; the GUARD-reduction invariant still holds (a chance-level weak
grain drops out -> the multi-grain verdict is byte-identical to the whole-shape argmin); freeze/
determinism mechanics; and the seed-guard md5 (this module never writes the stroke seed).

Runs under `.venv` (needs `substrate_rs`) -- the gate's `unit_sanity` stage invokes it via
`sys.executable`, mirroring run 50/54's own suite discipline.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import substrate_rs as srs
from domains import compositional_verdict as cv

STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
CHANCE = 1.0 / 20.0


def _native():
    return srs.Substrate()._inner


def _md5(path):
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


# ------------------------------------------------------------------------------------------- #
def test_reliability_weights_strong_grain_dominates_weak():
    """A STRONG grain (whole 85% standalone) is the reference (w_whole=1); a MODERATE grain
    (stroke ~40%) enters proportionally smaller; a CHANCE-level grain (rel ~5%) reads reliability
    ~0 and gets a ~0 weight. Equal spreads isolate the reliability factor from scale."""
    w = cv.reliability_weights(acc_whole=0.85, acc_stroke=0.40, acc_rel=0.05,
                               spread_whole=0.2, spread_stroke=0.2, spread_rel=0.2,
                               chance=CHANCE)
    assert w["w_whole"] == 1.0
    # whole-shape strictly dominates both weaker grains.
    assert w["w_whole"] > w["w_stroke"] > w["w_rel"], w
    # the chance-level grain drops out entirely.
    assert w["w_rel"] == 0.0, w
    # the moderate grain enters at reliability_stroke/reliability_whole (spreads equal):
    #   (0.40-0.05)/0.95 / ((0.85-0.05)/0.95) = 0.35/0.80 = 0.4375.
    assert abs(w["w_stroke"] - 0.4375) < 1e-9, w
    # reliabilities exposed and chance-corrected.
    assert abs(w["reliability"]["whole"] - (0.80 / 0.95)) < 1e-9
    assert w["reliability"]["rel"] == 0.0


def test_reliability_weights_fold_in_scale():
    """The weight is reliability-ratio TIMES spread-match: a weaker grain on a SMALLER spread is
    scaled UP by spread_whole/spread_grain (run 44a scale-dominance guard kept), then DOWN by its
    reliability ratio. Distinct spreads exercise both factors."""
    w = cv.reliability_weights(acc_whole=0.85, acc_stroke=0.40, acc_rel=0.30,
                               spread_whole=0.24, spread_stroke=0.12, spread_rel=0.06,
                               chance=CHANCE)
    r_whole = 0.80 / 0.95
    r_stroke = 0.35 / 0.95
    r_rel = 0.25 / 0.95
    assert abs(w["w_stroke"] - (r_stroke / r_whole) * (0.24 / 0.12)) < 1e-9, w
    assert abs(w["w_rel"] - (r_rel / r_whole) * (0.24 / 0.06)) < 1e-9, w


def test_reliability_guard_reduction_when_weak_grains_are_chance():
    """When BOTH added grains are at chance, reliability_weights -> {w_whole=1, 0, 0}, so the
    multi-grain verdict is BYTE-IDENTICAL to the whole-shape argmin (the GUARD-reduction invariant
    holds through the reliability path)."""
    native = _native()
    w = cv.reliability_weights(acc_whole=0.85, acc_stroke=CHANCE, acc_rel=0.0,
                               spread_whole=0.2, spread_stroke=0.2, spread_rel=0.2,
                               chance=CHANCE)
    assert w["w_stroke"] == 0.0 and w["w_rel"] == 0.0
    per_cand = [dict(whole=0.9, stroke=0.0, rel=0.0),
                dict(whole=0.3, stroke=9.0, rel=9.0),   # lowest whole must win.
                dict(whole=0.7, stroke=0.0, rel=0.0)]
    pred = cv.verdict_pred(native, per_cand, w_whole=w["w_whole"], w_stroke=w["w_stroke"],
                           w_rel=w["w_rel"])
    guard = cv.verdict_pred(native, per_cand, w_whole=1.0, w_stroke=0.0, w_rel=0.0)
    assert pred == guard == 1


def test_reliability_weights_degenerate_spread_is_zero_not_crash():
    """A zero/absent spread or zero whole-reliability yields an honest 0.0 weight, never a
    divide-by-zero."""
    w = cv.reliability_weights(acc_whole=0.85, acc_stroke=0.40, acc_rel=0.30,
                               spread_whole=0.2, spread_stroke=0.0, spread_rel=0.2,
                               chance=CHANCE)
    assert w["w_stroke"] == 0.0
    w2 = cv.reliability_weights(acc_whole=CHANCE, acc_stroke=0.40, acc_rel=0.30,
                                spread_whole=0.2, spread_stroke=0.2, spread_rel=0.2,
                                chance=CHANCE)
    # whole at chance -> reliability_whole 0 -> every added grain drops out (no division by 0).
    assert w2["w_stroke"] == 0.0 and w2["w_rel"] == 0.0


def test_reliability_weights_freeze_determinism():
    """Pure arithmetic -> identical inputs give identical weights (freeze mechanics)."""
    args = dict(acc_whole=0.85, acc_stroke=0.388, acc_rel=0.30,
                spread_whole=0.2462, spread_stroke=0.2165, spread_rel=0.1650, chance=CHANCE)
    a = cv.reliability_weights(**args)
    b = cv.reliability_weights(**args)
    assert a == b


def test_reliability_no_python_decision_tokens():
    """The added function introduces no banned Python ranking primitive (the module-wide audit
    also runs in run 54's own suite; this re-checks after the run-54b addition)."""
    src = open(os.path.join(ROOT, "domains", "compositional_verdict.py")).read()
    for banned in ("np.argmin", "np.argmax", "sorted(", ".sort("):
        assert banned not in src, banned
    for banned in (r"\bmin\(", r"\bmax\("):
        assert not re.search(banned, src), banned


def test_seed_guard_md5_unchanged():
    before = _md5(STROKE_SHAPES_SEED)
    cv.reliability_weights(acc_whole=0.85, acc_stroke=0.40, acc_rel=0.30,
                           spread_whole=0.2, spread_stroke=0.2, spread_rel=0.2, chance=CHANCE)
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after
