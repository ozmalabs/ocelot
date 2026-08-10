"""rung6_lib — shared bring-up for RUNG 6 (the signed simple layer).

Mechanical world construction + the calibrated rung-5 probe, reused unchanged.
No decisions.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.onoff_world import (add_onoff_retina, add_signed_units, freeze,  # noqa: E402
                                 set_params, signed_rf, weights,
                                 install_signed_rf, segregation)
from domains.complex_cells import (grating, binarize, present, cell_stats,  # noqa: E402
                                   gabor, THETAS)

H = W = 16
RF = 7
PERIOD = 4.0


def build(*, seed=0, n_units=6, split=1.0, subnorm=1.0, eta=5e-4,
          onoff=1.0, wmax=2.0, centres=None):
    """A booted world with the signed layer wired. Mechanical."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_onoff"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    # The legacy unsigned learning rules must not run: this rung's layer is the
    # SUnit population. oja SELECTED + eta 0 keeps bh_* gated off and makes
    # oja_learn an identity (there are no Units anyway — none are minted).
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", 0.0)
    w = WaveWorld(s, h=H, w=W, seed=seed)
    bip = add_onoff_retina(w)
    us = add_signed_units(w, bip, n_units, rf=RF, seed=seed, centres=centres)
    set_params(w, onoff=onoff, split=split, subnorm=subnorm, oo_eta=eta,
               oo_wmax=wmax, frozen=0.0)
    return w, us, bip


def run_waves(world, steps, *, ignite_every=5):
    """The formative input: the agent's OWN spontaneous waves. Clock only."""
    for i in range(steps):
        world.step(ignite_k=1 if i % ignite_every == 0 else 0)


def osi_of(world, units, *, period=PERIOD, key="rate"):
    """The rung-5 probe, FROZEN, reused UNCHANGED. Returns per-unit OSI.

    `key="rate"` reads the cell's OUTPUT (max(act - theta, 0)) rather than its
    raw drive: a firing rate is what physiology measures and what OSI is defined
    on. The instrument itself — rectification, period 4.0 anti-aliasing, phases
    in isolation, F0 tuning — is rung 5's, untouched."""
    freeze(world)
    st = cell_stats(world, units, key=key, period=period)
    return st["osi"], st


def adapt_theta(world, steps=400, *, ignite_every=5):
    """Let the spike threshold settle on the formative input WITHOUT moving any
    weight: `oo_eta=0` makes both learning rules exact identities, while
    `oo_sunit_adapt_theta` still runs. Mechanical — this is how a reference cell
    (ideal or untrained) is given the SAME threshold adaptation the arms get, so
    a comparison cannot be confounded by theta (PROTOCOL 4: adding a mechanism
    can silently invalidate your control)."""
    old = float(world.s.node(world.s.nodes("OnOffParams")[0])["attrs"]["oo_eta"])
    set_params(world, oo_eta=0.0, frozen=0.0)
    run_waves(world, steps, ignite_every=ignite_every)
    set_params(world, oo_eta=old)


def ideal_split_gabor(world, u, theta=0.0, phase=0.0, period=PERIOD):
    """Install the PERFECT signed simple cell for this architecture: the exact
    rectified split of a Gabor across the two non-negative channels."""
    G = gabor(RF, theta, phase, period=period)
    install_signed_rf(world, u, G)
    return G
