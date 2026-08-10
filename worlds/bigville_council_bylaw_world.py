"""BigvilleCouncilBylawWorld -- bigville R32 (block 322000): the council's meeting
schedule is a bylaw, enacted by the beadle, on bell time.

The meeting interval is a Law the council holds (and amends through its own
legislature). The beadle counts the passing days by the curfew bell and rings the
assembly bell when the bylaw says a meeting is due; the council convenes on the
assembly bell. No now_day % cadence integer math.

A WORLD ADAPTER. No count/ring/convene DECISION in Python -- cb_* are seed rules.
The adapter only tolls the curfew bell (via the sexton) and reads state.
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


class BigvilleCouncilBylawWorld(BigvilleLegislatureWorld):
    def __init__(self):
        super().__init__()                                    # town, LawBook, treasury, legislature
        self.eng.load_seed_manifest(manifest_for("bigville_bells"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_council_bylaw"), None)
        self._church = self.eng.add_node("Church", {"name": "Bigville Church"})
        self.eng.add_edge_unchecked(self._town, "has_church", self._church)
        self._bell = self.eng.add_node("Bell", {"ring_armed": 0.0, "toll_hour": 0.0,
                                                "toll_kind": "", "call_strength": 1.0})
        self.eng.add_edge_unchecked(self._church, "has_bell", self._bell)
        self._beadle = self.eng.add_node("Beadle", {"name": "beadle", "days_since_meeting": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_beadle", self._beadle)

    # ------------------------------------------------------------------ ingest
    def set_meeting_bylaw(self, interval):
        """The council's meeting interval, held as a Law in the book (a bylaw)."""
        return self.add_law("council_meeting_interval", float(interval))

    def _settle(self):
        for _ in range(6):                                    # curfew -> count -> [ring assembly -> convene]
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    def toll_curfew(self):
        """The sexton tolls the curfew bell -- one day passes. The beadle counts it; if
        the bylaw says a meeting is due, the beadle rings the assembly bell and the
        council convenes."""
        self.eng.set_attr(self._bell, "toll_kind", "curfew")
        self.eng.set_attr(self._bell, "ring_armed", 1.0)
        self._settle()

    def amend_meeting_bylaw(self, new_value, *, aids_bloc="poor", threshold=2):
        """The council amends its own meeting interval, through its legislature."""
        bill = self.propose_bill("amend", target="council_meeting_interval",
                                 new_value=float(new_value), aids_bloc=aids_bloc, threshold=threshold)
        self.run()
        return bill

    # ------------------------------------------------- glass-box read-offs
    def days_since_meeting(self):
        return int(self.eng.node(self._beadle)["attrs"].get("days_since_meeting", 0.0))

    def meeting_interval(self):
        return int(self.law_value("council_meeting_interval"))

    def meetings_convened(self):
        return len(self.eng.neighbours(self._town, "has_meeting"))
