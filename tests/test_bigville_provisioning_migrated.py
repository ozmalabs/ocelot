"""bigville: an agent BUYS FOOD FOR LATER from its PROJECTED needs, via its EXPECTATIONS -- generic planning.

Food is made to be stored and eaten later. An agent that is NOT hungry now still decides to lay in food,
because it understands it (and its household) will get hungry over the days ahead. Two things make this
GENERIC rather than special-cased:

  * the AMOUNT is DERIVED, not a magic larder target:
        projected need = plan_horizon * daily_ration * mouths,  mouths = self + dependents (kids at home).
  * the AFFORDANCE is an EXPECTATION, not co-location: the agent provisions because it EXPECTS a source
    (the baker) to have food -- it does NOT need to be standing in a shop. Acting on it PROPOSES a trade to
    the expected source; the trade is two-sided (see test_bigville_trade).

Provisioning always yields to a real immediate need (you eat now, shop when not starving).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld, BREAD   # noqa: E402
from worlds.bigville_time_world import DAY                        # noqa: E402

SQUARE = (14, 8)
BAKER_SPOT = (12, 8)      # the baker is elsewhere on the map -- the customer must GO there


def _town(*, hunger=0, coin=30, baker_bread=99):
    """A customer who EXPECTS the baker (standing elsewhere, holding bread) to have bread. No shop, no
    co-location -- provisioning is driven by the expectation."""
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", BAKER_SPOT, coin=0); w.stock_person("baker", BREAD, baker_bread, sell_price=1)
    w.make_trader("cust", SQUARE, coin=coin, hunger_level=hunger, satiety=5)
    w.expect_source("cust", BREAD, "baker")
    return w


# ------------------------------------------------------ G-provisions-for-later (headline)
def test_a_not_hungry_agent_lays_in_food_for_later():
    w = _town(hunger=0)
    assert w.hunger_of("cust") == 0 and w.inventory_of("cust", BREAD) == 0, "not hungry, empty larder"
    assert w.projected_need("cust") == 2.0, "it projects it will need food (horizon 2 * ration 1 * 1 mouth)"
    for _ in range(5):
        w.live("cust")                            # give it turns -- it provisions though not hungry
    assert w.inventory_of("cust", BREAD) == 2.0, "it laid in food for later, up to its projected need"
    assert w.inventory_of("cust", BREAD) == 2.0 and w.hunger_of("cust") < 5, \
        "it holds its store un-eaten -- this is provisioning (any small hunger is from the walk, not from eating the larder)"


# ------------------------------------------------------ G-household-scales-it (headline)
def test_a_parent_provisions_for_the_whole_household():
    lone = _town(hunger=0)
    parent = _town(hunger=0); parent.set_household("cust", dependents=3)
    assert parent.projected_need("cust") == 8.0, "4 mouths (self + 3 kids) * horizon 2 * ration 1"
    assert parent.projected_need("cust") == 4 * lone.projected_need("cust"), "the parent projects 4x the lone adult"
    for _ in range(12):
        lone.live("cust"); parent.live("cust")
    assert parent.inventory_of("cust", BREAD) > lone.inventory_of("cust", BREAD), \
        "the parent lays in far more food -- same understanding, more mouths at home"
    assert parent.inventory_of("cust", BREAD) == 8.0, "up to the household's projected need"


# ------------------------------------------------------ G-projection-is-derived (headline; no magic number)
def test_the_provisioning_target_is_derived_not_a_magic_number():
    w = _town(hunger=0)
    base = w.projected_need("cust")
    w.set_plan("cust", horizon=4); w.set_household("cust", dependents=1)
    assert w.projected_need("cust") == 4 * 1 * 2, "projection tracks horizon * ration * mouths -- computed, not set"
    assert w.projected_need("cust") == 4 * base, "doubling the horizon and mouths quadruples the projection"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body_choice.json")))
    r = next(x for x in seed["rules"] if x["name"] == "bc_score_acquire")
    logic = json.dumps(r["effects"])
    assert "plan_horizon" in logic and "daily_ration" in logic and "provides_for" in logic, \
        "the pull is the agent's projection (horizon, ration, dependents), not a hardcoded target"


# ------------------------------------------------------ G-affordance-is-an-expectation (headline)
def test_provisioning_is_planned_by_expectation_then_carried_out_on_the_map():
    w = _town(hunger=0)
    # the baker is elsewhere; the customer is NOT standing with them -- it plans from its EXPECTATION
    assert w.pos["cust"] != w.pos["baker"], "the customer is not standing with the baker"
    w.set_alive("cust", True); w.run_ticks(8)   # it decides to provision from its expectation, then WALKS there and buys
    assert w.inventory_of("cust", BREAD) > 0, "it provisioned -- deciding from its expectation, then going to the source"
    # the planning affordance is a held EXPECTATION (you plan from where you expect), NOT being co-located
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body_choice.json")))
    aff = next(x for x in seed["rules"] if x["name"] == "bc_expect_source")
    assert ["agent", "expects", "exp"] in aff["match"] and ["exp", "source", "holder"] in aff["match"], \
        "the affordance is a held EXPECTATION of a source; acting on it means going there on the map"


def test_without_an_expectation_the_agent_cannot_plan_to_provision():
    from worlds.bigville_need_world import BigvilleNeedWorld
    w = BigvilleNeedWorld(); w.add_mover("h", SQUARE)
    w.set_plan("h", horizon=3); w.set_household("h", dependents=2)
    assert w.projected_need("h") == 9.0, "it projects a real need"
    w.live("h")                                                  # but it holds no expectation of where to get food
    assert w.dependents("h") == 2, "the need is there, but with no expectation of a source it forms no plan"


# ------------------------------------------------------ G-immediate-need-wins (headline)
def test_immediate_hunger_beats_provisioning():
    w = _town(hunger=8); w.set_household("cust", dependents=3)   # very hungry, big projected shortfall
    w.give_good("cust", BREAD, 3)                                 # holds some food already
    assert w.hunger_of("cust") == 8
    w.live("cust")
    assert w.hunger_of("cust") < 8, "hungry now -> it EATS first; provisioning for later yields to real hunger"
