"""SETTLE — the shared harness. Builds a cortical SHEET (rung 8's anatomy with
the units on a LATTICE instead of at random centres) and runs the arms.

**Reuses rung 8's committed machinery unchanged** (`rung8_lib.build` /
`develop_retina` / `run_waves` / `freeze_all`, `rung8b_lib.weights_of`,
`rung8c_ensemble_transfer.adapt_theta_on_probe`, `complex_cells.cell_stats`) —
the probe is rung 8D's CALIBRATED one (IDEAL 0.9989, FLOOR 0.2691, n_dead 0,
scale-invariant to 5.55e-16). It is NOT rebuilt here (PROTOCOL 1/5).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.settle_world import set_settle_params, wire_sheet  # noqa: E402
from scripts.rung8_lib import H, RF, W, build  # noqa: E402


def lattice_centres(n_side: int, *, h: int = H, w: int = W, rf: int = RF):
    """`n_side` x `n_side` RF centres on a UNIFORMLY-SPACED integer lattice.

    The centres must sit at least `rf//2` from the edge or the RF is clipped
    (`add_signed_units` silently drops the missing bipolars, which would make
    the units ANATOMICALLY UNEQUAL — a confound, not a sheet). The span is read
    off the retina and the RF, both committed; nothing is chosen.

    **THE SPACING MUST BE UNIFORM, AND THE FIRST CUT'S WAS NOT — a silent
    anatomy bug of exactly PROTOCOL 12.3's dict-collision shape.**
    `np.linspace(3, 12, 3).round()` is `[3, 8, 12]`: steps of 5 and 4. The sheet
    wiring then reads a single lattice step off the centres and finds NO
    neighbour across the mismatched gap, so a 3x3 "lattice" wired 12 directed
    edges where 24 were due — an IRREGULAR graph masquerading as a lattice,
    with no error and no warning. An integer stride cannot do this.
    """
    half = rf // 2
    lo, hi = half, h - half - 1
    if n_side < 2:
        raise ValueError(f"n_side must be >= 2 (a sheet needs neighbours), got {n_side}")
    if n_side > (hi - lo + 1):
        raise ValueError(f"n_side={n_side} exceeds the {hi - lo + 1} admissible "
                         f"centres on a {h}x{w} retina at rf={rf}")
    stride = (hi - lo) // (n_side - 1)
    if stride < 1:
        raise ValueError(f"n_side={n_side} leaves no integer stride in [{lo},{hi}]")
    ys = [lo + i * stride for i in range(n_side)]
    xs = list(ys)
    return [(int(y), int(x)) for y in ys for x in xs]


def build_sheet(*, seed=0, n_side=4, channels="lateral", eta=5e-4,
                connectivity=4, settle=0.0, bubble=0.0, w0=1.0):
    """Rung 8's anatomy, with the SUnits on a cortical LATTICE + the sheet wired.

    **THIS RE-IMPLEMENTS `rung8_lib.build`'s BOOT RATHER THAN CALLING IT, FOR
    EXACTLY ONE REASON, AND IT IS A FINDING (see `VISION_SETTLE_RESULTS.md`):
    THE ENGINE'S RULE PRIORITY IS SEED LOAD ORDER.** `run_rules` tries rules in
    list order and restarts on the first that progresses, so a rule fires only
    once every EARLIER rule is exhausted. `vision_onoff`'s pipeline is
    `oo_sunit_activate` -> `oo_sunit_rate` -> `oo_sunit_burst_winner` ->
    `oo_learn_*`, each with a once-per-step guard. A seed loaded AFTER it can
    therefore never interpose a phase BETWEEN activate and rate: measured, with
    `vision_settle` appended last, `rate == aff` to the last digit — the readout
    had already run on the UNSETTLED `act`, and settling was VACUOUS downstream
    (PROTOCOL 1 clause 5). Loading `vision_settle` BEFORE `vision_onoff` gives
    `st_settle` priority, so the sheet relaxes to its fixed point BEFORE
    `oo_sunit_rate` reads it — which is precisely GCAL's "once all settling
    steps are complete ... the settled activation is deemed to be the V1
    response". The phase structure IS the rule order; the engine has no other
    way to say it. `rung8_lib.build` is another rung's file and is NOT edited
    (PROTOCOL 11 rule 4).

    The anatomy below is `rung8_lib.build`'s, followed line for line.
    """
    from domains.lateral_world import set_lat_params
    from domains.onoff_world import add_onoff_retina, add_signed_units, set_params
    from domains.wave_world import WaveWorld
    from scripts.rung8_lib import H as _H, W as _W
    from substrate.boot_core import boot_core, load_seeds_into

    centres = lattice_centres(n_side)
    s, ag = boot_core()
    # THE ORDER IS THE MECHANISM: vision_settle BEFORE vision_onoff.
    seeds = ["vision_waves", "vision_settle", "vision_onoff"]
    if channels == "lateral":
        seeds += ["vision_lateral", "vision_compose"]
    load_seeds_into(s, ag, seeds)

    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", 0.0)

    w = WaveWorld(s, h=_H, w=_W, seed=seed)

    if channels == "lateral":
        from domains.lateral_world import add_lateral_retina
        anat = add_lateral_retina(w)
        bip = anat["bipolars"]
        set_lat_params(w, lateral=1.0, learn_gain=1.0, radius2=1.0,
                       lat_eta=2e-3, lat_gmax=2.0, lat_g0=0.0, frozen=0.0)
        for p in w.s.nodes("ComposeParams"):
            w.s.set_attr(p, "compose", 1.0)
    elif channels == "degenerate":
        bip = add_onoff_retina(w)
    else:
        raise ValueError(f"unknown channels={channels!r}")

    us = add_signed_units(w, bip, len(centres), rf=RF, seed=seed,
                          centres=centres, w0=w0)
    set_params(w, onoff=1.0, split=1.0, subnorm=1.0, oo_eta=eta,
               oo_wmax=2.0, frozen=0.0)
    n_edges = wire_sheet(w, us, connectivity=connectivity)
    set_settle_params(w, settle=settle, bubble=bubble)
    return w, us, n_edges


def sheet_state(world, units):
    """Read (act, aff, rate, bursting) off the sheet. Mechanical query."""
    s = world.s
    out = {}
    for k in ("act", "aff", "rate", "bursting"):
        out[k] = np.array([float(s.node(u)["attrs"].get(k, 0.0)) for u in units])
    return out
