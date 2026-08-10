"""BigvilleCourtWorld -- bigville R24 v2 (block 313000): the council sits as court,
REWIRED onto the generic decision-by-collapse (agent_judgment).

Supersedes v1's evidence>=bar threshold (the user's correction: the councillor
CHOOSES; the verdict is the agent's OWN collapse, not a comparator). The Constable
files a Charge that IS a Matter (weight = evidence, -about_subject-> the defendant);
every councillor is a governed agent that -considers-> it, so jc_conclude fires and
each councillor collapses the charge against its OWN dispositions into its own
conclusion. Councillors DIVERGE. The court aggregates: guilty iff the condemning
councillors reach the charge's threshold, else acquitted; a guilty verdict fines
the defendant into the same Treasury the land_tax feeds, plus a standing hit.

A WORLD ADAPTER. No verdict/sentence DECISION in Python -- the collapse is
jc_conclude (agent_judgment) and the aggregation is ct_* (bigville_court). The
adapter mints the constable/charge, wires who-considers-what, ticks, and reads.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for                        # noqa: E402
from worlds.bigville_legislature_world import BigvilleLegislatureWorld  # noqa: E402

# The seeded stance candidates the councillors collapse over (agent_judgment).
_STANCES = [("denounce", 2.0), ("condemn", 1.0), ("doubt", -1.0), ("exonerate", -2.0)]


class BigvilleCourtWorld(BigvilleLegislatureWorld):
    def __init__(self):
        super().__init__()                                        # town, book, treasury, legislature
        self.eng.load_seed_manifest(manifest_for("agent_judgment"), None)  # the collapse
        self.eng.load_seed_manifest(manifest_for("bigville_court"), None)  # the court aggregation
        for label, pole in _STANCES:
            self.eng.add_node("Stance", {"label": label, "pole": pole})
        self._constable = None
        self._charges = []

    # ------------------------------------------------------------------ ingest
    def add_councillor(self, name, *, bloc, credence=1.0, punitiveness=0.0, deference=0.3):
        """A councillor is a governed agent (so it collapses on charges) AND on the
        council (so it legislates). Its dispositions are the held params the verdict
        collapse reads: credence (how much evidence moves it), punitiveness (baseline
        lean; negative = lenient), deference (how much it defers to the defendant's
        standing)."""
        c = super().add_councillor(name, bloc=bloc)
        self.eng.set_attr(c, "credence", float(credence))
        self.eng.set_attr(c, "punitiveness", float(punitiveness))
        self.eng.set_attr(c, "deference", float(deference))
        self.eng.add_edge_unchecked(self._town, "governs", c)     # a governed agent
        return c

    def add_constable(self, name):
        con = self.eng.add_node("Constable", {"name": name})
        self.eng.add_edge_unchecked(self._town, "has_constable", con)
        self._constable = con
        self._people[name] = con
        return con

    def prosecute(self, defendant, offence, *, evidence, penalty=5.0,
                  standing_penalty=1.0, threshold=2):
        """The Constable files a Charge (a Matter: weight = evidence). Every
        councillor considers it. Returns the Charge node."""
        charge = self.eng.add_node("Charge", {
            "offence": offence, "weight": float(evidence), "penalty": float(penalty),
            "standing_penalty": float(standing_penalty), "threshold": float(threshold),
            "convict_votes": 0.0, "status": "filed"})
        self.eng.add_edge_unchecked(self._town, "has_charge", charge)
        self.eng.add_edge_unchecked(charge, "about_subject", self._people[defendant])
        if self._constable is not None:
            self.eng.add_edge_unchecked(charge, "filed_by", self._constable)
        for c in self.eng.neighbours(self._town, "on_council"):
            self.eng.add_edge_unchecked(c, "considers", charge)
        self._charges.append(charge)
        return charge

    # ------------------------------------------------- glass-box read-offs
    def verdict(self, charge):
        return self.eng.node(charge)["attrs"]["status"]

    def convict_votes(self, charge):
        return int(self.eng.node(charge)["attrs"].get("convict_votes", 0.0))

    def coin_of(self, name):
        return float(self.eng.node(self._people[name])["attrs"]["coin"])

    def councillor_conclusions(self, charge):
        """Each councillor's own verdict on the charge (the divergent collapse)."""
        out = {}
        for c in self.eng.neighbours(self._town, "on_council"):
            nm = self.eng.node(c)["attrs"].get("name")
            for concl in self.eng.neighbours(c, "holds_conclusion"):
                if charge in self.eng.neighbours(concl, "about"):
                    out[nm] = self.eng.node(concl)["attrs"].get("verdict")
        return out

    def docket(self):
        out = []
        for ch in self._charges:
            a = self.eng.node(ch)["attrs"]
            out.append((a.get("offence"), a.get("status"), int(a.get("convict_votes", 0.0))))
        return out
