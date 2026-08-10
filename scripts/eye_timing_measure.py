#!/usr/bin/env python3
"""KILL THE QUADRATIC — measure the settled-task-prune fix (seed block 183000).

Block 182000 diagnosed WHY the 2-D photon eye is slow at scale: per-cell
`photon_transduce_onset` CognitiveTask nodes accumulate UN-PRUNED, so every
`run_rules` call re-examines them (the onset rule joins retina->column->rod->
has_task->task) and per-tick cost grows quadratically over the run. The fix is
the eye's OWN `GraphEye.prune_settled_tasks()` (block 183000): clear the
terminal-status retina tasks each tick, so per-tick cost stays flat.

This script MEASURES the fix behind the two prereg gates
(VISION_EYE_TIMING_PREREG.md):

  A. BYTE-IDENTITY (primary). The full common-fate carve protocol run WITH the
     prune vs WITHOUT it produces byte-identical outputs (same VisionPolygons,
     same union carve-vs-labels IoU to full precision) at every affordable
     resolution, and the 160x120 WITH-prune run reproduces the LANDED 182000
     carve (4 polygons, union_iou 0.1215, precision 0.978).

  B. QUADRATIC -> LINEAR. Per-tick cost is measured across the resolution sweep
     and across tick-index; the fitted scaling exponents show the accumulation
     is quadratic without the prune and linear with it, plus a representative
     absolute speedup at 4800 cells.

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term, no new seed.
Frames come from the COMMITTED real `defend_the_line` 160x120 fixture
(`tests/fixtures/doom_carve_scale/`), area-mean-downsampled to each sweep
resolution — VizDoom-free and importable, so the gate reuses this core.
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

SEED = 183000
FIXDIR = os.path.join(ROOT, "tests", "fixtures", "doom_carve_scale")
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(RESULTS, "eye_timing")

WARMUP = M.WARMUP            # 6 — reuse the 182000 protocol exactly
ADAPT_RATE = M.ADAPT_RATE    # 0.4
ONSET_DB = M.ONSET_DB        # 6.0
CARVE_MIN_COH = M.CARVE_MIN_COH
CARVE_MIN_EVENTS = M.CARVE_MIN_EVENTS

# Sweep: cols x rows = n_az x n_el. 4:3 landscape, exact area-mean downsamples of
# the committed 160x120 fixture. cells = 300 / 1200 / 4800 / 19200.
SWEEP = [(20, 15), (40, 30), (80, 60), (160, 120)]
FIRES_RES = (160, 120)


# ---------------------------------------------------------------- fixture ------
def _load_fixture():
    d = np.load(os.path.join(FIXDIR, "frames_160x120.npz"))
    names = json.load(open(os.path.join(FIXDIR, "label_names.json")))
    return d["lumas"].astype(np.float64), d["labels"].astype(np.int64), names


def _area_mean(grid, n_el, n_az):
    """Area-mean downsample a (H,W) grid to (n_el,n_az) (H,W multiples of the
    target). Mechanical resample — no decision."""
    H, W = grid.shape
    bh, bw = H // n_el, W // n_az
    g = grid[:n_el * bh, :n_az * bw]
    return g.reshape(n_el, bh, n_az, bw).mean(axis=(1, 3))


def _downsample_labels(lab, n_el, n_az):
    """Per-pixel label mask -> per-cell MODAL label grid (mirror of
    M.downsample_labels, on the fixture's 160x120 masks)."""
    H, W = lab.shape
    bh, bw = H // n_el, W // n_az
    out = np.zeros((n_el, n_az), dtype=np.int64)
    lab = lab[:n_el * bh, :n_az * bw]
    for r in range(n_el):
        for c in range(n_az):
            block = lab[r * bh:(r + 1) * bh, c * bw:(c + 1) * bw].reshape(-1)
            vals, cnts = np.unique(block, return_counts=True)
            order = np.lexsort((vals, -cnts))
            out[r, c] = int(vals[order[0]])
    return out


def build_eye(n_el, n_az):
    return GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=ADAPT_RATE,
        context={"retina_2d": True, "synchronous": True, "worker_capacity": 1,
                 "onset_threshold_db": ONSET_DB, "onset_refractory_epochs": 0.0,
                 "visual_carve": True, "carve_min_coherence": CARVE_MIN_COH,
                 "carve_min_events": CARVE_MIN_EVENTS}).build()


