#!/usr/bin/env python3
"""VIDEO PROBE — the assembled eye pointed at REAL VIDEO. The confirmatory run.

Pre-registration: VISION_VIDEO_PROBE_PREREG.md (committed BEFORE this run, §3).

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***
No seed is edited, no rule added, no default changed, no Rust touched. It boots
the committed seeds exactly as every committed rung does, sets only the graph-data
flags the eye already ships with (§9 opt-ins), presents REAL frames, and READS.

ARCHITECTURE (CLAUDE.md §0): every function here is mechanical I/O — decode a
frame, write luminance onto Cell nodes, tick, read attrs back, tally. There is no
conditional over graph state that decides anything the agent should decide. The
`_quantize` step (S3) is the one place a structure is HANDED to the graph, and
that is not a slip — it IS the measurement (see §3/S3 of the prereg: k goes IN,
nothing derives it, so k is SWEPT and its sensitivity is the reported result).

USAGE (from the gamma-substrate dir):
    PYTHONPATH=runners/dsl/python:. python scripts/video_probe_measure.py \
        --out results/video_probe.json

Seeds: block 54000-54999 claimed. Frame/crop indices turned out fully
deterministic, so NO seed in the block is consumed (recorded in the ledger).
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

# §10.1 rule 3: pin THIS tree's engine before any substrate_rs import.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import (  # noqa: E402
    add_lateral_retina, set_lat_params, residuals as lat_residuals, install_gains)
from domains import border_ownership_world as bow  # noqa: E402

IGNITE_EVERY = 5          # inherited from the committed instrument, unchanged
S3_MAX_STEPS = 200_000    # bow.tick's own committed cap


# --------------------------------------------------------------------------- #
#  BOOT — identical to the committed assembled-eye instrument.
# --------------------------------------------------------------------------- #
def boot_eye(grid, *, change=1.0, sustain=1.0, lateral=1.0):
    """Boot the ASSEMBLED eye: waves + change + lateral, all §9 opt-ins ON.
    Byte-for-byte the same boot as scripts/assembled_eye_scale.py::boot_eye."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    w = WaveWorld(s, h=grid, w=grid, seed=0)
    lat = add_lateral_retina(w)
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", float(change))
        s.set_attr(cp, "sustain", float(sustain))
    set_lat_params(w, lateral=float(lateral))
    return s, ag, w, lat


# --------------------------------------------------------------------------- #
#  CORPUS — REAL frames. Pure I/O; no content decision.
# --------------------------------------------------------------------------- #
def jellyfin_frames(n, *, every, start_s, size, episode_index=0):
    """Decode `n` real frames in TEMPORAL ORDER off Jellyfin, greyscale 0..255 at
    (size,size). Returns (frames, meta). Episode chosen by a fixed positional
    index into the sorted catalogue — deterministic, not a content choice."""
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from jellyfin_world import JellyfinWorld           # noqa: E402
    from domains.vision_corpus import area_downsample  # noqa: E402
    import av                                          # noqa: E402

    jf = JellyfinWorld().connect()
    # Deterministic positional pick: sorted series, sorted episodes. A POSITION,
    # not a content decision (the same convention vision_corpus uses).
    series = sorted(jf.catalog(("Series",)), key=lambda it: str(it["id"]))
    if not series:
        raise RuntimeError("jellyfin returned no series")
    eps = []
    si = 0
    while not eps and si < len(series):
        eps = sorted(jf.episodes(series[(episode_index + si) % len(series)]["id"]),
                     key=lambda e: str(e["id"]))
        si += 1
    if not eps:
        raise RuntimeError("jellyfin returned no episodes")
    ep = eps[episode_index % len(eps)]
    item_id = ep["id"]
    url = jf.stream_url(item_id)

    c = av.open(url, timeout=60)
    out = []
    try:
        c.streams.video[0].thread_type = "AUTO"
        if start_s:
            c.seek(int(start_s) * 1_000_000)
        for i, f in enumerate(c.decode(video=0)):
            if every > 1 and i % every:
                continue
            g = f.to_ndarray(format="gray").astype(np.float32)   # 0..255
            out.append(area_downsample(g / 255.0, size) * 255.0)
            if len(out) >= n:
                break
    finally:
        c.close()
    meta = {"source": "jellyfin", "episode_id": str(item_id),
            "series": str(ep.get("series", "?")),
            "name": str(ep.get("name", "?")),
            "season": ep.get("season"), "ep": ep.get("ep"),
            "n_series_in_catalogue": len(series),
            "n_episodes_in_series": len(eps), "episode_index": episode_index,
            "every_nth_decoded_frame": every, "start_s": start_s,
            "size": size, "n_frames": len(out)}
    return (np.stack(out) if out else np.zeros((0, size, size), np.float32)), meta


