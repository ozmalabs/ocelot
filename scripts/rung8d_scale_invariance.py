"""RUNG 8D — STEP 3: IS THE READOUT *EXACTLY* SCALE-INVARIANT IN THE DRIVE?

**§1 CALIBRATION on already-burned seeds (0 / 3000). NO confirmatory seed. NO
hypothesis.** A direct, minimal test of the analytic claim in
`rung8d_drive_match_pilot.py`, because the pilot produced an ANOMALY I could not
explain from theory and refuse to hand-wave:

    A3 floor x1        OSI 0.1420
    A4 floor x1/9.51   OSI 0.1912      |delta| = 0.049

Theory says that delta must be ~0: `act` is a linear Fold over weights, theta's
EMA is linear in `act` with init 0, so scaling every weight by k scales `act`,
`theta` and `rate` by k, and `osi = (a-b)/(a+b)` cancels k EXACTLY. The pilot
CONFIRMED the linear part — theta scaled to 5 significant figures
(20.3678 / 9.5126 = 2.1412, measured 2.1412) and drive scaled to 0.09% — **and
yet OSI moved.** Something between `rate` and `osi` is not scaling.

THIS SCRIPT COMPARES THE TUNING CURVES ELEMENTWISE rather than the summary. If
`tc_x1 == k * tc_x1/k` elementwise, the readout is scale-invariant and the OSI
delta must come from the floor's own duration WOBBLE (measured in
`rung8d_theta_convergence.py`: the floor OSI ranges over 0.0630 at steps>=2000
while theta never stops fluctuating). If the curves do NOT match, there is a
nonlinearity and the drive-matched control is not clean.

MY PREDICTION, IN ADVANCE (§3.7)
---------------------------------
**I predict the tuning curves DO scale (ratio ~= k elementwise) and the OSI delta
is the floor's WOBBLE, not a nonlinearity** — because the wobble (0.063) is
LARGER than the delta (0.049), and theta is a fluctuating quantity that is
sensitive to its exact trajectory. Specifically I expect the residual to come
from **f32 rounding amplified by CANCELLATION**: `rate = act - theta` with
act ~= theta ~= 20.8 and rate ~= 0.4 is a subtraction of two nearly-equal
numbers, so a 1e-7 relative error in `act` becomes a ~5e-6 relative error in
`rate` — but theta then FEEDS BACK on that residual over 2200 steps, and a
threshold sitting mid-distribution turns a tiny perturbation into a different
set of surviving orientations. **A chaotic amplification of rounding, not a
broken rule.**

**If the curves do NOT scale**, I am wrong about the mechanism and the pilot's
matched control is contaminated — report it and do not use it.

Either way this is decided by MEASUREMENT, not by the argument above (§12.4).
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
from scripts.rung8_lib import PERIOD, build, develop_retina, freeze_all  # noqa: E402
from scripts.rung8b_lib import theta_of, weights_of  # noqa: E402
from scripts.rung8d_drive_match_pilot import scale_weights  # noqa: E402
from scripts.rung8c_ensemble_transfer import N_UNITS, adapt_theta_on_probe  # noqa: E402

K = 9.5126


def build_floor(k: float, *, settle: int):
    w, us, _a, _b = build(seed=0, n_units=N_UNITS, channels="lateral")
    develop_retina(w, 3000)
    if k != 1.0:
        scale_weights(w, us, k)
    adapt_theta_on_probe(w, settle)
    set_params(w, homeo=0.0)
    freeze_all(w)
    st = cell_stats(w, us, key="rate", period=PERIOD)
    return {"tc": st["tuning"], "osi": st["osi"], "theta": theta_of(w),
            "w": weights_of(w, us)}


def compare(a, b, k, label):
    """b is expected to be a's arrays divided by k."""
    print(f"\n  --- {label} ---")
    wr = a["w"] / np.maximum(b["w"] * k, 1e-30)
    print(f"  weights:  max|w_x1 / (k*w_xk) - 1| = {np.abs(wr - 1).max():.3e}")
    tr = a["theta"] / np.maximum(b["theta"] * k, 1e-30)
    print(f"  theta:    max|th_x1 / (k*th_xk) - 1| = {np.abs(tr - 1).max():.3e}")
    m = a["tc"] > 1e-9
    rr = a["tc"][m] / np.maximum(b["tc"][m] * k, 1e-30)
    print(f"  tuning:   max|tc_x1 / (k*tc_xk) - 1| = {np.abs(rr - 1).max():.3e}"
          f"   (over {m.sum()} live entries)")
    print(f"  OSI x1    = {a['osi'].mean():.4f}   per cell "
          f"{np.array2string(a['osi'], precision=4)}")
    print(f"  OSI x1/k  = {b['osi'].mean():.4f}   per cell "
          f"{np.array2string(b['osi'], precision=4)}")
    print(f"  |delta OSI| = {abs(a['osi'].mean()-b['osi'].mean()):.4e}")


def main() -> int:
    print("=" * 78)
    print("RUNG 8D STEP 3 — IS THE READOUT EXACTLY SCALE-INVARIANT?")
    print(provenance_line())
    print("  Seeds 0/3000 (burned). NO confirmatory seed. NO hypothesis.")
    print("=" * 78)

    # (a) ZERO settling: theta is untouched by the trajectory, so this isolates
    #     the READOUT's algebra from theta's fluctuation. If the readout is
    #     scale-invariant at all, it is invariant HERE.
    print("\n" + "=" * 78)
    print("  (a) SETTLE = 0  — the READOUT's algebra alone, no theta trajectory")
    print("=" * 78)
    a0 = build_floor(1.0, settle=0)
    b0 = build_floor(1.0 / K, settle=0)
    compare(a0, b0, K, "floor, settle=0")

    # (b) FULL settling: adds theta's 2000-step fluctuating trajectory on top.
    print("\n" + "=" * 78)
    print("  (b) SETTLE = 2000 — theta's fluctuating trajectory included")
    print("=" * 78)
    a1 = build_floor(1.0, settle=2000)
    b1 = build_floor(1.0 / K, settle=2000)
    compare(a1, b1, K, "floor, settle=2000")

    print("""
  READING (fixed in advance):
    * settle=0 invariant AND settle=2000 invariant => the readout is
      scale-invariant; the pilot's 0.049 was the floor's WOBBLE.
    * settle=0 invariant but settle=2000 NOT => the algebra is exact and
      theta's trajectory amplifies rounding => the floor is CHAOTIC in the
      drive scale, which is itself a finding about the instrument.
    * settle=0 NOT invariant => a genuine nonlinearity in the readout; the
      drive-matched control is contaminated and must not be used.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
