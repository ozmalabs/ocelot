#!/usr/bin/env python
"""POWER PILOT + INSTRUMENT CHECK for the endogenous-setpoint arm.

PROTOCOL §3.3: n is FIXED IN ADVANCE by a power analysis on a pilot restricted
to ALREADY-BURNED seeds. This burns seeds 0-5 only (0-13 are long burned; see
the ledger). NO confirmatory seed is touched here, and the confirmatory block
(14000-14999) is declared in VISION_SETPOINT_PREREG.md before this runs.

Also runs the INSTRUMENT CHECK: arm A0 = FM-1b's exact protocol (no wave phase,
mu=0.024) on seed 0, which must reproduce FM-1b's published min aliveness 10.5%
/ max theta 0.4603. If it does not, the runner is not measuring what FM-1b
measured and nothing downstream is comparable.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

from eye_setpoint_lib import run_arm  # noqa: E402

PILOT_SEEDS = [0, 1, 2, 3, 4, 5]     # already burned (ledger: 0-13)


def main():
    print(ep.provenance_line())
    print("SETPOINT POWER PILOT — burned seeds only:", PILOT_SEEDS)
    print()

    # ---- INSTRUMENT CHECK: reproduce FM-1b's arm A ----------------------
    print("INSTRUMENT CHECK — FM-1b's exact protocol (no wave phase, mu=0.024),")
    print("seed 0. FM-1b published: min aliveness 10.5%, max theta 0.4603,")
    print("final mean resp 0.024958, t=0 mean resp 0.398910.")
    a0 = run_arm(0, mu_mode=0.0, no_waves=True)
    print(f"  reproduced: min aliveness {a0['min_alive']*100:.1f}% "
          f"(at t={a0['argmin_alive']}), max theta(mean) {a0['max_theta_mean']:.4f},")
    print(f"              final mean resp {a0['final_mean_resp']:.6f}, "
          f"t=0 mean resp {a0['t0_mean_resp']:.6f}")
    ok = (abs(a0["min_alive"] - 0.105) < 0.02
          and abs(a0["max_theta_mean"] - 0.4603) < 0.01
          and abs(a0["final_mean_resp"] - 0.024958) < 1e-4
          and abs(a0["t0_mean_resp"] - 0.398910) < 1e-4)
    print(f"  => reproduces FM-1b: {ok}")
    print()

    # ---- THE PILOT ------------------------------------------------------
    rows = {"A": [], "B": []}
    for sd in PILOT_SEEDS:
        a = run_arm(sd, mu_mode=0.0)
        b = run_arm(sd, mu_mode=1.0)
        rows["A"].append(a)
        rows["B"].append(b)
        print(f"  seed {sd:2d}: mu_endo={b['mu_endo']:.6f} | "
              f"A min_alive={a['min_alive']*100:5.1f}% maxth={a['max_theta_mean']:.4f} | "
              f"B min_alive={b['min_alive']*100:5.1f}% maxth={b['max_theta_mean']:.4f}")

    print()
    for k in ("A", "B"):
        v = np.array([r["min_alive"] for r in rows[k]])
        print(f"ARM {k}: min_alive mean={v.mean():.4f} sd={v.std(ddof=1):.4f} "
              f"range=[{v.min():.4f}, {v.max():.4f}]")
    mu = np.array([r["mu_endo"] for r in rows["B"]])
    print(f"mu_endo across seeds: mean={mu.mean():.6f} sd={mu.std(ddof=1):.6f} "
          f"range=[{mu.min():.6f}, {mu.max():.6f}]")

    a = np.array([r["min_alive"] for r in rows["A"]])
    b = np.array([r["min_alive"] for r in rows["B"]])
    d = b - a
    print()
    print(f"PAIRED DIFFERENCE (B - A) on min_alive: mean={d.mean():+.4f} "
          f"sd={d.std(ddof=1):.4f}")
    if d.std(ddof=1) > 0:
        dz = d.mean() / d.std(ddof=1)
        print(f"  Cohen's dz = {dz:.3f}")
        # n for 80% power, two-sided alpha=0.05, paired t: n ~ (1.96+0.84)^2/dz^2
        n80 = (2.80 ** 2) / (dz ** 2) if dz != 0 else float("inf")
        print(f"  n for 80% power (two-sided a=0.05) = {np.ceil(n80):.0f} seeds")
    else:
        print("  sd = 0 — the difference is DETERMINISTIC across seeds.")
        print("  A paired t-test is undefined/degenerate at sd=0. The pre-reg")
        print("  must therefore NOT use a t-test; see VISION_SETPOINT_PREREG.md.")


if __name__ == "__main__":
    main()
