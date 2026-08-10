"""bigville: WEIGHT slows a laden hauler (goods port -- weight becomes a movement constraint).

Every Good carries its catalog weight (416000). mv_energy_budget now subtracts the mover's carried
weight (Sum of held goods' weight * qty * 0.1) from the move budget -- so a heavy haul costs hops,
while an empty-handed mover is unchanged (the existing movement gates carry nothing). The catalog's
weights drive it; the penalty is a rule (Sum/Minus/Max), the aggregation graph-native.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld, good_code          # noqa: E402
from worlds.bigville_time_world import DAY                                   # noqa: E402
import domains.bigville_entities as E                                        # noqa: E402


def _hauler(load=0):
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("hauler", (2, 2), energy=20, slow_on=0)   # slow_on 0 -> the flat budget path
    if load:
        w.give_good("hauler", good_code("iron"), qty=load)  # iron: catalog weight 3
    w._run()
    return w


# ------------------------------------------------------ G-empty-handed-unchanged (no regression)
def test_an_empty_handed_mover_has_the_full_budget():
    w = _hauler(load=0)
    assert w.carry_weight("hauler") == 0.0, "carrying nothing"
    assert w.budget_of("hauler") == 3, "the full flat move budget -- weight penalty is zero"


# ------------------------------------------------------ G-weight-costs-hops (headline)
def test_a_heavy_load_costs_movement():
    light = _hauler(load=3)                                 # 3 iron = weight 9
    heavy = _hauler(load=10)                                # 10 iron = weight 30
    assert light.carry_weight("hauler") == 9.0 and heavy.carry_weight("hauler") == 30.0
    assert light.budget_of("hauler") == 2, "a light load costs a hop (3 - 0.9)"
    assert heavy.budget_of("hauler") == 0, "a heavy load stops the hauler (3 - 3.0)"
    assert heavy.budget_of("hauler") < light.budget_of("hauler") < 3, "heavier -> fewer hops"


# ------------------------------------------------------ G-weight-is-catalog-driven (headline)
def test_the_penalty_tracks_the_catalog_weight():
    # timber is bulkier/heavier than iron per unit -- the catalog weight drives the load
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("hauler", (2, 2), energy=20, slow_on=0)
    w.give_good("hauler", good_code("timber"), qty=2)       # timber weight 2
    w._run()
    assert w.carry_weight("hauler") == 2 * E.ITEMS["timber"]["weight"], "carried weight = catalog weight * qty"
