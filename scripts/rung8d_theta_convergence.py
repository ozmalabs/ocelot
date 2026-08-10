"""RUNG 8D — STEP 2: DOES THETA CONVERGE, AND IS THE GATE READ ON A DRIFT CURVE?

**§1/§2 CALIBRATION on already-burned seeds (0 / 3000). NO confirmatory seed. NO
hypothesis.** This is PROTOCOL §2 ("the rule must CONVERGE on its own input
distribution") applied to the one rule rung 8C's whole gate rests on — which
**§2 requires be run FIRST and which rung 8C never ran for theta on the probe
ensemble.**

WHY I AM RUNNING THIS (an anomaly I found, against my own pilot)
-----------------------------------------------------------------
`rung8d_drive_match_pilot.py` settled theta for **2200** steps (2000 + a 200-step
convergence check) and its floor arm scored **OSI 0.1420**. Rung 8C settled the
SAME arm, same seed, same rule, for **2000** steps and scored **0.2304**.
**Nothing else differs. 200 extra settling steps moved the floor by 0.088.**

The pilot also measured `|dtheta|` over its last 200 steps = **0.5942** on a
theta of 20.37 — **theta is still moving.**

**That is PROTOCOL §1 clause 3 / §2, biting the PROBE rather than the arm:**

    "if the score changes with how long you trained on the *same* input while
     duration is NOT your independent variable, you are reading an arbitrary
     point on a drift curve and every arm comparison is meaningless."

§1.2's discriminator is explicit: duration is NOT my independent variable here,
and rung 8C reported ONE number per arm at ONE timepoint. So if the floor is
still moving at 2000 steps, **rung 8C's 0.2304 is a point on a drift curve**,
and G2/G3 are read off it.

MY PREDICTION, IN ADVANCE, WITH PROVISOS (§3.7)
------------------------------------------------
The rule is `theta <- theta + theta_rate*(act - theta)`, an EMA. On a stationary
ensemble an EMA converges geometrically to E[act], so **theta ITSELF should
converge**. But the FLOOR cell's `act` has a much larger spread across the
ensemble than the ideal's, and theta chases it: I predict **theta's EMA never
settles to a fixed value but fluctuates around E[act] with a residual variance
set by theta_rate** — and because `rate = max(act - theta, 0)` is a THRESHOLD
sitting exactly in the middle of act's distribution, a small residual wobble in
theta moves which orientations survive the threshold, hence moves OSI.

**So I predict: theta converges IN MEAN but the FLOOR's OSI does NOT settle** —
it wobbles with theta's residual noise, and the wobble is large because the floor
cell's tuning curve is nearly flat (its `a` and `b` are close, so `(a-b)/(a+b)`
is a ratio of two small, noisy numbers).

**IF THAT IS RIGHT, RUNG 8C's GATE IS NOT CALIBRATED** and H1/H2 must NOT run:
a floor that wobbles by ~0.09 between 2000 and 2200 steps cannot anchor a
separation, and every arm comparison inherits the wobble.

**IF I AM WRONG** and OSI settles to a stable plateau by some duration, then the
gate is calibrated *at that duration*, rung 8C got lucky at 2000, and H1/H2 can
run with the settling duration declared in advance.

THE MEASUREMENT
---------------
Checkpoint theta, |dtheta|, and OSI on BOTH arms out to 6400 steps (§2 asks for
>=3200), on the composed pathway, weights frozen throughout. Report the whole
time-course, not a point. Both arms span the identical duration (§1.2).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.complex_cells import cell_stats, present  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from domains.lateral_world import set_lat_params  # noqa: E402
from domains.onoff_world import set_params  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    PERIOD, build, develop_retina, freeze_all, ideal_split_gabor,
)
from scripts.rung8b_lib import grating_ensemble, theta_of, weights_of  # noqa: E402

N_UNITS = 6
CHECKS = [400, 800, 1200, 1600, 2000, 2400, 3200, 4000, 4800, 6400]


def measure_frozen(w, us):
    """Measure OSI with theta PINNED and weights frozen — a snapshot that cannot
    disturb the settling it is measuring."""
    p = w.s.nodes("OnOffParams")[0]
    homeo_was = float(w.s.node(p)["attrs"]["homeo"])
    eta_was = float(w.s.node(p)["attrs"]["oo_eta"])
    set_params(w, homeo=0.0)                      # PIN theta for the probe
    st = cell_stats(w, us, key="rate", period=PERIOD)
    tc = st["tuning"]
    set_params(w, homeo=homeo_was, oo_eta=eta_was)  # restore, keep settling
    return {"osi": float(st["osi"].mean()),
            "osi_percell": st["osi"],
            "alive": (tc > 1e-9).sum(axis=1)}


def run(chan, *, ideal, seed=0):
    w, us, _a, _b = build(seed=seed, n_units=N_UNITS, channels=chan)
    develop_retina(w, 3000)
    if ideal:
        for u in us:
            ideal_split_gabor(w, u, theta=0.0, phase=0.0)
    wt0 = weights_of(w, us)
    # Settle theta on the PROBE ensemble, checkpointing as we go.
    set_params(w, oo_eta=0.0, frozen=0.0, homeo=1.0)
    if w.s.nodes("LatParams"):
        set_lat_params(w, frozen=1.0)
    rng = np.random.default_rng(7)
    rows, done, th_prev = [], 0, theta_of(w).copy()
    for target in CHECKS:
        while done < target:
            present(w, grating_ensemble(w, rng))
            done += 1
        th = theta_of(w).copy()
        m = measure_frozen(w, us)
        rows.append({"step": done, "theta": float(th.mean()),
                     "dtheta": float(np.abs(th - th_prev).max()),
                     "osi": m["osi"], "alive": m["alive"].mean(),
                     "osi_percell": m["osi_percell"]})
        th_prev = th
    dw = float(np.abs(weights_of(w, us) - wt0).max())
    freeze_all(w)
    return rows, dw


def main() -> int:
    print("=" * 78)
    print("RUNG 8D STEP 2 — §2 CONVERGENCE OF THETA ON THE PROBE ENSEMBLE")
    print(provenance_line())
    print("  Composed (lateral) pathway. Seeds 0/3000 (burned). NO hypothesis.")
    print("  Rung 8C read its gate at step 2000. Is that a plateau or a curve?")
    print("=" * 78)

    out = {}
    for armname, ideal in (("IDEAL", True), ("FLOOR", False)):
        rows, dw = run("lateral", ideal=ideal)
        out[armname] = rows
        print(f"\n  --- {armname} arm   (max|dw| over the whole run = {dw:.3e}) ---")
        print(f"  {'step':>6s} {'theta':>9s} {'max|dtheta|':>12s} {'OSI':>9s} "
              f"{'alive':>7s}")
        for r in rows:
            mark = "   <== RUNG 8C READ HERE" if r["step"] == 2000 else ""
            print(f"  {r['step']:>6d} {r['theta']:>9.4f} {r['dtheta']:>12.4f} "
                  f"{r['osi']:>9.4f} {r['alive']:>7.2f}{mark}")

    print("\n" + "=" * 78)
    print("  SEPARATION AS A FUNCTION OF SETTLING DURATION")
    print("=" * 78)
    print(f"  {'step':>6s} {'IDEAL':>9s} {'FLOOR':>9s} {'separation':>11s}")
    for i, s in enumerate(CHECKS):
        gi, gf = out["IDEAL"][i], out["FLOOR"][i]
        mark = "   <== RUNG 8C" if s == 2000 else ""
        print(f"  {s:>6d} {gi['osi']:>9.4f} {gf['osi']:>9.4f} "
              f"{gi['osi']-gf['osi']:>11.4f}{mark}")

    fl = np.array([r["osi"] for r in out["FLOOR"]])
    idl = np.array([r["osi"] for r in out["IDEAL"]])
    tail = slice(4, None)   # from step 2000 on
    print(f"\n  FLOOR OSI over steps>=2000:  min {fl[tail].min():.4f}  "
          f"max {fl[tail].max():.4f}  range {fl[tail].max()-fl[tail].min():.4f}")
    print(f"  IDEAL OSI over steps>=2000:  min {idl[tail].min():.4f}  "
          f"max {idl[tail].max():.4f}  range {idl[tail].max()-idl[tail].min():.4f}")
    print("""
  READING (fixed in advance):
    * A PLATEAU (floor range small and dtheta -> 0) => the gate is calibrated at
      that duration; declare the duration and H1/H2 may run.
    * A DRIFTING / WOBBLING floor => rung 8C's 0.2304 is a point on a curve
      (§1 clause 3), the probe is NOT calibrated, and H1/H2 MUST NOT RUN.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
