"""BigvilleLabourWorld -- bigville R60 (block 373000): darkness gates OUTDOOR labour.

Composes bigville_farm + bigville_daynight on ONE substrate: a farmhand works an open field
(an unsheltered Place under the sky), so the day/night rules set his sees_dark. The harvest counts
only workers who can SEE (fm_harvest's light-aware worker count) -- so a field is reaped by DAY or
by MOONLIGHT, but a moonless/overcast night brings nothing in. The FORGE is a sheltered, self-lit
place, so the smith there never sees_dark -- craftwork carries on after dark while fieldwork stops.

A WORLD ADAPTER. No labour DECISION in Python -- fm_*/dn_* are seed rules. The adapter builds the
scene (field + sky + farmhand at the open field, forge + smith), advances the clock, and reads.
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
from worlds.bigville_daynight_world import (daylight_hours, moon_illumination,   # noqa: E402
                                            SEE_THRESHOLD)
from worlds.bigville_weather_world import seasonal_weather                        # noqa: E402


class BigvilleLabourWorld:
    def __init__(self, *, latitude=51.5):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_farm"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_daynight"), None)
        self.latitude = float(latitude)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "weather_factor": 1.0})
        self._sky = self.eng.add_node("Sky", {"hour": 12.0, "sunrise": 6.0, "sunset": 18.0,
                                              "moon_illum": 0.0, "cloud": 0.3, "is_night": 0.0,
                                              "light_level": 1.0, "see_threshold": SEE_THRESHOLD,
                                              "daylight_hours": 12.0})
        self.eng.add_edge_unchecked(self._town, "has_sky", self._sky)
        self._farms = {}; self._fields = {}; self._agents = {}

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_farm(self, name):
        p = self.eng.add_node("Place", {"kind": "farm", "name": name, "sheltered": 0.0,   # open field
                                        "food_out": 0.0, "meat": 0.0, "manure": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_place", p)
        self._farms[name] = p
        return p

    def add_field(self, farm, name, *, area=1.0, fertility=10.0, per_worker=1.0, depletion=2.0,
                  potency=1.0, apply_cap=6.0):
        fld = self.eng.add_node("Field", {"name": name, "area": float(area), "fertility": float(fertility),
                                          "per_worker": float(per_worker), "depletion": float(depletion),
                                          "potency": float(potency), "apply_cap": float(apply_cap),
                                          "ripe": 0.0, "last_yield": 0.0, "harvest_armed": 0.0,
                                          "fertilize_armed": 0.0})
        self.eng.add_edge_unchecked(self._farms[farm], "has_field", fld)
        self._fields[name] = fld
        return fld

    def add_farmhand(self, name, farm):
        """A farmhand: works the farm AND is AT the open field, so the day/night rules set his
        sees_dark from the sky."""
        a = self.eng.add_node("Agent", {"name": name, "role": "farmhand", "sees_dark": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self.eng.add_edge_unchecked(a, "works", self._farms[farm])
        self.eng.add_edge_unchecked(a, "at", self._farms[farm])
        self._agents[name] = a
        return a

    def add_forge(self, name="Forge"):
        p = self.eng.add_node("Place", {"kind": "forge", "name": name, "sheltered": 1.0, "lit": 1.0})
        self.eng.add_edge_unchecked(self._town, "has_place", p)
        self._farms[name] = p
        return p

    def add_smith(self, name, forge):
        a = self.eng.add_node("Agent", {"name": name, "role": "blacksmith", "sees_dark": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self.eng.add_edge_unchecked(a, "at", self._farms[forge])
        self._agents[name] = a
        return a

    def set_time(self, sim_day, hour, *, cloud=None):
        dl = daylight_hours(self.latitude, sim_day)
        cl = seasonal_weather(sim_day)[3] if cloud is None else float(cloud)
        for k, v in (("hour", float(hour)), ("sunrise", 12.0 - dl / 2.0), ("sunset", 12.0 + dl / 2.0),
                     ("moon_illum", moon_illumination(sim_day)), ("cloud", cl), ("daylight_hours", dl)):
            self.eng.set_attr(self._sky, k, v)
        self._run()

    def harvest(self, farm, field):
        self.eng.set_attr(self._fields[field], "ripe", 1.0)
        self.eng.set_attr(self._fields[field], "harvest_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def food_out(self, farm): return round(float(self.eng.node(self._farms[farm])["attrs"]["food_out"]), 4)
    def sees_dark(self, agent): return float(self.eng.node(self._agents[agent])["attrs"]["sees_dark"]) == 1.0