def _tick(eye, luma, rng, do_prune):
    """One transduce tick; returns wall seconds for the tick. `do_prune` toggles
    the eye's OWN settled-task prune (the fix)."""
    t0 = time.perf_counter()
    eye.submit_photons_2d(dpw.photon_packets(luma, rng))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    if do_prune:
        eye.prune_settled_tasks()
    return time.perf_counter() - t0


# =====================================================================
#  A — BYTE-IDENTITY: full carve protocol, prune vs no-prune
# =====================================================================
def carve_run(lumas, label_grids, names_motion, n_el, n_az, do_prune,
              warmup=WARMUP, seed=SEED, max_ticks=None):
    """Run the 182000 carve protocol (warmup + event-flush + motion + settle),
    toggling the prune. Returns polygons + union_iou + per-tick costs. When
    `max_ticks` limits the motion window the carve is not scored (timing-only)."""
    f0, motion = lumas[0], lumas[1:]
    if max_ticks is not None:
        motion = motion[:max_ticks]
    eye = build_eye(n_el, n_az)
    rng = np.random.default_rng(seed)
    per_tick = []
    for _ in range(warmup):
        per_tick.append(_tick(eye, f0, rng, do_prune))
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for luma in motion:
        per_tick.append(_tick(eye, luma, rng, do_prune))
    eye.settle_carve_2d(since_epoch=since)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    ntasks = len(list(eye.substrate.nodes("CognitiveTask")))
    # The onset-event stream — the async percept the carve reads. Byte-identity
    # of THIS across prune/no-prune proves the prune changes nothing the eye
    # computes, even at resolutions where 0 polygons fire.
    onset = sorted(
        (int(round(float(eye.substrate.node(n)["attrs"]["column_index"]))),
         int(round(float(eye.substrate.node(n)["attrs"].get("row_index", 0.0)))),
         int(round(float(eye.substrate.node(n)["attrs"]["epoch"]))))
        for n in eye.substrate.nodes("RetinalOnsetEvent"))
    score = (M.score_carve(polys, names_motion, label_grids, n_el, n_az)
             if label_grids is not None else {})
    eye.stop()
    return {"polygons": polys, "per_tick": per_tick, "tasks_left": ntasks,
            "onset_stream": onset, **score}


def _poly_key(polys):
    """Canonical byte-identity key for a polygon set (the load-bearing spans +
    the recovered common-fate params, full precision)."""
    return [(p["col_min"], p["col_max"], p["row_min"], p["row_max"],
             repr(p["direction"]), repr(p["speed"]), repr(p["coherence"]),
             p["n_events"]) for p in polys]


# =====================================================================
#  B — SCALING: per-tick cost vs cells + vs tick-index
# =====================================================================
def fit_exponent(xs, ys):
    lx = np.log(np.array(xs, float))
    ly = np.log(np.array(ys, float))
    return float(np.polyfit(lx, ly, 1)[0])


def accumulation_run(lumas, n_el, n_az, n_ticks, do_prune, seed=SEED):
    """Per-tick cost vs tick-index at fixed resolution — the accumulation
    signature. Cycles the real motion frames so every tick fires real onsets."""
    motion = lumas[1:]
    eye = build_eye(n_el, n_az)
    rng = np.random.default_rng(seed)
    per_tick = []
    for t in range(n_ticks):
        per_tick.append(_tick(eye, motion[t % len(motion)], rng, do_prune))
    ntasks = len(list(eye.substrate.nodes("CognitiveTask")))
    eye.stop()
    return per_tick, ntasks


