"""PART 1B — THE ZERO-MEAN ARMS DID NOT CONVERGE BY 6400. WHERE ARE THEY GOING?

PART 1 measured, out to 6400 steps on waves alone:

  DC    : drift 1.79 -> 0.113 (falling) ; anisotropy plateaus ~0.29 ;
          DC frac stays 0.95-0.998 ; frac(w<0) = 0.0000 THROUGHOUT
  ZERO  : drift ~0.20-0.25, NOT falling ; anisotropy stuck at the 0.1525 random
          floor ; DC frac RISING 0.022 -> 0.110 ; frac(w<0) FALLING 0.502 -> 0.455
  ZEROM : drift ~0.29, NOT falling ; anisotropy 0.153 -> 0.240 (rising) ;
          DC frac RISING 0.022 -> 0.428 ; frac(w<0) FALLING 0.502 -> 0.272

Under PROTOCOL 2 the zero-mean arms are TRANSIENTS at 6400 and no fixed-point
claim may be read off them. But the DIRECTION of travel is unambiguous and it is
the same in both, at two different norms: **toward the DC mode**, monotonically.

THIS IS THE PREDICTION'S OWN MECHANISM, TESTABLE. If Oja's attractor on this
input is the leading eigenvector of the non-negative second-moment matrix
E[xx^T], then Perron-Frobenius says that eigenvector is NON-NEGATIVE, and the
zero-mean arms must be travelling to the SAME fixed point the DC arm sits at —
just from much further away. Then:

  * the DC prior is a HEAD START, not a different destination;
  * the committed default is where the rule was going anyway;
  * and rung 5's blindness is a property of the INPUT + the rule, not the init.

The alternative — the zero-mean arms settle somewhere else, signed and
structured — would mean the init picks the attractor, and rung 5's root cause is
an adapter artifact after all.

**Completing PROTOCOL 2's check at an adequate horizon is not a sweep.** No
parameter is searched: eta stays 5e-4, the input stays waves. The horizon is
extended because 6400 was measured to be too short to answer the question 2
asks ("does the rule settle?"). Reported either way.
"""
from __future__ import annotations

import numpy as np

from scripts.w0_ablation_lib import (build, run_waves, weights_of, drift,
                                     rf_stats, pmap)
from domains.engine_provenance import provenance_line

CKPTS = [0, 3200, 6400, 12800, 25600, 51200]
N_SEEDS = 4                    # seeds 0-3: BURNED. A dynamics measurement, n=4.


def _run(a):
    """(seed, arm) -> per-checkpoint stats. Pool entry point."""
    seed, arm = a
    w, us = build(seed, arm)
    prev = weights_of(w, us)
    out, done = [], 0
    for c in CKPTS:
        if c > done:
            run_waves(w, c - done)
            done = c
        cur = weights_of(w, us)
        st = rf_stats(w, us)
        st["drift"] = drift(prev, cur) if c else float("nan")
        out.append(st)
        prev = cur
    return out


if __name__ == "__main__":
    print(provenance_line())
    print("=" * 78)
    print("PART 1B — LONG-HORIZON CONVERGENCE. Do the zero-mean arms reach the")
    print("          DC arm's fixed point? n=4 BURNED seeds (0-3), eta=5e-4 FROZEN")
    print("=" * 78)
    for arm in ("DC", "ZERO", "ZEROM"):
        rows = pmap(_run, [(s, arm) for s in range(N_SEEDS)], procs=4)
        print(f"\n--- {arm}")
        print(f"{'steps':>6s} {'anisotropy':>11s} {'drift':>8s} {'DC frac':>9s} "
              f"{'frac(w<0)':>10s} {'||w||':>8s}")
        for i, c in enumerate(CKPTS):
            a = {k: float(np.nanmean([r[i][k] for r in rows]))
                 for k in rows[0][i]}
            print(f"{c:6d} {a['anis']:11.4f} {a['drift']:8.4f} "
                  f"{a['dc_frac']:9.4f} {a['frac_neg']:10.4f} {a['norm']:8.3f}")
