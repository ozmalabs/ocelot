"""BigvillePublisherWorld -- newspaper-writer Rung A (block 293000): the PORTABLE
gather-and-publish role.

WHAT THIS DEMONSTRATES (NEWSPAPER_WRITER_PLAN.md Rung A + BIGVILLE_PUBLISHER_ROLE_PREREG.md)
------------------------------------------------------------------------------------------
The newspaper is not a subsystem; the reporter is not a special node picked in
Python. The "gather information and write" role is a GENERAL, held, PORTABLE
thing: a Resident who `affords` a `makes_known` Affordance is the town's writer.
The town's Paper finds its writer by a RULE (whoever affords makes_known), and
the writer FOLLOWS the affordance -- move the `affords` edge and the paper's
`employs` edge moves with it. The role also bundles the general gather goal
`Goal{kind:know}`.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It edits no tracked file and holds NO decision about WHO the
publisher is -- that is the seed rule reading the affordance. This adapter only:
build the town/paper/residents (ingest), MOVE the `affords` edge when asked
(mechanical -- the caller says which resident to hand the affordance to, exactly
as a world hands an agent an object), run the Rust fixpoint, and read `employs`
and the gather goal back out. There is NO role-string / name test selecting the
writer (source-audit gate). `set_publisher(name)` is the mechanical
give-the-affordance-to-this-resident I/O, not a decision about who SHOULD write.
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


class BigvillePublisherWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_publisher_role"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._paper = self.eng.add_node("Paper", {"name": "The Bigville Times"})
        self.eng.add_edge_unchecked(self._town, "has_paper", self._paper)
        # ONE shared makes_known Affordance the town offers; whichever resident
        # `affords` it is the publisher (Gibsonian: affords making-things-known).
        self._makes_known = self.eng.add_node("Affordance", {"name": "makes_known"})
        self._residents = {}          # name -> Resident nid

    # ------------------------------------------------------------------ ingest
    def add_resident(self, name):
        """Register a townsperson. Mechanical -- no role assigned here."""
        res = self.eng.add_node("Resident", {"name": name})
        self.eng.add_edge_unchecked(self._town, "has_resident", res)
        self._residents[name] = res
        return res

    def set_publisher(self, name):
        """Hand the makes_known affordance to resident `name` (and take it from
        whoever held it). Mechanical give-the-affordance I/O -- the DECISION that
        this makes them the writer, and that the paper should employ them, is the
        seed rule, not this method. Pass name=None to remove the affordance from
        the town entirely (ablate the publisher)."""
        for other in self._residents.values():           # single-holder: clear first
            self.eng.remove_edge_unchecked(other, "affords", self._makes_known)
        if name is not None:
            self.eng.add_edge_unchecked(self._residents[name], "affords", self._makes_known)

    def add_publisher(self, name):
        """Hand the makes_known affordance to `name` WITHOUT taking it from others
        (used to show two afforders -> two employees; nothing hardcodes a single
        reporter)."""
        self.eng.add_edge_unchecked(self._residents[name], "affords", self._makes_known)

    # ---------------------------------------------------------------- rule step
    def run(self):
        """Run the publisher-role rules to a fixpoint. All decisions are rules.
        `force_all_dirty` first because the affordance is moved with the
        `*_unchecked` edge ops (which bypass dirty-tracking) -- a mechanical
        'the world changed, re-evaluate' step, exactly like the move world
        touching an attr to wake its rules. Correctness only; this demonstrator
        is tiny so the full re-scan is free."""
        self.eng.force_all_dirty()
        return self.eng.run_rules(1000000)

    # ------------------------------------------------- glass-box read-offs
    def publisher(self):
        """The name(s) the Paper currently EMPLOYS -- read off the graph, the rule's
        verdict. A list (usually one; can be several before a lead is chosen)."""
        out = []
        for res in self.eng.neighbours(self._paper, "employs"):
            out.append(self.eng.node(res)["attrs"].get("name"))
        return sorted(out)

    def holds_gather_goal(self, name):
        """Does resident `name` hold a general Goal{kind:know}? (the role's goal)."""
        res = self._residents[name]
        for g in self.eng.neighbours(res, "pursues"):
            if self.eng.node(g)["attrs"].get("kind") == "know":
                return True
        return False

    def close(self):
        self._residents.clear()
