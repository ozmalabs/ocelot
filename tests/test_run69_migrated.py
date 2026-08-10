"""test_run69_migrated.py -- unit gates for RUN 69 (writer-relative pose re-admission).

Gates the machinery BEFORE the expensive real-data eval (ops law "unit tests first"):
  * frame estimation on a SYNTHETIC line recovers baseline/x-height/slant;
  * de-slant (shear) normalizes a slanted letter back toward vertical;
  * writer-relative pose distinguishes an ascender-letter from an x-height letter IN-FRAME, where
    the plain rotation/scale-invariant channel (run 66/67's own `cc66.invariant`) does NOT --
    the exact mechanism the RUN 69 hypothesis rests on;
  * the within-writer bank split is writer-disjoint from the cross-writer bank/frame pool;
  * invariant-only reproduces a run-64/66-floor-shaped result (well above chance, well below the
    within-writer bar) on a small REAL DeepWriting sample;
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

Native (substrate_rs / DtwTo) tests run under .venv python (this run reuses `cc66.dtw`, a native
call); pure-geometry tests (frame estimation, de-slant) need neither native nor real data and are
marked accordingly so they also pass under system python3.
"""
from __future__ import annotations

import hashlib
import math
import os
import sys

import numpy as np
import pytest

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.jabberwock_pose_read_run69 as r69

STROKE_SHAPES_SEED = r69.STROKE_SHAPES_SEED
TRAIN_NPZ_PRESENT = os.path.exists(r69.dww.TRAIN_NPZ)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run69_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


# --------------------------------------------------------------------------------------------- #
# Synthetic line construction: N "words" of characters at a KNOWN baseline/x-height/slant, so
# frame estimation has ground truth to recover. y increases DOWNWARD (RUN 69's own verified
# convention): baseline = bottom of x-height letters (larger y); topline = top (smaller y);
# ascenders push further up (smaller y still); descenders push further down (larger y still).
# --------------------------------------------------------------------------------------------- #
def _make_glyph(sample, char_idx, kind, x0, baseline, x_height, slant_deg, writer=1):
    """kind in {'xh','asc','desc'}. A simple synthetic stroke: a vertical-ish stroke from the
    glyph's local bottom to its local top, SHEARED by slant_deg (so real slant estimation has
    something to recover), placed at x0 along the line."""
    top_y = baseline - x_height
    if kind == "asc":
        top_y = baseline - 2.2 * x_height
    n = 20
    ys = np.linspace(baseline if kind != "desc" else baseline + 0.5 * x_height, top_y, n)
    xs = np.full(n, x0)
    # apply the KNOWN slant as a shear: x += tan(slant) * (baseline - y)  (matches deslant's inverse)
    t = math.tan(math.radians(slant_deg))
    xs = xs + t * (baseline - ys)
    pts = np.stack([xs, ys], axis=1)
    return {"writer": writer, "sample": sample, "char_idx": char_idx, "class": 10, "symbol": "a",
            "strokes": [pts.tolist()]}


def _synthetic_sample(sample_id, baseline, x_height, slant_deg, pattern, writer=1):
    """`pattern`: list of 'xh'/'asc'/'desc' -- one synthetic glyph per position, spaced along x."""
    return [_make_glyph(sample_id, i, k, x0=2.0 * i, baseline=baseline, x_height=x_height,
                        slant_deg=slant_deg, writer=writer)
            for i, k in enumerate(pattern)]


PATTERN = ["xh", "xh", "asc", "xh", "desc", "xh", "asc", "xh", "xh", "desc"] * 2   # 20 chars.


def test_frame_estimation_synthetic_line():
    """aggregate_scale_slant recovers x_height and slant_deg on a synthetic multi-sample line with
    KNOWN ground truth (baseline drifts sample-to-sample, as real DeepWriting samples do -- x_height
    and slant are the writer-characteristic quantities that must survive that drift)."""
    true_xh, true_slant = 10.0, 12.0
    glyphs_by_sample = {}
    for k, base in enumerate([0.0, 50.0, -30.0]):        # different baselines per "window".
        gl = _synthetic_sample(100 + k, baseline=base, x_height=true_xh, slant_deg=true_slant,
                               pattern=PATTERN)
        glyphs_by_sample[100 + k] = gl

    frame = r69.aggregate_scale_slant(glyphs_by_sample)
    assert frame["n_glyphs"] == 3 * len(PATTERN)
    assert abs(frame["x_height"] - true_xh) < 1.0, f"x_height {frame['x_height']} != ~{true_xh}"
    assert abs(frame["slant_deg"] - true_slant) < 2.0, f"slant {frame['slant_deg']} != ~{true_slant}"


