"""BigvilleActionsWorld -- bigville R69 (block 385000): world actions are a data structure.

An ActionSpec is a recipe data row; ONE generic rule (ax_do) executes any of them. This adapter
sets up the store (Stock nodes) and actors, lets an actor DO an action by name, and -- crucially --
can add a NEW action as a DATA ROW at runtime (no code), which the same rule then runs.

A WORLD ADAPTER. No action logic in Python -- ax_do is the only rule; the adapter mints data.
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


class BigvilleActionsWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_actions"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._store = self.eng.add_node("Store", {"name": "store"})
        self.eng.add_edge_unchecked(self._town, "has_store", self._store)
        self._stock = {}
        self._actors = {}
        # wire the seed's recipe rows to this town (they were minted at seed-load, before the town existed)
        for n in self.eng.nodes("ActionSpec"):
            self.eng.add_edge_unchecked(self._town, "has_actionspec", n)
        self.set_stock("none", 1e9)                     # the empty-slot placeholder for unused inputs

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    def set_stock(self, kind, qty):
        if kind in self._stock:
            self.eng.set_attr(self._stock[kind], "qty", float(qty))
        else:
            s = self.eng.add_node("Stock", {"kind": kind, "qty": float(qty)})
            self.eng.add_edge_unchecked(self._store, "stock", s)
            self._stock[kind] = s
        return self._stock[kind]

    def add_actor(self, name, *, role="smith"):
        a = self.eng.add_node("Agent", {"name": name, "role": role, "doing": "", "fatigue": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_actor", a)
        self._actors[name] = a
        return a

    def add_action(self, name, *, requires, in1_kind, in1_qty, in2_kind="none", in2_qty=0.0,
                   out_kind, out_qty, difficulty=1.0, time_minutes=30.0, wear_rate=0.0):
        """Add a NEW action as a DATA ROW at runtime -- the generic ax_do rule runs it with no code."""
        sp = self.eng.add_node("ActionSpec", {"name": name, "requires": requires,
                                              "in1_kind": in1_kind, "in1_qty": float(in1_qty),
                                              "in2_kind": in2_kind, "in2_qty": float(in2_qty),
                                              "out_kind": out_kind, "out_qty": float(out_qty),
                                              "difficulty": float(difficulty),
                                              "time_minutes": float(time_minutes), "wear_rate": float(wear_rate)})
        self.eng.add_edge_unchecked(self._town, "has_actionspec", sp)
        return sp

    def do(self, actor, action_name):
        """The actor performs an action (by name). The generic rule applies the recipe from its data."""
        self.eng.set_attr(self._actors[actor], "doing", action_name)
        self.set_stock(self._out_kind(action_name), self.stock(self._out_kind(action_name)))  # ensure out stock exists
        self._run()

    def _out_kind(self, action_name):
        for n in self.eng.nodes("ActionSpec"):
            a = self.eng.node(n)["attrs"]
            if a["name"] == action_name:
                return a["out_kind"]
        return "none"

    # ------------------------------------------------- glass-box read-offs
    def stock(self, kind):
        return round(float(self.eng.node(self._stock[kind])["attrs"]["qty"]), 4) if kind in self._stock else 0.0
    def fatigue(self, actor): return round(float(self.eng.node(self._actors[actor])["attrs"]["fatigue"]), 4)
    def actions(self):
        return {self.eng.node(n)["attrs"]["name"] for n in self.eng.nodes("ActionSpec")}
