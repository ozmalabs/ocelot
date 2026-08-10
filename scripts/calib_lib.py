"""calib_lib — THE CALIBRATION REFRAME: is the waves' job to place a REFERENCE?

Shared bring-up + the calibration measure. Mechanical composition over
`rung6_lib` / `onoff_world` / `complex_cells`. No decisions, no new rules.

THE CRITERION (formalised, see VISION_CALIBRATION_PREREG.md):

    A unit is CALIBRATED iff its operating point sits INSIDE the signal's
    dynamic range, i.e. its evoked peak is separable from its spontaneous
    rate.  The statistic is rung 6's own

        RPI = peak / base = max_theta F0(theta) / baseline

    where `baseline` is the response to unstructured fields at the SAME duty
    cycle (complex_cells.baseline). RPI -> 1 means the cell cannot tell
    structure from noise (uncalibrated: theta too low, DC-swamped, or too
    high, silent). Rung 6's references: untrained floor 1.96, ideal split
    Gabor 6.44.

    RPI is a RATIO of two rates, so it is invariant to overall gain. That is
    deliberate: it measures the PLACEMENT of the operating point, not the
    scale of the response.

THE DECOMPOSITION THIS LIBRARY EXISTS TO MAKE (the reframe's sharp claim):

    `theta_only`  -- adapt_theta on an input with oo_eta=0: the REFERENCE is
                     placed, NO weight moves. This is CALIBRATION, isolated.
    `full`        -- the same input with learning armed: reference + content.
    `nocal`       -- theta pinned at 0 (homeo=0): NO reference at all.

    CALIBRATION account: full ~= theta_only  >> nocal.  The waves' job is the
                         reference; content learning adds nothing.
    TEACHING account   : full  >  theta_only.  The statistics are the point.

Engine provenance is recorded by every caller (PROTOCOL 10).
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains.onoff_world import set_params, freeze  # noqa: E402
from domains.complex_cells import cell_stats  # noqa: E402
from scripts.rung6_lib import (build, run_waves, adapt_theta,  # noqa: E402
                               ideal_split_gabor, PERIOD, RF, H, W)

__all__ = ["build", "run_waves", "adapt_theta", "ideal_split_gabor",
           "rpi_of", "arm_rpi", "PERIOD", "RF", "H", "W"]


def rpi_of(world, units, *, period=PERIOD, key="rate"):
    """THE CALIBRATION MEASURE. Returns (rpi_per_unit, stats).

    RPI = peak/base, read through rung 6's FROZEN probe, unchanged. `freeze`
    is rung 6's real freeze (gates every learning rule INCLUDING theta's
    adaptation -- adaptation is plasticity, and a probe that let theta chase
    the probe stimulus would be the instrument training itself).
    """
    freeze(world)
    st = cell_stats(world, units, key=key, period=period)
    peak = st["tuning"].max(axis=1)
    base = st["baseline"]
    rpi = peak / np.maximum(base, 1e-9)
    return rpi, st


def arm_rpi(arm, seed, *, steps=1600, theta_steps=400, eta=5e-4, n_units=6):
    """Run ONE arm on ONE seed; return (mean RPI, mean OSI, max|dw|).

    Arms are DATA-selected (PROTOCOL 0) -- no Python branch decides anything
    about the graph; each name only picks which params the adapter writes and
    how many mechanical steps of the clock it advances.

      nocal      : homeo=0 (theta pinned 0), no learning. NO reference.
      theta_only : homeo=1, oo_eta=0. Reference placed by the input, weights
                   untouched. CALIBRATION, ISOLATED.
      full       : homeo=1, oo_eta=eta. Reference + content learning.
    """
    w, us, _ = build(seed=seed, n_units=n_units, eta=eta)
    w0 = _weights_snapshot(w, us)

    if arm == "nocal":
        set_params(w, homeo=0.0, oo_eta=0.0)
        run_waves(w, theta_steps)
    elif arm == "theta_only":
        set_params(w, homeo=1.0)
        adapt_theta(w, steps=theta_steps)
    elif arm == "full":
        set_params(w, homeo=1.0)
        adapt_theta(w, steps=theta_steps)
        set_params(w, oo_eta=eta, frozen=0.0)
        run_waves(w, steps)
    else:
        raise ValueError(f"unknown arm {arm!r}")

    dw = float(np.abs(_weights_snapshot(w, us) - w0).max())
    rpi, st = rpi_of(w, us)
    return float(np.mean(rpi)), float(np.mean(st["osi"])), dw


def _weights_snapshot(world, units):
    from domains.onoff_world import weights
    return np.concatenate([np.asarray(weights(world, u), float).ravel()
                           for u in units])
