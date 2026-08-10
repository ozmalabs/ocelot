"""RECON (rung B) — committed-system diagnosis of the eye's mint-rule shape.

Measures the per-tick cand_enum (deterministic match work count) scaling of the
2-D retina GRAPH path (onset + carve mint rules), on the COMMITTED engine, with
incremental_match OFF and ON (A's per-edge-type versioning). This is structural
diagnosis of the committed matcher, NOT a rung-B result — B is not built yet.
"""
from __future__ import annotations
import math, os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runners", "dsl", "python"))

import substrate_rs as srs
from domains.photon_eye import GraphEye
from domains import doom_photon_world as dpw

ONSET_DB = 6.0
CARVE_MIN_COH = 0.5
CARVE_MIN_EVENTS = 2.5
SEED = 12345


def build_eye(n_el, n_az):
    return GraphEye(n_az=n_az, n_el=n_el, context={
        "retina_2d": True,
        "onset_threshold_db": ONSET_DB, "onset_refractory_epochs": 0.0,
        "visual_carve": True, "carve_min_coherence": CARVE_MIN_COH,
        "carve_min_events": CARVE_MIN_EVENTS}).build()


def moving_bar_frame(n_el, n_az, phase):
    """A vertical bright bar sweeping across a dark field — produces onsets."""
    luma = np.full((n_el, n_az), 10.0)
    col = phase % n_az
    luma[:, col] = 200.0
    luma[:, (col + 1) % n_az] = 200.0
    return luma


def measure(n_el, n_az, incr, unsound=False, warm=6):
    inner = None
    eye = build_eye(n_el, n_az)
    inner = eye.substrate._inner
    inner.set_incremental_match(incr)
    inner.set_incremental_match_unsound(unsound)
    rng = np.random.default_rng(SEED)
    # Warm up: several ticks so cursors are established and the field is moving.
    for t in range(warm):
        luma = moving_bar_frame(n_el, n_az, t)
        eye.submit_photons_2d(dpw.photon_packets(luma, rng))
        inner.run_cognitive_tasks(1)
        inner.run_rules()
        eye.prune_settled_tasks()
    # Measure ONE tick.
    srs._native.Substrate.scale_audit_set_enabled(True)
    srs._native.Substrate.scale_audit_reset()
    luma = moving_bar_frame(n_el, n_az, warm)
    eye.submit_photons_2d(dpw.photon_packets(luma, rng))
    inner.run_cognitive_tasks(1)
    inner.run_rules()
    snap = dict(srs._native.Substrate.scale_audit_snapshot())
    srs._native.Substrate.scale_audit_set_enabled(False)
    eye.prune_settled_tasks()
    onsets = len(list(eye.substrate.nodes("RetinalOnsetEvent")))
    return snap, onsets


def fit_exp(cells, vals):
    xs = [math.log(c) for c in cells]
    ys = [math.log(max(v, 1)) for v in vals]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


if __name__ == "__main__":
    scales = [(8, 10), (12, 15), (16, 20), (20, 25)]
    for incr in (False, True):
        print(f"\n=== incremental_match={'ON' if incr else 'OFF'} ===")
        cells, ce, ct, we = [], [], [], []
        for (ne, na) in scales:
            snap, onsets = measure(ne, na, incr)
            n = ne * na
            cells.append(n)
            ce.append(snap.get("cand_enum", 0))
            ct.append(snap.get("cand_tested", 0))
            we.append(snap.get("where_evals", 0))
            print(f"  cells={n:5d} ({ne}x{na})  cand_enum={snap.get('cand_enum',0):8d}"
                  f"  cand_tested={snap.get('cand_tested',0):8d}"
                  f"  where_evals={snap.get('where_evals',0):8d}"
                  f"  onsets={onsets}")
        print(f"  EXPONENT cand_enum={fit_exp(cells,ce):.3f}  "
              f"cand_tested={fit_exp(cells,ct):.3f}  where_evals={fit_exp(cells,we):.3f}")
