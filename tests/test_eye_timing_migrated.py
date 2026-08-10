"""KILL THE QUADRATIC — self-contained gate (block 183000).

Pins the settled-task-prune fix (`GraphEye.prune_settled_tasks`, wired into the
2-D carve/measure scaling path) on the COMMITTED real `defend_the_line` fixture
(`tests/fixtures/doom_carve_scale/frames_160x120.npz`, VizDoom-free):

  (a) BYTE-IDENTITY (the PRIMARY gate) — the full common-fate carve protocol run
      WITH the prune vs WITHOUT it produces byte-identical outputs: the same
      VisionPolygons AND the same onset-event stream (the async percept the carve
      reads). Able to fail: if the prune removed anything still read, the streams
      or polygons would diverge.

  (b) QUADRATIC -> LINEAR — un-pruned, per-cell transduce tasks accumulate and
      per-tick cost CLIMBS over the run (cumulative cost ~quadratic in ticks);
      pruned, per-tick cost is FLAT (cumulative ~linear) and no tasks are left.
      Able to fail: if the prune stopped clearing tasks (accumulation returns) or
      if it changed outputs (byte-identity above breaks).

  (c) the prune touches ONLY terminal-status retina tasks — a mechanical scope
      check (a still-requested task and a non-retina done task both survive).

Prereg: VISION_EYE_TIMING_PREREG.md. Timing THRESHOLDS here are ratio/exponent
shapes (process-independent), not fragile absolute ms.
"""
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
from scripts import eye_timing_measure as T          # noqa: E402


@pytest.fixture(scope="module")
def frames():
    lumas_full, labels_full, names = T._load_fixture()
    return lumas_full, labels_full, names


def _frames_at(f, n_el, n_az):
    lumas_full, labels_full, names = f
    lumas = [T._area_mean(lumas_full[i], n_el, n_az)
             for i in range(lumas_full.shape[0])]
    lg = [T._downsample_labels(labels_full[i], n_el, n_az)
          for i in range(1, labels_full.shape[0])]
    nm = [names[i] for i in range(1, labels_full.shape[0])]
    return lumas, lg, nm


# ---------------------------------------------------------------- (a) ----------
@pytest.mark.parametrize("n_az,n_el,cap", [(20, 15, None), (40, 30, 4)])
def test_prune_is_byte_identical(frames, n_az, n_el, cap):
    """PRIMARY: prune vs no-prune -> identical polygons AND onset stream."""
    lumas, lg, nm = _frames_at(frames, n_el, n_az)
    r_prune = T.carve_run(lumas, lg, nm, n_el, n_az, do_prune=True, max_ticks=cap)
    r_noprune = T.carve_run(lumas, lg, nm, n_el, n_az, do_prune=False,
                            max_ticks=cap)
    assert T._poly_key(r_prune["polygons"]) == T._poly_key(r_noprune["polygons"])
    assert r_prune["onset_stream"] == r_noprune["onset_stream"]
    assert r_prune.get("union_iou") == r_noprune.get("union_iou")
    assert r_prune.get("carve_precision") == r_noprune.get("carve_precision")
    # the point of the fix: no-prune leaves the accumulated residue, prune clears it
    assert r_noprune["tasks_left"] > r_prune["tasks_left"]


# ---------------------------------------------------------------- (b) ----------
def test_accumulation_quadratic_without_prune_flat_with(frames):
    """Un-pruned: per-tick CLIMBS (cumulative ~quadratic), tasks accumulate.
    Pruned: per-tick FLAT (cumulative ~linear), zero tasks left."""
    lumas, _, _ = _frames_at(frames, 30, 40)      # 1200 cells
    n_ticks = 7
    pt_np, tasks_np = T.accumulation_run(lumas, 30, 40, n_ticks, do_prune=False)
    pt_pr, tasks_pr = T.accumulation_run(lumas, 30, 40, n_ticks, do_prune=True)

    idx = list(range(1, n_ticks + 1))
    cum_exp_np = T.fit_exponent(idx, np.cumsum(pt_np))
    cum_exp_pr = T.fit_exponent(idx, np.cumsum(pt_pr))

    # accumulation: tasks pile up without the prune, cleared with it
    assert tasks_pr == 0
    assert tasks_np >= 40 * 30 * (n_ticks - 1)     # ~ one task/cell/tick retained

    # per-tick climbs without prune, flat with it
    assert pt_np[-1] / pt_np[0] > 2.0
    assert pt_pr[-1] / pt_pr[0] < 1.8

    # cumulative-cost-vs-ticks exponent: quadratic vs linear, clearly separated
    assert cum_exp_np > 1.6
    assert cum_exp_pr < 1.35
    assert cum_exp_np - cum_exp_pr > 0.4


# ---------------------------------------------------------------- (c) ----------
def test_prune_only_removes_terminal_retina_tasks(frames):
    """Scope check: prune_settled_tasks removes a done retina task, keeps a
    still-requested retina task and a done NON-retina task."""
    eye = T.build_eye(15, 20)
    s = eye.substrate
    done_retina = s.add_node("CognitiveTask",
                             {"status": "done", "area": "retina", "kind": "x"})
    req_retina = s.add_node("CognitiveTask",
                            {"status": "requested", "area": "retina", "kind": "x"})
    done_other = s.add_node("CognitiveTask",
                            {"status": "done", "area": "cortex", "kind": "x"})
    removed = eye.prune_settled_tasks()
    assert removed >= 1
    assert not s.has_node(done_retina)
    assert s.has_node(req_retina)
    assert s.has_node(done_other)
    eye.stop()
