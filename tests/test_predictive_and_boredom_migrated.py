"""predictive-curiosity + boredom, migrated — action-outcome stats + EMAs run in
the WorldAdapter (no CuriousAgent). Covers tests/test_predictive_and_boredom:
record_action_outcome persists running sums on an ActionStat node, and the
failure / boredom EMAs converge to their steady values.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def test_record_action_outcome_stores_sums():
    wa = WorldAdapter()
    wa.record_action_outcome("forward", novelty_delta=5, failure_delta=0.1, boredom_delta=12)
    wa.record_action_outcome("forward", novelty_delta=3, failure_delta=0.2, boredom_delta=8)
    a = wa.action_stat("forward")
    assert a["n"] == 2
    assert a["novelty_sum"] == 8
    assert abs(a["failure_sum"] - 0.3) < 1e-9
    assert a["boredom_sum"] == 20


def test_action_failure_estimate_converges():
    wa = WorldAdapter()
    for _ in range(1000):
        wa.record_action_outcome("attack", failure_delta=0.3)
    assert abs(wa.action_failure_estimate("attack") - 0.3) < 0.01


def test_action_boredom_estimate_converges():
    wa = WorldAdapter()
    for _ in range(1000):
        wa.record_action_outcome("noop", 0, boredom_delta=15)
    assert abs(wa.action_boredom_estimate("noop") - 15.0) < 0.2
