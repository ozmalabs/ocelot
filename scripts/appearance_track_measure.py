#!/usr/bin/env python3
"""APPEARANCE-TRACKED STABILITY -> REAL-VIDEO FREE-FALL PHYSICS (block 151000-151999).

H1: an APPEARANCE-TRACKED TEMPLATE holds the clean tennis-ball clip as ONE
    trajectory >=6 frames where the motion/overlap tracker fragments it.
H2: with the object held >=6 frames, the full pipeline recovers a STABLE
    single-sign acceleration through its FREE-FALL PHASE (the longest
    strictly-downward monotonic sub-run, excluding the bounce impact), passing
    149000's single-sign REPLICATION test (P1 order+sign & P2 two-window sign).

Everything downstream of the association is LANDED machinery imported UNCHANGED:
  carve            `subcell_crossframe_measure.carve_track_indexed` (per-frame
                   largest non-ground region)  [byte-identical import]
  free-fall phase  `clean_clip_measure.longest_monotonic_down`      [import]
  physics verdict  `realism_ladder_measure.physics_test`            [import]
The ONLY new element is the association: `appearance_track.longest_run` chains
the SAME per-frame largest regions by grey-patch NCC instead of by Region id.
Gated `enabled` — OFF reproduces the existing id-chained run byte-identically.

Clip: cand2_1yT0hxplVBg.mp4 (block 150000's identified clean clip). No seed drawn.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

from scripts.subcell_crossframe_measure import (        # noqa: E402
    quantize, carve_track_indexed, longest_run_indexed, S, SEARCH_CELLS,
)
from scripts.realism_ladder_measure import physics_test  # noqa: E402
from scripts.clean_clip_measure import longest_monotonic_down  # noqa: E402
from domains import appearance_track as at               # noqa: E402
from domains.engine_provenance import provenance_line, provenance_stamp  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIP = os.path.join(ROOT, "naming_corpus_local",
                    os.environ.get("CLIP_FILE", "cand2_1yT0hxplVBg.mp4"))


def decode_grey(path, ss, dur, fps, gw, gh):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", path,
           "-vf", f"fps={fps},scale={gw}:{gh},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (gw * gh)
    return np.frombuffer(raw[:n * gw * gh], dtype=np.uint8).reshape(n, gh, gw)


def run_clip(path, label, *, ss, dur, fps, gw, gh, block):
    grey = decode_grey(path, ss, dur, fps, gw, gh)
    fq = quantize(grey)
    track = carve_track_indexed(fq, gh, gw, block)          # per-frame largest NG
    # BASELINE: existing id-chained run (== appearance OFF, byte-identical).
    rust_run = at.longest_run(track, enabled=False)
    assert [ (r["fi"], round(r["cy"],6), round(r["cx"],6)) for r in rust_run ] == \
           [ (r["fi"], round(r["cy"],6), round(r["cx"],6)) for r in longest_run_indexed(track) ], \
           "appearance OFF is not byte-identical to the existing longest_run_indexed"
    # APPEARANCE: chain the SAME largest regions by grey-patch NCC on RAW grey.
    appear_run = at.longest_run(track, grey, enabled=True)
    row = {"label": label,
           "segment": {"ss": ss, "dur": dur, "fps": fps, "grid": [gw, gh], "block": block},
           "n_decoded": int(fq.shape[0]),
           "rust_id_run": len(rust_run),
           "rust_id_freefall": len(longest_monotonic_down(rust_run)),
           "appearance_run": len(appear_run),
           "HALF": at.HALF}
    fall = longest_monotonic_down(appear_run)
    row["appearance_freefall"] = len(fall)
    if len(fall) >= 6:
        cyf = [r["cy"] for r in fall]
        row["freefall_cy"] = [round(v, 2) for v in cyf]
        row["freefall_velocity_cells_per_frame"] = {
            "mean": round(float(np.mean(np.abs(np.diff(cyf)))), 3),
            "max": round(float(np.max(np.abs(np.diff(cyf)))), 3)}
        row["physics_test"] = physics_test(grey, fall)
    else:
        row["note"] = "appearance free-fall run < 6 — no witness (H-DEGRADE-a)"
    return row


def main():
    load0 = os.getloadavg()
    t0 = time.time()
    configs = json.loads(os.environ.get("MEASURE_CONFIGS", "null"))
    if not configs:
        configs = [
            # (label, ss, dur, fps, gw, gh, block) — 150000 trial2 + neighbours
            ["trial2_160x90_b4", 4.0, 8.0, 30, 160, 90, 4],
            ["trial2_160x90_b3", 4.0, 8.0, 30, 160, 90, 3],
            ["hi_214x120_b5", 4.0, 8.0, 30, 214, 120, 5],
            ["early_160x90_b4", 2.0, 10.0, 30, 160, 90, 4],
        ]
    rows = []
    for c in configs:
        label = c[0]
        rows.append(run_clip(CLIP, label, ss=c[1], dur=c[2], fps=c[3],
                             gw=c[4], gh=c[5], block=c[6]))
    result = {"block": "151000-151999", "clip": os.path.basename(CLIP),
              "HALF": at.HALF, "S": S, "search_cells": SEARCH_CELLS,
              "engine_provenance": provenance_stamp(),
              "provenance_line": provenance_line(),
              "trials": rows, "loadavg_start": list(load0)}
    print("=== APPEARANCE-TRACKED FREE-FALL (cand2 1yT0hxplVBg) ===")
    for r in rows:
        print("  [%s] RUST-ID run=%d (freefall=%d) | APPEAR run=%d (freefall=%d)"
              % (r["label"], r["rust_id_run"], r["rust_id_freefall"],
                 r["appearance_run"], r["appearance_freefall"]))
        if "physics_test" in r:
            pt = r["physics_test"]
            print("      velocity cells/f:", r["freefall_velocity_cells_per_frame"])
            print("      physics: full=%s winA=%s winB=%s  P1=%s P2=%s P3=%s PASS=%s"
                  % (pt["coeff_full"], pt["coeff_winA"], pt["coeff_winB"],
                     pt["P1_order_sign"], pt["P2_replication_sign"],
                     pt["P3_magnitude"], pt["PASS"]))
        else:
            print("     ", r.get("note"))
    result["wall_sec"] = round(time.time() - t0, 1)
    result["loadavg_end"] = list(os.getloadavg())
    stem = os.path.splitext(os.path.basename(CLIP))[0]
    outp = os.path.join(ROOT, "results", f"appearance_track_measure_{stem}.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", outp, "wall=%.1fs" % result["wall_sec"])


if __name__ == "__main__":
    main()
