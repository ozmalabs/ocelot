"""BigvilleContainerWorld -- bigville R71 (block 388000): containers, a sibling class to piles.

A Container (barrel, sack, bin, chest, safe) is a physical, located world-fact like a pile, but
with a capacity that holds contents. Filling/emptying moves matter (conserved), bounded by
capacity, by access. A WORLD ADAPTER: ct_fill/ct_empty are seed rules; the adapter mints the yard,
piles, containers (with an inner content pile), and agents, arms fill/empty, and reads.
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


class BigvilleContainerWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_container"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._yard = self.eng.add_node("Place", {"name": "the yard"})
        self.eng.add_edge_unchecked(self._town, "has_place", self._yard)
        self._agents = {}; self._piles = {}; self._containers = {}

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    def add_agent(self, name):
        a = self.eng.add_node("Agent", {"name": name, "fill_armed": 0.0, "fill_amount": 0.0,
                                        "empty_armed": 0.0, "empty_amount": 0.0,
                                        "lock_armed": 0.0, "unlock_armed": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self.eng.add_edge_unchecked(a, "at", self._yard)
        self._agents[name] = a
        return a

    def add_pile(self, kind, qty=0.0):
        """Loose matter -- a pile at the yard."""
        p = self.eng.add_node("Pile", {"kind": kind, "qty": float(qty)})
        self.eng.add_edge_unchecked(p, "at", self._yard)
        self._piles[kind] = p
        return p

    def add_container(self, name, *, kind="barrel", holds, capacity=10.0, qty=0.0,
                      lock_id=0.0, locked=False):
        """A container (peer of a pile): located, with a capacity, holding an inner content pile.
        A lockable container (lock_id > 0) can be locked -- a SAFE is a locked container."""
        c = self.eng.add_node("Container", {"kind": kind, "name": name, "capacity": float(capacity),
                                            "lock_id": float(lock_id), "locked": 1.0 if locked else 0.0})
        self.eng.add_edge_unchecked(c, "at", self._yard)
        inner = self.eng.add_node("Pile", {"kind": holds, "qty": float(qty)})   # the contents
        self.eng.add_edge_unchecked(c, "contains", inner)
        self._containers[name] = (c, inner)
        return c

    def give_key(self, agent, opens):
        """Give an agent a key that opens a given lock_id."""
        k = self.eng.add_node("Key", {"opens": float(opens)})
        self.eng.add_edge_unchecked(self._agents[agent], "holds_key", k)
        return k

    def lock(self, agent, container):
        self.eng.set_attr(self._agents[agent], "lock_armed", 1.0); self._run()

    def unlock(self, agent, container):
        self.eng.set_attr(self._agents[agent], "unlock_armed", 1.0); self._run()

    def is_locked(self, container):
        return float(self.eng.node(self._containers[container][0])["attrs"].get("locked", 0.0)) == 1.0

    def fill(self, agent, container, amount):
        self.eng.set_attr(self._agents[agent], "fill_amount", float(amount))
        self.eng.set_attr(self._agents[agent], "fill_armed", 1.0); self._run()

    def empty(self, agent, container, amount):
        self.eng.set_attr(self._agents[agent], "empty_amount", float(amount))
        self.eng.set_attr(self._agents[agent], "empty_armed", 1.0); self._run()

    # ------------------------------------------------- glass-box read-offs
    def loose_qty(self, kind): return round(float(self.eng.node(self._piles[kind])["attrs"]["qty"]), 4)
    def contents(self, container): return round(float(self.eng.node(self._containers[container][1])["attrs"]["qty"]), 4)
    def capacity(self, container): return round(float(self.eng.node(self._containers[container][0])["attrs"]["capacity"]), 4)
    def room(self, container): return round(self.capacity(container) - self.contents(container), 4)
    def is_container(self, container): return self.eng.node(self._containers[container][0])["type"] == "Container"
    def located(self, container): return self.eng.has_edge(self._containers[container][0], "at", self._yard)
    def total(self, kind):
        loose = self.loose_qty(kind) if kind in self._piles else 0.0
        inside = sum(round(float(self.eng.node(inner)["attrs"]["qty"]), 4)
                     for _, inner in self._containers.values()
                     if self.eng.node(inner)["attrs"]["kind"] == kind)
        return round(loose + inside, 4)
