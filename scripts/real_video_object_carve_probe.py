#!/usr/bin/env python3
"""REAL-VIDEO OBJECT-CARVE PROBE — the CONFIRM for the motion-common-fate carve.

The real-video probe (`VISION_REAL_VIDEO_PROBE_RESULTS.md`) measured the wall:
the EXACT-ISO-VALUE carve (`native.segment`) shatters ~1 moving presenter into
113-528 regions/frame on real 64x36 grey footage, 68-92% of them <=2-cell
speckle confab. This re-runs the SAME clip, SAME 64x36 decode, under the NEW
MOTION-COMMON-FATE carve (`native.segment_motion`) and measures the before/after.

Arms (all on the identical decoded+quantized frames, L=4 default):
  A. VALUE @64x36        — the documented wall (reproduce 113-528 / 68-92%).
  B. MOTION @64x36       — block-match motion upsampled to per-cell, motion carve
                           at full cell resolution (directly comparable numbers).
  C. MOTION @block-grid  — motion carve at the block grid (nh=36/B, nw=64/B):
                           the seed-faithful resolution where the tolerance is
                           derived over genuine block-adjacent pairs.
  D. VALUE @block-grid    — value carve at the SAME coarse grid, the CONTROL that
                           isolates the motion contribution from the coarsening.

Motion is sensed by the EXISTING `motion_group_world.vector_field` (block SAD);
nothing about the estimator is reinvented. No Rust here — this is an EMIT probe
over the new engine primitive. Deterministic (no RNG).
"""
from __future__ import annotations
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from domains import falling_world as fw                       # noqa: E402
from domains.motion_group_world import vector_field           # noqa: E402

CLIP = ("/home/matt/ozma/internal/research/experiments/gamma-substrate/"
        "naming_corpus/ABC_Phonics_Chant_for_Children_Sounds_and_Actions_from_A_to_.mp4")
SS, DUR, FPS = 50.0, 4.0, 15
GW, GH = 64, 36
L = 4                       # the eye's shipped default quantization
BLOCKS = [2, 4]             # motion-sensor aperture sweep (declared magic, §13-exempt)
SPECKLE = 2                 # <= 2 grid-units = speckle (cells for A/B, blocks for C/D)


def decode_grey(clip, ss, dur, fps, gw, gh):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", clip,
           "-vf", f"fps={fps},scale={gw}:{gh},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (gw * gh)
    return np.frombuffer(raw[:n * gw * gh], dtype=np.uint8).reshape(n, gh, gw)


def quantize(luma_u8, levels):
    return ((luma_u8.astype(np.int32) * levels) // 256)


def block_downsample(frame_q, B):
    """Coarsen a quantized cell frame to the block grid by block-mean, requantized
    to L levels — the coarse-grid VALUE input (control D)."""
    H, W = frame_q.shape
    nh, nw = H // B, W // B
    core = frame_q[:nh * B, :nw * B].reshape(nh, B, nw, B).astype(np.float64)
    return np.rint(core.mean(axis=(1, 3))).astype(np.int32)


def carve_stats(regs, total_units):
    ng = [r for r in regs if r["is_ground"] == 0.0]
    gnd = [r for r in regs if r["is_ground"] == 1.0]
    speckle = sum(1 for r in regs if r["count"] <= SPECKLE)
    largest_ng = max((r["count"] for r in ng), default=0.0)
    return {
        "n_regions": len(regs),
        "n_nonground": len(ng),
        "speckle": speckle,
        "speckle_frac_of_regions": (speckle / len(regs)) if regs else 0.0,
        "ground_frac": (max((r["count"] for r in gnd), default=0.0) / total_units),
        "largest_ng": largest_ng,
        "largest_ng_frac": largest_ng / total_units,
    }


def run_value(frames_q, h, w):
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, h, w)
    per = []
    for fi in range(frames_q.shape[0]):
        native.set_attr(game, "frame", float(fi))
        native.segment(game, h, w, frames_q[fi].reshape(-1).tolist(), cell_ids)
        per.append(carve_stats(fw.read_regions(native, game), h * w))
    return per


