#!/usr/bin/env python3
"""Record graph-witnessed task strategies (P10.04)."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (
    A, And, Append, Count, Eq, IfThenElse, IndexAt, L, Lt, N, Not, ONLINE_AREA,
    Plus, PApply, T, V, policy_on, productions, rule,
)

SEED_ID = "strategy_discovery"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def build():
    specs = [
        ("Agent", "has_strategy_discovery_policy", "StrategyDiscoveryPolicy"),
        ("Agent", "has_solve_task", "SolveTask"),
        ("SolveTask", "about_domain", "ProcessDomain"),
        ("Agent", "has_discovered_strategy", "DiscoveredStrategy"),
        ("DiscoveredStrategy", "about_domain", "ProcessDomain"),
        ("DiscoveredStrategy", "witnessed_by_task", "SolveTask"),
        ("SolveTask", "executes_discovered_strategy", "DiscoveredStrategy"),
    ]
    record = rule(
        "sd_record_solved_trace", ONLINE_AREA, 24,
        "Retain a strategy only from a completed task trace of graph-held processes.",
        [["agent", "has_strategy_discovery_policy", "pol"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"]],
        And(policy_on(), Eq(A("t", "status"), L("solved")),
            Not(Eq(A("t", "trace"), L([]))),
            Lt(Count(N("agent", "has_discovered_strategy")), A("pol", "max_records")),
            Not(Eq(A("t", "strategy_recorded"), L(1)))),
        [["add_node", "s", "DiscoveredStrategy", {
            "kind": T(A("d", "kind")), "domain": T(A("d", "name")),
            "trace": T(A("t", "trace")), "step_count": T(A("t", "steps")),
            "initial_state": T(A("t", "initial_state")), "goal_state": T(A("t", "goal")),
            "source": "observed_graph_trace", "status": "verified",
            "witnessed_effect": "solved_goal", "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")), "frame_epoch": T(A("d", "frame_epoch")),
            "probe_epoch": T(A("d", "probe_epoch")),
        }],
         ["add_edge", "agent", "has_discovered_strategy", "s", {}],
         ["add_edge", "s", "about_domain", "d", {}],
         ["add_edge", "s", "witnessed_by_task", "t", {}],
         ["set_attr", "t", "strategy_recorded", 1]],
    )
    start = rule(
        "sd_start_matching_strategy", ONLINE_AREA, 9,
        "Replay a verified graph trace only for a new task with the same domain, initial state, goal and epochs.",
        [["agent", "has_strategy_discovery_policy", "pol"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"],
         ["agent", "has_discovered_strategy", "s"], ["s", "about_domain", "d"],
         ["s", "witnessed_by_task", "source"]],
        And(policy_on(), Eq(A("t", "status"), L("active")), Eq(A("s", "status"), L("verified")),
            Not(Eq(V("t"), V("source"))), Eq(A("t", "state"), A("s", "initial_state")),
            Eq(A("t", "goal"), A("s", "goal_state")), Eq(A("d", "kind"), A("s", "kind")),
            Eq(A("d", "source_epoch"), A("s", "source_epoch")),
            Eq(A("d", "model_epoch"), A("s", "model_epoch")),
            Eq(A("d", "frame_epoch"), A("s", "frame_epoch")),
            Eq(A("d", "probe_epoch"), A("s", "probe_epoch")),
            Not(Eq(A("t", "strategy_started"), L(1)))),
        [["add_edge", "t", "executes_discovered_strategy", "s", {}],
         ["set_attr", "t", "strategy_started", 1], ["set_attr", "t", "strategy_index", 0],
         ["set_attr", "t", "status", "replaying"]],
        batch=False,
    )
    step = rule(
        "sd_apply_matching_strategy_step", ONLINE_AREA, 10,
        "Apply one witnessed process with the native evaluator and keep the executed trace on the task.",
        [["agent", "has_strategy_discovery_policy", "pol"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"],
         ["t", "executes_discovered_strategy", "s"], ["s", "about_domain", "d"],
         ["agent", "has_process_schema", "p"]],
        And(policy_on(), Eq(A("t", "status"), L("replaying")),
            Lt(A("t", "strategy_index"), Count(A("s", "trace"))),
            Eq(V("p"), IndexAt(A("s", "trace"), A("t", "strategy_index"))),
            Eq(A("d", "source_epoch"), A("s", "source_epoch")),
            Eq(A("d", "model_epoch"), A("s", "model_epoch")),
            Eq(A("d", "frame_epoch"), A("s", "frame_epoch")),
            Eq(A("d", "probe_epoch"), A("s", "probe_epoch"))),
        [["set_attr", "t", "strategy_next_state", T(PApply(A("p", "params"), A("t", "state")))],
         ["set_attr", "t", "state", T(A("t", "strategy_next_state"))],
         ["set_attr", "t", "trace", T(Append(A("t", "trace"), V("p")))],
         ["set_attr", "t", "steps", T(Plus(A("t", "steps"), L(1)))],
         ["set_attr", "t", "moves", T(Plus(A("t", "moves"), A("p", "cost")))],
         ["set_attr", "t", "strategy_index", T(Plus(A("t", "strategy_index"), L(1)))],
         ["set_attr", "t", "status", T(IfThenElse(
             Eq(A("t", "strategy_next_state"), A("t", "goal")), L("solved"),
             IfThenElse(Eq(A("t", "strategy_index"), Count(A("s", "trace"))),
                        L("strategy_failed"), L("replaying"))))],
         ["set_attr", "t", "strategy_next_state", None]],
        batch=False,
    )
    return {
        "id": SEED_ID, "version": "1.0.0", "depends_on": ["process_solving"],
        "self_load_only": True, "area": ONLINE_AREA,
        "description": "Retain graph-selected process traces as verified reusable strategy evidence.",
        "microtheory": {"name": SEED_ID, "description": "Learn strategies from witnessed task outcomes."},
        "nodes": [{"local_id": 0, "type": "StrategyDiscoveryPolicy", "attrs": {
            "name": "core_strategy_discovery_policy", "enabled": 0.0,
            "max_records": 128.0,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_strategy_discovery_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, specs), "rules": [start, step, record],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
