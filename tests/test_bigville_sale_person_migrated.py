"""bigville: A SALE IS BETWEEN TWO PEOPLE -- opening hours are a construct, not a world fact.

be_exchange no longer gates the physical sale on `shop.open` (which is derived from BUSINESS HOURS).
A sale needs the buyer and the SELLER (keeper) co-located, the seller CONSCIOUS (not asleep/collapsed
-- a world fact), goods, and coin. Business hours remain a held EXPECTATION (be_shop_open + the
expectation rule: the town holds 'the stall opens at 8', a violation is surprise) -- a human frame,
NOT a hard gate on whether two present, willing people can trade.
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

BAKER = (2, 2)


def _stall(*, collapsed=0):
    w = BigvilleEconWorld(day_range=16)
    w.make_trader("keeper", BAKER, collapsed=float(collapsed))
    sh = w.add_shop("bakery", good=BREAD, price=4, cell=BAKER, keeper="keeper",
                    activity=BAKING, input_good=GRAIN, stock=3, input_qty=0)
    w.eng.set_attr(sh, "open_scheduled", 0.0)          # OUTSIDE business hours -- the stall is "closed"
    w.refresh_open()
    w.make_trader("cust", BAKER, coin=10); w.give_good("cust", BREAD)   # a co-located buyer with coin
    return w


# ------------------------------------------------------ G-a-person-sells (headline)
def test_a_conscious_seller_trades_even_when_the_stall_is_closed_by_the_clock():
    w = _stall()
    assert w.shop_open("bakery") == 0, "by the business-hours clock the stall is 'closed'"
    w.buy("cust")
    assert w.stock_of("bakery") == 2 and w.coin_of("cust") == 6, \
        "but two present, conscious people trade anyway -- the sale is person-to-person, not stall-by-the-clock"


# ------------------------------------------------------ G-unconscious-cannot-sell (world fact)
def test_an_unconscious_seller_cannot_sell():
    w = _stall(collapsed=1)                            # the keeper collapsed -- unconscious
    w.buy("cust")
    assert w.stock_of("bakery") == 3 and w.coin_of("cust") == 10, \
        "an unconscious seller makes no sale -- THAT is the world fact (a person, present and awake)"


# ------------------------------------------------------ G-hours-are-a-frame-not-a-sale-gate (source audit)
def test_business_hours_are_a_construct_not_a_gate_on_the_sale():
    ex = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_exchange.json")))
    be = next(r for r in ex["rules"] if r["name"] == "be_exchange")
    where = json.dumps(be["where"])
    assert '"key": "open"' not in where, "be_exchange must NOT gate the sale on the shop's open/hours flag"
    assert '"key": "collapsed"' in where, "it DOES require the seller conscious (a world fact)"
    # the hours/open construct still lives -- as the shop-open derivation + the expectation frame
    prod = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_production.json")))
    assert any(r["name"] == "be_shop_open" for r in prod["rules"]), "the 'open' construct still exists (a frame)"
    exp = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_expectation.json")))
    assert "Surprise" in json.dumps(exp["rules"]), "and hours remain a held EXPECTATION (violation = surprise), not a sale gate"
