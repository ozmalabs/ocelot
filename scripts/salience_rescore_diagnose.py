"""salience_rescore_diagnose — the POST-HOC diagnostic that explains the
pre-registered verdict (VISION_SALIENCE_RESCORE_RESULTS.md §4).

NOT pre-registered. Found by chasing a zero-width confidence interval in one
cell (§12.3: verify the fact before touching anything). Reports (a) how
misidentification mass is distributed over BASE FRAMES, and (b) how strongly
per-frame failure tracks per-frame motion magnitude.

Mechanical measurement over stored rows and regenerated frames.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

N_BASE = 50
DELTAS = (1, 5, 25)
COMPARATORS = ("Q0", "Q1", "Q2")


def gini(x):
    x = np.sort(np.asarray(x, float))
    n = len(x)
    if x.sum() == 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float((2 * (i * x).sum()) / (n * x.sum()) - (n + 1) / n)


def main():
    rows_dir, frames_dir, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    out = {"corpora": {}}
    for cid in ("C1", "C2"):
        grey = np.load(os.path.join(frames_dir, f"frames_{cid}.npz"))["grey"].astype(float)
        motion = np.array([float(np.mean(np.abs(grey[t + 1] - grey[t])))
                           for t in range(N_BASE)])
        cells = {}
        for cmp_name in COMPARATORS:
            with open(os.path.join(
                    rows_dir,
                    f"invariant_comparator_rows_{cid}_{cmp_name}.json")) as fh:
                rows = json.load(fh)
            for d in DELTAS:
                per = np.zeros(N_BASE, int)
                for r in rows:
                    if r["tag"].startswith(f"A1|d{d}|") and not r["true_is_max"]:
                        per[r["base"]] += 1
                n = int(per.sum())
                if n == 0:
                    continue
                srt = np.sort(per)[::-1]
                thr = np.percentile(motion, 90)
                cells[f"{cmp_name}|d{d}"] = {
                    "n_misid": n,
                    "frames_with_any_error": int((per > 0).sum()),
                    "frames_where_all_16_regions_failed": int((per == 16).sum()),
                    "share_of_errors_in_top5_frames": float(srt[:5].sum() / n),
                    "gini_over_frames": gini(per),
                    "pearson_r_with_frame_motion":
                        float(np.corrcoef(motion, per)[0, 1]),
                    "share_of_errors_in_top10pct_motion_frames":
                        float(per[motion >= thr].sum() / n),
                }
        out["corpora"][cid] = {
            "motion_per_base": [float(v) for v in motion],
            "cells": cells,
        }
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
