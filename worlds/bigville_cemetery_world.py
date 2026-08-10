"""BigvilleCemeteryWorld -- bigville R53 (block 364000): the churchyard, funerals, the pauper's
grave.

The cemetery is at the church; the church holds funerals the estate pays for; an estate that
cannot pay gets a pauper's grave; with no undertaker the body lies unburied (a hazard). In a
small town the undertaker is also the doctor -- one person, two roles (a plural office).

A WORLD ADAPTER. No funeral/bury DECISION in Python -- cy_* are seed rules. The adapter mints
the church/cemetery/undertaker/residents, records deaths, and reads.
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


class BigvilleCemeteryWorld:
    def __init__(self, *, funeral_fee=5.0):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_cemetery"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._church = self.eng.add_node("Church", {"name": "Bigville Church", "funeral_fee": float(funeral_fee),
                                                    "coin": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_church", self._church)
        self._cem = self.eng.add_node("Cemetery", {"name": "the churchyard", "graves": 0.0})
        self.eng.add_edge_unchecked(self._church, "has_cemetery", self._cem)   # the cemetery is AT the church
        self._agents = {}
        self._undertaker = None

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_resident(self, name, *, estate=0.0, alive=1):
        a = self.eng.add_node("Agent", {"name": name, "estate": float(estate), "alive": float(alive),
                                        "buried": 0.0, "unburied": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self._agents[name] = a
        return a

    def appoint_doctor_undertaker(self, name):
        """A SMALL-TOWN plural office: one person is BOTH the doctor AND the undertaker."""
        a = self._agents.get(name) or self.add_resident(name, estate=20.0)
        self.eng.set_attr(a, "role", "doctor_undertaker")
        self.eng.add_edge_unchecked(self._town, "has_doctor", a)
        self.eng.add_edge_unchecked(self._town, "has_undertaker", a)
        self._undertaker = name
        return a

    def appoint_doctor_only(self, name):
        """A doctor who is NOT the undertaker (the town lacks anyone to bury the dead)."""
        a = self._agents.get(name) or self.add_resident(name, estate=20.0)
        self.eng.add_edge_unchecked(self._town, "has_doctor", a)
        return a

    def die(self, name):
        self.eng.set_attr(self._agents[name], "alive", 0.0); self._run()

    # ------------------------------------------------- glass-box read-offs
    def _a(self, name, k): return self.eng.node(self._agents[name])["attrs"].get(k)
    def is_buried(self, name): return float(self._a(name, "buried") or 0.0) == 1.0
    def is_unburied(self, name): return float(self._a(name, "unburied") or 0.0) == 1.0
    def estate(self, name): return round(float(self._a(name, "estate") or 0.0), 4)
    def church_coin(self): return round(float(self.eng.node(self._church)["attrs"]["coin"]), 4)
    def grave_count(self): return int(round(float(self.eng.node(self._cem)["attrs"]["graves"])))
    def has_role(self, name, *roles):
        return all(self.eng.has_edge(self._town, f"has_{r}", self._agents[name]) for r in roles)
    def in_paupers_grave(self, name):
        for g in self.eng.in_neighbours(self._agents[name], "holds"):
            return float(self.eng.node(g)["attrs"].get("pauper", 0.0)) == 1.0
        return False
