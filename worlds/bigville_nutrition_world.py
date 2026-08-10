"""BigvilleNutritionWorld -- bigville R41 (block 332000): nutrition + taste/spice + ale.

Different foods have different nutritional density and nutrient content; variety matters
(specific satiety); a chronically missing nutrient causes deficiency; taste (spice) buys
enjoyment (mood) and rescues a monotonous diet; ale feeds the body (calories) and the mind
(intoxication -> mood up, focus down).

A WORLD ADAPTER. No eat/metabolize/deficiency/psych DECISION in Python -- nu_* are seed
rules. The adapter arms which food (and whether spiced) is eaten, pulses metabolism, reads.
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

# the food codebook: (energy, protein, alcohol, taste)
_FOODS = {
    "fish":  (3.0, 2.0, 0.0, 0.4),   # nutrient-dense, some taste
    "bread": (4.0, 0.5, 0.0, 0.3),   # energy-dense, little protein
    "gruel": (3.0, 0.3, 0.0, 0.1),   # bland filler -- the monotony/spice case
    "ale":   (2.0, 0.0, 1.5, 0.5),   # empty calories + intoxicant
}


class BigvilleNutritionWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_nutrition"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "epoch": 0.0})
        for kind, (e, p, al, t) in _FOODS.items():
            f = self.eng.add_node("Food", {"kind": kind, "energy": e, "protein": p,
                                           "alcohol": al, "taste": t})
            self.eng.add_edge_unchecked(self._town, "has_food", f)
        self._agents = {}

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, spice_stock=0.0, protein_need=1.0):
        a = self.eng.add_node("Agent", {
            "name": name, "energy": 0.0, "protein_store": 0.0, "intoxication": 0.0,
            "monotony": 0.0, "last_kind": "", "deficiency": 0.0, "meal_pleasure": 0.0,
            "mood": 0.0, "focus": 1.0, "eat_armed": 0.0, "use_spice": 0.0,
            "eating_kind": "", "spice_stock": float(spice_stock), "last_meal_energy": 0.0,
            # dispositions
            "base_mood": 0.0, "base_focus": 1.0, "intox_mood_gain": 0.3, "intox_focus_pen": 0.25,
            "pleasure_gain": 0.6, "def_mood_pen": 0.6, "def_focus_pen": 0.5,
            "protein_need": float(protein_need), "protein_decay": 0.5, "sober_rate": 0.5,
            "monotony_step": 0.3, "monotony_cap": 0.9, "monotony_decay": 0.4, "pleasure_decay": 0.5,
            "def_step": 0.25, "def_recover": 0.3, "spice_bonus": 0.7, "intox_cap": 3.0,
            "metab_epoch": 0.0, "dchecked_epoch": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_agent", a)
        self._agents[name] = a
        return a

    def eat(self, name, kind, *, spiced=False):
        a = self._agents[name]
        self.eng.set_attr(a, "eating_kind", kind)
        self.eng.set_attr(a, "use_spice", 1.0 if spiced else 0.0)
        self.eng.set_attr(a, "eat_armed", 1.0)
        self._run()

    def give_spice(self, name, n):
        a = self._agents[name]
        self.eng.set_attr(a, "spice_stock", float(self.eng.node(a)["attrs"]["spice_stock"]) + float(n))

    def tick(self, n=1):
        for _ in range(n):
            self.eng.set_attr(self._town, "epoch", float(self.eng.node(self._town)["attrs"]["epoch"]) + 1.0)
            self._run()

    # ------------------------------------------------- glass-box read-offs
    def _a(self, name, k): return float(self.eng.node(self._agents[name])["attrs"].get(k, 0.0))
    def energy(self, name): return round(self._a(name, "energy"), 3)
    def last_meal_energy(self, name): return round(self._a(name, "last_meal_energy"), 3)
    def protein(self, name): return round(self._a(name, "protein_store"), 3)
    def intoxication(self, name): return round(self._a(name, "intoxication"), 3)
    def deficiency(self, name): return round(self._a(name, "deficiency"), 3)
    def mood(self, name): return round(self._a(name, "mood"), 3)
    def focus(self, name): return round(self._a(name, "focus"), 3)
    def meal_pleasure(self, name): return round(self._a(name, "meal_pleasure"), 3)
    def spice_stock(self, name): return round(self._a(name, "spice_stock"), 3)
