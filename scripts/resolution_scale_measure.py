"""SCALE THE EYE'S RESOLUTION — the confirmatory measurement.

`VISION_RESOLUTION_SCALE_PREREG.md`, committed at `1fa4fe6d` before any
headline. Seeds **79000-79199** (the resolution arms; the K arm draws
79200-79399 in its own script).

A RUNNER, not an agent. It sets the adapter's resolution constants, builds
candidate sets, calls the world, and reads three attributes back. Every
decision -- which region an observation is, whether to refuse -- is
`seeds/vision_verdict_comparator.json` and is unchanged by this rung.

THE TWO AXES ARE SEPARATED HERE AND NEVER COMBINED (prereg 2.1). `B` is the
shared origin of both and is the re-earned baseline: nothing is inherited from
`VISION_VERDICT_RESULTS.md` except the verdict (NCC), rho and K_LEVELS, each
named as inherited in the pre-registration.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import random
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import engine_provenance as ep          # noqa: E402

# PROTOCOL §10 rule 3 / 1b -- PIN, do not merely REPORT. Must run before the
# first import that LOADS the engine, or it is a no-op on resolution.
ep.engine_preamble()                                 # noqa: E402

from domains import verdict_comparator_world as vw   # noqa: E402

#: The five configurations. `(id, GRID, REGION, axis)`. B is the origin of
#: BOTH axes -- it is the same row for scale and for grain, measured once.
CONFIGS = [
    ("B",   24,  6, "origin"),
    ("S48", 48,  6, "scale"),
    ("S72", 72,  6, "scale"),
    ("G48", 48, 12, "grain"),
    ("G72", 72, 18, "grain"),
]

SEED_BLOCK = 79000
N_BASE = 50
BLOCK = 10                      # 5 contiguous blocks of 10 (prereg 2.3)
DELTAS = (1, 5)
MIN_SHUFFLE_GAP = 30
VERDICT = "ncc"                 # INHERITED from VISION_VERDICT_RESULTS.md

CORPORA = {
    "C1": {"episode_index": 0, "pin": "08630d4b7b215c469df19b9c42d7b617",
           "what": "cartoon"},
    "C2": {"episode_index": 3, "pin": "119eca433329b36b19e5d69fef84966e",
           "what": "live-action"},
}

FRAME_CACHE = os.environ.get("RS_FRAME_CACHE", "")


def set_resolution(grid, region):
    """Set the adapter's resolution. A blind write of declared measurement
    constants -- no read of graph state, no branch on one."""
    vw.GRID = grid
    vw.REGION = region
    vw.N_CELLS = region * region


def load_frames(cid, grid):
    """Decode the corpus at `grid`. The episode PIN is checked and a mismatch
    VOIDS the run (prereg 2.2)."""
    path = os.path.join(FRAME_CACHE, f"{cid}_{grid}.npy") if FRAME_CACHE else ""
    meta_path = os.path.join(FRAME_CACHE, "meta.json") if FRAME_CACHE else ""
    if path and os.path.exists(path):
        frames = np.load(path)
        meta = {}
        if os.path.exists(meta_path):
            meta = json.load(open(meta_path)).get(f"{cid}_{grid}", {})
        if meta and meta.get("episode_id") != CORPORA[cid]["pin"]:
            raise SystemExit(f"EPISODE PIN MISMATCH {cid}@{grid}: "
                             f"{meta.get('episode_id')} != {CORPORA[cid]['pin']}"
                             f" -- run is VOID")
        return [np.asarray(f, float) for f in frames], meta
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    vp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vp)
    fr, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=grid,
                                  episode_index=CORPORA[cid]["episode_index"])
    if meta.get("episode_id") != CORPORA[cid]["pin"]:
        raise SystemExit(f"EPISODE PIN MISMATCH {cid}@{grid} -- run is VOID")
    return [np.asarray(f, float) for f in fr], meta


def otsu_threshold(xs):
    """Otsu's two-class split. Byte-identical to the incumbent's."""
    a = sorted(float(x) for x in xs)
    n = len(a)
    if n < 2:
        return (float("inf"), n, 0, (a[0] if a else 0.0), 0.0)
    best, best_t = -1.0, a[0]
    total = sum(a)
    csum, ccnt = 0.0, 0
    for i in range(n - 1):
        csum += a[i]
        ccnt += 1
        if a[i + 1] == a[i]:
            continue
        w0 = ccnt / n
        w1 = 1.0 - w0
        m0 = csum / ccnt
        m1 = (total - csum) / (n - ccnt)
        v = w0 * w1 * (m0 - m1) ** 2
        if v > best:
            best, best_t = v, 0.5 * (a[i] + a[i + 1])
    lo = [x for x in a if x <= best_t]
    hi = [x for x in a if x > best_t]
    return (best_t, len(lo), len(hi),
            (sum(lo) / len(lo) if lo else 0.0),
            (sum(hi) / len(hi) if hi else 0.0))


def video_probes(qs, gs, t, rng, seed):
    """One base frame's probe set (prereg 2.3). Identical in construction to
    the incumbent's, with DELTAS reduced to (1, 5)."""
    far = [u for u in range(len(qs)) if abs(u - t) >= MIN_SHUFFLE_GAP]
    probes = []
    for d in DELTAS:
        tj = min(t + d, len(qs) - 1)
        probes.append((f"A1|d{d}", "A1", qs[tj], gs[tj], (0, 0), False))
    u = rng.choice(far)
    probes.append(("A2|d1", "A2", qs[u], gs[u], (0, 0), False))
    probes.append(("A3|d1", "A3", qs[min(t + 1, len(qs) - 1)],
                   gs[min(t + 1, len(qs) - 1)], (0, 0), True))
    probes.append(("G1|d0", "G1", qs[t], gs[t], (0, 0), False))
    for label, off in (("G2c", 700), ("G2t", 800)):
        r2 = np.random.RandomState(seed + off + t)
        nq = r2.randint(0, vw.K_LEVELS, qs[t].shape)
        ng = r2.randint(0, 256, qs[t].shape).astype(float)
        probes.append((f"{label}|d0", label, nq, ng, (0, 0), False))
    return probes


