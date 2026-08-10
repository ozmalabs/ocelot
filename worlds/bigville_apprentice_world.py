"""BigvilleApprenticeWorld -- bigville R61 (block 374000): the trades train apprentices.

A master takes on an apprentice, who learns the craft skill under them over successive training
periods (composing with bigville_craft: skill = tool quality, so a trained apprentice's tools
improve); graduates to journeyman near the master's competence; and inherits the trade when the
master dies.

A WORLD ADAPTER. No learn/graduate/succeed DECISION in Python -- ap_* are seed rules. The adapter
sets up the master + apprentice, advances training periods, and reflects the graph's succession
decision by moving the maker-role edge (mechanical; the trade type is data). It also loads
bigville_craft so the adapter can have an agent forge a head and read its quality.
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


class BigvilleApprenticeWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_apprentice"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_craft"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._store = self.eng.add_node("Store", {"iron": 50.0, "timber": 50.0, "charcoal": 50.0})
        self.eng.add_edge_unchecked(self._town, "has_store", self._store)
        self._agents = {}

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_master(self, name, *, trade="smith", skill=0.7, mentoring=0.8, reluctance=0.1):
        m = self.eng.add_node("Agent", {"name": name, "trade": trade, "role": "master", "skill": float(skill),
                                        "alive": 1.0, "period": 0.0, "make_armed": 0.0, "making_kind": "",
                                        "making_verb": "", "base_mult": 0.0, "base_effort": 0.0,
                                        "mat_cost": 0.0, "fuel_cost": 0.0, "made": 0.0,
                                        # disposition read by the ap_decide collapse
                                        "mentoring": float(mentoring), "reluctance": float(reluctance)})
        self.eng.add_edge_unchecked(self._town, "has_resident", m)
        self.eng.add_edge_unchecked(self._town, f"has_{trade}", m)     # the town's maker of this trade
        self._agents[name] = m
        self._trade_of = getattr(self, "_trade_of", {}); self._trade_of[name] = trade
        return m

    def seek_apprenticeship(self, name, master, *, skill=0.1, learn_rate=0.3):
        """A would-be apprentice SEEKS a master (cand -seeks_master-> master). The master then DECIDES
        (ap_decide collapse) whether to take them on -- this method does NOT force the bond. Returns
        whether the master accepted."""
        a = self.eng.add_node("Agent", {"name": name, "role": "seeker", "skill": float(skill),
                                        "learn_rate": float(learn_rate), "graduated": 0.0, "succeeded": 0.0,
                                        "learned_epoch": 0.0, "alive": 1.0, "period": 0.0, "make_armed": 0.0,
                                        "making_kind": "", "making_verb": "", "base_mult": 0.0,
                                        "base_effort": 0.0, "mat_cost": 0.0, "fuel_cost": 0.0, "made": 0.0,
                                        "apprentice_verdict": ""})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self.eng.add_edge_unchecked(a, "seeks_master", self._agents[master])
        self._agents[name] = a
        self._run()
        return self.role(name) == "apprentice"

    def take_apprentice(self, master, name, *, skill=0.1, learn_rate=0.3):
        """Convenience: seek + (assert) accepted, for the learning/succession tests. Uses a willing
        master by default so the bond forms."""
        return self.seek_apprenticeship(name, master, skill=skill, learn_rate=learn_rate)

    def verdict(self, name): return self.eng.node(self._agents[name])["attrs"].get("apprentice_verdict", "")

    def _reflect_makers(self):
        """Reflect the graph's graduation/succession decisions: a graduated apprentice (a journeyman)
        is wired as a town maker of their trade (has_<trade>), so they can practise it. Mechanical --
        the DECISION (graduated) is the rule; the trade is data; the edge type is a fixed string a
        generic rule cannot add."""
        for a in self.eng.neighbours(self._town, "has_resident"):
            attrs = self.eng.node(a)["attrs"]
            if float(attrs.get("graduated", 0.0)) == 1.0 and attrs.get("trade"):
                trade = attrs["trade"]
                if not self.eng.has_edge(self._town, f"has_{trade}", a):
                    self.eng.add_edge_unchecked(self._town, f"has_{trade}", a)

    def train(self, master, periods=1):
        """Advance `periods` training periods -- the apprentice learns a step each (epoch-guarded)."""
        m = self._agents[master]
        for _ in range(int(periods)):
            self.eng.set_attr(m, "period", float(self.eng.node(m)["attrs"]["period"]) + 1.0)
            self._run()
        self._reflect_makers()

    def die(self, name):
        """The master dies. Settle succession, then reflect it: move the maker-role edge to a
        graduated apprentice who has succeeded (mechanical -- the trade type is data)."""
        self.eng.set_attr(self._agents[name], "alive", 0.0)
        self._run()
        trade = self._trade_of.get(name)
        dead = self._agents[name]
        for app in self.eng.neighbours(dead, "has_apprentice"):
            if float(self.eng.node(app)["attrs"].get("succeeded", 0.0)) == 1.0:
                if self.eng.has_edge(self._town, f"has_{trade}", dead):
                    self.eng.remove_edge_unchecked(self._town, f"has_{trade}", dead)
                self.eng.add_edge_unchecked(self._town, f"has_{trade}", app)   # the heir is now the maker

    def forge_head(self, maker, *, kind="pick", verb="mine", base_mult=2.0):
        """Have an agent forge a tool head (bigville_craft) and return the head's quality (= skill)."""
        m = self._agents[maker]
        before = set(self.eng.neighbours(self._town, "has_part"))
        for k, v in (("making_kind", kind), ("making_verb", verb), ("base_mult", base_mult),
                     ("base_effort", 1.0), ("mat_cost", 1.0), ("fuel_cost", 1.0), ("make_armed", 1.0)):
            self.eng.set_attr(m, k, v if isinstance(v, str) else float(v))
        self._run()
        new = set(self.eng.neighbours(self._town, "has_part")) - before
        return round(float(self.eng.node(next(iter(new)))["attrs"]["quality"]), 4) if new else None

    # ------------------------------------------------- glass-box read-offs
    def skill(self, name): return round(float(self.eng.node(self._agents[name])["attrs"]["skill"]), 4)
    def role(self, name): return self.eng.node(self._agents[name])["attrs"]["role"]
    def graduated(self, name): return float(self.eng.node(self._agents[name])["attrs"]["graduated"]) == 1.0
    def is_town_maker(self, name, trade):
        return self.eng.has_edge(self._town, f"has_{trade}", self._agents[name])
