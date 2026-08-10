"""BigvilleMotivationWorld -- bigville cognitive C1 (block 325000): the motivational core.

Each agent holds a data-driven set of Drives; the dominant urge selects the pursued goal
(an Argmax collapse over the agent's own drives), Psi modulators derive from arousal, and
the selection threshold provides goal-hysteresis. Different weight profiles diverge.

A WORLD ADAPTER. No urge/select/switch DECISION in Python -- mv_* are seed rules; the goal
selection is an Argmax collapse in the seed. The adapter mints drives, sets levels (world
I/O: a metabolic pulse depletes them), ticks, and reads.
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


class BigvilleMotivationWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_motivation"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._agents = {}
        self._drives = {}   # (agent, kind) -> nid

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, drives, res_gain=0.6, thr_gain=0.5):
        """drives: {kind: (setpoint, level, weight)}. res_gain/thr_gain: modulator sensitivities."""
        a = self.eng.add_node("Agent", {"name": name, "pursues": "", "pursued_urge": 0.0,
                                        "arousal": 0.0, "resolution_level": 1.0,
                                        "selection_threshold": 0.0,
                                        "res_gain": float(res_gain), "thr_gain": float(thr_gain)})
        self.eng.add_edge_unchecked(self._town, "has_agent", a)
        self._agents[name] = a
        for kind, (sp, lv, w) in drives.items():
            d = self.eng.add_node("Drive", {"kind": kind, "setpoint": float(sp),
                                            "level": float(lv), "weight": float(w), "urge": 0.0})
            self.eng.add_edge_unchecked(a, "has_drive", d)
            self._drives[(name, kind)] = d
        return a

    def set_level(self, name, kind, level):
        """World I/O: satisfy (raise) or deplete (lower) a drive's level."""
        self.eng.set_attr(self._drives[(name, kind)], "level", float(level))

    def run(self):
        for _ in range(5):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------- glass-box read-offs
    def pursues(self, name):
        return self.eng.node(self._agents[name])["attrs"].get("pursues")

    def urge(self, name, kind):
        return round(float(self.eng.node(self._drives[(name, kind)])["attrs"].get("urge", 0.0)), 3)

    def arousal(self, name):
        return round(float(self.eng.node(self._agents[name])["attrs"].get("arousal", 0.0)), 3)

    def resolution(self, name):
        return round(float(self.eng.node(self._agents[name])["attrs"].get("resolution_level", 0.0)), 3)

    def selection_threshold(self, name):
        return round(float(self.eng.node(self._agents[name])["attrs"].get("selection_threshold", 0.0)), 3)
