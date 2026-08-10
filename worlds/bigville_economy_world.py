"""BigvilleEconomyWorld -- production-economy R5 (block 304000): the CLOSED
self-balancing loop, on the real 100-resident cast.

Composes resource supply + emergent price (R3) + labour mobility (R4) into one
loop: scarce good -> high price -> high wage -> labour IN -> more supply ->
price DOWN -> labour OUT -> equilibrium at supply ~ demand. The mobile labour pool
and its per-resident role_identity come from the seeded 100-cast
(bigville_cast100.json). Untuned; stability is measured, not dialed.

A WORLD ADAPTER. No economic decision in Python -- extract/price/wage/switch are
the seed rules (bigville_econloop). The adapter mints trades/workers, advances the
tick (bump epoch, reset the per-tick price gate), schedules one switch-turn per
worker, and reads state.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs                                              # noqa: E402
from substrate.seed_loader import manifest_for                   # noqa: E402

# cast role -> which extraction trade that resident works (the mobile labour pool).
_ROLE_TO_TRADE = {"fisher": "fishing", "forester": "foresting", "quarrier": "quarrying",
                  "labourer": "fishing", "farm_labourer": "foresting"}


class BigvilleEconomyWorld:
    def __init__(self, *, friction_scale=6.0):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_econloop"), None)
        self._town = self.eng.add_node("Town", {"friction_scale": float(friction_scale),
                                                "epoch": 0.0})
        self._jobs = {}          # trade -> Job nid
        self._deps = {}          # trade -> Deposit nid
        self._workers = {}       # name -> Worker nid

    # ------------------------------------------------------------------ ingest
    def add_trade(self, trade, *, stock, growback, capacity, yield_=1.0, demand=10.0,
                  price=5.0, price_step=0.5, min_price=1.0, crowd=0.3):
        dep = self.eng.add_node("Deposit", {"kind": trade, "stock": float(stock),
                                            "growback": float(growback),
                                            "capacity": float(capacity)})
        job = self.eng.add_node("Job", {"trade": trade, "yield": float(yield_),
                                        "demand": float(demand), "price": float(price),
                                        "price_step": float(price_step),
                                        "min_price": float(min_price),
                                        "wage": float(price) * float(yield_),
                                        "crowd": float(crowd),
                                        "supply": 0.0, "n_workers": 0.0,
                                        "ec_epoch": 0.0, "priced_epoch": 0.0})
        self.eng.add_edge_unchecked(job, "harvests", dep)
        self.eng.add_edge_unchecked(job, "in_town", self._town)
        self.eng.add_edge_unchecked(self._town, "has_job", job)
        self._jobs[trade] = job
        self._deps[trade] = dep
        return job

    def add_worker(self, name, *, trade, role_identity):
        w = self.eng.add_node("Worker", {"name": name, "role": trade,
                                         "role_identity": float(role_identity),
                                         "can_switch": 0.0})
        self.eng.add_edge_unchecked(w, "in_town", self._town)
        self.eng.add_edge_unchecked(w, "works_as", self._jobs[trade])
        self._workers[name] = w
        return w

    def load_cast_labour(self, cast_seed="bigville_cast100", limit=None):
        """Wire the extraction-eligible residents of the seeded cast into the loop,
        with their real role_identity. Returns how many were placed."""
        path = os.path.join(_ROOT, "seeds", cast_seed + ".json")
        cast = json.load(open(path))["residents"]
        n = 0
        for r in cast:
            trade = _ROLE_TO_TRADE.get(r.get("role"))
            if trade is None or trade not in self._jobs:
                continue
            self.add_worker(r["name"], trade=trade, role_identity=float(r["role_identity"]))
            n += 1
            if limit and n >= limit:
                break
        return n

    # ---------------------------------------------------------------- tick
    def tick(self):
        """One economic tick: re-price/extract at the tick's labour allocation, then
        let each worker take a switch-turn (labour responds to this tick's wages)."""
        self.eng.set_attr(self._town, "epoch",
                          float(self.eng.node(self._town)["attrs"]["epoch"]) + 1.0)
        for job in self._jobs.values():
            self.eng.set_attr(job, "priced_epoch", 0.0)      # allow one price move
        self.eng.force_all_dirty()
        self.eng.run_rules(1000000)                          # extract -> price -> wage
        for w in self._workers.values():                     # labour mobility, one turn each
            self.eng.set_attr(w, "can_switch", 1.0)
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)
            self.eng.set_attr(w, "can_switch", 0.0)

    def run(self, T=40):
        for _ in range(T):
            self.tick()
        return T

    # ------------------------------------------------- glass-box read-offs
    def price(self, trade):
        return float(self.eng.node(self._jobs[trade])["attrs"]["price"])

    def wage(self, trade):
        return float(self.eng.node(self._jobs[trade])["attrs"]["wage"])

    def supply(self, trade):
        return float(self.eng.node(self._jobs[trade])["attrs"]["supply"])

    def deposit_stock(self, trade):
        return float(self.eng.node(self._deps[trade])["attrs"]["stock"])

    def n_in(self, trade):
        j = self._jobs[trade]
        return int(len([w for w in self._workers.values()
                        if j in list(self.eng.neighbours(w, "works_as"))]))

    def snapshot(self):
        return {t: dict(price=round(self.price(t), 2), wage=round(self.wage(t), 2),
                        n=self.n_in(t), supply=round(self.supply(t), 1),
                        stock=round(self.deposit_stock(t), 1)) for t in sorted(self._jobs)}
