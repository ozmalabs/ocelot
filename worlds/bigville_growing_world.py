"""BigvilleGrowingWorld -- bigville R67 (block 383000): the season drives the harvest.

Composes bigville_weather + bigville_farm + bigville_growing on one town: the farm's weather_factor
is DERIVED from the real seasonal weather (temperature/rain/sun), so a good growing season yields
more than a cold drought. Closes the weather->farm hook left open since 368000.

A WORLD ADAPTER -- wf_growing / fm_harvest are seed rules; the adapter sets the season, builds the
farm, arms the harvest, and reads.
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


class BigvilleGrowingWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_farm"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_growing"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "temperature": 15.0, "rain": 0.0,
                                                "sun": 0.5, "weather_factor": 1.0})
        self._farms = {}; self._fields = {}

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    def add_farm(self, name):
        p = self.eng.add_node("Place", {"kind": "farm", "name": name, "food_out": 0.0, "meat": 0.0,
                                        "manure": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_place", p)
        self._farms[name] = p
        return p

    def add_field(self, farm, name, *, area=1.0, fertility=10.0, per_worker=1.0):
        fld = self.eng.add_node("Field", {"name": name, "area": float(area), "fertility": float(fertility),
                                          "per_worker": float(per_worker), "depletion": 2.0, "potency": 1.0,
                                          "apply_cap": 6.0, "ripe": 0.0, "last_yield": 0.0,
                                          "harvest_armed": 0.0, "fertilize_armed": 0.0})
        self.eng.add_edge_unchecked(self._farms[farm], "has_field", fld)
        self._fields[name] = fld
        return fld

    def hire_worker(self, farm, name):
        w = self.eng.add_node("Agent", {"name": name, "role": "farmhand", "sees_dark": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", w)
        self.eng.add_edge_unchecked(w, "works", self._farms[farm])
        return w

    def set_season(self, *, temperature, rain, sun):
        """Set the season's real weather; wf_growing derives the farm's weather_factor from it."""
        self.eng.set_attr(self._town, "temperature", float(temperature))
        self.eng.set_attr(self._town, "rain", float(rain))
        self.eng.set_attr(self._town, "sun", float(sun))
        self._run()

    def harvest(self, farm, field):
        self.eng.set_attr(self._fields[field], "ripe", 1.0)
        self.eng.set_attr(self._fields[field], "harvest_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def weather_factor(self): return round(float(self.eng.node(self._town)["attrs"]["weather_factor"]), 4)
    def food_out(self, farm): return round(float(self.eng.node(self._farms[farm])["attrs"]["food_out"]), 4)
    def last_yield(self, field): return round(float(self.eng.node(self._fields[field])["attrs"]["last_yield"]), 4)
