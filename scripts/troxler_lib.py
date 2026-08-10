#!/usr/bin/env python
"""Shared runner for the TROXLER arms. Adapter-only.

THE ARMS, AND WHAT EACH CORRESPONDS TO IN THE ANIMAL (PROTOCOL §6 — state this
BEFORE running; §6 exists because `dark` was set to "no input" for TWO
pre-registrations while the plan said dark-reared animals keep their waves).

  Arm A — DRIFT (the normal animal).  `saw=1`, the scene is STATIONARY in the
    world.  The eye's fixational drift walks the retinal window across a static
    scene, so the RETINAL image MOVES.  This is an eye at fixation.

  Arm B — STABILISED (Ditchburn & Ginsborg 1952 / Riggs & Ratliff 1952 /
    Yarbus).  `saw=1` — **THE EYE KEEPS MOVING** — but the scene is re-painted
    each step at the eye's current position, so the RETINAL image is STATIC.
    This is the mirror on the contact lens: the image FOLLOWS the eye.
    **This is NOT "freeze the drift".**  Freezing the gaze is PARALYSIS, a
    different manipulation with a different meaning (arm C).

  Arm C — FROZEN GAZE (paralysis / the FM-0 ablation).  `saw=0`, static scene.
    The eye does not move, so the retinal image is static too.  Included ONLY to
    MEASURE whether "freeze the gaze" and "stabilise the image" coincide in this
    model rather than assuming it (the §6 error, made twice already).  They
    coincide IFF the gaze's ONLY wired consumer is the sampling; `D(B,C) == 0`
    exactly is what proves it, and it is a measurement, not a grep (§12.1 — the
    ninth inert instrument was the supervisor's and it WAS a grep).

WHY THE STABILISATION LIVES IN THE WORLD AND NOT IN A RULE.  Ditchburn's mirror
is APPARATUS, not physiology.  The adapter's documented job is to state that
photons exist at world locations (`add_world`: "the adapter states that photons
exist at world locations.  It does NOT say which receptor sees which photon —
that is `ey_sample_at_gaze`'s decision"), and `present_world` exists verbatim
"for a moving-scene control".  Arm B IS that moving-scene control: a scene whose
motion happens to equal the gaze's.  The EYE is byte-identical across all three
arms but for `saw`, which is graph DATA on EyeParams (PROTOCOL §0).
Implementing the stabilisation as a RULE would put the mirror INSIDE the eye and
make the retina cancel its own gaze — that is efference copy / VOR, a DIFFERENT
mechanism that no stabilisation experiment contains.  There is no Python
conditional over graph state here: the apparatus is an affine translation of the
photon field, applied unconditionally.

ORDERING, MEASURED NOT ASSUMED (`/tmp/probe_order.py`, reproduced in
`troxler_calibrate.py`): within one tick the sampler reads the gaze BEFORE
`ey_saw_move` moves it.  So the apparatus paints the world at the gaze position
read BEFORE `step()`.  Arm B asserts its own success every step
(`stab_err` = max|lum − W|), because a stabilisation that silently failed would
look exactly like "the drift does not matter".

THE FADE MEASURE.  `contrast = SD over cells of resp`.  **SD(resp) reads 0 for a
SILENT sheet and a UNIFORM one alike** — this is exactly how FM-1's headline fade
window (t≈300–800) was disqualified as dead-arm readings (§1.1).  So contrast is
NEVER read alone: `alive` = frac(resp > 0) is reported at every timepoint, for
every arm, and a fade claim requires the sheet to be ALIVE and UNIFORM.  A silent
arm is a FAILED GATE, never a successful fade.  `peak/base` is NOT read
(unbounded; blown up in two independent rungs).

Phase 0 is the setpoint rung's, unchanged: the eye is closed, its only input is
its own spontaneous waves, and `mu_endo` accumulates the cumulative mean of its
own output.  `mu_mode=1` is used because `mu_mode=0` (GCAL's imported 0.024)
drives the sheet to 0% aliveness for a window — §1's fourth clause would fail on
the arm before any fade could be read.  That is the setpoint rung's own finding,
used rather than re-litigated.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import domains.seed_registry  # noqa: F401
from domains import eye_world
from domains.wave_world import WaveWorld
from substrate.boot_core import boot_core, load_seeds_into

H = W = 16
GAZE_L = 21
WH = GAZE_L + H - 1          # 36 — the world must span gaze + retina
CALIB_STEPS = 3200           # §2: the setpoint rung measured convergence here
IGNITE_EVERY = 5             # rung 1's committed wave protocol

ARM_DRIFT = "drift"
ARM_STABILISED = "stabilised"
ARM_FROZEN = "frozen"


def world_scene(seed: int = 0) -> np.ndarray:
    """The stationary scene, 36x36.  The SAME spatial statistics as the setpoint
    rung's `static_frame` (a period-8 diagonal grating plus a Gaussian blob),
    extended to the world's extent so the retinal window can slide over it.  The
    grating period (8 receptors) is NOT tuned to anything here: it is the frame
    the setpoint rung already committed, reused unchanged."""
    yy, xx = np.mgrid[0:WH, 0:WH]
    f = 0.5 + 0.35 * np.sin(2 * np.pi * (xx + yy) / 8.0)
    f += 0.15 * np.exp(-(((yy - 13) ** 2 + (xx - 19) ** 2) / 6.0))
    return np.clip(f, 0.0, 1.0)


def uniform_scene(level: float = 0.5) -> np.ndarray:
    """A FLAT world — no spatial structure anywhere.  The fade measure's FLOOR
    exemplar: there is no contrast to represent, so `contrast` must read ~0
    while the sheet is still ALIVE."""
    return np.full((WH, WH), float(level))


def lums(ey) -> np.ndarray:
    out = np.zeros((H, W), np.float64)
    for (r, c), n in ey.cells.items():
        out[r, c] = float(ey.s.node(n)["attrs"]["lum"])
    return out


def _paint(ey, frame: np.ndarray) -> None:
    """Mechanical: state the photon count at each world location."""
    for (r, c), n in ey.wcells.items():
        ey.s.set_attr(n, "lum", float(frame[r, c]))


def _paint_window(ey, W_img: np.ndarray, g: tuple[int, int]) -> None:
    """THE MIRROR.  Paint the stabilised image onto the world at the eye's
    current position, so that world(gaze + receptor) == W_img(receptor).  Only
    the 16x16 window the retina overlies is ever sampled, so only it is written.
    An unconditional affine translation of the photon field — no decision."""
    gr, gc = g
    for i in range(H):
        for j in range(W):
            ey.s.set_attr(ey.wcells[(gr + i, gc + j)], "lum", float(W_img[i, j]))


def run_arm(seed: int, arm: str, *, vis_steps: int,
            calib_steps: int = CALIB_STEPS, scene=None,
            frozen: float = 0.0, no_waves: bool = False,
            record_resp: bool = False) -> dict:
    """One eye, one seed, one arm.

    `frozen=1` gates every adaptation rule (`eye_world.freeze`'s real freeze) and
    is the §1-clause-3 control: with the MECHANISM off, the measure must not
    drift on its own over the same duration.
    """
    if arm not in (ARM_DRIFT, ARM_STABILISED, ARM_FROZEN):
        raise ValueError(f"unknown arm {arm!r}")
    S = world_scene(0) if scene is None else scene

    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    ey = eye_world.EyeWorld(s, h=H, w=W, gaze_l=GAZE_L, seed=seed)

    mu_endo_mean = float("nan")
    if not no_waves:
        ww = WaveWorld(s, h=H, w=W, seed=seed)
        ey.couple_waves(ww)
        # ---- PHASE 0: the eye is closed; its only input is its own waves ----
        eye_world.set_params(ey, eye=1.0, calib=1.0, saw=0.0, mu_mode=1.0,
                             world_sample=0.0)
        for t in range(1, calib_steps + 1):
            k = 1 if (t - 1) % IGNITE_EVERY == 0 else 0
            ww.step(ignite_k=k)
            ey.step(frame=None)
        mu_endo_mean = float(ey.mu_endos().mean())
    else:
        eye_world.set_params(ey, eye=1.0, mu_mode=1.0, world_sample=0.0)

    # ---- PHASE 1: the eye opens onto the world ----
    ey.add_world(S)
    saw = 0.0 if arm == ARM_FROZEN else 1.0
    eye_world.set_params(ey, calib=0.0, saw=saw, world_sample=1.0,
                         frozen=float(frozen))

    # The stabilised image is the window the retina overlies at t=0, so ALL
    # THREE ARMS SEE AN IDENTICAL RETINAL IMAGE AT t=0 and diverge only as the
    # gaze moves.  Nothing is chosen here: it is wherever the gaze already is.
    g0 = ey.gaze_pos()
    W_img = S[g0[0]:g0[0] + H, g0[1]:g0[1] + W].copy()

    contrast, alive, mean_resp, stab_err, gaze_path = [], [], [], [], []
    resp_trace = []
    for t in range(vis_steps):
        if arm == ARM_STABILISED:
            _paint_window(ey, W_img, ey.gaze_pos())   # the mirror, BEFORE the tick
        gaze_path.append(ey.gaze_pos())
        ey.step(frame=None)                            # `frame=None`: `present()` is dead here;
                                                       # the GRAPH samples the world at the gaze.
        r = ey.responses()
        contrast.append(float(r.std()))
        alive.append(float((r > 0).mean()))
        mean_resp.append(float(r.mean()))
        stab_err.append(float(np.abs(lums(ey) - W_img).max()))
        if record_resp:
            resp_trace.append(r.copy())

    contrast = np.array(contrast)
    alive = np.array(alive)
    out = {
        "seed": seed, "arm": arm, "mu_endo": mu_endo_mean,
        "contrast_t0": float(contrast[0]),
        "contrast_final": float(contrast[-1]),
        "contrast_min": float(contrast.min()),
        "alive_t0": float(alive[0]),
        "alive_final": float(alive[-1]),
        "alive_min": float(alive.min()),
        "alive_argmin": int(alive.argmin()),
        "mean_resp_final": float(mean_resp[-1]),
        "max_stab_err": float(np.max(stab_err)),
        "gaze_distinct": len(set(gaze_path)),
        "gaze_path_len": float(sum(
            max(abs(a[0] - b[0]), abs(a[1] - b[1]))
            for a, b in zip(gaze_path, gaze_path[1:]))),
        "contrast": contrast, "alive": alive,
        "mean_resp": np.array(mean_resp),
    }
    if record_resp:
        out["resp_trace"] = np.array(resp_trace)
        out["W_img"] = W_img
    return out


__all__ = ["run_arm", "world_scene", "uniform_scene", "H", "W", "GAZE_L", "WH",
           "CALIB_STEPS", "ARM_DRIFT", "ARM_STABILISED", "ARM_FROZEN"]
