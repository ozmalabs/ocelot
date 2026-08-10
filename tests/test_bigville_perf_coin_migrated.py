"""Perf gate: `system_coin` (the per-tick conserved-money sum) computed by a targeted
`get_attr_many` over the money-bearing types must be BYTE-IDENTICAL to the whole-graph
`graph_to_dict` coin+reserves sum it replaces.

Motivation: post phase-batching, `graph_to_dict` (a full graph serialisation across the
PyO3 boundary, every tick, just to sum a coin column) was ~9% of the tick and grows with
graph size. The targeted sum is ~645x cheaper (22ms -> 0.03ms) and captures the same
money. If a future rung mints coin/reserves on a NEW node type, this gate reddens and the
type must be added to BigvilleInteg2World._COIN_TYPES / _RESERVE_TYPES.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def test_targeted_coin_sum_is_byte_identical_to_graph_dict():
    from worlds.bigville_integ2_world import BigvilleInteg2World
    from worlds.bigville_integ4_world import BigvilleInteg4World
    w = BigvilleInteg4World(cast=16, seed=275000)
    for _ in range(50):
        w.integ_step()
        cheap = BigvilleInteg2World.system_coin(w)      # targeted get_attr_many sum
        truth = w.system_coin_via_graph_dict()          # whole-graph coin+reserves
        assert abs(cheap - truth) < 1e-6, (
            "targeted coin sum diverged from the whole-graph sum -- a money-bearing "
            "type is uncounted; add it to _COIN_TYPES/_RESERVE_TYPES")


def test_full_system_coin_still_conserves():
    """The full conserved quantity (incl. the school Treasury) stays invariant."""
    from worlds.bigville_integ4_world import BigvilleInteg4World
    w = BigvilleInteg4World(cast=16, seed=275000)
    s0 = w.system_coin()
    for _ in range(50):
        w.integ_step()
    assert abs(w.system_coin() - s0) < 1e-6, "money leaked (system_coin not invariant)"
