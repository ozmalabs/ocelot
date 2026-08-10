"""THE ACCELERATION — self-contained gate (block 184000).

Pins the DROPPABLE, BYTE-IDENTICAL vectorized mirror of the 2-D retina sheet
(Rust `retina_onset_batch`, adapter flag `retina_accel`) on the COMMITTED real
`defend_the_line` fixture (`tests/fixtures/doom_carve_scale/frames_160x120.npz`,
VizDoom-free):

  (a) BYTE-IDENTITY / DROPPABLE (the PRIMARY gate) — the full common-fate carve
      protocol run with the accelerator ON vs OFF produces byte-identical
      outputs: the same VisionPolygons, the same onset-event stream (the async
      percept the carve reads), the same union_iou/precision, AND the same
      per-cell rod adaptation (the state that persists across ticks). OFF is the
      graph/run_rules path — the correctness oracle. Able to fail: if the batch
      mirror computed anything differently, a stream/polygon/adaptation diverges.

  (b) FALSIFIER (non-vacuity) — a deliberately-perturbed kernel
      (`retina_accel_perturb`) MUST break the ON≡OFF onset stream. Proves the
      byte-identity check in (a) can DETECT a wrong mirror (it is not vacuous).

  (c) CELLS AXIS LINEARIZED — per-tick cost vs cells: the graph/OFF path is
      super-linear (the residual O(cells²) the 183000 prune left), the
      accelerated/ON path is ~linear, with a large speedup. Able to fail: if the
      batch reintroduced per-cell run_rules cost the exponent/speedup collapse.
      Timing THRESHOLDS are ratio/exponent shapes (process-independent) with
      conservative margins, not fragile absolute ms.

Prereg: VISION_EYE_ACCEL_PREREG.md.
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
from scripts import eye_accel_measure as A          # noqa: E402


@pytest.fixture(scope="module")
def frames():
    return A._load_fixture()


def _frames_at(f, n_el, n_az):
    lumas_full, labels_full, names = f
    lumas = [A._area_mean(lumas_full[i], n_el, n_az)
             for i in range(lumas_full.shape[0])]
    lg = [A._downsample_labels(labels_full[i], n_el, n_az)
          for i in range(1, labels_full.shape[0])]
    nm = [names[i] for i in range(1, labels_full.shape[0])]
    return lumas, lg, nm


# ---------------------------------------------------------------- (a) ----------
@pytest.mark.parametrize("n_az,n_el", [(20, 15), (40, 30), (80, 60)])
def test_accel_is_byte_identical_and_droppable(frames, n_az, n_el):
    """PRIMARY: accelerator ON vs OFF -> identical polygons, onset stream,
    iou/precision, AND rod adaptation. OFF is the graph/run_rules oracle."""
    lumas, lg, nm = _frames_at(frames, n_el, n_az)
    r_on = A.carve_run(lumas, lg, nm, n_el, n_az, accel=True)
    r_off = A.carve_run(lumas, lg, nm, n_el, n_az, accel=False)
    assert A._poly_key(r_on["polygons"]) == A._poly_key(r_off["polygons"])
    assert r_on["onset_stream"] == r_off["onset_stream"]
    assert r_on.get("union_iou") == r_off.get("union_iou")
    assert r_on.get("carve_precision") == r_off.get("carve_precision")
    assert r_on["rod_adaptation"] == r_off["rod_adaptation"]
    # the accelerator mints NO per-cell CognitiveTask nodes (only the single
    # carve task remains), while both arms end with the same onset events.
    assert r_on["tasks_left"] == r_off["tasks_left"]


# ---------------------------------------------------------------- (b) ----------
def test_perturbed_kernel_breaks_identity(frames):
    """FALSIFIER: a wrong mirror (perturb) diverges from the graph path — the
    byte-identity check is NON-VACUOUS (it can detect a wrong kernel)."""
    lumas, lg, nm = _frames_at(frames, 40, 30)
    r_off = A.carve_run(lumas, lg, nm, 30, 40, accel=False)
    r_pert = A.carve_run(lumas, lg, nm, 30, 40, accel=True, perturb=True)
    assert r_pert["onset_stream"] != r_off["onset_stream"]
    # ... and the correct mirror at the same grid does NOT diverge (guard: the
    # test only catches a WRONG mirror, not any accelerator).
    r_on = A.carve_run(lumas, lg, nm, 30, 40, accel=True)
    assert r_on["onset_stream"] == r_off["onset_stream"]


# ---------------------------------------------------------------- (c) ----------
def test_cells_axis_linearized_and_speedup(frames):
    """Per-tick cost vs cells: OFF (graph) super-linear, ON (accel) ~linear, with
    a large speedup at 4800. Exponent/ratio shapes with conservative margins."""
    grids = [(20, 15), (40, 30), (80, 60)]     # 300 / 1200 / 4800
    accel_pt, graph_pt, cells = [], [], []
    for (n_az, n_el) in grids:
        lumas, _, _ = _frames_at(frames, n_el, n_az)
        r_on = A.carve_run(lumas, None, None, n_el, n_az, accel=True, max_ticks=2)
        r_off = A.carve_run(lumas, None, None, n_el, n_az, accel=False,
                            max_ticks=2)
        accel_pt.append(float(np.median(r_on["per_tick"][2:])))
        graph_pt.append(float(np.median(r_off["per_tick"][2:])))
        cells.append(n_az * n_el)
    exp_accel = A.fit_exponent(cells, accel_pt)
    exp_graph = A.fit_exponent(cells, graph_pt)
    speedup_4800 = graph_pt[-1] / accel_pt[-1]

    # accelerated cells axis is ~linear (conservative <= 1.4), graph is
    # super-linear, and the drop is real.
    assert exp_accel <= 1.4, f"accel exponent {exp_accel} not linearized"
    assert exp_graph - exp_accel >= 0.3, (
        f"exponent drop {exp_graph - exp_accel} too small "
        f"(graph {exp_graph}, accel {exp_accel})")
    # a clear speedup at 4800 (prereg >=5x; conservative gate margin 3x).
    assert speedup_4800 >= 3.0, f"speedup@4800 {speedup_4800}x below margin"