def run_motion_cellres(frames_q, B):
    """Block-match motion, upsample each block vector to its B x B cells, carve at
    full GH x GW cell resolution (directly comparable to the value carve)."""
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, GH, GW)
    per, tols = [], []
    prev = frames_q[0]
    for fi in range(1, frames_q.shape[0]):
        cur = frames_q[fi]
        vf = vector_field(prev, cur, block=B)                # (nh, nw, 2)
        vy = np.repeat(np.repeat(vf[:, :, 0], B, axis=0), B, axis=1)
        vx = np.repeat(np.repeat(vf[:, :, 1], B, axis=0), B, axis=1)
        # pad back to GH x GW if B does not divide exactly (edge rows/cols = 0)
        full_y = np.zeros((GH, GW)); full_x = np.zeros((GH, GW))
        full_y[:vy.shape[0], :vy.shape[1]] = vy
        full_x[:vx.shape[0], :vx.shape[1]] = vx
        native.set_attr(game, "frame", float(fi))
        native.segment_motion(game, GH, GW, full_y.reshape(-1).tolist(),
                              full_x.reshape(-1).tolist(), cell_ids)
        per.append(carve_stats(fw.read_regions(native, game), GH * GW))
        tols.append(float(native.node(game)["attrs"].get("mtol", 0.0)))
        prev = cur
    return per, tols


def run_motion_blockgrid(frames_q, B):
    """Motion carve at the block grid (nh x nw) — the seed-faithful resolution."""
    s, ag, native = fw.boot_falling()
    nh, nw = GH // B, GW // B
    game, cell_ids = fw.setup_world(native, nh, nw)
    per, tols = [], []
    prev = frames_q[0]
    for fi in range(1, frames_q.shape[0]):
        cur = frames_q[fi]
        vf = vector_field(prev, cur, block=B)
        native.set_attr(game, "frame", float(fi))
        native.segment_motion(game, nh, nw, vf[:, :, 0].reshape(-1).tolist(),
                              vf[:, :, 1].reshape(-1).tolist(), cell_ids)
        per.append(carve_stats(fw.read_regions(native, game), nh * nw))
        tols.append(float(native.node(game)["attrs"].get("mtol", 0.0)))
        prev = cur
    return per, tols


def run_value_blockgrid(frames_q, B):
    s, ag, native = fw.boot_falling()
    nh, nw = GH // B, GW // B
    game, cell_ids = fw.setup_world(native, nh, nw)
    per = []
    for fi in range(frames_q.shape[0]):
        ds = block_downsample(frames_q[fi], B)
        native.set_attr(game, "frame", float(fi))
        native.segment(game, nh, nw, ds.reshape(-1).tolist(), cell_ids)
        per.append(carve_stats(fw.read_regions(native, game), nh * nw))
    return per


def mean(per, key):
    return float(np.mean([p[key] for p in per])) if per else 0.0


def summarize(per):
    return {k: mean(per, k) for k in
            ("n_regions", "n_nonground", "speckle", "speckle_frac_of_regions",
             "ground_frac", "largest_ng", "largest_ng_frac")}


def main():
    load0 = os.getloadavg()
    luma = decode_grey(CLIP, SS, DUR, FPS, GW, GH)
    assert luma.shape[0] >= 30, f"expected ~60 frames, got {luma.shape[0]}"
    fq = quantize(luma, L)
    result = {"clip": os.path.basename(CLIP), "grid": [GW, GH], "L": L,
              "n_frames": int(fq.shape[0]), "provenance": provenance_line(), "arms": {}}

    t0 = time.perf_counter()
    A = run_value(fq, GH, GW)
    result["arms"]["A_value_64x36"] = summarize(A)
    print("A VALUE @64x36        :", {k: round(v, 2) for k, v in result["arms"]["A_value_64x36"].items()})

    for B in BLOCKS:
        Bc, tolc = run_motion_cellres(fq, B)
        Bg, tolg = run_motion_blockgrid(fq, B)
        D = run_value_blockgrid(fq, B)
        result["arms"][f"B_motion_cellres_B{B}"] = summarize(Bc) | {"mtol_mean": float(np.mean(tolc))}
        result["arms"][f"C_motion_blockgrid_B{B}"] = summarize(Bg) | {"mtol_mean": float(np.mean(tolg)), "grid": [GW // B, GH // B]}
        result["arms"][f"D_value_blockgrid_B{B}"] = summarize(D) | {"grid": [GW // B, GH // B]}
        print(f"B MOTION @64x36 B={B}  :", {k: round(v, 2) for k, v in summarize(Bc).items()}, f"mtol~{np.mean(tolc):.2f}")
        print(f"C MOTION @{GW//B}x{GH//B} B={B} :", {k: round(v, 2) for k, v in summarize(Bg).items()}, f"mtol~{np.mean(tolg):.2f}")
        print(f"D VALUE  @{GW//B}x{GH//B} B={B} :", {k: round(v, 2) for k, v in summarize(D).items()})

    result["wall_s"] = time.perf_counter() - t0
    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "real_video_object_carve.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)


if __name__ == "__main__":
    main()
