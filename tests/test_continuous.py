"""Continuous probability — distributions over a continuum, handled by their
closed-form MOMENTS (beyond the finite-discrete probability floor). Exact where
rational.
"""
from __future__ import annotations

from fractions import Fraction

from domains import continuous as c


def test_family_moments():
    assert (c.mean(("gamma", 3, 1)), c.variance(("gamma", 3, 1))) == (3, 3)
    assert (c.mean(("normal", 0, 1)), c.variance(("normal", 0, 1))) == (0, 1)
    assert c.mean(("exponential", 2)) == Fraction(1, 2)
    assert c.variance(("exponential", 2)) == Fraction(1, 4)
    assert c.variance(("uniform", 0, 1)) == Fraction(1, 12)
    assert c.mean(("beta", 2, 3)) == Fraction(2, 5)


def test_affine_and_independent_sums():
    assert c.affine_mean(("normal", 1, 4), 2, 5) == 7          # E[2X+5]=2·1+5
    assert c.affine_variance(("normal", 1, 4), 2) == 16        # Var[2X]=4·4
    # trace of the covariance of an independent vector = Σ component variances
    assert c.covariance_trace([("gamma", 3, 1), ("normal", 0, 2),
                               ("exponential", 2)]) == Fraction(21, 4)
