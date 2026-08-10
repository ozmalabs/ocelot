"""RUNG 8D — STEP 4: THE PILOT. Seed-level variance of the calibrated probe.

**§3.3 PILOT, restricted to ALREADY-BURNED seeds (0-13), exactly as rung 8's
prereg §5 specifies** ("a power analysis on a pilot restricted to already-burned
seeds ... 0-13, 3000"). **NO confirmatory seed is touched. NO hypothesis is
tested.** This exists ONLY to fix `n` in advance for the confirmation run.

WHY THIS IS NEEDED AND WHY 8C's n=1 IS NOT ENOUGH
---------------------------------------------------
Rung 8C measured ONE seed (0) and reported the mean over its 6 cells. §4 is
explicit: **"Unit of analysis is the SEED, not the unit. Units in a run share
input and compete under winner-take-all => not independent."** So 8C's floor
0.2304 is n=1, and its spread across seeds is UNKNOWN.

And this rung has now MEASURED why that matters (`rung8d_scale_invariance.py`
+ the argmax audit): **the FLOOR cell's tuning curve contains EXACT TIES between
orientations** (tc[30deg] == tc[150deg] to 1e-16; tc[60deg] == tc[120deg]), so
`osi()`'s `argmax` is decided by FLOAT ROUNDING, and the orthogonal of the
winning tie is a DIFFERENT orientation with a DIFFERENT value. **The floor's OSI
is a LOTTERY over tie-breaks.** It is noise, not bias — but it is noise the
confirmation must be powered against, and nobody has measured its size across
seeds.

MY PREDICTION, IN ADVANCE (§3.7)
---------------------------------
* **IDEAL: ~1.0000 on every seed with near-zero variance.** Its tuning curve has
  REAL gaps (top1-top2 relative gap 0.15-0.28 measured), so no tie, no lottery.
* **FLOOR: a mean near 0.2-0.3 with a LARGE per-seed sd (I predict sd >= 0.05)**,
  because of the tie lottery. If the sd is small, the lottery is real but its
  effect on the seed-level mean is small, and I have overstated it.

Provisos:
 1. If any seed's FLOOR exceeds 0.50, G2 is not robust across seeds and rung
    8C's PASS was a property of seed 0 rather than of the probe.
 2. If the IDEAL varies across seeds, the ideal arm is not the exact reference I
    claim and the whole gate is softer than reported.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.engine_provenance import provenance_line  # noqa: E402
from scripts.rung8c_ensemble_transfer import measure, prepare  # noqa: E402

PILOT_SEEDS = list(range(14))          # 0-13: ALREADY BURNED (rung 8 prereg §5)


def main() -> int:
    print("=" * 78)
    print("RUNG 8D STEP 4 — PILOT: SEED-LEVEL VARIANCE (burned seeds 0-13)")
    print(provenance_line())
    print("  §3.3 pilot. NO confirmatory seed. NO hypothesis. Fixes n only.")
    print("=" * 78)

    rows = []
    for sd in PILOT_SEEDS:
        wi, usi, dwi = prepare("lateral", ideal=True, adapt="probe", seed=sd)
        wf, usf, dwf = prepare("lateral", ideal=False, adapt="probe", seed=sd)
        mi, mf = measure(wi, usi), measure(wf, usf)
        rows.append({"seed": sd, "ideal": mi["osi"], "floor": mf["osi"],
                     "sep": mi["osi"] - mf["osi"],
                     "alive_i": mi["alive"], "alive_f": mf["alive"],
                     "dw": max(dwi, dwf)})
        r = rows[-1]
        print(f"  seed {sd:>3d}  ideal {r['ideal']:.4f} (alive {r['alive_i']:5.2f})"
              f"   floor {r['floor']:.4f} (alive {r['alive_f']:5.2f})"
              f"   sep {r['sep']:.4f}   max|dw| {r['dw']:.1e}")

    ideal = np.array([r["ideal"] for r in rows])
    floor = np.array([r["floor"] for r in rows])
    sep = np.array([r["sep"] for r in rows])
    n = len(rows)

    def rep(name, x):
        sd_ = x.std(ddof=1)
        se = sd_ / np.sqrt(n)
        print(f"  {name:<10s} mean {x.mean():.4f}  sd {sd_:.4f}  se {se:.4f}  "
              f"min {x.min():.4f}  max {x.max():.4f}")

    print(f"\n--- PILOT SUMMARY (n = {n} seeds, unit of analysis = SEED per §4) ---")
    rep("IDEAL", ideal)
    rep("FLOOR", floor)
    rep("SEPARATION", sep)

    print("\n--- PROVISO CHECKS ---")
    print(f"  any seed FLOOR > 0.50 (G2 would fail)? "
          f"{'YES -> ' + str(floor[floor > 0.5]) if (floor > 0.5).any() else 'NO'}")
    print(f"  IDEAL varies across seeds? sd = {ideal.std(ddof=1):.4f} "
          f"({'NO — exact reference' if ideal.std(ddof=1) < 0.01 else 'YES'})")

    # --- POWER ANALYSIS for the CONFIRMATION run -------------------------- #
    # The confirmation asserts the GATE holds prospectively on fresh seeds. The
    # binding criterion is G2 (FLOOR <= 0.50), the only one with real variance.
    # One-sample, one-sided margin: how many seeds to show mean FLOOR < 0.50?
    sd_f = floor.std(ddof=1)
    margin = 0.50 - floor.mean()
    if sd_f > 0:
        # n for 95% CI upper bound below 0.50 (t ~ 2 for small n, conservative)
        n_need = max(3, int(np.ceil((2.0 * sd_f / margin) ** 2)))
    else:
        n_need = 3
    print("\n--- POWER ANALYSIS -> n FOR THE CONFIRMATION RUN ---")
    print(f"  FLOOR sd (per seed) = {sd_f:.4f};  margin to G2's 0.50 = {margin:.4f}")
    print(f"  n such that a 95% CI on the FLOOR mean excludes 0.50: "
          f"n >= {n_need}")
    print(f"  SESOI (rung 6's, adopted) = 0.0595;  separation mean "
          f"{sep.mean():.4f} sd {sep.std(ddof=1):.4f}")
    print(f"\n  => DECLARE n = {max(n_need, 8)} confirmatory seeds "
          f"(floor at 8 for a usable CI).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
