"""BigvilleJailWorld -- bigville R26 (block 314000): custodial sentences.

Extends BigvilleCourtWorld with a real jail. A guilty charge that prescribes a
jail_term imprisons the defendant (held, removed from circulation) for that term;
the term counts down as days advance; the inmate is released when it expires. The
fine (ct_sentence) still applies -- custody and fine are independent consequences.

A WORLD ADAPTER. No imprison/serve/release DECISION in Python -- jl_* are seed
rules. The adapter mints the jail, sets the prescribed term, arms the day-advance,
and reads state.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for                # noqa: E402
from worlds.bigville_court_world import BigvilleCourtWorld     # noqa: E402


class BigvilleJailWorld(BigvilleCourtWorld):
    def __init__(self):
        super().__init__()
        self.eng.load_seed_manifest(manifest_for("bigville_bells"), None)   # the town clock
        self.eng.load_seed_manifest(manifest_for("bigville_jail"), None)
        self._jail = self.eng.add_node("Jail", {"name": "Bigville Gaol"})
        self.eng.add_edge_unchecked(self._town, "has_jail", self._jail)
        # the church bell tolls the day -- there is no forced day counter.
        self._church = self.eng.add_node("Church", {"name": "Bigville Church"})
        self.eng.add_edge_unchecked(self._town, "has_church", self._church)
        self._bell = self.eng.add_node("Bell", {"ring_armed": 0.0, "toll_hour": 0.0,
                                                "toll_kind": "", "call_strength": 1.0})
        self.eng.add_edge_unchecked(self._church, "has_bell", self._bell)

    # ------------------------------------------------------------------ ingest
    def prosecute(self, defendant, offence, *, evidence, penalty=5.0,
                  standing_penalty=1.0, threshold=2, jail_term=0.0):
        """As the court, plus a prescribed custodial term (days). jail_term=0 -> a
        fine-only charge (no imprisonment)."""
        charge = super().prosecute(defendant, offence, evidence=evidence, penalty=penalty,
                                   standing_penalty=standing_penalty, threshold=threshold)
        self.eng.set_attr(charge, "jail_term", float(jail_term))
        return charge

    def toll_curfew(self):
        """The curfew bell tolls the day: every inmate with time left serves a day, and
        the released walk free. The day turns because the BELL marks it -- no forced
        day counter. (advance_day is kept as an alias for the existing interface.)"""
        self.eng.set_attr(self._bell, "toll_kind", "curfew")
        self.eng.set_attr(self._bell, "ring_armed", 1.0)
        for _ in range(4):                      # settle ring -> serve -> release
            self.run()

    advance_day = toll_curfew

    # ------------------------------------------------- glass-box read-offs
    def is_imprisoned(self, name):
        return float(self.eng.node(self._people[name])["attrs"].get("imprisoned", 0.0)) == 1.0

    def remaining(self, name):
        return int(self.eng.node(self._people[name])["attrs"].get("sentence_remaining", 0.0))

    def jail_roll(self):
        """Who is currently held (by name)."""
        return sorted(self.eng.node(d)["attrs"].get("name")
                      for d in self.eng.neighbours(self._jail, "holds_inmate"))
