"""RUNG 4 — THE CONFIRMATORY RUN. Exactly the two pre-registered tests.

VISION_RUNG4_PREREG.md, committed before this ran. No sweeps. No re-runs.

  H1  d_on          = smoothness(lateral=1) - shuffled-position null   two-sided
  H2  d_on - d_off  = the INTERACTION (the mechanism test)             two-sided

BUILT iff both pass at Bonferroni alpha=0.025. n=70 FIXED IN ADVANCE by the
pilot on burned seeds. Seeds 5000-5069, never used for anything.

Waves only — NO vision in either arm. The arms differ ONLY in MapParams.lateral,
which is graph data the agent holds.
"""
from __future__ import annotations

import json
import sys

import numpy as np

from rung4_lib import ETA, GH, GW, STEPS, arm, report

SEEDS = list(range(5000, 5070))          # n = 70, FIXED IN ADVANCE


def main():
    on, off, sel_on, sel_off = [], [], [], []
    for sd in SEEDS:
        a = arm(1.0, sd)
        b = arm(0.0, sd)
        on.append(a["d"])
        off.append(b["d"])
        sel_on.append(a["selectivity"])
        sel_off.append(b["selectivity"])
        print(f"  seed {sd}: d_on {a['d']:+7.2f}  d_off {b['d']:+7.2f}  "
              f"diff {a['d'] - b['d']:+7.2f}")
        sys.stdout.flush()

    on = np.asarray(on)
    off = np.asarray(off)
    sel_on = np.asarray(sel_on)
    sel_off = np.asarray(sel_off)
    inter = on - off

    print(f"\n{'=' * 78}")
    print(f"RUNG 4 CONFIRMATORY — n={len(SEEDS)} seeds ({SEEDS[0]}-{SEEDS[-1]}), "
          f"{STEPS} steps, waves only, {GH}x{GW} sheet, oja eta={ETA}")
    print(f"{'=' * 78}\n")

    print("THE TWO PRE-REGISTERED TESTS (Bonferroni alpha=0.025 each):")
    h1 = report("H1  d_on", on)
    h2 = report("H2  interaction (d_on - d_off)", inter)

    p1 = h1["p"] < 0.025 and h1["mean"] < 0
    p2 = h2["p"] < 0.025 and h2["mean"] < 0
    print(f"\n  H1 {'PASS' if p1 else 'FAIL'}   H2 {'PASS' if p2 else 'FAIL'}")
    print(f"  DECISION: {'*** BUILT ***' if (p1 and p2) else 'NOT BUILT'}")

    print("\nPRE-COMMITTED DESCRIPTIVES (not tests, no alpha spent):")
    report("  d_off (the ablation arm)", off)
    print(f"  {'mean selectivity':32s} on {sel_on.mean():.4f}   "
          f"off {sel_off.mean():.4f}   gap {sel_on.mean() - sel_off.mean():+.4f}")
    gap = sel_on - sel_off
    r = float(np.corrcoef(gap, inter)[0, 1])
    print(f"  {'corr(selectivity gap, interaction)':32s} r = {r:+.3f}")
    print("    (THE NAMED PROVISO: a strongly negative r means the interaction "
          "is\n     substantially readout-cleanliness, not co-tuning. See the prereg.)")

    print(f"\n  arms: d_on {on.mean():.2f} | d_off {off.mean():.2f}  (degrees; "
          "0 = chance, negative = smoother than chance)")

    with open("../results/rung4_confirm.json", "w") as f:
        json.dump({"seeds": SEEDS, "d_on": on.tolist(), "d_off": off.tolist(),
                   "sel_on": sel_on.tolist(), "sel_off": sel_off.tolist(),
                   "H1": h1, "H2": h2, "corr_gap_interaction": r,
                   "built": bool(p1 and p2)}, f, indent=1)


if __name__ == "__main__":
    main()
