"""bigville: PERISHABLE GOODS ROT in the living economy (goods port -- physical properties).

Each Good a mover holds carries its catalog perishable/decay/condition (via _good_node). be_spoil
decays a held perishable good's freshness once per living tick at its CATALOG decay rate; be_spoil_gone
discards it when fully rotted. The rich stack's spoilage, now in the living town -- a resident's larder
goes off, while durable goods keep. The catalog's decay rates drive it; the clock is published
mechanically (like the obligation clock), the decay itself is a seed rule.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld, good_code          # noqa: E402
from worlds.bigville_time_world import DAY                                   # noqa: E402
import domains.bigville_entities as E                                        # noqa: E402


def _larder(fish=3, iron=3):
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("resident", (2, 2))
    w.give_good("resident", good_code("fish"), qty=fish)   # perishable
    w.give_good("resident", good_code("iron"), qty=iron)   # durable
    return w


# ------------------------------------------------------ G-perishables-rot (headline)
def test_a_held_perishable_good_loses_freshness_each_day():
    w = _larder()
    assert w.good_condition("resident", "fish") == 1.0, "the fish starts fresh"
    w.tick_spoilage()
    assert w.good_condition("resident", "fish") == round(1.0 - E.decay_rate("fish"), 4), \
        "one day off -> freshness down by the fish's CATALOG decay rate"


# ------------------------------------------------------ G-rotted-is-discarded (headline)
def test_a_fully_rotted_good_is_thrown_out():
    w = _larder(fish=3)
    w.tick_spoilage(6)                                    # accelerated decay -> gone within a few days
    assert w.good_held_qty("resident", "fish") == 0.0, "rotted away -> the spoiled fish is discarded (qty 0)"


# ------------------------------------------------------ G-accelerated-decay (headline)
def test_a_more_degraded_pile_rots_faster():
    w = _larder(fish=3)
    w.tick_spoilage(1); c1 = w.good_condition("resident", "fish")
    w.tick_spoilage(1); c2 = w.good_condition("resident", "fish")
    drop_fresh, drop_stale = 1.0 - c1, c1 - c2
    assert drop_stale > drop_fresh, "a more-degraded pile loses freshness FASTER -- rot spreads (accelerated decay)"


# ------------------------------------------------------ G-empty-pile-is-fresh-again (headline)
def test_an_emptied_pile_resets_to_fresh():
    w = _larder(fish=3)
    w.tick_spoilage(6)                                    # rots away
    assert w.good_held_qty("resident", "fish") == 0.0 and w.good_condition("resident", "fish") == 1.0, \
        "an emptied pile has no old stock -- it is fresh again for the next catch (no stale contamination carried)"


# ------------------------------------------------------ G-durables-keep (headline)
def test_durable_goods_do_not_rot():
    w = _larder(iron=3)
    w.tick_spoilage(10)
    assert w.good_held_qty("resident", "iron") == 3.0 and w.good_condition("resident", "iron") == 1.0, \
        "iron is not perishable -- it keeps however long it sits"


# ------------------------------------------------------ G-shop-stock-rots (headline)
def test_a_shops_unsold_perishable_stock_rots_on_the_stall():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("monger", (2, 2))
    w.add_catalog_shop("fishstall", "fish", cell=(2, 2), keeper="monger", price=6, stock=4)
    assert w.stock_condition("fishstall") == 1.0, "fresh on the stall"
    w.tick_spoilage(1)
    assert w.stock_condition("fishstall") < 1.0, "unsold fish loses freshness on the stall (a world fact)"
    w.tick_spoilage(6)
    assert w.stock_qty("fishstall") == 0.0, "left too long, the unsold fish rots away and is thrown out"


# ------------------------------------------------------ G-durable-stock-keeps (no regression)
def test_a_shops_durable_stock_does_not_rot():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("smith", (2, 2))
    w.add_catalog_shop("ironmonger", "iron", cell=(2, 2), keeper="smith", price=5, stock=4)
    w.tick_spoilage(10)
    assert w.stock_qty("ironmonger") == 4.0 and w.stock_condition("ironmonger") == 1.0, "iron keeps"


# ------------------------------------------------------ G-the-price-is-the-sellers (headline)
def _coin(w, name):
    return float(w.eng.node(w._movers[name])["attrs"]["coin"])


def _buy_fish_at(stale_days):
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("monger", (2, 2), coin=0)
    w.add_catalog_shop("stall", "fish", cell=(2, 2), keeper="monger", price=8, stock=5)   # the SELLER sets price 8
    w.refresh_open()
    if stale_days:
        w.tick_spoilage(stale_days)
    w.make_trader("cust", (2, 2), coin=100, hunger_level=8, satiety=5)
    w.give_good("cust", good_code("fish"))
    c0, m0 = _coin(w, "cust"), _coin(w, "monger")
    w.buy("cust")
    return w.stock_condition("stall"), c0 - _coin(w, "cust"), _coin(w, "monger") - m0


def test_the_engine_transfers_the_sellers_price_it_does_not_compute_it():
    # fresh: sells at the seller's price 8
    cond, paid, got = _buy_fish_at(0)
    assert cond == 1.0 and paid == 8.0 and got == 8.0, "the buyer pays the SELLER's price (8), the monger receives it"
    # stale: the fish has spoiled (a world fact) but the ENGINE still transfers the price the seller SET --
    # it does not mark it down. A markdown for stale stock is the SELLER's pricing decision, not an engine multiply.
    cond, paid, got = _buy_fish_at(2)
    assert cond < 1.0 and paid == 8.0 and got == 8.0, "the price is the seller's -- the engine does not discount it for freshness"
    assert paid == got and paid == int(paid), "coin conserved and integer (fixed precision -- no float markdown)"


# ------------------------------------------------------ G-catalog-drives-decay (source audit)
def test_the_catalog_decay_rate_drives_spoilage_via_a_rule():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_spoil.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"be_spoil", "be_spoil_gone"} <= names, "spoilage is two seed rules, not Python"
    logic = json.dumps([{k: r[k] for k in ("match", "where", "effects")} for r in seed["rules"]])
    for named in ("fish", "bread", "milk"):
        assert named not in logic, f"the rules name no good ({named}) -- they read generic perishable/decay/condition"
    # different perishables decay at different catalog rates (bread vs cheese)
    assert E.decay_rate("cheese") < E.decay_rate("fish"), "aged cheese keeps far longer than fresh fish (catalog data)"
