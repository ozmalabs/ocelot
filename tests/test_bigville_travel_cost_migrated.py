"""bigville: TRAVEL COSTS THE BODY -- walking is exertion, so an errand tires you and makes you hungry.

The agents run on the map, and getting somewhere takes walking. Walking is exertion: each step draws down
the body's stamina reserve (bd_exert_cost) and raises hunger. A long errand EXHAUSTS you -- at empty
stamina you can barely move -- and it makes you hungry, so after the trip you rest and eat. You cannot rest
WHILE walking; you rest once you have arrived. The map and the body are one loop.
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


def _reserve(w, name):
    b = list(w.eng.neighbours(w._movers[name], "has_body"))[0]
    return round(float(w.eng.node(b)["attrs"].get("stamina_reserve", 1.0)), 4)


def _far_pair():
    """An agent a LONG but REACHABLE walk from the baker (a trip within its stamina capacity, so it goes --
    a longer trip it would decline; see test_bigville_journey_estimate). It provisions, so it heads out."""
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    start = (14, 8)
    # a walkable cell ~9 away: est ~0.9 stamina, just within capacity 1.0 -- a tiring but makeable errand
    reachable = [c for c in w._cell_at if 8 <= abs(c[0] - start[0]) + abs(c[1] - start[1]) <= 9]
    baker_cell = sorted(reachable)[0] if reachable else (6, 8)
    w.make_trader("baker", baker_cell, coin=0); w.stock_person("baker", BREAD, 9, sell_price=1)
    w.make_trader("me", start, coin=20, hunger_level=0, satiety=5)
    w.expect_source("me", BREAD, "baker"); w.set_plan("me", horizon=5)
    w.set_alive("me", True)
    return w


# ------------------------------------------------------ G-walking-tires (headline)
def test_a_long_errand_exhausts_the_body():
    w = _far_pair()
    r0 = _reserve(w, "me")
    lo = r0
    for _ in range(6):
        w.run_ticks(1)
        lo = min(lo, _reserve(w, "me"))
    assert r0 == 1.0, "the body starts rested"
    assert lo <= 0.2, "a long walk draws the stamina reserve right down -- travel is tiring"


# ------------------------------------------------------ G-walking-makes-you-hungry (headline)
def test_walking_makes_you_hungrier():
    w = _far_pair()
    h0 = w.hunger_of("me")
    for _ in range(5):
        w.run_ticks(1)
    assert w.hunger_of("me") > h0 + 0.5, "the steps out to the baker have made it hungry (exertion -> hunger)"


# ------------------------------------------------------ G-rest-after-arriving (headline)
def test_you_cannot_rest_while_walking_only_after_you_arrive():
    # rest is suppressed while EN ROUTE, so the reserve keeps falling during the walk...
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", (10, 8), coin=0); w.stock_person("baker", BREAD, 9, sell_price=1)
    w.make_trader("me", (14, 8), coin=20, hunger_level=0, satiety=5)
    w.expect_source("me", BREAD, "baker"); w.set_plan("me", horizon=1)
    w.set_alive("me", True)
    w.run_ticks(1)                                  # walking -> tired
    tired = _reserve(w, "me")
    assert tired < 1.0, "the walk drew the reserve down (could not rest en route)"
    for _ in range(6):
        w.run_ticks(1)                              # arrived + provisioned -> now it can rest
    assert _reserve(w, "me") > tired, "having arrived, the tired body rests and the reserve recovers"


# ------------------------------------------------------ G-travel-is-exertion (source audit)
def test_travel_is_exertion_through_the_body():
    src = open(os.path.join(_ROOT, "worlds", "bigville_need_world.py")).read()
    trav = src.split("def _step_travellers", 1)[1].split("\n    def ", 1)[0]
    assert 'add_node("Effort"' in trav and "stamina_cost" in trav, \
        "each tick of walking mints an Effort with a stamina cost -- walking IS exertion"
    assert "exerted" in trav, "hung on the agent so bd_exert_cost draws down the reserve + raises hunger"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body_choice.json")))
    rest = next(r for r in seed["rules"] if r["name"] == "bc_score_rest")
    assert "going_to" in json.dumps(rest["effects"]), "you cannot rest while EN ROUTE -- rest is zero while going_to"
