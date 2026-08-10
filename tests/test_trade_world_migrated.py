"""bigville production-economy R2 (block 301000): production consumes raw material;
tradesmen transform raw -> goods; the fishmonger can't sell fish nobody caught.
Gates mirror BIGVILLE_TRADES_PREREG.md.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_trade_world import BigvilleTradeWorld         # noqa: E402


def _fish_town(supply):
    w = BigvilleTradeWorld()
    w.add_shop("fishmonger", (0, 0), input_kind="fish", output_kind="fish_ready", price=3.0)
    w.add_deposit("fish", (2, 3), stock=(40.0 if supply else 0.0),
                  growback=(2.0 if supply else 0.0), capacity=100.0)
    if supply:
        w.add_supplier("finn", (2, 3), dep_kind="fish", to_trade="fishmonger", yield_=3.0)
    w.add_customer("cara", "fishmonger", coin=100.0)
    w.add_customer("dave", "fishmonger", coin=100.0)
    w.run(T=40)
    return w


# ------------------------------------------------------ G-chain-sells
def test_full_chain_sells_when_supplied():
    """fish extracted -> delivered -> transformed -> sold. The fishmonger earns coin
    and customers receive goods."""
    w = _fish_town(supply=True)
    assert w.shop_coin("fishmonger") > 0, "supplied fishmonger earned nothing"
    assert w.bought("cara") > 0 and w.bought("dave") > 0, "customers bought nothing"
    w.close()


# ------------------------------------------------------ G-no-fish-no-sale (HEADLINE)
def test_fishmonger_cannot_sell_fish_nobody_caught():
    """Cut the fish supply -> the fishmonger's input stays 0 -> no transform -> no
    output -> NO SALE. Customers keep their coin. The supply dependency is real."""
    w = _fish_town(supply=False)
    assert w.input_stock("fishmonger") == 0.0
    assert w.output_stock("fishmonger") == 0.0, "output made from no input"
    assert w.shop_coin("fishmonger") == 0.0, "sold with no fish"
    assert w.bought("cara") == 0.0 and w.bought("dave") == 0.0
    assert w.customer_coin("cara") == 100.0, "customer charged for nothing"
    w.close()


# ------------------------------------------------------ G-transform-general
def test_transform_is_general_across_trades():
    """The carpenter (lumber->furniture) transforms and sells too -- transform is
    a general raw->good op, not fish-specific."""
    w = BigvilleTradeWorld()
    w.add_shop("carpenter", (0, 0), input_kind="lumber", output_kind="furniture", price=5.0)
    w.add_deposit("lumber", (5, 0), stock=40.0, growback=2.0, capacity=100.0)
    w.add_supplier("woody", (5, 0), dep_kind="lumber", to_trade="carpenter", yield_=3.0)
    w.add_customer("cara", "carpenter", coin=100.0)
    w.run(T=50)
    assert w.shop_coin("carpenter") > 0, "carpenter never sold furniture"
    assert w.bought("cara") > 0
    w.close()


# ------------------------------------------------------ G-coin-conserved
def test_coin_is_conserved_in_sales():
    """Coin only MOVES customer -> shop; the shop's take equals the customers' total
    spend. No coin is minted."""
    w = _fish_town(supply=True)
    spent = (100.0 - w.customer_coin("cara")) + (100.0 - w.customer_coin("dave"))
    assert abs(w.shop_coin("fishmonger") - spent) < 1e-6, (
        "coin not conserved: shop=%.1f spent=%.1f" % (w.shop_coin("fishmonger"), spent))
    # and every unit sold cost exactly `price` (bought * price == spend)
    sold = w.bought("cara") + w.bought("dave")
    assert abs(sold * 3.0 - spent) < 1e-6
    w.close()


# ------------------------------------------------------ G-no-python-decision
def test_no_python_decides_trade():
    src = open(os.path.join(_ROOT, "worlds", "bigville_trade_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_trades.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"tf_transform", "tf_sell"} <= names, names
    # sale is gated on output availability (the supply coupling).
    sell = next(r for r in seed["rules"] if r["name"] == "tf_sell")
    assert "outstk" in __import__("json").dumps(sell) and "amount" in __import__("json").dumps(sell)
