"""Analysis — limits, derivatives, integrals: the mathematics of the LIMIT.

The earlier floors are finite/discrete; analysis is about what a process
APPROACHES. So its grounding is genuinely a limiting computation: a limit is
the value a sequence converges to, a derivative is the limit of difference
quotients, an integral is the limit of Riemann sums. We ground them
computationally — evaluate the process and detect convergence — which is what
"grounding a limit" honestly means (you cannot store infinitely many terms; you
take the process far enough to see where it goes). This is the continuous-world
analogue of "infinity is recursion": a limit is a process pushed to its horizon.

Functions/sequences are Python callables here (the continuous input doesn't sit
on the integer number floor); convergence is checked to a tolerance.
"""
from __future__ import annotations


def limit_of_sequence(seq, max_n: int = 10**6, tol: float = 1e-7):
    """The value a sequence approaches at its horizon, or None if it does not
    settle. Sample far-out terms; converged iff the differences are within
    ``tol`` OR strictly shrinking (the sequence is closing in); the far term is
    the estimate. (Diverging sequences — differences growing — return None.)"""
    a, b, c = seq(max_n), seq(max_n // 2), seq(max_n // 4)
    d1, d2 = abs(a - b), abs(b - c)
    if d1 <= tol or d1 < d2 * 0.999:
        return a
    return None


def converges_to(seq, L: float, tol: float = 1e-5) -> bool:
    """Does the sequence approach L? Its horizon estimate is within ``tol`` of L
    (uses :func:`limit_of_sequence`, so slow convergence is handled)."""
    lim = limit_of_sequence(seq)
    return lim is not None and abs(lim - L) < tol


def series_sum(term, max_n: int = 200000, tol: float = 1e-12):
    """Σ term(k) for k=1.. : the limit of the partial sums (None if divergent)."""
    total, prev = 0.0, None
    stable = 0
    for k in range(1, max_n + 1):
        total += term(k)
        if prev is not None and abs(total - prev) < tol:
            stable += 1
            if stable >= 10:
                return total
        else:
            stable = 0
        prev = total
    return total


def derivative(f, x: float, h: float = 1e-6) -> float:
    """f′(x) as the (symmetric) limit of difference quotients."""
    return (f(x + h) - f(x - h)) / (2 * h)


def integral(f, a: float, b: float, n: int = 100000) -> float:
    """∫ₐᵇ f — the limit of Riemann sums (midpoint rule)."""
    dx = (b - a) / n
    return sum(f(a + (i + 0.5) * dx) for i in range(n)) * dx
