"""PART 1 — CONVERGENCE, PER ARM (PROTOCOL 2). Run BEFORE any comparison.

PROTOCOL 2 is not optional and it is not a formality: it is the check that
explained nine failed rung-2 attempts. A zero-mean init is a DIFFERENT dynamical
starting point, so the DC arm's convergence licenses NOTHING about the zero-mean
arms'. Each arm gets its own check, on the formative input (waves) alone.

  CONVERGENT + USEFUL : anisotropy plateaus at non-zero structure AND drift -> 0
  never converges      : the arm is a transient; every number is a point on a
                         decay curve => report and STOP for that arm
  converges to death   : plateaus at zero structure => equally useless

Also tracked per checkpoint: DC power fraction and frac(w<0) — because the whole
question is whether the DC mode SURVIVES learning or is IMPOSED by the init.
"""
from __future__ import annotations

import numpy as np

from scripts.w0_ablation_lib import (INITS, build, run_waves, weights_of,
                                     drift, rf_stats)
from domains.engine_provenance import provenance_line

CKPTS = [0, 100, 400, 800, 1600, 3200, 6400]
N_SEEDS = 8          # seeds 0-7: BURNED (rung-1 exploration, rung-3/5/6 calib)


if __name__ == "__main__":
    print(provenance_line())
    print("=" * 78)
    print("PART 1 — CONVERGENCE on waves alone, per init arm. n=8 BURNED seeds (0-7)")
    print("=" * 78)
    for arm in INITS:
        print(f"\n--- {arm}  ({INITS[arm]})")
        print(f"{'steps':>6s} {'anisotropy':>11s} {'drift':>8s} "
              f"{'DC frac':>9s} {'frac(w<0)':>10s} {'||w||':>8s} {'NaN':>5s}")
        rows = {c: [] for c in CKPTS}
        for seed in range(N_SEEDS):
            w, us = build(seed, arm)
            prev = weights_of(w, us)
            done = 0
            for c in CKPTS:
                if c > done:
                    run_waves(w, c - done)
                    done = c
                cur = weights_of(w, us)
                st = rf_stats(w, us)
                st["drift"] = drift(prev, cur) if c else float("nan")
                st["nan"] = float(np.isnan(cur).mean())
                rows[c].append(st)
                prev = cur
        for c in CKPTS:
            a = {k: float(np.nanmean([r[k] for r in rows[c]])) for k in rows[c][0]}
            print(f"{c:6d} {a['anis']:11.4f} {a['drift']:8.4f} "
                  f"{a['dc_frac']:9.4f} {a['frac_neg']:10.4f} {a['norm']:8.3f} "
                  f"{a['nan']:5.2f}")
