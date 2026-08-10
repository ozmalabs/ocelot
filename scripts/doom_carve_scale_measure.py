#!/usr/bin/env python3
"""SCALE THE DOOM RETINA + MAKE THE CARVE FIRE — measure (seed block 182000-182999).

Block 181000 put the photon eye on real VizDoom and the eye BUILT structure, but
its 2-D common-fate CARVE produced ZERO VisionPolygons at 15x20 — RESOLUTION-
LIMITED (sub-grid objects), the same sub-grid wall the old RGB arc found. This
rung SCALES the az x el retina resolution and gets the eye's OWN async
common-fate carve to actually produce objects, SCORED against VizDoom's labels
buffer (ORACLE ONLY, never fed to the eye).

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term, no new seed.
It feeds real VizDoom frames as per-receptor Poisson PHOTON FLUX into the
event-native 2-D photon eye (blocks 164/171-180: transduce -> onset events ->
`retinal_common_fate_carve_2d`), and reads out the eye's OWN VisionPolygons.

THE DIFFERENTIAL-MOTION CONDITION (disclosed, prereg): the common-fate carve
needs a genuinely INDEPENDENTLY-MOVING object. Pure egomotion (turning) sweeps
the WHOLE field coherently -> one blob covering everything, which the current
spatial-connectivity carve cannot velocity-split (a named follow-on). So the
scene is `defend_the_line` with a STILL camera (noop) and laterally-moving
monsters (Demon/DoomImp) -- the same moving-enemy regime the old RGB ~0.24
baseline used. Full egomotion compensation is a SEPARATE frontier, not this rung.

THE FEED (prereg): hold f0 for W warmup ticks so the eye's receptors ADAPT to
the static background (it goes silent); then feed the M real motion frames so
ONLY the moving monster fires onsets; settle the carve over the motion window
(epoch >= W+1). Per tick, done retina CognitiveTask nodes are pruned (mechanical
housekeeping -- the eye's own `_refresh_settled` does the same; it keeps the
per-cell run_rules cost flat and is what lets high resolution COMPLETE).

Cost is reported as WORK UNITS / wall-seconds-to-complete FACTS for the next
rung -- NO timing pass/fail (timing is deferred per the rung scope).

Prereg: VISION_DOOM_CARVE_SCALE_PREREG.md. The core (build_eye / carve_scale_run
/ refusal_run / score_carve) is importable and gated on a COMMITTED frame fixture
in tests/test_doom_carve_scale_migrated.py -- self-contained, VizDoom-free.
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

SEED = 182000
SCEN = "defend_the_line.cfg"
SKIP = 6                 # tics per captured frame -> differential motion magnitude
N_CAP = 14               # f0 + 13 motion frames
WARMUP = 6               # hold f0 W ticks -> background adaptation (goes silent)
ADAPT_RATE = 0.4         # fast adaptation: silence static field, keep the mover
ONSET_DB = 6.0
CARVE_MIN_COH = 0.5      # SHIPPED carve default (not tuned)
CARVE_MIN_EVENTS = 2.5   # SHIPPED carve default (>2.5 => >=3 firing cells)
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(RESULTS, "doom_carve_scale")
# Resolutions swept (n_az x n_el = cols x rows). 4:3 LANDSCAPE, exact area-mean
# downsamples of the 320(W)x240(H) screen (n_az>n_el, matching block 181000's
# 20x15). Highest resolution runs "as high as COMPLETES" (timing deferred).
SWEEP = [(20, 15), (40, 30), (80, 60), (160, 120)]
FIRES_RES = (160, 120)         # the fires-resolution (prereg headline grid)
SUBGRID_RES = (20, 15)         # the sub-grid-wall grid (reproduces 181000 zero)


# =====================================================================
#  CORE — importable, VizDoom-free (the gate reuses this on the fixture)
# =====================================================================
def build_eye(n_el, n_az):
    return GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=ADAPT_RATE,
        context={"retina_2d": True, "synchronous": True, "worker_capacity": 1,
                 "onset_threshold_db": ONSET_DB, "onset_refractory_epochs": 0.0,
                 "visual_carve": True, "carve_min_coherence": CARVE_MIN_COH,
                 "carve_min_events": CARVE_MIN_EVENTS}).build()


def _prune_done_tasks(eye):
    """Remove done retina CognitiveTask nodes (mechanical housekeeping). Delegates
    to the eye's OWN `prune_settled_tasks` (block 183000) — the same settled-task
    prune a real eye tick uses — which removes exactly the terminal-status retina
    tasks this helper always did. Keeps per-cell run_rules cost flat so high
    resolution COMPLETES. No decision, no effect on the carve (byte-identical)."""
    eye.prune_settled_tasks()


def _tick(eye, luma, rng):
    eye.submit_photons_2d(dpw.photon_packets(luma, rng))
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    _prune_done_tasks(eye)


def _onsets_at(eye, epoch):
    return sum(1 for nid in eye.substrate.nodes("RetinalOnsetEvent")
               if int(round(float(eye.substrate.node(nid)["attrs"]["epoch"]))) == epoch)


def downsample_labels(labels_buf, n_el, n_az):
    """Per-pixel object-id mask -> per-cell MODAL label value grid (n_el, n_az).
    A cell owns the plurality object (ties -> lower value). 0 = background.
    (Mirror of scripts/eye_on_doom_probe.downsample_labels.)"""
    lab = np.asarray(labels_buf)
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


def _poly_span(p):
    return {(r, c) for r in range(p["row_min"], p["row_max"] + 1)
            for c in range(p["col_min"], p["col_max"] + 1)}


def score_carve(polys, names_motion, labels_motion, n_el, n_az):
    """Score carved VisionPolygons vs the moving-monster label cells.

    Common-fate carve captures the object's SWEPT PATH over the window, so the
    ground truth is the UNION of each monster's label cells over the motion
    frames (the swept region). `best_iou[name]` = best polygon IoU vs that union.
    `false_poly_rate` = fraction of polygons touching NO monster cell (fabricated
    on textureless/background) -- the REFUSAL measure.

    `labels_motion` is a list of per-frame MODAL label grids (n_el,n_az);
    `names_motion` is a list of per-frame [{name,value},...]."""
    unions = {}
    for grid, labs in zip(labels_motion, names_motion):
        grid = np.asarray(grid)
        names = {int(l["value"]): l["name"] for l in labs}
        for v, nm in names.items():
            if nm == "DoomPlayer":
                continue
            cells = {(int(r), int(c)) for r, c in zip(*np.where(grid == v))}
            unions.setdefault(nm, set()).update(cells)
    unions = {nm: c for nm, c in unions.items() if c}
    allmon = set().union(*unions.values()) if unions else set()
    best = {}
    for nm, cells in unions.items():
        b = 0.0
        for p in polys:
            span = _poly_span(p)
            u = len(cells | span)
            b = max(b, (len(cells & span) / u) if u else 0.0)
        best[nm] = round(b, 4)
    fp = sum(1 for p in polys if len(_poly_span(p) & allmon) == 0)
    # COLLECTIVE COVERAGE (the primary carve-vs-labels measure for a common-fate
    # carve: the carve captures the object's swept path, so score the UNION of all
    # polygon spans against the UNION of monster cells over the window).
    allpoly = set().union(*[_poly_span(p) for p in polys]) if polys else set()
    inter = len(allpoly & allmon)
    denom = len(allpoly | allmon)
    union_iou = (inter / denom) if denom else 0.0
    precision = (inter / len(allpoly)) if allpoly else 0.0
    recall = (inter / len(allmon)) if allmon else 0.0
    return {
        "n_polygons": len(polys),
        "best_iou": best,
        "best_iou_overall": round(max(best.values()), 4) if best else 0.0,
        "union_iou": round(union_iou, 4),
        "carve_precision": round(precision, 4),
        "carve_recall": round(recall, 4),
        "false_polygons": fp,
        "false_poly_rate": round(fp / max(len(polys), 1), 4),
        "monster_union_sizes": {nm: len(c) for nm, c in unions.items()},
        "carve_cells": len(allpoly),
    }


def carve_scale_run(lumas, labels_motion, names_motion, n_el, n_az,
                    warmup=WARMUP, seed=SEED):
    """One eye over [f0]*warmup + motion. Returns carve metrics + polygons + cost.

    `lumas`        : [f0, f1, ..., fM]  (M motion luma grids after f0)
    `labels_motion`: [modal-label-grid(f1), ...]  (n_el,n_az) oracle grids
    `names_motion` : [[{name,value},...] for f1..fM]
    """
    f0, motion = lumas[0], lumas[1:]
    eye = build_eye(n_el, n_az)
    rng = np.random.default_rng(seed)
    t0 = time.time()
    for _ in range(warmup):
        _tick(eye, f0, rng)
    # Prune warmup onset events (excluded by the window anyway; keeps the graph
    # small). Mechanical: the carve reads only epoch >= since.
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    motion_onsets = []
    for luma in motion:
        _tick(eye, luma, rng)
        motion_onsets.append(_onsets_at(eye, eye._epoch))
    eye.settle_carve_2d(since_epoch=since)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    wall = time.time() - t0
    score = score_carve(polys, names_motion, labels_motion, n_el, n_az)
    eye.stop()
    return {
        "grid_az": n_az, "grid_el": n_el, "cells": n_az * n_el,
        "warmup": warmup, "motion_ticks": len(motion),
        "motion_onsets": motion_onsets,
        "motion_onset_total": int(sum(motion_onsets)),
        "wall_seconds": round(wall, 2),
        "polygons": polys,
        **score,
    }


def refusal_run(f0, n_el, n_az, ticks, seed=SEED):
    """REFUSAL control: feed the STATIC f0 for the whole run (warmup + a 'motion'
    window of the same length) -- NO independently-moving object. The adapted
    field is silent, so the carve must mint ZERO polygons. Able-to-fail: a carve
    that fabricated on textureless/adapted input would mint here."""
    eye = build_eye(n_el, n_az)
    rng = np.random.default_rng(seed)
    for _ in range(WARMUP):
        _tick(eye, f0, rng)
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    motion_onsets = []
    for _ in range(ticks):
        _tick(eye, f0, rng)          # STILL -> adapted -> silent
        motion_onsets.append(_onsets_at(eye, eye._epoch))
    eye.settle_carve_2d(since_epoch=since)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    eye.stop()
    return {"grid_az": n_az, "grid_el": n_el, "n_polygons": len(polys),
            "motion_onset_total": int(sum(motion_onsets))}


# =====================================================================
#  CAPTURE (world-adapter I/O) + RENDER (mechanical emit)
# =====================================================================
def capture(nframes=N_CAP, skip=SKIP, seed=SEED):
    import vizdoom as vzd
    g = vzd.DoomGame()
    g.load_config(os.path.join(vzd.scenarios_path, SCEN))
    g.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    g.set_screen_format(vzd.ScreenFormat.RGB24)
    g.set_depth_buffer_enabled(True)
    g.set_labels_buffer_enabled(True)
    g.set_render_hud(False)
    g.set_render_weapon(False)
    g.set_window_visible(False)
    g.set_seed(int(seed))
    g.init()
    g.new_episode()
    act = [0] * len(g.get_available_buttons())      # noop -> STILL camera
    frames = []
    for _ in range(nframes):
        if g.is_episode_finished() or g.is_player_dead():
            break
        st = g.get_state()
        if st is None:
            break
        frames.append({
            "rgb": np.array(st.screen_buffer, copy=True),
            "labels_buf": np.array(st.labels_buffer, copy=True),
            "depth": np.array(st.depth_buffer, copy=True),
            "labels": [{"name": l.object_name, "value": int(l.value)}
                       for l in st.labels],
        })
        g.make_action(act, int(skip))
    g.close()
    return frames


def render_overlay(res, label_grids_motion, names_motion, n_el, n_az, path):
    """Carve overlay: carved polygon bboxes vs the monster labels grid (union)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    grid = np.zeros((n_el, n_az))
    for g, labs in zip(label_grids_motion, names_motion):
        g = np.asarray(g)
        names = {int(l["value"]): l["name"] for l in labs}
        for v, nm in names.items():
            if nm not in ("DoomPlayer",) and v != 0:
                grid[g == v] = 1.0
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.imshow(grid, cmap="Greys", interpolation="nearest", alpha=0.85)
    for p in res["polygons"]:
        rect = mpatches.Rectangle(
            (p["col_min"] - 0.5, p["row_min"] - 0.5),
            p["col_max"] - p["col_min"] + 1, p["row_max"] - p["row_min"] + 1,
            fill=False, edgecolor="#d73027", linewidth=2)
        ax.add_patch(rect)
    ax.set_title(f"{n_az}x{n_el}: {res['n_polygons']} VisionPolygon(s) (red) vs "
                 f"monster labels (grey)\nbest IoU={res['best_iou_overall']} "
                 f"false-poly rate={res['false_poly_rate']}", fontsize=9)
    ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)
    return path


