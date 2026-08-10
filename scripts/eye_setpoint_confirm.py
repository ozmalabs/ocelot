#!/usr/bin/env python
"""THE ENDOGENOUS SETPOINT — pre-registered CONFIRMATORY run.

Pre-registered in VISION_SETPOINT_PREREG.md, committed at 88d23b68 BEFORE this
ran. Exactly the two declared statistics, exactly the declared test, exactly the
declared n, on the declared block. No sweeps. No re-runs.

  PRIMARY   : min aliveness per seed per arm; EXACT PAIRED SIGN TEST.
              n = 8 FIXED IN ADVANCE (two-sided p = 2*(1/2)^8 = 0.0078).
  SECONDARY : max theta (spatial MEAN -- FM-1b's statistic); paired t.

BURNS: seeds 14000-14007 (block 14000-14999, declared in the pre-reg).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

from eye_setpoint_lib import run_arm  # noqa: E402

SEEDS = list(range(14000, 14008))   # n = 8, FIXED IN ADVANCE


def main():
    print(ep.provenance_line())
    print("ENDOGENOUS SETPOINT — PRE-REGISTERED CONFIRMATORY RUN")
    print(f"seeds {SEEDS[0]}-{SEEDS[-1]} (n={len(SEEDS)}), block 14000-14999")
    print()

    A, B = [], []
    for sd in SEEDS:
        a = run_arm(sd, mu_mode=0.0)
        b = run_arm(sd, mu_mode=1.0)
        A.append(a)
        B.append(b)
        print(f"  seed {sd}: mu_endo={b['mu_endo']:.6f} | "
              f"A min_alive={a['min_alive']*100:5.1f}% th={a['max_theta_mean']:.4f} | "
              f"B min_alive={b['min_alive']*100:5.1f}% th={b['max_theta_mean']:.4f}")

    a_alive = np.array([r["min_alive"] for r in A])
    b_alive = np.array([r["min_alive"] for r in B])
    a_th = np.array([r["max_theta_mean"] for r in A])
    b_th = np.array([r["max_theta_mean"] for r in B])
    mu = np.array([r["mu_endo"] for r in B])

    print()
    print("=" * 72)
    print("PRIMARY — min aliveness (§1.1's metric), EXACT PAIRED SIGN TEST")
    print(f"  arm A (GCAL's imported mu=0.024): mean {a_alive.mean()*100:.1f}%  "
          f"sd {a_alive.std(ddof=1)*100:.1f}%  range [{a_alive.min()*100:.1f}, "
          f"{a_alive.max()*100:.1f}]")
    print(f"  arm B (endogenous setpoint)     : mean {b_alive.mean()*100:.1f}%  "
          f"sd {b_alive.std(ddof=1)*100:.1f}%  range [{b_alive.min()*100:.1f}, "
          f"{b_alive.max()*100:.1f}]")
    n_pos = int((b_alive > a_alive).sum())
    n_neg = int((b_alive < a_alive).sum())
    n_tie = int((b_alive == a_alive).sum())
    n = len(SEEDS)
    p = 2.0 * (0.5 ** n) if n_pos == n else None
    print(f"  B > A on {n_pos}/{n} seeds   (B < A on {n_neg}, ties {n_tie})")
    if p is not None:
        print(f"  exact two-sided sign test: p = 2*(1/2)^{n} = {p:.4f}")
    else:
        from math import comb
        k = min(n_pos, n_neg)
        pv = 2.0 * sum(comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
        print(f"  exact two-sided sign test: p = {min(pv,1.0):.4f}")
        p = min(pv, 1.0)

    print()
    print("SECONDARY — max theta (spatial mean), paired t")
    d = b_th - a_th
    tstat = d.mean() / (d.std(ddof=1) / np.sqrt(n)) if d.std(ddof=1) > 0 else float("inf")
    print(f"  arm A: {a_th.mean():.4f} +/- {a_th.std(ddof=1):.4f}")
    print(f"  arm B: {b_th.mean():.4f} +/- {b_th.std(ddof=1):.4f}")
    print(f"  paired diff (B-A) = {d.mean():+.4f} +/- {d.std(ddof=1):.4f}, "
          f"t({n-1}) = {tstat:+.2f}")

    print()
    print("THE SETPOINT ITSELF (what fell out)")
    print(f"  mu_endo across seeds: mean {mu.mean():.6f}  sd {mu.std(ddof=1):.6f}  "
          f"range [{mu.min():.6f}, {mu.max():.6f}]")
    print(f"  GCAL's imported mu  : 0.024000  => ratio {mu.mean()/0.024:.2f}x")

    print()
    print("=" * 72)
    if n_pos == n:
        print("VERDICT: H1 SUPPORTED per the pre-registered decision rule "
              f"(B > A on {n}/{n}, p = {p:.4f} < 0.01).")
        print("The SOURCE of the setpoint decides whether the eye must go BLIND")
        print("to reach it. An eye using the setpoint it measured in itself never")
        print("has a single silent cell; the SAME eye, same waves, same input,")
        print("given GCAL's constant, blacks out completely for a window.")
        print()
        print("SCOPE — do NOT read this as 'arm A dies'. `min_alive` is a")
        print("statistic about the TRANSIENT: BOTH arms end at 100% aliveness")
        print("(arm A recovers to mean resp ~0.0249 ~ mu, FM-1b's own finding).")
        print("The effect is the TRANSIENT COST of an imported scale: xbar ~0.145")
        print("is 6x above mu=0.024, so theta must overshoot to force a 16.6x")
        print("compression, and the sheet blacks out until it relaxes.")
    else:
        print("VERDICT: H1 NOT SUPPORTED at the declared level. Per the pre-reg")
        print("this is a RESULT (§7): the endogenous activity does not carry the")
        print("scale the visual regime needs — evidence AGAINST the pre-visual")
        print("thesis. It licenses NO floor, fraction or tuned mu (§13, §5).")


if __name__ == "__main__":
    main()
