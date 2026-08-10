"""RUNG 6 — CONVERGENCE (PROTOCOL 2), on burned seeds (3000-3011 block reused).

"Before any experience/ablation arm is run, measure: does the rule SETTLE?"
This single check explains nine failed attempts. Run it FIRST.

  CONVERGENT + USEFUL : OSI plateaus at non-zero AND drift -> 0
  never converges     : the scaffold is a TRANSIENT; every arm is measured at an
                        arbitrary point on a decay curve  => STOP
  converges to death  : drift -> 0 at floor structure      => STOP

Formative input ONLY (the agent's own waves). Drift = ||w(t)-w(t-D)||/||w(t)||.
"""
from __future__ import annotations

import numpy as np

from scripts.rung6_lib import build, run_waves, osi_of, adapt_theta
from domains.onoff_world import set_params, weights, segregation

CHECKPOINTS = [400, 800, 1600, 3200, 6400]


def line(k, v):
    print(f"  {k:<40s} {v}")


print("=" * 78)
print("RUNG 6 CONVERGENCE — does the rule settle on ITS OWN input (waves)?")
print("=" * 78)

for subnorm, tag in ((1.0, "MILLER subtractive"), (0.0, "plain OJA")):
    for eta in (5e-4, 1e-4):
        print(f"\n--- {tag}  eta={eta:g} ---")
        w, us, _ = build(seed=3000, n_units=6, subnorm=subnorm, eta=eta)
        adapt_theta(w, 400)
        set_params(w, oo_eta=eta, frozen=0.0)
        prev = weights(w, us).copy()
        done = 0
        for cp in CHECKPOINTS:
            run_waves(w, cp - done)
            done = cp
            cur = weights(w, us)
            drift = float(np.linalg.norm(cur - prev) / max(np.linalg.norm(cur), 1e-12))
            nan = int(np.isnan(cur).sum())
            o, st = osi_of(w, us)
            set_params(w, frozen=0.0)          # un-freeze to continue training
            pk = st["tuning"].max(axis=1)
            bs = np.maximum(st["baseline"], 1e-9)
            clump = float(np.mean([segregation(w, u)["clumpiness"] for u in us]))
            line(f"{cp:5d} steps  OSI",
                 f"{o.mean():.4f}  drift {drift:.4f}  NaN {nan}  "
                 f"peak/base {(pk/bs).mean():9.2f}  clump {clump:.3f}")
            prev = cur.copy()