def main(calibrate=False):
    os.makedirs(OUTDIR, exist_ok=True)
    from domains.engine_provenance import provenance_stamp
    prov = provenance_stamp(strict=False)
    lumas_full, labels_full, names = _load_fixture()

    def frames_at(n_el, n_az):
        lumas = [_area_mean(lumas_full[i], n_el, n_az)
                 for i in range(lumas_full.shape[0])]
        label_grids = [_downsample_labels(labels_full[i], n_el, n_az)
                       for i in range(1, labels_full.shape[0])]
        names_motion = [names[i] for i in range(1, labels_full.shape[0])]
        return lumas, label_grids, names_motion

    report = {"block": SEED, "engine_source_match": prov.get("source_match"),
              "warmup": WARMUP, "adapt_rate": ADAPT_RATE}

    # ---- A. BYTE-IDENTITY (prune vs no-prune) at affordable resolutions -------
    # Full protocol (all 13 motion frames) where no-prune is cheap (300/1200);
    # capped motion at 4800 (no-prune full protocol IS the quadratic being
    # killed). Identity of polygons + onset stream holds regardless of motion
    # length, so a capped 4800 arm still proves the prune changes nothing there.
    byte_ident = []
    BI_RES = [(20, 15, None), (40, 30, None), (80, 60, 4)]
    for (n_az, n_el, cap) in BI_RES:
        lumas, lg, nm = frames_at(n_el, n_az)
        r_prune = carve_run(lumas, lg, nm, n_el, n_az, do_prune=True,
                            max_ticks=cap)
        r_noprune = carve_run(lumas, lg, nm, n_el, n_az, do_prune=False,
                              max_ticks=cap)
        identical = (
            _poly_key(r_prune["polygons"]) == _poly_key(r_noprune["polygons"])
            and r_prune["onset_stream"] == r_noprune["onset_stream"]
            and r_prune.get("union_iou") == r_noprune.get("union_iou")
            and r_prune.get("carve_precision")
                == r_noprune.get("carve_precision"))
        byte_ident.append({
            "grid": f"{n_az}x{n_el}", "cells": n_az * n_el,
            "motion_cap": cap,
            "n_polygons_prune": len(r_prune["polygons"]),
            "n_polygons_noprune": len(r_noprune["polygons"]),
            "onset_events": len(r_prune["onset_stream"]),
            "onset_stream_identical":
                r_prune["onset_stream"] == r_noprune["onset_stream"],
            "union_iou_prune": r_prune.get("union_iou"),
            "union_iou_noprune": r_noprune.get("union_iou"),
            "precision_prune": r_prune.get("carve_precision"),
            "identical": bool(identical),
            "tasks_left_prune": r_prune["tasks_left"],
            "tasks_left_noprune": r_noprune["tasks_left"],
        })
        print(f"[byte-identity] {n_az}x{n_el} cap={cap}: identical={identical} "
              f"npoly={len(r_prune['polygons'])} onsets={len(r_prune['onset_stream'])} "
              f"iou={r_prune.get('union_iou')} tasks(prune/noprune)="
              f"{r_prune['tasks_left']}/{r_noprune['tasks_left']}", flush=True)
    report["byte_identity"] = byte_ident

    # 160x120 reproduces the LANDED 182000 carve via the 182000 HARNESS itself
    # (M.carve_scale_run, seed 182000) — now that its per-tick prune delegates to
    # the eye's own prune_settled_tasks (block 183000), this confirms the wiring
    # is byte-identical to the pre-change landed result (4 polys, union_iou
    # 0.1215, precision 0.978). NB: the committed fixture stores luma as float32,
    # so a hair of the last-place Poisson noise may shift vs the float64 capture;
    # the exact reproduced value is recorded here as a fact.
    lumas160 = [_area_mean(lumas_full[i], 120, 160)
                for i in range(lumas_full.shape[0])]
    lg160 = [_downsample_labels(labels_full[i], 120, 160)
             for i in range(1, labels_full.shape[0])]
    nm160 = [names[i] for i in range(1, labels_full.shape[0])]
    r_land = M.carve_scale_run(lumas160, lg160, nm160, 120, 160)
    report["fires_160x120_landed_harness"] = {
        "n_polygons": r_land["n_polygons"],
        "union_iou": r_land["union_iou"],
        "carve_precision": r_land["carve_precision"],
        "carve_recall": r_land["carve_recall"],
        "false_poly_rate": r_land["false_poly_rate"],
    }
    print(f"[fires 160x120 landed-harness] npoly={r_land['n_polygons']} "
          f"iou={r_land['union_iou']} prec={r_land['carve_precision']} "
          f"false_rate={r_land['false_poly_rate']}", flush=True)

    # ---- B1. ACCUMULATION: per-tick vs tick-index @ 4800 cells ----------------
    N_ACC = 8
    lumas48, _, _ = frames_at(60, 80)
    acc = {}
    for lab, dp in (("noprune", False), ("prune", True)):
        pt, nt = accumulation_run(lumas48, 60, 80, N_ACC, dp)
        idx = list(range(1, len(pt) + 1))
        acc[lab] = {
            "per_tick_s": [round(x, 4) for x in pt],
            "tasks_left": nt,
            "last_over_first": round(pt[-1] / pt[0], 3),
            # slope of log(per-tick) vs log(tick-index): ~1 climbing, ~0 flat.
            "index_slope": round(fit_exponent(idx, pt), 3),
            # cumulative-cost-vs-ticks exponent: quadratic(~2) vs linear(~1).
            "cumulative_exponent": round(
                fit_exponent(idx, np.cumsum(pt)), 3),
        }
        print(f"[accumulation@4800 {lab}] per_tick={acc[lab]['per_tick_s']} "
              f"index_slope={acc[lab]['index_slope']} "
              f"cumexp={acc[lab]['cumulative_exponent']} "
              f"last/first={acc[lab]['last_over_first']} tasks_left={nt}",
              flush=True)
    report["accumulation_4800"] = acc

    # ---- B2. SCALING: per-tick cost vs cells ----------------------------------
    # Mean steady-state per-tick over the carve protocol's transduce loop. No-prune
    # is affordable to 4800; the pruned arm runs the full sweep incl. 19200.
    K = 8   # timing ticks per resolution (warmup path, real f0 then motion)
    scaling = {"noprune": [], "prune": []}
    for (n_az, n_el) in SWEEP:
        lumas, _, _ = frames_at(n_el, n_az)
        # prune arm — full sweep
        r = carve_run(lumas, None, None, n_el, n_az, do_prune=True,
                      max_ticks=K - WARMUP)
        mean_pt = float(np.mean(r["per_tick"][2:]))
        scaling["prune"].append({"cells": n_az * n_el, "mean_pt_s": mean_pt,
                                 "tasks_left": r["tasks_left"]})
        print(f"[scaling prune {n_az}x{n_el}] cells={n_az*n_el} "
              f"mean_pt={mean_pt*1000:.1f}ms tasks_left={r['tasks_left']}",
              flush=True)
    for (n_az, n_el) in SWEEP:
        if n_az * n_el > 4800:
            continue  # no-prune at 19200 is prohibitive (the quadratic itself)
        lumas, _, _ = frames_at(n_el, n_az)
        r = carve_run(lumas, None, None, n_el, n_az, do_prune=False,
                      max_ticks=K - WARMUP)
        mean_pt = float(np.mean(r["per_tick"][2:]))
        scaling["noprune"].append({"cells": n_az * n_el, "mean_pt_s": mean_pt,
                                   "tasks_left": r["tasks_left"]})
        print(f"[scaling noprune {n_az}x{n_el}] cells={n_az*n_el} "
              f"mean_pt={mean_pt*1000:.1f}ms tasks_left={r['tasks_left']}",
              flush=True)

    np_pts = scaling["noprune"]
    pr_pts = [p for p in scaling["prune"] if p["cells"] <= 4800]
    exp_noprune = fit_exponent([p["cells"] for p in np_pts],
                               [p["mean_pt_s"] for p in np_pts])
    exp_prune_lo = fit_exponent([p["cells"] for p in pr_pts],
                                [p["mean_pt_s"] for p in pr_pts])
    exp_prune_all = fit_exponent([p["cells"] for p in scaling["prune"]],
                                 [p["mean_pt_s"] for p in scaling["prune"]])
    sp48 = (np_pts[-1]["mean_pt_s"] / pr_pts[-1]["mean_pt_s"])
    report["scaling"] = {
        "noprune": np_pts, "prune": scaling["prune"],
        "exponent_noprune": round(exp_noprune, 3),
        "exponent_prune_le4800": round(exp_prune_lo, 3),
        "exponent_prune_full": round(exp_prune_all, 3),
        "speedup_at_4800": round(sp48, 2),
    }
    print(f"\n[scaling] exponent noprune={exp_noprune:.3f} "
          f"prune(<=4800)={exp_prune_lo:.3f} prune(full)={exp_prune_all:.3f} "
          f"speedup@4800={sp48:.1f}x", flush=True)

    # ---- 240x180 (43200 cells) COMPLETION check, pruned only. The mission
    # notes no-prune 240x180 did not finish in 30 min. With the prune each tick
    # is bounded, so a full run COMPLETES (slow — the O(C^2) event-scan residual).
    # A few pruned ticks confirm boundedness without a 15-min full run.
    # Nearest-neighbour UPSAMPLE the fixture frames to 240x180 (timing-only, no
    # labels): the fixture is 160x120 so it cannot be area-mean upsampled, and
    # the O(cells^2) cost this probes does not depend on the exact content.
    def _upsample(grid, n_el, n_az):
        H, W = grid.shape
        ri = (np.arange(n_el) * H // n_el).clip(0, H - 1)
        ci = (np.arange(n_az) * W // n_az).clip(0, W - 1)
        return grid[np.ix_(ri, ci)]
    lumas240 = [_upsample(lumas_full[i], 180, 240)
                for i in range(lumas_full.shape[0])]
    eye = build_eye(180, 240)
    rng = np.random.default_rng(SEED)
    comp = []
    for t in range(3):
        comp.append(_tick(eye, lumas240[t % len(lumas240)], rng, True))
    eye.stop()
    report["completion_240x180_prune"] = {
        "cells": 43200, "per_tick_s": [round(x, 3) for x in comp],
        "bounded": all(x < 300 for x in comp), "n_ticks_probed": len(comp)}
    print(f"[completion 240x180 prune] per_tick={[round(x,2) for x in comp]}s "
          f"bounded={report['completion_240x180_prune']['bounded']}", flush=True)

    if not calibrate:
        with open(os.path.join(RESULTS, "eye_timing.json"), "w") as fh:
            json.dump(report, fh, indent=2)
        _plot(report)
    print("source_match:", prov.get("source_match"))
    return report


def _plot(report):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return
    s = report["scaling"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    npc = [p["cells"] for p in s["noprune"]]
    npy = [p["mean_pt_s"] for p in s["noprune"]]
    prc = [p["cells"] for p in s["prune"]]
    pry = [p["mean_pt_s"] for p in s["prune"]]
    ax1.loglog(npc, npy, "o-", color="#d73027",
               label=f"no prune (exp {s['exponent_noprune']})")
    ax1.loglog(prc, pry, "s-", color="#1a9850",
               label=f"prune (exp {s['exponent_prune_full']})")
    ax1.set_xlabel("cells (n_az x n_el)")
    ax1.set_ylabel("mean per-tick cost (s)")
    ax1.set_title("per-tick cost vs cells (log-log)")
    ax1.legend(); ax1.grid(True, which="both", alpha=0.3)
    acc = report["accumulation_4800"]
    xs = list(range(1, len(acc["noprune"]["per_tick_s"]) + 1))
    ax2.plot(xs, acc["noprune"]["per_tick_s"], "o-", color="#d73027",
             label=f"no prune (cum exp {acc['noprune']['cumulative_exponent']})")
    ax2.plot(xs, acc["prune"]["per_tick_s"], "s-", color="#1a9850",
             label=f"prune (cum exp {acc['prune']['cumulative_exponent']})")
    ax2.set_xlabel("tick index @ 4800 cells")
    ax2.set_ylabel("per-tick cost (s)")
    ax2.set_title("accumulation: per-tick cost vs tick index")
    ax2.legend(); ax2.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "scaling.png"), dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main(calibrate="--calibrate" in sys.argv)
