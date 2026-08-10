"""Continuous probability — distributions over a continuum, beyond the finite-
discrete probability floor.

The discrete floor sums weights over finitely many outcomes; a continuous
distribution has none to enumerate. It is handled by its MOMENTS instead — the
closed-form mean and variance of each family — and by the algebra of moments
under affine maps and independent sums. That is enough for the questions that
ask for an expectation, a variance, or the trace of a covariance matrix (the
sum of the component variances of an independent vector).

A distribution is a tuple ``(family, *params)``; exact where rational (Fraction).
"""
from __future__ import annotations

from fractions import Fraction


def _F(x):
    return x if isinstance(x, float) else Fraction(x)


def mean(dist):
    """E[X] for a distribution ``(family, *params)``."""
    fam, *p = dist
    if fam == "normal":           # (mu, var)
        return p[0]
    if fam == "gamma":            # (shape k, scale theta)  → k·theta
        return _F(p[0]) * _F(p[1])
    if fam == "exponential":      # (rate lambda)           → 1/lambda
        return Fraction(1) / _F(p[0])
    if fam == "uniform":          # (a, b)                  → (a+b)/2
        return (_F(p[0]) + _F(p[1])) / 2
    if fam == "beta":             # (alpha, beta)           → a/(a+b)
        return _F(p[0]) / (_F(p[0]) + _F(p[1]))
    if fam == "poisson":          # (lambda)                → lambda
        return _F(p[0])
    raise KeyError(f"unknown distribution family '{fam}'")


def variance(dist):
    """Var[X] for a distribution ``(family, *params)``."""
    fam, *p = dist
    if fam == "normal":
        return p[1]
    if fam == "gamma":            # k·theta²
        return _F(p[0]) * _F(p[1]) ** 2
    if fam == "exponential":      # 1/lambda²
        return Fraction(1) / _F(p[0]) ** 2
    if fam == "uniform":          # (b-a)²/12
        return (_F(p[1]) - _F(p[0])) ** 2 / 12
    if fam == "beta":             # ab / ((a+b)²(a+b+1))
        a, b = _F(p[0]), _F(p[1])
        return a * b / ((a + b) ** 2 * (a + b + 1))
    if fam == "poisson":
        return _F(p[0])
    raise KeyError(f"unknown distribution family '{fam}'")


def affine_mean(dist, a, b):
    """E[aX + b] = a·E[X] + b."""
    return _F(a) * _F(mean(dist)) + _F(b)


def affine_variance(dist, a):
    """Var[aX + b] = a²·Var[X]."""
    return _F(a) ** 2 * _F(variance(dist))


def covariance_trace(dists):
    """The trace of the covariance matrix of an INDEPENDENT random vector — the
    sum of the component variances (off-diagonal covariances are 0)."""
    total = Fraction(0)
    for d in dists:
        total += _F(variance(d))
    return total
