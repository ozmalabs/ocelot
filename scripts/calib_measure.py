"""calib_measure — PROTOCOL 1: gate the MEASURE before the agent.

Three checks, all on ALREADY-BURNED seeds (0-2, 3000, 7):

  1. RANDOM input  -> the measure must sit at a FLOOR.
  2. IDEAL exemplar -> it must score HIGH.
  3. LEARNING DURATION -> if the score moves with how long you adapt on the
     SAME input, the measure is duration-confounded and every arm comparison
     is meaningless.

Check 3 is also the reframe's OWN claim under test: a "reference" that never
settles is not a fixed point. So this doubles as PROTOCOL 2 for the theta
channel.

Run:  PYTHONPATH=runners/dsl/python python3 scripts/calib_measure.py
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.calib_lib import (build, adapt_theta, ideal_split_gabor,  # noqa: E402
                               rpi_of, run_waves)
from domains.onoff_world import set_params  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402

BURNED = (0, 1, 2)


def _theta_of(w, us):
    return np.array([float(w.s.node(u)["attrs"]["theta"]) for u in us])


def main():
    print(provenance_line())
    print()

    # ---- 2. IDEAL EXEMPLAR ------------------------------------------------ #
    # The perfect signed simple cell, with theta adapted on waves exactly as
    # every arm gets it (PROTOCOL 4: a control must get the same mechanism).
    w, us, _ = build(seed=0, eta=5e-4)
    for u in us:
        ideal_split_gabor(w, u)
    adapt_theta(w, steps=400)
    rpi, st = rpi_of(w, us)
    print(f"IDEAL split-Gabor (theta adapted) : RPI {rpi.mean():.3f}  "
          f"OSI {st['osi'].mean():.4f}")

    # The same ideal cell with NO reference at all (homeo=0, theta pinned 0).
    w, us, _ = build(seed=0, eta=5e-4)
    for u in us:
        ideal_split_gabor(w, u)
    set_params(w, homeo=0.0)
    run_waves(w, 400)
    rpi0, st0 = rpi_of(w, us)
    print(f"IDEAL split-Gabor (NO reference)  : RPI {rpi0.mean():.3f}  "
          f"OSI {st0['osi'].mean():.4f}")
    print()

    # ---- 1. FLOOR: random weights ---------------------------------------- #
    fl, fo = [], []
    for sd in BURNED:
        w, us, _ = build(seed=sd, eta=5e-4)
        adapt_theta(w, steps=400)
        rpi, st = rpi_of(w, us)
        fl.append(rpi.mean())
        fo.append(st["osi"].mean())
        print(f"FLOOR untrained seed {sd} (theta adapted): RPI {rpi.mean():.3f}"
              f"  OSI {st['osi'].mean():.4f}")
    print(f"FLOOR mean: RPI {np.mean(fl):.4f}   OSI {np.mean(fo):.4f}")
    print()

    # ---- 3. DURATION CONFOUND (and the theta fixed point) ---------------- #
    print("DURATION: RPI / mean theta / theta drift vs adaptation steps, "
          "waves only, weights FROZEN (oo_eta=0)")
    print(f"{'steps':>7} {'RPI':>8} {'OSI':>8} {'theta':>9} {'drift':>9}")
    for sd in (0,):
        w, us, _ = build(seed=sd, eta=5e-4)
        set_params(w, homeo=1.0, oo_eta=0.0, frozen=0.0)
        prev = _theta_of(w, us)
        tot = 0
        for chunk in (25, 25, 50, 100, 200, 400, 800, 1600):
            run_waves(w, chunk)
            tot += chunk
            th = _theta_of(w, us)
            drift = (np.abs(th - prev).sum()
                     / max(np.abs(th).sum(), 1e-9))
            prev = th.copy()
            # read RPI without disturbing the adapting state: freeze() inside
            # rpi_of sets frozen=1; restore after.
            rpi, st = rpi_of(w, us)
            set_params(w, frozen=0.0, oo_eta=0.0, homeo=1.0)
            print(f"{tot:>7} {rpi.mean():>8.3f} {st['osi'].mean():>8.4f} "
                  f"{th.mean():>9.4f} {drift:>9.4f}")


if __name__ == "__main__":
    main()
