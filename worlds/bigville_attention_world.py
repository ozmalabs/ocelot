"""BigvilleAttentionWorld -- bigville cognitive C2 (block 327000): attention as a bounded,
arousal-modulated resource. focus follows the Yerkes-Dodson inverted-U in arousal,
multiplies task outcome, and gates which tasks can be completed (capacity).

A WORLD ADAPTER. No focus/complete DECISION in Python -- at_* are seed rules. The adapter
sets arousal/pressure (world I/O), gives tasks, ticks, and reads.
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


class BigvilleAttentionWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_attention"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._agents = {}
        self._tasks = {}   # name -> [task nid]

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, baseline_arousal=0.5, unmet_pressure=0.0,
                  arousal_opt=0.5, overload_gain=2.0):
        a = self.eng.add_node("Agent", {"name": name, "baseline_arousal": float(baseline_arousal),
                                        "unmet_pressure": float(unmet_pressure),
                                        "arousal_opt": float(arousal_opt),
                                        "overload_gain": float(overload_gain),
                                        "focus": 0.0, "arousal_eff": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_agent", a)
        self._agents[name] = a
        self._tasks[name] = []
        return a

    def set_arousal(self, name, baseline):
        self.eng.set_attr(self._agents[name], "baseline_arousal", float(baseline))

    def set_pressure(self, name, p):
        self.eng.set_attr(self._agents[name], "unmet_pressure", float(p))

    def give_task(self, name, *, base_skill=1.0, demand=0.0):
        t = self.eng.add_node("Task", {"base_skill": float(base_skill), "demand": float(demand),
                                       "done": 0.0, "outcome": 0.0})
        self.eng.add_edge_unchecked(self._agents[name], "has_task", t)
        self._tasks[name].append(t)
        return len(self._tasks[name]) - 1

    def run(self):
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def focus(self, name):
        return round(float(self.eng.node(self._agents[name])["attrs"]["focus"]), 4)

    def arousal_eff(self, name):
        return round(float(self.eng.node(self._agents[name])["attrs"]["arousal_eff"]), 4)

    def task_done(self, name, idx):
        return float(self.eng.node(self._tasks[name][idx])["attrs"]["done"]) == 1.0

    def task_outcome(self, name, idx):
        return round(float(self.eng.node(self._tasks[name][idx])["attrs"]["outcome"]), 4)