def bsds_frame(size, idx=0):
    """One REAL BSDS300 natural photograph, centre-cropped to (size,size) at
    8-bit — the natural-statistics control (the same corpus and the same crop
    convention the committed agreement arm used)."""
    from domains.vision_corpus import bsds_paths
    from PIL import Image
    paths = bsds_paths("train")
    if not paths:
        return None, {"error": "BSDS300 absent (data/ not linked?)"}
    p = paths[idx % len(paths)]
    im = np.asarray(Image.open(p).convert("L"), np.float32)
    h, w = im.shape
    r0, c0 = max(0, (h - size) // 2), max(0, (w - size) // 2)
    return im[r0:r0 + size, c0:c0 + size], {"source": "bsds300",
                                            "path": os.path.basename(p),
                                            "native": [int(h), int(w)]}


# --------------------------------------------------------------------------- #
#  S1 — RETINA on real video. Positive-controlled BEFORE any number is read.
# --------------------------------------------------------------------------- #
def _settle_read(world, lat, frame, steps=6):
    """Hold a frame for `steps` (> window_steps) so the previous stimulus's
    transient ages out, leaving the sustained spatial response. Read |residual|.
    Same convention as the committed agreement arm."""
    for _ in range(steps):
        world.step(ignite_k=0, frame=frame)
    return np.abs(lat_residuals(world, lat["hcells"]))


def stage_s1(frames, grid, *, meta):
    """Fraction of HCells firing on REAL video, with the two pre-registered
    controls. If a control fails, the stage is UNINTERPRETABLE (§1 cl.4)."""
    s, ag, world, lat = boot_eye(grid)
    # Isolate the SPATIAL response: suppress waves so `bursting` is not
    # contaminated by travelling-wave activity (committed agreement convention).
    for wp in s.nodes("WaveParams"):
        s.set_attr(wp, "propagate", 0.0)
    install_gains(world, lat["hcells"], 0.5, 0.5)   # DC-nulling predictor

    # -- CONTROL 1: uniform field -> ~0% fire (calibrates the floor) --
    r_flat = _settle_read(world, lat, np.full((grid, grid), 128.0, np.float32))
    floor = float(np.max(r_flat)) + 1e-6
    flat_fire = float(np.mean(r_flat > floor))
    # -- CONTROL 2: hard edge -> fires ONLY at the boundary --
    edge = np.zeros((grid, grid), np.float32)
    edge[:, grid // 2:] = 255.0
    r_edge = _settle_read(world, lat, edge)
    fire_mask = r_edge > floor
    edge_fire = float(np.mean(fire_mask))
    cols = np.abs(np.arange(grid) - grid // 2)
    dist = (float(np.mean(np.tile(cols, (grid, 1))[fire_mask.reshape(grid, grid)]))
            if fire_mask.any() else None)
    # A hard edge must fire SPARSELY and CLOSE to the boundary.
    controls_pass = bool(flat_fire == 0.0 and 0.0 < edge_fire < 0.5
                         and dist is not None and dist <= 2.0)

    per_frame = []
    for i, f in enumerate(frames):
        r = _settle_read(world, lat, f.astype(np.float32))
        per_frame.append(float(np.mean(r > floor)))

    fire = np.asarray(per_frame, float)
    return {
        "grid": grid, "n_frames": len(per_frame), "corpus": meta,
        "control_uniform_fire_pct": flat_fire * 100.0,
        "control_edge_fire_pct": edge_fire * 100.0,
        "control_edge_mean_dist_to_boundary": dist,
        "controls_pass": controls_pass,
        "floor_calibrated_from_uniform": floor,
        "fire_pct_mean": float(fire.mean()) * 100.0 if len(fire) else None,
        "fire_pct_sd": float(fire.std()) * 100.0 if len(fire) else None,
        "fire_pct_min": float(fire.min()) * 100.0 if len(fire) else None,
        "fire_pct_max": float(fire.max()) * 100.0 if len(fire) else None,
        "verdict": (("UNINTERPRETABLE — control failed" if not controls_pass else
                     "DENSE (>50%)" if fire.mean() > 0.5 else
                     "SPARSE (<25%)" if fire.mean() < 0.25 else
                     "INDETERMINATE (25-50%)") if len(fire) else "NO FRAMES"),
    }


# --------------------------------------------------------------------------- #
#  S2 — COMPUTE vs SURPRISE. The headline test.
# --------------------------------------------------------------------------- #
def _spearman(a, b):
    """Spearman rho via Pearson on ranks. Ties get average ranks."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3:
        return None

    def rank(x):
        o = np.argsort(x, kind="mergesort")
        r = np.empty(len(x), float)
        r[o] = np.arange(len(x), dtype=float)
        # average ties
        for v in np.unique(x):
            m = x == v
            if m.sum() > 1:
                r[m] = r[m].mean()
        return r
    ra, rb = rank(a), rank(b)
    sa, sb = ra.std(), rb.std()
    if sa == 0 or sb == 0:
        return None
    return float(((ra - ra.mean()) * (rb - rb.mean())).mean() / (sa * sb))


def stage_s2(frames, grid, *, meta):
    """Per-frame wall-clock vs per-frame surprise on a REAL temporal sequence.
    Unit of analysis is the FRAME (§4)."""
    s, ag, world, lat = boot_eye(grid)
    costs, surprises = [], []
    prev = None
    for i, f in enumerate(frames):
        f = f.astype(np.float32)
        surp = None if prev is None else float(np.mean(np.abs(f - prev)))
        t0 = time.perf_counter()
        world.step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0, frame=f)
        dt = (time.perf_counter() - t0) * 1000.0
        if surp is not None:
            costs.append(dt)
            surprises.append(surp)
        prev = f

    c, sp = np.asarray(costs), np.asarray(surprises)
    rho = _spearman(sp, c) if len(c) >= 3 else None
    cv = float(c.std() / c.mean()) if len(c) and c.mean() else None
    # The surprise axis must genuinely vary or rho is meaningless (§1 control).
    surprise_varies = bool(len(sp) and sp.max() > 0 and (sp.max() / max(sp.min(), 1e-9)) > 3.0)
    if not surprise_varies:
        verdict = "UNINTERPRETABLE — surprise axis does not vary"
    elif rho is None or cv is None:
        verdict = "UNINTERPRETABLE — too few frames"
    elif rho < 0.3 and cv < 0.10:
        verdict = "FLAT — compute-proportional-to-surprise REFUTED as built"
    elif rho > 0.5:
        verdict = "TRACKS — compute-proportional-to-surprise SURVIVES"
    else:
        verdict = "INDETERMINATE"
    return {
        "grid": grid, "n_frames_paired": len(c), "corpus": meta,
        "spearman_rho_surprise_vs_cost": rho,
        "cost_ms_mean": float(c.mean()) if len(c) else None,
        "cost_ms_sd": float(c.std()) if len(c) else None,
        "cost_ms_cv": cv,
        "cost_ms_min": float(c.min()) if len(c) else None,
        "cost_ms_max": float(c.max()) if len(c) else None,
        "surprise_min": float(sp.min()) if len(sp) else None,
        "surprise_median": float(np.median(sp)) if len(sp) else None,
        "surprise_max": float(sp.max()) if len(sp) else None,
        "surprise_ratio_max_over_min": (float(sp.max() / max(sp.min(), 1e-9))
                                        if len(sp) else None),
        "surprise_axis_varies": surprise_varies,
        "verdict": verdict,
    }


# --------------------------------------------------------------------------- #
#  S3 — PROTO-OBJECTS on real frames, under a SWEPT quantization k.
# --------------------------------------------------------------------------- #
def _quantize(frame, k):
    """Uniform k-level quantization of a real frame to the INTEGER value grid
    `border_ownership_world.add_field` requires.

    THIS IS THE HAND-SUPPLIED STRUCTURE. `k` is derived from nothing: I choose
    it. That is precisely why it is swept rather than tuned (§13, prereg S3)."""
    f = np.asarray(frame, float)
    lo, hi = float(f.min()), float(f.max())
    if hi <= lo:
        return [[0] * f.shape[1] for _ in range(f.shape[0])]
    q = np.clip(((f - lo) / (hi - lo) * k).astype(int), 0, k - 1)
    return [[int(v) for v in row] for row in q]


def _n_components(grid):
    """4-connected components of equal value — the reference count the graph's
    own flood should be labelling. Plain numpy; a REFERENCE, not the graph."""
    a = np.asarray(grid)
    H, W = a.shape
    seen = np.zeros((H, W), bool)
    n = 0
    for r in range(H):
        for c in range(W):
            if seen[r, c]:
                continue
            n += 1
            v = a[r, c]
            stack = [(r, c)]
            seen[r, c] = True
            while stack:
                y, x = stack.pop()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and not seen[yy, xx] and a[yy, xx] == v:
                        seen[yy, xx] = True
                        stack.append((yy, xx))
    return n


def _s3_positive_control():
    """Reproduce the committed synthetic answer (border_ownership_measure's
    arm_figure_ground: ONE proto, 24 members). If this does not reproduce, no
    real-frame S3 number is claimed (§1 cl.4, §10.2 rule 3)."""
    H = W = 12
    g = [[0] * W for _ in range(H)]
    for r in range(3, 9):
        for c in range(4, 8):
            g[r][c] = 1
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    bow.add_field(s, g)
    bow.set_flag(s, bown=1.0)
    t0 = time.perf_counter()
    sweeps = bow.tick(s, max_steps=S3_MAX_STEPS)
    ms = (time.perf_counter() - t0) * 1000.0
    protos = bow.protos(s)
    ok = (len(protos) == 1 and protos[0]["members"] == 24)
    return {"n_protos": len(protos),
            "members": protos[0]["members"] if protos else None,
            "expected": {"n_protos": 1, "members": 24},
            "sweeps": sweeps, "ms": ms, "reproduces_committed_answer": bool(ok)}


def stage_s3(frames, grid, ks, *, meta, n_frames=3):
    ctrl = _s3_positive_control()
    rows = []
    if ctrl["reproduces_committed_answer"]:
        for fi in range(min(n_frames, len(frames))):
            f = frames[fi][:grid, :grid]
            for k in ks:
                g = _quantize(f, k)
                ncomp = _n_components(g)
                s, ag = boot_core()
                load_seeds_into(s, ag, ["vision_border_ownership"])
                bow.add_field(s, g)
                bow.set_flag(s, bown=1.0)
                t0 = time.perf_counter()
                sweeps = bow.tick(s, max_steps=S3_MAX_STEPS)
                ms = (time.perf_counter() - t0) * 1000.0
                protos = bow.protos(s)
                cells = grid * grid
                rows.append({
                    "frame_index": fi, "k": k, "grid": grid, "cells": cells,
                    "n_components_reference": ncomp,
                    "n_protos": len(protos),
                    "proto_per_cell": len(protos) / cells,
                    "sweeps": sweeps, "hit_step_cap": bool(sweeps >= S3_MAX_STEPS),
                    "ms": ms,
                })
    # -- the two pre-registered meaningfulness halves --
    verdict, ratio, worst = "UNINTERPRETABLE — positive control failed", None, None
    if rows:
        by_frame_ok, ratios = [], []
        for fi in sorted({r["frame_index"] for r in rows}):
            sub = [r for r in rows if r["frame_index"] == fi]
            counts = [r["n_protos"] for r in sub]
            lo = max(min(counts), 1)
            ratios.append(max(counts) / lo)
            by_frame_ok.append(max(r["proto_per_cell"] for r in sub) < 0.05
                               and (max(counts) / lo) < 3.0)
        ratio = float(np.mean(ratios))
        worst = float(max(r["proto_per_cell"] for r in rows))
        verdict = ("MEANINGFUL — object-scaled and k-stable" if all(by_frame_ok)
                   else "FAILS — texture-scaled and/or k-unstable")
    return {"corpus": meta, "positive_control": ctrl, "k_sweep": ks,
            "rows": rows,
            "mean_k_instability_ratio": ratio,
            "worst_proto_per_cell": worst,
            "threshold_proto_per_cell": 0.05, "threshold_k_ratio": 3.0,
            "verdict": verdict}


# --------------------------------------------------------------------------- #
#  S4 — the IDENTITY seam. A POSITIVE STRUCTURAL ENUMERATION (§13.2's method).
# --------------------------------------------------------------------------- #
def stage_s4():
    """Enumerate every consumer of ProtoObject and every producer of "cell"
    signature tuples, and ask whether ANY path carries a pixel-derived region
    into a ShapeSignature. Enumerated positively over the tree — never off a
    soft accessor, never off a token count (§12.1)."""
    import re
    roots = ["domains", "scripts", "seeds", "substrate", "tests"]
    self_rel = os.path.relpath(os.path.abspath(__file__), ROOT)
    # A MENTION is not a USE (§12.1: "a claim about what code SELECTS is not
    # established by counting the tokens that select it — read one"). So the
    # bridge test is a DATAFLOW test: the file must both mention ProtoObject and
    # actually CONSTRUCT an identity-layer object (a "cell" signature tuple or an
    # add_node("ShapeSignature"...) call), not merely name one in prose.
    CELL_CTOR = re.compile(r'\[\s*"cell"\s*,')
    SIG_CTOR = re.compile(r'add_node\(\s*["\']ShapeSignature["\']')
    proto_files, cell_files, sig_files = set(), set(), set()
    proto_mentions_prose_only = {}
    for root in roots:
        base = os.path.join(ROOT, root)
        for dirpath, _dirs, files in os.walk(base):
            for fn in files:
                if not fn.endswith((".py", ".json")):
                    continue
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, ROOT)
                if rel == self_rel:              # never count the instrument itself
                    continue
                try:
                    txt = open(p, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                if "ProtoObject" in txt:
                    proto_files.add(rel)
                    # does it CONSTRUCT one, or only name it?
                    # the two real construction forms: a Python add_node(...) call
                    # and the seed's JSON effect ["add_node", "<var>", "ProtoObject"]
                    if not (re.search(r'add_node\(\s*["\']ProtoObject', txt)
                            or re.search(r'"add_node"\s*,\s*"[^"]*"\s*,\s*"ProtoObject"',
                                         txt)
                            or re.search(r'NodesOfType["\'\s:]+.{0,40}ProtoObject', txt)
                            or 'nodes("ProtoObject")' in txt):
                        proto_mentions_prose_only[rel] = True
                if CELL_CTOR.search(txt):
                    cell_files.add(rel)
                if SIG_CTOR.search(txt):
                    sig_files.add(rel)
    bridge = sorted(proto_files & (cell_files | sig_files))
    return {
        "method": ("positive enumeration over domains/ scripts/ seeds/ substrate/ "
                   "tests/; bridge = DATAFLOW (constructs a 'cell' tuple or a "
                   "ShapeSignature node), not a mention (§12.1)"),
        "n_proto_object_files": len(proto_files),
        "proto_object_files": sorted(proto_files),
        "proto_mention_is_prose_only": sorted(proto_mentions_prose_only),
        "n_cell_tuple_producer_files": len(cell_files),
        "n_shapesignature_constructor_files": len(sig_files),
        "bridge_files": bridge,
        "bridge_exists": bool(bridge),
        "verdict": ("A PATH EXISTS — exercise it" if bridge else
                    "STRUCTURAL ABSENCE — no ProtoObject reaches the identity layer"),
    }


# --------------------------------------------------------------------------- #
#  S5 — SCALE on REAL frames.
# --------------------------------------------------------------------------- #
def stage_s5(sizes, *, ticks=4, repeats=3, episode_meta=None, frames_by_size=None):
    rows = []
    for g in sizes:
        f = frames_by_size[g]
        s, ag, world, lat = boot_eye(g)
        for i in range(3):                      # warmup
            world.step(ignite_k=0, frame=f[i % len(f)].astype(np.float32))
        samples = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            for i in range(ticks):
                world.step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0,
                           frame=f[i % len(f)].astype(np.float32))
            samples.append((time.perf_counter() - t0) * 1000.0 / ticks)
        a = np.asarray(samples)
        rows.append({"grid": g, "cells": g * g,
                     "ms_per_tick_mean": float(a.mean()),
                     "ms_per_tick_sd": float(a.std()),
                     "us_per_cell": float(a.mean() * 1000.0 / (g * g))})
    # log-log fit of ms vs cells
    fit = None
    if len(rows) >= 3:
        x = np.log10([r["cells"] for r in rows])
        y = np.log10([r["ms_per_tick_mean"] for r in rows])
        A = np.vstack([x, np.ones_like(x)]).T
        (m, b), res, *_ = np.linalg.lstsq(A, y, rcond=None)
        ss_tot = float(((y - y.mean()) ** 2).sum())
        ss_res = float(res[0]) if len(res) else 0.0
        fit = {"exponent": float(m), "intercept": float(b),
               "r2": (1.0 - ss_res / ss_tot) if ss_tot else None,
               "n_points": len(rows)}
    return {"corpus": episode_meta, "rows": rows, "fit_total_vs_cells": fit,
            "committed_synthetic_fit_drive_exponent": 1.9882229567973935,
            "verdict": (("CONFIRMED — quadratic in cells" if fit and fit["exponent"] > 1.7
                         else "REFUTED — not quadratic") if fit else "NO FIT")}


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/video_probe.json")
    ap.add_argument("--grid", type=int, default=24)
    ap.add_argument("--n-frames", type=int, default=150)
    ap.add_argument("--every", type=int, default=2)
    ap.add_argument("--start-s", type=int, default=300)
    ap.add_argument("--episode-index", type=int, default=0)
    ap.add_argument("--s3-grid", type=int, default=16)
    ap.add_argument("--s5-sizes", default="12,16,24,32")
    ap.add_argument("--skip", default="", help="comma list of stages to skip")
    args = ap.parse_args()
    skip = {x.strip() for x in args.skip.split(",") if x.strip()}

    prov = provenance_line()
    print(f"[provenance] {prov}", flush=True)
    out = {"provenance": prov,
           "prereg": "VISION_VIDEO_PROBE_PREREG.md",
           "base_sha": "328065b62a31cf1daeb601557f21a0d331a2aed2",
           "args": vars(args)}

    # ---- S0: decode REAL video ----
    t0 = time.perf_counter()
    frames, meta = jellyfin_frames(args.n_frames, every=args.every,
                                   start_s=args.start_s, size=args.grid,
                                   episode_index=args.episode_index)
    meta["decode_s"] = time.perf_counter() - t0
    out["S0_corpus"] = meta
    print(f"[S0] {meta['n_frames']} real frames from "
          f"{meta['series']} / {meta['name']} in {meta['decode_s']:.1f}s", flush=True)

    bs, bmeta = bsds_frame(args.grid, 0)
    out["S0_bsds_control"] = bmeta

    if "s1" not in skip:
        out["S1_retina"] = stage_s1(frames[:40], args.grid, meta=meta)
        print(f"[S1] {out['S1_retina']['verdict']} "
              f"fire={out['S1_retina']['fire_pct_mean']:.2f}%", flush=True)

    if "s2" not in skip:
        out["S2_compute_vs_surprise"] = stage_s2(frames, args.grid, meta=meta)
        r = out["S2_compute_vs_surprise"]
        print(f"[S2] {r['verdict']} rho={r['spearman_rho_surprise_vs_cost']} "
              f"CV={r['cost_ms_cv']}", flush=True)

    if "s3" not in skip:
        out["S3_proto_objects"] = stage_s3(frames, args.s3_grid, [2, 4, 8, 16],
                                           meta=meta)
        print(f"[S3] {out['S3_proto_objects']['verdict']}", flush=True)

    if "s4" not in skip:
        out["S4_identity_seam"] = stage_s4()
        print(f"[S4] {out['S4_identity_seam']['verdict']}", flush=True)

    if "s5" not in skip:
        sizes = [int(x) for x in args.s5_sizes.split(",")]
        fbs = {}
        for g in sizes:
            if g == args.grid:
                fbs[g] = frames
            else:
                fbs[g], _ = jellyfin_frames(8, every=args.every,
                                            start_s=args.start_s, size=g,
                                            episode_index=args.episode_index)
        out["S5_scale"] = stage_s5(sizes, episode_meta=meta, frames_by_size=fbs)
        print(f"[S5] {out['S5_scale']['verdict']} "
              f"exp={out['S5_scale']['fit_total_vs_cells']}", flush=True)

    os.makedirs(os.path.dirname(os.path.join(ROOT, args.out)), exist_ok=True)
    with open(os.path.join(ROOT, args.out), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
