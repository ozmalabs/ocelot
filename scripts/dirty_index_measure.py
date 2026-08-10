#!/usr/bin/env python3
"""THE PER-AREA DIRTY-INDEX — per-tick cost O(SURPRISE), not O(cells) (block 185000).

184000 vectorized the uniform retina sheet (cells exponent 1.838 -> 1.072,
30.5 fps @160x120) and named its own residual: an O(cells) FLOOR — the batch
touches EVERY cell EVERY tick. This rung processes only the CHANGED cells.

THE CENTRAL TENSION, resolved explicitly (see VISION_DIRTY_INDEX_PREREG.md).
"Skip unchanged cells" is NOT trivially byte-identical: the per-receptor floor is
an EMA that keeps moving toward `caught` even when the input is frozen. Two
branches, measured separately and never conflated:

  BRANCH A (EXACT). Skip a cell ONLY when re-processing it would be BIT-IDENTICAL
    to skipping it. The float64 EMA DOES reach an exact fixed point — at
    adapt_rate 0.4 after t* ~= 71 ticks of bit-repeatable input — after which the
    update is a genuine no-op. Byte-identity is then PROVABLE and the win is FREE.
  BRANCH B (BOUNDED SHEDDING). Skip cells whose photon count moved by <= delta
    from the last PROCESSED input. A SEMANTIC OPTION, DEFAULT OFF, NO byte-identity
    claim — reported as a measured speed<->fidelity curve.

MECHANICAL MEASURE-ADAPTER. No agent decision. Frames come from the COMMITTED
real `defend_the_line` fixture (VizDoom-free). Two sensors, both already in the
world adapter: the Poisson shot-noise sensor (`photon_counts(luma, rng)` — the
default; every cell's count changes every tick) and the noiseless "read the true
field" sensor (`rng=None` — a held frame is bit-repeatable).
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.photon_eye import GraphEye                       # noqa: E402
from domains import doom_photon_world as dpw                  # noqa: E402
from scripts import doom_carve_scale_measure as M             # noqa: E402
from scripts import eye_accel_measure as EA                   # noqa: E402

SEED = 185000
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(RESULTS, "dirty_index")

ADAPT_RATE = M.ADAPT_RATE
HOLD = 80          # > t* (~71) so the EXACT fixed point is reached in-protocol
SWEEP = [(20, 15), (40, 30), (80, 60), (160, 120)]

# 184000's measured baseline (results/eye_accel.json), for the overlay.
BASE_184000 = {300: 0.0003737909719347954, 1200: 0.0015700089861638844,
               4800: 0.006637629994656891, 19200: 0.0328213035245426}


# ---------------------------------------------------------------- fixture ------
def _resize_nn(grid, n_el, n_az):
    """Nearest-neighbour resample (used ONLY to reach a resolution above the
    fixture's native 160x120 for the scaling fact). Mechanical."""
    H, W = grid.shape
    r = (np.arange(n_el) * H // n_el).clip(0, H - 1)
    c = (np.arange(n_az) * W // n_az).clip(0, W - 1)
    return grid[np.ix_(r, c)]


def _grid(luma_full, n_el, n_az):
    H, W = luma_full.shape
    if H % n_el == 0 and W % n_az == 0 and H >= n_el and W >= n_az:
        return EA._area_mean(luma_full, n_el, n_az)
    return _resize_nn(luma_full, n_el, n_az)


# ---------------------------------------------------------------- the eye ------
def build_eye(n_el, n_az, *, accel=True, dirty=False, stamp=True, naive=False,
              perturb=False, shed=False):
    return GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=ADAPT_RATE,
        context={"retina_2d": True, "synchronous": True, "worker_capacity": 1,
                 "onset_threshold_db": M.ONSET_DB, "onset_refractory_epochs": 0.0,
                 "visual_carve": True, "carve_min_coherence": M.CARVE_MIN_COH,
                 "carve_min_events": M.CARVE_MIN_EVENTS,
                 "retina_accel": accel, "retina_accel_perturb": perturb,
                 "retina_dirty": dirty, "retina_dirty_stamp_epoch": stamp,
                 "retina_dirty_naive": naive,
                 "retina_dirty_shed": shed}).build()


def rod_state(eye):
    """The FULL per-cell persistent receptor state — every attribute the sheet
    carries across ticks, at full precision (`repr` of the float)."""
    n = eye.n_az * eye.n_el
    rods = [eye._receptors[(f, "rod")] for f in range(n)]
    return {k: [repr(x) for x in eye.substrate.get_attr_many(rods, k)]
            for k in ("adaptation", "activation", "prev_activation",
                      "caught_quanta", "input_epoch")}


def onset_stream(eye):
    return sorted(
        (int(round(float(eye.substrate.node(nd)["attrs"]["column_index"]))),
         int(round(float(eye.substrate.node(nd)["attrs"].get("row_index", 0.0)))),
         int(round(float(eye.substrate.node(nd)["attrs"]["epoch"]))),
         repr(float(eye.substrate.node(nd)["attrs"]["magnitude_db"])))
        for nd in eye.substrate.nodes("RetinalOnsetEvent"))


class Sensor:
    """The world's change-reporting photon sensor (mechanical I/O).

    Holds the last REPORTED per-cell count so a sub-delta drift accumulates
    against the last value the eye actually folded (a dead-band, never a reset).
    """

    def __init__(self, delta=0):
        self.delta = delta
        self.last = None

    def submit(self, eye, grid, rng=None):
        counts = dpw.photon_counts(grid, rng)
        flat = counts.reshape(-1)
        ch = dpw.changed_cells(counts, self.last, self.delta)
        if self.last is None:
            self.last = flat.copy()
        else:
            self.last = self.last.copy()
            self.last[ch] = flat[ch]
        pk = dpw.packets_from_counts(counts, ch)
        t0 = time.perf_counter()
        eye.submit_photons_2d(pk, dirty=ch)
        return time.perf_counter() - t0, len(ch)

    def submit_full(self, eye, grid, rng=None):
        """The 184000/graph arm: the whole sheet, every tick, no change report."""
        counts = dpw.photon_counts(grid, rng)
        pk = dpw.packets_from_counts(counts, None)
        t0 = time.perf_counter()
        eye.submit_photons_2d(pk)
        return time.perf_counter() - t0, eye.n_az * eye.n_el


# ---------------------------------------------------------------- protocol -----
def hold_carve_run(lumas, label_grids, names_motion, n_el, n_az, *, arm,
                   hold=HOLD, delta=0, naive=False, noiseless=True, seed=SEED,
                   max_ticks=None, stamp=True):
    """The 182000 carve protocol with the adaptation hold EXTENDED past t*.

    arm: "dirty" (dirty-index ON), "accel" (184000 full sweep), "graph"
    (retina_accel OFF — the run_rules oracle). Identical frames, identical
    sensor, identical carve settle in every arm.
    """
    f0 = _grid(lumas[0], n_el, n_az)
    motion = [_grid(f, n_el, n_az) for f in lumas[1:]]
    if max_ticks is not None:
        motion = motion[:max_ticks]
    eye = build_eye(n_el, n_az, accel=(arm != "graph"), dirty=(arm == "dirty"),
                    stamp=stamp, naive=naive)
    rng = None if noiseless else np.random.default_rng(seed)
    sensor = Sensor(delta)
    per_tick, reported = [], []

    def one(grid):
        if arm == "dirty":
            dt, k = sensor.submit(eye, grid, rng)
        else:
            t0 = time.perf_counter()
            counts = dpw.photon_counts(grid, rng)
            eye.submit_photons_2d(dpw.packets_from_counts(counts, None))
            if arm == "graph":
                eye.substrate._inner.run_cognitive_tasks(1)
                eye.substrate._inner.run_rules()
                eye.prune_settled_tasks()
            dt, k = time.perf_counter() - t0, n_el * n_az
        per_tick.append(dt)
        reported.append(k)

    for _ in range(hold):
        one(f0)
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for g in motion:
        one(g)
    eye.settle_carve_2d(since_epoch=since)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    score = (M.score_carve(polys, names_motion, label_grids, n_el, n_az)
             if label_grids is not None else {})
    out = {"polygons": polys, "per_tick": per_tick, "reported": reported,
           "onset_stream": onset_stream(eye), "rod": rod_state(eye),
           "skipped": list(eye._skip_log), **score}
    eye.stop()
    return out


def poisson_carve_run(lumas, label_grids, names_motion, n_el, n_az, *, arm,
                      delta=0, seed=182000, warmup=M.WARMUP, stamp=True,
                      shed=False):
    """The LANDED 182000 carve protocol, VERBATIM photon stream.

    Uses `dpw.photon_packets(luma, rng)` — the exact per-cell Poisson draw order
    the landed 4 / 0.1215 / 0.9784 number was produced with — and derives the
    change report from those very packets, so the dirty arm sees the SAME light.
    """
    f0 = _grid(lumas[0], n_el, n_az)
    motion = [_grid(f, n_el, n_az) for f in lumas[1:]]
    eye = build_eye(n_el, n_az, accel=(arm != "graph"), dirty=(arm == "dirty"),
                    stamp=stamp, shed=shed)
    rng = np.random.default_rng(seed)
    n = n_el * n_az
    last = None
    per_tick = []

    def one(grid):
        nonlocal last
        pk = dpw.photon_packets(grid, rng)          # the landed photon stream
        if arm != "dirty":
            t0 = time.perf_counter()
            eye.submit_photons_2d(pk)
            if arm == "graph":
                eye.substrate._inner.run_cognitive_tasks(1)
                eye.substrate._inner.run_rules()
                eye.prune_settled_tasks()
            per_tick.append(time.perf_counter() - t0)
            return
        counts = np.zeros(n, dtype=np.int64)
        for p in pk:
            counts[int(p["row"]) * n_az + int(p["col"])] = int(p["count"])
        ch = (np.arange(n) if last is None
              else np.flatnonzero(np.abs(counts - last) > delta))
        last = counts.copy() if last is None else last.copy()
        last[ch] = counts[ch]
        # The reported cells' packets, rebuilt EXACTLY as `photon_packets` emits
        # them (a zero count emits nothing) — the same light, fewer messages.
        sub = [{"col": int(f) % n_az, "row": int(f) // n_az,
                "wavelength_nm": dpw.ROD_NM, "count": int(counts[f])}
               for f in ch if counts[f] > 0]
        t0 = time.perf_counter()
        eye.submit_photons_2d(sub, dirty=ch)
        per_tick.append(time.perf_counter() - t0)

    for _ in range(warmup):
        one(f0)
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for g in motion:
        one(g)
    eye.settle_carve_2d(since_epoch=since)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    score = (M.score_carve(polys, names_motion, label_grids, n_el, n_az)
             if label_grids is not None else {})
    out = {"polygons": polys, "per_tick": per_tick,
           "onset_stream": onset_stream(eye), "rod": rod_state(eye),
           "skipped": list(eye._skip_log), **score}
    eye.stop()
    return out


def poly_key(polys):
    return EA._poly_key(polys)


def state_equal(a, b, keys=("adaptation", "activation", "prev_activation",
                            "caught_quanta")):
    return all(a["rod"][k] == b["rod"][k] for k in keys)


# ------------------------------------------------------------- cost harness ----
def settled_eye(n_el, n_az, grid, hold=HOLD, delta=0, stamp=True):
    """Adapt an eye to a held frame until the EXACT fixed point is reached.
    Returns (eye, sensor, per-tick list, skipped-per-tick list)."""
    eye = build_eye(n_el, n_az, dirty=True, stamp=stamp)
    sensor = Sensor(delta)
    ticks = []
    for _ in range(hold):
        dt, _k = sensor.submit(eye, grid)
        ticks.append(dt)
    return eye, sensor, ticks, list(eye._skip_log)


def cost_at_worklist(eye, sensor, grid, k, reps=7, rng=None):
    """Median per-tick cost when the sensor reports EXACTLY k cells.

    The reported cells are re-presented with their UNCHANGED input, so the work
    is real (payload build + FFI + kernel + writes + settle check) and the sheet
    stays settled — which makes the cost-vs-work-list-size curve repeatable and
    isolates exactly the quantity of interest.
    """
    n = eye.n_az * eye.n_el
    rng = rng or np.random.default_rng(SEED + 7)
    counts = dpw.photon_counts(grid)
    out = []
    for _ in range(reps):
        cells = (np.arange(n) if k >= n
                 else np.sort(rng.choice(n, size=k, replace=False)))
        pk = dpw.packets_from_counts(counts, cells)
        t0 = time.perf_counter()
        eye.submit_photons_2d(pk, dirty=cells)
        out.append(time.perf_counter() - t0)
    return float(np.median(out))


def fit_affine(ks, ts):
    ks = np.asarray(ks, float)
    ts = np.asarray(ts, float)
    a, b = np.polyfit(ks, ts, 1)
    pred = a * ks + b
    ss_res = float(((ts - pred) ** 2).sum())
    ss_tot = float(((ts - ts.mean()) ** 2).sum())
    return float(a), float(b), (1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0)


# ------------------------------------------------------------------ main -------
def main(trials=3):
    os.makedirs(OUTDIR, exist_ok=True)
    from domains.engine_provenance import provenance_stamp
    prov = provenance_stamp(strict=False)
    lumas_full, labels_full, names = EA._load_fixture()
    lumas = list(lumas_full)
    rep = {"block": SEED, "engine_source_match": prov.get("source_match"),
           "adapt_rate": ADAPT_RATE, "hold": HOLD, "trials": trials,
           "baseline_184000_per_tick_s": BASE_184000}

    _lab_cache = {}

    def labels_at(n_el, n_az):
        if (n_el, n_az) not in _lab_cache:
            _lab_cache[(n_el, n_az)] = (
                [EA._downsample_labels(labels_full[i], n_el, n_az)
                 for i in range(1, labels_full.shape[0])],
                [names[i] for i in range(1, labels_full.shape[0])])
        return _lab_cache[(n_el, n_az)]

    # ---- C0: WHEN does the exact predicate fire? (the branch decision) --------
    c0 = {}
    for tag, noisy in (("noiseless", False), ("poisson", True)):
        eye = build_eye(120, 160, dirty=True)
        sensor = Sensor(0)
        rng = np.random.default_rng(SEED) if noisy else None
        g = _grid(lumas[0], 120, 160)
        frac, ticks = [], []
        for _t in range(120):
            dt, _k = sensor.submit(eye, g, rng)
            frac.append(eye._skip_log[-1] / 19200.0)
            ticks.append(dt)
        c0[tag] = {"skipped_fraction": frac, "per_tick": ticks,
                   "first_tick_above_0.5": next(
                       (i + 1 for i, f in enumerate(frac) if f > 0.5), None),
                   "max_fraction": max(frac),
                   "fraction_before_tick_65": max(frac[:64]) if frac else None,
                   "fraction_at_tick_90": frac[89]}
        eye.stop()
        print(f"[C0 {tag}] max skipped fraction={max(frac):.4f} "
              f"first>50% at tick={c0[tag]['first_tick_above_0.5']} "
              f"@tick90={frac[89]:.4f} pre-65 max={c0[tag]['fraction_before_tick_65']:.4f}",
              flush=True)
    rep["C0_exact_predicate"] = c0

    # ---- C1a/b: BYTE-IDENTITY, dirty-ON vs 184000 accel vs the graph path -----
    ident = []
    for (n_az, n_el) in SWEEP:
        lg, nm = labels_at(n_el, n_az)
        r_on = hold_carve_run(lumas, lg, nm, n_el, n_az, arm="dirty")
        r_off = hold_carve_run(lumas, lg, nm, n_el, n_az, arm="accel")
        row = {"grid": f"{n_az}x{n_el}", "cells": n_az * n_el,
               "sensor": "noiseless",
               "polygons": len(r_on["polygons"]),
               "polygons_identical": poly_key(r_on["polygons"]) == poly_key(r_off["polygons"]),
               "onset_events": len(r_on["onset_stream"]),
               "onset_identical": r_on["onset_stream"] == r_off["onset_stream"],
               "rod_state_identical": state_equal(r_on, r_off),
               "input_epoch_identical": r_on["rod"]["input_epoch"] == r_off["rod"]["input_epoch"],
               "union_iou_on": r_on.get("union_iou"),
               "union_iou_off": r_off.get("union_iou"),
               "precision_on": r_on.get("carve_precision"),
               "score_identical": (r_on.get("union_iou") == r_off.get("union_iou")
                                   and r_on.get("carve_precision") == r_off.get("carve_precision")),
               "skipped_cell_ticks": int(sum(r_on["skipped"])),
               "skipped_fraction_final_tick": r_on["skipped"][-1] / (n_az * n_el),
               "graph_arm": None}
        if n_az * n_el <= 4800:
            r_gr = hold_carve_run(lumas, lg, nm, n_el, n_az, arm="graph")
            row["graph_arm"] = {
                "polygons_identical": poly_key(r_on["polygons"]) == poly_key(r_gr["polygons"]),
                "onset_identical": r_on["onset_stream"] == r_gr["onset_stream"],
                "rod_state_identical": state_equal(r_on, r_gr),
                "union_iou": r_gr.get("union_iou")}
        row["identical"] = bool(
            row["polygons_identical"] and row["onset_identical"]
            and row["rod_state_identical"] and row["input_epoch_identical"]
            and row["score_identical"]
            and (row["graph_arm"] is None
                 or (row["graph_arm"]["polygons_identical"]
                     and row["graph_arm"]["onset_identical"]
                     and row["graph_arm"]["rod_state_identical"])))
        ident.append(row)
        print(f"[C1 {row['grid']}] identical={row['identical']} "
              f"3way={row['graph_arm'] is not None} npoly={row['polygons']} "
              f"onsets={row['onset_events']} iou={row['union_iou_on']} "
              f"skipfinal={row['skipped_fraction_final_tick']:.3f}", flush=True)
    rep["C1_byte_identity_noiseless"] = ident

    # ---- C1d: the WRONG predicate must BREAK the identity ---------------------
    lg12, nm12 = labels_at(30, 40)
    r_on12 = hold_carve_run(lumas, lg12, nm12, 30, 40, arm="dirty")
    r_off12 = hold_carve_run(lumas, lg12, nm12, 30, 40, arm="accel")
    r_nv12 = hold_carve_run(lumas, lg12, nm12, 30, 40, arm="dirty", naive=True)
    rep["C1d_wrong_predicate_falsifier"] = {
        "grid": "40x30",
        "exact_matches_full_sweep": state_equal(r_on12, r_off12),
        "naive_matches_full_sweep": state_equal(r_nv12, r_off12),
        "naive_adaptation_identical": r_nv12["rod"]["adaptation"] == r_off12["rod"]["adaptation"],
        "naive_activation_identical": r_nv12["rod"]["activation"] == r_off12["rod"]["activation"],
        "naive_onset_identical": r_nv12["onset_stream"] == r_off12["onset_stream"],
        "naive_skipped_cell_ticks": int(sum(r_nv12["skipped"])),
        "exact_skipped_cell_ticks": int(sum(r_on12["skipped"])),
        "breaks": not state_equal(r_nv12, r_off12)}
    print(f"[C1d falsifier] naive breaks identity="
          f"{rep['C1d_wrong_predicate_falsifier']['breaks']} "
          f"(naive skips {rep['C1d_wrong_predicate_falsifier']['naive_skipped_cell_ticks']} "
          f"vs exact {rep['C1d_wrong_predicate_falsifier']['exact_skipped_cell_ticks']} cell-ticks)",
          flush=True)

    # ---- C1e: input_epoch — the one attribute a skip leaves stale -------------
    r_nostamp = hold_carve_run(lumas, None, None, 30, 40, arm="dirty", stamp=False)
    rep["C1e_input_epoch"] = {
        "stamp_on_identical": r_on12["rod"]["input_epoch"] == r_off12["rod"]["input_epoch"],
        "stamp_off_identical": r_nostamp["rod"]["input_epoch"] == r_off12["rod"]["input_epoch"],
        "stamp_off_other_state_identical": state_equal(r_nostamp, r_off12),
        "stamp_off_onset_identical": r_nostamp["onset_stream"] == r_off12["onset_stream"]}
    print(f"[C1e] input_epoch stamp ON identical="
          f"{rep['C1e_input_epoch']['stamp_on_identical']} / stamp OFF identical="
          f"{rep['C1e_input_epoch']['stamp_off_identical']} "
          f"(other state still identical={rep['C1e_input_epoch']['stamp_off_other_state_identical']})",
          flush=True)

    # ---- C1c: the LANDED 160x120 Doom carve, Poisson sensor, seed 182000 ------
    LANDED = {"n_polygons": 4, "union_iou": 0.1215, "carve_precision": 0.9784,
              "false_poly_rate": 0.0}
    lg160, nm160 = labels_at(120, 160)
    p_on = poisson_carve_run(lumas, lg160, nm160, 120, 160, arm="dirty")
    p_off = poisson_carve_run(lumas, lg160, nm160, 120, 160, arm="accel")
    tup = {"n_polygons": len(p_on["polygons"]), "union_iou": p_on.get("union_iou"),
           "carve_precision": p_on.get("carve_precision"),
           "false_poly_rate": p_on.get("false_poly_rate")}
    rep["C1c_landed_carve_dirty"] = {
        **tup,
        "matches_accel": (p_on["onset_stream"] == p_off["onset_stream"]
                          and poly_key(p_on["polygons"]) == poly_key(p_off["polygons"])
                          and state_equal(p_on, p_off)),
        "matches_landed": (tup["n_polygons"] == LANDED["n_polygons"]
                           and round(tup["union_iou"], 4) == LANDED["union_iou"]
                           and round(tup["carve_precision"], 4) == LANDED["carve_precision"]),
        "skipped_cell_ticks_under_poisson": int(sum(p_on["skipped"])),
        "cell_ticks": len(p_on["skipped"]) * 19200,
        "landed_reference": LANDED}
    print(f"[C1c landed 160x120 DIRTY] npoly={tup['n_polygons']} iou={tup['union_iou']} "
          f"prec={tup['carve_precision']} ==accel={rep['C1c_landed_carve_dirty']['matches_accel']} "
          f"==landed={rep['C1c_landed_carve_dirty']['matches_landed']} "
          f"skips={rep['C1c_landed_carve_dirty']['skipped_cell_ticks_under_poisson']}",
          flush=True)

    # ---- C2a: cost vs DIRTY COUNT at fixed 19200 cells ------------------------
    # The `input_epoch` STAMP (the exactness bookkeeping) is itself O(cells), so
    # both arms are measured: stamp ON = exact whole-graph identity; stamp OFF =
    # exact on every observable + persistent attr, with `input_epoch` left as the
    # rod's OWN per-sensor time.
    g160 = _grid(lumas[0], 120, 160)
    KS = [0, 1, 16, 64, 256, 1024, 4096, 19200]
    c2a = {"cells": 19200, "ks": KS}
    for stamp in (True, False):
        tag = "stamp_on" if stamp else "stamp_off"
        eye, sensor, _t, _s = settled_eye(120, 160, g160, stamp=stamp)
        costs = [cost_at_worklist(eye, sensor, g160, k) for k in KS]
        slope, icept, r2 = fit_affine(KS, costs)
        # A REAL perturbation: a 4x4 patch changes, nothing else does.
        g_p = g160.copy()
        g_p[10:14, 20:24] += 20.0
        patch = []
        for _ in range(5):
            dt_patch, k_patch = sensor.submit(eye, g_p)
            patch.append(dt_patch)
            sensor.submit(eye, g160)          # put it back
        c2a[tag] = {
            "per_tick_s": costs, "affine_slope_s_per_cell": slope,
            "affine_intercept_s": icept, "r2": r2,
            "cost_k16_over_k19200": costs[2] / costs[-1],
            "real_4x4_patch": {
                "reported_cells": int(k_patch),
                "per_tick_s": float(np.median(patch)),
                "vs_full_sweep_184000": float(np.median(patch)) / BASE_184000[19200]}}
        eye.stop()
        print(f"[C2a {tag}] " +
              " ".join(f"k={k}:{1000*c:.3f}ms" for k, c in zip(KS, costs)) +
              f"  R2={r2:.4f} k16/k19200={costs[2]/costs[-1]:.4f} "
              f"real 4x4 patch({int(k_patch)} cells)="
              f"{1000*np.median(patch):.3f}ms", flush=True)
    rep["C2a_cost_vs_dirty"] = c2a

    # ---- C2b: cost vs TOTAL CELLS at a FIXED dirty count of 16 ---------------
    c2b = {"exponent_184000": 1.072}
    for stamp in (True, False):
        tag = "stamp_on" if stamp else "stamp_off"
        fixed = []
        for (n_az, n_el) in SWEEP:
            g = _grid(lumas[0], n_el, n_az)
            e2, s2, _t2, _s2 = settled_eye(n_el, n_az, g, stamp=stamp)
            c16 = cost_at_worklist(e2, s2, g, 16)
            cfull = cost_at_worklist(e2, s2, g, n_az * n_el)
            fixed.append({"cells": n_az * n_el, "per_tick_dirty16_s": c16,
                          "per_tick_full_s": cfull})
            e2.stop()
            print(f"[C2b {tag}] cells={n_az*n_el} dirty16={1000*c16:.4f}ms "
                  f"fullwork={1000*cfull:.3f}ms", flush=True)
        exp16 = EA.fit_exponent([r["cells"] for r in fixed],
                                [r["per_tick_dirty16_s"] for r in fixed])
        expfull = EA.fit_exponent([r["cells"] for r in fixed],
                                  [r["per_tick_full_s"] for r in fixed])
        c2b[tag] = {"rows": fixed, "exponent_dirty16": round(float(exp16), 3),
                    "exponent_full_work": round(float(expfull), 3)}
        print(f"[C2b {tag}] exponent @fixed dirty 16 = {exp16:.3f} "
              f"(full work {expfull:.3f}; 184000 accel 1.072)", flush=True)
    rep["C2b_fixed_dirty_vs_cells"] = c2b

    # ---- C2c/C3: the DRAIN, and the adapted-scene fps ------------------------
    drain = {}
    for (n_az, n_el) in ((160, 120), (240, 180)):
        g = _grid(lumas[0], n_el, n_az)
        # the 184000 full-sweep arm on the SAME machine, same frames
        eye2 = build_eye(n_el, n_az, dirty=False)
        s2 = Sensor(0)
        t2 = [s2.submit_full(eye2, g)[0] for _ in range(12)]
        eye2.stop()
        full = float(np.median(t2[2:]))
        row = {"cells": n_az * n_el, "full_sweep_per_tick_s": full,
               "full_sweep_fps": 1.0 / full,
               "baseline_184000_per_tick_s": BASE_184000.get(n_az * n_el)}
        for stamp in (True, False):
            tag = "stamp_on" if stamp else "stamp_off"
            eye = build_eye(n_el, n_az, dirty=True, stamp=stamp)
            sensor = Sensor(0)
            ticks, skipped = [], []
            for _ in range(120):
                dt, _k = sensor.submit(eye, g)
                ticks.append(dt)
                skipped.append(eye._skip_log[-1] / float(n_az * n_el))
            eye.stop()
            adapted = float(np.median(ticks[-10:]))
            row[tag] = {
                "per_tick": ticks, "skipped_fraction": skipped,
                "adapted_per_tick_s": adapted, "adapted_fps": 1.0 / adapted,
                "tick3_per_tick_s": ticks[2],
                "drain_ratio_tick3_over_tick120": ticks[2] / adapted,
                "speedup_vs_full_sweep": full / adapted,
                "speedup_vs_184000": (BASE_184000[n_az * n_el] / adapted
                                      if n_az * n_el in BASE_184000 else None)}
            print(f"[C2c/C3 {n_az}x{n_el} {tag}] adapted per-tick="
                  f"{1000*adapted:.4f}ms ({row[tag]['adapted_fps']:.0f} fps) "
                  f"full sweep={1000*full:.2f}ms ({row['full_sweep_fps']:.1f} fps) "
                  f"speedup={row[tag]['speedup_vs_full_sweep']:.0f}x "
                  f"drain(t3/t120)={row[tag]['drain_ratio_tick3_over_tick120']:.0f}x",
                  flush=True)
        drain[f"{n_az}x{n_el}"] = row
    rep["C2c_C3_drain_and_fps"] = drain

    # ---- C3b: the REAL scene — adapted sheet, real Doom motion ---------------
    # The honest operating point: not a frozen frame (where the work list empties
    # and the cost collapses to the change-detect) but the adapted sheet watching
    # the 13 real motion frames, where only what MOVED is dirty.
    c3b = {}
    for arm in ("dirty", "accel"):
        r = hold_carve_run(lumas, None, None, 120, 160, arm=arm)
        motion_ticks = r["per_tick"][HOLD:]
        c3b[arm] = {"median_motion_per_tick_s": float(np.median(motion_ticks)),
                    "fps": 1.0 / float(np.median(motion_ticks)),
                    "median_dirty_cells": (float(np.median(r["reported"][HOLD:]))
                                           if arm == "dirty" else 19200.0),
                    "median_skipped": (float(np.median(r["skipped"][HOLD:]))
                                       if arm == "dirty" else 0.0)}
    c3b["speedup"] = (c3b["accel"]["median_motion_per_tick_s"]
                      / c3b["dirty"]["median_motion_per_tick_s"])
    c3b["speedup_vs_184000_published"] = (
        BASE_184000[19200] / c3b["dirty"]["median_motion_per_tick_s"])
    rep["C3b_real_motion_160x120"] = c3b
    print(f"[C3b real Doom motion @160x120] dirty="
          f"{1000*c3b['dirty']['median_motion_per_tick_s']:.3f}ms "
          f"({c3b['dirty']['fps']:.0f} fps, {c3b['dirty']['median_dirty_cells']:.0f} "
          f"dirty cells) vs full sweep "
          f"{1000*c3b['accel']['median_motion_per_tick_s']:.2f}ms "
          f"({c3b['accel']['fps']:.1f} fps) = {c3b['speedup']:.0f}x", flush=True)

    # ---- C4: FALSIFIER — full-field change must cost ~ the full sweep ---------
    fals = {}
    rng_f = np.random.default_rng(SEED + 1)
    frames = [rng_f.uniform(0, 255, size=(120, 160)) for _ in range(14)]
    for arm in ("dirty", "accel"):
        eye = build_eye(120, 160, dirty=(arm == "dirty"))
        sensor = Sensor(0)
        ts = []
        for f in frames:
            dt, _k = (sensor.submit(eye, f) if arm == "dirty"
                      else sensor.submit_full(eye, f))
            ts.append(dt)
        fals[f"noiseless_random_{arm}"] = float(np.median(ts[3:]))
        eye.stop()
    rng_p = np.random.default_rng(SEED + 2)
    for arm in ("dirty", "accel"):
        eye = build_eye(120, 160, dirty=(arm == "dirty"))
        sensor = Sensor(0)
        rng = np.random.default_rng(SEED + 2)
        ts = []
        for _ in range(14):
            dt, _k = (sensor.submit(eye, g160, rng) if arm == "dirty"
                      else sensor.submit_full(eye, g160, rng))
            ts.append(dt)
        fals[f"poisson_held_{arm}"] = float(np.median(ts[3:]))
        eye.stop()
    fals["ratio_noiseless_random"] = (fals["noiseless_random_dirty"]
                                      / fals["noiseless_random_accel"])
    fals["ratio_poisson_held"] = (fals["poisson_held_dirty"]
                                  / fals["poisson_held_accel"])
    fals["passes"] = bool(0.80 <= fals["ratio_noiseless_random"] <= 1.25
                          and 0.80 <= fals["ratio_poisson_held"] <= 1.25)
    rep["C4_full_field_falsifier"] = fals
    print(f"[C4] full-field random: dirty/accel = {fals['ratio_noiseless_random']:.3f}; "
          f"poisson held: {fals['ratio_poisson_held']:.3f}; passes={fals['passes']}",
          flush=True)

    # ---- C5: BRANCH B — the SHEDDING curve (semantic option, DEFAULT OFF) -----
    curve = []
    base = p_on            # the EXACT (Branch A) arm at 160x120, same protocol
    for delta in (0, 1, 2, 4, 8, 16, 32):
        r = poisson_carve_run(lumas, lg160, nm160, 120, 160, arm="dirty",
                              delta=delta, shed=True)
        a0 = np.array([float(x) for x in base["rod"]["adaptation"]])
        a1 = np.array([float(x) for x in r["rod"]["adaptation"]])
        dev = np.abs(a1 - a0)
        on0, on1 = set(base["onset_stream"]), set(r["onset_stream"])
        curve.append({
            "delta": delta,
            "skipped_fraction": float(np.mean(r["skipped"]) / 19200.0),
            "median_per_tick_s": float(np.median(r["per_tick"])),
            "fps": 1.0 / float(np.median(r["per_tick"])),
            "n_polygons": len(r["polygons"]),
            "union_iou": r.get("union_iou"), "carve_precision": r.get("carve_precision"),
            "false_poly_rate": r.get("false_poly_rate"),
            "onset_events": len(r["onset_stream"]),
            "onset_symmetric_diff": len(on0 ^ on1),
            "polygons_identical_to_exact": poly_key(r["polygons"]) == poly_key(base["polygons"]),
            "adaptation_max_dev": float(dev.max()),
            "adaptation_mean_dev": float(dev.mean()),
            "adaptation_identical": bool(dev.max() == 0.0)})
        c = curve[-1]
        print(f"[C5 delta={delta:2d}] skip={c['skipped_fraction']:.3f} "
              f"per_tick={1000*c['median_per_tick_s']:.2f}ms npoly={c['n_polygons']} "
              f"iou={c['union_iou']} prec={c['carve_precision']} "
              f"onsetdiff={c['onset_symmetric_diff']} "
              f"maxdev={c['adaptation_max_dev']:.4g}", flush=True)
    _probe = build_eye(15, 20)
    defaults = {"retina_dirty": bool(_probe._dirty_index),
                "retina_dirty_shed": bool(_probe._dirty_shed),
                "retina_dirty_naive": bool(_probe._dirty_naive)}
    _probe.stop()
    rep["C5_shedding_curve"] = {
        "adapter_defaults": defaults,
        "default_delta": 0, "default_dirty_index": defaults["retina_dirty"],
        "note": "BRANCH B is a SEMANTIC OPTION. No byte-identity is claimed for "
                "delta>0; the numbers below ARE the divergence.",
        "rows": curve,
        "first_delta_changing_landed_carve": next(
            (c["delta"] for c in curve
             if not c["polygons_identical_to_exact"]), None)}

    with open(os.path.join(RESULTS, "dirty_index.json"), "w") as fh:
        json.dump(rep, fh, indent=2)
    _plot(rep)
    print("source_match:", prov.get("source_match"))
    return rep


def _plot(rep):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    ax = axes[0]
    c2 = rep["C2a_cost_vs_dirty"]
    for tag, colour in (("stamp_on", "#1a9850"), ("stamp_off", "#4575b4")):
        ax.plot(c2["ks"], [1000 * x for x in c2[tag]["per_tick_s"]], "o-",
                color=colour,
                label=f"dirty-index {tag} (R²={c2[tag]['r2']:.4f})")
    ax.axhline(1000 * rep["baseline_184000_per_tick_s"][19200], color="#d73027",
               ls="--", label="184000 full sweep @19200")
    ax.set_xlabel("dirty cells (of 19200)")
    ax.set_ylabel("per-tick (ms)")
    ax.set_title("cost vs DIRTY COUNT — O(surprise)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[1]
    for tag, style in (("160x120", "o-"), ("240x180", "s-")):
        d = rep["C2c_C3_drain_and_fps"][tag]
        ax.semilogy(range(1, len(d["stamp_on"]["per_tick"]) + 1),
                    [1000 * x for x in d["stamp_on"]["per_tick"]], style, ms=3,
                    label=f"{tag} dirty-index")
        ax.axhline(1000 * d["full_sweep_per_tick_s"], ls="--", alpha=0.6,
                   label=f"{tag} full sweep")
    ax.set_xlabel("tick on a HELD scene")
    ax.set_ylabel("per-tick (ms, log)")
    ax.set_title("the DRAIN — cost falls as the scene grounds")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")

    ax = axes[2]
    rows = rep["C5_shedding_curve"]["rows"]
    ax.plot([r["delta"] for r in rows], [r["skipped_fraction"] for r in rows],
            "o-", color="#4575b4", label="skipped fraction")
    ax2 = ax.twinx()
    ax2.plot([r["delta"] for r in rows], [r["adaptation_max_dev"] for r in rows],
             "s--", color="#d73027", label="max |Δadaptation|")
    ax.set_xlabel("BRANCH B shed threshold δ (photon counts)")
    ax.set_ylabel("skipped fraction")
    ax2.set_ylabel("max |Δadaptation| vs exact")
    ax.set_title("BRANCH B: speed ↔ fidelity (DEFAULT OFF)")
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "dirty_index.png"), dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()
