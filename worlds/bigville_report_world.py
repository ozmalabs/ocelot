"""BigvilleReportWorld -- newspaper-writer Rung B (block 294000): townspeople GO
TO the publisher to report what they hold.

WHAT THIS DEMONSTRATES (NEWSPAPER_WRITER_PLAN.md Rung B + BIGVILLE_REPORT_PREREG.md)
----------------------------------------------------------------------------------
"Know to go to him to report" is not a hardcode. A resident holding a salient Fact
forms -- by RULE -- the intent to report it to whoever affords `makes_known`,
sets its own spatial goal to that afforder's cell, and WALKS there on the nav
flood (block 291000/292000). On arrival it delivers the Fact (directed,
proximity-bound conduct). Ablate the affordance -> no target, no goal, no
delivery. Ablate movement -> never arrives, no delivery.

Built ON TOP OF BigvilleMoveWorld so the "go to him" is the REAL nav flood, in the
SAME substrate as the report rules -- the report goal is a `seeks` edge a rule
writes, which the unchanged nav then routes.

ARCHITECTURE-RULE COMPLIANCE
----------------------------
A WORLD ADAPTER. No decision about who reports, to whom, or when to deliver -- all
three are the seed rules (rep_form_report_goal / rep_deliver_on_arrival) reading
the affordance, the held Fact's salience, and co-location. The adapter only mints
the movers/facts/affordance (ingest), ticks movement + rules, and reads state.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                   # noqa: E402
from worlds.bigville_move_world import BigvilleMoveWorld         # noqa: E402


class BigvilleReportWorld(BigvilleMoveWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        # the report rules live in the SAME nav substrate: the report goal is a
        # `seeks` edge a rule writes, which the unchanged nav flood then routes.
        self.eng.load_seed_manifest(manifest_for("bigville_report"), None)
        self._makes_known = self.eng.add_node("Affordance", {"name": "makes_known"})
        self._publisher = None            # name of the makes_known-affording mover
        self._facts = {}                  # reporter name -> Fact nid

    # ------------------------------------------------------------------ ingest
    def add_publisher(self, name, cell):
        """A stationary mover who affords makes_known -- the report TARGET."""
        m = self.add_mover(name, cell, energy=1e9, energy_cost=0.0)
        self.eng.add_edge_unchecked(m, "affords", self._makes_known)
        self._publisher = name
        return m

    def set_publisher_affordance(self, on):
        """Ablation lever: remove/restore the makes_known affordance (no target)."""
        m = self._movers[self._publisher]
        if on:
            self.eng.add_edge_unchecked(m, "affords", self._makes_known)
        else:
            self.eng.remove_edge_unchecked(m, "affords", self._makes_known)

    def add_reporter(self, name, cell, *, salience=1.0, desc=""):
        """A resident who HOLDS a salient Fact and (by rule) will carry it to the
        publisher. No goal set here -- the report rule forms it."""
        m = self.add_mover(name, cell, energy=1e9, energy_cost=0.0)
        self.eng.set_attr(m, "report_intent", 0.0)
        f = self.eng.add_node("Fact", {"salience": float(salience), "reported": 0.0,
                                        "desc": desc, "witnessed": 1.0})
        self.eng.add_edge_unchecked(m, "holds", f)
        self._facts[name] = f
        return m

    # ---------------------------------------------------------------- tick
    def step(self, *, move=True):
        """One tick: run the report rules (form the report goal / deliver on
        arrival), then advance each reporter one nav step toward its goal.
        `move=False` ablates movement (the reporter never travels)."""
        self.eng.force_all_dirty()
        self._cost_steps += self.eng.run_rules(1000000)
        if move:
            for name in list(self._facts):
                if name != self._publisher:
                    self.move_one(name)          # nav flood toward the report goal

    def run(self, T=40, *, move=True):
        for _ in range(T):
            self.step(move=move)
            if all(self.delivered(nm) for nm in self._facts if nm != self._publisher):
                break
        return self.tick if hasattr(self, "tick") else T

    # ------------------------------------------------- glass-box read-offs
    def delivered(self, reporter_name):
        """Did the publisher RECEIVE this reporter's fact? (a graph read)."""
        f = self._facts.get(reporter_name)
        if f is None or self._publisher is None:
            return False
        pub = self._movers[self._publisher]
        return f in list(self.eng.neighbours(pub, "received"))

    def report_intent(self, reporter_name):
        m = self._movers[reporter_name]
        return float(self.eng.node(m)["attrs"].get("report_intent", 0.0)) == 1.0

    def received_facts(self):
        """The facts the publisher now holds (delivered), as (desc, salience)."""
        pub = self._movers[self._publisher]
        out = []
        for f in self.eng.neighbours(pub, "received"):
            a = self.eng.node(f)["attrs"]
            out.append((a.get("desc", ""), float(a.get("salience", 0.0))))
        return out
