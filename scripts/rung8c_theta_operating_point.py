"""RUNG 8C — STEP 2 DIAGNOSTIC: DOES **ANY** THETA MAKE THE COMPOSED PROBE SEE?

**This is PROTOCOL §1 CALIBRATION, not a confirmatory arm.** The protocol's own
order is: convergence (§2) -> calibrate the measure + positive control (§1) ->
pre-register and commit -> ONE confirmatory run. This script is in the SECOND
box. It burns NO confirmatory seed (seed 0 / 3000 only -- already burned, the
ledger's rung-8 calibration row), tests no hypothesis, and trains nothing.

WHY THIS MEASUREMENT, AND WHY BEFORE ANY MECHANISM
---------------------------------------------------
Rung 8 and rung 8B BOTH diagnose the same blocker:

    rung 8   theta is an EMA of the cell's own DRIVE on the FORMATIVE input;
             rung 7's retina is a predictive coder, so waves are cheap
             (act 0.861) and the OOD grating is expensive (act 1.902, 2.21x).
             theta = 0.774 lands BELOW the probe drive => the iceberg never
             bites => an IDEAL split-Gabor scores 0.1290.
    rung 8B   GCAL's Eq 8 self-positions theta correctly (3.51 vs 9.75 for
             drives of 2.19 vs 5.18) -- the MECHANISM is right -- but an
             ABSOLUTE setpoint in UNNORMALISED units winds theta up and kills
             the floor arm. "GCAL's A requires GCAL's GC."

Both conclude: **fix theta's PLACEMENT.** Every named next step (GC; a
setpoint; a probe delivered at the formative drive) is a different way of
MOVING THETA.

**But that shared diagnosis has never been tested directly.** It asserts that a
correctly-placed theta EXISTS. Nobody has asked the prior question:

    >> IS THERE ANY theta AT ALL that makes an IDEAL cell visible on the
    >> composed pathway while leaving a RANDOM cell at the floor, with BOTH
    >> arms ALIVE?

If YES -- the blindness is a theta-PLACEMENT problem, the diagnosis holds, and
the rung's job is a mechanism that lands theta there (and this run reports what
that theta is, so a later pre-registration can state what it must FALL OUT of,
per §13).

If NO -- **theta is not the blocker**, and rung 8's and rung 8B's diagnosis is
incomplete. Building GC on top of it would be building on a false premise, and
the two rungs' "named next" lists would ALL be chasing a placement that does not
exist. That is the more valuable answer, and it is the one this arc's evidence
should make us take seriously (PROTOCOL §7).

THIS IS A SWEEP, AND THAT IS LEGITIMATE **HERE** AND NOWHERE ELSE
------------------------------------------------------------------
PROTOCOL §3.6 forbids sweeps in a CONFIRMATORY run: "Exactly the listed tests.
No sweeps. No re-runs." This is a MEASURE-CALIBRATION sweep -- the same class as
rung 8B's own G5 (adapt = 2000/5000/8000) and rung 8's duration check
(0/400/1600). It asks whether the INSTRUMENT has an operating point at all, and
its output is a GATE VERDICT plus a diagnostic, never a hypothesis test.

**It cannot be used to pick a theta and then report the score at it.** That would
be metric surgery (§5) -- fitting theta to the answer. Any theta this run
identifies is an input to a FUTURE pre-registration whose mechanism must make
theta land there ON ITS OWN, from something the system measures for itself
(§13). The number found here is a TARGET TO EXPLAIN, not a knob to set.

THE THREE THINGS MEASURED AT EVERY THETA, AND WHY EACH
-------------------------------------------------------
  IDEAL   OSI of a hand-installed PERFECT split-Gabor (§1 clause 2: an ideal
          exemplar must score HIGH).
  FLOOR   OSI of the untouched init (§1 clause 1: random input must score at
          the floor). Measured IN-RUN at every theta, never inherited: OSI's
          floor is init-dependent (0.0044 DC / 0.3899 signed / 0.3168 rung 6 /
          0.0205 rung 8 composed -- four values, ONE probe).
  ALIVE   **§1's FOURTH clause, and the one that killed rung 8B:** how many of
          the probe's 12 orientations each arm responds to AT ALL.
          `complex_cells.osi()` ends `(a-b)/(a+b) if (a+b) > 1e-9 else 0.0`, so
          **a DEAD cell returns a flawless 0.0000** and a "perfect floor" is
          SATISFIED BY DEATH. Rung 8B passed all four of its criteria with a
          floor arm firing at 0 of 12. A theta is only an operating point if
          BOTH arms are ALIVE at it.

`peak/base` is NOT read. It is an unbounded ratio that has blown up in two
independent rungs (1.6e6; 7.1e7 / 2.4e8) and §1.1 says bound it or retire it.

theta is PINNED throughout (no adaptation rule fires) and WEIGHTS ARE FROZEN --
verified `max|dw| = 0`, because `oja=0 IS NOT A FREEZE` was rung 5's worst
instrument bug. This isolates theta's PLACEMENT from every other moving part:
whatever this curve shows is a property of the theta axis alone.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PROTOCOL §10.1 rule 3: "Any non-pytest entrypoint (a rung script) must call
# `engine_preamble()` ITSELF." It must run BEFORE any `domains.*` import, because
# the FIRST import of `substrate_rs` binds the engine for the whole process — a
# preamble that runs afterwards is a no-op that LOOKS correct. Caught live: this
# rung's scripts imported `domains.complex_cells` first and silently loaded the
# CANONICAL tree's engine via the `.pth`, which went RED mid-session when a
# concurrent agent rebuilt it from ITS Rust source (§11.5: "long-running
# measurement is not a lock").
from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.complex_cells import cell_stats  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from domains.onoff_world import set_params  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    PERIOD, build, develop_retina, freeze_all, ideal_split_gabor,
)
from scripts.rung8b_lib import weights_of  # noqa: E402

N_UNITS = 6


def line(k, v):
    print(f"  {k:<52s} {v}")


def prepare(chan, *, ideal, seed=0, w0=1.0):
    """Build -> develop the retina to ITS OWN fixed point -> optionally install a
    PERFECT cell -> FREEZE everything.

    `develop_retina` is rung 8's own instrument fix (its §G): at `lat_g0=0` the
    residual IS the raw centre `c >= 0`, so `OFF = max(-c,0) == 0` and the OFF
    channel is DEAD at init. The retina must be at its own fixed point -- the
    state every rung-7 claim is measured at, and the order that matches the
    animal (retinal centre-surround precedes cortical simple cells).
    """
    w, us, _a, _b = build(seed=seed, n_units=N_UNITS, channels=chan, w0=w0)
    develop_retina(w, 3000)
    if ideal:
        for u in us:
            ideal_split_gabor(w, u, theta=0.0, phase=0.0)
    # Rung 6's EMA theta rule is PINNED by its OWN documented knob (`homeo=0`),
    # so nothing re-adapts theta underneath the sweep. The seed is NOT edited
    # (PROTOCOL §11.4) -- this is graph data, the agent's own configuration.
    set_params(w, homeo=0.0)
    wt0 = weights_of(w, us)
    freeze_all(w)
    return w, us, wt0


def set_theta(world, value):
    """Mechanical state write on the SUnit population: PIN theta at `value`.

    No rule decides this and no rule re-adapts it -- `homeo=0` pins rung 6's EMA
    and `vision_theta` is not loaded at all here. The theta AXIS is the
    independent variable, so it is set by the adapter exactly as the probe's
    orientation is.
    """
    for u in world.s.nodes("SUnit"):
        world.s.set_attr(u, "theta", float(value))


def measure(world, units):
    """OSI + §1-clause-4 ALIVENESS, off ONE `cell_stats` read (one probe, one
    pass -- so the two can never disagree about which run they describe)."""
    st = cell_stats(world, units, key="rate", period=PERIOD)
    tc = st["tuning"]
    return {"osi": float(st["osi"].mean()),
            "alive": float((tc > 1e-9).sum(axis=1).mean()),
            "tmax": float(tc.max())}


def main() -> int:
    print("=" * 78)
    print("RUNG 8C — STEP 2 DIAGNOSTIC: IS THERE **ANY** THETA OPERATING POINT?")
    print(provenance_line())
    print("  §1 CALIBRATION. Seeds 0/3000 (already burned). NO confirmatory seed.")
    print("=" * 78)

    # THE GRID MUST BRACKET **EACH PATHWAY'S OWN** DRIVE, and the first version
    # of this script got that wrong -- recorded rather than quietly fixed,
    # because it is §12's defect in a new costume.
    #
    # Rung 8 measured the two pathways' drives, and they differ ~6x -- which is
    # the whole reason rung 8B's absolute mu could not transfer:
    #     lateral (composed)   waves 0.861  gratings 1.902   theta lands 0.774
    #     degenerate (rung 6)  waves 5.317  gratings 5.120   theta lands 5.430
    # A grid sized to the COMPOSED pathway (max 4.0) does not reach the
    # DEGENERATE pathway's operating point at ~5.4 AT ALL. The first run
    # therefore reported "NO OPERATING POINT" for the degenerate arm -- i.e. it
    # failed its own POSITIVE CONTROL, on a pathway where rung 6 demonstrably
    # scores 1.0000. That was a GRID artifact, not a finding: **an absence off a
    # range you did not sample is evidence about the RANGE, not the pathway**
    # (§12's "a selector that matches by substring is not a selector", in the
    # numeric domain; §1.1's "a gate that checks a rule's CONSTANTS but not the
    # AXIS they parameterise is not a gate").
    #
    # The grid now spans BOTH drive regimes, is declared before any score is
    # seen, and is reported IN FULL below -- every point, no selection (§4:
    # ~15 comparisons reported selectively is a forking-paths garden).
    grid = [0.0, 0.25, 0.5, 0.774, 1.0, 1.25, 1.5, 1.75, 1.902,
            2.0, 2.1, 2.2, 2.3, 2.5, 3.0, 4.0,
            4.5, 5.0, 5.12, 5.43, 5.75, 6.0, 6.5, 7.0]

    for chan in ("lateral", "degenerate"):
        print(f"\n{'=' * 78}\n  PATHWAY: {chan}\n{'=' * 78}")
        wi, usi, wt0i = prepare(chan, ideal=True)
        wf, usf, wt0f = prepare(chan, ideal=False)
        print(f"  {'theta':>7s} | {'IDEAL osi':>9s} {'alive/12':>8s} | "
              f"{'FLOOR osi':>9s} {'alive/12':>8s} | {'separation':>10s}")
        print(f"  {'-'*7}-+-{'-'*9}-{'-'*8}-+-{'-'*9}-{'-'*8}-+-{'-'*10}")
        best = None
        for th in grid:
            set_theta(wi, th)
            set_theta(wf, th)
            mi = measure(wi, usi)
            mf = measure(wf, usf)
            sep = mi["osi"] - mf["osi"]
            # An operating point requires BOTH arms ALIVE (§1 clause 4) --
            # a dead floor scores a perfect 0.0 and rung 8B passed on exactly
            # that artifact.
            ok = mi["osi"] >= 0.80 and mf["osi"] <= 0.50 and sep >= 0.30 \
                and mi["alive"] > 0 and mf["alive"] > 0
            mark = "  <== OPERATING POINT" if ok else ""
            if ok and (best is None or sep > best[1]):
                best = (th, sep)
            print(f"  {th:7.3f} | {mi['osi']:9.4f} {mi['alive']:8.2f} | "
                  f"{mf['osi']:9.4f} {mf['alive']:8.2f} | {sep:10.4f}{mark}")
        dwi = float(np.abs(weights_of(wi, usi) - wt0i).max())
        dwf = float(np.abs(weights_of(wf, usf) - wt0f).max())
        line("WEIGHTS FROZEN across the sweep? max|dw|",
             f"{max(dwi, dwf):.3e}   (rung 5: `oja=0` IS NOT a freeze)")
        if best:
            print(f"  ==> [{chan}] AN OPERATING POINT EXISTS: theta={best[0]:.3f}, "
                  f"separation {best[1]:.4f}")
            print(f"      The diagnosis HOLDS on this pathway: the blindness is a")
            print(f"      theta-PLACEMENT problem. A mechanism must land theta")
            print(f"      there ON ITS OWN, from a quantity the system measures")
            print(f"      for itself (§13). This theta is a TARGET TO EXPLAIN,")
            print(f"      NOT a knob to set (§5).")
        else:
            print(f"  ==> [{chan}] **NO OPERATING POINT ANYWHERE ON THE GRID.**")
            print(f"      No theta makes an ideal cell visible while leaving a")
            print(f"      random cell at the floor with both arms alive. On this")
            print(f"      pathway theta is NOT the blocker, and rung 8's and rung")
            print(f"      8B's shared diagnosis is INCOMPLETE — every 'named next'")
            print(f"      that moves theta (GC included) is chasing a placement")
            print(f"      that does not exist.")

    print("\n" + "=" * 78)
    print("""  READING THIS TABLE

  The `degenerate` column is the POSITIVE CONTROL for the sweep itself: rung 6's
  channels are where this probe demonstrably WORKS (ideal 1.0000 at theta 5.43).
  If the degenerate pathway shows an operating point and the lateral one does
  not, the sweep is sound and the composed pathway genuinely has none -- the
  instrument is not simply broken in both.

  A theta identified here is NOT a result and MUST NOT be set. It is the input to
  a future pre-registration that must answer: WHAT DOES THIS NUMBER FALL OUT OF?
  If the answer is "nothing in the system -- I would have to measure it against
  the answer", the mechanism is incomplete and the constant is a symptom, not a
  knob (§13).""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
