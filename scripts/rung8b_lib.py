"""rung8b_lib — RUNG 8B's harness: GCAL's SETPOINT THETA, on rung 8's composition.

PROTOCOL §10: the engine is pinned by `engine_preamble()` (via `rung8_lib`) and
every number is reported with `provenance_line()`.

WHAT THIS RUNG IS
-----------------
Rung 8 stopped at the PROTOCOL §1 calibration gate: an **IDEAL** split-Gabor
scored **OSI 0.1290** on the composed pathway against **1.0000** on rung 6's own
channels. A perfect cell could not be seen, so no arm was interpretable and
H1/H2 were never tested. Its measured cause:

    theta is an EMA of the cell's own drive on the FORMATIVE input, and rung 7's
    retina is a PREDICTIVE CODER. Waves are cheap (act 0.861 — the surround
    predicts the centre, which is exactly what rung 7 earned); an
    out-of-distribution period-4 grating is expensive (act 1.902, 2.21x). theta
    lands at 0.774, BELOW the probe drive, so the iceberg never bites.

THE HYPOTHESIS IS A FIDELITY CLAIM, NOT A PARAMETER SEARCH
-----------------------------------------------------------
Rung 6's `oo_sunit_adapt_theta` CITES GCAL and implements something structurally
different (`VISION_RUNG8B_PREREG.md` §2):

    GCAL (Stevens et al. 2013, Eqs 7-8)   |  rung 6's rule
    rbar <- beta*rbar + (1-beta)*RATE     |  theta <- theta + rate*(ACT - theta)
    theta <- theta + lambda*(rbar - MU)   |
    tracks the cell's OUTPUT              |  tracks the cell's INPUT drive
    error is a deviation from a SETPOINT  |  error is a deviation from ITSELF
    fixed point: mean OUTPUT = mu         |  fixed point: theta = mean INPUT
    integral feedback with a setpoint     |  a low-pass FOLLOWER

**Ours regulates nothing.** Rung 6 took GCAL's PLACEMENT (outside the learning
rule, where theta cannot flip dw's sign — correctly, and that is why it never
annihilated like BCM) and dropped GCAL's SETPOINT. Rung 8's §I.1 named the
consequence exactly: *"nothing there pins its SCALE across distributions."*
**mu is what pins it.**

THE MEASUREMENT PROTOCOL: ADAPT -> FREEZE -> MEASURE
-----------------------------------------------------
`adapt_theta_on(world, stim, steps)` equilibrates theta on the ensemble being
RESPONDED TO, with orientation and phase interleaved at random every step so
theta's timescale averages over many orientations by construction. Then
`pin_theta()` sets `theta_adapt = 0` and the probe runs against a FROZEN theta.

This is ADAPTATION, not training, and the distinction is not a convenience:

  * WEIGHTS stay frozen throughout (`frozen=1`), verified `max|dw| = 0`;
  * theta CANNOT flip dw's sign — that is precisely why rung 6 put it where GCAL
    puts it — so with weights frozen, theta's adaptation changes no weight;
  * theta is PINNED during the measurement itself, verified `dtheta = 0`, so the
    probe never chases theta (rung 6's own discipline, kept).

THE GATE IS SEPARATION, NOT THE IDEAL ALONE
--------------------------------------------
Raising theta raises the ideal score AND the floor: OSI `argmax`-selects over 12
orientations, so clipping the orthogonal response to 0 inflates a RANDOM cell
toward 1.0 just as it does an ideal one. So floor and ideal are measured under
the SAME theta rule, IN-RUN, never inherited (OSI's floor is init-dependent:
0.0044 DC / 0.3899 signed / 0.3168 rung 6 / 0.0205 rung 8 composed — four values,
one probe).

`seeds/vision_onoff.json` and `seeds/vision_lateral.json` are NOT edited
(PROTOCOL §11.4; rung 8's "compose, don't modify"). The GCAL arm sets rung 6's
existing `homeo = 0`, which PINS its EMA rule — its own documented meaning — so
the two theta rules can never both fire.
"""
from __future__ import annotations

import numpy as np

from scripts.rung8_lib import (  # noqa: F401  (engine_preamble runs on import)
    PERIOD, RF, H, W, build as _rung8_build, develop_retina, drift, freeze_all,
    ideal_split_gabor, osi_of, run_waves,
)

from domains.complex_cells import THETAS, binarize, grating, present
from domains.onoff_world import set_params, weights as _oo_weights
from substrate.boot_core import load_seeds_into

__all__ = ["build8b", "set_theta_params", "pin_theta", "adapt_theta_on",
           "grating_ensemble", "wave_ensemble", "theta_of", "rbar_of",
           "weights_of", "GCAL_MU", "GCAL_BETA", "GCAL_LAMBDA"]

