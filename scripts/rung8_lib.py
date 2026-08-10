"""rung8_lib — RUNG 8's harness: COMPOSE rung 7's eye with rung 6's cortex.

PROTOCOL §10: the engine is pinned by `engine_preamble()` (which resolves THIS
TREE's build, or a source-identical one, and fails loudly otherwise), and every
number this library produces is reported with `provenance_line()`.

WHAT THIS RUNG IS
-----------------
Rung 6 built a signed simple layer (SUnits over two NON-NEGATIVE channels) and
its development FAILED: waves grew nothing (OSI 0.283 -> 0.329 against a 0.3168
floor). Its measured diagnosis was that rung 6's own split is DEGENERATE —
`x_OFF = 1 - x_ON` forces `C_ON,OFF(d) = -C_ON,ON(d)` identically, so the two
channels carry NO independent correlation structure, and Miller 1994's mechanism
consumes exactly that.

Rung 7 then built a retina whose channels DO have different spatial dependence
(SD 0.3601, sigma_ON,ON 1.627 vs sigma_ON,OFF 3.264, ratio 2.007) — but it
explicitly claimed NO orientation selectivity: *"a precondition is not a
result"*, and the two seeds were deliberately NEVER COMPOSED.

**This rung composes them and re-runs rung 6's own convergence gate and OSI
measure, UNCHANGED. It tests whether the precondition was the blocker.**

THE COMPOSITION NEEDS NO NEW RULE — AND THAT IS A FINDING, NOT A SHORTCUT
-------------------------------------------------------------------------
Rung 6's SUnit rules bind their presynaptic channel by an UNTYPED edge
traversal (`["b", "oo_pre", "sy"]`), and read only `bursting` + `bstep` off it.
The string "Bipolar" appears in `oo_sunit_activate` and `oo_learn_sub` ONLY in
their comments. Rung 7's `LBipolar` carries both attrs and `lat_bipolar` sets
both. So the cortex is GRAIN-AGNOSTIC about which retina feeds it: composition
is pure ANATOMY (which synapse touches which cell), the same class of mechanical
fact as rung 6's own RF geometry and rung 4's retinotopy.

Verified before use, not assumed (`rung8_compose_check.py`).

So `seeds/vision_compose.json` adds NO rule to either seed — it is the
`ComposeParams` node that makes the ARM the agent's own configuration
(PROTOCOL §0) rather than a fork in the host, plus the manifest that declares
the dependency on BOTH. `seeds/vision_lateral.json` and `seeds/vision_onoff.json`
are NOT edited: compose, don't modify.

THE TWO ARMS
------------
  `channels="lateral"`  — SUnits read rung 7's LBipolars (decorrelated).  H1
  `channels="degenerate"` — SUnits read rung 6's Bipolars (x_OFF = 1-x_ON). H2

Both arms have IDENTICAL SUnit anatomy, identical synapse count, identical RF
geometry, identical probe, identical learning rules and identical eta. The ONLY
difference is which retina is upstream — which is exactly the difference rung 6
diagnosed and rung 7 removed.

THE FLOOR IS MEASURED PER-INIT, IN THIS RUN, AS A REPORTED ARM
---------------------------------------------------------------
The w0 ablation established that OSI's random floor is INIT-DEPENDENT: 0.0044
(DC init) vs 0.3899 (signed init) — 89x, same probe. Rung 6's 0.3168 is a third
value. **A floor is not inheritable.** So `untrained` is an ARM of this run, at
the same init, measured through the same frozen probe, and every lift is stated
against it. A "lift" below its own untrained floor is not a lift — that is how
rung 5's zero-mean arm's apparent 0.3665 evaporated.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

import domains.seed_registry  # noqa: F401,E402
from domains.complex_cells import cell_stats, gabor  # noqa: E402
from domains.lateral_world import (  # noqa: E402
    add_lateral_retina, freeze_lateral, gains, set_lat_params,
)
from domains.onoff_world import (  # noqa: E402
    add_onoff_retina, add_signed_units, freeze, install_signed_rf, segregation,
    set_params, signed_rf, weights,
)
from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

# Rung 6's geometry and probe constants, REUSED UNCHANGED.
H = W = 16
RF = 7
PERIOD = 4.0


# --------------------------------------------------------------------------- #
#  BUILD  (mechanical anatomy; the arm is graph data)
# --------------------------------------------------------------------------- #
def build(*, seed=0, n_units=6, channels="lateral", eta=5e-4, split=1.0,
          subnorm=1.0, wmax=2.0, centres=None, w0=1.0, lat_eta=2e-3,
          lat_g0=0.0, learn_gain=1.0, compose=1.0):
    """A booted world with rung 7's retina (or rung 6's) under rung 6's SUnits.

    `channels` selects WHICH retina is upstream. `w0` is the SUnit init the w0
    ablation isolated — recorded on every number, and run BOTH ways.
    """
    s, ag = boot_core()
    seeds = ["vision_waves", "vision_onoff"]
    if channels == "lateral":
        seeds += ["vision_lateral", "vision_compose"]
    load_seeds_into(s, ag, seeds)

    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    # The legacy unsigned layer must not learn: oja SELECTED keeps bh_* gated
    # off, eta 0 makes oja_learn an identity. Rung 6's own preamble, unchanged.
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", 0.0)

    w = WaveWorld(s, h=H, w=W, seed=seed)

    if channels == "lateral":
        anat = add_lateral_retina(w)
        bip = anat["bipolars"]
        set_lat_params(w, lateral=1.0, learn_gain=learn_gain, radius2=1.0,
                       lat_eta=lat_eta, lat_gmax=2.0, lat_g0=lat_g0,
                       frozen=0.0)
        for p in w.s.nodes("ComposeParams"):
            w.s.set_attr(p, "compose", float(compose))
    elif channels == "degenerate":
        anat = {"bipolars": None, "hcells": None}
        bip = add_onoff_retina(w)
    else:
        raise ValueError(f"unknown channels={channels!r}")

    us = add_signed_units(w, bip, n_units, rf=RF, seed=seed, centres=centres,
                          w0=w0)
    set_params(w, onoff=1.0, split=split, subnorm=subnorm, oo_eta=eta,
               oo_wmax=wmax, frozen=0.0)
    return w, us, anat, bip


def run_waves(world, steps, *, ignite_every=5):
    """The formative input: the agent's OWN spontaneous waves. Clock only."""
    for i in range(steps):
        world.step(ignite_k=1 if i % ignite_every == 0 else 0)


