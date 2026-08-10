"""RUNG 8D — THE CONFIRMATION RUN. Pre-registered in `VISION_RUNG8D_PREREG.md`,
COMMITTED BEFORE THIS RUNS.

**CONFIRMATORY. Seeds 6100-6107 (n=8, declared in advance, never used for
anything). Seeds 13000-13999 are NOT touched.**

Runs EXACTLY the pre-registered gate and nothing else (§3.6: "Exactly the listed
tests. No sweeps. No re-runs."):

    IDEAL_s / FLOOR_s / SEP_s  per SEED (unit of analysis, §4), composed pathway,
    theta settled on the PROBE for 2000 steps, weights frozen, theta PINNED.

    G1 IDEAL >= 0.80        on the 95% CI LOWER bound
    G2 FLOOR <= 0.50        on the 95% CI UPPER bound
    G3 SEPARATION >= 0.30   on the 95% CI LOWER bound
    G0 n_dead == 0          every arm, every seed
    G4 max|dw| == 0.0       every arm

The CI — not the point estimate — must clear each threshold (stricter than rung
8C, which read points at n=1; §5 permits stricter-against-self).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.complex_cells import THETAS, cell_stats  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from scripts.rung8_lib import PERIOD  # noqa: E402
from scripts.rung8c_ensemble_transfer import prepare  # noqa: E402

CONFIRM_SEEDS = list(range(6100, 6108))     # DECLARED IN THE PREREG. n = 8.


def t_ci(x, conf=0.95):
    """95% t-interval on the mean. n-1 df, two-sided (§3.1)."""
    x = np.asarray(x, float)
    n = len(x)
    m, sd = x.mean(), x.std(ddof=1)
    se = sd / np.sqrt(n)
    # two-sided t crit, df = n-1, 95%
    tcrit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447,
             8: 2.365, 9: 2.306, 10: 2.262, 11: 2.228, 12: 2.201,
             13: 2.179}.get(n - 1, 1.96)
    return m, sd, m - tcrit * se, m + tcrit * se


def arm(chan, *, ideal, seed):
    w, us, dw = prepare(chan, ideal=ideal, adapt="probe", seed=seed)
    st = cell_stats(w, us, key="rate", period=PERIOD)
    tc = st["tuning"]
    alive = (tc > 1e-9).sum(axis=1)
    return {"osi": float(st["osi"].mean()), "alive_percell": alive,
            "n_dead": int((alive == 0).sum()), "dw": dw,
            "osi_percell": st["osi"]}


def main() -> int:
    print("=" * 78)
    print("RUNG 8D — CONFIRMATION. Pre-registered; prereg COMMITTED BEFORE THIS RUN.")
    print(provenance_line())
    print(f"  CONFIRMATORY SEEDS {CONFIRM_SEEDS[0]}-{CONFIRM_SEEDS[-1]} (n="
          f"{len(CONFIRM_SEEDS)}), declared in advance.")
    print("  13000-13999 NOT TOUCHED.  Composed (lateral) pathway. theta on PROBE.")
    print("=" * 78)

    rows = []
    for sd in CONFIRM_SEEDS:
        ai = arm("lateral", ideal=True, seed=sd)
        af = arm("lateral", ideal=False, seed=sd)
        rows.append({"seed": sd, "i": ai, "f": af,
                     "sep": ai["osi"] - af["osi"]})
        r = rows[-1]
        print(f"\n  seed {sd}")
        print(f"    IDEAL osi {ai['osi']:.4f}  alive/12 per cell "
              f"{list(map(int, ai['alive_percell']))}  n_dead {ai['n_dead']}  "
              f"max|dw| {ai['dw']:.1e}")
        print(f"    FLOOR osi {af['osi']:.4f}  alive/12 per cell "
              f"{list(map(int, af['alive_percell']))}  n_dead {af['n_dead']}  "
              f"max|dw| {af['dw']:.1e}")
        print(f"    SEPARATION {r['sep']:.4f}")

    ideal = np.array([r["i"]["osi"] for r in rows])
    floor = np.array([r["f"]["osi"] for r in rows])
    sep = np.array([r["sep"] for r in rows])

    print("\n" + "=" * 78)
    print("  THE PRE-REGISTERED STATISTIC (unit = SEED, n = %d)" % len(rows))
    print("=" * 78)
    for name, x in (("IDEAL", ideal), ("FLOOR", floor), ("SEPARATION", sep)):
        m, sd_, lo, hi = t_ci(x)
        print(f"  {name:<11s} mean {m:.4f}  sd {sd_:.4f}  95% CI [{lo:.4f}, {hi:.4f}]"
              f"   min {x.min():.4f}  max {x.max():.4f}")

    n_dead_tot = sum(r["i"]["n_dead"] + r["f"]["n_dead"] for r in rows)
    dw_max = max(max(r["i"]["dw"], r["f"]["dw"]) for r in rows)

    print("\n" + "=" * 78)
    print("  THE GATE — the CI must clear each threshold, not the point estimate")
    print("=" * 78)
    mi, _, lo_i, _ = t_ci(ideal)
    mf, _, _, hi_f = t_ci(floor)
    ms, _, lo_s, _ = t_ci(sep)
    checks = [
        ("G1 IDEAL >= 0.80      (CI lower)", lo_i >= 0.80, f"{lo_i:.4f}"),
        ("G2 FLOOR <= 0.50      (CI upper)", hi_f <= 0.50, f"{hi_f:.4f}"),
        ("G3 SEPARATION >= 0.30 (CI lower)", lo_s >= 0.30, f"{lo_s:.4f}"),
        ("G0 no dead arm (n_dead==0 all)  ", n_dead_tot == 0, f"{n_dead_tot} dead"),
        ("G4 weights frozen (max|dw|==0)  ", dw_max == 0.0, f"{dw_max:.1e}"),
    ]
    for nm, ok, val in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {nm}  {val}")
    ok = all(c[1] for c in checks)
    print(f"\n  GATE: {'PASS' if ok else 'FAIL'}")

    print("\n--- AGAINST RUNG 8C's n=1 POINT ESTIMATES (seed 0) ---")
    print(f"  8C IDEAL 1.0000 -> confirmation mean {ideal.mean():.4f}")
    print(f"  8C FLOOR 0.2304 -> confirmation mean {floor.mean():.4f}  "
          f"(prereg §5 predicted the DIGITS would NOT reproduce; sd across "
          f"seeds {floor.std(ddof=1):.4f})")
    print(f"  8C SEP   0.7696 -> confirmation mean {sep.mean():.4f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
