"""bigville: ONE reasoning, on TICKS -- doing it myself and asking someone are ROUTES in the same decision.

There are no separate faculties and no turns. While an agent is ALIVE, on every tick it perceives its state
and reasons over what to do -- and meeting an acquisition need is ONE decision over routes: go get it MYSELF
or ASK SOMEONE, whichever is cheaper (the offer I'd owe them vs the effort of the trip). A free relation gets
asked (saves the trip); an expensive ask I do myself; if I can't do it myself I ask. Delegation is not a
separate thing -- it is a route in the agent's normal reasoning.
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


def _town(*, i_know_a_source=True, helper=None, helper_free=True):
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", (12, 8), coin=0); w.stock_person("baker", BREAD, 99, sell_price=1)
    w.make_trader("me", (14, 8), coin=20, hunger_level=0, satiety=5); w.give_good("me", BREAD, 0)
    if i_know_a_source:
        w.expect_source("me", BREAD, "baker")
    else:
        w.set_provision_good("me", BREAD)   # knows WHAT it eats + a slot to receive it, but no source of its own
    if helper:
        w.make_trader(helper, (15, 8), coin=20, hunger_level=0, satiety=5)
        w.expect_source(helper, BREAD, "baker"); w.set_plan(helper, horizon=0)   # helper doesn't provision itself here
        if helper_free:
            w.set_relationship("me", helper, kind="spouse", strength=3.0, min_ask=1.0, mutual=True)
        else:
            w.set_relationship("me", helper, kind="stranger", strength=0.0, expected_ask=3.0, min_ask=3.0, mutual=True)
        w.set_alive(helper, True)
    w.set_alive("me", True)
    return w


# ------------------------------------------------------ G-ask-a-free-relation (headline)
def test_it_asks_a_free_relation_to_save_the_trip():
    w = _town(i_know_a_source=True, helper="spouse", helper_free=True)   # I COULD go myself
    w.run_ticks(8)
    assert w.delegated_to("me") == "spouse", "with a free spouse to hand, I ask them rather than make the trip"
    assert w.inventory_of("me", BREAD) > 0, "and the food is provisioned (they fetched it for me)"


# ------------------------------------------------------ G-do-an-expensive-ask-myself (headline)
def test_an_expensive_ask_i_do_myself():
    w = _town(i_know_a_source=True, helper="stranger", helper_free=False)   # only a costly stranger
    w.run_ticks(8)
    assert w.delegated_to("me") is None, "asking the stranger costs more than the trip, so I go myself"
    assert w.inventory_of("me", BREAD) > 0, "and provision it directly"


# ------------------------------------------------------ G-ask-when-i-cannot (headline)
def test_when_i_cannot_do_it_myself_i_ask():
    w = _town(i_know_a_source=False, helper="spouse", helper_free=True)   # I know no source
    w.run_ticks(8)
    assert w.delegated_to("me") == "spouse", "not knowing where to get it, I ask someone who does"
    assert w.inventory_of("me", BREAD) > 0, "and it still gets provisioned"


# ------------------------------------------------------ G-no-route-no-action (control)
def test_with_no_route_at_all_nothing_happens():
    w = _town(i_know_a_source=False, helper=None)   # no source of my own, no one to ask
    w.run_ticks(8)
    assert w.delegated_to("me") is None and w.inventory_of("me", BREAD) == 0, \
        "no way to get it -> the agent provisions nothing (it cannot, and asks no one)"


# ------------------------------------------------------ G-means-ends: hunger drives getting food (headline)
def test_hunger_drives_getting_food_even_with_no_larder_plan():
    # a hungry agent that does NOT provision for later (horizon 0) still gets food -- to EAT now
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", (12, 8), coin=0); w.stock_person("baker", BREAD, 99, sell_price=1)
    w.make_trader("me", (14, 8), coin=20, hunger_level=8, satiety=5); w.expect_source("me", BREAD, "baker")
    w.set_plan("me", horizon=0)
    w.set_alive("me", True); w.run_ticks(8)
    assert w.hunger_of("me") < 8, "hungry with nothing to eat -> it GETS food and eats it (means-ends), no larder plan needed"


def test_hunger_drives_asking_someone_when_it_cannot_go_itself():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", (12, 8), coin=0); w.stock_person("baker", BREAD, 99, sell_price=1)
    w.make_trader("me", (14, 8), coin=20, hunger_level=8, satiety=5)
    w.set_provision_good("me", BREAD)                          # knows WHAT it eats, but no source of its own
    w.set_plan("me", horizon=0)
    w.make_trader("spouse", (15, 8), coin=20, hunger_level=0, satiety=5); w.expect_source("spouse", BREAD, "baker")
    w.set_relationship("me", "spouse", kind="spouse", strength=3.0, min_ask=1.0, mutual=True)
    w.set_alive("me", True); w.set_alive("spouse", True)
    w.run_ticks(8)
    assert w.hunger_of("me") < 8, "hungry + can't go itself -> it ASKS someone to fetch food, then eats -- one need, either route"


# ------------------------------------------------------ G-one-decision-over-routes (source audit)
def test_acquisition_is_one_pursuit_over_routes_not_separate_faculties():
    # the food NEED mints a goal (bc_want_food); ONE pursuit routes ANY goal -- self vs ask -- for food AND notes
    body = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body_choice.json")))
    assert any(r["name"] == "bc_want_food" for r in body["rules"]), "acquiring food MINTS a goal (a task) like any other"
    assert not any(r["name"] in ("bc_route", "bc_do_delegate", "ur_cost_tie") for r in body["rules"]), \
        "the food-specific route/delegate rules are GONE -- folded into the one pursuit"
    pursuit = json.load(open(os.path.join(_ROOT, "seeds", "bigville_pursuit.json")))
    names = {r["name"] for r in pursuit["rules"]}
    assert {"pu_route", "pu_do_self_fetch", "pu_do_self_generic", "pu_do_ask"} <= names, \
        "ONE pursuit: route (self vs ask), do-it-myself (fetch or generic), or ask -- for every goal"
    route = json.dumps(next(r for r in pursuit["rules"] if r["name"] == "pu_route")["effects"])
    assert "self_cost" in route and "ask_cost" in route, "the route weighs doing it myself vs the cheapest capable person"
    deleg = json.load(open(os.path.join(_ROOT, "seeds", "bigville_delegation.json")))
    dnames = {r["name"] for r in deleg["rules"]}
    assert dnames == {"dl_accept", "dl_decline"}, "delegation is now ONLY the asked person's reply -- whom-to-ask is the pursuit"


# ------------------------------------------------------ G-ticks-not-turns (source audit)
def test_the_agent_acts_on_ticks_while_alive_not_on_turns():
    src = open(os.path.join(_ROOT, "worlds", "bigville_need_world.py")).read()
    assert "def run_ticks" in src and "deliberating" not in src, "the driver is run_ticks; there is no turn flag"
    assert "def set_alive" in src, "aliveness is a persistent property, not a per-call turn"
    for seed_name in ("bigville_body_choice", "bigville_pursuit"):
        seed = json.load(open(os.path.join(_ROOT, "seeds", seed_name + ".json")))
        assert '"alive"' in json.dumps(seed), f"{seed_name} rules fire while the agent is alive, every tick"
