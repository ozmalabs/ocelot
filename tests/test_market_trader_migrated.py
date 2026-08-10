"""bigville R29 v2 (block 318000): the visiting market trader sells DIFFERENT goods
that are not locally available. He deals only in exotic wares (no local producer),
is the sole source, and the town gains import-access. A stall of a locally-made
good is refused. Gates mirror BIGVILLE_MARKET_TRADER_PREREG.md (v2). open/refuse/
grant/buy/depart are seed rules (mt_*).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_market_trader_world import BigvilleMarketTraderWorld   # noqa: E402

# the town makes these itself:
_LOCAL = ("fish", "lumber", "stone", "furniture", "blocks")


def _town():
    return BigvilleMarketTraderWorld(local_goods=_LOCAL)


# ------------------------------------------------------ G-sells-exotic (headline)
def test_trader_sells_an_exotic_good():
    w = _town()
    w.add_resident("Alice", coin=20.0, wants=1)
    w.add_resident("Bob", coin=20.0, wants=1)
    w.arrive_trader("Fizzwick", good="spice", stock=5, ask_price=6.0)   # spice is not local
    w.market_day()
    assert w.stall_open() and not w.stall_refused(), "an exotic stall should open"
    assert w.stall_stock() == 3, w.stall_stock()
    assert w.holds_of("Alice") == 1 and w.holds_of("Bob") == 1
    assert abs(w.trader_coin() - 12.0) < 1e-9


# ------------------------------------------------------ G-refuses-local (headline)
def test_trader_refuses_a_locally_made_good():
    w = _town()
    w.add_resident("Dan", coin=50.0, wants=3)          # willing and able
    w.arrive_trader("Grubb", good="fish", stock=5, ask_price=6.0)       # fish IS local
    w.market_day()
    assert w.stall_refused() and not w.stall_open(), "a locally-made good must be refused"
    assert w.stall_stock() == 5, "no sale of a locally-available good"
    assert w.holds_of("Dan") == 0 and abs(w.trader_coin() - 0.0) < 1e-9
    assert "fish" not in w.imported_goods()


# ------------------------------------------------------ G-sole-source + G-grows-available-goods
def test_the_town_gains_access_to_a_new_good():
    w = _town()
    w.add_resident("Alice", coin=20.0, wants=1)
    # before the trader: silk is neither produced nor imported, and nobody holds it.
    assert "silk" not in w.local_goods() and w.imported_goods() == []
    assert w.holds_of("Alice") == 0
    w.arrive_trader("Silas", good="silk", stock=3, ask_price=5.0)
    w.market_day()
    # the ONLY way to get silk is the visiting trader.
    assert w.imported_goods() == ["silk"], w.imported_goods()
    assert set(w.local_goods()).isdisjoint(w.imported_goods()), "imported is disjoint from produced"
    assert w.holds_of("Alice") == 1, "the town could not obtain silk any other way"


# ------------------------------------------------------ G-coin-leaves-the-town (boundary)
def test_coin_leaves_the_closed_economy():
    w = _town()
    for n in ("Alice", "Bob", "Cora"):
        w.add_resident(n, coin=20.0, wants=1)
    w.arrive_trader("Fizzwick", good="spice", stock=5, ask_price=6.0)
    before = 3 * 20.0
    w.market_day()
    after = sum(w.coin_of(n) for n in ("Alice", "Bob", "Cora"))
    leaked = before - after
    assert abs(leaked - w.external_outflux()) < 1e-9 and abs(leaked - w.trader_coin()) < 1e-9
    assert abs(leaked - 18.0) < 1e-9, "3 buyers * 6.0 left the town"


# ------------------------------------------------------ G-sells-out-and-departs
def test_exotic_trader_sells_out_and_departs():
    w = _town()
    for n in ("Alice", "Bob", "Cora"):
        w.add_resident(n, coin=20.0, wants=1)
    w.arrive_trader("Fizzwick", good="spice", stock=3, ask_price=6.0)
    w.market_day()
    assert w.stall_stock() == 0 and w.stall_stock() >= 0, "exhausted, never negative"
    assert w.trader_departed() and not w.has_stall()


# ------------------------------------------------------ G-no-coin-no-buy (falsifier)
def test_no_coin_or_no_want_means_no_purchase():
    w = _town()
    w.add_resident("Broke", coin=2.0, wants=3)
    w.add_resident("Sated", coin=50.0, wants=0)
    w.arrive_trader("Fizzwick", good="spice", stock=5, ask_price=6.0)
    w.market_day()
    assert w.stall_open(), "the exotic stall still opens"
    assert w.stall_stock() == 5 and abs(w.trader_coin() - 0.0) < 1e-9
    assert w.holds_of("Broke") == 0 and w.holds_of("Sated") == 0


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_runs_the_market():
    src = open(os.path.join(_ROOT, "worlds", "bigville_market_trader_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_market_trader.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"mt_open", "mt_refuse_local", "mt_grant_access", "mt_buy", "mt_depart"} <= names, names


# ------------------------------------------------------ G-market-opens-on-the-bell (block 321000)
def test_trade_only_happens_after_the_market_bell():
    """No buying until the MARKET BELL tolls -- the market day is opened by the bell,
    not a forced flag."""
    w = _town()
    w.add_resident("Alice", coin=20.0, wants=1)
    w.arrive_trader("Fizzwick", good="spice", stock=5, ask_price=6.0)
    # arm the buyer and run WITHOUT ringing the market bell -> no market peal -> no buy.
    w.eng.set_attr(w._residents["Alice"], "buy_armed", 1.0)
    w._run()
    assert w.stall_stock() == 5 and w.holds_of("Alice") == 0, "no trade before the market bell"
    # now hold the market day (rings the bell) -> trade proceeds.
    w.market_day()
    assert w.holds_of("Alice") == 1, "the market bell opened trading"
