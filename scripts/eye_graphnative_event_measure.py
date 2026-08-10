#!/usr/bin/env python3
"""EYE GRAPH-NATIVE EVENT PATH — measure (seed block 191000-191999).

MECHANICAL MEASURE-ADAPTER. No agent decision, no new seed. It drives the
event-native 2-D photon eye (blocks 164/171-188) through its full per-frame
cycle — submit photons -> settle carve/motion/salience from the onset-event
stream -> run kernels -> read off polygons/percepts/salience -> prune — and
times each stage, comparing the SHIPPED graph-native event path
(`event_native=True`, block 191000) against the old Python per-event marshalling
loop (`event_native=False`, the byte-identity ORACLE).

WHAT THIS ISOLATES. The receptor sheet is accelerated in BOTH arms
(`retina_accel=True`, block 184000) so submit is O(cells) on both sides; the ONLY
difference between the arms is the EVENT PATH (the six `settle_*` methods). So
the settle-stage timing is a clean read of the marshalling cost the 191000 fix
removes. The scene is a full-field MOVING random texture (rolled one column per
frame) on a STILL camera, so onset events fire across ~all cells every frame:
events scale with cells and the event path is exercised at its worst case.

HEADLINE (falsifiable, prereg EYE_GRAPHNATIVE_EVENT_PREREG.md):
  * settle-stage ms/frame vs receptors: BEFORE exponent ~quadratic, AFTER ~1;
  * end-to-end frame ms -> max receptors @30/60 fps, before vs after;
  * name the NEW dominant per-stage cost after the fix.

Cost is WALL-CLOCK (the headline is timing). Run SOLO. Deterministic scene.
Byte-identity of outputs is pinned by tests/test_eye_graphnative_event_migrated.py.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as stats
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains import doom_photon_world as dpw          # noqa: E402
from domains.photon_eye import GraphEye               # noqa: E402

SEED = 191000
ADAPT_RATE = 0.4
ONSET_DB = 6.0
# Resolutions swept (n_az x n_el = cols x rows), 4:3 landscape (same family as the
# doom carve sweep). cells = n_az*n_el = 300 / 1200 / 4800 / 19200.
SWEEP = [(20, 15), (40, 30), (80, 60), (160, 120)]
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(RESULTS, "eye_graphnative_event")


# =====================================================================
#  CORE — importable, self-contained (no VizDoom)
# =====================================================================
def make_scene(n_az, n_el, n_frames, seed=SEED):
    """Full-field moving random texture: a fixed random luma base rolled one
    column per frame. On a still camera every cell's value changes as the
    texture shifts, so onset events fire across ~all cells each frame (events
    scale with cells). Mechanical world I/O."""
    rng = np.random.default_rng(seed)
    base = rng.integers(8, 220, size=(n_el, n_az)).astype(float)
    return [np.roll(base, k, axis=1) for k in range(n_frames)]


def build_eye(n_az, n_el, event_native, perturb=False):
    """The SHIPPED eye: receptor sheet accelerated (184000), all three event
    stages (carve/motion/salience) on. `event_native` switches the 191000 fix
    (True, shipped) vs the old Python loop (False, oracle)."""
    return GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=ADAPT_RATE,
        context={
            "retina_2d": True, "synchronous": True, "worker_capacity": 1,
            "onset_threshold_db": ONSET_DB, "onset_refractory_epochs": 0.0,
            "retina_accel": True,                       # receptor sheet fixed
            "visual_carve": True, "visual_motion": True, "visual_salience": True,
            "carve_min_coherence": 0.5, "carve_min_events": 2.5,
            "event_native": event_native,
            "event_native_perturb": perturb,
        }).build()


def _prune_events(eye):
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)


def _prune_results(eye):
    for t in ("VisionPolygon", "RetinalMotionPercept", "RetinalSalience"):
        for nid in list(eye.substrate.nodes(t)):
            eye.substrate.remove_node(nid)


def _one_frame(eye, luma, rng):
    """One full per-frame cycle, returning per-stage seconds + counts.

    submit -> (onsets minted by accel) -> settle(carve+motion+salience) ->
    kernels -> readout. The settle stage is THE EVENT PATH (what 191000 fixes).
    Pruning (events + minted results + done tasks) happens OUTSIDE the timers so
    steady-state per-frame cost is measured, and pruning is identical in both
    arms."""
    packets = dpw.photon_packets(luma, rng)
    t0 = time.perf_counter()
    eye.submit_photons_2d(packets)
    t1 = time.perf_counter()
    since = eye._epoch
    eye.settle_carve_2d(since_epoch=since)
    eye.settle_motion_2d(since_epoch=since)
    eye.settle_salience_2d(since_epoch=since)
    t2 = time.perf_counter()
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    t3 = time.perf_counter()
    polys = eye.carve_polygons_2d()
    mp = eye.motion_percepts_2d()
    sp = eye.salience_percepts_2d()
    t4 = time.perf_counter()
    n_events = len(list(eye.substrate.nodes("RetinalOnsetEvent")))
    # Housekeeping (outside timers): keep the graph in steady state.
    _prune_results(eye)
    eye.prune_settled_tasks()
    _prune_events(eye)
    return {
        "submit": t1 - t0, "settle": t2 - t1, "kernel": t3 - t2,
        "readout": t4 - t3, "frame": t4 - t0,
        "n_events": n_events, "n_polys": len(polys),
        "n_motion": len(mp), "n_salience": len(sp),
    }


def measure(n_az, n_el, event_native, warmup=2, motion=5, trials=3, seed=SEED):
    """Median per-stage ms over `trials` fresh eyes x `motion` frames (warmup
    frames discarded). Returns per-stage medians (ms) + spreads + event count."""
    per_stage = {k: [] for k in ("submit", "settle", "kernel", "readout", "frame")}
    n_events = n_polys = 0
    for tr in range(trials):
        eye = build_eye(n_az, n_el, event_native)
        frames = make_scene(n_az, n_el, warmup + motion, seed=seed + tr)
        rng = np.random.default_rng(seed + 1000 + tr)
        for i, luma in enumerate(frames):
            r = _one_frame(eye, luma, rng)
            if i >= warmup:
                for k in per_stage:
                    per_stage[k].append(r[k])
                n_events = r["n_events"]
                n_polys = r["n_polys"]
        eye.stop()
    out = {"grid_az": n_az, "grid_el": n_el, "cells": n_az * n_el,
           "event_native": event_native, "n_events_per_frame": n_events,
           "n_polys": n_polys, "samples": len(per_stage["frame"])}
    for k, xs in per_stage.items():
        out[f"{k}_ms"] = round(1000 * stats.median(xs), 4)
        out[f"{k}_ms_min"] = round(1000 * min(xs), 4)
        out[f"{k}_ms_max"] = round(1000 * max(xs), 4)
    return out


def fit_exponent(cells, ms):
    """Log-log slope of ms vs cells (the cost exponent). Least squares."""
    x = np.log(np.asarray(cells, float))
    y = np.log(np.asarray(ms, float))
    A = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(slope), float(intercept)


def max_receptors_at_fps(cells, frame_ms, fps):
    """Given (cells, frame_ms) samples, fit frame_ms ~ a*cells^b and solve for
    the cell count where frame_ms == 1000/fps (the real-time budget). Returns
    the interpolated/extrapolated max receptor count."""
    budget_ms = 1000.0 / fps
    slope, intercept = fit_exponent(cells, frame_ms)
    # log(budget) = slope*log(N) + intercept  ->  N = exp((log(budget)-intercept)/slope)
    logN = (np.log(budget_ms) - intercept) / slope
    return int(round(float(np.exp(logN)))), slope


# =====================================================================
#  DRIVER
# =====================================================================
def run_sweep(sweep=SWEEP, warmup=2, motion=5, trials=3):
    rows = {"native": [], "oracle": []}
    for (n_az, n_el) in sweep:
        for native, tag in ((True, "native"), (False, "oracle")):
            r = measure(n_az, n_el, native, warmup=warmup, motion=motion,
                        trials=trials)
            rows[tag].append(r)
            print(f"{tag:7s} {n_az:3d}x{n_el:3d} cells={r['cells']:6d} "
                  f"ev/frame={r['n_events_per_frame']:6d} "
                  f"submit={r['submit_ms']:8.3f} settle={r['settle_ms']:9.3f} "
                  f"kernel={r['kernel_ms']:8.3f} readout={r['readout_ms']:7.3f} "
                  f"FRAME={r['frame_ms']:9.3f} ms", flush=True)
    return rows


def summarise(rows):
    out = {"rows": rows, "fits": {}, "max_receptors": {}}
    for tag in ("native", "oracle"):
        cells = [r["cells"] for r in rows[tag]]
        for stage in ("settle", "frame"):
            ms = [r[f"{stage}_ms"] for r in rows[tag]]
            slope, intercept = fit_exponent(cells, ms)
            out["fits"][f"{tag}_{stage}_exponent"] = round(slope, 4)
        for fps in (30, 60):
            frame_ms = [r["frame_ms"] for r in rows[tag]]
            n, slope = max_receptors_at_fps(cells, frame_ms, fps)
            out["max_receptors"][f"{tag}_{fps}fps"] = n
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--motion", type=int, default=5)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--out", default=os.path.join(OUTDIR, "curves.json"))
    args = ap.parse_args(argv)
    os.makedirs(OUTDIR, exist_ok=True)
    rows = run_sweep(warmup=args.warmup, motion=args.motion, trials=args.trials)
    summary = summarise(rows)
    print("\n=== EXPONENTS (log-log slope of ms vs cells) ===")
    for k, v in summary["fits"].items():
        print(f"  {k:28s} = {v}")
    print("=== MAX RECEPTORS @ real-time budget ===")
    for k, v in summary["max_receptors"].items():
        print(f"  {k:20s} = {v}")
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nwrote {args.out}")
    return summary


if __name__ == "__main__":
    main()
