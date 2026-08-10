"""bigville_map_kitchen -- block 342000: the food lifecycle runs on the GENERATED map.

The payoff of the generated map + affordance reuse: a cook prepares a meal in a kitchen the
GENERATOR placed (not a hand-built one), the real `fs_prepare` / `fs_eat` rules firing against
the generated `Station`. Meal quality tracks the kitchen TIER (commercial > normal > poor),
and a kitchenless house genuinely cannot cook -- its household eats raw, which the food rules
grade as poor nutrition + illness. That last case is the glass-box of the social determinants
of health: the affordance distribution (who has a kitchen) drives who eats well.

A WORLD ADAPTER: it mints food/cook/eater nodes and arms prep/eating; the cooking and the
grading are the seed rules (fs_prepare / fs_eat). No agent decisions here.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for          # noqa: E402
from worlds.bigville_map_generator import BigvilleMapGenerator   # noqa: E402
from worlds.bigville_foodstuff_world import _FOODS      # noqa: E402  (the food codebook, reused)


class MapKitchen:
    def __init__(self, *, seed=0, spec=None):
        self.gen = BigvilleMapGenerator(spec=spec, seed=seed).generate()
        self.eng = self.gen.eng
        self.eng.load_seed_manifest(manifest_for("bigville_foodstuff"), None)
        self._town = self.gen._town
        self._n = 0

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    def _raw_item(self, kind):
        e, t, sr, np_, pb = _FOODS[kind]
        larder = self.eng.add_node("Larder", {"cold": 0.0, "capacity": 100.0, "cold_factor": 0.4})
        self.eng.add_edge_unchecked(self._town, "has_larder", larder)
        it = self.eng.add_node("FoodItem", {"kind": kind, "state": "raw", "freshness": 1.0,
                                            "portions": 3.0, "energy": e, "taste": t, "spoil_rate": sr,
                                            "needs_prep": np_, "prep_bonus": pb, "prep_armed": 0.0,
                                            "prep_kind": "cook", "eat_armed": 0.0, "seen_epoch": 0.0})
        self.eng.add_edge_unchecked(larder, "has_item", it)
        return it

    def cook_meal(self, place, *, kind="grain", cook_skill=0.7):
        """A cook prepares a meal at `place`'s kitchen (the Station the generator placed).
        Returns (state, quality). If the place has no kitchen, the meal stays raw."""
        it = self._raw_item(kind)
        self._n += 1
        cook = self.eng.add_node("Agent", {"name": f"cook{self._n}", "cook_skill": float(cook_skill),
                                           "energy": 10.0, "cook_effort": 1.0, "learn_rate": 0.05})
        self.eng.add_edge_unchecked(cook, "preparing", it)
        station = self.gen.kitchen_station(place)         # None -> no heated station -> cannot cook
        if station is not None:
            self.eng.add_edge_unchecked(cook, "using", station)
        self.eng.set_attr(it, "prep_armed", 1.0)
        self._run()
        a = self.eng.node(it)["attrs"]
        return a["state"], round(float(a.get("quality", 0.0)), 4), it

    def eat(self, it, *, eater="Diner"):
        """A household eats the item -- fs_eat grades it (raw/uncooked -> poor nutrition + illness)."""
        e = self.eng.add_node("Agent", {"name": eater, "raw_penalty": 0.15, "spoiled_disgust": 0.6,
                                        "rot_illness": 0.5, "raw_illness": 0.3, "illness": 0.0,
                                        "last_nutrition": 0.0, "last_pleasantness": 0.0, "last_ate": 0.0})
        self.eng.add_edge_unchecked(it, "eaten_by", e)
        self.eng.set_attr(it, "eat_armed", 1.0)
        self._run()
        a = self.eng.node(e)["attrs"]
        return {"nutrition": round(float(a["last_nutrition"]), 4),
                "illness": round(float(a["illness"]), 4)}
