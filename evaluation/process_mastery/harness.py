"""PMB v1 harness: boot an agent, hand it a domain's affordances and tasks, tick.

Mechanical only. The harness:
  * selects an explicit seed/policy profile (including a Track-I-free baseline);
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
from evaluation.process_mastery.native_process_execution import params_digest  # noqa: E402
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

# The PMB adapter owns only data vocabulary and admissible data links. It does
# not install a solver or any Track I policy, so both arms can receive the
# same graph-resident world without giving the baseline the treatment rules.
WORLD_MANIFEST = {
    "id": "pmb_world_adapter", "version": "1.0.0", "depends_on": [],
    "productions": [
        {"provenance": "pmb:has_process_domain", "src": {"type": "Agent", "var": "s"}, "edge_type": "has_process_domain", "tgt": {"type": "ProcessDomain", "var": "t"}},
        {"provenance": "pmb:has_process_schema", "src": {"type": "Agent", "var": "s"}, "edge_type": "has_process_schema", "tgt": {"type": "ProcessSchema", "var": "t"}},
        {"provenance": "pmb:has_solve_task", "src": {"type": "Agent", "var": "s"}, "edge_type": "has_solve_task", "tgt": {"type": "SolveTask", "var": "t"}},
        {"provenance": "pmb:about_domain", "src": {"type": "SolveTask", "var": "s"}, "edge_type": "about_domain", "tgt": {"type": "ProcessDomain", "var": "t"}},
    ],
}


class Agent:
    """A profile-specific agent. The default remains the Track I treatment."""

    def __init__(self, extra_seeds=(), policy_overrides=None, budget=None, view_enabled=False,
                 track_i=True, profile=None, adapters=None):
        self.track_i = bool(track_i)
        self.profile = profile or ("track-i" if self.track_i else "baseline")
        self.adapters = dict(adapters or {})
        self.resource_budget = dict(budget or {})
        selected = TRACK_I_SEEDS if self.track_i else ()
        seeds = tuple(dict.fromkeys(CORE_SEEDS + selected + tuple(extra_seeds)))
        self.s, self.ag = boot_core(seeds)
        self.s._inner.load_seed_manifest(WORLD_MANIFEST, self.ag)
        self.native = self.s._inner
        for t, k in (("ProcessSchema", "fingerprint"), ("ProcessSchema", "operator")):
            self.native.declare_attr_index(t, k)
        overrides = policy_overrides or {}
        for ptype in (list(POLICIES) if self.track_i else []) + [t for t in overrides if t not in POLICIES]:
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
        d = self.s.add_node("ProcessDomain", {
            "name": name, "kind": kind, "probes": probes, "probe_epoch": 0,
            "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0, **attrs,
        })
        self.s.add_edge(self.ag, "has_process_domain", d, {})
        for hname, params in held.items():
            node = {
                "kind": kind, "domain": name, "domain_kind": kind, "name": hname,
                "params": list(params), "source_digest": params_digest(list(params)),
                "cost": 1.0, "provenance": "held", "status": "active",
                "invariants": [], "owner_agent": self.ag, "source_epoch": 0,
                "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0,
                "source_probe_epoch": 0,
            }
            if trees and hname in trees:
                node["expr_tree"] = trees[hname]
            sid = self.s.add_node("ProcessSchema", node)
            self.s.add_edge(self.ag, "has_process_schema", sid, {})
        self.domains[name] = d
        return d

    def add_loopover_domain(self, n, name=None):
        moves = gen.loopover_moves(n)
        name = name or f"loopover_{n}"
        return self.add_domain(name, "permutation", [list(range(n * n))], moves,
                               trees={k: gen.move_tree(k) for k in moves}, size=float(n))

    def add_solve_task(self, domain, state, goal, **attrs):
        t = self.s.add_node("SolveTask", {
            "domain": domain, "state": list(state), "initial_state": list(state),
            "goal": list(goal), "status": "active",
            "steps": 0, "moves": 0.0, "trace": [], "stuck_count": 0, "tools_seen": 0, **attrs})
        self.s.add_edge(self.ag, "has_solve_task", t, {})
        self.s.add_edge(t, "about_domain", self.domains[domain], {})
        return t

    def request_action(self, task, action, *, adapter="action"):
        """Submit an explicit requested action through a registered world adapter."""
        handler = self.adapters.get(adapter)
        if handler is None:
            raise RuntimeError(f"unsupported: missing {adapter!r} action adapter")
        return handler(self, task, action)

    def register_program_adapter(self):
        """Opt this explicit PMB agent into family-e's native MBPP adapter."""
        from evaluation.process_mastery.program_adapter import register
        register(self)

    @staticmethod
    def trial_record(status, **fields):
        if status not in {"NOT_RUN", "UNSUPPORTED", "TIMEOUT", "FAILED", "COMPLETED"}:
            raise ValueError(f"unknown PMB trial status: {status}")
        return {"status": status, **fields}

    # -- running -----------------------------------------------------------
    def run(self, max_ticks=400, max_steps=100_000):
        t0 = time.time()
        ticks = 0
        quiescent = False
        for _ in range(max_ticks):
            ticks += 1
            if self.s.tick(max_steps) == 0:
                quiescent = True
                break
        return {"ticks": ticks, "seconds": round(time.time() - t0, 2),
                "quiescent": quiescent}

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
