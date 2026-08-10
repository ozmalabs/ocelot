"""BigvilleJudgmentWorld -- bigville R25 (block 312000): GENERIC decision-by-collapse.

Any agent forms its OWN conclusion about a matter and acts on it. The verdict is
the agent COLLAPSING over the seeded Stance candidates (Argmax nearest-pole to its
own assessed lean) -- the substrate's decision idiom (cf. af_choose_action /
ss_choose_burn), NOT a threshold. Different agents reach different verdicts on the
SAME matter because the collapse's value reads each agent's OWN held dispositions.

A WORLD ADAPTER. No verdict/action DECISION in Python -- jc_conclude / jc_act are
seed rules. The adapter mints agents/matters/stances, wires who-considers-what,
ticks the fixpoint, arms the acting phase, and reads state.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                        # noqa: E402
from substrate.seed_loader import manifest_for             # noqa: E402

# The seeded stance candidates: a graded, signed set. The collapse picks the one
# whose pole sits closest to the agent's assessed lean, so >2 verdicts can emerge.
_STANCES = [("denounce", 2.0), ("condemn", 1.0), ("doubt", -1.0), ("exonerate", -2.0)]


class BigvilleJudgmentWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("agent_judgment"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "acting": 0.0})
        self._people = {}     # name -> nid (agents and/or subjects, all carry standing)
        self._agents = []     # names the town governs (the deciding agents)
        self._matters = {}    # claim -> Matter nid
        self._seed_stances()

    def _seed_stances(self):
        self._stances = []
        for label, pole in _STANCES:
            s = self.eng.add_node("Stance", {"label": label, "pole": pole})
            self._stances.append(s)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, credence=1.0, punitiveness=0.0, deference=0.0,
                  sanction=0.5, standing=3.0):
        """An agent with its OWN dispositions -- the held params the collapse reads.
        credence: how much evidence moves it; punitiveness: baseline lean to condemn
        (negative = lenient); deference: how much it defers to a subject's standing;
        sanction: how much public standing it strips when it condemns. Agents carry
        standing too, so an agent can itself be a subject."""
        a = self.eng.add_node("Person", {"name": name, "credence": float(credence),
                                          "punitiveness": float(punitiveness),
                                          "deference": float(deference),
                                          "sanction": float(sanction),
                                          "standing": float(standing)})
        self.eng.add_edge_unchecked(self._town, "governs", a)
        self._people[name] = a
        self._agents.append(name)
        return a

    def add_subject(self, name, *, standing=3.0):
        """A person the matter is about (needn't be a deciding agent)."""
        b = self.eng.add_node("Person", {"name": name, "standing": float(standing)})
        self._people[name] = b
        return b

    def raise_matter(self, claim, *, weight, subject):
        m = self.eng.add_node("Matter", {"claim": claim, "weight": float(weight)})
        self.eng.add_edge_unchecked(m, "about_subject", self._people[subject])
        self._matters[claim] = m
        return m

    def consider(self, agent, matter):
        self.eng.add_edge_unchecked(self._people[agent], "considers", matter)

    def consider_all(self, matter):
        """Every governed agent considers the matter (the whole citizenry weighs in)."""
        for name in self._agents:
            self.eng.add_edge_unchecked(self._people[name], "considers", matter)

    # ------------------------------------------------------------------ run
    def run(self):
        """Deliberation: every considering agent collapses to its own conclusion."""
        self.eng.force_all_dirty()
        return self.eng.run_rules(1000000)

    def enact(self):
        """Arm the acting phase: condemning agents strip the subject's standing."""
        self.eng.set_attr(self._town, "acting", 1.0)
        self.run()
        self.eng.set_attr(self._town, "acting", 0.0)

    # ------------------------------------------------- glass-box read-offs
    def conclusion_of(self, agent):
        a = self._people[agent]
        for concl in self.eng.neighbours(a, "holds_conclusion"):
            at = self.eng.node(concl)["attrs"]
            return at.get("verdict"), round(float(at.get("lean", 0.0)), 3)
        return None

    def verdicts(self):
        """Distribution of verdicts across all conclusions: {verdict: count}."""
        out = {}
        for a in self._people.values():
            for concl in self.eng.neighbours(a, "holds_conclusion"):
                v = self.eng.node(concl)["attrs"].get("verdict")
                out[v] = out.get(v, 0) + 1
        return out

    def condemn_count(self):
        """How many agents reached a condemning verdict (pole > 0)."""
        n = 0
        for a in self._people.values():
            for concl in self.eng.neighbours(a, "holds_conclusion"):
                if float(self.eng.node(concl)["attrs"].get("verdict_pole", 0.0)) > 0.0:
                    n += 1
        return n

    def standing_of(self, name):
        return float(self.eng.node(self._people[name])["attrs"]["standing"])
