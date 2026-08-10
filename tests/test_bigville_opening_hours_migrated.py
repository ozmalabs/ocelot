"""bigville: OPENING HOURS ARE A CONSTRUCT -- a sale is done by a present, conscious, WILLING person.

Opening hours are not an engine gate; they are a seller's own ROUTINE/decision. The world-facts the trade
enforces are only these: to sell, the seller must be a PERSON who is there (co-located), awake (not asleep/
collapsed), and WILLING. A baker "keeps hours" by choosing to be there and willing to trade; "shut up shop"
is the baker deciding not to trade right now. So a buyer who walks to a baker that has closed up is turned
away -- because the person isn't trading, not because a flag says "closed".
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


def _shopper(baker_keeping_shop=True):
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", (12, 8), coin=0)
    # "keeping shop" = present + willing to trade; "shut up shop" = the baker's own decision not to trade now
    w.stock_person("baker", BREAD, 9, sell_price=1, willing=baker_keeping_shop)
    w.make_trader("me", (14, 8), coin=20, hunger_level=8, satiety=5)
    w.expect_source("me", BREAD, "baker"); w.set_plan("me", horizon=0)
    w.set_alive("me", True); w.run_ticks(4)
    return w


# ------------------------------------------------------ G-keeping-shop-sells (headline)
def test_a_baker_keeping_shop_sells():
    w = _shopper(baker_keeping_shop=True)
    assert w.pos["me"] == (12, 8), "the buyer walked to the baker"
    assert w.offer_status("me") == 1 and w.hunger_of("me") < 8, "the baker was there and trading -- it sold, the buyer ate"


# ------------------------------------------------------ G-closed-up-makes-no-sale (headline)
def test_a_baker_who_has_closed_up_makes_no_sale():
    w = _shopper(baker_keeping_shop=False)
    assert w.pos["me"] == (12, 8), "the buyer still walked all the way to the baker"
    assert w.offer_status("me") == -2 and w.inventory_of("me", BREAD) == 0, \
        "but the baker had CLOSED UP (its own choice not to trade) -- turned away, no sale"
    assert w.hunger_of("me") >= 8, "and it went for nothing -- opening hours are the seller's routine, not an engine gate"


# ------------------------------------------------------ G-the-gate-is-the-person (source audit)
def test_the_trade_gates_on_the_person_not_an_open_flag():
    trade = json.load(open(os.path.join(_ROOT, "seeds", "bigville_trade.json")))
    names = {r["name"] for r in trade["rules"]}
    assert "tr_shut" not in names, "there is no 'shut' gate -- opening hours are not an engine construct"
    for r in trade["rules"]:
        assert '"open"' not in json.dumps(r.get("where", {})), "no rule reads an `open` flag -- opening hours are not an engine thing"
    acc = next(r for r in trade["rules"] if r["name"] == "tr_accept")
    aj = json.dumps(acc["where"])
    assert "asleep" in aj and "collapsed" in aj and "sell_willing" in aj, \
        "a sale requires a PRESENT, CONSCIOUS, WILLING person -- the world-fact the trade enforces"
