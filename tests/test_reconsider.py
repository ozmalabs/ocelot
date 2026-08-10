"""When the default plan's complexity blows the budget, the agent RECONSIDERS
— it asks "is there a more efficient way?" and "is this in a special form I
can exploit (G+X, sparse n, …)?" — before giving up. Encoded as ALTERNATIVES
per concept: each has a cheaper estimator + a body that may raise _CantApply
when its assumptions don't hold.
"""
from __future__ import annotations

import pytest

from domains.reason import (
    answer_within, BudgetExceeded, reconsider,
    _largest_prime_factor_strip_smalls, _CantApply,
)


def test_default_plan_runs_when_budget_allows():
    ans, est, strategy = answer_within(
        "What is the largest prime divisor of 8139881", {}, 1e8)
    assert ans == 5003
    assert strategy == "default"
    assert est < 1e4


def test_reconsider_strips_small_primes_for_structured_huge_n():
    # 10^100 = 2^100 × 5^100 — default would be ~10^50 ops, way over budget.
    # The strip-small-primes alternative finds it in ~200k ops, returns 5.
    big = 10 ** 100
    ans, est, strategy = answer_within(
        f"What is the largest prime divisor of {big}", {}, 1e8)
    assert ans == 5
    assert strategy == "reconsider:strip_small_primes"
    assert est <= 1e6                            # cheap, but the strategy ran


def test_reconsider_declines_when_no_alternative_applies():
    # an n that's the product of two primes both larger than the small-bound —
    # the strip-small-primes alternative can't help, no other alternative exists,
    # so the agent honestly says it can't afford this one
    p, q = 982451653, 1000000007                 # both prime, both > 1e5
    n = p * q
    with pytest.raises(BudgetExceeded) as exc:
        answer_within(f"What is the largest prime divisor of {n}", {}, 1e8)
    assert "no_alternative" in str(exc.value)


def test_reconsider_picks_strategy_by_cost_then_applicability():
    # call reconsider directly with controlled args — strip_small_primes is the
    # only alternative for largest_prime_factor and DOES apply for 12 = 2^2 × 3
    ans, est, strategy = reconsider("largest_prime_factor", {"of": 12}, 1e8)
    assert ans == 3
    assert strategy == "strip_small_primes"
    assert est < 1e6


def test_alternative_can_signal_cant_apply():
    # the alternative body raises _CantApply when its structural assumptions
    # don't hold — caller catches and falls through to other alternatives /
    # ultimately to BudgetExceeded
    big_p = 982451653 * 1000000007              # composite of two big primes
    with pytest.raises(_CantApply):
        _largest_prime_factor_strip_smalls({"of": big_p})
