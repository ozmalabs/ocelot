"""BigvilleBellWorld -- bigville R31 (block 320000): the church bells are the clock.

There is no forced global clock. The sexton rings the bell (the one exogenous act);
the peal is heard across town; each resident learns the hour FROM the bell and
CHOOSES whether to answer. A rested sleeper wakes; an exhausted one sleeps through
and never learns the time.

A WORLD ADAPTER. No hear/wake/decide DECISION in Python -- bl_* are seed rules, the
answer is an Argmax collapse in the seed. The adapter only pulls the bell-rope
(arms one ring) and reads state. There is NO `now`/day counter driving the agents.
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

_CHOICES = [("go", 1.0), ("stay", -1.0)]


class BigvilleBellWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_bells"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})   # NO `now`/`sunday` on it
        self._church = self.eng.add_node("Church", {"name": "Bigville Church"})
        self.eng.add_edge_unchecked(self._town, "has_church", self._church)
        self._bell = self.eng.add_node("Bell", {"ring_armed": 0.0, "toll_hour": 0.0,
                                                "toll_kind": "", "call_strength": 1.0})
        self.eng.add_edge_unchecked(self._church, "has_bell", self._bell)
        for label, sign in _CHOICES:
            self.eng.add_node("ChurchChoice", {"label": label, "attend_sign": sign})
        self._residents = {}
        self._seen_peals = set()
        self._last_peal = None

    # ------------------------------------------------------------------ ingest
    def add_resident(self, name, *, piety=0.5, worldly_pull=0.3, rest=1.0, asleep=0):
        """rest: how rested (a rested sleeper wakes at the bell); asleep: 1 if abed.
        No `known_hour` is set -- a resident learns the time only by hearing a bell."""
        r = self.eng.add_node("Resident", {"name": name, "piety": float(piety),
                                           "worldly_pull": float(worldly_pull),
                                           "rest": float(rest), "asleep": float(asleep),
                                           "church_choice": "", "woke_at_bell": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", r)
        self._residents[name] = r
        return r

    def ring_bell(self, hour, *, kind="service", call_strength=1.0):
        """The sexton pulls the rope -- the town's ONE time signal. Everything else is
        the residents perceiving it and choosing."""
        self.eng.set_attr(self._bell, "toll_hour", float(hour))
        self.eng.set_attr(self._bell, "toll_kind", kind)
        self.eng.set_attr(self._bell, "call_strength", float(call_strength))
        self.eng.set_attr(self._bell, "ring_armed", 1.0)
        # settle the perceptual cascade: ring -> hear/wake -> decide -> attend. Each
        # stage's edges feed the next stage's guards, so re-settle until it is stable
        # (a within-pass added edge does not always re-wake a downstream rule's guard).
        for _ in range(4):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)
        new = [p for p in self.eng.neighbours(self._church, "peals") if p not in self._seen_peals]
        for p in new:
            self._seen_peals.add(p)
        if new:
            self._last_peal = new[0]
        return self._last_peal

    # ------------------------------------------------- glass-box read-offs
    def known_hour(self, name):
        """What the resident thinks the hour is -- None until a bell tells them."""
        a = self.eng.node(self._residents[name])["attrs"]
        return int(a["known_hour"]) if "known_hour" in a else None

    def is_asleep(self, name):
        return float(self.eng.node(self._residents[name])["attrs"].get("asleep", 0.0)) == 1.0

    def woke_at_bell(self, name):
        return float(self.eng.node(self._residents[name])["attrs"].get("woke_at_bell", 0.0)) == 1.0

    def heard_last(self, name):
        r = self._residents[name]
        return self._last_peal is not None and self._last_peal in self.eng.neighbours(r, "heard")

    def congregation(self):
        """Who answered the last service bell (emergent, by name)."""
        if self._last_peal is None:
            return []
        return sorted(n for n, r in self._residents.items()
                      if self._last_peal in self.eng.neighbours(r, "attends"))
