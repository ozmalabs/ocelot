#!/usr/bin/env python
"""Shared runner for the ENDOGENOUS SETPOINT arms. Adapter-only.

THE DESIGN, and the control it buys (PROTOCOL §6 — state what each arm
corresponds to IN THE ANIMAL before running):

  Phase 0 (BOTH arms, identical): the eye is closed. Its only input is its own
    spontaneous retinal waves. `calib=1`, so the cell's output IS its burst
    (`ey_endo_resp`) and `mu_endo` accumulates the cumulative mean of that
    output (`ey_endo_latch`). theta is FROZEN throughout (the `calib<0.5` guard
    on both adapt rules) -- a homeostat running during the measurement would be
    regulating the quantity being measured.
  Phase 1 (BOTH arms, identical input): the eye opens onto a static scene.
    `calib=0`; theta adapts.

  **The arms differ in `mu_mode` AND NOTHING ELSE.** Both eyes have the same
  age, the same wave history, the same visual input, the same RNG streams; both
  even MEASURE `mu_endo` in phase 0. Arm A then ignores it and uses GCAL's
  imported 0.024; arm B uses what it measured. That is what makes this a
  controlled comparison of WHERE THE SETPOINT CAME FROM, rather than two
  different models.

  Arm A0 (`no_waves=True`) reproduces FM-1b's exact protocol -- no phase 0 at
  all -- as an INSTRUMENT CHECK on already-burned seed 0. It is not part of the
  confirmatory test.

The statistic is §1.1's: ALIVENESS = fraction of cells with `resp > 0`, and the
headline is its MINIMUM over phase 1. `osi`-style guarded divisions mean a dead
cell scores a flawless floor, so aliveness is reported for the ARM, not just the
measure. `peak/base` is NOT read (unbounded; blown up in two rungs).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import domains.seed_registry  # noqa: F401
from domains import eye_world
from domains.wave_world import WaveWorld
from substrate.boot_core import boot_core, load_seeds_into

H = W = 16
CALIB_STEPS = 3200      # §2: converged by 3200 (L2 drift 0.0033), measured on seed 0
VIS_STEPS = 1200        # FM-1b's protocol, unchanged
IGNITE_EVERY = 5        # rung 1's committed wave protocol


def static_frame() -> np.ndarray:
    """FM-1b's frame, byte-identical."""
    yy, xx = np.mgrid[0:H, 0:W]
    f = 0.5 + 0.35 * np.sin(2 * np.pi * (xx + yy) / 8.0)
    f += 0.15 * np.exp(-(((yy - 5) ** 2 + (xx - 11) ** 2) / 6.0))
    return np.clip(f, 0.0, 1.0)


def run_arm(seed: int, mu_mode: float, *, no_waves: bool = False,
            calib_steps: int = CALIB_STEPS, vis_steps: int = VIS_STEPS) -> dict:
    """One eye, one seed. Returns the pre-registered statistics."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    ey = eye_world.EyeWorld(s, h=H, w=W, gaze_l=21, seed=seed)

    mu_endo_mean = float("nan")
    if not no_waves:
        ww = WaveWorld(s, h=H, w=W, seed=seed)
        ey.couple_waves(ww)
        # ---- PHASE 0: the pre-visual phase ----
        eye_world.set_params(ey, eye=1.0, calib=1.0, saw=0.0, mu_mode=mu_mode)
        for t in range(1, calib_steps + 1):
            k = 1 if (t - 1) % IGNITE_EVERY == 0 else 0
            ww.step(ignite_k=k)
            ey.step(frame=None)
        mu_endo_mean = float(ey.mu_endos().mean())
    else:
        eye_world.set_params(ey, eye=1.0, mu_mode=mu_mode)

    # ---- PHASE 1: the eye opens ----
    eye_world.set_params(ey, calib=0.0, saw=0.0)
    f = static_frame()
    alive, mean_resp, th_mean, th_max = [], [], [], []
    for t in range(vis_steps):
        ey.step(frame=f)
        r = ey.responses()
        th = ey.thetas()
        alive.append(float((r > 0).mean()))
        mean_resp.append(float(r.mean()))
        # TWO theta statistics, and the distinction is load-bearing for the
        # reproduction control: FM-1b's reported "max theta" is
        # `max_t( thetas().MEAN() )` (see its `run()`), NOT the spatial max.
        # Reading the spatial max against FM-1b's number would have reported a
        # reproduction FAILURE (0.8125 vs 0.4603) that is purely two different
        # statistics -- an instrument mismatch, not a model difference.
        th_mean.append(float(th.mean()))
        th_max.append(float(th.max()))

    alive = np.array(alive)
    return {
        "seed": seed,
        "mu_mode": mu_mode,
        "mu_endo": mu_endo_mean,
        "min_alive": float(alive.min()),
        "argmin_alive": int(alive.argmin()),
        "final_alive": float(alive[-1]),
        "max_theta_mean": float(np.max(th_mean)),   # FM-1b's statistic
        "max_theta_max": float(np.max(th_max)),     # the spatial max
        "final_mean_resp": float(mean_resp[-1]),
        "t0_mean_resp": float(mean_resp[0]),
    }


__all__ = ["run_arm", "static_frame", "H", "W", "CALIB_STEPS", "VIS_STEPS"]
