#!/usr/bin/env python3
"""POST-HOC DIAGNOSTIC — NOT PRE-REGISTERED, and labelled as such everywhere.

`VISION_CUT_ABSTENTION_PREREG.md` declared arm 2b (a fast rigid pan must not be
refused) and arm 4 (a cut-free sequence must not be refused). Arm 2b PASSED for
the magnitude statistic and arm 4 FAILED, which is the opposite of the
pre-registered prediction on 2b — and the reason is an instrument defect in MY
OWN arm, found by refusing to accept a convenient pass (§12.3: verify the fact
first, then decide what it means).

THE DEFECT: `np.roll(frame0, v*t)` is a CONSTANT-VELOCITY rigid pan, so its
per-step motion is the SAME NUMBER at every step. A distribution with zero
variance has no Otsu split above its maximum, so nothing can be marked — arm 2b
passes by DEGENERACY, not by the rule distinguishing a pan from a cut. What it
does establish (and this is real) is that the threshold is RELATIVE: a
uniformly fast sequence is uniformly normal, which a hand-set corpus-wide
threshold would have got catastrophically wrong.

This script measures the non-degenerate version — a pan whose velocity VARIES,
which is what a real camera does — and characterises arm 4's failure. Neither
rescues anything: arm 4 had already failed when these were written.

USAGE:
    PYTHONPATH=runners/dsl/python:. python scripts/cut_abstention_diagnose.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np                                    # noqa: E402
import importlib.util as _iu                          # noqa: E402

_spec = _iu.spec_from_file_location(
    "cut_abstention_measure",
    os.path.join(ROOT, "scripts", "cut_abstention_measure.py"))
cam = _iu.module_from_spec(_spec)
_spec.loader.exec_module(cam)

#: Post-hoc, and drawn from THIS RUNG'S OWN BLOCK (73000-73999).
DIAG_SEED = 73500


def main():
    out = {"provenance": provenance_line(),
           "label": "POST-HOC. NOT PRE-REGISTERED. See the docstring.",
           "constant_velocity_pan_is_degenerate": {},
           "varying_velocity_pan": {},
           "arm4_characterisation": {}}

    for cid in ("C1", "C2"):
        try:
            frames, _meta = cam.load_video(cid)
        except Exception as e:                            # noqa: BLE001
            print(f"[{cid}] ABSENT: {e}", flush=True)
            continue
        ref_step = [float(np.mean(np.abs(frames[t + 1] - frames[t])))
                    for t in range(len(frames) - 1)]
        ref_thr = cam.otsu_threshold(ref_step)
        cuts = [t for t, x in enumerate(ref_step) if x > ref_thr]

        # 1. THE DEGENERACY, stated as a number rather than an argument.
        for v in cam.PAN_VELOCITIES:
            seq = [np.roll(frames[0], (0, v * t), axis=(0, 1))
                   for t in range(len(frames))]
            m = [float(np.mean(np.abs(seq[t + 1] - seq[t])))
                 for t in range(len(seq) - 1)]
            out["constant_velocity_pan_is_degenerate"][f"{cid}|pan{v}"] = {
                "mean_motion": float(np.mean(m)),
                "sd_motion": float(np.std(m)),
                "n_distinct_values": len({round(x, 12) for x in m})}

        # 2. THE NON-DEGENERATE PAN. Velocity varies per step, so the motion
        # distribution has a spread — as a real camera's does — while the
        # sequence still contains NO discontinuity: every frame is a rigid
        # translation of the same source frame.
        rng = np.random.RandomState(DIAG_SEED)
        for label, vs in (("uniform_1_to_8", rng.randint(1, 9, len(frames))),
                          ("mostly_slow_occasional_fast",
                           np.where(np.random.RandomState(DIAG_SEED + 1)
                                    .rand(len(frames)) < 0.1, 8, 1))):
            off = np.cumsum(vs)
            seq = [np.roll(frames[0], (0, int(off[t])), axis=(0, 1))
                   for t in range(len(frames))]
            m = [float(np.mean(np.abs(seq[t + 1] - seq[t])))
                 for t in range(len(seq) - 1)]
            for armed in ("mag", "xcorr"):
                sr = cam._sequence_only(seq, armed)
                out["varying_velocity_pan"][f"{cid}|{label}|{armed}"] = {
                    "n_steps": len(sr["steps"]), "n_cut": sr["n_cut"],
                    "cut_fraction": sr["n_cut"] / max(1, len(sr["steps"])),
                    "graph_threshold": sr["cut_threshold"],
                    "motion_mean": float(np.mean(m)),
                    "motion_sd": float(np.std(m))}
                print(f"  [{cid} {label} {armed}] cut {sr['n_cut']}/"
                      f"{len(sr['steps'])} sd={np.std(m):.3f}", flush=True)

        # 3. ARM 4's FAILURE, characterised: is the rule finding structure, or
        # is it simply marking the top of whatever distribution it is handed?
        bounds = [-1] + cuts + [len(ref_step)]
        best = max(range(len(bounds) - 1), key=lambda i: bounds[i + 1] - bounds[i])
        lo, hi = bounds[best] + 1, bounds[best + 1]
        run = ref_step[lo:hi]
        sr = cam._sequence_only(frames[lo:hi + 1], "mag")
        marked = [s["t"] for s in sr["steps"] if s["is_cut"]]
        mags = sorted(run, reverse=True)
        out["arm4_characterisation"][cid] = {
            "frame_range": [lo, hi], "n_steps": len(run),
            "n_marked": len(marked),
            "marked_fraction": len(marked) / max(1, len(run)),
            "marked_are_the_top_n": set(marked) == set(sorted(
                range(len(run)), key=lambda i: -run[i])[:len(marked)]),
            "threshold": sr["cut_threshold"],
            "run_motion_max": float(max(run)) if run else 0.0,
            "run_motion_median": float(np.median(run)) if run else 0.0,
            "ratio_max_to_median": (float(max(run) / np.median(run))
                                    if run and np.median(run) else 0.0),
            "corpus_cut_min": float(min((ref_step[t] for t in cuts), default=0.0)),
            "corpus_otsu_threshold": ref_thr,
            "marked_magnitudes": [float(run[t]) for t in marked if t < len(run)],
            "top_5_magnitudes": [float(x) for x in mags[:5]]}
        print(f"  [arm4 {cid}] marked {len(marked)}/{len(run)} "
              f"thr={sr['cut_threshold']:.3f} max={max(run):.3f} "
              f"corpus_cut_min={min((ref_step[t] for t in cuts), default=0):.3f}",
              flush=True)

    path = os.path.join(ROOT, "results", "cut_abstention_diagnose.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {path}")


if __name__ == "__main__":
    main()
