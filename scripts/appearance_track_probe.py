#!/usr/bin/env python3
"""PROBE (block 151000-151999): does APPEARANCE-TEMPLATE association hold the
clean tennis-ball clip as ONE trajectory >=6 frames where the motion/overlap
tracker fragments it?

Mechanical measurement only: decode grey -> carve per frame (Rust segment_motion)
-> read the eye's carve back out -> chain the tracked object two ways:
  RUST-ID   the existing largest-non-ground-by-Region-id run (the fragmentation
            baseline — `_id_chain_largest`, byte-identical to
            `longest_run_indexed(carve_track_indexed(...))`);
  APPEAR    grey-patch NCC association (`appearance_track.longest_run(enabled=True)`).
Also reports the CEILING: the longest consecutive stretch of frames that carve
ANY non-ground region (appearance cannot bridge an empty frame).

Clip: cand2_1yT0hxplVBg.mp4 — bright yellow tennis ball on black, static camera,
no ruler (the clip block 150000 already identified as clean). No seed drawn.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp
engine_preamble()
from domains import falling_world as fw                       # noqa: E402
from domains.motion_group_world import vector_field           # noqa: E402
from domains import appearance_track as at                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIP = os.path.join(ROOT, "naming_corpus_local", "cand2_1yT0hxplVBg.mp4")
L = 4


def decode_grey(path, ss, dur, fps, gw, gh):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", path,
           "-vf", f"fps={fps},scale={gw}:{gh},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (gw * gh)
    return np.frombuffer(raw[:n * gw * gh], dtype=np.uint8).reshape(n, gh, gw)


def quantize(u8, levels=L):
    return (u8.astype(np.int32) * levels) // 256


def carve_all(frames_q, gh, gw, block):
    """Per carved frame return (fi, largest_ng|None, [all_ng regions])."""
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, gh, gw)
    out = []
    prev = frames_q[0]
    for fi in range(1, frames_q.shape[0]):
        cur = frames_q[fi]
        vf = vector_field(prev, cur, block=block)
        vy = np.repeat(np.repeat(vf[:, :, 0], block, 0), block, 1)
        vx = np.repeat(np.repeat(vf[:, :, 1], block, 0), block, 1)
        full_y = np.zeros((gh, gw)); full_x = np.zeros((gh, gw))
        full_y[:vy.shape[0], :vy.shape[1]] = vy
        full_x[:vx.shape[0], :vx.shape[1]] = vx
        native.set_attr(game, "frame", float(fi))
        native.segment_motion(game, gh, gw, full_y.reshape(-1).tolist(),
                              full_x.reshape(-1).tolist(), cell_ids)
        ng = [r for r in fw.read_regions(native, game) if r["is_ground"] == 0.0]
        largest = max(ng, key=lambda r: r["count"]) if ng else None
        out.append((fi, largest, ng))
        prev = cur
    return out


def longest_ng_stretch(carve):
    best = cur = 0
    for _, largest, _ in carve:
        cur = cur + 1 if largest is not None else 0
        best = max(best, cur)
    return best


def probe_config(path, ss, dur, fps, gw, gh, block, label):
    grey = quantize(decode_grey(path, ss, dur, fps, gw, gh))
    carve = carve_all(grey, gh, gw, block)
    track = [(fi, largest) for fi, largest, _ in carve]
    rust_run = at.longest_run(track, enabled=False)
    appear_run_largest = at.longest_run(track, grey, enabled=True)
    rpf = [(fi, ng) for fi, _, ng in carve]
    appear_run_all = at.longest_run_all(rpf, grey)
    return {
        "label": label, "ss": ss, "dur": dur, "fps": fps,
        "grid": [gw, gh], "block": block, "n_frames": int(grey.shape[0]),
        "longest_ng_stretch": longest_ng_stretch(carve),
        "rust_id_run": len(rust_run),
        "rust_id_one": len({r["id"] for r in rust_run}) == 1 if rust_run else False,
        "appearance_run_largest": len(appear_run_largest),
        "appearance_run_all": len(appear_run_all),
        "appear_cy": [round(r["cy"], 2) for r in appear_run_largest],
    }


def main():
    load0 = os.getloadavg()
    t0 = time.time()
    configs = json.loads(os.environ.get("PROBE_CONFIGS", "null"))
    if not configs:
        configs = [
            # (ss, dur, fps, gw, gh, block, label) — 150000's trial2 + neighbours
            [4.0, 8.0, 30, 160, 90, 4, "trial2_160x90_b4"],
            [4.0, 8.0, 30, 214, 120, 5, "hi_214x120_b5"],
            [4.0, 8.0, 30, 160, 90, 3, "trial2_160x90_b3"],
            [2.0, 10.0, 30, 160, 90, 4, "early_160x90_b4"],
        ]
    rows = [probe_config(CLIP, *c) for c in configs]
    out = {"block": "151000-151999", "clip": os.path.basename(CLIP),
           "HALF": at.HALF, "L": L,
           "engine_provenance": provenance_stamp(),
           "provenance_line": provenance_line(), "configs": rows,
           "loadavg_start": list(load0)}
    for r in rows:
        print(f"[{r['label']}] frames={r['n_frames']} ng_stretch={r['longest_ng_stretch']} "
              f"RUST-ID run={r['rust_id_run']} | APPEAR(largest)={r['appearance_run_largest']} "
              f"APPEAR(all)={r['appearance_run_all']}")
    out["wall_sec"] = round(time.time() - t0, 1)
    out["loadavg_end"] = list(os.getloadavg())
    outp = os.path.join(ROOT, "results", "appearance_track_probe.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as fh:
        json.dump(out, fh, indent=2)
    print("wrote", outp, "wall=%.1fs" % out["wall_sec"])


if __name__ == "__main__":
    main()
