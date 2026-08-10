#!/usr/bin/env python3
"""frustration_measure — BLOCK 226000 powered measure.

Runs the pre-registered gates on the SYNTHETIC cycling scenario (futile vs
productive arms), N=200 per arm, bootstrap 95% CI:

  G-frustration-tracks-futility (HEADLINE + teeth): frustration after W=6 looped
    repeats, FUTILE (high) vs PRODUCTIVE (0) -- CI-separated. The productive
    control is the gate that FAILS a repeat-counter.
  G-breaks-the-loop: steps-to-break, regulation ON vs OFF on the FUTILE scenario.
  G-no-false-break (selectivity): false-break rate on the PRODUCTIVE scenario ON.

Writes results/frustration.json. Every agent decision is a rule; this script is
mechanical measurement only.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402
from domains.frustration_world import run_episode, CAP  # noqa: E402

BASE = 226000
N = 200
W = 6           # looped repeats at which the headline frustration is read


def _boot_ci(xs, reps=2000, seed=0):
    xs = np.asarray(xs, dtype=float)
    if len(xs) == 0:
        return (0.0, 0.0, 0.0)
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return float(xs.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def main():
    out = {"block": BASE, "N": N, "W": W,
           "constants": {"frust_unit": 8, "half_life": 4,
                         "frustration_thresh": 20, "cap": CAP}}

    # --- G-frustration-tracks-futility (HEADLINE): frustration after W repeats ---
    fut_at_W, prod_at_W = [], []
    for i in range(N):
        rf = run_episode("futile", BASE + i, enabled=True, measure_horizon=W)
        rp = run_episode("productive", BASE + 1000 + i, enabled=True, measure_horizon=W)
        # frustration at the W-th looped repeat (index W-1 of loop_traj)
        fut_at_W.append(rf["loop_traj"][W - 1] if len(rf["loop_traj"]) >= W else rf["loop_traj"][-1])
        prod_at_W.append(rp["loop_traj"][W - 1] if len(rp["loop_traj"]) >= W else rp["loop_traj"][-1])
    out["headline_frustration_tracks_futility"] = {
        "futile_at_W": dict(zip(("mean", "lo", "hi"), _boot_ci(fut_at_W, seed=1))),
        "productive_at_W": dict(zip(("mean", "lo", "hi"), _boot_ci(prod_at_W, seed=2))),
        "ci_separated": _boot_ci(prod_at_W, seed=2)[2] < _boot_ci(fut_at_W, seed=1)[1],
        "productive_upper_ci_is_zero": _boot_ci(prod_at_W, seed=2)[2] == 0.0,
    }

    # --- also record the mean trajectory (first 10 looped repeats), both arms ---
    H = 10
    fut_tr = np.zeros(H); prod_tr = np.zeros(H)
    for i in range(N):
        rf = run_episode("futile", BASE + i, enabled=True, measure_horizon=H)
        rp = run_episode("productive", BASE + 1000 + i, enabled=True, measure_horizon=H)
        for j in range(H):
            fut_tr[j] += rf["loop_traj"][j] if len(rf["loop_traj"]) > j else rf["loop_traj"][-1]
            prod_tr[j] += rp["loop_traj"][j] if len(rp["loop_traj"]) > j else rp["loop_traj"][-1]
    out["mean_trajectory"] = {"futile": list(fut_tr / N), "productive": list(prod_tr / N)}

    # --- G-breaks-the-loop: steps-to-break ON vs OFF on the FUTILE scenario ---
    on_steps, off_steps = [], []
    for i in range(N):
        on = run_episode("futile", BASE + i, enabled=True)
        off = run_episode("futile", BASE + i, enabled=False)
        on_steps.append(on["steps_to_break"])
        off_steps.append(off["steps_to_break"])
    on_ci = _boot_ci(on_steps, seed=3); off_ci = _boot_ci(off_steps, seed=4)
    out["breaks_the_loop"] = {
        "on_steps_to_break": dict(zip(("mean", "lo", "hi"), on_ci)),
        "off_steps_to_break": dict(zip(("mean", "lo", "hi"), off_ci)),
        "ci_separated_on_below_off": on_ci[2] < off_ci[1],
        "on_ever_broke": sum(1 for r in on_steps if r < CAP),
        "off_ever_broke": sum(1 for r in off_steps if r < CAP),
    }

    # --- G-no-false-break (selectivity): PRODUCTIVE ON never breaks ---
    prod_breaks = 0; prod_on_steps = []
    for i in range(N):
        rp = run_episode("productive", BASE + 1000 + i, enabled=True)
        prod_on_steps.append(rp["steps_to_break"])
        if rp["break_step"] is not None:
            prod_breaks += 1
    p, lo, hi = _wilson(prod_breaks, N)
    # futile ON break rate (lower CI) for the pre-set selectivity bar
    fut_breaks = sum(1 for r in on_steps if r < CAP)
    fp, flo, fhi = _wilson(fut_breaks, N)
    out["no_false_break_selectivity"] = {
        "productive_false_break_count": prod_breaks,
        "productive_false_break_rate": {"p": p, "lo": lo, "hi": hi},
        "futile_break_rate": {"p": fp, "lo": flo, "hi": fhi},
        "selective": hi < flo,          # productive upper CI < futile lower CI
    }

    # --- G-narration: a verbatim sample from a futile run ---
    r = run_episode("futile", BASE + 0, enabled=True)
    out["narration_sample"] = {
        "break_step": r["break_step"], "prefix": r["prefix"],
        "narration": r["narration"]}

    dst = os.path.join(_ROOT, "results", "frustration.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))
    print("\nwrote", dst)


if __name__ == "__main__":
    main()
