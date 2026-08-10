"""BigvilleLegislatureWorld -- bigville R23 (block 310000): the council sets real
laws, and makes the routine decisions / statements / censures that get posted.

Two frequencies:
  * THE NORM -- issue_act(decision|statement|censure) -> posted to the noticeboard;
    a censure of a named person lowers their standing (ca_censure_effect).
  * THE RARE ACT -- propose_bill(enact|amend|repeal) -> councillors VOTE by bloc,
    it PASSES at a threshold and is APPLIED to the law-book, and laws have real
    effects (the land_tax law's value is what collect_tax() takes).

A WORLD ADAPTER. No legislative/vote/effect DECISION in Python -- all are the seed
rules (leg_*/ca_*/law_*). The adapter mints the council/law-book/bills/acts, ticks
the fixpoint, arms a tax collection, and reads state.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs                                              # noqa: E402
from substrate.seed_loader import manifest_for                   # noqa: E402


class BigvilleLegislatureWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_legislature"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._book = self.eng.add_node("LawBook", {})
        self.eng.add_edge_unchecked(self._town, "has_book", self._book)
        self._treasury = self.eng.add_node("Treasury", {"collected": 0.0, "collecting": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_treasury", self._treasury)
        self._laws = {}          # name -> Law nid
        self._people = {}        # name -> Resident/Councillor nid (has standing/coin)
        self._acts = []          # CouncilAct nids
        self._bills = []         # Bill nids

    # ------------------------------------------------------------------ ingest
    def add_law(self, name, value, *, status="active"):
        law = self.eng.add_node("Law", {"name": name, "value": float(value), "status": status})
        self.eng.add_edge_unchecked(self._book, "has_law", law)
        self._laws[name] = law
        return law

    def add_councillor(self, name, *, bloc):
        c = self.eng.add_node("Councillor", {"name": name, "bloc": bloc, "standing": 5.0})
        self.eng.add_edge_unchecked(self._town, "on_council", c)
        self._people[name] = c
        return c

    def add_resident(self, name, *, coin=20.0, standing=3.0):
        r = self.eng.add_node("Resident", {"name": name, "coin": float(coin),
                                            "standing": float(standing), "taxed": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", r)
        self._people[name] = r
        return r

    # ---- THE NORM: routine council acts (posted) --------------------------------
    def issue_act(self, kind, content, *, target=None):
        """decision | statement | censure -> a posted CouncilAct. A censure names a
        target (a person) and bites (lowers their standing)."""
        act = self.eng.add_node("CouncilAct", {"kind": kind, "content": content,
                                               "posted": 1.0, "applied": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_act", act)
        if target is not None:
            self.eng.add_edge_unchecked(act, "targets", self._people[target])
        self._acts.append(act)
        return act

    # ---- THE RARE ACT: a bill before the council --------------------------------
    def propose_bill(self, action, *, target, new_value=0.0, aids_bloc="poor", threshold=2):
        bill = self.eng.add_node("Bill", {"action": action, "target": target,
                                          "new_value": float(new_value),
                                          "aids_bloc": aids_bloc,
                                          "threshold": float(threshold),
                                          "votes_for": 0.0, "status": "pending"})
        self.eng.add_edge_unchecked(self._town, "has_bill", bill)
        self._bills.append(bill)
        return bill

    # ---------------------------------------------------------------- run
    def run(self):
        """Run the legislative + council-act fixpoint (votes -> pass -> apply;
        censure effect)."""
        self.eng.force_all_dirty()
        return self.eng.run_rules(1000000)

    def collect_tax(self):
        """Arm a tax collection: each resident pays the ACTIVE land_tax law's value
        (if any) into the treasury. Returns the amount collected this round."""
        before = self.treasury_collected()
        for p in self._people.values():
            self.eng.set_attr(p, "taxed", 0.0)
        self.eng.set_attr(self._treasury, "collecting", 1.0)
        self.run()
        self.eng.set_attr(self._treasury, "collecting", 0.0)
        return self.treasury_collected() - before

    # ------------------------------------------------- glass-box read-offs
    def law_value(self, name):
        return float(self.eng.node(self._laws[name])["attrs"]["value"]) if name in self._laws else None

    def law_status(self, name):
        # the law may have been enacted at runtime (not in self._laws) -> scan the book.
        for law in self.eng.neighbours(self._book, "has_law"):
            a = self.eng.node(law)["attrs"]
            if a.get("name") == name:
                return a.get("status"), float(a.get("value", 0.0))
        return None

    def law_book(self):
        out = {}
        for law in self.eng.neighbours(self._book, "has_law"):
            a = self.eng.node(law)["attrs"]
            out[a.get("name")] = (a.get("status"), round(float(a.get("value", 0.0)), 2))
        return out

    def treasury_collected(self):
        return float(self.eng.node(self._treasury)["attrs"]["collected"])

    def standing_of(self, name):
        return float(self.eng.node(self._people[name])["attrs"]["standing"])

    def bill_status(self, bill):
        return self.eng.node(bill)["attrs"]["status"]

    def posted_acts(self):
        out = []
        for act in self._acts:
            a = self.eng.node(act)["attrs"]
            if float(a.get("posted", 0.0)) == 1.0:
                out.append((a.get("kind"), a.get("content")))
        return out
