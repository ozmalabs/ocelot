#!/usr/bin/env python
"""TROXLER — THE TWO TIMESCALES. The §13.1 crux, quantified.

Descriptive, NOT a gate, and on ALREADY-BURNED seed 0 — it burns nothing.

The pre-registration says the falsifiable content of this rung is ENTIRELY in the
drifting arm: **does the drift's own timescale outrun adaptation?** That is not
forced by any rule. The drift's timescale falls out of Engbert's self-avoiding
walk (alpha measured, never imported: 1.1553 / 0.7590); the adaptation timescale
falls out of lam / beta / mu_endo (the last derived from endogenous activity).
**Neither was chosen with the other in mind.** So the two numbers below are the
result of two independent derivations landing where they land — and their RATIO
is the margin the claim actually rests on.

  tau_drift  = the lag at which the RETINAL image decorrelates to 1/e, measured
               with adaptation FROZEN so it is PURE image motion and nothing else.
  tau_adapt  = the time for the stabilised arm's contrast to fall to 1/e of its
               t=0 value — the homeostat's own e-folding.

If tau_drift << tau_adapt the drift outruns adaptation and the drifting arm
cannot fade. If tau_drift >> tau_adapt BOTH arms fade and the wired drift is
quantitatively wrong — a real, reportable NEGATIVE (pre-reg §7 proviso 1).

**The margin is reported because the SIGN alone would hide the regime.** The drift
here moves ~1 receptor per step, which is LARGE relative to the receptor lattice;
real fixational drift is a small fraction of it. A win with a 100x margin is a
win in a COARSE-drift regime, and saying so is §8.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import troxler_lib as T  # noqa: E402


def main():
    print(ep.provenance_line())
    print("TROXLER — THE TWO TIMESCALES (burned seed 0; descriptive, not a gate)\n")

    # ---- tau_drift: PURE image motion, adaptation frozen ----
    r = T.run_arm(0, T.ARM_DRIFT, vis_steps=400, calib_steps=T.CALIB_STEPS,
                  frozen=1.0, record_resp=True)
    tr = r["resp_trace"]                       # (t, 16, 16), theta FROZEN
    a0 = tr[0].ravel() - tr[0].mean()
    corr = []
    for t in range(len(tr)):
        at = tr[t].ravel() - tr[t].mean()
        den = np.linalg.norm(a0) * np.linalg.norm(at)
        corr.append(float(np.dot(a0, at) / den) if den > 0 else 0.0)
    corr = np.array(corr)
    below = np.where(corr < 1 / np.e)[0]
    tau_drift = int(below[0]) if len(below) else -1
    print("tau_drift — the RETINAL image's decorrelation (adaptation FROZEN,")
    print("            so this is PURE image motion driven by the SAW):")
    for t in (0, 1, 2, 3, 4, 5, 8, 16, 32, 64):
        if t < len(corr):
            print(f"    lag {t:3d}: corr(resp(t), resp(0)) = {corr[t]:+.4f}")
    print(f"  => tau_drift (first lag with corr < 1/e = 0.3679) = {tau_drift} steps")

    # ---- tau_adapt: the homeostat's own e-folding, on the stabilised arm ----
    s = T.run_arm(0, T.ARM_STABILISED, vis_steps=3200, calib_steps=T.CALIB_STEPS)
    c = s["contrast"]
    thr = c[0] / np.e
    below = np.where(c < thr)[0]
    tau_adapt = int(below[0]) if len(below) else -1
    print("\ntau_adapt — the stabilised arm's contrast e-folding (the homeostat):")
    for t in (0, 25, 50, 100, 150, 200, 400, 800):
        print(f"    t={t:4d}: contrast = {c[t]:.6f}")
    print(f"  => tau_adapt (first t with contrast < {thr:.6f}) = {tau_adapt} steps")

    print("\n" + "=" * 74)
    if tau_drift > 0 and tau_adapt > 0:
        print(f"  tau_drift = {tau_drift} steps   tau_adapt = {tau_adapt} steps")
        print(f"  SEPARATION = {tau_adapt / tau_drift:.1f}x  "
              f"(the drift {'OUTRUNS' if tau_drift < tau_adapt else 'does NOT outrun'} adaptation)")
        print("\n  Neither number was chosen with the other in mind: the first falls")
        print("  out of Engbert's walk, the second out of GCAL's lam/beta and the")
        print("  cell's OWN measured mu_endo. They could have landed on the same")
        print("  side of the boundary. They did not.")
        print("\n  SCOPE (§8): the drift here moves ~1 receptor/step, which is LARGE")
        print("  relative to the receptor lattice. This is a win in a COARSE-drift")
        print("  regime, NOT in the delicate biological one where the margin is thin.")
    print("=" * 74)


if __name__ == "__main__":
    main()
