"""RUNG 8D — PILOT: DOES THE PER-CELL PROBE SEPARATE BY SELECTIVITY OR BY DRIVE?

**§1 CALIBRATION PILOT on already-burned seeds (0 / 3000), for a power/feasibility
read before pre-registration (§3.3: "a pilot restricted to already-burned
seeds"). NO confirmatory seed. NO hypothesis is tested here.**

THE CHARGE (the supervisor's, and it is the right one)
-------------------------------------------------------
    "The sweep's separation was by DRIVE, not selectivity ... Your calibrated
     probe must be shown to separate by SELECTIVITY. Prove it — do not inherit
     it."

Rung 8C's `rung8c_drive_audit.py` measured that a FLOOR cell carries **9.5x** an
IDEAL cell's drive, and correctly killed its own GLOBAL-theta sweep with it: a
global theta placed for a drive-2.18 cell leaves a drive-20.75 cell unsliced, so
that sweep separated cells by DRIVE. **That verdict is about a GLOBAL theta.**
Rung 8C's actual gate uses rung 6's PER-CELL theta, and whether THAT separates
by drive is a DIFFERENT question which nobody has asked. This asks it.

THE ANALYTIC CLAIM I AM TESTING (stated first, then measured — §12.4)
----------------------------------------------------------------------
Read off the two seed rules:

    rate  = max(act - theta, 0)                       (`oo_sunit_rate`)
    theta <- theta + theta_rate * (act - theta)       (`oo_sunit_adapt_theta`)

theta's update is **LINEAR in act** and its init is 0, so theta is a linear
functional of the act sequence. Therefore, for any constant k > 0, scaling a
cell's weights by k scales its drive by k and:

    act -> k*act  =>  theta -> k*theta
    rate -> max(k*act - k*theta, 0) = k*max(act - theta, 0) = k*rate
    tc   -> k*tc
    osi  =  (k*a - k*b)/(k*a + k*b) = (a - b)/(a + b)   **UNCHANGED**

**So a PER-CELL EMA theta makes OSI EXACTLY SCALE-INVARIANT in the drive, and
the 9.5x gap is divided out BY CONSTRUCTION.** That is precisely what a global
theta cannot do, and it is why the drive audit's verdict does not transfer.

**But an analytic claim about a rule is not a measurement of the system** (the
`mu_endo` premise was analytic too, and false). Non-linearities elsewhere could
break it: `oo_wmax` clipping, `subnorm`, the retina's own gain, or a theta that
has not converged in 2000 steps. **So I MEASURE it, and the measurement can
falsify it.**

THE DESIGN — A DRIVE-MATCHED CONTROL, WHICH RUNG 8C NEVER RAN
--------------------------------------------------------------
Four arms. The two middle ones are the point: they put the IDEAL cell at the
FLOOR's drive and the FLOOR cell at the IDEAL's drive, by scaling weights only.

    A1  ideal, x1        drive ~2.18   (rung 8C's ideal arm)
    A2  ideal, x9.51     drive ~20.75  == THE FLOOR'S DRIVE
    A3  floor, x1        drive ~20.75  (rung 8C's floor arm)
    A4  floor, x(1/9.51) drive ~2.18   == THE IDEAL'S DRIVE

**A2 vs A3 is the decisive pair: two cells at the SAME drive.** If they still
separate, the separation cannot be drive — there is no drive difference left to
carry it.

MY PREDICTION, IN ADVANCE, WITH PROVISOS (§3.7)
------------------------------------------------
**I predict OSI is INVARIANT under the scaling to within numerical noise**:
A1 == A2 == 1.0000 and A3 == A4 == 0.2304, so the separation at MATCHED drive
(A2 vs A3) equals the separation at unmatched drive (A1 vs A3) = 0.7696.
**=> the probe separates by SELECTIVITY.**

Provisos, each of which tells me what I did not understand if it breaks:
 1. **If OSI MOVES under scaling**, the analytic argument is wrong — something
    downstream of theta is NOT linear (wmax clipping is the prime suspect, then
    the retina's gain). The probe would then be drive-contaminated and rung 8C's
    gate would NOT be rescued. This is the outcome that kills the gate, and it
    is a real possibility, not a strawman.
 2. **If A2's drive does not actually land near the floor's 20.75**, the match
    failed and A2-vs-A3 is not a matched comparison — the arm is void, not
    passed. **I therefore MEASURE and REPORT the achieved drive of every arm**
    rather than assuming the scaling did what I asked.
 3. **If theta has not converged**, scale-invariance holds only approximately;
    I report |dtheta| over the last stretch to show it has.
 4. **This proves the probe separates by selectivity. It says NOTHING about
    H1/H2** — whether waves DEVELOP selectivity is untouched, and my prediction
    there stays NULL.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.complex_cells import cell_stats  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from domains.onoff_world import set_params  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    PERIOD, build, develop_retina, freeze_all, ideal_split_gabor,
)
from scripts.rung8b_lib import grating_ensemble, theta_of, weights_of  # noqa: E402
from scripts.rung8c_ensemble_transfer import N_UNITS, adapt_theta_on_probe  # noqa: E402
from domains.complex_cells import binarize, grating, present  # noqa: E402

ADAPT = 2000


def scale_weights(world, us, k: float) -> None:
    """Multiply every SUnit synapse's weight by k. Mechanical: the ONLY thing
    this changes is the cell's DRIVE. The RF's SHAPE — hence its selectivity —
    is identical, because every weight is scaled by the SAME constant."""
    for u in us:
        for sy in world.s.in_neighbours(u, "oo_post"):
            w = float(world.s.node(sy)["attrs"]["weight"])
            world.s.set_attr(sy, "weight", w * k)


def mean_drive(world, us, *, seed=11, n=64):
    """The cell's mean `act` over the PROBE ensemble — rung 8C's drive audit's
    own statistic, measured here per arm rather than inherited."""
    rng = np.random.default_rng(seed)
    acc = np.zeros(len(us))
    for _ in range(n):
        present(world, grating_ensemble(world, rng))
        acc += np.array([float(world.s.node(u)["attrs"]["act"]) for u in us])
    return acc / n


def arm(chan, *, ideal: bool, k: float, seed=0):
    w, us, _a, _b = build(seed=seed, n_units=N_UNITS, channels=chan)
    develop_retina(w, 3000)
    if ideal:
        for u in us:
            ideal_split_gabor(w, u, theta=0.0, phase=0.0)
    if k != 1.0:
        scale_weights(w, us, k)          # DRIVE changes; RF SHAPE does not.
    wt0 = weights_of(w, us)
    adapt_theta_on_probe(w, ADAPT)
    th_mid = theta_of(w).mean()
    # Convergence evidence: settle a little more and show theta barely moves.
    adapt_theta_on_probe(w, 200, seed=8)
    th_end = theta_of(w).mean()
    set_params(w, homeo=0.0)             # PIN theta (rung 6's discipline)
    freeze_all(w)
    dw = float(np.abs(weights_of(w, us) - wt0).max())
    drive = mean_drive(w, us).mean()
    st = cell_stats(w, us, key="rate", period=PERIOD)
    tc = st["tuning"]
    return {"osi": float(st["osi"].mean()),
            "alive_percell": (tc > 1e-9).sum(axis=1),
            "theta": float(theta_of(w).mean()),
            "dtheta_tail": float(abs(th_end - th_mid)),
            "drive": float(drive), "dw": dw,
            "osi_percell": st["osi"]}


def main() -> int:
    print("=" * 78)
    print("RUNG 8D PILOT — SELECTIVITY OR DRIVE? A DRIVE-MATCHED CONTROL")
    print(provenance_line())
    print("  Seeds 0/3000 (already burned). PILOT. NO confirmatory seed.")
    print("=" * 78)

    # k is measured from rung 8C's own audit (ideal 2.1818 vs floor 20.7545).
    K = 20.7545 / 2.1818
    print(f"\n  scaling constant k = floor_drive/ideal_drive = {K:.4f}")
    print("  (rung 8C's drive audit, lateral/grating: 20.7545 / 2.1818)")

    arms = {
        "A1 ideal x1     ": arm("lateral", ideal=True, k=1.0),
        "A2 ideal x9.51  ": arm("lateral", ideal=True, k=K),
        "A3 floor x1     ": arm("lateral", ideal=False, k=1.0),
        "A4 floor x1/9.51": arm("lateral", ideal=False, k=1.0 / K),
    }

    print(f"\n  {'arm':<17s} {'drive':>8s} {'theta':>8s} {'|dth|tail':>9s} "
          f"{'OSI':>8s} {'alive/12 per cell':>22s} {'max|dw|':>9s}")
    print("  " + "-" * 92)
    for name, r in arms.items():
        al = ",".join(str(int(x)) for x in r["alive_percell"])
        print(f"  {name:<17s} {r['drive']:8.4f} {r['theta']:8.4f} "
              f"{r['dtheta_tail']:9.4f} {r['osi']:8.4f} {al:>22s} {r['dw']:9.1e}")

    a1, a2 = arms["A1 ideal x1     "], arms["A2 ideal x9.51  "]
    a3, a4 = arms["A3 floor x1     "], arms["A4 floor x1/9.51"]

    print("\n--- PROVISO 2: DID THE DRIVE MATCH ACTUALLY LAND? ---")
    print(f"  A2 ideal-scaled drive {a2['drive']:.4f}  vs  "
          f"A3 floor drive {a3['drive']:.4f}   ratio {a2['drive']/a3['drive']:.4f}")
    print(f"  A4 floor-scaled drive {a4['drive']:.4f}  vs  "
          f"A1 ideal drive {a1['drive']:.4f}   ratio {a4['drive']/a1['drive']:.4f}")

    print("\n--- THE INVARIANCE: DOES OSI MOVE WHEN ONLY DRIVE MOVES? ---")
    print(f"  ideal:  OSI x1 {a1['osi']:.4f}  ->  x{K:.2f} {a2['osi']:.4f}   "
          f"|delta| = {abs(a1['osi']-a2['osi']):.2e}")
    print(f"  floor:  OSI x1 {a3['osi']:.4f}  ->  x1/{K:.2f} {a4['osi']:.4f}   "
          f"|delta| = {abs(a3['osi']-a4['osi']):.2e}")

    print("\n--- THE DECISIVE PAIR: SEPARATION AT *MATCHED* DRIVE ---")
    print(f"  UNMATCHED (8C's gate)  A1 - A3 = {a1['osi']-a3['osi']:.4f}   "
          f"(drives {a1['drive']:.2f} vs {a3['drive']:.2f})")
    print(f"  MATCHED (drive equal)  A2 - A3 = {a2['osi']-a3['osi']:.4f}   "
          f"(drives {a2['drive']:.2f} vs {a3['drive']:.2f})")
    print(f"  MATCHED (drive equal)  A1 - A4 = {a1['osi']-a4['osi']:.4f}   "
          f"(drives {a1['drive']:.2f} vs {a4['drive']:.2f})")
    print("""
  READING (fixed in advance):
    * If the MATCHED separations ~= the UNMATCHED one, the 9.5x drive gap
      carries NONE of the separation => the per-cell probe separates by
      SELECTIVITY, and the drive audit's verdict (true of a GLOBAL theta) does
      not transfer to rung 6's PER-CELL rule.
    * If a MATCHED separation COLLAPSES, the drive was carrying it and the gate
      is dead.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
