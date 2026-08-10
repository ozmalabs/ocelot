#!/usr/bin/env python3
"""McCollough PILOT / measure-calibration (PROTOCOL §1) — NOT the confirmatory run.
Exploratory only; no confirmatory seeds consumed. Verifies the MEASURE is sound
before pre-registration: ideal exemplar high, floors at the floor, feedforward
control null, and the mechanism is ALIVE.
"""
from __future__ import annotations
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import mccollough_world as mw  # noqa: E402

# opponent-colour stimulus definitions (integer cone values, in-frame).
NEUTRAL = dict(cL=10, cM=10, cS=10)            # achromatic: rg=0, by=-10 (const)
RED     = dict(cL=15, cM=5,  cS=10)            # rg=+10 (L-M): "red" on the L-M axis
GREEN   = dict(cL=5,  cM=15, cS=10)            # rg=-10: "green"
VERT, HORIZ = 90.0, 0.0                        # orientation labels (arbitrary, distinct)

FRAMES = 8


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_mccollough"])
    return s, ag


def _adapt_test(s, adapt_patches, test_patches, *, mode):
    h = mw.add_field(s, patches=adapt_patches + test_patches)
    mw.set_flags(s, enabled=1.0, mode=mode)
    mw.adapt(s, h, frames=FRAMES)
    mw.test(s, h)
    return h


def standard_adapt():
    return [dict(theta=VERT, is_adapt=1.0, **RED),
            dict(theta=HORIZ, is_adapt=1.0, **GREEN)]


def run():
    print(provenance_line())

    # --- PREDICTIVE, standard adaptation, achromatic test -----------------------
    s, _ = _boot()
    adapt = standard_adapt()
    test = [dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL),
            dict(theta=HORIZ, rrow=11, is_adapt=0.0, **NEUTRAL)]
    h = _adapt_test(s, adapt, test, mode=0.0)
    pv = mw.cell_percept(s, h, 10, 0, "percept_rg")
    ph = mw.cell_percept(s, h, 11, 0, "percept_rg")
    print(f"[PRED] vert-test percept_rg={pv:+.3f} (expect <0 GREEN)  "
          f"horiz-test percept_rg={ph:+.3f} (expect >0 PINK)")
    print(f"       priors: vert={mw.prior_of(s,h,VERT)}  horiz={mw.prior_of(s,h,HORIZ)}")

    # --- FEEDFORWARD control, same adaptation, achromatic test (THE CRUX) -------
    s, _ = _boot()
    h = _adapt_test(s, standard_adapt(),
                    [dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL),
                     dict(theta=HORIZ, rrow=11, is_adapt=0.0, **NEUTRAL)], mode=1.0)
    fv = mw.cell_percept(s, h, 10, 0, "percept_rg")
    fh = mw.cell_percept(s, h, 11, 0, "percept_rg")
    print(f"[FF ]  vert-test percept_rg={fv:+.3f}  horiz-test percept_rg={fh:+.3f} "
          f"(BOTH expect 0.0 — NO aftereffect)")

    # --- FF ALIVE positive control: coloured test reports real colour -----------
    s, _ = _boot()
    h = _adapt_test(s, standard_adapt(),
                    [dict(theta=VERT, rrow=10, is_adapt=0.0, **RED)], mode=1.0)
    fa = mw.cell_percept(s, h, 10, 0, "percept_rg")
    print(f"[FF-alive] coloured(red) test percept_rg={fa:+.3f} (expect +10 — arm is ALIVE)")

    # --- FLOOR: no adaptation -> no aftereffect (predictive) ---------------------
    s, _ = _boot()
    h = mw.add_field(s, patches=[dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL)])
    mw.set_flags(s, enabled=1.0, mode=0.0)
    mw.test(s, h)  # NO adaptation
    nf = mw.cell_percept(s, h, 10, 0, "percept_rg")
    print(f"[FLOOR no-adapt] percept_rg={nf:+.3f} (expect 0.0)")

    # --- FLOOR: colour alone (red on BOTH orientations) -> no contingency -------
    s, _ = _boot()
    h = _adapt_test(s, [dict(theta=VERT, is_adapt=1.0, **RED),
                        dict(theta=HORIZ, is_adapt=1.0, **RED)],
                    [dict(theta=VERT, rrow=10, is_adapt=0.0, **NEUTRAL),
                     dict(theta=HORIZ, rrow=11, is_adapt=0.0, **NEUTRAL)], mode=0.0)
    cv = mw.cell_percept(s, h, 10, 0, "percept_rg")
    ch = mw.cell_percept(s, h, 11, 0, "percept_rg")
    print(f"[FLOOR colour-alone] vert={cv:+.3f} horiz={ch:+.3f} "
          f"(both <0, EQUAL: no orientation-contingency, diff={cv-ch:+.3f})")

    # --- §9 OFF-day: flag off -> inert ------------------------------------------
    s, _ = _boot()
    h = _boot_offday(s)
    print(f"[OFFDAY] percept_rg={mw.cell_percept(s,h,10,0,'percept_rg'):+.3f} (expect 0.0 inert)")


def _boot_offday(s):
    h = mw.add_field(s, patches=[dict(theta=VERT, rrow=10, is_adapt=1.0, **RED),
                                 dict(theta=VERT, rrow=11, is_adapt=0.0, **NEUTRAL)])
    mw.set_flags(s, enabled=0.0, mode=0.0)   # OFF
    mw.adapt(s, h, frames=FRAMES)
    mw.test(s, h)
    return h


if __name__ == "__main__":
    run()
