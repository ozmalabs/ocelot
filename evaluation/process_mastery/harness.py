"""PMB v1 harness: boot an agent, hand it a domain's affordances and tasks, tick.

Mechanical only. The harness:
  * boots the core seeds plus the Track I seeds and switches their policies on;
  * declares an attribute index on ProcessSchema.fingerprint (an engine
    performance hint; without it the same rules run by linear scan);
  * installs the WORLD: a ProcessDomain (state encoding + probe battery),
    the held processes the world affords, and SolveTasks;
  * ticks until the graph is quiescent and reads results back.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from substrate.boot_core import CORE_SEEDS, boot_core  # noqa: E402

from evaluation.process_mastery import generators as gen  # noqa: E402
from evaluation.process_mastery.scorecard import write_scorecard  # noqa: E402,F401

TRACK_I_SEEDS = (
    "thinking_budget",
    "process_schema",
    "invention_operators",
    "invention_round",
    "invariant_miner",
    "process_solving",
)
POLICIES = {
    "ProcessSchemaPolicy": {},
    "InventionPolicy": {},
    "InvariantMinerPolicy": {},
    "SolverPolicy": {},
}


class Agent:
    """A booted agent with Track I seeds on. `extra_seeds` adds later seeds."""

    def __init__(self, extra_seeds=(), policy_overrides=None, budget=None, view_enabled=False):
        seeds = tuple(dict.fromkeys(CORE_SEEDS + TRACK_I_SEEDS + tuple(extra_seeds)))
        self.s, self.ag = boot_core(seeds)
        self.native = self.s._inner
        for t, k in (("ProcessSchema", "fingerprint"), ("ProcessSchema", "operator")):
            self.native.declare_attr_index(t, k)
        overrides = policy_overrides or {}
        for ptype in list(POLICIES) + [t for t in overrides if t not in POLICIES]:
            for nid in self.s.nodes(ptype):
                self.s.set_attr(nid, "enabled", 1.0)
                for k, v in overrides.get(ptype, {}).items():
                    self.s.set_attr(nid, k, v)
        for nid in self.s.nodes("ProcessSchemaPolicy"):
            self.s.set_attr(nid, "view_enabled", 1.0 if view_enabled else 0.0)
        if budget is not None:
            for nid in self.s.nodes("ThinkingBudget"):
                for k, v in budget.items():
                    self.s.set_attr(nid, k, v)
        self.domains: dict[str, int] = {}

    # -- world installation ------------------------------------------------
    def add_domain(self, name, kind, probes, held: dict[str, object], trees=None, **attrs):
        d = self.s.add_node("ProcessDomain", {"name": name, "kind": kind, "probes": probes, **attrs})
        self.native.add_edge_unchecked(self.ag, "has_process_domain", d, {})
        for hname, params in held.items():
            node = {
                "kind": kind, "domain": name, "domain_kind": kind, "name": hname,
                "params": list(params), "cost": 1.0, "provenance": "held", "status": "active",
                "invariants": [],
            }
            if trees and hname in trees:
                node["expr_tree"] = trees[hname]
            sid = self.s.add_node("ProcessSchema", node)
            self.native.add_edge_unchecked(self.ag, "has_process_schema", sid, {})
        self.domains[name] = d
        return d

    def add_loopover_domain(self, n, name=None):
        moves = gen.loopover_moves(n)
        name = name or f"loopover_{n}"
        return self.add_domain(name, "permutation", [list(range(n * n))], moves,
                               trees={k: gen.move_tree(k) for k in moves}, size=float(n))

    def add_solve_task(self, domain, state, goal, **attrs):
        t = self.s.add_node("SolveTask", {
            "domain": domain, "state": list(state), "goal": list(goal), "status": "active",
            "steps": 0, "moves": 0.0, "trace": [], "stuck_count": 0, "tools_seen": 0, **attrs})
        self.native.add_edge_unchecked(self.ag, "has_solve_task", t, {})
        self.native.add_edge_unchecked(t, "about_domain", self.domains[domain], {})
        return t

    # -- running -----------------------------------------------------------
    def run(self, max_ticks=400, max_steps=100_000):
        t0 = time.time()
        ticks = 0
        for _ in range(max_ticks):
            ticks += 1
            if self.s.tick(max_steps) == 0:
                break
        return {"ticks": ticks, "seconds": round(time.time() - t0, 2)}

    # -- reading -----------------------------------------------------------
    def attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def nodes(self, ntype, **match):
        out = []
        for nid in self.s.nodes(ntype):
            a = self.attrs(nid)
            if all(a.get(k) == v for k, v in match.items()):
                out.append(nid)
        return out

    def schemas(self, domain, **match):
        return self.nodes("ProcessSchema", domain=domain, **match)

    def invented(self, domain):
        return [x for x in self.schemas(domain, status="active") if self.attrs(x).get("invented") == 1]
