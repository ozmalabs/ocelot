"""bigville: THE GOODS PORT -- the living economy's goods ARE catalog kinds.

The living economy used opaque integer good codes (GRAIN=10, BREAD=11, ...). Now the codes are
catalog-driven: the classic goods keep their codes, but ANY catalog item gets a stable code by NAME
(good_code), and each Good node carries its catalog `kind` + `weight` (self-describing). So a good new
to the living economy -- cheese, milk, anything in bigville_entities -- is added by name with no new
constant, produced by the existing be_produce, and traded by the existing be_exchange.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import (                                    # noqa: E402
    BigvilleEconWorld, good_code, good_kind, GRAIN, BREAD, FISH, BAKING)
from worlds.bigville_time_world import DAY                                  # noqa: E402
import domains.bigville_entities as E                                       # noqa: E402

DAIRY = 6.0


# ------------------------------------------------------ G-codes-are-catalog-driven (headline)
def test_good_codes_are_catalog_driven_classic_preserved_new_by_name():
    assert good_code("grain") == GRAIN and good_code("bread") == BREAD and good_code("fish") == FISH, \
        "the classic goods keep their codes (back-compat)"
    # a good new to the living economy gets a STABLE code, derived from the catalog, and round-trips
    c = good_code("cheese")
    assert c >= 1000.0 and good_kind(c) == "cheese", "cheese: a catalog code by name, reversible"
    assert good_code("cheese") == c and good_code("milk") != c, "stable, and distinct per kind"
    # bait is the one living good with no catalog entry -- it still has its code
    assert good_kind(13.0) == "bait"


# ------------------------------------------------------ G-goods-are-self-describing (headline)
def test_goods_carry_their_catalog_kind_and_weight():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("dairymaid", (2, 2)); w.set_skill("dairymaid", DAIRY, 2)
    w.add_catalog_shop("dairy", "cheese", cell=(2, 2), keeper="dairymaid", price=3,
                       activity=DAIRY, input_kind="milk", stock=0, input_qty=3)
    assert w.stock_kind("dairy") == "cheese", "the Good node knows it is cheese"
    assert w.stock_weight("dairy") == E.ITEMS["cheese"]["weight"], "and carries cheese's catalog weight"


# ------------------------------------------------------ G-a-new-good-produces-and-trades (headline)
def test_a_catalog_good_new_to_the_economy_is_made_and_bought_by_name():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("dairymaid", (2, 2)); w.set_skill("dairymaid", DAIRY, 2)
    w.add_catalog_shop("dairy", "cheese", cell=(2, 2), keeper="dairymaid", price=3,
                       activity=DAIRY, input_kind="milk", stock=0, input_qty=3)
    w.refresh_open()
    w.produce("dairy")                                          # milk -> cheese via the EXISTING be_produce
    assert w.stock_qty("dairy") == 2.0, "the dairymaid makes cheese (yield = her skill), no new rule"
    # a co-located buyer buys the cheese via the EXISTING be_exchange (code compare)
    w.make_trader("cust", (2, 2), coin=10, hunger_level=8, satiety=5)
    copy = w.give_good("cust", good_code("cheese"))
    w.buy("cust")
    assert float(w.eng.node(copy)["attrs"]["qty"]) >= 1.0, "the buyer now holds cheese -- a new good trades unchanged"
    assert w.stock_qty("dairy") < 2.0, "and the dairy's stock went down"


# ------------------------------------------------------ G-classic-economy-unchanged (no regression)
def test_the_classic_bread_economy_is_unchanged():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("baker", (2, 2)); w.set_skill("baker", BAKING, 3)
    w.add_shop("bakery", good=BREAD, price=4, cell=(2, 2), keeper="baker",
               activity=BAKING, input_good=GRAIN, stock=0, input_qty=2)
    w.refresh_open(); w.produce("bakery")
    assert w.stock_qty("bakery") == 3.0 and w.stock_kind("bakery") == "bread", \
        "the classic bakery still bakes 3 bread -- now with its kind carried (additive)"


# ------------------------------------------------------ G-the-seam (source audit)
def test_the_codes_derive_from_the_catalog():
    src = open(os.path.join(_ROOT, "worlds", "bigville_econ_world.py")).read()
    assert "list(E.ITEMS).index" in src, "good_code derives new codes from the catalog order"
    assert good_code("nutmeg") == 1000.0 + float(list(E.ITEMS).index("nutmeg")), \
        "any catalog kind resolves to its catalog-indexed code"
