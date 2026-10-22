#!/usr/bin/env python3
"""Generate the disabled-by-default graph selector for P16 native execution."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from track_i_seed_lib import A, And, Eq, Exists, L, N, Not, OFFLINE_AREA, policy_on, productions, rule  # noqa: E402

SEED_ID = "native_process_execution"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def build():
    specs = [
        ("Agent", "has_native_process_execution_policy", "NativeProcessExecutionPolicy"),
        ("Agent", "has_invention_operator", "InventionOperator"),
        ("InventionOperator", "derived_from_candidate", "CandidateOperator"),
        ("Agent", "has_solve_task", "SolveTask"),
        ("SolveTask", "has_native_execution_request", "NativeExecutionRequest"),
        ("NativeExecutionRequest", "selected_operator", "InventionOperator"),
        ("NativeExecutionRequest", "selected_candidate", "CandidateOperator"),
        ("NativeExecutionRequest", "for_solve_task", "SolveTask"),
        ("NativeExecutionRequest", "has_execution_budget_request", "ThinkingBudgetRequest"),
    ]
    select = rule(
        "npe_select_current_graph_operator", OFFLINE_AREA, 10,
        "Select the active graph-owned candidate for a task; no arm name or host process is consulted.",
        [["agent", "has_native_process_execution_policy", "pol"],
         ["agent", "has_invention_operator", "operator"],
         ["operator", "derived_from_candidate", "candidate"],
         ["agent", "has_solve_task", "task"],
         ["agent", "has_thinking_budget", "budget"]],
        And(policy_on(), Eq(A("operator", "status"), L("active")),
            Eq(A("budget", "enabled"), L(1.0)),
            Eq(A("candidate", "status"), L("promoted")),
            Eq(A("task", "status"), L("active")),
            Not(Exists(N("task", "has_native_execution_request"), "old",
                       Eq(A("old", "status"), L("selected"))))),
        [["add_node", "request", "NativeExecutionRequest", {
            "status": "selected", "selected_by": "native_graph_rule",
            "source_epoch": {"__term__": A("candidate", "source_epoch")}}],
         ["add_edge", "agent", "has_native_execution_request", "request", {}],
         ["add_edge", "task", "has_native_execution_request", "request", {}],
         ["add_edge", "request", "selected_operator", "operator", {}],
         ["add_edge", "request", "selected_candidate", "candidate", {}],
         ["add_edge", "request", "for_solve_task", "task", {}],
         ["add_node", "budget_request", "ThinkingBudgetRequest", {
            "requester_kind": "native_process_expression", "status": "pending",
            "cost": 24.0, "deadline_epoch": None}],
         ["add_edge", "request", "has_execution_budget_request", "budget_request", {}],
         ["add_edge", "budget_request", "draws_on_thinking_budget", "budget", {}]], batch=True)
    fund_selected = rule(
        "npe_enable_only_funded_selection", OFFLINE_AREA, 11,
        "Make a graph-selected operator executable only after its one shared-budget request is approved.",
        [["agent", "has_native_process_execution_policy", "pol"],
         ["agent", "has_native_execution_request", "request"],
         ["request", "selected_operator", "operator"],
         ["request", "selected_candidate", "candidate"],
         ["request", "for_solve_task", "task"],
         ["request", "has_execution_budget_request", "budget_request"]],
        And(policy_on(), Eq(A("request", "status"), L("selected")),
            Eq(A("request", "selected_by"), L("native_graph_rule")),
            Eq(A("operator", "status"), L("active")),
            Eq(A("candidate", "status"), L("promoted")),
            Eq(A("task", "status"), L("active")),
            Eq(A("budget_request", "status"), L("approved"))),
        [["set_attr", "request", "status", "funded"]])
    return {
        "id": SEED_ID, "version": "1.0.0", "depends_on": ["recursive_process_improvement"],
        "self_load_only": True, "area": OFFLINE_AREA,
        "description": "P16.03 graph selector for native expression execution. Disabled by default; action authorization remains at the existing sink.",
        "nodes": [{"local_id": 0, "type": "NativeProcessExecutionPolicy", "attrs": {
            "name": "native_process_execution_policy", "enabled": 0.0,
            "max_expression_visits": 64.0, "human_gate": 1.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_native_process_execution_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, specs), "rules": [select, fund_selected],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
