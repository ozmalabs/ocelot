#!/usr/bin/env python
"""TROXLER — IS THE DRIFT ARM'S CONTRAST STRUCTURE, OR RECTIFICATION NOISE?

**DESCRIPTIVE, NOT PRE-REGISTERED, and it can only make the claim STRICTER.**
§5 forbids changing a measure to RESCUE a failure; making a measure stricter
AGAINST YOURSELF is always allowed and is what §1 and §7 demand (rung 8B
disqualified its own PASS; that was correct). The pre-registered primary remains
`contrast = SD(resp)`; nothing here replaces it. Burned seed 0 only.

THE WORRY, and it is the one the pre-registration named as my LEAST confident
prediction: the drift arm settles at `alive ~ 0.625`, so ~37% of cells sit at
exactly 0 (the ReLU floor). An SD computed over a sheet that is 37% hard-zero
could be driven by the RECTIFICATION BOUNDARY rather than by the image. If so,
"the drifting arm does not fade" would be true of the STATISTIC and false of the
CLAIM — the same shape of error as FM-1's dead-arm fade window, mirrored.

THE CHECK: does the drift arm's RESPONSE still carry the IMAGE that is on the
retina at that instant? Correlate `resp(t)` against `lum(t)` across the 256
cells, at the SETTLED end of the run. A response that has faded to uniform
(the stabilised arm) cannot correlate with anything; a response that is pure
rectification noise would not track the image either.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import troxler_lib as T  # noqa: E402
from domains import eye_world  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402


def run(arm: str, steps: int = 3200, tail: int = 50):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    ey = eye_world.EyeWorld(s, h=T.H, w=T.W, gaze_l=T.GAZE_L, seed=0)
    ww = WaveWorld(s, h=T.H, w=T.W, seed=0)
    ey.couple_waves(ww)
    eye_world.set_params(ey, eye=1.0, calib=1.0, saw=0.0, mu_mode=1.0,
                         world_sample=0.0)
    for t in range(1, T.CALIB_STEPS + 1):
        k = 1 if (t - 1) % T.IGNITE_EVERY == 0 else 0
        ww.step(ignite_k=k)
        ey.step(frame=None)
    S = T.world_scene(0)
    ey.add_world(S)
    eye_world.set_params(ey, calib=0.0, saw=0.0 if arm == T.ARM_FROZEN else 1.0,
                         world_sample=1.0)
    g0 = ey.gaze_pos()
    W_img = S[g0[0]:g0[0] + T.H, g0[1]:g0[1] + T.W].copy()

    cors, alives, contrasts = [], [], []
    for t in range(steps):
        if arm == T.ARM_STABILISED:
            T._paint_window(ey, W_img, ey.gaze_pos())
        ey.step(frame=None)
        if t >= steps - tail:
            r = ey.responses().ravel()
            l = T.lums(ey).ravel()
            rr, ll = r - r.mean(), l - l.mean()
            den = np.linalg.norm(rr) * np.linalg.norm(ll)
            cors.append(float(np.dot(rr, ll) / den) if den > 0 else 0.0)
            alives.append(float((r > 0).mean()))
            contrasts.append(float(r.std()))
    return np.array(cors), np.array(alives), np.array(contrasts)


def main():
    print(ep.provenance_line())
    print("TROXLER — STRUCTURE CHECK (descriptive; burned seed 0; NOT pre-registered)")
    print("Does the response still carry the image ON THE RETINA at that instant?")
    print("corr(resp, lum) across the 256 cells, over the last 50 settled steps.\n")
    for arm in (T.ARM_DRIFT, T.ARM_STABILISED):
        c, a, ct = run(arm)
        print(f"  {arm:11s} corr(resp,lum) = {c.mean():+.4f} +/- {c.std():.4f}  "
              f"[min {c.min():+.4f}, max {c.max():+.4f}]")
        print(f"              alive = {a.mean():.4f}   contrast = {ct.mean():.6f}")
    print("\nREADING:")
    print("  A HIGH corr in the drift arm => the 37% hard-zero floor is NOT what the")
    print("  SD is measuring; the response tracks the image that is actually there,")
    print("  so 'does not fade' is a claim about STRUCTURE, not about rectification.")
    print("  A LOW/ZERO corr in the stabilised arm => nothing left to correlate with:")
    print("  the response is uniform. That is the fade, and it is not death (alive=1).")


if __name__ == "__main__":
    main()
