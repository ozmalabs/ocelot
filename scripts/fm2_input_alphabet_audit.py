#!/usr/bin/env python
"""FM-2 PRECONDITION: what is rung 7's retina's INPUT ALPHABET?

Mach bands and simultaneous contrast are defined on a GRADED LUMINANCE ramp. Before
pre-registering either, establish empirically whether this retina can receive one.

Structural reading (to be measured, not asserted): `lat_pool` and `lat_residual`
compute the centre as IfThenElse((r.step - c.last_burst) <= window_steps, 1.0, 0.0)
-- i.e. the RULE binarizes its own input from burst TIMING, so a graded `bursting`
value is discarded. If so, the input alphabet is {0, 1} and no ramp is presentable.

The inert-instrument rule applies to the READER: prove the probe can SEE a
difference when one IS there (the binary contrast), or "graded input has no effect"
is evidence of a dead probe, not of binarization.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import rung7_lib as R7


def residual_map(world, anat, lit_values):
    """Present `lit_values` (a dict cell->float) as `bursting`, tick, read residuals."""
    st = float(world.s.node(world.retina)["attrs"]["step"]) + 1.0
    world.s.set_attr(world.retina, "step", st)
    for (r, c), n in world.cells.items():
        v = float(lit_values.get((r, c), 0.0))
        world.s.set_attr(n, "state", "rested")
        world.s.set_attr(n, "bursting", v)
        # last_burst is what the RULE reads: mark as burst iff v > 0
        world.s.set_attr(n, "last_burst", st if v > 0.0 else -999.0)
    world.s.tick(200_000)
    out = np.zeros((R7.H, R7.W), np.float64)
    for (r, c), hc in anat["hcells"].items():
        out[r, c] = float(world.s.node(hc)["attrs"]["resid"])
    return out


def main():
    print(ep.provenance_line())
    print("FM-2 PRECONDITION — rung 7 retina's INPUT ALPHABET")
    print()

    world, anat = R7.build(seed=0, lateral=1.0)
    R7.run_waves(world, 400)          # bring the retina to its own fixed point
    R7.freeze_lateral(world)
    g = [float(world.s.node(anat["hcells"][(8, 8)])["attrs"][k]) for k in ("g1", "g2")]
    print(f"learned gains at (8,8): g1={g[0]:.4f} g2={g[1]:.4f}  (CS = g1+g2 = {sum(g):.4f})")
    print()

    # A horizontal luminance RAMP across the sheet, values in [0,1].
    ramp = {}
    for r in range(R7.H):
        for c in range(R7.W):
            ramp[(r, c)] = min(1.0, max(0.0, (c - 4) / 8.0))  # 0 for c<=4, 1 for c>=12

    # The SAME ramp, binarized at 0.5 -- what the rule would see if it binarizes.
    binar = {k: (1.0 if v > 0.0 else 0.0) for k, v in ramp.items()}

    A = residual_map(world, anat, ramp)
    B = residual_map(world, anat, binar)

    print("Row 8 residual profile:")
    print("  graded ramp    :", np.array2string(A[8], precision=4, max_line_width=200))
    print("  binarized ramp :", np.array2string(B[8], precision=4, max_line_width=200))
    print()
    D = float(np.max(np.abs(A - B)))
    print(f"max |graded - binarized| over the whole sheet = {D:.6e}")
    print()

    # ---- POSITIVE CONTROL ON THE READER -----------------------------------
    # The probe must SEE a difference when one IS there. Compare all-lit vs
    # all-dark: if THAT is also 0, the probe is dead and the audit says nothing.
    allon = {k: 1.0 for k in ramp}
    alloff = {k: 0.0 for k in ramp}
    C1 = residual_map(world, anat, allon)
    C0 = residual_map(world, anat, alloff)
    ctl = float(np.max(np.abs(C1 - C0)))
    print("POSITIVE CONTROL ON THE READER (can the probe see ANY difference?)")
    print(f"  max |all-lit - all-dark| = {ctl:.6e}")
    print(f"  probe is ALIVE: {ctl > 1e-9}")
    print()

    if ctl > 1e-9 and D == 0.0:
        print("VERDICT: the input alphabet is **{0, 1}**. The graded ramp and its")
        print("binarization produce byte-identical residuals (D = 0.0 exactly) while")
        print("the probe demonstrably SEES the binary contrast. The rule binarizes")
        print("its own input from burst TIMING; graded luminance is discarded before")
        print("any gain is applied.")
        print("=> MACH BANDS and SIMULTANEOUS CONTRAST are NOT PRESENTABLE on this")
        print("   retina: both are defined on a graded luminance ramp. Not tested.")
        print("   The HERMANN GRID is a BINARY figure and remains presentable.")
    elif ctl <= 1e-9:
        print("VERDICT: PROBE DEAD — audit uninterpretable.")
    else:
        print("VERDICT: the retina DOES read graded input (D > 0) — the structural")
        print("reading was wrong; a ramp is presentable and Mach bands are testable.")


if __name__ == "__main__":
    main()
