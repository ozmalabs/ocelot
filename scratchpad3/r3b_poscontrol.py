"""RUNG 3B POSITIVE CONTROL (PROTOCOL section 2 / the null-instrument lesson).
Can the BISTABLE rule learn direction from a PERFECT single-direction stimulus
at all? Burned seeds 0-3 ONLY. This is an INSTRUMENT check, never an arm: it
trains on the probe stimulus, which is exactly why it can only calibrate.
It is also where bi_eta is FIXED — on a control containing no arm and no
hypothesis, exactly as rung 3 fixed eta=2e-3."""
import numpy as np, sys
sys.path.insert(0, ".")
from scratchpad3.r3b_lib import boot, probe_dsi
from domains.dorsal_world import sweep_frames

SEEDS = (0, 1, 2, 3)
CKPT = (0, 400, 1600, 3200)


def one(seed, bistable, bi_eta):
    s, w, us, dp, wp = boot(seed, bistable=bistable, bi_eta=bi_eta)
    s.set_attr(wp, "propagate", 0.0)
    fr = sweep_frames(w.h, w.w, 0)          # ONE direction, forever
    out, nan = {}, 0
    i = 0
    for c in CKPT:
        while i < c:
            w.step(ignite_k=0, frame=fr[i % len(fr)])
            i += 1
        d = probe_dsi(w, us, seed=seed)
        nan += int(np.isnan(d).sum())
        out[c] = float(np.nanmean(d))
    return out, nan


print("STEP-0 MUST EQUAL THE 0.111 FLOOR IN EVERY ROW (the instrument check)")
print("bi_eta      " + "".join(f"{c:>9d}" for c in CKPT) + "     NaN")
for bistable, bi_eta in ((0.0, 0.0), (1.0, 1e-3), (1.0, 1e-2), (1.0, 3e-2), (1.0, 1e-1)):
    rows = [one(s, bistable, bi_eta) for s in SEEDS]
    nan = sum(r[1] for r in rows)
    lab = "OFF (rung3)" if bistable == 0 else f"{bi_eta:.0e}      "
    print(f"{lab:12s}" + "".join(f"{np.mean([r[0][c] for r in rows]):+9.3f}" for c in CKPT)
          + f"   {nan:5d}", flush=True)
