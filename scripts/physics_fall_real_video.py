#!/usr/bin/env python3
"""PHYSICS FROM REAL VIDEO — order-2 from a REAL free-fall, end to end.

Compose LANDED machinery only (NO Rust, NO seed):
  ffmpeg decode -> grey -> downsample to the eye grid
  -> motion_group_world.vector_field (block-SAD)
  -> native.segment_motion (common-fate carve `segment_motion_and_track`)
  -> track the falling object (largest non-ground moving region) by Region id
  -> feed its perceived cy trajectory to discover_order (order-N / run_rules).

Thin video->grid adapter = admissible I/O. Every product is read FROM THE GRAPH
(`read_regions`, `discover_order`'s minted LatentDimension) and the Rust Term
(`native.evaluate`, TUPLES). Deterministic; draws NO seed.

Clip: E6jv9WTcgEQ "Slow motion acceleration of gravity trial 5 at 4000 fps" —
a white ball in genuine free fall past a measuring ruler, static camera, no
person. 128x640, 24fps, ~91s (super slow-mo). See PHYSICS_FALL_REAL_VIDEO_PREREG.
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
        "naming_corpus/gravity_freefall_ruler_E6jv9WTcgEQ.mp4")
RAW_W, RAW_H = 128, 640
L = 4                        # the eye's shipped default quantization


def decode_grey(ss, dur, fps, gw, gh):
    """Decode [ss, ss+dur] at `fps`, greyscale, scaled to gw x gh. Honest
    greyscale + downsample only (no crop, no clip tuning)."""
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", CLIP,
           "-vf", f"fps={fps},scale={gw}:{gh},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (gw * gh)
    return np.frombuffer(raw[:n * gw * gh], dtype=np.uint8).reshape(n, gh, gw)


def quantize(luma_u8, levels):
    return ((luma_u8.astype(np.int32) * levels) // 256)


def carve_track(frames_q, gh, gw, block):
    """Common-fate carve every frame; track the falling object = the LARGEST
    non-ground region, by persistent Region id. Returns per-frame dicts of the
    tracked object (or None), plus per-frame carve diagnostics."""
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, gh, gw)
    track, diag = [], []
    prev = frames_q[0]
    wall = []
    for fi in range(1, frames_q.shape[0]):
        cur = frames_q[fi]
        t0 = time.perf_counter()
        vf = vector_field(prev, cur, block=block)             # (nh,nw,2)
        vy = np.repeat(np.repeat(vf[:, :, 0], block, 0), block, 1)
        vx = np.repeat(np.repeat(vf[:, :, 1], block, 0), block, 1)
        full_y = np.zeros((gh, gw)); full_x = np.zeros((gh, gw))
        full_y[:vy.shape[0], :vy.shape[1]] = vy
        full_x[:vx.shape[0], :vx.shape[1]] = vx
        native.set_attr(game, "frame", float(fi))
        native.segment_motion(game, gh, gw, full_y.reshape(-1).tolist(),
                              full_x.reshape(-1).tolist(), cell_ids)
        wall.append(time.perf_counter() - t0)
        regs = fw.read_regions(native, game)
        ng = [r for r in regs if r["is_ground"] == 0.0]
        obj = max(ng, key=lambda r: r["count"]) if ng else None
        track.append(obj)
        diag.append({"n_regions": len(regs), "n_nonground": len(ng),
                     "largest_ng": (obj["count"] if obj else 0.0),
                     "mtol": float(native.node(game)["attrs"].get("mtol", 0.0))})
        prev = cur
    return s, ag, native, track, diag, wall


def longest_run(track):
    best, cur = [], []
    for b in track:
        if b is None:
            cur = []; continue
        if cur and b["id"] == cur[-1]["id"]:
            cur.append(b)
        else:
            cur = [b]
        if len(cur) > len(best):
            best = list(cur)
    return best


def order_n_on(native, s, ag, cy, cx):
    """Rust Term product (TUPLES) + graph run_rules verdict on the perceived cy."""
    frames = [[["obj", int(round(y)), int(round(x)), "obj"]] for y, x in zip(cy, cx)]
    prod = {}
    for f in ("explained", "order"):
        prod[f] = native.evaluate(
            {"type": "TimeInfer", "sequence": {"type": "Lit", "value": frames},
             "codebook_type": "ShapeSignature", "max_b": 8, "field": f}, {})
    status, mints = fw.discover_order(s, ag, native, cy, cx)
    return prod, status, mints


def run_config(ss, dur, fps, gw, gh, block, label):
    fq = quantize(decode_grey(ss, dur, fps, gw, gh), L)
    s, ag, native, track, diag, wall = carve_track(fq, gh, gw, block)
    run = longest_run(track)
    out = {"label": label, "ss": ss, "dur": dur, "fps": fps, "grid": [gw, gh],
           "block": block, "n_frames": int(fq.shape[0]),
           "n_carved_frames": len(track),
           "n_tracked_frames_with_obj": sum(1 for b in track if b is not None),
           "longest_run_len": len(run),
           "mean_ms_per_frame": float(np.mean(wall) * 1000) if wall else 0.0,
           "carve_mean_nonground": float(np.mean([d["n_nonground"] for d in diag])) if diag else 0.0,
           "carve_mean_largest": float(np.mean([d["largest_ng"] for d in diag])) if diag else 0.0}
    if len(run) >= 4:
        cy = [b["cy"] for b in run]; cx = [b["cx"] for b in run]
        ids = {b["id"] for b in run}
        out["run_one_id"] = (len(ids) == 1)
        out["cy"] = [round(v, 2) for v in cy]
        out["cx"] = [round(v, 2) for v in cx]
        cyi = [int(round(v)) for v in cy]
        d1 = [b - a for a, b in zip(cyi, cyi[1:])]
        d2 = [b - a for a, b in zip(d1, d1[1:])]
        out["cy_int"] = cyi; out["d1"] = d1; out["d2"] = d2
        prod, status, mints = order_n_on(native, s, ag, cy, cx)
        out["term_explained"] = prod["explained"]; out["term_order"] = prod["order"]
        out["run_rules_status"] = status
        out["mints"] = [[m[0], m[1], list(m[2]), list(m[3])] for m in mints]
    else:
        out["note"] = "longest continuous run < 4 frames — no order-2 witness"
    return out


def main():
    load0 = os.getloadavg()
    configs = json.loads(os.environ.get("PFR_CONFIGS", "null"))
    if not configs:
        # default characterization sweep (windows across the fall; fps/grid/block)
        configs = [
            # (ss, dur, fps, gw, gh, block, label)
            [5.0, 78.0, 0.5, 64, 320, 8, "whole_fall_0p5fps_64x320_b8"],
            [30.0, 40.0, 1.0, 64, 320, 6, "mid_1fps_64x320_b6"],
            [55.0, 20.0, 2.0, 64, 320, 6, "fast_2fps_64x320_b6"],
            [55.0, 20.0, 2.0, 48, 240, 4, "fast_2fps_48x240_b4"],
            [60.0, 18.0, 3.0, 64, 320, 4, "fastest_3fps_64x320_b4"],
        ]
    results = {"clip": os.path.basename(CLIP), "provenance": provenance_line(),
               "raw": [RAW_W, RAW_H], "L": L, "configs": []}
    for c in configs:
        r = run_config(*c)
        results["configs"].append(r)
        print(f"[{r['label']}] frames={r['n_frames']} run={r['longest_run_len']} "
              f"one_id={r.get('run_one_id')} ms/f={r['mean_ms_per_frame']:.1f} "
              f"nonground~{r['carve_mean_nonground']:.1f}")
        if "cy_int" in r:
            print(f"    cy_int={r['cy_int']}")
            print(f"    d1={r['d1']}  d2={r['d2']}")
            print(f"    term: explained={r['term_explained']} order={r['term_order']} "
                  f"| run_rules={r['run_rules_status']} mints={r['mints']}")
        else:
            print(f"    {r.get('note')}")
    results["loadavg_start"] = list(load0); results["loadavg_end"] = list(os.getloadavg())
    outp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "results", "physics_fall_real_video.json")
    with open(outp, "w") as fh:
        json.dump(results, fh, indent=2)
    print("wrote", outp)


if __name__ == "__main__":
    main()
