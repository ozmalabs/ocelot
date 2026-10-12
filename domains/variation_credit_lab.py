"""Graph-level driver for outcome-credited variation episodes (WP2/WP4).

Mechanical harness only: it creates the StandingConcern a human promote would
create, asks the held `variation_pick` Program which family to try, writes the
Experiment/SeedDelta/Run shape `_compose_experiment_rule` + the dispatcher
produce, and sets `outcome` exactly as a family judge would from the child's
report. The child's report is supplied by an authored experiment WORLD (a
per-concern hidden fixing family), which is disclosed in every result. All
policy decisions -- which family, what credit, how credit changes the next
choice -- are made by graph rules and the held Program.
"""
from __future__ import annotations

from domains import reflective_faculty as rf
from substrate.boot_core import boot_core

ALL_HEADS = ["test", "replay", "send", "judge", "adopt", "bound", "ruleliteral",
             "datumfeedback", "shapemint", "structure", "gradient"]


class VariationLab:
    def __init__(self, credit: bool, use_credit: bool = True, window="seed"):
        self.s, self.ag = boot_core()
        self.native = rf._native_eval2(self.s)
        seeds = ("variation_ops", "variation_credit") if credit else ("variation_ops",)
        rf._ensure_seed_chain(self.s, self.native, self.ag, seeds)
        self.native.run_rules()
        for p in self.s.nodes("VariationPolicy"):
            self.s.set_attr(p, "use_credit", 1 if use_credit else 0)
            if window != "seed":           # None -> unbounded history (v1.0.0)
                self.s.set_attr(p, "window", window)
        self.n = 0

    def pick(self, key: str, heads=ALL_HEADS):
        return rf._pick_variation_op(self, heads, key)

    @property
    def inner(self):
        return self.native

    @property
    def agent(self):
        return self.ag

    def concern(self, kind: str) -> str:
        self.n += 1
        key = f"concern_{self.n}"
        self.s.add_node("StandingConcern", {"name": key, "kind": kind})
        return key

    def trial(self, key: str, op: str, outcome: str):
        exp = self.s.add_node("Experiment", {"status": "done", "axis_tag": key})
        delta = self.s.add_node("SeedDelta", {"variation_op": op, "concern_key": key})
        run = self.s.add_node("Run", {"status": "done"})
        # Unchecked, as the experiment-dispatch ingest does for these
        # host-produced records (their Γ productions live in the full corpus).
        self.native.add_edge_unchecked(exp, "has_delta", delta)
        self.native.add_edge_unchecked(exp, "produced", run)
        self.s.set_attr(exp, "outcome", outcome)
        self.native.add_edge_unchecked(exp, "analysed", run)
        self.native.run_rules()
        return exp, delta

    def episode(self, kind: str, fixes: str, budget: int = 8, heads=ALL_HEADS):
        """Run one improvement episode; returns the list of ops tried (the last
        one supported if fixed within budget)."""
        key = self.concern(kind)
        tried = []
        for _ in range(budget):
            op = self.pick(key, heads)
            if op is None:
                break
            out = "supported" if op == fixes else "refuted"
            self.trial(key, op, out)
            tried.append(op)
            if out == "supported":
                break
        return tried

    def credits(self):
        return {(a.get("op"), a.get("kind")): (a.get("trials"), a.get("supports"))
                for a in (self.s.node(n)["attrs"] for n in self.s.nodes("VariationCredit"))}