def run_cell(qbase, gbase, origins, probes, seed):
    """ONE substrate: one codebook, every probe that shares it. Returns
    (rows, graph_run_ms, read_s, n_groups)."""
    rng = random.Random(seed)
    region = vw.REGION
    codebook = [(qbase[r:r + region, c:c + region],
                 gbase[r:r + region, c:c + region]) for r, c in origins]
    order = list(range(len(origins)))
    rng.shuffle(order)
    w = vw.VerdictWorld(VERDICT)
    w.hold(codebook, order)
    for _prefix, kind, qsrc, gsrc, (dr, dc), shuffle in probes:
        pad = vw.RHO + max(abs(dr), abs(dc))
        qpad = vw.pad_edge(qsrc, pad)
        gpad = vw.pad_edge(gsrc, pad)
        for i, (r0, c0) in enumerate(origins):
            orbit = vw.orbit_windows(qpad, gpad, (r0 + dr, c0 + dc), vw.RHO,
                                     region=region, pad=pad)
            if shuffle:
                orbit = [(j, vw.shuffle_arrangement(q, rng),
                          vw.shuffle_arrangement(g, rng)) for j, q, g in orbit]
            w.present(orbit, truth=i, tag=f"{_prefix}|{i}", kind=kind)
    n_groups = len(w._groups)
    t0 = time.perf_counter()
    w.run()
    run_ms = (time.perf_counter() - t0) * 1000.0
    t0 = time.perf_counter()
    rows = w.read()
    read_s = time.perf_counter() - t0
    return rows, run_ms, read_s, n_groups


