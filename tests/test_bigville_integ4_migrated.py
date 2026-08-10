"""bigville R10d (275000) gate -- circulation is REAL: the shopping loop is wired
(know -> seek -> walk -> buy), coin flows buyer->keeper, Sigma(coin) stays invariant, and
movers actually reach the market stalls.

Diagnosis-confirming: in R10c the Source knowledge is ABSENT and the keepers are NOT on
their stalls (so be_exchange could never match); R10d seeds the Source, mans the stall,
steps the landed nd_/mv_/be_ rules, and circulation goes 0 -> >0 with coin conserved.
No new seed, no new Rust -- the RULES already existed."""
from __future__ import annotations

import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_integ3_world import BigvilleInteg3World            # noqa: E402
from worlds.bigville_integ4_world import BigvilleInteg4World, TICKS_PER_DAY  # noqa: E402

_DAYS = 4
_TICKS = _DAYS * TICKS_PER_DAY


@pytest.fixture(scope="module")
def town():
    w = BigvilleInteg4World(cast=16, seed=275000)
    w._c0 = w.system_coin()
    w._circ0 = w.circulation()
    for _ in range(_TICKS):
        w.integ_step()
    return w


def test_builds_and_does_not_explode(town):
    assert town.exploded is None
    assert len(town.macro) == _TICKS


def test_diagnosis_r10c_had_no_source_and_no_seller_on_the_stall():
    """The gap R10d closes: in R10c NO Source node exists (a buyer has no knowledge of
    where a good is sold) and the keepers are NOT co-located with their shops (be_exchange
    can never match). Cheap: construction only, no ticks."""
    base = BigvilleInteg3World(cast=16, seed=275000, enable_drama=False,
                               enable_school=False, enable_loud=False)
    assert not list(base.eng.nodes("Source")), "R10c should have NO Source knowledge"
    co_located = 0
    for nm, sh in base._shops.items():
        cell = list(base.eng.neighbours(sh, "at_cell"))[0]
        a = base.eng.node(cell)["attrs"]
        scell = (int(a["cx"]), int(a["cy"]))
        if base.pos.get(base._shopkeepers[nm]) == scell:
            co_located += 1
    assert co_located == 0, "R10c keepers are not on their stalls"


def test_r10d_seeds_source_knowledge_and_mans_the_stall(town):
    """After R10d: a Source per shop, at the stall cell, carrying the shop's good; and the
    keeper is on the stall (a seller present to sell)."""
    sources = list(town.eng.nodes("Source"))
    assert len(sources) >= len(town._shops)
    for nm, sh in town._shops.items():
        scell = town._market[nm]
        assert town.pos.get(town._shopkeepers[nm]) == scell, "keeper mans the stall"
        # a Source sits at the stall carrying the shop's good.
        good = float(town.eng.node(sh)["attrs"]["good"])
        src = town._source_of[nm]
        a = town.eng.node(src)["attrs"]
        assert (int(a["cx"]), int(a["cy"])) == scell
        assert float(a["good"]) == good


def test_circulation_is_real_zero_to_positive(town):
    """circulation goes 0 -> >0 -- real buys, not a read-off. Per-day buys are recorded."""
    assert town._circ0 == 0
    assert town.circulation() > 0
    assert sum(d["buys"] for d in town.buys_per_day) > 0


def test_coin_flows_buyer_to_keeper(town):
    """A purchase is a conserved buyer->keeper transfer: at least one keeper accrued
    takings from selling."""
    takings = town.keeper_takings()
    assert any(v > 0 for v in takings.values()), takings


def test_conservation_invariant_after_real_buying(town):
    """Wiring real buying introduces NO coin leak: Sigma(coin+reserves+pool+funds) is
    invariant (a buy moves price buyer->keeper; the raw-material inflow is goods, not
    coin)."""
    assert abs(town.system_coin() - town._c0) < 1e-6


def test_movers_reach_the_stall(town):
    """The walk actually happens: recorded is_at traces show movers arriving at a stall,
    starting from a distinct home cell."""
    assert town.shopping_traces
    arrived = [t for t in town.shopping_traces if t["arrived"]]
    assert arrived, "at least one mover reached a stall"
    t = arrived[0]
    assert t["home"] != t["shop"] and t["hops"] >= 1


def test_trip_fits_the_unchanged_day_budget(town):
    """The market is clustered so the home->shop trip fits the UNCHANGED 36-tick day
    (the day was not lengthened to manufacture circulation)."""
    tr = town.trip_report
    assert tr["ticks_per_day"] == 36
    assert tr["fits_day_budget"] is True
    assert tr["home_to_shop_max"] <= 18
