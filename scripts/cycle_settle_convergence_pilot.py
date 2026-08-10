"""EXPLORATORY convergence pilot — is the settling loop's §2 question ANSWERABLE
now that `run_rules` can terminate on it?

**STATUS: EXPLORATORY, on BURNED seed 0 only. NOT a confirmatory arm; no seed
from the 23000 block is consumed here.** Per PROTOCOL §3, a pilot on an
already-burned seed is what informs a future power analysis — it makes no
claim that needs pre-registration.

WHAT THIS MEASURES (§2)
-----------------------
The settling loop is now BUILT (`seeds/vision_settle.json`), LOAD-ORDERED so it
is load-bearing (`settle_lib` boots `vision_settle` BEFORE `vision_onoff`, so
`st_settle` relaxes `act` before `oo_sunit_rate` reads it — settling is NOT
vacuous), and — with cycle detection — TERMINABLE. §2 asks: does the
DEVELOPMENTAL learning loop that reads the settled sheet converge on its own
formative input? drift(t) = ‖w(t) − w(t−Δ)‖ / ‖w(t)‖ should fall toward 0 if it
converges, stay high if it runs away, and plateau at ~0 structure if it dies.

WHY THE SLOW PATH (and what that costs)
---------------------------------------
`wave_world.step()` calls `s.tick(200_000)` internally and does NOT thread
`detect_cycles` — it is shared infrastructure this rung does not edit (PROTOCOL
§11 rule 4; the change is REPORTED for the supervisor to sequence, not made
here). So each developmental step burns the cap on the settling dither AFTER the
one-shot learning rule has already fired. **The learning TRAJECTORY is identical
either way** — the guarded `oo_learn` rule fires once per step regardless of how
long the settling dithers afterward — so this SLOW path measures the true
trajectory; cycle detection would only make it ~30000× faster and is what makes
the full 3200-step / GCAL-scale version tractable. That is exactly the value of
the fix for the science: it makes this question askable at scale.

WHAT IS NOT CLAIMED
-------------------
* ONE η (the committed default 5e-4) and ONE seed. This is a pilot, not the
  η-sweep. 8D's question — is there an η at which the rule is BOTH convergent and
  load-bearing? — needs its own pre-registration, a power analysis, the 23000
  confirmatory block, AND the `wave_world.step` opt-in. This pilot only says
  whether the question is now worth pre-registering.
* ρ(M) → 1 as the sheet grows is UNFIXED by any of this (n_side kept small here
  precisely because a GCAL-scale sheet settles arbitrarily slowly regardless of
  termination). A converging small sheet is NOT the ceiling moving.
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

from scripts.rung8b_lib import weights_of  # noqa: E402
from scripts.settle_lib import build_sheet  # noqa: E402


def convergence_trace(*, eta, n_side=3, connectivity=8, steps=160, delta=20,
                      seed=0):
    """drift(t) = ‖w(t) − w(t−Δ)‖/‖w(t)‖ and ‖w‖ over developmental time."""
    w, us, _ = build_sheet(seed=seed, n_side=n_side, connectivity=connectivity,
                           settle=1.0, bubble=0.0, eta=eta)
    hist = []
    prev = np.asarray(weights_of(w, us), dtype=float)
    w0 = float(np.linalg.norm(prev))
    for t in range(1, steps + 1):
        w.step(ignite_k=1 if t % 5 == 0 else 0)
        if t % delta == 0:
            cur = np.asarray(weights_of(w, us), dtype=float)
            nrm = float(np.linalg.norm(cur))
            drift = float(np.linalg.norm(cur - prev)) / (nrm if nrm > 0 else 1.0)
            hist.append((t, nrm, drift))
            prev = cur
    return {"eta": eta, "w0": w0, "hist": hist}


def main():
    print(provenance_line())
    print()
    print("EXPLORATORY §2 CONVERGENCE PILOT — burned seed 0, default η=5e-4")
    print("=" * 72)
    eta = 5e-4
    t0 = time.time()
    r = convergence_trace(eta=eta)
    print(f"  ‖w(0)‖ = {r['w0']:.4f}")
    print(f"  {'step':>5} {'‖w‖':>12} {'drift = ‖Δw‖/‖w‖':>18}")
    for (t, nrm, drift) in r["hist"]:
        print(f"  {t:>5} {nrm:>12.4f} {drift:>18.6f}")
    drifts = [d for _, _, d in r["hist"]]
    norms = [n for _, n, _ in r["hist"]]
    print()
    print(f"  first drift = {drifts[0]:.6f}   last drift = {drifts[-1]:.6f}")
    trend = "FALLING (→ convergent)" if drifts[-1] < 0.5 * drifts[0] else \
            "FLAT/RISING (not converging on this horizon)"
    print(f"  drift trend: {trend}")
    exploded = norms[-1] > 10 * r["w0"] + 1e-9
    print(f"  ‖w‖ {norms[0]:.3f} → {norms[-1]:.3f}  "
          f"({'RUNS AWAY' if exploded else 'bounded'})")
    print(f"  ({time.time() - t0:.1f}s on the slow cap-burning path)")
    print()
    print("  READING: exploratory only. A falling, bounded drift says the §2")
    print("  question is worth a proper pre-registration (η-sweep, fresh seeds,")
    print("  wave_world.step opt-in). A flat/exploding drift says the learning")
    print("  rule has no operating regime at this η — 8D's tension, unresolved.")


if __name__ == "__main__":
    main()