# =====================================================================
def main():
    from domains.engine_provenance import provenance_stamp
    import vizdoom as vzd
    os.makedirs(OUTDIR, exist_ok=True)
    if not os.path.exists(os.path.join(vzd.scenarios_path, SCEN)):
        print("VizDoom scenario unavailable — aborting.")
        return 2
    prov = provenance_stamp(strict=False)

    frames = capture()
    assert len(frames) >= N_CAP, f"only captured {len(frames)} frames"
    names_motion = [f["labels"] for f in frames[1:]]

    sweep = []
    for (n_az, n_el) in SWEEP:
        lumas = [dpw.luma_grid(f["rgb"], n_el, n_az) for f in frames]
        label_grids = [downsample_labels(f["labels_buf"], n_el, n_az)
                       for f in frames[1:]]
        res = carve_scale_run(lumas, label_grids, names_motion, n_el, n_az)
        ref = refusal_run(lumas[0], n_el, n_az, ticks=len(frames) - 1)
        res["refusal_n_polygons"] = ref["n_polygons"]
        sweep.append(res)
        print(f"{n_az}x{n_el}: npoly={res['n_polygons']} "
              f"union_iou={res['union_iou']} prec={res['carve_precision']} "
              f"rec={res['carve_recall']} best_single={res['best_iou_overall']} "
              f"false_poly_rate={res['false_poly_rate']} "
              f"refusal_npoly={ref['n_polygons']} "
              f"onset_total={res['motion_onset_total']} "
              f"wall={res['wall_seconds']}s", flush=True)
        render_overlay(res, label_grids, names_motion, n_el, n_az,
                       os.path.join(OUTDIR, f"overlay_{n_az}x{n_el}.png"))

    out = {"block": SEED, "scenario": SCEN, "skip": SKIP,
           "warmup": WARMUP, "adapt_rate": ADAPT_RATE,
           "carve_min_coherence": CARVE_MIN_COH,
           "carve_min_events": CARVE_MIN_EVENTS,
           "engine_source_match": prov.get("source_match"),
           "sweep": [{k: v for k, v in r.items() if k != "polygons"}
                     for r in sweep]}
    with open(os.path.join(RESULTS, "doom_carve_scale.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    # committed fixture for the self-contained gate: luma + modal labels at the
    # sub-grid-wall res (15x20) and the fires res (60x80).
    fixdir = os.path.join(ROOT, "tests", "fixtures", "doom_carve_scale")
    os.makedirs(fixdir, exist_ok=True)
    for (n_az, n_el) in [SUBGRID_RES, (80, 60), FIRES_RES]:
        lumas = np.stack([dpw.luma_grid(f["rgb"], n_el, n_az) for f in frames])
        labs = np.stack([downsample_labels(f["labels_buf"], n_el, n_az)
                         for f in frames]).astype(np.int32)
        np.savez_compressed(
            os.path.join(fixdir, f"frames_{n_az}x{n_el}.npz"),
            lumas=lumas.astype(np.float32), labels=labs)
    with open(os.path.join(fixdir, "label_names.json"), "w") as fh:
        json.dump([f["labels"] for f in frames], fh)

    print("source_match:", prov.get("source_match"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
