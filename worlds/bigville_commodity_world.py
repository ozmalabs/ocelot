"""BigvilleCommodityWorld -- bigville R63 (block 377000): a good is tradeable purely because it
exists. One generic rule (tr_trade) trades any Good node -- charcoal for the same reason timber,
grain, or a tool would.

A WORLD ADAPTER. No trade DECISION in Python -- tr_trade is a seed rule. The adapter mints agents,
goods, and wants, ticks, and reads who holds what and the coin.
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


class BigvilleCommodityWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_commodity"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._agents = {}
        self._goods = {}

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, coin=0.0):
        a = self.eng.add_node("Agent", {"name": name, "coin": float(coin), "wants": ""})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self._agents[name] = a
        return a

    def give_good(self, holder, kind, *, qty=1.0, price=1.0):
        """Give an agent a Good to hold (e.g. a lot of charcoal). It exists -> it is tradeable."""
        g = self.eng.add_node("Good", {"kind": kind, "qty": float(qty), "price": float(price),
                                       "owner": holder})
        self.eng.add_edge_unchecked(self._agents[holder], "holds", g)
        self._goods[(holder, kind)] = g
        return g

    def wants(self, buyer, kind):
        self.eng.set_attr(self._agents[buyer], "wants", kind)

    def trade(self):
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def coin(self, agent): return round(float(self.eng.node(self._agents[agent])["attrs"]["coin"]), 4)
    def holds_kind(self, agent, kind):
        return any(self.eng.node(g)["attrs"]["kind"] == kind
                   for g in self.eng.neighbours(self._agents[agent], "holds"))
    def total_coin(self):
        return round(sum(float(self.eng.node(a)["attrs"]["coin"]) for a in self._agents.values()), 4)
