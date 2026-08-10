"""BigvilleStressWorld -- bigville cognitive C4 (block 328000): allostatic load + coping.

Chronic stress accumulates as load (McEwen); crossing the window of tolerance breaks the
agent; coping (co-regulation) and rest recover it.

A WORLD ADAPTER. No accumulate/break/cope/recover DECISION in Python -- al_* are seed
rules. The adapter presents stressors, arms coping, pulses rest, and reads.
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


class BigvilleStressWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_stress"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "rest_epoch": 0.0})
        self._agents = {}

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, window=1.0, coping_relief=0.5, recovery=0.7):
        a = self.eng.add_node("Agent", {"name": name, "load": 0.0, "window": float(window),
                                        "coping_relief": float(coping_relief),
                                        "recovery": float(recovery), "broken": 0.0,
                                        "cope_armed": 0.0, "rested_epoch": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_agent", a)
        self._agents[name] = a
        return a

    def stress(self, name, magnitude):
        """A stressor: its magnitude accumulates onto the agent's allostatic load."""
        s = self.eng.add_node("Stressor", {"magnitude": float(magnitude), "absorbed": 0.0})
        self.eng.add_edge_unchecked(self._agents[name], "perceives_stress", s)
        self._run()

    def cope(self, name):
        """A coping act (co-regulation) reduces the load."""
        self.eng.set_attr(self._agents[name], "cope_armed", 1.0)
        self._run()

    def rest(self, epochs=1):
        """Passive recovery: load decays over rest epochs."""
        for _ in range(epochs):
            self.eng.set_attr(self._town, "rest_epoch",
                              float(self.eng.node(self._town)["attrs"]["rest_epoch"]) + 1.0)
            self._run()

    # ------------------------------------------------- glass-box read-offs
    def load(self, name):
        return round(float(self.eng.node(self._agents[name])["attrs"]["load"]), 4)

    def broken(self, name):
        return float(self.eng.node(self._agents[name])["attrs"]["broken"]) == 1.0
