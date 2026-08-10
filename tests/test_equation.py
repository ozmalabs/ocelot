"""Equation solving — linear equations isolated by REWRITING on the engine.

The unknown is peeled free of its operations by inverse-operation rewrite rules
(do the same to both sides), to a fixed point ``x = <constant>``. Exact (Fraction).
"""
from __future__ import annotations

from fractions import Fraction

from domains import equation as eq


def test_solves_linear_equations():
    assert eq.solve_for(("+", ("*", 2, "x"), 3), 7) == 2        # 2x+3=7
    assert eq.solve_for(("/", ("-", "x", 1), 2), 3) == 7        # (x-1)/2=3
    assert eq.solve_for(("*", 3, "x"), 12) == 4                 # 3x=12
    assert eq.solve_for(("+", ("/", "x", 3), 2), 5) == 9        # x/3+2=5


def test_swaps_to_keep_unknown_left():
    assert eq.solve_for(5, ("+", ("*", 2, "x"), 1)) == 2        # 5=2x+1
    assert eq.solve_for(("-", 10, "x"), 3) == 7                 # 10-x=3


def test_exact_fractions():
    assert eq.solve_for(("-", ("*", 2, "x"), 1), 4) == Fraction(5, 2)  # 2x-1=4


def test_cannot_isolate_returns_none():
    # unknown on both sides is out of scope (needs a collect step)
    assert eq.solve_for(("+", "x", 1), ("*", 2, "x")) is None
