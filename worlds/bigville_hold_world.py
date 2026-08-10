"""BigvilleHoldWorld -- newspaper-writer Rung C (block 295000): the publisher HOLDS
what he is told or witnessed as a general belief.

WHAT THIS DEMONSTRATES (NEWSPAPER_WRITER_PLAN.md Rung C + BIGVILLE_HOLD_PREREG.md)
-------------------------------------------------------------------------------
After a reporter delivers a Fact (Rung B: the publisher `received` it), the
publisher INTEGRATES it into his held beliefs -- pub `knows` the Fact -- via a
RULE, with provenance (testimony). He also knows what he WITNESSED directly. The
held set is testimony-bound and anti-confabulation is STRUCTURAL: `knows` is
minted only from `received` or `witnessed_fact`, so a fact he was never given and
never saw is NOT known. Prose (Rung D) is then written from these held `knows`.

Built on BigvilleReportWorld (so the delivery is the real report+travel) + the
bigville_hold seed in the same substrate.

ARCHITECTURE-RULE COMPLIANCE
----------------------------
A WORLD ADAPTER. No decision about what the publisher believes -- that is the
hold rules reading `received` / `witnessed_fact`. The adapter mints facts, wires
the witnessed edge, ticks, and reads the held beliefs back.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                   # noqa: E402
from worlds.bigville_report_world import BigvilleReportWorld     # noqa: E402


class BigvilleHoldWorld(BigvilleReportWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.eng.load_seed_manifest(manifest_for("bigville_hold"), None)
        self._all_facts = {}          # desc -> Fact nid (every fact minted, for audit)

    # keep an index of every reporter fact too (for the audit read-offs)
    def add_reporter(self, name, cell, *, salience=1.0, desc=""):
        m = super().add_reporter(name, cell, salience=salience, desc=desc)
        self._all_facts[desc] = self._facts[name]
        return m

    # ------------------------------------------------------------------ ingest
    def add_witnessed_fact(self, desc, *, salience=1.0):
        """A Fact the publisher SAW directly (no reporter, no travel). He should
        come to know it by witness."""
        f = self.eng.add_node("Fact", {"salience": float(salience), "reported": 0.0,
                                        "desc": desc, "witnessed": 1.0})
        pub = self._movers[self._publisher]
        self.eng.add_edge_unchecked(pub, "witnessed_fact", f)
        self._all_facts[desc] = f
        return f

    def add_rumor(self, desc, *, salience=1.0):
        """A Fact that EXISTS in the world but was never delivered to the publisher
        and never witnessed by him -- the anti-confabulation control. He must NOT
        come to know it."""
        f = self.eng.add_node("Fact", {"salience": float(salience), "reported": 0.0,
                                        "desc": desc, "witnessed": 0.0})
        self._all_facts[desc] = f
        return f

    # ------------------------------------------------- glass-box read-offs
    def _knows_set(self):
        pub = self._movers[self._publisher]
        return set(self.eng.neighbours(pub, "knows"))

    def knows(self, desc):
        """Does the publisher HOLD a belief about the fact with this desc?"""
        f = self._all_facts.get(desc)
        return f is not None and f in self._knows_set()

    def known_facts(self):
        """The publisher's held beliefs: (desc, provenance) for each `knows` fact."""
        out = []
        for f in self._knows_set():
            a = self.eng.node(f)["attrs"]
            prov = ("witness" if a.get("provenance_witness") == 1.0
                    else ("testimony" if a.get("provenance_testimony") == 1.0 else "?"))
            out.append((a.get("desc", ""), prov))
        return sorted(out)

    def held_equals_told_union_witnessed(self):
        """Anti-confabulation audit: is the held `knows` set EXACTLY the facts that
        were delivered (received) OR witnessed -- with no extra fact?"""
        pub = self._movers[self._publisher]
        received = set(self.eng.neighbours(pub, "received"))
        witnessed = set(self.eng.neighbours(pub, "witnessed_fact"))
        return self._knows_set() == (received | witnessed)
