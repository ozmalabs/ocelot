"""BigvilleMemoryWorld -- bigville cognitive C3 (block 326000): episodic memory.

Events become appraised, decaying traces (Tulving + OCC + ACT-R); mood = the most-active
trace's appraisal; recall boosts and re-appraises (reconsolidation).

A WORLD ADAPTER. No appraise/decay/recall/mood DECISION in Python -- mem_* are seed rules;
mood is an Argmax collapse in the seed. The adapter presents events, pulses time (a
world-fact metabolic epoch), arms recall, and reads.
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


class BigvilleMemoryWorld:
    def __init__(self, retention=0.6):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_memory"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "epoch": 0.0,
                                                "retention": float(retention)})
        self._agents = {}
        self._traces = {}   # name -> [trace nid in creation order]

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, cares_about, mood_thr=0.25):
        a = self.eng.add_node("Agent", {"name": name, "cares_about": cares_about,
                                        "mood": 0.0, "mood_thr": float(mood_thr)})
        self.eng.add_edge_unchecked(self._town, "has_agent", a)
        self._agents[name] = a
        self._traces[name] = []
        return a

    def present_event(self, name, *, topic, valence):
        """The agent perceives an event and lays down an appraised episodic trace."""
        ev = self.eng.add_node("Event", {"topic": topic, "valence": float(valence), "appraised": 0.0})
        self.eng.add_edge_unchecked(self._agents[name], "perceives", ev)
        self._run()
        # register the newly-minted trace (a has_trace neighbour not yet tracked).
        known = set(self._traces[name])
        for tr in self.eng.neighbours(self._agents[name], "has_trace"):
            if tr not in known:
                self._traces[name].append(tr)
        return len(self._traces[name]) - 1

    def pass_time(self, epochs=1):
        """A metabolic pulse: time passes, traces decay."""
        for _ in range(epochs):
            self.eng.set_attr(self._town, "epoch", float(self.eng.node(self._town)["attrs"]["epoch"]) + 1.0)
            self._run()

    def recall(self, name, idx, *, context_target):
        """Recall a trace in an emotional context: it reboosts and re-encodes toward it."""
        tr = self._traces[name][idx]
        self.eng.set_attr(tr, "context_target", float(context_target))
        self.eng.set_attr(tr, "recall_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def mood(self, name):
        return round(float(self.eng.node(self._agents[name])["attrs"].get("mood", 0.0)), 3)

    def activation(self, name, idx):
        return round(float(self.eng.node(self._traces[name][idx])["attrs"]["activation"]), 4)

    def appraisal(self, name, idx):
        return round(float(self.eng.node(self._traces[name][idx])["attrs"]["appraisal"]), 4)
