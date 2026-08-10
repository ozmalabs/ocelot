#!/usr/bin/env python
"""PROTOCOL §2 — DOES THE SETPOINT RULE SETTLE ON ITS OWN INPUT DISTRIBUTION?

Run BEFORE any experience/ablation arm, on the formative input alone. §2 exists
because this single check explains nine failed attempts in this arc, and the
memory of the last rung is explicit: the boring convergence measurement (does
the rule settle on its own input?) is what cracked it after nine failures on a
transient.

  * CONVERGENT + USEFUL: `mu_endo` plateaus at NON-ZERO structure AND drift -> 0.
  * Never converges  => the setpoint is a TRANSIENT and every arm is measured at
    an arbitrary point on a decay curve.
  * Converges to death (drift -> 0 at ~0) => `mu_endo` ~ 0 targets a mean output
    of zero and the eye dies. That is a REAL possible outcome here and would be
    evidence AGAINST the pre-visual thesis (§7) -- NOT a reason to add a floor.

Burns SEED 0 only (already-burned calibration seed). No confirmatory seed.

Adapter-only: co-advance the two worlds, read attributes back. Every decision is
a seed rule; `calib` is graph DATA on EyeParams (PROTOCOL §0).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

import domains.seed_registry  # noqa: F401
from domains import eye_world
from domains.wave_world import WaveWorld
from substrate.boot_core import boot_core, load_seeds_into


def build(seed: int, h: int = 16, w: int = 16):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    ww = WaveWorld(s, h=h, w=w, seed=seed)
    ey = eye_world.EyeWorld(s, h=h, w=w, gaze_l=21, seed=seed)
    n = ey.couple_waves(ww)
    eye_world.set_params(ey, eye=1.0, calib=1.0, saw=0.0)
    return ww, ey, n


def main():
    STEPS = int(os.environ.get("CONV_STEPS", "3200"))
    SEED = 0
    IGNITE_EVERY = 5   # rung 1's committed wave protocol (record(): ignite_k=1)

    print(ep.provenance_line())
    print(f"§2 CONVERGENCE — steps={STEPS} seed={SEED} ignite_every={IGNITE_EVERY}")
    print()

    ww, ey, n_edges = build(SEED)
    print(f"coupled {n_edges} RetinaCell -endo_drives-> EyeCell (1:1 co-located)")

    # POSITIVE CONTROL ON THE READER, and it CAUGHT A REAL ERROR (§1, §12).
    # The first cut of this probe read `ww.frame()` as "the endogenous input".
    # `frame()` is `state == "active"` -- the WAVE pathway, sampled AFTER
    # `step()`'s double-buffered commit -- and it reported 0.0234 while the
    # quantity `ey_endo_resp` actually reads (`bursting` = active OR driven,
    # marked BEFORE the commit) was 0.1444. A 6x error, in the direction that
    # would have made the setpoint look like GCAL's 0.024. Read what the RULE
    # reads, never a nearby convenience.
    def bursting_mean():
        return float(np.mean([[float(ww.s.node(ww.cells[(r, c)])["attrs"]["bursting"])
                               for c in range(ww.w)] for r in range(ww.h)]))

    ckpt = [50, 100, 200, 400, 800, 1200, 1600, 2000, 2400, 2800, 3200,
            4000, 4800, 5600, 6400]
    ckpt = [c for c in ckpt if c <= STEPS]
    prev = None
    rows = []
    burst_hist = []
    trace = []
    for t in range(1, STEPS + 1):
        k = 1 if (t - 1) % IGNITE_EVERY == 0 else 0
        ww.step(ignite_k=k)
        ey.step(frame=None)
        burst_hist.append(bursting_mean())
        trace.append((t, float(ey.mu_endos().mean())))
        if t in ckpt:
            mu = ey.mu_endos()
            m = float(mu.mean())
            # §2's SPECIFIED drift: ||w(t)-w(t-D)|| / ||w||, a norm ratio.
            # (The first cut used max|.|/mean -- a MAX over 256 cells of a
            # deliberately noisy EMA, which is not what §2 asks for.)
            drift = (float(np.linalg.norm(mu - prev) / max(np.linalg.norm(mu), 1e-12))
                     if prev is not None else float("nan"))
            rows.append((t, m, float(mu.std()), float(mu.min()),
                         float(mu.max()), drift))
            prev = mu.copy()

    print()
    print("  step    mean mu_endo    sd        min       max      drift(L2 rel)")
    for t, m, sd, lo, hi, dr in rows:
        print(f"  {t:5d}   {m:.6f}      {sd:.6f}  {lo:.6f}  {hi:.6f}   {dr:.6f}")

    b = np.array(burst_hist)
    print()
    print(f"ENDOGENOUS INPUT (positive control, reading `bursting` -- the "
          f"attribute the RULE reads):")
    print(f"  mean burst rate over the run = {b.mean():.6f}  "
          f"(last 800 steps: {b[-800:].mean():.6f})")
    print(f"  wave activity nonzero at {int((b > 0).sum())}/{len(b)} steps")

    # STRICTER THAN THE DRIFT GATE, AND AIMED AT MYSELF (§5 permits this
    # direction only). A small L2 drift is satisfied by a slow RAMP as well as
    # by a plateau. Regress mean mu_endo on t over the SECOND HALF: a plateau
    # has a slope indistinguishable from 0; a transient does not.
    tr = np.array(trace[len(trace) // 2:])
    tt, vv = tr[:, 0], tr[:, 1]
    slope, icept = np.polyfit(tt, vv, 1)
    resid = vv - (slope * tt + icept)
    se = float(np.sqrt((resid ** 2).sum() / (len(tt) - 2)
                       / ((tt - tt.mean()) ** 2).sum()))
    tstat = float(slope / se) if se > 0 else float("inf")
    drift_per_1k = float(slope * 1000.0)
    print()
    print(f"TREND OVER THE SECOND HALF (t={int(tt[0])}..{int(tt[-1])}): "
          f"slope = {drift_per_1k:+.6f} per 1000 steps, t = {tstat:+.2f}")
    print(f"  (a PLATEAU has slope ~ 0; a RAMP does not. This is stricter than "
          f"the L2 drift gate, which a slow ramp passes.)")

    final_m = rows[-1][1]
    final_drift = rows[-1][5]
    print()
    print(f"VERDICT INPUTS: final mean mu_endo = {final_m:.6f}, "
          f"final relative drift = {final_drift:.6f}")
    if b.mean() <= 0.0:
        print("=> NO ENDOGENOUS ACTIVITY. The probe is uninterpretable "
              "(positive control on the input FAILED).")
    elif abs(tstat) > 3.0 and abs(drift_per_1k) > 0.002:
        print("=> RAMP, NOT A PLATEAU: the mean setpoint is still moving at "
              f"{drift_per_1k:+.6f}/1000 steps (t={tstat:+.2f}). The setpoint is "
              "a TRANSIENT and every arm would be measured at an arbitrary "
              "point on a curve (§2). STOP.")
    elif final_m <= 1e-6:
        print("=> CONVERGES TO DEATH: the measured setpoint is ~0, so the "
              "homeostat would target a mean output of zero. Evidence AGAINST "
              "the pre-visual thesis; report, do not floor it (§7, §13).")
    elif final_drift > 0.05:
        print("=> DOES NOT SETTLE: the setpoint is a TRANSIENT. Every arm would "
              "be measured at an arbitrary point on a curve (§2). STOP.")
    else:
        print("=> CONVERGENT + NON-ZERO: the setpoint settles on its own input "
              "distribution. §2 satisfied; an arm may now be pre-registered.")


if __name__ == "__main__":
    main()
