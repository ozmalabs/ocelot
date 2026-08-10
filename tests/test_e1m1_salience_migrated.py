"""GATE for block 156000-156999 — E1M1 + salience wiring.

Verifies, WITHOUT trusting impressions:

  1. the EXISTING salience operator (`Substrate.shape_salience`) ranks a directed
     / moving trajectory strictly ABOVE a flat / static one — a CONSTRUCTED
     synthetic case that is able to FAIL (if the operator stopped separating
     motion from stasis, this reddens);
  2. the W2 wiring READS that existing signal — `track_salience` delegates to
     `Substrate.shape_salience`, not a Python re-implementation (a known
     input/output must equal the native operator's on the same input);
  3. a CONSTRUCTED moving carved region out-ranks a CONSTRUCTED static one
     through the FULL wiring (tracker -> salience), able to fail;
  4. the E1M1 end-to-end pipeline RUNS on the real WAD and records the W1/W2/W3
     metric structures with in-range values — or SKIPS explicitly if VizDoom or
     the (copyrighted, uncommitted) DOOM.WAD is absent.

Every assertion reads a MEASURED / graph value or a structural invariant; none
pins an exact carve output (§ discipline — score by measured value, never
cross-process region-id or a frozen d2).
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts import e1m1_salience_probe as P  # noqa: E402


def _native_substrate():
    from substrate_rs import _native as n
    return n.Substrate


# ---------------------------------------------------------------------------
# 1. The existing operator separates directed motion from stasis (able to fail)
# ---------------------------------------------------------------------------
def test_shape_salience_operator_ranks_directed_above_static():
    S = _native_substrate()
    directed = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]      # a moving/looming trajectory
    static = [3.0, 3.0, 3.0, 3.0, 3.0, 3.0]        # a view-fixed trajectory
    random = [2.0, -1.0, 3.0, -2.0, 1.0, 0.0]      # a wander (steps cancel)
    s_dir = S.shape_salience(directed)
    s_flat = S.shape_salience(static)
    s_rand = S.shape_salience(random)
    assert s_flat == 0.0, f"a flat trajectory must be non-salient, got {s_flat}"
    assert s_dir > s_flat, f"directed {s_dir} must beat static {s_flat}"
    assert s_dir > s_rand, f"directed {s_dir} must beat random wander {s_rand}"


# ---------------------------------------------------------------------------
# 2. The wiring reads the existing native signal (not a re-implementation)
# ---------------------------------------------------------------------------
def test_wiring_reads_existing_native_signal():
    S = _native_substrate()
    # a track whose centroid-x ramps (directed) -> track_salience must equal the
    # native operator's value on that exact ramp (proving delegation, not a copy)
    ramp = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    track = {"pts": [{"frame": i, "cells": frozenset({(0, i)}),
                      "cy": 0.0, "cx": float(v), "area": 1.0}
                     for i, v in enumerate(ramp)]}
    sal, comp = P.track_salience(track, S)
    native_cx = S.shape_salience(ramp)
    assert comp["cx"] == pytest.approx(native_cx), \
        "track_salience(cx) must be the native Substrate.shape_salience value"
    assert sal == pytest.approx(max(comp["cx"], comp["cy"], comp["area"]))
    # source audit: the probe must not define its own salience arithmetic
    src = open(os.path.join(ROOT, "scripts", "e1m1_salience_probe.py")).read()
    assert "shape_salience" in src, "the wiring must call the native operator"
    assert "def shape_salience" not in src, \
        "the probe must not re-implement the salience operator in Python"


# ---------------------------------------------------------------------------
# 3. A constructed MOVING region out-ranks a constructed STATIC one (able to fail)
# ---------------------------------------------------------------------------
def _block(r0, c0, h=3, w=3):
    return frozenset((r0 + dr, c0 + dc) for dr in range(h) for dc in range(w))


def test_constructed_moving_region_outranks_static_region():
    S = _native_substrate()
    n_frames = 8
    per_frame = []
    for fi in range(n_frames):
        moving = {"cells": _block(2, 2 + fi), "cy": 0.0, "cx": 0.0,
                  "is_ground": 0.0, "rid": 1}       # slides right +1/frame
        static = {"cells": _block(40, 40), "cy": 0.0, "cx": 0.0,
                  "is_ground": 0.0, "rid": 2}       # fixed
        per_frame.append([moving, static])
    tracks = [t for t in P._collect_tracks(per_frame) if len(t["pts"]) >= 3]
    assert len(tracks) >= 2, f"expected a moving + a static track, got {len(tracks)}"
    sal = []
    for t in tracks:
        s, _ = P.track_salience(t, S)
        # a track's mean centroid-x tells moving (drifting) from static (fixed)
        cxs = [p["cx"] for p in t["pts"]]
        sal.append((s, max(cxs) - min(cxs)))
    moving_sal = max(s for s, span in sal if span > 1.0)     # the drifting track
    static_sal = min(s for s, span in sal if span <= 1.0)    # the fixed track
    assert static_sal == 0.0, f"the fixed region must be non-salient, got {static_sal}"
    assert moving_sal > static_sal, \
        f"the moving region {moving_sal} must out-rank the static {static_sal}"


# ---------------------------------------------------------------------------
# 4. E1M1 end-to-end runs and records W1/W2/W3 metrics (skip if WAD/VizDoom gone)
# ---------------------------------------------------------------------------
def test_e1m1_end_to_end_runs_and_records_metrics():
    frames = P.capture_e1m1(n_frames=60)
    if not frames:
        pytest.skip("VizDoom or DOOM.WAD absent — E1M1 end-to-end not runnable here")
    assert len(frames) > 10, "the scripted walk must produce frames"

    # W1: value carve scored vs the labels buffer
    w1, per_frame, gt_grids = P.w1_carve_score(frames, "gate")
    assert w1["n_frames"] == len(frames)
    assert w1["false_positive_regions_per_frame"]["mean"] >= 0.0
    assert w1["ms_per_frame"] > 0.0
    # every reported category IoU is a valid fraction
    for cat, s in w1["iou_by_category"].items():
        assert 0.0 <= s["mean"] <= 1.0, f"{cat} IoU out of range: {s}"

    # W2: salience ranking reads the native operator; AUCs are valid or None
    from substrate_rs import _native as n
    w2 = P.w2_salience_ranking(per_frame, gt_grids, frames, n.Substrate)
    assert w2["n_tracks_scored"] >= 1
    for key in ("auc_foreground_vs_apparatus", "auc_foreground_vs_background"):
        v = w2[key]
        assert v is None or (0.0 <= v <= 1.0), f"{key} out of range: {v}"
    # the cutoff is the existing effort-dial mechanism, not a tuned constant
    assert w2["effort_dial_salience_threshold"] == n.EffortDial().salience_threshold()
    # every category salience is finite and non-negative
    for cat, s in w2["salience_by_category"].items():
        assert s["mean"] >= 0.0 and np.isfinite(s["mean"]), f"{cat}: {s}"

    # W3: egomotion cancellation runs; visibility + cancelled/raw recorded
    w3 = P.w3_egomotion(frames)
    ev = w3["egomotion_visibility"]
    assert 0.0 <= ev["nonzero_flow_fraction_mean"] <= 1.0
    for k in ("raw_monster_iou", "efference_monster_iou"):
        assert 0.0 <= w3[k]["mean"] <= 1.0, f"{k} out of range: {w3[k]}"