def name_width_gate(n):
    """G1 sub-gate: the codebook name width is 2 below 100 entries, so B is
    byte-identical to the pre-fix path (prereg 2.4)."""
    return max(2, len(str(max(n - 1, 0))))


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    only_cfg = sys.argv[2] if len(sys.argv) > 2 else None
    prov = ep.provenance_line()
    out = {"provenance": prov, "prereg": "VISION_RESOLUTION_SCALE_PREREG.md",
           "prereg_commit": "1fa4fe6d7f44b69980ad198cbac439ea284446aa",
           "verdict": VERDICT, "seed_block": SEED_BLOCK,
           "n_base": N_BASE, "block": BLOCK, "deltas": list(DELTAS),
           "rho": vw.RHO, "k_levels": vw.K_LEVELS,
           "configs": [{"id": c, "grid": g, "region": r, "axis": a}
                       for c, g, r, a in CONFIGS],
           "loadavg_start": os.getloadavg(),
           "corpora": {}, "cells": {}, "motion": {}}
    print(f"[provenance] {prov}", flush=True)
    print(f"[machine] loadavg {out['loadavg_start']}", flush=True)

    cids = [c for c in ("C1", "C2") if which in ("all", c)]
    for cid in cids:
        for cfg_id, grid, region, axis in CONFIGS:
            if only_cfg and cfg_id != only_cfg:
                continue
            set_resolution(grid, region)
            frames, meta = load_frames(cid, grid)
            out["corpora"][f"{cid}@{grid}"] = meta
            qs = [vw.quantize(f) for f in frames]
            gs = list(frames)
            origins = list(vw.region_origins(shape=(grid, grid), region=region))
            nreg = len(origins)
            # motion + cut flags are RE-MEASURED at this resolution; nothing
            # about the cut partition is inherited (prereg 1.1).
            step = [float(np.mean(np.abs(frames[t + 1] - frames[t])))
                    for t in range(len(frames) - 1)]
            thr, nlo, nhi, mlo, mhi = otsu_threshold(step)
            cutflag = {}
            for t in range(N_BASE):
                for d in DELTAS:
                    seg = step[t:min(t + d, len(step))]
                    cutflag[f"{t}|{d}"] = bool(seg and max(seg) > thr)
            out["motion"][f"{cid}|{cfg_id}"] = {
                "otsu": thr, "n_low": nlo, "n_high": nhi,
                "mean_low": mlo, "mean_high": mhi,
                "n_cut_base": sum(1 for t in range(N_BASE)
                                  if cutflag[f"{t}|1"])}
            key = f"{cid}|{cfg_id}"
            print(f"[{key}] grid={grid} region={region} nreg={nreg} "
                  f"cells={region*region} otsu={thr:.4f} "
                  f"width={name_width_gate(nreg)}", flush=True)
            rows_all, run_ms_all, read_s_all = [], [], []
            t_wall = time.time()
            for t in range(N_BASE):
                rng = random.Random(SEED_BLOCK + 400 + t)
                probes = video_probes(qs, gs, t, rng, SEED_BLOCK)
                seed = SEED_BLOCK + 200 + t
                rows, run_ms, read_s, ngrp = run_cell(
                    qs[t], gs[t], origins, probes, seed)
                for x in rows:
                    x["base"] = t
                    x["block"] = t // BLOCK
                    x["cut"] = cutflag.get(f"{t}|1", False)
                rows_all.extend(rows)
                run_ms_all.append(run_ms)
                read_s_all.append(read_s)
                if t % 10 == 0:
                    print(f"  [{key}] base {t}/{N_BASE} "
                          f"({time.time() - t_wall:.0f}s, run "
                          f"{run_ms:.0f}ms, read {read_s:.1f}s)", flush=True)
            rp = os.path.join(ROOT, "results", f"resscale_rows_{cid}_{cfg_id}.json")
            with open(rp, "w") as fh:
                json.dump(rows_all, fh)
            h = hashlib.sha256(open(rp, "rb").read()).hexdigest()
            out["cells"][key] = {
                "grid": grid, "region": region, "axis": axis,
                "n_regions": nreg, "cells_per_region": region * region,
                "chance": 1.0 / nreg,
                "name_width": name_width_gate(nreg),
                "n_rows": len(rows_all), "n_groups_per_frame": ngrp,
                # COUNTED cost -- load-independent (prereg 2.5)
                "cell_comparisons_per_probe":
                    nreg * nreg * 25 * region * region,
                "graph_run_ms_mean": float(np.mean(run_ms_all)),
                "graph_run_ms_total": float(np.sum(run_ms_all)),
                "ref_read_s_total": float(np.sum(read_s_all)),
                "wall_s": time.time() - t_wall,
                "loadavg": os.getloadavg(),
                "rows_sha256": h, "rows_path": os.path.basename(rp)}
            print(f"  [{key}] done {time.time()-t_wall:.0f}s  "
                  f"graph {np.sum(run_ms_all)/1000:.1f}s  "
                  f"ref-read {np.sum(read_s_all):.1f}s  load {os.getloadavg()}",
                  flush=True)

    out["loadavg_end"] = os.getloadavg()
    tag = which if not only_cfg else f"{which}_{only_cfg}"
    path = os.path.join(ROOT, "results", f"resolution_scale_{tag}.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {path}", flush=True)


if __name__ == "__main__":
    main()
