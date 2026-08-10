"""BigvilleFarmWorld -- bigville R52 (block 368000): real farms.

A farm is a Place on the map, worked by farmhand agents, with fields (crops) and livestock that
live, grow, breed, and die/are slaughtered. Understaffed fields don't get fully reaped; the herd
must breed to replace slaughtered/dead animals; manure closes the nutrient loop.

A WORLD ADAPTER. No harvest/grow/breed/die/slaughter DECISION in Python -- fm_*/fa_* are seed
rules. The adapter mints the farm-place/fields/workers/animals, passes seasons, arms
harvest/slaughter, delivers night-soil, and reads.
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


class BigvilleFarmWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_farm"), None)
        # weather_factor is the HOOK the real weather system (bigville_weather) drives; default 1.0
        self._town = self.eng.add_node("Town", {"name": "Bigville", "weather_factor": 1.0})
        self._farms = {}
        self._fields = {}
        self._animals = {}
        self._x = 20.0        # farms sit out on the map's edge

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ the farm is a PLACE on the map
    def add_farm(self, name, *, owner="Farmer"):
        p = self.eng.add_node("Place", {"kind": "farm", "name": name, "owner": owner,
                                        "x": self._x, "y": 0.0, "manure": 0.0, "food_out": 0.0, "meat": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_place", p)   # on the map
        self._x += 3.0
        self._farms[name] = p
        return p

    def add_field(self, farm, name, *, area=1.0, fertility=10.0, per_worker=0.5, depletion=2.0,
                  potency=1.0, apply_cap=6.0):
        fld = self.eng.add_node("Field", {"name": name, "area": float(area), "fertility": float(fertility),
                                          "per_worker": float(per_worker), "depletion": float(depletion),
                                          "potency": float(potency), "apply_cap": float(apply_cap),
                                          "ripe": 0.0, "last_yield": 0.0, "harvest_armed": 0.0,
                                          "fertilize_armed": 0.0})
        self.eng.add_edge_unchecked(self._farms[farm], "has_field", fld)
        self._fields[name] = fld
        return fld

    def hire_worker(self, farm, name):
        """A FARMHAND (an agent) hired to work the land -- worker -works-> farm (a role; composes
        with bigville_office). Enough hands are needed to bring in the harvest."""
        w = self.eng.add_node("Agent", {"name": name, "role": "farmhand", "alive": 1.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", w)
        self.eng.add_edge_unchecked(w, "works", self._farms[farm])
        self._animals.setdefault("__workers__", {})[name] = w
        return w

    def add_animal(self, farm, name, *, sex="F", age=4.0, weight=6.0, maturity=3.0, max_weight=10.0,
                   growth=2.0, muck_rate=1.0, lifespan=12.0):
        a = self.eng.add_node("Animal", {"name": name, "sex": sex, "age": float(age), "weight": float(weight),
                                         "alive": 1.0, "died": 0.0, "maturity": float(maturity),
                                         "max_weight": float(max_weight), "growth": float(growth),
                                         "muck_rate": float(muck_rate), "lifespan": float(lifespan),
                                         "season_armed": 0.0, "breed_armed": 0.0, "slaughter_armed": 0.0})
        self.eng.add_edge_unchecked(self._farms[farm], "has_animal", a)
        self._animals[name] = a
        return a

    def pass_season(self, farm, n=1):
        """A season passes -- the herd ages/grows/breeds and the old die."""
        for _ in range(int(n)):
            for a in self.eng.neighbours(self._farms[farm], "has_animal"):
                self.eng.set_attr(a, "season_armed", 1.0)
                self.eng.set_attr(a, "breed_armed", 1.0)
            self._run()

    def set_weather(self, factor):
        """The season's weather quality that scales the harvest (driven by bigville_weather)."""
        self.eng.set_attr(self._town, "weather_factor", float(factor)); self._run()

    def harvest(self, farm, field):
        self.eng.set_attr(self._fields[field], "ripe", 1.0)
        self.eng.set_attr(self._fields[field], "harvest_armed", 1.0)
        self._run()

    def slaughter(self, animal):
        self.eng.set_attr(self._animals[animal], "slaughter_armed", 1.0); self._run()

    def deliver_nightsoil(self, farm, qty):
        f = self._farms[farm]
        self.eng.set_attr(f, "manure", float(self.eng.node(f)["attrs"]["manure"]) + float(qty))

    def fertilize(self, field):
        self.eng.set_attr(self._fields[field], "fertilize_armed", 1.0); self._run()

    # ------------------------------------------------- glass-box read-offs
    def is_farm_on_map(self, name):
        p = self._farms[name]
        return self.eng.node(p)["type"] == "Place" and self.eng.node(p)["attrs"]["kind"] == "farm" \
            and self.eng.has_edge(self._town, "has_place", p)
    def worker_count(self, farm): return len(self.eng.in_neighbours(self._farms[farm], "works"))
    def food_out(self, farm): return round(float(self.eng.node(self._farms[farm])["attrs"]["food_out"]), 4)
    def meat(self, farm): return round(float(self.eng.node(self._farms[farm])["attrs"]["meat"]), 4)
    def manure(self, farm): return round(float(self.eng.node(self._farms[farm])["attrs"]["manure"]), 4)
    def last_yield(self, field): return round(float(self.eng.node(self._fields[field])["attrs"]["last_yield"]), 4)
    def fertility(self, field): return round(float(self.eng.node(self._fields[field])["attrs"]["fertility"]), 4)
    def animal_age(self, name): return round(float(self.eng.node(self._animals[name])["attrs"]["age"]), 4)
    def animal_weight(self, name): return round(float(self.eng.node(self._animals[name])["attrs"]["weight"]), 4)
    def is_alive(self, name): return float(self.eng.node(self._animals[name])["attrs"]["alive"]) == 1.0
    def herd_size(self, farm):
        return sum(1 for a in self.eng.neighbours(self._farms[farm], "has_animal")
                   if float(self.eng.node(a)["attrs"]["alive"]) == 1.0)
