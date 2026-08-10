#!/usr/bin/env python3
"""VIDEO PROBE — POST-HOC DIAGNOSTICS.

*** THESE ARE DIAGNOSTICS, NOT THE PRE-REGISTERED RESULT. ***
The confirmatory verdicts are whatever `scripts/video_probe_measure.py` wrote to
`results/video_probe.json`, and NOTHING here revises them (PROTOCOL §5: a measure
is never changed to rescue a failure). Each block below exists to DIAGNOSE a
result that came back INDETERMINATE or that a sampling defect made uninformative
(§7: a negative that is diagnosed is worth more than a positive that is not).

D1  S1's natural-statistics control. The prereg declared BSDS300 as the control
    corpus (§2) and the confirmatory run measured only the cartoon video. Same
    instrument, both corpora, so the cartoon number has something to be read
    against.

D2  S2 came back INDETERMINATE (rho=0.300, CV=0.220). There is a KNOWN CONFOUND
    I introduced and did not declare: the committed drive convention ignites the
    wave every 5th frame (`IGNITE_EVERY`), which adds cost on 20% of frames
    INDEPENDENTLY of surprise. This stratifies cost by ignite phase to see how
    much of the variance and how much of rho is the confound rather than content.

D3  S3 sampled frames 0,1,2 — which came from ONE STATIC SHOT and returned
    byte-identical rows, so its effective n was 1, not 3. This repeats it on
    frames spread across the whole decoded sequence. This is repairing a
    SAMPLING defect, not changing a measure: the criterion is untouched.

D4  S2's rho REPLICATED, and the TIME-DRIFT control. §4: "replicate on fresh
    seeds before believing — p=0.013 and p=0.0016 both evaporated." A single
    rho=0.30 off one pass is exactly the shape of finding this arc has twice
    watched evaporate. This runs the same drive R times and also correlates cost
    against FRAME INDEX, because a warm-up / cache / thermal drift in cost that
    happens to align with a drift in surprise would manufacture a correlation
    that has nothing to do with content.

USAGE (from the gamma-substrate dir):
    PYTHONPATH=runners/dsl/python:. python scripts/video_probe_diagnose.py \
        --out results/video_probe_diagnose.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
import importlib.util as _iu  # noqa: E402

_spec = _iu.spec_from_file_location(
    "video_probe_measure", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
vp = _iu.module_from_spec(_spec)
_spec.loader.exec_module(vp)


# --------------------------------------------------------------------------- #
def d1_bsds_control(grid, n_images=12):
    """S1's instrument on REAL BSDS300 photographs — the declared control."""
    from domains.vision_corpus import bsds_paths
    from PIL import Image
    paths = bsds_paths("train")
    if not paths:
        return {"error": "BSDS300 absent"}
    frames = []
    for i in range(n_images):
        p = paths[i % len(paths)]
        im = np.asarray(Image.open(p).convert("L"), np.float32)
        h, w = im.shape
        r0, c0 = max(0, (h - grid) // 2), max(0, (w - grid) // 2)
        frames.append(im[r0:r0 + grid, c0:c0 + grid])
    out = vp.stage_s1(np.stack(frames), grid,
                      meta={"source": "bsds300", "n_images": n_images,
                            "paths": [os.path.basename(paths[i % len(paths)])
                                      for i in range(n_images)]})
    return out


# --------------------------------------------------------------------------- #
def d2_ignite_stratified(frames, grid):
    """Re-run S2's drive recording the IGNITE PHASE per frame, then report the
    statistic WITHIN the non-ignite stratum (where the confound is absent) and
    within the ignite stratum, alongside the pooled (pre-registered) value."""
    s, ag, world, lat = vp.boot_eye(grid)
    rows = []
    prev = None
    for i, f in enumerate(frames):
        f = f.astype(np.float32)
        surp = None if prev is None else float(np.mean(np.abs(f - prev)))
        ig = 1 if i % vp.IGNITE_EVERY == 0 else 0
        t0 = time.perf_counter()
        world.step(ignite_k=ig, frame=f)
        dt = (time.perf_counter() - t0) * 1000.0
        if surp is not None:
            rows.append({"i": i, "ignite": ig, "surprise": surp, "cost_ms": dt})
        prev = f

    def block(sel):
        sp = np.array([r["surprise"] for r in rows if sel(r)])
        c = np.array([r["cost_ms"] for r in rows if sel(r)])
        if len(c) < 3:
            return None
        return {"n": len(c),
                "spearman_rho": vp._spearman(sp, c),
                "cost_ms_mean": float(c.mean()),
                "cost_ms_cv": float(c.std() / c.mean()) if c.mean() else None,
                "cost_ms_min": float(c.min()), "cost_ms_max": float(c.max())}

    pooled = block(lambda r: True)
    noig = block(lambda r: r["ignite"] == 0)
    ig = block(lambda r: r["ignite"] == 1)
    # How much of the pooled spread is the ignite phase alone?
    share = None
    if noig and ig and pooled and pooled["cost_ms_mean"]:
        share = (ig["cost_ms_mean"] - noig["cost_ms_mean"]) / pooled["cost_ms_mean"]
    return {"pooled_reproduction": pooled, "non_ignite_stratum": noig,
            "ignite_stratum": ig,
            "ignite_mean_cost_excess_as_frac_of_pooled_mean": share,
            "note": ("The PRE-REGISTERED verdict is the pooled one in "
                     "results/video_probe.json and is NOT revised here.")}


# --------------------------------------------------------------------------- #
def d3_s3_spread(frames, grid, ks, idxs):
    """S3's criterion, UNCHANGED, on frames spread across the whole sequence."""
    rows = []
    for fi in idxs:
        if fi >= len(frames):
            continue
        f = frames[fi][:grid, :grid]
        for k in ks:
            g = vp._quantize(f, k)
            ncomp = vp._n_components(g)
            from substrate.boot_core import boot_core, load_seeds_into
            from domains import border_ownership_world as bow
            s, ag = boot_core()
            load_seeds_into(s, ag, ["vision_border_ownership"])
            bow.add_field(s, g)
            bow.set_flag(s, bown=1.0)
            t0 = time.perf_counter()
            sweeps = bow.tick(s, max_steps=vp.S3_MAX_STEPS)
            ms = (time.perf_counter() - t0) * 1000.0
            protos = bow.protos(s)
            rows.append({"frame_index": fi, "k": k, "grid": grid,
                         "cells": grid * grid,
                         "n_components_reference": ncomp,
                         "n_protos": len(protos),
                         "proto_per_cell": len(protos) / (grid * grid),
                         "sweeps": sweeps, "ms": ms})
    per_frame = {}
    for fi in sorted({r["frame_index"] for r in rows}):
        sub = [r for r in rows if r["frame_index"] == fi]
        counts = [r["n_protos"] for r in sub]
        per_frame[fi] = {"counts_by_k": {r["k"]: r["n_protos"] for r in sub},
                         "zero_at_any_k": bool(min(counts) == 0),
                         "max_over_min": max(counts) / max(min(counts), 1)}
    n_distinct = len({tuple(sorted(v["counts_by_k"].items()))
                      for v in per_frame.values()})
    return {"rows": rows, "per_frame": per_frame,
            "n_distinct_k_profiles": n_distinct,
            "frames_with_zero_protos_at_some_k":
                sum(1 for v in per_frame.values() if v["zero_at_any_k"]),
            "n_frames": len(per_frame)}


# --------------------------------------------------------------------------- #
def d4_replicate_rho(frames, grid, reps=4):
    """Run S2's drive `reps` times on the SAME frames and report the spread of
    rho, plus the time-drift control rho(frame_index, cost)."""
    runs = []
    for rep in range(reps):
        s, ag, world, lat = vp.boot_eye(grid)
        idx, sp, cost = [], [], []
        prev = None
        for i, f in enumerate(frames):
            f = f.astype(np.float32)
            surp = None if prev is None else float(np.mean(np.abs(f - prev)))
            t0 = time.perf_counter()
            world.step(ignite_k=1 if i % vp.IGNITE_EVERY == 0 else 0, frame=f)
            dt = (time.perf_counter() - t0) * 1000.0
            if surp is not None:
                idx.append(i); sp.append(surp); cost.append(dt)
            prev = f
        idx, sp, cost = map(np.asarray, (idx, sp, cost))
        h = len(cost) // 2
        runs.append({
            "rep": rep, "n": int(len(cost)),
            "rho_surprise_vs_cost": vp._spearman(sp, cost),
            "rho_frameindex_vs_cost": vp._spearman(idx, cost),
            "rho_frameindex_vs_surprise": vp._spearman(idx, sp),
            "rho_first_half": vp._spearman(sp[:h], cost[:h]),
            "rho_second_half": vp._spearman(sp[h:], cost[h:]),
            "cost_ms_mean": float(cost.mean()),
            "cost_ms_cv": float(cost.std() / cost.mean()),
        })
    rhos = [r["rho_surprise_vs_cost"] for r in runs]
    return {"runs": runs,
            "rho_min": float(min(rhos)), "rho_max": float(max(rhos)),
            "rho_mean": float(np.mean(rhos)), "rho_sd": float(np.std(rhos)),
            "rho_spread_factor": float(max(rhos) / max(min(rhos), 1e-9)),
            "note": ("The PRE-REGISTERED S2 verdict (INDETERMINATE) is NOT revised "
                     "here. This measures whether the weak positive rho REPLICATES.")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/video_probe_diagnose.json")
    ap.add_argument("--grid", type=int, default=24)
    ap.add_argument("--s3-grid", type=int, default=16)
    ap.add_argument("--n-frames", type=int, default=150)
    ap.add_argument("--every", type=int, default=2)
    ap.add_argument("--start-s", type=int, default=300)
    args = ap.parse_args()

    prov = provenance_line()
    print(f"[provenance] {prov}", flush=True)
    out = {"provenance": prov, "kind": "POST-HOC DIAGNOSTICS — not the prereg result",
           "prereg": "VISION_VIDEO_PROBE_PREREG.md",
           "confirmatory_result": "results/video_probe.json",
           "args": vars(args)}

    frames, meta = vp.jellyfin_frames(args.n_frames, every=args.every,
                                      start_s=args.start_s, size=args.grid)
    out["corpus"] = meta
    print(f"[D0] {meta['n_frames']} frames from {meta['series']} / {meta['name']}",
          flush=True)

    out["D1_bsds_natural_statistics_control"] = d1_bsds_control(args.grid)
    b = out["D1_bsds_natural_statistics_control"]
    print(f"[D1] BSDS fire={b.get('fire_pct_mean')} controls_pass={b.get('controls_pass')}",
          flush=True)

    out["D2_ignite_stratified"] = d2_ignite_stratified(frames, args.grid)
    print(f"[D2] {json.dumps(out['D2_ignite_stratified']['non_ignite_stratum'])}",
          flush=True)

    idxs = [0, 25, 50, 75, 100, 125, 149]
    out["D3_s3_spread_frames"] = d3_s3_spread(frames, args.s3_grid,
                                              [2, 4, 8, 16], idxs)
    d3 = out["D3_s3_spread_frames"]
    print(f"[D3] {d3['n_distinct_k_profiles']} distinct k-profiles over "
          f"{d3['n_frames']} frames; "
          f"{d3['frames_with_zero_protos_at_some_k']} lose ALL protos at some k",
          flush=True)

    out["D4_rho_replication"] = d4_replicate_rho(frames, args.grid)
    d4 = out["D4_rho_replication"]
    print(f"[D4] rho over {len(d4['runs'])} reps: "
          f"{[round(r['rho_surprise_vs_cost'], 3) for r in d4['runs']]} "
          f"(spread {d4['rho_min']:.3f}-{d4['rho_max']:.3f})", flush=True)

    with open(os.path.join(ROOT, args.out), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
