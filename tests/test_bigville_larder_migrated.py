"""bigville: the HUMAN CONDITION of food -- perpetual, automatic, and bounded by your LARDER and WEALTH.

You have to work out what to eat every single day of your life; it never resolves, only renews. How well
you get ahead of it varies:

  * PLANNING HORIZON -- a distributed trait (some plan a week out, some day-to-day).
  * LARDER -- how much food you can STORE, which you must afford. Provisioning is bounded by
    min(what you project you'll need, what you can store). A tiny larder = hand-to-mouth = exposed the
    day supply fails; a big larder (which wealth buys) = a buffer you ride lean spells out on.

The agents do this AUTOMATICALLY (run_days): each day they get hungry and feed + provision themselves --
no world call to eat or buy. The larder + wealth + horizon decide who stays fed through a supply gap.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.bigville_entities as E                          # noqa: E402
from worlds.bigville_econ_world import BigvilleEconWorld, BREAD   # noqa: E402
from worlds.bigville_time_world import DAY                     # noqa: E402

BAKER_SPOT = (13, 8)


def _town():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", BAKER_SPOT, coin=0); w.stock_person("baker", BREAD, 0, sell_price=1)
    w.make_trader("rich", (14, 8), coin=100, hunger_level=0, satiety=5)
    w.set_larder("rich", 8); w.set_plan("rich", horizon=4); w.expect_source("rich", BREAD, "baker")
    w.make_trader("poor", (15, 8), coin=20, hunger_level=0, satiety=5)
    w.set_larder("poor", 1); w.set_plan("poor", horizon=1); w.expect_source("poor", BREAD, "baker")
    return w


def _restock(w, q):
    w.eng.set_attr(w._invent[("baker", float(BREAD))], "qty", float(q))


# ------------------------------------------------------ G-larder-caps-provisioning (headline)
def test_the_larder_bounds_how_much_you_provision():
    w = _town()
    _restock(w, 99)
    for _ in range(6):
        w.run_days(["rich", "poor"], days=1)
    assert w.inventory_of("poor", BREAD) <= 2.0, "a tiny larder -> the poor hold only ~a day (+ a meal in hand) -> hand-to-mouth"
    assert w.inventory_of("rich", BREAD) >= w.inventory_of("poor", BREAD) + 3, "a bigger larder -> the rich buffer far more"
    # the cap is min(projection, larder) in the decision rule
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body_choice.json")))
    r = json.dumps(next(x for x in seed["rules"] if x["name"] == "bc_score_acquire")["effects"])
    assert '"Min"' in r and "larder_capacity" in r, "provisioning is bounded by min(projection, larder_capacity)"


# ------------------------------------------------------ G-horizon-is-a-drawn-trait (data)
def test_the_planning_horizon_is_a_distributed_trait():
    rng = np.random.default_rng(20260801)
    pop = [E.draw_plan_horizon(rng) for _ in range(3000)]
    assert min(pop) >= E.PLAN_HORIZON["min"], "everyone at least sorts out today (floored)"
    assert np.std(pop) > 0.5, "real spread -- some plan a week ahead, some live day-to-day"
    assert abs(float(np.mean(pop)) - E.PLAN_HORIZON["mean"]) < 0.3, "reproduces the population mean horizon"


def test_the_larder_scales_with_wealth():
    assert E.larder_for_wealth(2) < E.larder_for_wealth(30), "a richer purse affords a bigger larder"
    assert E.larder_for_wealth(0) >= 1.0, "everyone can keep at least a little (floored)"
    assert E.larder_for_wealth(1e6) <= 20.0, "but storage is capped -- you can't hoard the whole town"


# ------------------------------------------------------ G-eating-is-perpetual-and-automatic (headline)
def test_agents_feed_themselves_automatically_every_day():
    w = _town(); _restock(w, 99)
    log = w.run_days(["rich", "poor"], days=5)      # they LIVE on their own -- no eat()/buy() calls
    assert all(h < 2 for h in log["rich"]) and all(h < 2 for h in log["poor"]), \
        "with supply, every agent works out its food each day and stays fed -- automatically, perpetually"
    src = open(os.path.join(_ROOT, "worlds", "bigville_need_world.py")).read()
    body = src.split("def run_days", 1)[1].split("\n    def ", 1)[0]
    assert "run_ticks" in body, "the loop TICKS the world -- the alive agents live, no turns"
    for call in ("self.eat(", "self.buy(", "self.perform_task("):
        assert call not in body, f"run_days must not call {call} -- the agents decide"


# ------------------------------------------------------ G-larder-and-wealth-decide-resilience (headline)
def test_the_rich_ride_out_a_lean_spell_the_poor_go_hungry():
    w = _town()
    rich_days, poor_days = [], []
    for day in range(7):
        _restock(w, 0 if day in (3, 4) else 99)     # a TWO-day supply gap the town must weather
        d = w.run_days(["rich", "poor"], days=1)
        rich_days.append(d["rich"][0]); poor_days.append(d["poor"][0])
    assert all(h < 2 for h in rich_days), "the rich agent's larder buffers it right through the gap -- stays fed"
    assert max(poor_days) >= 2, "the poor agent, hand-to-mouth, GOES HUNGRY once its one-day buffer runs out"
    assert poor_days[4] >= 2 and poor_days[6] < 2, "clearly hungry on the second lean day; fed again when supply returns"


# ------------------------------------------------------ G-poverty-cant-afford (control)
def test_a_buyer_too_poor_to_pay_proposes_but_cannot_afford():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", (12, 8), coin=0); w.stock_person("baker", BREAD, 5, sell_price=5)
    w.make_trader("pauper", (12, 8), coin=2, hunger_level=0, satiety=5)   # WITH the baker; 2 coin, bread costs 5
    w.set_plan("pauper", horizon=2); w.expect_source("pauper", BREAD, "baker")
    w.set_alive("pauper", True); w.run_ticks(2)
    assert w.offer_status("pauper") == -3, "it reached the baker and proposed but CANNOT AFFORD the price -- poverty, not absence"
    assert w.inventory_of("pauper", BREAD) == 0, "no bread; the baker still has it (had the coin been there)"
