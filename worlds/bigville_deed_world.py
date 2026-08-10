"""BigvilleDeedWorld -- bigville R55 (block 366000): land ownership by deed, register, and bank.

Land ownership is what the Clerk's register records; the register is authoritative only insofar
as the clerk's office is recognized; the bank holds mortgaged deeds and forecloses on default.
The formal, institutional version of bigville's recognition thesis.

A WORLD ADAPTER. No record/transfer/foreclose DECISION in Python -- ld_* are seed rules. The
adapter mints the clerk/register/plots/deeds/bank, submits and transfers deeds, and reads.
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


class BigvilleDeedWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_deed"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._register = self.eng.add_node("Register", {"name": "the deed register"})
        self.eng.add_edge_unchecked(self._town, "has_register", self._register)
        self._clerk = None
        self._agents = {}
        self._deeds = {}          # plot -> deed node

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name):
        a = self.eng.add_node("Agent", {"name": name})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self._agents[name] = a
        return a

    def add_clerk(self, name="Clerk"):
        c = self.eng.add_node("Agent", {"name": name, "role": "clerk", "authority": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_clerk", c)
        self._agents[name] = c
        self._clerk = c
        return c

    def recognize_clerk(self, name):
        self.eng.add_edge_unchecked(self._agents.get(name) or self.add_agent(name), "recognizes", self._clerk)

    def add_bank(self, name="Bank"):
        b = self.eng.add_node("Bank", {"name": name})
        self._agents[name] = b
        return b

    def issue_deed(self, plot, owner):
        """A deed for `plot` is submitted to the register; the clerk records it (if recognized)."""
        if owner not in self._agents:
            self.add_agent(owner)
        d = self.eng.add_node("Deed", {"plot": plot, "owner": owner, "registered": 0.0,
                                       "transfer_to": "", "defaulted": 0.0, "foreclosed": 0.0})
        self.eng.add_edge_unchecked(d, "submitted_to", self._register)
        self._deeds[plot] = d
        self._run()
        return d

    def transfer(self, plot, to):
        """Sell/gift/bequeath the plot -- the clerk records the new owner."""
        if to not in self._agents:
            self.add_agent(to)
        self.eng.set_attr(self._deeds[plot], "transfer_to", to)
        self._run()

    def pledge_to_bank(self, plot, bank):
        self.eng.add_edge_unchecked(self._deeds[plot], "pledged_to", self._agents[bank])

    def default(self, plot):
        self.eng.set_attr(self._deeds[plot], "defaulted", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def is_registered(self, plot):
        return float(self.eng.node(self._deeds[plot])["attrs"].get("registered", 0.0)) == 1.0
    def owner_of(self, plot):
        """The RECOGNIZED owner: the register's recorded owner (None if the deed is not registered)."""
        d = self._deeds.get(plot)
        if d is None or not self.is_registered(plot):
            return None
        return self.eng.node(d)["attrs"]["owner"]
    def clerk_authority(self):
        return int(round(float(self.eng.node(self._clerk)["attrs"].get("authority", 0.0))))
