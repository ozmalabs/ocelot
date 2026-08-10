"""RUNG 4 — PILOT on ALREADY-BURNED seeds, to FIX n before the confirmatory run.

PROTOCOL 3.3: n must be fixed in advance by a power analysis on a pilot
restricted to already-burned seeds. Seeds 4200-4215 were burned by
`rung4_calibrate.py`. This run is NOT a hypothesis test and NOTHING it reports
is a result — its only output is the per-seed SD used to size the confirmatory
run.
"""
from __future__ import annotations

import sys

import numpy as np

from rung4_lib import STEPS, arm


def main():
    seeds = list(range(4200, 4216))
    on, off = [], []
    for sd in seeds:
        a = arm(1.0, sd)
        b = arm(0.0, sd)
        on.append(a["d"])
        off.append(b["d"])
        print(f"  seed {sd}: d_on {a['d']:+7.2f}  d_off {b['d']:+7.2f}  "
              f"diff {a['d'] - b['d']:+7.2f}   "
              f"(sel on {a['selectivity']:.3f} / off {b['selectivity']:.3f})")
        sys.stdout.flush()

    on = np.asarray(on)
    off = np.asarray(off)
    diff = on - off

    print(f"\n=== PILOT (n={len(seeds)} burned seeds 4200-4215, {STEPS} steps, waves only)")
    for nm, x in (("d_on", on), ("d_off", off), ("interaction d_on - d_off", diff)):
        sd = float(np.std(x, ddof=1))
        print(f"{nm:26s} mean {x.mean():+7.3f}   SD {sd:6.3f}   "
              f"SEM {sd / np.sqrt(len(x)):6.3f}")

    print("\n=== POWER — n for 80% power, two-sided alpha=0.025 (Bonferroni, 2 tests)")
    print("    (paired one-sample; n ~= ((z_{1-a/2} + z_{0.8}) * SD / delta)^2)")
    za, zb = 2.2414, 0.8416          # z_{1-0.025/2}=2.2414, z_{0.80}=0.8416
    for nm, x in (("H1 d_on", on), ("H2 interaction", diff)):
        sd = float(np.std(x, ddof=1))
        print(f"  {nm:16s} SD={sd:6.3f}")
        for delta in (1.0, 2.0, 3.0, 5.0):
            n = ((za + zb) * sd / delta) ** 2
            print(f"      |delta| = {delta:4.1f} deg  ->  n = {int(np.ceil(n)):4d}")


if __name__ == "__main__":
    main()
