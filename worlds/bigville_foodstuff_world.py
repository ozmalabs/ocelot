"""BigvilleFoodstuffWorld -- bigville R42 (block 333000): the food lifecycle.

Discrete FoodItems (integer portions) stored in a larder, spoiling at kind-specific rates
(slowed by cold), prepared raw->cooked by a kitchen (some foods inedible raw), consumed one
portion at a time.

A WORLD ADAPTER. No spoil/rot/prepare/eat/reject DECISION in Python -- fs_* are seed rules.
The adapter mints items with their physical properties, pulses time, arms prep/eating, reads.
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

# codebook: (energy, taste, spoil_rate per epoch, needs_prep, prep_bonus)
_FOODS = {
    "fish":      (3.0, 0.4, 0.30, 0.0, 0.3),   # spoils fast, edible raw
    "grain":     (4.0, 0.1, 0.05, 1.0, 0.3),   # slow, INEDIBLE until baked
    "salt_fish": (3.0, 0.3, 0.02, 0.0, 0.2),   # preserved -- barely spoils
    "ale":       (2.0, 0.5, 0.03, 0.0, 0.0),   # keeps well
}


class BigvilleFoodstuffWorld:
    def __init__(self, *, cold=False, capacity=100.0, cold_factor=0.4, fuel=10.0, cook_cost=1.0):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_foodstuff"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "epoch": 0.0})
        self._larder = self.eng.add_node("Larder", {"cold": 1.0 if cold else 0.0,
                                                    "capacity": float(capacity),
                                                    "cold_factor": float(cold_factor)})
        self.eng.add_edge_unchecked(self._town, "has_larder", self._larder)
        self._items = []
        self._cooks = {}
        self._cook_station = {}
        self._preparing_wired = set()
        self._households = {}
        self._eaters = {}
        self._eaten_wired = set()
        # Preparation needs an AGENT, not a kitchen. Stations are OPTIONAL surfaces:
        # bare hands / the ground (no heat, no bonus) is always available; a hearth (fire)
        # or stove adds heat (needed only to COOK) and prep_power. Seasoning needs neither.
        self._stations = {}
        self.add_station("hands", heat=0.0, prep_power=0.0)                 # the ground / bare hands
        self.add_station("hearth", heat=1.0, prep_power=0.5,
                         fuel=float(fuel), fuel_cost=float(cook_cost))       # a communal fire

    def add_station(self, name, *, heat=0.0, prep_power=0.5, fuel=0.0, fuel_cost=1.0):
        """A STATION food can be prepared on: bare hands / ground (heat 0), a bench (heat 0,
        some prep_power), a fire or stove (heat>=1, burns fuel). A station is optional --
        cooking needs heat, seasoning needs nothing."""
        st = self.eng.add_node("Station", {"name": name, "heat": float(heat),
                                           "prep_power": float(prep_power), "fuel": float(fuel),
                                           "fuel_cost": float(fuel_cost)})
        self.eng.add_edge_unchecked(self._town, "has_station", st)
        self._stations[name] = st
        return st

    def add_eater(self, name, *, raw_penalty=0.15, spoiled_disgust=0.6,
                  rot_illness=0.5, raw_illness=0.3):
        """An EATER -- the agent a meal is graded against. Its 'hardiness' params
        (how badly raw/spoiled food treats it) are per-agent, so a hardy stomach
        differs from a delicate one. Illness accrues on the eater, cumulatively."""
        e = self.eng.add_node("Agent", {"name": name, "raw_penalty": float(raw_penalty),
                                        "spoiled_disgust": float(spoiled_disgust),
                                        "rot_illness": float(rot_illness), "raw_illness": float(raw_illness),
                                        "illness": 0.0, "last_nutrition": 0.0,
                                        "last_pleasantness": 0.0, "last_ate": 0.0})
        self._eaters[name] = e
        return e

    def add_cook(self, name, *, cook_skill=0.7, energy=10.0, cook_effort=1.0, learn_rate=0.05,
                 station="hearth"):
        """A COOK -- an agent who prepares food, with a cooking skill. Preparation needs the
        AGENT (not a kitchen); the agent works at a station (default a hearth so cooking works
        out of the box; pass 'hands' to prepare on the ground)."""
        c = self.eng.add_node("Agent", {"name": name, "cook_skill": float(cook_skill),
                                        "energy": float(energy), "cook_effort": float(cook_effort),
                                        "learn_rate": float(learn_rate)})
        self.eng.add_edge_unchecked(c, "using", self._stations[station])
        self._cooks[name] = c
        self._cook_station[name] = station
        return c

    def _set_station(self, cook, station):
        """Move the cook to a different station (one 'using' edge at a time)."""
        old = self._cook_station[cook]
        if old != station:
            self.eng.remove_edge_unchecked(self._cooks[cook], "using", self._stations[old])
            self.eng.add_edge_unchecked(self._cooks[cook], "using", self._stations[station])
            self._cook_station[cook] = station

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_item(self, kind, *, portions=3, freshness=1.0, state="raw"):
        e, t, sr, np_, pb = _FOODS[kind]
        it = self.eng.add_node("FoodItem", {"kind": kind, "state": state, "freshness": float(freshness),
                                            "portions": float(int(portions)), "energy": e, "taste": t,
                                            "spoil_rate": sr, "needs_prep": np_, "prep_bonus": pb,
                                            "prep_armed": 0.0, "prep_kind": "cook", "eat_armed": 0.0,
                                            "seen_epoch": 0.0})
        self.eng.add_edge_unchecked(self._larder, "has_item", it)
        self._items.append(it)
        return len(self._items) - 1

    # ---- agent-chosen quantization: a household splits its food among members ----
    def add_household(self, name, *, members, food, shares=None):
        """A household DIVIDES its food among its members. `shares` is the household's chosen
        split (defaults to members = equal division); it can re-quantize by changing it."""
        hh = self.eng.add_node("Household", {"name": name, "members": float(members),
                                             "food": float(food),
                                             "shares": float(shares if shares is not None else members),
                                             "per_member": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_household", hh)
        self._households[name] = hh
        self._run()
        return hh

    def requantize(self, name, shares):
        """The household re-quantizes: choose a new number of ways to split the food."""
        self.eng.set_attr(self._households[name], "shares", float(shares))
        self._run()

    def set_food(self, name, food):
        self.eng.set_attr(self._households[name], "food", float(food))
        self._run()

    def per_member(self, name):
        return round(float(self.eng.node(self._households[name])["attrs"]["per_member"]), 4)

    def tick(self, n=1):
        for _ in range(n):
            self.eng.set_attr(self._town, "epoch", float(self.eng.node(self._town)["attrs"]["epoch"]) + 1.0)
            self._run()

    def prepare(self, idx, by="Cook", *, kind="cook", station=None):
        """An AGENT prepares the item -- 'cook' (needs a heat station) or 'season' (add spices,
        needs nothing). Wires agent -preparing-> item once; sets the agent's station if given."""
        if by not in self._cooks:
            self.add_cook(by)
        if station is not None:
            self._set_station(by, station)
        key = (by, idx)
        if key not in self._preparing_wired:
            self.eng.add_edge_unchecked(self._cooks[by], "preparing", self._items[idx])
            self._preparing_wired.add(key)
        self.eng.set_attr(self._items[idx], "prep_kind", kind)
        self.eng.set_attr(self._items[idx], "prep_armed", 1.0)
        self._run()

    def season(self, idx, by="Cook", *, station="hands"):
        """Seasoning is preparation too -- add spices, anywhere (no heat needed)."""
        self.prepare(idx, by, kind="season", station=station)

    def eat(self, idx, eater="Diner"):
        """An eater consumes one portion. Spoiled/raw food is NOT rejected -- it is
        eaten and GRADED (poor nutrition, unpleasant, illness). Only an empty stock
        yields nothing. The eaten_by edge is wired exactly once per (item, eater)."""
        if eater not in self._eaters:
            self.add_eater(eater)
        key = (idx, eater)
        if key not in self._eaten_wired:
            self.eng.add_edge_unchecked(self._items[idx], "eaten_by", self._eaters[eater])
            self._eaten_wired.add(key)
        self.eng.set_attr(self._items[idx], "eat_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def _i(self, idx, k): return self.eng.node(self._items[idx])["attrs"].get(k)
    def freshness(self, idx): return round(float(self._i(idx, "freshness")), 4)
    def state(self, idx): return self._i(idx, "state")
    def portions(self, idx): return int(float(self._i(idx, "portions")))
    def taste(self, idx): return round(float(self._i(idx, "taste")), 4)
    def prep_style(self, idx): return self._i(idx, "prep_style")
    def station_fuel(self, name="hearth"): return round(float(self.eng.node(self._stations[name])["attrs"]["fuel"]), 4)

    # the meal is graded against the EATER (spoiled food is eaten, not rejected)
    def _e(self, name, k): return round(float(self.eng.node(self._eaters[name])["attrs"].get(k, 0.0)), 4)
    def nutrition(self, name="Diner"): return self._e(name, "last_nutrition")
    def pleasantness(self, name="Diner"): return self._e(name, "last_pleasantness")
    def illness(self, name="Diner"): return self._e(name, "illness")
    def did_eat(self, name="Diner"): return self._e(name, "last_ate") == 1.0
