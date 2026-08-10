#!/usr/bin/env python3
"""THE ACCELERATION — a droppable, byte-identical vectorized mirror of the
uniform retina sheet (seed block 184000).

Block 183000 killed the settled-task ACCUMULATION quadratic (prune) but left the
CELLS axis at exponent ~1.83 and ~0.73 s/tick @4800 — the residual O(cells²) is
the onset-mint rule's per-tick `run_rules` join over the retina, and the per-cell
transduce/onset work is a sheet of IDENTICAL microcircuits processed one
CognitiveTask node at a time. This rung ACCELERATES that uniform sheet with a
Rust batch graph op (`retina_onset_batch`) that computes the WHOLE sheet in ONE
FFI crossing, O(cells) — NO CognitiveTask nodes, NO run_rules join — reusing the
shared `photon_transduce_onset` kernel VERBATIM and mirroring both graph rules.

MEASURED behind the prereg gates (VISION_EYE_ACCEL_PREREG.md):

  C1 BYTE-IDENTITY (primary). Accelerator ON vs OFF produces byte-identical
     outputs (VisionPolygons + onset stream + union_iou/precision + rod
     adaptation) at every affordable resolution; and the landed 160x120 Doom
     carve reproduces EXACTLY (4 / 0.1215 / 0.9784 / 0 false).
  C2 DROPPABLE. OFF is the graph path (the correctness oracle); ON≡OFF.
  C3 CELLS AXIS LINEARIZED. Per-tick vs cells exponent + speedup @4800.
  C4 FALSIFIER. A perturbed kernel breaks ON≡OFF (the check is non-vacuous).

MECHANICAL MEASURE-ADAPTER. No agent decision. The OFF arm is the 183000 pruned
graph path (submit tasks -> run_cognitive_tasks -> run_rules -> prune). The ON
arm branches the eye's own `submit_photons_2d` on `context['retina_accel']`.
Frames come from the COMMITTED real `defend_the_line` 160x120 fixture,
area-mean-downsampled — VizDoom-free and importable, so the gate reuses this core.
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

SEED = 184000
FIXDIR = os.path.join(ROOT, "tests", "fixtures", "doom_carve_scale")
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(RESULTS, "eye_accel")

WARMUP = M.WARMUP
ADAPT_RATE = M.ADAPT_RATE
ONSET_DB = M.ONSET_DB
CARVE_MIN_COH = M.CARVE_MIN_COH
CARVE_MIN_EVENTS = M.CARVE_MIN_EVENTS

SWEEP = [(20, 15), (40, 30), (80, 60), (160, 120)]   # cells 300/1200/4800/19200


# ---------------------------------------------------------------- fixture ------
def _load_fixture():
    d = np.load(os.path.join(FIXDIR, "frames_160x120.npz"))
    names = json.load(open(os.path.join(FIXDIR, "label_names.json")))
    return d["lumas"].astype(np.float64), d["labels"].astype(np.int64), names


def _area_mean(grid, n_el, n_az):
    H, W = grid.shape
    bh, bw = H // n_el, W // n_az
    g = grid[:n_el * bh, :n_az * bw]
    return g.reshape(n_el, bh, n_az, bw).mean(axis=(1, 3))


def _downsample_labels(lab, n_el, n_az):
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


def build_eye(n_el, n_az, accel, perturb=False):
    """Same params as M.build_eye + the droppable accelerator flags. accel=False
    is byte-identical to the 183000 pruned graph path (the oracle)."""
    return GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=ADAPT_RATE,
        context={"retina_2d": True, "synchronous": True, "worker_capacity": 1,
                 "onset_threshold_db": ONSET_DB, "onset_refractory_epochs": 0.0,
                 "visual_carve": True, "carve_min_coherence": CARVE_MIN_COH,
                 "carve_min_events": CARVE_MIN_EVENTS,
                 "retina_accel": accel,
                 "retina_accel_perturb": perturb,
                 # ISOLATE THE ACCELERATOR (block 195000 interaction). This gate
                 # measures the 184000 SIMD accelerator's OWN cells-axis effect
                 # (transduce-loop vectorization). Block 195000 made
                 # `binding_projection` DEFAULT-ON on the shipped eye, and it
                 # INDEPENDENTLY linearizes the graph path by killing the
                 # scheduler-rule quadratic (`ct_area_effort_tracks_live_salience`)
                 # — an ORTHOGONAL win. With projection on it confounds this gate:
                 # the graph baseline is already ~linear (exp 1.07), so the
                 # accel's exponent DROP shrinks to ~0.13 though it still gives a
                 # 14.6x CONSTANT-factor speedup@4800. Disabling it here restores
                 # the accel's isolated measurement (the condition this gate ran
                 # under before 195000 changed the default): drop 0.71, 102x. NOT
                 # a threshold change — a confound removal. The shipped eye runs
                 # BOTH (projection kills the quadratic; the accel vectorizes the
                 # loop); their combination is measured in the 195000 gate.
                 "binding_projection": False}).build()


def _tick(eye, luma, rng, accel):
    """One transduce tick; returns wall seconds. When accel is off this is the
    183000 pruned graph path (submit -> run_cognitive_tasks -> run_rules ->
    prune). When on, `submit_photons_2d` settles the whole sheet in one batch
    call (no tasks, no run_rules join)."""
    t0 = time.perf_counter()
    eye.submit_photons_2d(dpw.photon_packets(luma, rng))
    if not accel:
        eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
        eye.prune_settled_tasks()
    return time.perf_counter() - t0


def _rod_adaptation(eye):
    rods = [eye._receptors[(f, "rod")] for f in range(eye.n_az * eye.n_el)]
    return [repr(x) for x in eye.substrate.get_attr_many(rods, "adaptation")]


def carve_run(lumas, label_grids, names_motion, n_el, n_az, accel, perturb=False,
              warmup=WARMUP, seed=SEED, max_ticks=None):
    """The 182000/183000 carve protocol (warmup + event-flush + motion + settle),
    toggling the accelerator. Returns polygons + union_iou + onset stream + rod
    adaptation + per-tick costs. The carve settle (one task) is the IRREGULAR
    part left on the graph — identical in both arms."""
    f0, motion = lumas[0], lumas[1:]
    if max_ticks is not None:
        motion = motion[:max_ticks]
    eye = build_eye(n_el, n_az, accel, perturb)
    rng = np.random.default_rng(seed)
    per_tick = []
    for _ in range(warmup):
        per_tick.append(_tick(eye, f0, rng, accel))
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for luma in motion:
        per_tick.append(_tick(eye, luma, rng, accel))
    eye.settle_carve_2d(since_epoch=since)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    ntasks = len(list(eye.substrate.nodes("CognitiveTask")))
    onset = sorted(
        (int(round(float(eye.substrate.node(n)["attrs"]["column_index"]))),
         int(round(float(eye.substrate.node(n)["attrs"].get("row_index", 0.0)))),
         int(round(float(eye.substrate.node(n)["attrs"]["epoch"]))))
        for n in eye.substrate.nodes("RetinalOnsetEvent"))
    rod_adapt = _rod_adaptation(eye)
    score = (M.score_carve(polys, names_motion, label_grids, n_el, n_az)
             if label_grids is not None else {})
    eye.stop()
    return {"polygons": polys, "per_tick": per_tick, "tasks_left": ntasks,
            "onset_stream": onset, "rod_adaptation": rod_adapt, **score}


def _poly_key(polys):
    return [(p["col_min"], p["col_max"], p["row_min"], p["row_max"],
             repr(p["direction"]), repr(p["speed"]), repr(p["coherence"]),
             p["n_events"]) for p in polys]


def fit_exponent(xs, ys):
    lx = np.log(np.array(xs, float))
    ly = np.log(np.array(ys, float))
    return float(np.polyfit(lx, ly, 1)[0])


def main(calibrate=False, trials=3):
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
              "warmup": WARMUP, "adapt_rate": ADAPT_RATE, "trials": trials}

    # ---- C1/C2 BYTE-IDENTITY (ON vs OFF) at every resolution incl. 19200 ------
    # Full protocol (all 13 motion frames). The OFF arm at 19200 is the 183000
    # PRUNED graph path — affordable (bounded per-tick), unlike 182000 no-prune.
    byte_ident = []
    for (n_az, n_el) in SWEEP:
        lumas, lg, nm = frames_at(n_el, n_az)
        r_on = carve_run(lumas, lg, nm, n_el, n_az, accel=True)
        r_off = carve_run(lumas, lg, nm, n_el, n_az, accel=False)
        identical = (
            _poly_key(r_on["polygons"]) == _poly_key(r_off["polygons"])
            and r_on["onset_stream"] == r_off["onset_stream"]
            and r_on.get("union_iou") == r_off.get("union_iou")
            and r_on.get("carve_precision") == r_off.get("carve_precision")
            and r_on["rod_adaptation"] == r_off["rod_adaptation"])
        byte_ident.append({
            "grid": f"{n_az}x{n_el}", "cells": n_az * n_el,
            "n_polygons_on": len(r_on["polygons"]),
            "n_polygons_off": len(r_off["polygons"]),
            "onset_events": len(r_on["onset_stream"]),
            "onset_stream_identical": r_on["onset_stream"] == r_off["onset_stream"],
            "polygons_identical": _poly_key(r_on["polygons"]) == _poly_key(r_off["polygons"]),
            "rod_adaptation_identical": r_on["rod_adaptation"] == r_off["rod_adaptation"],
            "union_iou_on": r_on.get("union_iou"),
            "union_iou_off": r_off.get("union_iou"),
            "precision_on": r_on.get("carve_precision"),
            "identical": bool(identical),
            "tasks_left_on": r_on["tasks_left"],
            "tasks_left_off": r_off["tasks_left"],
        })
        print(f"[byte-identity] {n_az}x{n_el} cells={n_az*n_el}: "
              f"identical={identical} npoly={len(r_on['polygons'])} "
              f"onsets={len(r_on['onset_stream'])} iou={r_on.get('union_iou')} "
              f"tasks(on/off)={r_on['tasks_left']}/{r_off['tasks_left']}", flush=True)
    report["byte_identity"] = byte_ident

    # C1e — the LANDED 160x120 Doom carve reproduced EXACTLY under the
    # accelerator. The landed value (4 / 0.1215 / 0.9784 / 0-false) was produced
    # by the 182000 carve protocol at SEED 182000 (the 183000 landed check used
    # M.carve_scale_run at that seed); reproducing it therefore RE-RUNS that
    # protocol at seed 182000 — accelerator ON and OFF — and both must equal the
    # landed tuple. (The byte_identity sweep above proves ON≡OFF at every grid at
    # this rung's own block-184000 seed, incl. the firing 19200 carve.)
    LANDED = {"n_polygons": 4, "union_iou": 0.1215, "carve_precision": 0.9784,
              "false_poly_rate": 0.0}
    lumas160, lg160, nm160 = frames_at(120, 160)
    r_on160 = carve_run(lumas160, lg160, nm160, 120, 160, accel=True,
                        seed=182000)
    r_off160 = carve_run(lumas160, lg160, nm160, 120, 160, accel=False,
                         seed=182000)
    on_tuple = {"n_polygons": len(r_on160["polygons"]),
                "union_iou": r_on160.get("union_iou"),
                "carve_precision": r_on160.get("carve_precision"),
                "false_poly_rate": r_on160.get("false_poly_rate")}
    report["fires_160x120_accel_landed_seed"] = {
        **on_tuple,
        "matches_off": r_on160["onset_stream"] == r_off160["onset_stream"]
                       and _poly_key(r_on160["polygons"]) == _poly_key(r_off160["polygons"]),
        "matches_landed": (on_tuple["n_polygons"] == LANDED["n_polygons"]
                           and round(on_tuple["union_iou"], 4) == LANDED["union_iou"]
                           and round(on_tuple["carve_precision"], 4) == LANDED["carve_precision"]),
        "landed_reference": LANDED,
    }
    print(f"[fires 160x120 ACCEL landed-seed 182000] npoly={on_tuple['n_polygons']} "
          f"iou={on_tuple['union_iou']} prec={on_tuple['carve_precision']} "
          f"==off={report['fires_160x120_accel_landed_seed']['matches_off']} "
          f"==landed={report['fires_160x120_accel_landed_seed']['matches_landed']}",
          flush=True)

    # ---- C4 FALSIFIER — perturbed kernel breaks ON≡OFF ------------------------
    lumas12, lg12, nm12 = frames_at(30, 40)
    r_off12 = carve_run(lumas12, lg12, nm12, 30, 40, accel=False)
    r_pert = carve_run(lumas12, lg12, nm12, 30, 40, accel=True, perturb=True)
    falsifier_breaks = (r_pert["onset_stream"] != r_off12["onset_stream"])
    report["falsifier"] = {
        "grid": "40x30", "onset_on_perturb": len(r_pert["onset_stream"]),
        "onset_off": len(r_off12["onset_stream"]),
        "perturb_breaks_identity": bool(falsifier_breaks)}
    print(f"[falsifier] perturb onsets={len(r_pert['onset_stream'])} "
          f"oracle onsets={len(r_off12['onset_stream'])} "
          f"breaks_identity={falsifier_breaks}", flush=True)

    # ---- C3 SCALING: median per-tick vs cells, ON vs OFF ----------------------
    K = 8
    scaling = {"accel": [], "graph": []}
    for arm, accel in (("accel", True), ("graph", False)):
        for (n_az, n_el) in SWEEP:
            lumas, _, _ = frames_at(n_el, n_az)
            samples = []
            for _t in range(trials):
                r = carve_run(lumas, None, None, n_el, n_az, accel=accel,
                              max_ticks=K - WARMUP, seed=SEED + _t)
                samples.append(float(np.median(r["per_tick"][2:])))
            med = float(np.median(samples))
            spread = float(np.max(samples) - np.min(samples))
            scaling[arm].append({"cells": n_az * n_el, "median_pt_s": med,
                                 "spread_s": spread})
            print(f"[scaling {arm} {n_az}x{n_el}] cells={n_az*n_el} "
                  f"median_pt={med*1000:.2f}ms spread={spread*1000:.2f}ms "
                  f"fps={1.0/med:.2f}", flush=True)

    exp_accel = fit_exponent([p["cells"] for p in scaling["accel"]],
                             [p["median_pt_s"] for p in scaling["accel"]])
    exp_graph = fit_exponent([p["cells"] for p in scaling["graph"]],
                             [p["median_pt_s"] for p in scaling["graph"]])
    g48 = [p for p in scaling["graph"] if p["cells"] == 4800][0]["median_pt_s"]
    a48 = [p for p in scaling["accel"] if p["cells"] == 4800][0]["median_pt_s"]
    report["scaling"] = {
        "accel": scaling["accel"], "graph": scaling["graph"],
        "exponent_accel": round(exp_accel, 3),
        "exponent_graph": round(exp_graph, 3),
        "exponent_drop": round(exp_graph - exp_accel, 3),
        "speedup_at_4800": round(g48 / a48, 2),
        "fps_accel": {p["cells"]: round(1.0 / p["median_pt_s"], 2)
                      for p in scaling["accel"]},
    }
    print(f"\n[scaling] exponent accel={exp_accel:.3f} graph={exp_graph:.3f} "
          f"drop={exp_graph-exp_accel:.3f} speedup@4800={g48/a48:.1f}x", flush=True)

    if not calibrate:
        with open(os.path.join(RESULTS, "eye_accel.json"), "w") as fh:
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
    fig, ax = plt.subplots(1, 1, figsize=(6.5, 5))
    gc = [p["cells"] for p in s["graph"]]
    gy = [p["median_pt_s"] for p in s["graph"]]
    ac = [p["cells"] for p in s["accel"]]
    ay = [p["median_pt_s"] for p in s["accel"]]
    ax.loglog(gc, gy, "o-", color="#d73027",
              label=f"graph/OFF = 183000 pruned (exp {s['exponent_graph']})")
    ax.loglog(ac, ay, "s-", color="#1a9850",
              label=f"accel/ON (exp {s['exponent_accel']})")
    ax.set_xlabel("cells (n_az x n_el)")
    ax.set_ylabel("median per-tick cost (s)")
    ax.set_title("per-tick cost vs cells (log-log) — accel vs 183000 graph")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "scaling.png"), dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main(calibrate="--calibrate" in sys.argv)