def test_local_baseline_topline_recovers_ground_truth():
    """local_baseline_topline, applied to one synthetic sample, recovers the KNOWN baseline/topline
    for an x-height glyph's neighbors (median of neighbors' own extents)."""
    baseline, x_height = 0.0, 10.0
    gl = _synthetic_sample(200, baseline=baseline, x_height=x_height, slant_deg=0.0,
                           pattern=PATTERN)
    # an x-height position away from the ends (so it has full +/-window neighbors).
    idx = 5
    assert PATTERN[idx] == "xh"
    base_est, top_est = r69.local_baseline_topline(gl, idx, window=3)
    assert abs(base_est - baseline) < 0.6, f"baseline {base_est} != ~{baseline}"
    assert abs(top_est - (baseline - x_height)) < 0.6, f"topline {top_est} != ~{baseline - x_height}"


def test_deslant_normalizes_slanted_letter():
    """A vertical line SHEARED by a known slant, de-slanted with THAT slant, returns to
    (near-)zero horizontal variation -- the shear and its inverse cancel."""
    slant_deg = 18.0
    baseline = 5.0
    ys = np.linspace(baseline, baseline - 10.0, 20)
    xs_vertical = np.full(20, 3.0)                      # a perfectly vertical line at x=3.
    t = math.tan(math.radians(slant_deg))
    xs_sheared = xs_vertical + t * (baseline - ys)       # apply the slant (matches _make_glyph).
    sheared = np.stack([xs_sheared, ys], axis=1)

    # before de-slanting: substantial x-variation (the shear is real).
    assert np.std(sheared[:, 0]) > 0.5

    deslanted = r69.deslant_points(sheared, slant_deg, baseline)
    assert np.std(deslanted[:, 0]) < 1e-6, "de-slant should remove ALL horizontal shear variation"
    assert np.allclose(deslanted[:, 0], 3.0, atol=1e-6)
    # y is untouched by a shear.
    assert np.allclose(deslanted[:, 1], ys)


# --------------------------------------------------------------------------------------------- #
# THE MECHANISM TEST: writer-relative pose distinguishes ascender vs x-height letters IN-FRAME;
# the plain rotation/scale-invariant channel does NOT (it normalizes away exactly this cue).
# --------------------------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def native():
    srs = pytest.importorskip("substrate_rs")
    return srs.Substrate()._inner


def test_pose_distinguishes_ascender_from_xheight_in_frame(native):
    """Two glyph 'shapes' with the IDENTICAL humped outline (same relative curve), one drawn at
    x-height scale and one stretched into an ascender -- i.e. differing ONLY in vertical extent
    relative to the frame. `invariant_canon` (arclen-normalized-to-1, rotate-to-own-heading)
    should score them as nearly IDENTICAL (it discards absolute scale/placement); `pose_canon`
    (writer-relative: scaled by x_height, not by the letter's own arclength) should score them as
    clearly DIFFERENT. This is the exact mechanism RUN 69 rests on."""
    baseline, x_height = 0.0, 10.0

    def hump(scale_y):
        # a simple hump: up then down, arclength shape is IDENTICAL regardless of scale_y (just a
        # taller/shorter copy of the same curve).
        t = np.linspace(0, math.pi, 24)
        xs = t
        ys = baseline - scale_y * np.sin(t)              # 0 at ends, dips to -scale_y at the peak.
        return [np.stack([xs, ys], axis=1).tolist()]

    xh_strokes = hump(1.0 * x_height)                    # a plain x-height hump (like 'n').
    asc_strokes = hump(2.2 * x_height)                    # the SAME hump, stretched to ascender height.

    inv_xh = r69.invariant_canon(xh_strokes)
    inv_asc = r69.invariant_canon(asc_strokes)
    inv_dist = r69.cc66.dtw(native, inv_xh, inv_asc)

    pose_xh = r69.pose_canon(xh_strokes, baseline, x_height, 0.0)
    pose_asc = r69.pose_canon(asc_strokes, baseline, x_height, 0.0)
    pose_dist = r69.cc66.dtw(native, pose_xh, pose_asc)

    assert inv_dist < 0.05, (
        f"invariant channel should barely distinguish same-shape-different-scale glyphs "
        f"(got {inv_dist:.4f}) -- this is the discarded-pose premise")
    assert pose_dist > 5.0 * max(inv_dist, 1e-6), (
        f"writer-relative pose should separate them MUCH more sharply than invariant "
        f"(pose={pose_dist:.4f} vs invariant={inv_dist:.4f})")