# --------------------------------------------------------------------------- #
#  FREEZE / PROBE  (rung 6's, unchanged — including rung 5's calibrated OSI)
# --------------------------------------------------------------------------- #
def develop_retina(world, steps=3000, *, ignite_every=5):
    """Bring rung 7's retina to its OWN fixed point BEFORE the cortex is probed
    or trained — with the cortex held inert so only the retina moves.

    THE INSTRUMENT BUG THIS FIXES, found by PROTOCOL §1 before any gate (the
    fourth such fix in this arc; rung 5 found three).

    `lat_g0 = 0.0` means the retina is born a PURE CENTRE — that is rung 7's
    whole point, the surround is GROWN, never installed. But at `g = 0` the
    residual IS the raw centre `c`, and `c >= 0` for a binary wave field, so

        ON  = max(c, 0) = c        OFF = max(-c, 0) = 0

    **the OFF channel is identically DEAD.** MEASURED: at g=0, ON mean 0.5000 /
    OFF mean 0.0000; after 3000 wave steps, gains [0.517, 0.448] and ON 0.1953 /
    OFF 0.1933 — both channels alive and balanced.

    A cortex probed against a dead OFF channel has no signed filter to use, so
    even a PERFECT ideal split-Gabor scored OSI 0.1944 there (vs 1.0000 on rung
    6's channels). That is an INSTRUMENT reading, not a fact about the cortex:
    the composed system's operating state is a DEVELOPED retina, and rung 7's
    every claim (CS 1.0839, SD 0.3601, the sigma ratio 2.007) is measured at
    that fixed point, not at g=0.

    This is not metric surgery (PROTOCOL §5): nothing about the READOUT changed.
    The retina is simply put into the state whose channels this rung exists to
    test. Probing it at g=0 would be measuring rung 7's INIT, not rung 7.
    """
    if not world.s.nodes("LatParams"):
        return
    p = world.s.nodes("OnOffParams")[0]
    old = float(world.s.node(p)["attrs"]["oo_eta"])
    set_params(world, oo_eta=0.0, frozen=1.0)   # cortex inert: only the retina moves
    set_lat_params(world, frozen=0.0)
    run_waves(world, steps, ignite_every=ignite_every)
    set_params(world, oo_eta=old, frozen=0.0)


def freeze_all(world):
    """Freeze BOTH seeds' learning. Rung 6's `freeze` plus rung 7's
    `freeze_lateral` — a probe must not train the retina either, which is the
    composed form of rung 5's `oja=0 IS NOT A FREEZE` lesson."""
    freeze(world)
    if world.s.nodes("LatParams"):
        freeze_lateral(world)


def osi_of(world, units, *, period=PERIOD, key="rate"):
    """Rung 5's probe via rung 6's wrapper, FROZEN, REUSED UNCHANGED."""
    freeze_all(world)
    st = cell_stats(world, units, key=key, period=period)
    return st["osi"], st


def adapt_theta(world, steps=400, *, ignite_every=5):
    """Rung 6's threshold settling: `oo_eta=0` makes the learning rules exact
    identities while `oo_sunit_adapt_theta` still runs — so a reference cell
    gets the SAME theta adaptation the arms get (PROTOCOL §4)."""
    p = world.s.nodes("OnOffParams")[0]
    old = float(world.s.node(p)["attrs"]["oo_eta"])
    set_params(world, oo_eta=0.0, frozen=0.0)
    # The retina must keep running (it supplies the drive theta adapts to), but
    # must not LEARN while we settle theta.
    if world.s.nodes("LatParams"):
        set_lat_params(world, frozen=1.0)
    run_waves(world, steps, ignite_every=ignite_every)
    set_params(world, oo_eta=old)


def ideal_split_gabor(world, u, theta=0.0, phase=0.0, period=PERIOD):
    """Rung 6's PERFECT signed simple cell — the positive control's target."""
    G = gabor(RF, theta, phase, period=period)
    install_signed_rf(world, u, G)
    return G


def drift(w_prev, w_now):
    """PROTOCOL §2's drift: ||w(t) - w(t-d)|| / ||w(t)||."""
    n = float(np.linalg.norm(w_now))
    return float(np.linalg.norm(w_now - w_prev) / n) if n > 0 else float("nan")


__all__ = ["build", "run_waves", "develop_retina", "freeze_all", "osi_of",
           "adapt_theta",
           "ideal_split_gabor", "drift", "weights", "signed_rf", "segregation",
           "gains", "H", "W", "RF", "PERIOD"]
