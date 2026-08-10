"""SCALE THE DOOM RETINA + MAKE THE CARVE FIRE — self-contained gate (block 182000).

Pins the mechanism of `scripts/doom_carve_scale_measure.py` on a COMMITTED real
`defend_the_line` frame fixture (luma + modal labels, VizDoom-free):

  * the sub-grid wall REPRODUCES 181000's zero carve at 20x15;
  * the eye's OWN 2-D common-fate carve FIRES at fine grain (N>0 VisionPolygons);
  * the carve RECOVERS the moving monsters -- union carve-vs-labels IoU >= floor
    AND near-perfect precision (the carved cells are almost all on real monsters);
  * polygon count RISES with resolution (0 at the sub-grid grid -> N>0 at fine);
  * REFUSAL: the carve mints ZERO polygons on the STATIC control (no independently
    moving object -> adapted field silent), and fabricates ~no false polygons.

Prereg: VISION_DOOM_CARVE_SCALE_PREREG.md. Timing is DEFERRED (no timing assert).

For SPEED the fine-grain firing test runs on a fixed CROP of the committed 160x120
grids (a ~87x40 window over the monster band, 2px cells -- the mechanism grain);
the RESULTS doc carries the full 160x120 headline (union_iou 0.1215, prec 0.978).
The gate floor (0.08) is the crop's resolution-physics floor with margin.
"""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

pytest.importorskip("substrate_rs")
from scripts import doom_carve_scale_measure as M          # noqa: E402

FIXDIR = os.path.join(ROOT, "tests", "fixtures", "doom_carve_scale")
# Fixed crop of the 160x120 grids (2px cells) over the monster band -- the
# mechanism grain at speed. Deterministic; NOT tuned to the score.
CROP = (46, 86, 33, 120)      # r0, r1, c0, c1  -> 40 rows x 87 cols
IOU_FLOOR = 0.08              # crop resolution-physics floor (full-res H1c is 0.10)
PREC_FLOOR = 0.85
FALSE_POLY_BOUND = 0.10


def _load(tag):
    d = np.load(os.path.join(FIXDIR, f"frames_{tag}.npz"))
    names = json.load(open(os.path.join(FIXDIR, "label_names.json")))
    return d["lumas"], d["labels"], names


@pytest.fixture(scope="module")
def subgrid():
    """20x15 (the sub-grid wall). npoly must be 0; refusal must be 0."""
    lumas, labs, names = _load("20x15")
    lseq = [lumas[i] for i in range(lumas.shape[0])]
    lg = [labs[i] for i in range(1, labs.shape[0])]
    nm = [names[i] for i in range(1, labs.shape[0])]
    n_el, n_az = labs.shape[1], labs.shape[2]
    res = M.carve_scale_run(lseq, lg, nm, n_el, n_az)
    ref = M.refusal_run(lseq[0], n_el, n_az, ticks=len(lseq) - 1)
    return res, ref


@pytest.fixture(scope="module")
def fine():
    """Fine-grain CROP of the 160x120 grids -- the carve must FIRE here."""
    lumas, labs, names = _load("160x120")
    r0, r1, c0, c1 = CROP
    lumas = lumas[:, r0:r1, c0:c1]
    labs = labs[:, r0:r1, c0:c1]
    lseq = [lumas[i] for i in range(lumas.shape[0])]
    lg = [labs[i] for i in range(1, labs.shape[0])]
    nm = [names[i] for i in range(1, labs.shape[0])]
    n_el, n_az = labs.shape[1], labs.shape[2]
    res = M.carve_scale_run(lseq, lg, nm, n_el, n_az)
    ref = M.refusal_run(lseq[0], n_el, n_az, ticks=len(lseq) - 1)
    return res, ref


# ---------------------------------------------------------------- H1a ---------
def test_subgrid_wall_reproduces_zero_carve(subgrid):
    res, _ref = subgrid
    assert res["n_polygons"] == 0, (
        f"sub-grid wall must reproduce the 181000 zero carve, "
        f"got {res['n_polygons']} polygons")


# ---------------------------------------------------------------- H1b ---------
def test_carve_fires_at_scale(fine):
    res, _ref = fine
    assert res["n_polygons"] >= 1, (
        f"the common-fate carve must FIRE at fine grain, "
        f"got {res['n_polygons']} polygons")


# ---------------------------------------------------------------- H1c ---------
def test_carve_recovers_objects(fine):
    res, _ref = fine
    assert res["union_iou"] >= IOU_FLOOR, (
        f"carve-vs-labels union_iou {res['union_iou']} < floor {IOU_FLOOR}")
    assert res["carve_precision"] >= PREC_FLOOR, (
        f"carve precision {res['carve_precision']} < {PREC_FLOOR} "
        f"(carved cells must be almost all on real monsters)")


# ---------------------------------------------------------------- H1d ---------
def test_polygon_count_rises_with_resolution(subgrid, fine):
    sub, _ = subgrid
    fin, _ = fine
    assert fin["n_polygons"] > sub["n_polygons"] == 0, (
        f"polygon count must rise with resolution: sub-grid "
        f"{sub['n_polygons']} -> fine {fin['n_polygons']}")


# ---------------------------------------------------------------- C1 ----------
def test_refusal_static_mints_no_polygons(subgrid, fine):
    _s, sref = subgrid
    _f, fref = fine
    assert sref["n_polygons"] == 0, (
        f"REFUSAL: static field must mint 0 polygons at sub-grid, "
        f"got {sref['n_polygons']}")
    assert fref["n_polygons"] == 0, (
        f"REFUSAL: static field must mint 0 polygons at fine grain, "
        f"got {fref['n_polygons']}")


# ---------------------------------------------------------------- C2 ----------
def test_no_fabricated_false_polygons(fine):
    res, _ref = fine
    assert res["false_poly_rate"] <= FALSE_POLY_BOUND, (
        f"false-poly rate {res['false_poly_rate']} > {FALSE_POLY_BOUND} "
        f"(a carve that fires by covering everything is not a win)")


# ---------- no-Python-agent-decision source audit (architecture rule) ---------
def test_no_agent_decision_in_measure_source():
    src = open(os.path.join(ROOT, "scripts",
                            "doom_carve_scale_measure.py")).read()
    # the carve is the graph-native Rust kernel + seed rule; the adapter must not
    # run the Python rule engine or segment RGB pixels.
    for banned in ("graph_rewrite.run", "gr._match", "gr._apply",
                   "native.segment", "make_rule"):
        assert banned not in src, f"measure adapter must not use {banned}"
