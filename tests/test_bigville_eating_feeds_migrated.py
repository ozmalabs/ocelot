"""bigville: EATING feeds you -- BUYING does not. They are different acts.

A purchase (be_exchange) moves coin<->good into the bag; it no longer touches hunger. What relieves
hunger is EATING a held good (bd_meal_feeds: a meal's `feeds` drops hunger_level). So the loop is
buy -> hold -> eat -> fed, and you can only eat what you actually hold. This also closes the exertion
loop: hard work raises hunger, and only eating brings it back down.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld, BREAD, GRAIN, BAKING   # noqa: E402
from worlds.bigville_time_world import DAY                                       # noqa: E402
from worlds.bigville_need_world import BigvilleNeedWorld                         # noqa: E402

BAKER_CELL = (2, 2)


def _bought_bread(hunger=8, satiety=5):
    """A customer co-located with an open, stocked baker, who has just BOUGHT one bread."""
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", BAKER_CELL); w.set_skill("baker", BAKING, 3)
    w.add_shop("bakery", good=BREAD, price=4, cell=BAKER_CELL, keeper="baker",
               activity=BAKING, input_good=GRAIN, stock=3, input_qty=2)
    w.make_trader("cust", BAKER_CELL, coin=10, hunger_level=hunger, satiety=satiety)
    w.give_good("cust", BREAD)
    w.set_hours(1); w.refresh_open()
    w.buy("cust")
    return w


# ------------------------------------------------------ G-buying-does-not-feed (headline)
def test_buying_fills_the_bag_but_does_not_feed():
    w = _bought_bread(hunger=8)
    assert w.inventory_of("cust", BREAD) == 1, "the bought bread is in the bag"
    assert w.hunger_of("cust") == 8, "buying did NOT feed him -- hunger is unchanged"


# ------------------------------------------------------ G-eating-feeds (headline)
def test_eating_the_held_bread_feeds_him():
    w = _bought_bread(hunger=8, satiety=5)
    w.eat("cust", BREAD)
    assert w.hunger_of("cust") == 3, "eating the bread drops hunger 8->3 (fed by the meal)"
    assert w.inventory_of("cust", BREAD) == 0, "and the bread is consumed from the bag"


def test_you_can_only_eat_what_you_hold():
    w = _bought_bread(hunger=8)
    w.eat("cust", BREAD)                                  # eats the one loaf
    assert w.hunger_of("cust") == 3 and w.inventory_of("cust", BREAD) == 0
    again = w.eat("cust", BREAD)                          # nothing left to eat
    assert again == 3, "with an empty bag, eating does nothing -- you cannot eat bread you don't have"


# ------------------------------------------------------ G-the-model-is-a-rule (source audit)
def test_purchase_no_longer_touches_hunger_only_eating_does():
    ex = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_exchange.json")))
    for name in ("be_exchange", "be_credit"):
        r = next(x for x in ex["rules"] if x["name"] == name)
        assert "hunger_level" not in json.dumps(r["effects"]), f"{name} (a purchase) must not touch hunger"
    body = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body.json")))
    feeds = next(x for x in body["rules"] if x["name"] == "bd_meal_feeds")
    assert ["agent", "ate", "meal"] in feeds["match"], "hunger relief keys on EATING a meal"
    assert "hunger_level" in json.dumps(feeds["effects"]) and "feeds" in json.dumps(feeds["where"]), \
        "and drops hunger by the meal's `feeds`"


# ------------------------------------------------------ G-exertion-then-eat closes the loop (headline)
def test_hard_work_makes_you_hungry_and_only_eating_brings_it_back():
    w = BigvilleNeedWorld(); w.add_mover("H", (14, 8)); w.set_physique("H", sta_base=2.0)
    for _ in range(4):
        w.perform_task("H", stamina=True, stamina_cost=0.5)   # a hard day's labour
    worked = w.hunger("H")
    assert worked > 1.5, "the exertion has made him hungry"
    w.eat_meal("H", 2.0, liking=0.7)                          # he eats a meal
    assert w.hunger("H") < worked, "and eating brings the hunger back down (only eating feeds him)"