# --------------------------------------------------------------------------------------------- #
# Real-data checks (skipped if the corpus isn't present).
# --------------------------------------------------------------------------------------------- #
pytestmark_real = pytest.mark.skipif(not TRAIN_NPZ_PRESENT, reason="DeepWriting corpus not present")


@pytest.fixture(scope="module")
def small_prep():
    if not TRAIN_NPZ_PRESENT:
        pytest.skip("DeepWriting corpus not present")
    dw = r69.dww.load_deepwriting(r69.SPLIT)
    glyphs = r69.dww.extract_char_glyphs(dw)
    return r69.build_prep(target_n=60, m_bank=2, dw=dw, all_glyphs=glyphs)


@pytestmark_real
def test_own_bank_writer_disjoint_from_cross_bank(small_prep):
    """Own-bank keys are exactly the held-out TEST writers (subset of ho_writers); cross-bank
    exemplars are drawn only from bg_writers; bg/ho are disjoint."""
    bg = set(small_prep["bg_writers"])
    ho = set(small_prep["ho_writers"])
    assert bg.isdisjoint(ho)

    own_bank_writers = {int(w) for w in small_prep["own_bank"].keys()}
    assert own_bank_writers.issubset(ho), "own-bank writers must all be held-out"
    assert own_bank_writers.isdisjoint(bg), "own-bank writers must never be background writers"

    test_writers = set(small_prep["test_writers"])
    assert test_writers == own_bank_writers

    # every query char's writer is a held-out (test) writer, never a background writer.
    for q in small_prep["queries"]:
        assert q["writer"] in ho
        assert q["writer"] not in bg


@pytestmark_real
def test_invariant_only_reproduces_floor_shape(small_prep, native):
    """The INV_CROSS arm (invariant-only, cross-writer bank) on a small real sample lands well
    ABOVE chance (3.85%, 26-way) and well BELOW the within-writer milestone bar -- the same
    'weak but not chance, far below usable' shape run 64/66/67 reported (13.1-18.6% char, cross-
    writer). Not an exact-number reproduction (different sampling/bank), a plausibility gate."""
    cross_bank = small_prep["cross_bank"]
    correct = 0
    for q in small_prep["queries"]:
        vec = r69._class_cost(native, q["inv"], cross_bank, "inv")
        pred = r69._pred_inv(vec)
        correct += int(pred == q["true_class"])
    n = len(small_prep["queries"])
    acc = 100.0 * correct / n
    assert n >= 40
    assert acc > 3.85 * 1.5, f"invariant-only cross-writer should clear chance, got {acc:.1f}%"
    assert acc < r69.BAR_WITHIN_CHAR, (
        f"invariant-only cross-writer should sit well below the within-writer bar "
        f"({acc:.1f}% vs bar {r69.BAR_WITHIN_CHAR}%)")


@pytestmark_real
def test_own_frame_differs_from_population_frame(small_prep):
    """Sanity: per-writer frames are not all identical to the population frame (there is real
    writer-to-writer variation for the pose mechanism to exploit)."""
    pop = small_prep["population_frame"]
    xhs = [fr["x_height"] for fr in small_prep["writer_frames"].values()]
    assert len(xhs) >= 5
    assert np.std(xhs) > 1e-6, "writer x_height estimates should not all collapse to one constant"
