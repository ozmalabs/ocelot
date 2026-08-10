"""bigville: an agent ESTIMATES a journey before setting out -- rests if it's short, declines if it's too far.

The agents run on the map and walking costs stamina, so before heading for a source an agent estimates the
trip: the distance to where it expects the good, and the stamina that would cost. If it hasn't the stamina
right now, it RESTS first, then goes. If the trip is beyond its full capacity -- too far for it at all -- it
DECLINES to go itself and asks someone who can. Look before you leap.
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


# ------------------------------------------------------ G-estimate-the-journey (data)
def test_the_agent_estimates_distance_and_whether_it_can_make_the_trip():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", (10, 8), coin=0); w.stock_person("baker", BREAD, 9, sell_price=1)
    w.make_trader("me", (14, 8), coin=20, hunger_level=8, satiety=5)
    w.expect_source("me", BREAD, "baker"); w.set_plan("me", horizon=0)
    w.set_alive("me", True); w.run_ticks(1)
    a = w.eng.node(w._movers["me"])["attrs"]
    assert abs(float(a["src_est"]) - 0.4) < 1e-6, "it estimated the trip's stamina cost (dist 4 * 0.1/hop)"
    assert float(a["src_reach"]) == 1.0, "a 4-cell trip is within its capacity -- reachable"


# ------------------------------------------------------ G-rest-before-going (headline)
def test_a_tired_agent_rests_before_setting_out_then_completes_the_trip():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", (10, 8), coin=0); w.stock_person("baker", BREAD, 9, sell_price=1)
    w.make_trader("me", (14, 8), coin=20, hunger_level=8, satiety=5)
    w.expect_source("me", BREAD, "baker"); w.set_plan("me", horizon=0)
    b = list(w.eng.neighbours(w._movers["me"], "has_body"))[0]
    w.eng.set_attr(b, "stamina_reserve", 0.2)                # too tired to make the 0.4 trip right now
    w.set_alive("me", True)
    w.run_ticks(4)
    assert w.hunger_of("me") < 8, "it rested to recover enough, then made the trip and ate -- it did not set out spent"


# ------------------------------------------------------ G-decline-too-far (headline)
def test_it_declines_a_trip_beyond_its_reach_and_asks_someone():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    cells = sorted(w._cell_at.keys())
    far = max(cells, key=lambda c: abs(c[0] - 14) + abs(c[1] - 8))   # a baker across the whole map
    w.make_trader("baker", far, coin=0); w.stock_person("baker", BREAD, 9, sell_price=1)
    w.make_trader("me", (14, 8), coin=20, hunger_level=8, satiety=5)
    w.set_provision_good("me", BREAD); w.expect_source("me", BREAD, "baker"); w.set_plan("me", horizon=0)
    w.make_trader("helper", (15, 8), coin=20, hunger_level=0, satiety=5); w.expect_source("helper", BREAD, "baker")
    w.set_relationship("me", "helper", kind="spouse", strength=3.0, min_ask=1.0, mutual=True)
    w.set_alive("me", True)
    w.run_ticks(1)
    a = w.eng.node(w._movers["me"])["attrs"]
    dist = abs(far[0] - 14) + abs(far[1] - 8)
    assert dist * 0.1 > 1.0 and float(a["src_reach"]) == 0.0, "the trip is beyond its full stamina -- unreachable"
    assert w.pos["me"] == (14, 8), "so it did NOT set out itself on a trip it cannot make"
    assert w.delegated_to("me") == "helper", "it declined to go and ASKED someone instead"


# ------------------------------------------------------ G-delegate-also-estimates (headline)
def test_a_delegate_also_declines_a_trip_it_cannot_make():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    cells = sorted(w._cell_at.keys())
    far = max(cells, key=lambda c: abs(c[0] - 14) + abs(c[1] - 8))   # too far for anyone here
    w.make_trader("baker", far, coin=0); w.stock_person("baker", BREAD, 9, sell_price=1)
    w.make_trader("me", (14, 8), coin=20, hunger_level=8, satiety=5)
    w.set_provision_good("me", BREAD); w.expect_source("me", BREAD, "baker"); w.set_plan("me", horizon=0)
    w.make_trader("helper", (15, 8), coin=20, hunger_level=0, satiety=5); w.expect_source("helper", BREAD, "baker")
    w.set_relationship("me", "helper", kind="spouse", strength=3.0, min_ask=1.0, mutual=True)
    w.set_alive("me", True); w.set_alive("helper", True)
    w.run_ticks(1)
    assert w.delegated_to("me") == "helper", "I couldn't make it, so I asked my spouse"
    assert w.delegation_status("me") == -1 and not w.took_on_task("helper"), \
        "but the spouse ESTIMATED the trip too and DECLINED -- it can't make it either. The asked party looks before it leaps."


# ------------------------------------------------------ G-estimate-is-a-rule (source audit)
def test_the_estimate_and_the_gates_are_rules():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_pursuit.json")))
    est = next(r for r in seed["rules"] if r["name"] == "pu_estimate")
    ej = json.dumps(est)
    assert '"cx"' in ej and '"cy"' in ej, "the estimate is the distance over the agent's and source's positions"
    assert "src_est" in ej and "src_reach" in ej and "stamina" in ej, "cost of the trip + can my capacity make it"
    sf = next(r for r in seed["rules"] if r["name"] == "pu_do_self_fetch")
    assert "src_est" in json.dumps(sf["where"]) and "stamina_reserve" in json.dumps(sf["where"]), \
        "going myself is gated on having the stamina for the trip now (else rest first)"
