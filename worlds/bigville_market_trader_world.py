"""BigvilleMarketTraderWorld -- bigville R29 v2 (block 318000): the visiting market
trader who sells DIFFERENT goods, not locally available.

A remote merchant deals only in EXOTIC wares the town cannot make itself (no local
producer). He is the sole source, so the town gains access to a good it otherwise
could not have; coin leaves the closed economy the way the inn brings it in. A
stall of a locally-produced good is refused. Departs when sold out.

A WORLD ADAPTER. No open/refuse/grant/buy/depart DECISION in Python -- mt_* are
seed rules. The adapter mints the town's local goods, the trader/stall, serialises
buyer turns (so stock never races negative), ticks, and reads.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402


class BigvilleMarketTraderWorld:
    def __init__(self, local_goods=("fish", "lumber", "stone", "furniture", "blocks")):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_bells"), None)   # the town clock
        self.eng.load_seed_manifest(manifest_for("bigville_market_trader"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "external_outflux": 0.0})
        self._residents = {}
        self._trader = None
        self._stall = None
        # the market bell opens trading -- there is no forced market-day flag.
        self._church = self.eng.add_node("Church", {"name": "Bigville Church"})
        self.eng.add_edge_unchecked(self._town, "has_church", self._church)
        self._bell = self.eng.add_node("Bell", {"ring_armed": 0.0, "toll_hour": 0.0,
                                                "toll_kind": "", "call_strength": 1.0})
        self.eng.add_edge_unchecked(self._church, "has_bell", self._bell)
        for g in local_goods:                                   # what the town makes itself
            lg = self.eng.add_node("LocalGood", {"name": g})
            self.eng.add_edge_unchecked(self._town, "produces", lg)

    # ------------------------------------------------------------------ ingest
    def add_local_good(self, name):
        lg = self.eng.add_node("LocalGood", {"name": name})
        self.eng.add_edge_unchecked(self._town, "produces", lg)
        return lg

    def add_resident(self, name, *, coin=20.0, wants=0.0):
        r = self.eng.add_node("Resident", {"name": name, "coin": float(coin),
                                            "wants": float(wants), "holds_ware": 0.0,
                                            "buy_armed": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", r)
        self._residents[name] = r
        return r

    def arrive_trader(self, name, *, good, stock, ask_price):
        self._trader = self.eng.add_node("Trader", {"name": name, "coin": 0.0, "departed": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_trader", self._trader)
        self._stall = self.eng.add_node("Stall", {"good": good, "stock": float(stock),
                                                  "ask_price": float(ask_price),
                                                  "open": 0.0, "refused": 0.0})
        self.eng.add_edge_unchecked(self._trader, "has_stall", self._stall)
        return self._trader

    # ------------------------------------------------------------------ run
    def _run(self):
        self.eng.force_all_dirty()
        return self.eng.run_rules(1000000)

    def market_day(self):
        """One market day: the MARKET BELL tolls to open trading (no forced flag), the
        stall opens (if exotic) or is refused, the town gains import-access, then each
        resident gets a serialised turn to buy; a sold-out trader departs."""
        self.eng.set_attr(self._bell, "toll_kind", "market")   # ring the market bell
        self.eng.set_attr(self._bell, "ring_armed", 1.0)
        self._run()                                             # ring -> open / refuse / grant access
        for r in self._residents.values():
            self.eng.set_attr(r, "buy_armed", 0.0)
        for r in self._residents.values():
            self.eng.set_attr(r, "buy_armed", 1.0)
            self._run()
            self.eng.set_attr(r, "buy_armed", 0.0)
        self._run()                                             # settle departure

    # ------------------------------------------------- glass-box read-offs
    def stall_open(self):
        return float(self.eng.node(self._stall)["attrs"].get("open", 0.0)) == 1.0

    def stall_refused(self):
        return float(self.eng.node(self._stall)["attrs"].get("refused", 0.0)) == 1.0

    def stall_stock(self):
        return int(self.eng.node(self._stall)["attrs"]["stock"]) if self._stall else 0

    def trader_coin(self):
        return float(self.eng.node(self._trader)["attrs"]["coin"])

    def trader_departed(self):
        return float(self.eng.node(self._trader)["attrs"].get("departed", 0.0)) == 1.0

    def has_stall(self):
        return self._stall in self.eng.neighbours(self._trader, "has_stall")

    def coin_of(self, name):
        return float(self.eng.node(self._residents[name])["attrs"]["coin"])

    def holds_of(self, name):
        return int(self.eng.node(self._residents[name])["attrs"]["holds_ware"])

    def local_goods(self):
        return sorted(self.eng.node(g)["attrs"]["name"]
                      for g in self.eng.neighbours(self._town, "produces"))

    def imported_goods(self):
        return sorted(self.eng.node(g)["attrs"]["name"]
                      for g in self.eng.neighbours(self._town, "imports_good"))

    def external_outflux(self):
        return float(self.eng.node(self._town)["attrs"]["external_outflux"])
