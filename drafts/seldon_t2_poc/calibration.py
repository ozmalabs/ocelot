"""
Calibration diagnostics for stepped predictive distributions.

PIT (Probability Integral Transform) for a discrete/stepped predictive CDF:
for a continuous F, PIT = F(y) is Uniform(0,1) under calibration. For a discrete
F there is a well-known subtlety: PIT is not uniform even under perfect
calibration because of the jumps. The standard fix is the RANDOMISED PIT
(Czado et al. 2009): draw u ~ Uniform(F(y^-), F(y)), i.e. interpolate uniformly
across the probability jump at the realised value. Under calibration the
randomised PIT is Uniform(0,1). We use that.

We report:
  - a PIT histogram (counts per bin) — flat == calibrated
  - a scalar calibration error: max deviation of empirical PIT CDF from the
    diagonal (a Kolmogorov-style statistic), lower == better calibrated
"""

from __future__ import annotations

import numpy as np


def _cdf_at(values, masses, y):
    """Return (F(y^-), F(y)) for a stepped dist: mass strictly below y, and
    mass at-or-below y."""
    v = np.asarray(values, float)
    p = np.asarray(masses, float)
    p = p / p.sum()
    below = p[v < y].sum()
    at = p[np.isclose(v, y)].sum()
    return below, below + at


def randomised_pit(values, masses, y, rng):
    lo, hi = _cdf_at(values, masses, y)
    if hi <= lo:
        # y not in support at all; place at nearest edge
        return float(np.clip(hi, 0.0, 1.0))
    return float(rng.uniform(lo, hi))


def pit_values(forecasts, outcomes, seed=0):
    """forecasts: list of (values, masses); outcomes: list of y. Returns PITs."""
    rng = np.random.default_rng(seed)
    return np.array([
        randomised_pit(v, m, y, rng) for (v, m), y in zip(forecasts, outcomes)
    ])


def pit_histogram(pits, n_bins=10):
    counts, edges = np.histogram(pits, bins=n_bins, range=(0.0, 1.0))
    return counts, edges


def calibration_error(pits):
    """Max abs deviation of empirical PIT CDF from Uniform CDF (KS statistic)."""
    p = np.sort(pits)
    n = len(p)
    if n == 0:
        return float("nan")
    emp = np.arange(1, n + 1) / n
    # compare to the ideal uniform quantiles p itself
    d_plus = np.max(emp - p)
    d_minus = np.max(p - (np.arange(0, n) / n))
    return float(max(d_plus, d_minus))


def ascii_histogram(counts, width=40):
    total = counts.sum()
    lines = []
    n = len(counts)
    for i, c in enumerate(counts):
        lo = i / n
        hi = (i + 1) / n
        frac = c / total if total else 0
        bar = "#" * int(round(frac * width))
        lines.append(f"  [{lo:.1f},{hi:.1f})  {bar:<{width}} {c:5d} ({frac*100:4.1f}%)")
    return "\n".join(lines)
