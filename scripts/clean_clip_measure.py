#!/usr/bin/env python3
"""SECONDARY (best-effort): run the FULL free-fall pipeline on a CLEANER real
clip chosen on PRINCIPLED grounds (block 150000-150999).

PRE-REGISTERED: report WHATEVER clips are acquired (at most 2, chosen by
description before running) — no cherry-picking, no retry-until-pass. A bounce
clip's DOWNWARD approach to the first impact IS a genuine free fall; we isolate
the longest strictly-downward monotonic run of the tracked ball (the free-fall
phase), which is the physically-correct segment, not a passing subset.

Reuses the 149000 pipeline (carve + track + sub-cell registration + robust
witness) UNCHANGED via import; only the decode source (clip path + segment) and
the monotonic free-fall selection differ. NO agent decision in Python.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

from scripts.subcell_crossframe_measure import (        # noqa: E402
    quantize, carve_track_indexed, longest_run_indexed, S, SEARCH_CELLS,
)
from scripts.realism_ladder_measure import physics_test  # noqa: E402
from domains.engine_provenance import provenance_line, provenance_stamp  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "naming_corpus_local")


def decode_grey_path(path, ss, dur, fps, gw, gh):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", path,
           "-vf", f"fps={fps},scale={gw}:{gh},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (gw * gh)
    return np.frombuffer(raw[:n * gw * gh], dtype=np.uint8).reshape(n, gh, gw)


def longest_monotonic_down(run):
    """Longest strictly-downward (cy increasing) contiguous sub-run — the
    free-fall phase of a bounce. Ties keep the earliest longest."""
    best, cur = [], []
    for r in run:
        if cur and r["cy"] > cur[-1]["cy"] + 1e-9:
            cur.append(r)
        else:
            cur = [r]
        if len(cur) > len(best):
            best = list(cur)
    return best


def run_clip(path, label, *, ss, dur, fps, gw, gh, block):
    grey = decode_grey_path(path, ss, dur, fps, gw, gh)
    fq = quantize(grey)
    track = carve_track_indexed(fq, gh, gw, block)
    full_run = longest_run_indexed(track)
    fall = longest_monotonic_down(full_run)
    row = {"label": label, "clip": os.path.basename(path),
           "segment": {"ss": ss, "dur": dur, "fps": fps, "grid": [gw, gh], "block": block},
           "n_decoded": int(fq.shape[0]),
           "longest_track_run": len(full_run),
           "freefall_run_len": len(fall)}
    if len(fall) >= 6:
        cyf = [r["cy"] for r in fall]
        row["freefall_cy"] = [round(v, 2) for v in cyf]
        row["freefall_velocity_cells_per_frame"] = {
            "mean": round(float(np.mean(np.abs(np.diff(cyf)))), 3),
            "max": round(float(np.max(np.abs(np.diff(cyf)))), 3)}
        row["physics_test"] = physics_test(grey, fall)
    else:
        row["note"] = "free-fall run < 6 — no witness"
    return row


def main():
    load0 = os.getloadavg()
    t0 = time.time()
    # Candidate 2 = the CLEAN one (bright yellow tennis ball on black background,
    # static camera, single object, NO ruler). Candidate 1 (WcS8gyPrRCA) is
    # REJECTED as unclean (shutterstock watermark across the path + a hand hitting
    # the ball laterally) — recorded, per the report-whatever pre-registration.
    cand2 = os.path.join(CORPUS, "cand2_1yT0hxplVBg.mp4")
    # sweep a few segments/resolutions for the free-fall approach; report the
    # longest clean downward run found. (Segment choice is decode framing, not a
    # pass filter — every attempt's physics verdict is reported.)
    trials = [
        {"ss": 6.0, "dur": 5.0, "fps": 30, "gw": 160, "gh": 90, "block": 4},
        {"ss": 6.0, "dur": 5.0, "fps": 30, "gw": 214, "gh": 120, "block": 5},
        {"ss": 4.0, "dur": 8.0, "fps": 30, "gw": 160, "gh": 90, "block": 4},
    ]
    rows = []
    for i, tr in enumerate(trials):
        rows.append(run_clip(cand2, "cand2_trial%d" % i, **tr))
    result = {
        "block": "150000-150999",
        "engine_provenance": provenance_stamp(),
        "provenance_line": provenance_line(),
        "S": S, "search_cells": SEARCH_CELLS,
        "candidate_1_rejected": {
            "id": "WcS8gyPrRCA",
            "reason": "shutterstock watermark across the fall path + a hand hitting the ball laterally (not a clean vertical free fall)"},
        "candidate_2": {"id": "1yT0hxplVBg",
            "desc": "bright yellow tennis ball, black plain background, static camera, single object, NO ruler, slow-motion bounce (downward approach = free fall)"},
        "trials": rows,
        "loadavg_start": list(load0),
    }
    print("=== CLEAN CLIP (cand2 1yT0hxplVBg — tennis ball, black bg) ===")
    for r in rows:
        print("  [%s] track=%d freefall=%d" % (r["label"], r["longest_track_run"], r["freefall_run_len"]))
        if "physics_test" in r:
            pt = r["physics_test"]
            print("     velocity cells/f:", r["freefall_velocity_cells_per_frame"])
            print("     physics_test: full=%s winA=%s winB=%s  P1=%d P2=%d PASS=%s"
                  % (pt["coeff_full"], pt["coeff_winA"], pt["coeff_winB"],
                     pt["P1_order_sign"], pt["P2_replication_sign"], pt["PASS"]))
        else:
            print("     ", r.get("note"))
    result["wall_sec"] = round(time.time() - t0, 1)
    result["loadavg_end"] = list(os.getloadavg())
    outp = os.path.join(ROOT, "results", "clean_clip_measure.json")
    with open(outp, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", outp, "wall=%.1fs" % result["wall_sec"])


if __name__ == "__main__":
    main()
