"""BigvilleCognitionWorld -- bigville INTEGRATION (block 331000): the cognitive agent loop.

C1-C6 wired live on one agent: metabolism depletes energy (C6) -> drives rise (C1) -> the
dominant drive selects a costed/impactful action (C6: eat/work) whose output is scaled by
focus (C2, from arousal) -> the outcome becomes an appraised memory (C3) -> mood; chronic
frustration accrues allostatic load (C4) -> breakdown. One tick() = one cognitive cycle.

A WORLD ADAPTER. No decision in Python -- cg_*/mem_* are seed rules (goal selection, action,
appraisal, mood, load). The adapter advances the tick, provisions the world, and reads.
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


class BigvilleCognitionWorld:
    def __init__(self, *, deposit_stock=1000.0, retention=0.6):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_memory"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_cognition"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "tick_epoch": 0.0,
                                                "epoch": 0.0, "retention": float(retention)})
        self._dep = self.eng.add_node("Deposit", {"stock": float(deposit_stock)})
        self.eng.add_edge_unchecked(self._town, "has_deposit", self._dep)
        self._store = self.eng.add_node("Store", {"stock": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_store", self._store)
        self._agents = {}

    def _run(self):
        for _ in range(6):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, energy=8.0, max_energy=10.0, metab_cost=1.0,
                  comp_decay=0.25, w_sus=1.4, w_comp=1.0, arousal_opt=0.4, overload_gain=1.2,
                  work_cost=2.0, work_yield=3.0, comp_gain=0.3, food_energy=3.0,
                  window=3.0, frust_load=1.2, load_recovery=0.8, mood_thr=0.25):
        a = self.eng.add_node("Agent", {
            "name": name, "energy": float(energy), "max_energy": float(max_energy),
            "metab_cost": float(metab_cost), "comp_decay": float(comp_decay),
            "competence_level": 1.0, "sustenance_level": 1.0,
            "w_sus": float(w_sus), "w_comp": float(w_comp),
            "arousal": 0.0, "focus": 1.0, "arousal_opt": float(arousal_opt),
            "overload_gain": float(overload_gain), "pursues": "",
            "work_cost": float(work_cost), "work_yield": float(work_yield),
            "comp_gain": float(comp_gain), "food_energy": float(food_energy), "last_output": 0.0,
            "load": 0.0, "window": float(window), "frust_load": float(frust_load),
            "load_recovery": float(load_recovery), "broken": 0.0,
            "cares_about": "life", "mood": 0.0, "mood_thr": float(mood_thr),
            "ticked_epoch": 0.0, "acted_epoch": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_agent", a)
        self._agents[name] = a
        return a

    def tick(self, n=1):
        """One cognitive cycle: metabolize -> derive state -> act -> appraise -> mood/load."""
        for _ in range(n):
            e = self._town
            self.eng.set_attr(e, "tick_epoch", float(self.eng.node(e)["attrs"]["tick_epoch"]) + 1.0)
            self.eng.set_attr(e, "epoch", float(self.eng.node(e)["attrs"]["epoch"]) + 1.0)
            self._run()

    # ------------------------------------------------- glass-box read-offs
    def _a(self, name, k): return float(self.eng.node(self._agents[name])["attrs"].get(k, 0.0))
    def energy(self, name): return round(self._a(name, "energy"), 3)
    def competence(self, name): return round(self._a(name, "competence_level"), 3)
    def pursues(self, name): return self.eng.node(self._agents[name])["attrs"].get("pursues")
    def focus(self, name): return round(self._a(name, "focus"), 3)
    def arousal(self, name): return round(self._a(name, "arousal"), 3)
    def mood(self, name): return round(self._a(name, "mood"), 3)
    def load(self, name): return round(self._a(name, "load"), 3)
    def broken(self, name): return self._a(name, "broken") == 1.0
    def store_stock(self): return round(float(self.eng.node(self._store)["attrs"]["stock"]), 3)
    def deposit_stock(self): return round(float(self.eng.node(self._dep)["attrs"]["stock"]), 3)
