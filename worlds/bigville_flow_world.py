"""BigvilleFlowWorld -- bigville cognitive C5 (block 329000): intrinsic motivation ->
flow -> generativity. Flow at challenge~=skill; sustained flow mints a creation whose
value is recognized (appreciator count), not intrinsic.

A WORLD ADAPTER. No state/streak/generate/worth DECISION in Python -- fl_* are seed rules.
The adapter sets skill/challenge, steps, wires appreciation, and reads.
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


class BigvilleFlowWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_flow"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "step_epoch": 0.0})
        self._agents = {}
        self._creations = {}   # name -> [creation nid]

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, skill=0.5, flow_gain=8.0, tol=0.12, flow_needed=3):
        a = self.eng.add_node("Agent", {"name": name, "skill": float(skill), "challenge": float(skill),
                                        "flow_gain": float(flow_gain), "tol": float(tol),
                                        "flow_needed": float(flow_needed), "flow": 0.0,
                                        "flow_state": "", "flow_streak": 0.0, "stepped_epoch": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_agent", a)
        self._agents[name] = a
        self._creations[name] = []
        return a

    def set_challenge(self, name, difficulty):
        self.eng.set_attr(self._agents[name], "challenge", float(difficulty))

    def step(self, n=1):
        """Advance time: recompute flow/state, grow/reset the streak, generate on sustained flow."""
        for _ in range(n):
            self.eng.set_attr(self._town, "step_epoch",
                              float(self.eng.node(self._town)["attrs"]["step_epoch"]) + 1.0)
            self._run()
            for name, a in self._agents.items():
                seen = set(self._creations[name])
                for cr in self.eng.neighbours(a, "created"):
                    if cr not in seen:
                        self._creations[name].append(cr)

    def appreciate(self, name, idx, n_appreciators):
        """n agents recognize the creation -> its worth is that count."""
        cr = self._creations[name][idx]
        for _ in range(int(n_appreciators)):
            ap = self.eng.add_node("Agent", {"name": "admirer"})
            self.eng.add_edge_unchecked(ap, "appreciates", cr)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def flow(self, name):
        return round(float(self.eng.node(self._agents[name])["attrs"]["flow"]), 4)

    def flow_state(self, name):
        return self.eng.node(self._agents[name])["attrs"]["flow_state"]

    def n_creations(self, name):
        return len(self._creations[name])

    def creation_worth(self, name, idx):
        return int(self.eng.node(self._creations[name][idx])["attrs"]["worth"])
