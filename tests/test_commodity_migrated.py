"""bigville R63 (block 377000): a good is tradeable PURELY BECAUSE IT EXISTS. One generic rule
(tr_trade) trades any Good node -- charcoal for the same reason timber, grain, or a tool would.
Gates mirror the generic trade.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_commodity_world import BigvilleCommodityWorld as Trade   # noqa: E402


# ------------------------------------------------------ G-charcoal-trades-because-it-exists (headline)
def test_charcoal_is_tradeable_because_it_is_a_good():
    w = Trade(); w.add_agent("Smith", coin=0.0); w.add_agent("Buyer", coin=10.0)
    w.give_good("Smith", "charcoal", qty=5.0, price=3.0); w.wants("Buyer", "charcoal")
    w.trade()
    assert w.holds_kind("Buyer", "charcoal") and not w.holds_kind("Smith", "charcoal"), "the charcoal changed hands"
    assert w.coin("Buyer") == 7.0 and w.coin("Smith") == 3.0, "coin moved buyer->seller at the price"


# ------------------------------------------------------ G-the-same-rule-trades-any-good (headline)
def test_the_same_rule_trades_any_good_no_special_case():
    w = Trade(); w.add_agent("Woodman", coin=0.0); w.add_agent("Joiner", coin=10.0)
    w.give_good("Woodman", "timber", qty=4.0, price=2.0); w.wants("Joiner", "timber")
    w.trade()
    assert w.holds_kind("Joiner", "timber") and w.coin("Joiner") == 8.0, \
        "timber trades through the SAME rule as charcoal -- charcoal was never special-cased"


# ------------------------------------------------------ G-coin-conserved
def test_trade_conserves_coin():
    w = Trade(); w.add_agent("S", coin=0.0); w.add_agent("B", coin=10.0)
    before = w.total_coin()
    w.give_good("S", "charcoal", qty=1.0, price=3.0); w.wants("B", "charcoal")
    w.trade()
    assert w.total_coin() == before, "trade only MOVES coin -- the total is conserved"


# ------------------------------------------------------ G-cannot-afford
def test_a_buyer_who_cannot_afford_it_does_not_get_it():
    w = Trade(); w.add_agent("S", coin=0.0); w.add_agent("B", coin=2.0)
    w.give_good("S", "charcoal", qty=1.0, price=3.0); w.wants("B", "charcoal")
    w.trade()
    assert not w.holds_kind("B", "charcoal") and w.coin("B") == 2.0, "no coin, no charcoal -- nothing moves"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_trade():
    src = open(os.path.join(_ROOT, "worlds", "bigville_commodity_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_commodity.json")))
    rule = [r for r in seed["rules"] if r["name"] == "tr_trade"][0]
    logic = json.dumps({k: rule[k] for k in ("match", "where", "effects")})   # exclude the comment
    assert "charcoal" not in logic, "the trade LOGIC must NOT name charcoal -- it trades ANY good"
    assert "holds" in logic and "coin" in logic, "it matches a held good and moves coin"
