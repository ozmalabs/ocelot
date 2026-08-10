"""BigvilleCommodityPhysicalWorld -- bigville R70 (block 387000): a pile is just a pile.

A commodity pile is a world-fact -- located matter, conserved -- with NO intrinsic owner. Physical
acts (burn, consume) work by ACCESS (co-location). OWNERSHIP is a human frame people add: a Claim on
a pile becomes ownership only when others RECOGNIZE it. A pile can be ownerless, contested, or its
claim unrecognized.

A WORLD ADAPTER: cp_burn/cp_consume/cp_owner are seed rules; the adapter mints the yard, piles (at
the yard), agents (at the yard), claims and recognitions, arms acts, and reads. owner_of is a
mechanical read of the recognized frame off the graph -- the pile stores no owner.
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


class BigvilleCommodityPhysicalWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_commodity_physical"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._yard = self.eng.add_node("Place", {"name": "the yard"})
        self.eng.add_edge_unchecked(self._town, "has_place", self._yard)
        self._agents = {}
        self._piles = {}
        self._claims = {}

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    def add_agent(self, name):
        a = self.eng.add_node("Agent", {"name": name, "burn_armed": 0.0, "wood_in": 0.0,
                                        "fire_armed": 0.0, "charcoal_in": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self.eng.add_edge_unchecked(a, "at", self._yard)     # AT the yard -> access
        self._agents[name] = a
        return a

    def add_pile(self, kind, qty=0.0):
        """A physical pile: located matter in the yard. NOT owned -- a pile is just a pile."""
        p = self.eng.add_node("Pile", {"kind": kind, "qty": float(qty)})
        self.eng.add_edge_unchecked(p, "at", self._yard)     # LOCATED (world-fact); no owner
        self._piles[kind] = p
        return p

    # ------------------------------------------------- ownership is a human frame, added on
    def claim(self, claimant, kind):
        """A person ADDS an ownership claim to a pile (claimant -claims-> Claim -on-> pile)."""
        c = self.eng.add_node("Claim", {"claimant": claimant, "recognized": 0.0, "recognizers": 0.0})
        self.eng.add_edge_unchecked(self._agents[claimant], "claims", c)
        self.eng.add_edge_unchecked(c, "on", self._piles[kind])
        self._claims[(claimant, kind)] = c
        self._run()
        return c

    def recognize(self, recognizer, claimant, kind):
        """Another agent RECOGNIZES a claim -- that is what makes it ownership."""
        self.eng.add_edge_unchecked(self._agents[recognizer], "recognizes", self._claims[(claimant, kind)])
        self._run()

    # ------------------------------------------------- acts (by access)
    def burn(self, agent, wood_in):
        self.eng.set_attr(self._agents[agent], "wood_in", float(wood_in))
        self.eng.set_attr(self._agents[agent], "burn_armed", 1.0); self._run()

    def fire_forge(self, agent, charcoal_in):
        self.eng.set_attr(self._agents[agent], "charcoal_in", float(charcoal_in))
        self.eng.set_attr(self._agents[agent], "fire_armed", 1.0); self._run()

    # ------------------------------------------------- glass-box read-offs
    def qty(self, kind): return round(float(self.eng.node(self._piles[kind])["attrs"]["qty"]), 4)
    def total_mass(self): return round(sum(self.qty(k) for k in self._piles), 4)
    def has_owner_attr(self, kind): return "owner" in self.eng.node(self._piles[kind])["attrs"]

    def owner_of(self, kind):
        """Read the recognized owner off the graph -- the claimant of the most-recognized RECOGNIZED
        claim on the pile. None if the pile is ownerless (no recognized claim). The pile stores nothing."""
        pile = self._piles[kind]
        best, best_n = None, 0
        for c in self.eng.in_neighbours(pile, "on"):
            a = self.eng.node(c)["attrs"]
            if float(a.get("recognized", 0.0)) == 1.0 and float(a.get("recognizers", 0.0)) > best_n:
                best, best_n = a["claimant"], float(a["recognizers"])
        return best

    def claim_recognized(self, claimant, kind):
        return float(self.eng.node(self._claims[(claimant, kind)])["attrs"].get("recognized", 0.0)) == 1.0
