"""RUNG 8C — THE CONFOUND AUDIT: is the operating point measuring SELECTIVITY,
or is it measuring DRIVE?

**This audit exists to attack my OWN diagnostic's headline**, and it is the check
that rung 8B's post-mortem says was missing: *"its gate tested only one direction
of failure and was blind to the other"* (§4 -- adding a mechanism can silently
invalidate your control).

THE HAZARD, STATED BEFORE MEASURING
------------------------------------
`rung8c_theta_operating_point.py` pins **ONE GLOBAL theta** across every SUnit
and reports, on the composed pathway:

    theta 2.1   IDEAL osi 1.0000 (11/12 alive)   FLOOR osi 0.0111 (12/12 alive)
                separation 0.9889

But **no mechanism places a global theta.** GCAL's theta is PER CELL; rung 6's
EMA theta is PER CELL; any homeostat is PER CELL, because a homeostat regulates
a CELL. And rung 8B measured the fact that makes this matter:

    "A random cell's drive is ~10x an ideal cell's (unstructured `w0=1` weights
     sum; a zero-mean Gabor cancels)."

If that holds on the composed pathway, then at a global theta = 2.1:
  * the IDEAL cell (act ~2.19) is sliced NEAR ITS PEAK -> rectification bites ->
    OSI 1.0;
  * the RANDOM cell (act ~20) is NOT SLICED AT ALL -> it sits far above theta,
    responds ~flat across all 12 orientations -> OSI ~0.01.

**Then the "separation of 0.9889" is separating CELLS BY THEIR DRIVE MAGNITUDE,
not by their selectivity** -- the same disease as rung 8B's fake separation
("the ideal cell reaches the setpoint; the random cell dies -- and THAT asymmetry
IS the fake separation"), inverted: there the floor DIED, here the floor is
UNSLICED. Both are "the two arms are at different points of the same nonlinearity
for a reason that has nothing to do with orientation".

A PER-CELL theta would track EACH cell's OWN drive -- landing the random cell's
theta near ~20, slicing ITS OWN NOISE, and inflating its OSI toward rung 6's
measured floor of 0.3168/0.3105. **Which is exactly what rung 6's floor IS.**

WHAT THIS MEASURES
-------------------
The drive (`act`) distribution of the FLOOR arm's cells vs the IDEAL arm's cells,
on the composed pathway, under the PROBE ensemble -- the quantity every per-cell
theta rule integrates. No hypothesis, no seed burned (seed 0, already burned).

If the ratio is ~1, the global-theta sweep is a fair proxy for a per-cell rule
and its separation is real. If the ratio is ~10, the sweep's separation is an
UPPER BOUND no per-cell mechanism can reach, and the operating point I reported
is not the operating point a mechanism would find.

**I expect ~10, i.e. I expect this to damage my own headline.** Stating it in
advance so that being right is evidence and being wrong is informative (§3.7).
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

from domains.complex_cells import present  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from domains.onoff_world import set_params  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    build, develop_retina, freeze_all, ideal_split_gabor,
)
from scripts.rung8b_lib import grating_ensemble, wave_ensemble  # noqa: E402

N_UNITS = 6


def acts_of(world):
    """The cell's DRIVE — the quantity rung 6's EMA theta follows and the
    quantity GCAL's rbar is the OUTPUT of. Read straight off the SUnit."""
    return np.array([float(world.s.node(u)["attrs"].get("act", np.nan))
                     for u in world.s.nodes("SUnit")])


def drive_stats(chan, *, ideal, stim, steps=400, seed=0):
    w, us, _a, _b = build(seed=seed, n_units=N_UNITS, channels=chan)
    develop_retina(w, 3000)
    if ideal:
        for u in us:
            ideal_split_gabor(w, u, theta=0.0, phase=0.0)
    # Pin rung 6's EMA theta (its own knob) and pin theta itself at 0 so `act`
    # is read raw — the drive, before any threshold. Weights frozen.
    set_params(w, homeo=0.0)
    for u in us:
        w.s.set_attr(u, "theta", 0.0)
    freeze_all(w)
    rng = np.random.default_rng(7)
    draw = grating_ensemble if stim == "grating" else wave_ensemble
    acc = []
    for _ in range(steps):
        present(w, draw(w, rng))
        acc.append(acts_of(w))
    a = np.array(acc)
    return {"mean": float(a.mean()), "max": float(a.max()),
            "per_cell_mean": a.mean(axis=0)}


def main() -> int:
    print("=" * 78)
    print("RUNG 8C — CONFOUND AUDIT: SELECTIVITY, or DRIVE?")
    print(provenance_line())
    print("  §1 calibration. Seed 0 (already burned). NO confirmatory seed.")
    print("=" * 78)

    for chan in ("lateral", "degenerate"):
        print(f"\n--- PATHWAY: {chan} ---")
        for stim in ("grating", "wave"):
            fl = drive_stats(chan, ideal=False, stim=stim)
            idl = drive_stats(chan, ideal=True, stim=stim)
            ratio = fl["mean"] / max(idl["mean"], 1e-9)
            print(f"  [{stim:7s}] IDEAL-arm drive  mean {idl['mean']:8.4f}  "
                  f"max {idl['max']:9.4f}")
            print(f"  [{stim:7s}] FLOOR-arm drive  mean {fl['mean']:8.4f}  "
                  f"max {fl['max']:9.4f}")
            print(f"  [{stim:7s}] **FLOOR/IDEAL DRIVE RATIO**            "
                  f"{ratio:8.2f}x")
            print(f"  [{stim:7s}] per-cell FLOOR drive means: "
                  f"{np.round(fl['per_cell_mean'], 3).tolist()}")

    print("\n" + "=" * 78)
    print("""  THE VERDICT THIS DECIDES

  ratio ~ 1   => the global-theta sweep is a fair proxy for a per-cell rule.
                 Its operating point and separation stand, and a mechanism that
                 lands theta in [1.9, 3.0] would genuinely separate the arms.

  ratio >> 1  => **the sweep's separation is an ARTIFACT of the drive gap.** A
                 global theta placed for the IDEAL cell leaves the FLOOR cell
                 unsliced (hence its clean 0.011), but a PER-CELL theta -- which
                 is the only kind any mechanism implements -- tracks each cell's
                 OWN drive, slices the floor cell's own noise, and inflates its
                 OSI toward rung 6's measured 0.3168. The operating point I
                 reported is then NOT the one a mechanism would find, the 0.9889
                 separation is an unreachable upper bound, and STEP 2 must NOT be
                 entered as though the probe were calibrated.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
