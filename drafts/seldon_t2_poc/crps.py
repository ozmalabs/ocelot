"""
CRPS for stepped / empirical predictive distributions.

The load-bearing correctness module. A Seldon-manifold-with-confidence forecast
is, per (entity, horizon), a set of reachable integer cells (the manifold
support) with a stepped credence mass on each cell (the confidence dimension).
That is exactly a discrete predictive distribution given as (value, mass) pairs,
and CRPS has a closed form on it.

CRPS definition (lower is better; units = units of the observation):

    CRPS(F, y) = integral_{-inf}^{+inf} ( F(x) - 1{x >= y} )^2 dx

where F is the predictive CDF and y is the realised outcome.

For a stepped predictive distribution with support values v_1 < v_2 < ... < v_K
and probability masses p_k (sum p_k = 1), the CDF is a right-continuous step
function. This module computes CRPS by the exact piecewise integral, and also
provides the well-known energy-score / sample form as an independent check:

    CRPS(F, y) = E|X - y| - 0.5 * E|X - X'|

where X, X' are independent draws from F. For a discrete distribution this is
exact (no sampling error), so the two implementations must agree to machine
precision. That mutual agreement is the correctness gate.

References the two textbook special cases used as unit tests:
  - Point mass at m:            CRPS = |m - y|      (so CRPS reduces to abs error / MAE)
  - Empirical dist over sample: matches the energy form above.
"""

from __future__ import annotations

import numpy as np


def _normalise(values, masses):
    """Merge duplicate support points, sort, drop zero mass, renormalise."""
    values = np.asarray(values, dtype=float)
    masses = np.asarray(masses, dtype=float)
    if values.shape != masses.shape:
        raise ValueError("values and masses must have the same shape")
    if np.any(masses < -1e-12):
        raise ValueError("masses must be non-negative")
    masses = np.clip(masses, 0.0, None)
    total = masses.sum()
    if total <= 0:
        raise ValueError("total mass must be positive")
    masses = masses / total
    # merge duplicate values
    order = np.argsort(values, kind="mergesort")
    values = values[order]
    masses = masses[order]
    uniq_vals, inv = np.unique(values, return_inverse=True)
    merged = np.zeros_like(uniq_vals, dtype=float)
    np.add.at(merged, inv, masses)
    return uniq_vals, merged


def crps_stepped(values, masses, y):
    """Exact CRPS of a stepped predictive distribution via the piecewise integral.

    values, masses : support points and their probability masses (need not be
                     sorted or normalised; this function normalises).
    y              : the realised outcome (scalar).

    Method. Sort the support v_1<...<v_K with cumulative CDF levels
    c_k = sum_{j<=k} p_j (c_K = 1). The CDF is 0 below v_1, equals c_k on
    [v_k, v_{k+1}), and 1 at/after v_K. The integrand (F(x)-1{x>=y})^2 is
    piecewise constant on the intervals defined by the support points *and* y.
    We integrate constant^2 * width over each such interval. Contributions from
    the two unbounded tails vanish because the integrand is 0 there (F=0 and
    x<y on the left tail; F=1 and x>=y on the right tail).
    """
    v, p = _normalise(values, masses)
    y = float(y)
    cdf = np.cumsum(p)  # c_k at v_k, right-continuous

    # Build the ordered set of breakpoints: all support points plus y.
    # Between consecutive breakpoints, both F(x) and 1{x>=y} are constant.
    breaks = np.unique(np.concatenate([v, [y]]))

    total = 0.0
    # For an interval [a, b): F(x) = cdf value for the largest support <= a.
    # (F is right-continuous: F(v_k) already includes p_k.)
    for a, b in zip(breaks[:-1], breaks[1:]):
        width = b - a
        if width <= 0:
            continue
        # F on [a, b): number of support points <= a, take that cumulative level
        idx = np.searchsorted(v, a, side="right") - 1
        F = cdf[idx] if idx >= 0 else 0.0
        indicator = 1.0 if a >= y else 0.0  # 1{x>=y} constant on (a,b) since y is a breakpoint
        diff = F - indicator
        total += diff * diff * width
    return total


def crps_energy(values, masses, y):
    """CRPS via the energy-score identity, exact for a discrete distribution.

        CRPS = E|X - y| - 0.5 * E|X - X'|

    Computed exactly by summing over the discrete support (no Monte Carlo).
    Used as an independent cross-check of crps_stepped.
    """
    v, p = _normalise(values, masses)
    y = float(y)
    e_xy = np.sum(p * np.abs(v - y))
    # E|X - X'| = sum_{i,j} p_i p_j |v_i - v_j|
    diff = np.abs(v[:, None] - v[None, :])
    e_xx = np.sum((p[:, None] * p[None, :]) * diff)
    return e_xy - 0.5 * e_xx


def crps_sample(sample, y):
    """CRPS of the empirical distribution of a raw sample (equal weights)."""
    sample = np.asarray(sample, dtype=float)
    masses = np.ones_like(sample) / len(sample)
    return crps_stepped(sample, masses, y)


def crps_point(m, y):
    """CRPS of a point mass at m: equals |m - y|."""
    return abs(float(m) - float(y))
