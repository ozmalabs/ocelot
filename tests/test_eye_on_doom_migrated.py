"""GATE for the eye-on-Doom probe (block 152000-152999).

Two independent things are gated:

1. THE SCORER IS CORRECT ON A CONSTRUCTED CASE (always runs, no VizDoom
   needed). A synthetic labels grid with a known object at known cells, and a
   carve cell-set overlapping it by a known amount, must yield the KNOWN IoU /
   precision / recall. This is the part able to FAIL — it prices the metric,
   not the Doom number.

2. THE PROBE RUNS END-TO-END (VizDoom headless -> carve -> ground-truth score)
   and produced the recorded metrics. If VizDoom is unavailable the end-to-end
   half SKIPS EXPLICITLY (never silently passes); the scorer half still runs.

The Doom IoU itself is the FINDING and is NOT hard-coded here — the gate reads
the measured value from results/eye_on_doom.json and asserts only that it is a
well-formed score in [0,1], present for both carve modes and both conditions.
"""
import json
import os

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
import sys
if os.path.join(ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "scripts"))

import eye_on_doom_probe as P  # noqa: E402


# ----------------------------------------------------------------------
#  1. SCORER CORRECTNESS — constructed, deterministic, able to fail
# ----------------------------------------------------------------------
def test_iou_known_values():
    a = frozenset({(0, 0), (0, 1), (1, 0), (1, 1)})     # 4 cells
    assert P.iou(a, a) == 1.0
    b = frozenset({(0, 0), (0, 1)})                     # 2 of a's cells
    # |a&b|=2, |a|b|=4 -> 0.5
    assert P.iou(a, b) == 0.5
    c = frozenset({(5, 5)})                             # disjoint
    assert P.iou(a, c) == 0.0
    # partial overlap: a (4) vs d (4) sharing 1 -> 1/7
    d = frozenset({(1, 1), (2, 2), (2, 3), (3, 3)})
    assert abs(P.iou(a, d) - 1.0 / 7.0) < 1e-12


def test_downsample_labels_modal():
    # 4x4 label buffer, object value 7 fills the top-left 2x2 pixel block ->
    # with gh=gw=2 (2x2 pixels per cell) the top-left CELL is fully object 7.
    lab = np.zeros((4, 4), dtype=np.uint8)
    lab[0:2, 0:2] = 7
    grid = P.downsample_labels(lab, 2, 2)
    assert grid[0, 0] == 7
    assert grid[0, 1] == 0 and grid[1, 0] == 0 and grid[1, 1] == 0


def test_score_frame_known_object():
    # 6x6 grid, one GT object (value 5) is a 2x2 block at rows 2-3 cols 2-3.
    gt = np.zeros((6, 6), dtype=np.int64)
    gt[2:4, 2:4] = 5
    gt_cells = frozenset({(2, 2), (2, 3), (3, 2), (3, 3)})   # 4 cells

    # Carve region EXACTLY the object -> IoU 1.0, recovered, no false positive.
    sc = P.score_frame([gt_cells], gt)
    assert sc["per_obj_best"][5]["iou"] == 1.0
    assert sc["recovery"]["0.5"] == 1.0
    assert sc["false_positive_regions"]["0.5"] == 0
    assert sc["precision"]["0.5"] == 1.0

    # Carve region overlapping HALF (2 of the 4 cells) + 0 extra -> IoU 0.5.
    half = frozenset({(2, 2), (2, 3)})
    sc2 = P.score_frame([half], gt)
    assert sc2["per_obj_best"][5]["iou"] == 0.5
    assert sc2["recovery"]["0.5"] == 1.0     # IoU 0.5 >= threshold 0.5 -> recovered
    assert sc2["recovery"]["0.25"] == 1.0

    # A spurious carve far away -> false positive, object not recovered.
    spurious = frozenset({(0, 0), (0, 1)})
    sc3 = P.score_frame([spurious], gt)
    assert sc3["per_obj_best"][5]["iou"] == 0.0
    assert sc3["recovery"]["0.1"] == 0.0
    assert sc3["false_positive_regions"]["0.1"] == 1     # the spurious region
    assert sc3["precision"]["0.1"] == 0.0


def test_recovery_threshold_boundary():
    # IoU exactly 0.5 counts as recovered at t=0.5 (>=), not at t>0.5.
    gt = np.zeros((4, 4), dtype=np.int64)
    gt[0:2, 0:2] = 3      # 4 cells
    half = frozenset({(0, 0), (0, 1)})     # IoU = 2/4 = 0.5
    sc = P.score_frame([half], gt, iou_thresholds=(0.25, 0.5))
    assert sc["per_obj_best"][3]["iou"] == 0.5
    assert sc["recovery"]["0.5"] == 1.0
    assert sc["recovery"]["0.25"] == 1.0


def test_quantize_levels():
    luma = np.array([[0, 63, 127, 255]], dtype=np.uint8)
    q = P.quantize(luma, 4)      # (v*4)//256
    assert q.tolist() == [[0, 0, 1, 3]]


# ----------------------------------------------------------------------
#  2. END-TO-END — VizDoom headless -> carve -> score (skips if no VizDoom)
# ----------------------------------------------------------------------
def _have_vizdoom():
    try:
        import vizdoom  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _have_vizdoom(), reason="VizDoom unavailable in this env")
def test_probe_ran_and_recorded_wellformed_scores():
    path = os.path.join(ROOT, "results", "eye_on_doom.json")
    if not os.path.exists(path):
        pytest.skip("results/eye_on_doom.json not present (run the probe first)")
    with open(path) as fh:
        r = json.load(fh)
    assert r["scenario"] == "defend_the_center"
    assert r["engine_source_match"] in ("shared", "own")   # never DIVERGED
    # both conditions present; both carve modes produced a well-formed IoU
    for cond in ("stationary", "turning"):
        assert cond in r["runs"], f"missing condition {cond}"
        run = r["runs"][cond]
        assert run["n_frames"] >= 1
        L = str(r["levels"][0])
        for mode in ("value_carve", "motion_carve", "depth_carve"):
            iou = run[mode][L]["enemy_iou"]["mean"]
            assert 0.0 <= iou <= 1.0, f"{cond}/{mode} IoU out of range: {iou}"


@pytest.mark.skipif(not _have_vizdoom(), reason="VizDoom unavailable in this env")
def test_doom_capture_gives_frame_aligned_ground_truth():
    # A short live capture must return frame-aligned RGB + labels-buffer + depth
    # + labels list of matching shape. Mechanical world-adapter check.
    frames = P.capture_doom("attack", n_frames=3)
    assert len(frames) >= 1
    f = frames[0]
    assert f["rgb"].shape[-1] == 3 or f["rgb"].shape[0] == 3
    assert f["labels_buf"].shape == f["depth"].shape        # both 240x320
    # every NAMED object's value is rendered into the labels buffer (frame
    # alignment). NB VizDoom may put extra low reserved values in the buffer
    # with no labels-list entry, so the subset runs list -> buffer, not back.
    lab_vals = set(int(v) for v in np.unique(f["labels_buf"]))
    list_vals = {l["value"] for l in f["labels"]}
    assert list_vals.issubset(lab_vals)
