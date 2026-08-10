#!/usr/bin/env python3
"""THE DOOM REAL-TIME RUNG (seed block 201000-201999) — the post-195000 uniform
real-time CEILING on the shipped photon eye, + the foveated-layout spec.

Prereg: VISION_DOOM_REALTIME_CEILING_PREREG.md (base 0f2eb74a41).

MEASUREMENT ONLY — no Rust, no Term, no seed edit, no eye code change. This is a
mechanical measure-adapter over the SHIPPED photon-eye `_tick`
(`doom_carve_scale_measure._tick`: submit_photons_2d -> run_cognitive_tasks(1) ->
run_rules() -> prune_settled_tasks): the 182000 carve-scale harness over the
181000 photon eye, 191000 event path, 195000-linearised. Feed = real VizDoom
frames. Accelerator OFF (the graph path is the correctness oracle AND where the
195000 run_rules linearisation lives).

IMPORT-INERT: importing this module builds no eye, captures no Doom, times
nothing. All work is inside `main()` / the scoped functions.

USAGE
  PYTHONPATH=runners/dsl/python python scripts/doom_realtime_ceiling_measure.py \
      --out results/doom_realtime_ceiling.json
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
from substrate_rs import _native  # noqa: E402

from domains import doom_photon_world as dpw  # noqa: E402
from domains.photon_eye import GraphEye  # noqa: E402
from scripts.doom_carve_scale_measure import (  # noqa: E402
    build_eye, _tick, capture, WARMUP, ADAPT_RATE, ONSET_DB,
    CARVE_MIN_COH, CARVE_MIN_EVENTS)

AUDIT = _native.Substrate
SEED = 201000


def build_eye_mode(n_el, n_az, mode):
    """Shipped photon eye at (n_el x n_az). `mode`:
      'graph' — the correctness-oracle graph path (build_eye default; run_rules).
      'accel' — the 184000 vectorized mirror (retina_accel; no CognitiveTask/
                run_rules for transduce). The shipped real-time fast path.
      'dirty' — accel + the 185000 dirty index (compute proportional to surprise).
    Identical shipped params to build_eye; only the accel/dirty flags differ."""
    if mode == "graph":
        return build_eye(n_el, n_az)
    ctx = {"retina_2d": True, "synchronous": True, "worker_capacity": 1,
           "onset_threshold_db": ONSET_DB, "onset_refractory_epochs": 0.0,
           "visual_carve": True, "carve_min_coherence": CARVE_MIN_COH,
           "carve_min_events": CARVE_MIN_EVENTS, "retina_accel": True}
    if mode == "dirty":
        ctx["retina_dirty"] = True
    return GraphEye(n_az=n_az, n_el=n_el, adapt_rate=ADAPT_RATE, context=ctx).build()


def _tick_mode(eye, luma, rng, mode, dirty=None):
    """One shipped tick. graph/accel: submit handles the path internally, then
    the fixpoint (carve/onset rules) runs. dirty: pass the change report."""
    if mode == "dirty":
        eye.submit_photons_2d(dpw.photon_packets(luma, rng), dirty=dirty)
    else:
        eye.submit_photons_2d(dpw.photon_packets(luma, rng))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    eye.prune_settled_tasks()

# Prompt's range: cells 300 -> 19,200 (160x120), 64x span, ~geometric.
SWEEP = [(20, 15), (28, 21), (40, 30), (56, 42), (80, 60), (113, 85), (160, 120)]

BUDGETS_MS = (28.5, 33.0)   # 35 fps and 30 fps Doom frame budgets


# ------------------------------------------------------------------ helpers
def _spread(xs):
    xs = sorted(xs)
    n = len(xs)
    return {
        "median_ms": round(float(np.median(xs)), 4),
        "min_ms": round(float(xs[0]), 4),
        "max_ms": round(float(xs[-1]), 4),
        "p25_ms": round(float(np.percentile(xs, 25)), 4),
        "p75_ms": round(float(np.percentile(xs, 75)), 4),
        "n": n,
    }


def _n_onset_events(eye):
    return len(list(eye.substrate.nodes("RetinalOnsetEvent")))


def _time_stream(eye, lumas, rng, reps, mode, dirty_seq=None):
    """Time `reps` steady-state end-to-end ticks over a luma stream (cycled if
    reps>len). Returns (per-tick ms list, onsets fired during window). gc off."""
    per = []
    ev0 = _n_onset_events(eye)
    gc.collect()
    gc.disable()
    try:
        for i in range(reps):
            luma = lumas[i % len(lumas)]
            dirty = None if dirty_seq is None else dirty_seq[i % len(dirty_seq)]
            t0 = time.perf_counter()
            _tick_mode(eye, luma, rng, mode, dirty=dirty)
            per.append((time.perf_counter() - t0) * 1000.0)
    finally:
        gc.enable()
    return per, _n_onset_events(eye) - ev0


def _decompose(eye, lumas, rng, reps, mode):
    """Split the tick into submit_photons_2d (transduce ingest) vs
    run_cognitive_tasks+run_rules (the fixpoint) vs prune. Sums ~ end-to-end."""
    sub_s = fix_s = pr_s = 0.0
    gc.collect(); gc.disable()
    try:
        for i in range(reps):
            luma = lumas[i % len(lumas)]
            t0 = time.perf_counter()
            eye.submit_photons_2d(dpw.photon_packets(luma, rng))
            t1 = time.perf_counter()
            eye.substrate._inner.run_cognitive_tasks(1)
            eye.substrate._inner.run_rules()
            t2 = time.perf_counter()
            eye.prune_settled_tasks()
            t3 = time.perf_counter()
            sub_s += t1 - t0; fix_s += t2 - t1; pr_s += t3 - t2
    finally:
        gc.enable()
    return {"submit_ms": round(sub_s / reps * 1000.0, 4),
            "fixpoint_ms": round(fix_s / reps * 1000.0, 4),
            "prune_ms": round(pr_s / reps * 1000.0, 4)}


def _counters_per_tick(eye, lumas, rng, ticks, mode):
    """Deterministic WORK-COUNT per tick via scale_audit (cand_enum /
    term_evals_total), averaged over `ticks` real-motion ticks."""
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    for i in range(ticks):
        _tick_mode(eye, lumas[i % len(lumas)], rng, mode)
    AUDIT.scale_audit_set_enabled(False)
    c = dict(AUDIT.scale_audit_snapshot())
    return {"cand_enum": c.get("cand_enum", 0),
            "term_evals_total": c.get("term_evals_total", 0),
            "cand_enum_per_tick": c.get("cand_enum", 0) / ticks,
            "term_evals_per_tick": c.get("term_evals_total", 0) / ticks,
            "ticks": ticks}


def run_grid(n_az, n_el, motion_lumas, f0, *, mode="graph", warmup=WARMUP,
             reps=10, count_ticks=4, decompose=True):
    """One grid point in one mode. Steady-state end-to-end ms + counters +
    liveness. Liveness = onset events fired > 0 AND (graph: cand_enum>0)."""
    rng = np.random.default_rng(SEED)
    eye = build_eye_mode(n_el, n_az, mode)
    for _ in range(warmup):
        _tick_mode(eye, f0, rng, mode)
    per, onsets = _time_stream(eye, motion_lumas, rng, reps, mode)
    sp = _spread(per)
    decomp = _decompose(eye, motion_lumas, rng, max(4, reps // 2), mode) if decompose else None
    counters = _counters_per_tick(eye, motion_lumas, rng, count_ticks, mode)
    onset_total = _n_onset_events(eye)
    # Liveness (a dead tick is infinitely fast): real per-tick work is enumerated
    # (cand_enum>0) AND the onset path has fired over the eye's life (onset_total>0
    # — real Doom monster motion at low res is sparse so per-window onset deltas
    # are small, but the transduce+onset fixpoint is demonstrably doing work).
    live = counters["cand_enum"] > 0 and onset_total > 0
    eye.stop()
    return {"grid_az": n_az, "grid_el": n_el, "cells": n_az * n_el, "mode": mode,
            "motion": sp, "onset_events_window": int(onsets),
            "onset_events_total": int(onset_total), "live": bool(live),
            "decompose": decomp, "counters": counters}


def held_uplift(n_az, n_el, motion_lumas, f0, *, warmup=WARMUP, reps=10):
    """SECONDARY (compute proportional to surprise) on the 185000 dirty path.
    HELD = feed the adapted f0 with an EMPTY change report (dirty=[]) -> the eye
    processes only its own not-yet-settled residual -> cheap. CHANGING = feed
    motion with a FULL change report (dirty=all cells) -> full sweep. The ratio
    changing_ms / held_ms is the held-scene uplift on the ceiling."""
    n = n_az * n_el
    all_cells = list(range(n))

    def _held(shed):
        ctx = {"retina_2d": True, "synchronous": True, "worker_capacity": 1,
               "onset_threshold_db": ONSET_DB, "onset_refractory_epochs": 0.0,
               "visual_carve": True, "carve_min_coherence": CARVE_MIN_COH,
               "carve_min_events": CARVE_MIN_EVENTS, "retina_accel": True,
               "retina_dirty": True}
        if shed:
            ctx["retina_dirty_shed"] = True
        eye = GraphEye(n_az=n_az, n_el=n_el, adapt_rate=ADAPT_RATE, context=ctx).build()
        r = np.random.default_rng(SEED)
        for _ in range(warmup):
            _tick_mode(eye, f0, r, "dirty", dirty=all_cells)
        hel, _o = _time_stream(eye, [f0], r, reps, "dirty", dirty_seq=[[]])
        skip = list(getattr(eye, "_skip_log", []) or [])[-reps:]
        eye.stop()
        return float(np.median(hel)), skip

    # CHANGING baseline: full dirty every tick (byte-identical full sweep)
    rng = np.random.default_rng(SEED)
    eye = build_eye_mode(n_el, n_az, "dirty")
    for _ in range(warmup):
        _tick_mode(eye, f0, rng, "dirty", dirty=all_cells)
    chg, _o = _time_stream(eye, motion_lumas, rng, reps, "dirty", dirty_seq=[all_cells])
    eye.stop()
    cm = float(np.median(chg))

    hm_id, skip_id = _held(shed=False)      # BRANCH A — byte-identical
    hm_shed, skip_shed = _held(shed=True)   # BRANCH B — shed (NOT byte-identical)
    return {"cells": n, "changing_ms": round(cm, 4),
            "held_identical_ms": round(hm_id, 4),
            "uplift_identical": round(cm / hm_id, 3) if hm_id > 0 else None,
            "held_identical_skip_per_tick": skip_id,
            "held_shed_ms": round(hm_shed, 4),
            "uplift_shed": round(cm / hm_shed, 3) if hm_shed > 0 else None,
            "held_shed_skip_per_tick": skip_shed}


def _loglog_exponent(cells, ys):
    """Least-squares slope of log(y) vs log(cells) — the scaling exponent."""
    x = np.log(np.asarray(cells, float))
    y = np.log(np.asarray(ys, float))
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"exponent": round(float(b), 4), "coef_a": round(float(math.exp(a)), 6),
            "r2": round(r2, 5)}


def _ceiling(cells, ms, budget):
    """Cell count at a ms budget: piecewise-linear interpolation on the measured
    points (model-free) + a power-law fit read-off. Returns both."""
    cells = np.asarray(cells, float)
    ms = np.asarray(ms, float)
    # piecewise interpolation in LOG-LOG space (the data is a power law, so
    # log(cells) is locally linear in log(ms)) — find the bracket where ms
    # crosses budget and read off the cell count.
    lin = None
    for i in range(len(ms) - 1):
        lo, hi = ms[i], ms[i + 1]
        if (lo - budget) * (hi - budget) <= 0 and hi != lo:
            t = (math.log(budget) - math.log(lo)) / (math.log(hi) - math.log(lo))
            lc = math.log(cells[i]) + t * (math.log(cells[i + 1]) - math.log(cells[i]))
            lin = math.exp(lc)
            break
    if lin is None:
        lin = float("inf") if ms[0] > budget else float(cells[-1])  # below smallest / above largest
    fit = _loglog_exponent(cells.tolist(), ms.tolist())
    a, b = fit["coef_a"], fit["exponent"]
    powc = (budget / a) ** (1.0 / b) if b > 0 else float("nan")
    return {"budget_ms": budget,
            "cells_piecewise": None if lin == float("inf") else int(round(lin)),
            "cells_powerfit": int(round(powc)) if powc == powc else None}


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "doom_realtime_ceiling.json"))
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--nframes", type=int, default=14)
    ap.add_argument("--skip", type=int, default=6)
    args = ap.parse_args()

    from domains.engine_provenance import provenance_line
    prov = provenance_line()
    print(prov)

    # ---- capture real Doom frames ONCE (world-adapter I/O) ------------------
    frames = capture(nframes=args.nframes, skip=args.skip, seed=SEED)
    if len(frames) < 3:
        raise SystemExit(f"capture returned {len(frames)} frames; need >=3")
    print(f"captured {len(frames)} real VizDoom frames (defend_the_line, seed {SEED})")

    # precompute luma grids per resolution
    grids = {}
    for (n_az, n_el) in SWEEP:
        f0 = dpw.luma_grid(frames[0]["rgb"], n_el, n_az).astype(np.float32)
        motion = [dpw.luma_grid(fr["rgb"], n_el, n_az).astype(np.float32)
                  for fr in frames[1:]]
        grids[(n_az, n_el)] = (f0, motion)

    modes = {}
    for mode in ("graph", "accel"):
        print(f"\n--- MODE: {mode} ({'oracle graph path, run_rules' if mode=='graph' else '184000 accelerator, shipped fast path'}) ---")
        rows = []
        for (n_az, n_el) in SWEEP:
            f0, motion = grids[(n_az, n_el)]
            r = run_grid(n_az, n_el, motion, f0, mode=mode, reps=args.reps)
            rows.append(r)
            m = r["motion"]
            print(f"  {n_az:>3}x{n_el:<3} cells={r['cells']:>6}  "
                  f"end2end={m['median_ms']:>8.3f}ms [{m['min_ms']:.2f}-{m['max_ms']:.2f}] "
                  f"p25-75 {m['p25_ms']:.2f}-{m['p75_ms']:.2f}  "
                  f"cand/tick={r['counters']['cand_enum_per_tick']:>10.0f}  "
                  f"tevals/tick={r['counters']['term_evals_per_tick']:>11.0f}  "
                  f"live={r['live']} onsets={r['onset_events_total']}")
        modes[mode] = rows

    # held-scene uplift (dirty path) — one sweep
    print("\n--- HELD-SCENE UPLIFT (185000 dirty path: changing vs held) ---")
    uplifts = []
    for (n_az, n_el) in SWEEP:
        f0, motion = grids[(n_az, n_el)]
        u = held_uplift(n_az, n_el, motion, f0, reps=args.reps)
        uplifts.append(u)
        print(f"  cells={u['cells']:>6}  changing={u['changing_ms']:>7.3f}ms  "
              f"held(id)={u['held_identical_ms']:>7.3f}ms uplift={u['uplift_identical']}x skip={u['held_identical_skip_per_tick'][:2]}  "
              f"held(shed)={u['held_shed_ms']:>7.3f}ms uplift={u['uplift_shed']}x skip={u['held_shed_skip_per_tick'][:2]}")

    def _fit_block(rows):
        cells = [r["cells"] for r in rows]
        ms = [r["motion"]["median_ms"] for r in rows]
        cand = [r["counters"]["cand_enum_per_tick"] for r in rows]
        tev = [r["counters"]["term_evals_per_tick"] for r in rows]
        exps = {"wall_ms": _loglog_exponent(cells, ms)}
        if all(c > 0 for c in cand):
            exps["cand_enum"] = _loglog_exponent(cells, cand)
        if all(t > 0 for t in tev):
            exps["term_evals_total"] = _loglog_exponent(cells, tev)
        ceil = [_ceiling(cells, ms, b) for b in BUDGETS_MS]
        return {"cells": cells, "ms": ms, "exponents": exps, "ceilings": ceil}

    summary = {mode: _fit_block(rows) for mode, rows in modes.items()}

    out = {
        "provenance": prov, "seed": SEED,
        "sweep_cells": [n_az * n_el for (n_az, n_el) in SWEEP],
        "budgets_ms": list(BUDGETS_MS),
        "modes": modes, "summary": summary, "held_uplift": uplifts,
        "history_context": "pre-195000 end-to-end ceiling ~700 receptors @30fps (run_rules O(cells^2))",
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)

    for mode in ("graph", "accel"):
        s = summary[mode]
        print(f"\n=== {mode.upper()} exponents (log-log, cells 300->19200) ===")
        for k, v in s["exponents"].items():
            print(f"  {k:<18} exponent={v['exponent']:>7}  r2={v['r2']}")
        print(f"=== {mode.upper()} ceiling (uniform cells at budget) ===")
        for b, c in zip(BUDGETS_MS, s["ceilings"]):
            print(f"  @ {b}ms: piecewise={c['cells_piecewise']}  powerfit={c['cells_powerfit']}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
