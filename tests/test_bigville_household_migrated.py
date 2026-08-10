"""bigville: HOUSEHOLD LABOUR DIVISION -- one shared need, one fetcher, one store; nobody duplicates.

A household is a group living together with ONE shared food need and ONE shared store. When the store runs
low the HOUSEHOLD wants food (not each member separately); ONE member -- the most rested -- volunteers to
fetch it, carries it home to the shared store, and everyone eats from it. So household-mates don't all set
out for food at once (the old spouses-both-fetch collision), and one trip feeds the whole house.
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

HOME = (14, 8)
BAKER = (12, 8)


def _household():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", BAKER, coin=0); w.stock_person("baker", BREAD, 20, sell_price=1)
    for nm in ("A", "B"):
        w.make_trader(nm, HOME, coin=20, hunger_level=6, satiety=5); w.expect_source(nm, BREAD, "baker")
    w.form_household(["A", "B"], HOME, horizon=2, ration=1, good=BREAD)
    w.set_alive("A", True); w.set_alive("B", True)
    return w


# ------------------------------------------------------ G-one-fetcher-at-a-time (headline)
def test_household_mates_do_not_all_set_out_at_once():
    w = _household()
    max_away = 0
    for _ in range(10):
        w.run_ticks(1)
        away = sum(1 for nm in ("A", "B") if w.pos[nm] != HOME)
        max_away = max(max_away, away)
    assert max_away <= 1, "at any moment at most ONE household member is out fetching -- labour divides, no collision"


# ------------------------------------------------------ G-one-fetch-feeds-the-house (headline)
def test_one_member_fetches_and_the_whole_household_eats():
    w = _household()
    assert w.hunger_of("A") == 6 and w.hunger_of("B") == 6, "both start hungry, the larder empty"
    baker0 = w.inventory_of("baker", BREAD)
    for _ in range(10):
        w.run_ticks(1)
    assert w.inventory_of("baker", BREAD) < baker0, "trips were made to the baker"
    assert w.hunger_of("A") < 3 and w.hunger_of("B") < 3, "BOTH members got fed -- from the one shared store"
    assert w.household_store(["A", "B"]) >= 0, "the shared store is never over-drawn (one eater per tick)"


# ------------------------------------------------------ G-store-never-negative (control)
def test_the_shared_store_is_never_over_drawn():
    w = _household()
    lo = 0.0
    for _ in range(12):
        w.run_ticks(1)
        lo = min(lo, w.household_store(["A", "B"]))
    assert lo >= 0.0, "two members never both take the last unit -- the store stays >= 0"


# ------------------------------------------------------ G-fixed-provider-role (headline)
def test_a_household_can_have_a_fixed_provider_who_does_the_errands():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", BAKER, coin=0); w.stock_person("baker", BREAD, 20, sell_price=1)
    for nm in ("A", "B"):
        w.make_trader(nm, HOME, coin=20, hunger_level=6, satiety=5); w.expect_source(nm, BREAD, "baker")
    w.form_household(["A", "B"], HOME, horizon=2, ration=1, good=BREAD, provider="A")   # A is the fixed provider
    w.set_alive("A", True); w.set_alive("B", True)
    b_left_home = False
    for _ in range(10):
        w.run_ticks(1)
        if w.pos["B"] != HOME:
            b_left_home = True
    assert not b_left_home, "B never sets out -- A is the fixed provider (not alternating turns)"
    assert w.hunger_of("A") < 3 and w.hunger_of("B") < 3, "and both are still fed -- A fetches for the house"


# ------------------------------------------------------ G-division-is-rules (source audit)
def test_household_division_is_rules_not_per_member_provisioning():
    hh = json.load(open(os.path.join(_ROOT, "seeds", "bigville_household.json")))
    names = {r["name"] for r in hh["rules"]}
    assert {"hh_want_food", "hh_volunteer", "hh_eat"} <= names, \
        "one shared need (hh_want_food), one volunteer (hh_volunteer), shared eating (hh_eat)"
    vol = next(r for r in hh["rules"] if r["name"] == "hh_volunteer")
    assert '"Argmax"' in json.dumps(vol["where"]), "the volunteer is a single deterministic winner (Argmax availability), not a race"
    # a member in a household does NOT individually provision or eat -- the household does
    body = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body_choice.json")))
    for rule in ("bc_score_acquire", "bc_score_eat"):
        r = next(x for x in body["rules"] if x["name"] == rule)
        assert "in_household" in json.dumps(r["effects"]), f"{rule} is suppressed for household members"