# GCAL's PUBLISHED constants (Stevens, Law, Antolik & Bednar 2013, Eqs 7-8;
# VISION_PRIOR_ART.md §2.2). LITERAL and UNMODIFIED, ONE set for both pathways.
# Moving these after seeing a score is the parameter search the pre-registration
# forbids (VISION_RUNG8B_PREREG.md §4).
GCAL_MU = 0.024
GCAL_BETA = 0.991
GCAL_LAMBDA = 0.01


# --------------------------------------------------------------------------- #
#  BUILD  (mechanical anatomy; every arm is graph data — PROTOCOL §0)
# --------------------------------------------------------------------------- #
def build8b(*, seed=0, n_units=6, channels="lateral", theta_mode=1.0, **kw):
    """Rung 8's composed world, plus `vision_theta`.

    `theta_mode=1` selects GCAL's setpoint homeostat AND pins rung 6's EMA rule
    (`homeo=0`), so the two can never both fire. `theta_mode=0` reproduces rung 8
    exactly — the seed is inert and rung 6's rule runs untouched (PROTOCOL §9).
    """
    w, us, anat, bip = _rung8_build(seed=seed, n_units=n_units,
                                    channels=channels, **kw)
    load_seeds_into(w.s, w.s.nodes("Agent")[0], ["vision_theta"])
    set_theta_params(w, theta_mode=theta_mode, theta_adapt=0.0,
                     theta_mu=GCAL_MU, theta_beta=GCAL_BETA,
                     theta_lambda=GCAL_LAMBDA)
    if theta_mode > 0.5:
        # Rung 6's EMA theta is PINNED by its OWN documented knob. Its seed is
        # not edited (PROTOCOL §11.4).
        set_params(w, homeo=0.0)
        # GCAL Eq 7's published initial condition: rbar(0) = mu. Mechanical
        # state init by the world adapter, no decision.
        for u in us:
            w.s.set_attr(u, "rbar", float(GCAL_MU))
            w.s.set_attr(u, "rbar_step", -1.0)
    return w, us, anat, bip


def set_theta_params(world, **kw):
    """Write ThetaParams knobs. Every arm runs through this — the agent's own
    configuration (PROTOCOL §0), never a Python branch."""
    for p in world.s.nodes("ThetaParams"):
        for k, v in kw.items():
            world.s.set_attr(p, k, float(v))


def pin_theta(world):
    """FREEZE theta. The probe must never chase it (rung 6's discipline)."""
    set_theta_params(world, theta_adapt=0.0)


# --------------------------------------------------------------------------- #
#  THE ENSEMBLES  (mechanical stimulus generation)
# --------------------------------------------------------------------------- #
def grating_ensemble(world, rng):
    """One draw from the PROBE's own stimulus family: orientation AND phase
    interleaved at random. Interleaving is what separates theta's timescale from
    the sweep — a theta fast enough to track ONE orientation would cancel the
    very modulation OSI measures (PREREG §6's two-sided hazard)."""
    th = float(rng.choice(THETAS))
    ph = float(rng.uniform(0, 2 * np.pi))
    return binarize(grating((world.h, world.w), th, ph, PERIOD))


def wave_ensemble(world, rng):
    """The FORMATIVE ensemble, as an unstructured field at the waves' duty
    cycle. Used only to measure what theta does when adapted to the input it
    developed on — the control for the ensemble-transfer claim."""
    return (rng.random((world.h, world.w)) > 0.5).astype(np.float32)


# --------------------------------------------------------------------------- #
#  ADAPT -> FREEZE -> MEASURE
# --------------------------------------------------------------------------- #
def adapt_theta_on(world, steps=2000, *, stim="grating", seed=7,
                   track_every=0):
    """Equilibrate theta on the ensemble being RESPONDED TO, weights FROZEN.

    Returns the per-checkpoint theta trace when `track_every > 0`, for PROTOCOL
    §2's convergence check applied to theta itself — *does the rule settle on
    its own input*, the boring measurement that cracked rung 2.
    """
    rng = np.random.default_rng(seed)
    draw = grating_ensemble if stim == "grating" else wave_ensemble
    # WEIGHTS FROZEN, theta free. This combination is the whole point: theta's
    # placement (outside the learning rule) is what makes it separable.
    freeze_all(world)
    set_theta_params(world, theta_adapt=1.0)
    trace = []
    for i in range(steps):
        present(world, draw(world, rng))
        if track_every and (i + 1) % track_every == 0:
            trace.append(theta_of(world))
    pin_theta(world)
    return np.array(trace) if track_every else None


def theta_of(world):
    return np.array([float(world.s.node(u)["attrs"].get("theta", np.nan))
                     for u in world.s.nodes("SUnit")])


def rbar_of(world):
    return np.array([float(world.s.node(u)["attrs"].get("rbar", np.nan))
                     for u in world.s.nodes("SUnit")])


def weights_of(world, units):
    """Rung 6's own stable-ordered weight read, reused unchanged — for the
    max|dw| freeze audit. `oja=0 IS NOT A FREEZE` was rung 5's worst instrument
    bug; this rung re-measures the freeze rather than trusting it."""
    return _oo_weights(world, units)
