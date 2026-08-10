"""BigvilleWasteWorld -- bigville R51 (block 362000): where does rubbish go?

Rubbish does not vanish. Living and working produce refuse that accumulates where it is made;
unmanaged, it is a health hazard; a raker carts it to the town tip (a midden -- moved, not
destroyed); dumping it in the river relocates it as pollution. Conservation at the waste end.

A WORLD ADAPTER. No produce/hazard/collect/dump DECISION in Python -- wa_* are seed rules.
The adapter mints places/tip/river/raker, passes days, arms collection/dumping, and reads.
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


class BigvilleWasteWorld:
    def __init__(self, *, hazard_threshold=5.0):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_waste"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "hazard_threshold": float(hazard_threshold)})
        self._tip = self.eng.add_node("Tip", {"name": "the midden", "refuse": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_tip", self._tip)
        self._river = self.eng.add_node("River", {"name": "the river", "pollution": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_river", self._river)
        self._raker = None
        self._places = {}

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_place(self, name, *, occupants=4.0, waste_rate=0.5):
        p = self.eng.add_node("Place", {"name": name, "occupants": float(occupants),
                                        "waste_rate": float(waste_rate), "refuse": 0.0,
                                        "produce_armed": 0.0, "dump_armed": 0.0, "hazard": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_place", p)
        self._places[name] = p
        return p

    def appoint_raker(self, name="Raker"):
        """The raker/scavenger -- an appointed sanitation office (see bigville_office)."""
        r = self.eng.add_node("Agent", {"name": name, "role": "raker", "collect_armed": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_raker", r)
        self._raker = r
        return r

    def live_a_day(self, n=1):
        """Days pass -- every place produces refuse from its occupants."""
        for _ in range(int(n)):
            for p in self._places.values():
                self.eng.set_attr(p, "produce_armed", 1.0)
            self._run()

    def collect(self):
        """The raker makes his round -- carts every place's refuse to the tip."""
        if self._raker is None:
            self._run(); return
        self.eng.set_attr(self._raker, "collect_armed", 1.0)
        self._run()
        self.eng.set_attr(self._raker, "collect_armed", 0.0)

    def dump(self, place):
        """A place dumps its refuse in the river (pollution)."""
        self.eng.set_attr(self._places[place], "dump_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def place_refuse(self, name): return round(float(self.eng.node(self._places[name])["attrs"]["refuse"]), 4)
    def is_hazard(self, name): return float(self.eng.node(self._places[name])["attrs"]["hazard"]) == 1.0
    def tip_refuse(self): return round(float(self.eng.node(self._tip)["attrs"]["refuse"]), 4)
    def river_pollution(self): return round(float(self.eng.node(self._river)["attrs"]["pollution"]), 4)
    def total_waste(self):
        return round(sum(self.place_refuse(n) for n in self._places) + self.tip_refuse() + self.river_pollution(), 4)
