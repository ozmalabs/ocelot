"""RUNG 8E — H1 AND H2, THE CONFIRMATORY RUN. Pre-registered in
`VISION_RUNG8E_PREREG.md`, COMMITTED BEFORE THIS RUNS.

**CONFIRMATORY. Seeds 13000-13015 (n=16, declared in advance) — the block that
has been ALLOCATED, UNUSED and CLEAN through rungs 8, 8B, 8C and 8D. This run
spends them.**

Runs EXACTLY the pre-registered tests and nothing else (§3.6):

    Delta_arm   = OSI(trained, arm) - OSI(untrained, arm)   [paired, per seed]
    INTERACTION = Delta_lateral - Delta_degenerate           [SECONDARY, declared
                                                              UNDERPOWERED at n=16]
    SESOI = 0.0595

    H1 CONFIRMED  iff Delta_lateral > SESOI with a 95% CI excluding 0
    H1 NULL       iff Delta_lateral's 95% CI EXCLUDES the SESOI
    INCONCLUSIVE  iff the CI includes BOTH 0 and the SESOI
    H2 must be null (Delta_degenerate's CI must include 0)

Floors are measured IN-RUN, per arm, per seed. Per-cell aliveness and n_dead are
reported for every arm (§1 clause 4). `peak/base` is NOT read (§1.1).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.engine_provenance import provenance_line  # noqa: E402
from scripts.rung8d_confirm import t_ci  # noqa: E402
from scripts.rung8d_h1_power_pilot import ETA, SESOI, TRAIN, arm  # noqa: E402

CONFIRM_SEEDS = list(range(13000, 13016))    # DECLARED IN THE PREREG. n = 16.


def main() -> int:
    print("=" * 78)
    print("RUNG 8E — H1 / H2 CONFIRMATION. Prereg COMMITTED BEFORE THIS RUN.")
    print(provenance_line())
    print(f"  CONFIRMATORY SEEDS {CONFIRM_SEEDS[0]}-{CONFIRM_SEEDS[-1]} "
          f"(n={len(CONFIRM_SEEDS)}) — CLEAN through rungs 8/8B/8C/8D.")
    print(f"  eta={ETA:.0e} (FROZEN, rung 8's prereg), train={TRAIN} steps, "
          f"SESOI={SESOI}")
    print("=" * 78)

    data = {"lateral": [], "degenerate": []}
    dead_total = 0
    for sd in CONFIRM_SEEDS:
        print(f"\n  seed {sd}")
        for chan in ("lateral", "degenerate"):
            t = arm(chan, trained=True, seed=sd)
            u = arm(chan, trained=False, seed=sd)
            delta = t["osi"] - u["osi"]
            data[chan].append({"trained": t["osi"], "untrained": u["osi"],
                               "delta": delta, "t": t, "u": u})
            dead_total += t["n_dead"] + u["n_dead"]
            print(f"    {chan:<11s} trained {t['osi']:.4f} "
                  f"(alive {list(map(int, t['alive']))}, dead {t['n_dead']}, "
                  f"train|dw| {t['dw_train']:.4f}, probe|dw| {t['dw_probe']:.1e})")
            print(f"    {'':<11s} floor   {u['osi']:.4f} "
                  f"(alive {list(map(int, u['alive']))}, dead {u['n_dead']})"
                  f"   DELTA {delta:+.4f}")

    dl = np.array([r["delta"] for r in data["lateral"]])
    dd = np.array([r["delta"] for r in data["degenerate"]])
    inter = dl - dd

    print("\n" + "=" * 78)
    print("  THE PRE-REGISTERED STATISTIC (unit = SEED, n = %d)" % len(dl))
    print("=" * 78)
    for name, x in (("Delta_lateral (PRIMARY)", dl),
                    ("Delta_degenerate (H2)", dd),
                    ("INTERACTION (secondary,", inter)):
        m, s, lo, hi = t_ci(x)
        print(f"  {name:<24s} mean {m:+.4f}  sd {s:.4f}  "
              f"95% CI [{lo:+.4f}, {hi:+.4f}]")
    print("   ^ INTERACTION was DECLARED UNDERPOWERED at n=16 (needs n>=59).")

    print("\n  Arm means (context; the test is on the DELTAS):")
    for chan in ("lateral", "degenerate"):
        tr = np.array([r["trained"] for r in data[chan]])
        un = np.array([r["untrained"] for r in data[chan]])
        print(f"    {chan:<11s} trained {tr.mean():.4f} +- {tr.std(ddof=1):.4f}"
              f"   floor (IN-RUN) {un.mean():.4f} +- {un.std(ddof=1):.4f}")

    # ------------------------------------------------------------------ #
    #  THE PRE-REGISTERED DECISION RULE
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 78)
    print("  THE PRE-REGISTERED DECISION RULE")
    print("=" * 78)
    m_l, _, lo_l, hi_l = t_ci(dl)
    m_d, _, lo_d, hi_d = t_ci(dd)

    print(f"  G0 no dead arm (n_dead==0 everywhere): "
          f"{'PASS' if dead_total == 0 else 'FAIL'}  ({dead_total} dead)")

    h1_conf = (m_l > SESOI) and (lo_l > 0)
    h1_null = (hi_l < SESOI) or (lo_l > SESOI)
    h1_null = hi_l < SESOI            # CI excludes SESOI from below
    inconcl = (lo_l <= 0) and (hi_l >= SESOI)
    h2_null = (lo_d <= 0 <= hi_d)

    print(f"\n  H1: Delta_lateral = {m_l:+.4f}, 95% CI [{lo_l:+.4f}, {hi_l:+.4f}]"
          f"   SESOI = {SESOI}")
    if h1_conf:
        print("  => H1 CONFIRMED (Delta > SESOI and CI excludes 0)")
    elif inconcl:
        print("  => H1 INCONCLUSIVE (CI includes BOTH 0 and the SESOI) "
              "— reported as such, NOT as a null")
    elif h1_null:
        print("  => **H1 NULL** (the 95% CI EXCLUDES the SESOI)")
        print("     Decorrelated input is NOT sufficient. Rung 6's negative")
        print("     DEEPENS: the blocker is NOT the channels' correlation")
        print("     structure. This is a FINDING, not a failure.")
    else:
        print("  => H1: does not meet any pre-registered category — report raw.")

    print(f"\n  H2: Delta_degenerate = {m_d:+.4f}, 95% CI [{lo_d:+.4f}, {hi_d:+.4f}]")
    print(f"  => H2 {'NULL (CI includes 0) — the control is VALID' if h2_null else 'NOT NULL — THE CONTROL IS INVALID and NEITHER hypothesis is interpretable'}")
    print(f"     (and it is NOT null-for-a-trivial-reason: the degenerate arm's")
    print(f"      weights move ~58% during training — measured, prereg §3.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
