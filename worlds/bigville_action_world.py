"""BigvilleActionWorld -- bigville R75 (block 393000): the generic action.

Perform an action on N THINGS with Y TOOLS (or none). An action is data: its inputs and its tools.
ONE generic engine (an_meet / an_use_tool / an_done) runs any of them -- forge, burn, and assemble
are all instances (assemble = using a hammer on two component inputs). Adding an action of any
shape is a data row.

A WORLD ADAPTER: the rules are the logic; this adapter installs the action data as graph nodes,
opens a Job (copying the action's checklist), and reads. Tools live in the town and WEAR with use.
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


class BigvilleActionWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_action_general"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._store = self.eng.add_node("Store", {"name": "store"})
        self.eng.add_edge_unchecked(self._town, "has_store", self._store)
        self._stock = {}; self._actors = {}; self._actions = {}; self._tools = {}

    def _run(self):
        for _ in range(6):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    def set_stock(self, kind, qty):
        if kind in self._stock:
            self.eng.set_attr(self._stock[kind], "qty", float(qty))
        else:
            s = self.eng.add_node("Stock", {"kind": kind, "qty": float(qty)})
            self.eng.add_edge_unchecked(self._store, "stock", s)
            self._stock[kind] = s
        return self._stock[kind]

    def add_tool(self, kind, *, condition=1.0, wear=0.05):
        """A tool in the town (a hammer, a crucible). It WEARS each time an action uses it."""
        t = self.eng.add_node("Tool", {"kind": kind, "condition": float(condition), "wear": float(wear)})
        self.eng.add_edge_unchecked(self._town, "has_tool", t)
        self._tools[kind] = t
        return t

    def add_actor(self, name, *, role):
        a = self.eng.add_node("Agent", {"name": name, "role": role, "busy": 0.0, "fatigue": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_actor", a)
        self._actors[name] = a
        return a

    def install_action(self, spec):
        """Install a general action as DATA: {name, requires, inputs:[[kind,qty],...], tools:[kind,...],
        out:[kind,qty], difficulty}. inputs can be ANY number (N); tools ANY number or none (Y)."""
        asp = self.eng.add_node("ActionSpec", {"name": spec["name"], "requires": spec.get("requires", ""),
                                               "out_kind": spec["out"][0], "out_qty": float(spec["out"][1]),
                                               "difficulty": float(spec.get("difficulty", 1.0))})
        self.eng.add_edge_unchecked(self._town, "has_actionspec", asp)
        for kind, qty in spec.get("inputs", []):
            need = self.eng.add_node("Need", {"kind": kind, "qty": float(qty)})
            self.eng.add_edge_unchecked(asp, "in_need", need)
        for kind in spec.get("tools", []):
            tu = self.eng.add_node("ToolUse", {"kind": kind})
            self.eng.add_edge_unchecked(asp, "in_tool", tu)
        self.set_stock(spec["out"][0], self.qty(spec["out"][0]))     # ensure the output pile exists
        self._actions[spec["name"]] = asp
        return asp

    def do(self, actor, action_name):
        """Perform an action: open a Job that copies the action's checklist (one Need per input, one
        ToolUse per tool); the generic rules meet each need, use each tool, and complete it."""
        asp = self._actions[action_name]
        job = self.eng.add_node("Job", {"action": action_name})
        self.eng.add_edge_unchecked(self._actors[actor], "on_job", job)
        self.eng.add_edge_unchecked(job, "runs", asp)
        self.eng.set_attr(self._actors[actor], "busy", 1.0)
        for need in self.eng.neighbours(asp, "in_need"):            # copy the checklist onto the job
            a = self.eng.node(need)["attrs"]
            jn = self.eng.add_node("Need", {"kind": a["kind"], "qty": float(a["qty"]), "met": 0.0})
            self.eng.add_edge_unchecked(job, "need", jn)
        for tu in self.eng.neighbours(asp, "in_tool"):
            a = self.eng.node(tu)["attrs"]
            jt = self.eng.add_node("ToolUse", {"kind": a["kind"], "met": 0.0})
            self.eng.add_edge_unchecked(job, "uses", jt)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def qty(self, kind):
        return round(float(self.eng.node(self._stock[kind])["attrs"]["qty"]), 4) if kind in self._stock else 0.0
    def tool_condition(self, kind): return round(float(self.eng.node(self._tools[kind])["attrs"]["condition"]), 4)
    def fatigue(self, actor): return round(float(self.eng.node(self._actors[actor])["attrs"]["fatigue"]), 4)
    def busy(self, actor): return float(self.eng.node(self._actors[actor])["attrs"]["busy"]) == 1.0
