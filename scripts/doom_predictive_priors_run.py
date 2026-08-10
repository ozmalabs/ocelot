"""Run E1M1 with simultaneous graph-native structural priors and make the video.

Left panel is captured Doom RGB. Right panel is a mechanical read of two
distinct graph beliefs: cyan room/corridor wall confabulations and amber
grounded cells. Rules own hypothesis projection and prediction residuals.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from domains.engine_provenance import engine_preamble
engine_preamble()

import numpy as np  # noqa: E402

from domains.engine_provenance import engine_provenance, provenance_line  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
from domains import doom_map_ingest as dm  # noqa: E402
from domains import doom_prior_readout as pr  # noqa: E402
from scripts import doom_ingraph_map_run as base  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "doom_predictive_priors")
MAP_SEED = os.path.join(ROOT, "seeds", "doom_ingraph_map.json")
PRIOR_SEED = os.path.join(ROOT, "seeds", "doom_predictive_priors.json")


def _unique_prediction_cells(predictions, observed):
    pts = set()
    for p in predictions:
        (x0, y0), (x1, y1) = p["lo"], p["hi"]
        pts.update((x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1))
    return len(pts - set(observed))


def _fraction(corrected, tested):
    return round(corrected / tested, 4) if tested else None


def run(frames=80, seed=1234, fps=10, outdir=None):
    outdir = outdir or OUTDIR
    os.makedirs(outdir, exist_ok=True)
    caps = base._capture(frames, seed)
    if not caps:
        return None

    wa = WorldAdapter(seeds=())
    for path in (MAP_SEED, PRIOR_SEED):
        wa.inner.load_seed_manifest(json.load(open(path)), None)
    S = wa.s
    game = S.add_node("WorldInstance", {
        "world_type": "Game", "map_mode": "doom", "predictive_map": 1.0,
        "body_w": 1.0, "flood_epoch": 0.0,
    })

    trajectory, walked = [], set()
    spearmans, seen_frames = [], 0
    snapshots, per_frame = [], []
    for fi, cap in enumerate(caps):
        epoch = fi + 1
        px, py, ang = cap["pose"]
        acell = dm.ingest_walk(wa, game, (px, py))
        if fi >= 1:
            az_depths, _diag = base._seen_depth_by_column(caps, fi)
            if az_depths is not None:
                dm.ingest_seen_walls(wa, game, (px, py, ang), az_depths)
                seen_frames += 1
            rho = base._score_vs_depth_buffer(caps, fi, None)
            if rho is not None:
                spearmans.append(rho)

        # The prior from t-1 and bottom-up evidence at t coexist in this
        # run_rules call; rules, not this loop, decide confirmation/correction.
        pr.stamp_observation_epoch(wa, game, epoch)
        dm.accumulate(wa, game, epoch=epoch)
        trajectory.append(acell)
        walked.add(acell)

        snap = pr.read_snapshot(wa, game, epoch)
        snapshots.append(snap)
        now = [x for x in snap["outcomes"] if x["observation_epoch"] == epoch]
        corrected = sum(x["result"] == "corrected" for x in now)
        confirmed = sum(x["result"] == "confirmed" for x in now)
        per_frame.append({
            "frame": fi, "epoch": epoch, "observed_cells": len(snap["cells"]),
            "confabulated_cells": _unique_prediction_cells(snap["predictions"], snap["cells"]),
            "spatial_hypotheses": len(snap["hypotheses"]),
            "colour_flips": len(now), "confirmed": confirmed, "corrected": corrected,
        })

    video_path = os.path.join(outdir, "doom_predictive_priors.mp4")
    video = pr.encode_video([c["rgb"] for c in caps], snapshots, video_path, fps=fps)
    video["path"] = os.path.relpath(video_path, ROOT)

    final = snapshots[-1]
    cells = final["cells"]
    all_outcomes = final["outcomes"]
    confirmed = sum(x["result"] == "confirmed" for x in all_outcomes)
    corrected = sum(x["result"] == "corrected" for x in all_outcomes)
    half = len(per_frame) // 2
    early = per_frame[:half]
    late = per_frame[half:]
    e_test = sum(x["colour_flips"] for x in early)
    e_corr = sum(x["corrected"] for x in early)
    l_test = sum(x["colour_flips"] for x in late)
    l_corr = sum(x["corrected"] for x in late)
    walked_wall = sum(cells.get(p) == 1.0 for p in walked)
    walked_free = sum(cells.get(p) == 0.0 for p in walked)
    sp = np.asarray(spearmans, float)

    summary = {
        "seed": seed, "frames": len(caps), "mechanism": "simultaneous_structural_confabulation",
        "engine": engine_provenance(), "engine_line": provenance_line(),
        "video": video,
        "final_observed_cells": len(cells),
        "final_free": sum(v == 0.0 for v in cells.values()),
        "final_walls": sum(v == 1.0 for v in cells.values()),
        "final_confabulated_cells": per_frame[-1]["confabulated_cells"],
        "final_spatial_hypotheses": per_frame[-1]["spatial_hypotheses"],
        "tested_predictions": len(all_outcomes),
        "confirmed_predictions": confirmed,
        "corrected_predictions": corrected,
        "correction_fraction": _fraction(corrected, len(all_outcomes)),
        "early_half": {
            "tested": e_test, "corrected": e_corr,
            "correction_fraction": _fraction(e_corr, e_test),
        },
        "late_half": {
            "tested": l_test, "corrected": l_corr,
            "correction_fraction": _fraction(l_corr, l_test),
        },
        "seen_forward_frames": seen_frames,
        "M2_trajectory_consistency": walked_free / max(1, len(walked)),
        "M2_walls_on_walked_cells": int(walked_wall),
        "M2_seen_vs_depthbuffer_spearman": {
            "n": int(sp.size),
            "median": round(float(np.median(sp)), 4) if sp.size else None,
            "mean": round(float(np.mean(sp)), 4) if sp.size else None,
            "frac_pos": round(float((sp > 0).mean()), 3) if sp.size else None,
        },
        "per_frame": per_frame,
    }
    with open(os.path.join(outdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=80)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--fps", type=int, default=10)
    args = ap.parse_args()
    if not os.path.exists(base.WAD):
        print("SKIP: DOOM.WAD absent")
        raise SystemExit(0)
    summary = run(args.frames, args.seed, args.fps)
    print(json.dumps(summary, indent=2))
