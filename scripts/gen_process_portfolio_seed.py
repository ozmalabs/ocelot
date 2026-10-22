#!/usr/bin/env python3
"""Generate disabled-by-default graph scheduling for P15 process portfolios."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from track_i_seed_lib import (  # noqa: E402
    A, And, Count, Eq, Exists, L, Lt, Lte, N, Not, Or, Sum, T,
)

SEED_ID = "process_portfolio"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"
AREA = "process_portfolio"


def build():
    relations = [
        ("Agent", "has_process_portfolio_policy", "ProcessPortfolioPolicy"),
        ("Agent", "has_portfolio_batch", "ProcessPortfolioBatch"),
        ("ProcessPortfolioBatch", "has_work_unit", "ProcessPortfolioWorkUnit"),
        ("ProcessPortfolioBatch", "funded_by", "ThinkingBudgetRequest"),
        ("Agent", "has_cognitive_area", "CognitiveArea"),
        ("ProcessPortfolioWorkUnit", "has_native_task", "CognitiveTask"),
        ("ProcessPortfolioWorkUnit", "has_receipt", "ProcessPortfolioReceipt"),
        ("Agent", "has_process_portfolio_receipt", "ProcessPortfolioReceipt"),
        ("CognitiveArea", "has_task", "CognitiveTask"),
        ("CognitiveTask", "has_result", "TaskResult"),
    ]
    productions = [
        {"provenance": f"seed:{SEED_ID}:{edge}:{src}:{dst}",
         "src": {"type": src, "var": "src"}, "edge_type": edge,
         "tgt": {"type": dst, "var": "tgt"}}
        for src, edge, dst in relations
    ]
    policy = ["agent", "has_process_portfolio_policy", "policy"]
    total_cost = Sum(N("batch", "has_work_unit"), "member", A("member", "cost"))
    active_batch = Exists(
        N("agent", "has_portfolio_batch"), "active",
        Or(Eq(A("active", "status"), L("funding_pending")),
           Eq(A("active", "status"), L("funded")),
           Eq(A("active", "status"), L("running"))),
    )
    earlier_batch = Exists(
        N("agent", "has_portfolio_batch"), "earlier",
        And(Eq(A("earlier", "status"), L("proposed")),
            Lt(A("earlier", "batch_key"), A("batch", "batch_key"))),
    )
    rules = [
        {
            "name": "pp_apply_bounded_worker_cap_to_native_area",
            "area": "memory_consolidation", "order": 5,
            "latency_class": "background", "batch": False,
            "comment": "The graph policy bounds the existing native cognitive area; available hardware never raises the graph-selected cap.",
            "match": [policy, ["agent", "has_cognitive_area", "area"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                         Eq(A("area", "name"), L(AREA)),
                         Lt(A("policy", "max_workers"), A("area", "desired_workers"))),
            "effects": [["set_attr", "area", "desired_workers", T(A("policy", "max_workers"))]],
        },
        {
            "name": "pp_fund_one_bounded_batch_from_shared_budget",
            "area": "memory_consolidation", "order": 10,
            "latency_class": "background", "batch": False,
            "comment": "Reserve the sum of all partition costs with one shared-budget request before a batch can run. Only one batch may be active, preventing same-settlement double debit races.",
            "match": [policy, ["agent", "has_thinking_budget", "budget"],
                      ["agent", "has_network_mode_state", "mode"],
                      ["agent", "has_portfolio_batch", "batch"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                         Eq(A("batch", "status"), L("proposed")),
                         Lte(Count(N("batch", "has_work_unit")), A("policy", "max_partitions")),
                         Lte(total_cost, A("policy", "max_work_units")),
                         Not(active_batch),
                         Not(earlier_batch),
                         Not(Exists(N("batch", "has_work_unit"), "cancel",
                                     Eq(A("cancel", "status"), L("cancel_requested")))),
                         Not(Exists(N("batch", "funded_by"), "old", L(True)))),
            "effects": [
                ["add_node", "request", "ThinkingBudgetRequest", {
                    "requester_kind": "process_portfolio",
                    "requester_key": T(A("batch", "batch_key")),
                    "source_key": T(A("batch", "batch_key")),
                    "source_epoch": T(A("batch", "source_epoch")),
                    "requested_epoch": T(A("mode", "epoch")),
                    "deadline_epoch": T(A("batch", "deadline_epoch")),
                    "cost": T(total_cost), "status": "pending",
                }],
                ["add_edge", "batch", "funded_by", "request", {}],
                ["add_edge", "request", "draws_on_thinking_budget", "budget", {}],
                ["set_attr", "batch", "status", "funding_pending"],
            ],
        },
        {
            "name": "pp_accept_approved_batch",
            "area": "memory_consolidation", "order": 20,
            "latency_class": "background", "batch": False,
            "comment": "Only a completely funded batch becomes runnable; the aggregate debit prevents partition workers from overspending independently.",
            "match": [["agent", "has_process_portfolio_policy", "policy"],
                      ["agent", "has_portfolio_batch", "batch"],
                      ["batch", "funded_by", "request"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                         Eq(A("batch", "status"), L("funding_pending")),
                         Eq(A("request", "status"), L("approved"))),
            "effects": [["set_attr", "batch", "status", "funded"]],
        },
        {
            "name": "pp_reject_batch_when_shared_budget_denies_it",
            "area": "memory_consolidation", "order": 21,
            "latency_class": "background", "batch": False,
            "comment": "A denied aggregate reservation creates terminal per-partition records and no CognitiveTasks.",
            "match": [["agent", "has_portfolio_batch", "batch"],
                      ["batch", "funded_by", "request"],
                      ["batch", "has_work_unit", "unit"]],
            "where": And(Eq(A("batch", "status"), L("funding_pending")),
                         Eq(A("request", "status"), L("denied")),
                         Eq(A("unit", "status"), L("proposed")),
                         Not(Exists(N("unit", "has_receipt"), "old", L(True)))),
            "effects": [
                ["add_node", "receipt", "ProcessPortfolioReceipt", {
                    "task_key": T(A("unit", "task_key")),
                    "batch_key": T(A("batch", "batch_key")),
                    "partition": T(A("unit", "partition")),
                    "generation": T(A("unit", "generation")),
                    "logical_time": T(A("unit", "logical_time")),
                    "status": "denied", "work_units": 0,
                    "reason": "budget_exhausted",
                }],
                ["add_edge", "agent", "has_process_portfolio_receipt", "receipt", {}],
                ["add_edge", "unit", "has_receipt", "receipt", {}],
                ["set_attr", "unit", "status", "denied"],
                ["set_attr", "batch", "status", "denied"],
            ],
        },
        {
            "name": "pp_materialize_funded_partitions_as_native_tasks",
            "area": "memory_consolidation", "order": 30,
            "latency_class": "background", "batch": False,
            "comment": "Graph rules choose funded partitions; the existing AreaParallel cycle plan executes pure native reductions and folds results by logical task key.",
            "match": [["agent", "has_process_portfolio_policy", "policy"],
                      ["agent", "has_portfolio_batch", "batch"],
                      ["batch", "has_work_unit", "unit"],
                      ["agent", "has_cognitive_area", "area"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                         Or(Eq(A("batch", "status"), L("funded")),
                            Eq(A("batch", "status"), L("running"))),
                         Eq(A("unit", "status"), L("proposed")),
                         Eq(A("area", "name"), L(AREA)),
                         Not(Exists(N("unit", "has_native_task"), "old", L(True)))),
            "effects": [
                ["add_node", "task", "CognitiveTask", {
                    "status": "requested", "kind": "vector_sum",
                    "payload": T(A("unit", "evidence_vector")),
                    "input_epoch": T(A("unit", "source_epoch")),
                    "logical_time": T(A("unit", "logical_time")),
                    "area": AREA, "order": 1, "urgency": 1,
                    "estimated_cost": T(A("unit", "cost")),
                }],
                ["add_edge", "unit", "has_native_task", "task", {}],
                ["add_edge", "area", "has_task", "task", {}],
                ["set_attr", "unit", "status", "requested"],
                ["set_attr", "batch", "status", "running"],
            ],
        },
        {
            "name": "pp_record_completed_native_result_once",
            "area": "memory_consolidation", "order": 40,
            "latency_class": "background", "batch": False,
            "comment": "Fold native numeric evidence into graph-owned portfolio records; it does not choose or promote an operator.",
            "match": [["agent", "has_portfolio_batch", "batch"],
                      ["batch", "has_work_unit", "unit"],
                      ["unit", "has_native_task", "task"],
                      ["task", "has_result", "result"]],
            "where": And(Eq(A("batch", "status"), L("running")),
                         Eq(A("unit", "status"), L("requested")),
                         Eq(A("task", "status"), L("done")),
                         Eq(A("result", "status"), L("done")),
                         Not(Exists(N("unit", "has_receipt"), "old", L(True)))),
            "effects": [
                ["add_node", "receipt", "ProcessPortfolioReceipt", {
                    "task_key": T(A("unit", "task_key")),
                    "batch_key": T(A("batch", "batch_key")),
                    "partition": T(A("unit", "partition")),
                    "generation": T(A("unit", "generation")),
                    "logical_time": T(A("unit", "logical_time")),
                    "source_epoch": T(A("unit", "source_epoch")),
                    "result": T(A("result", "output")),
                    "status": "completed", "work_units": T(A("unit", "cost")),
                }],
                ["add_edge", "agent", "has_process_portfolio_receipt", "receipt", {}],
                ["add_edge", "unit", "has_receipt", "receipt", {}],
                ["set_attr", "unit", "status", "completed"],
            ],
        },
        {
            "name": "pp_keep_failed_native_result_as_terminal_receipt",
            "area": "memory_consolidation", "order": 41,
            "latency_class": "background", "batch": False,
            "comment": "Failed partitions stay visible and charged; they are never reclassified as successful output.",
            "match": [["agent", "has_portfolio_batch", "batch"],
                      ["batch", "has_work_unit", "unit"],
                      ["unit", "has_native_task", "task"],
                      ["task", "has_result", "result"]],
            "where": And(Eq(A("batch", "status"), L("running")),
                         Eq(A("unit", "status"), L("requested")),
                         Eq(A("task", "status"), L("failed")),
                         Eq(A("result", "status"), L("failed")),
                         Not(Exists(N("unit", "has_receipt"), "old", L(True)))),
            "effects": [
                ["add_node", "receipt", "ProcessPortfolioReceipt", {
                    "task_key": T(A("unit", "task_key")),
                    "batch_key": T(A("batch", "batch_key")),
                    "partition": T(A("unit", "partition")),
                    "generation": T(A("unit", "generation")),
                    "logical_time": T(A("unit", "logical_time")),
                    "result_status": "failed", "error": T(A("result", "error")),
                    "status": "failed", "work_units": T(A("unit", "cost")),
                }],
                ["add_edge", "agent", "has_process_portfolio_receipt", "receipt", {}],
                ["add_edge", "unit", "has_receipt", "receipt", {}],
                ["set_attr", "unit", "status", "failed"],
            ],
        },
        {
            "name": "pp_cancel_unstarted_partition_without_erasing_receipts",
            "area": "memory_consolidation", "order": 25,
            "latency_class": "background", "batch": False,
            "comment": "Cancellation before funding yields a terminal receipt and never deletes completed sibling receipts.",
            "match": [["agent", "has_portfolio_batch", "batch"],
                      ["batch", "has_work_unit", "unit"]],
            "where": And(Eq(A("batch", "status"), L("cancel_requested")),
                         Eq(A("unit", "status"), L("cancel_requested")),
                         Not(Exists(N("unit", "has_receipt"), "old", L(True)))),
            "effects": [
                ["add_node", "receipt", "ProcessPortfolioReceipt", {
                    "task_key": T(A("unit", "task_key")),
                    "batch_key": T(A("batch", "batch_key")),
                    "partition": T(A("unit", "partition")),
                    "generation": T(A("unit", "generation")),
                    "logical_time": T(A("unit", "logical_time")),
                    "status": "cancelled", "work_units": 0,
                }],
                ["add_edge", "agent", "has_process_portfolio_receipt", "receipt", {}],
                ["add_edge", "unit", "has_receipt", "receipt", {}],
                ["set_attr", "unit", "status", "cancelled"],
            ],
        },
        {
            "name": "pp_close_batch_after_every_partition_is_terminal",
            "area": "memory_consolidation", "order": 50,
            "latency_class": "background", "batch": False,
            "comment": "A batch releases the single-active-batch slot only after every partition has a terminal receipt.",
            "match": [["agent", "has_portfolio_batch", "batch"],
                      ["batch", "has_work_unit", "unit"]],
            "where": And(Eq(A("batch", "status"), L("running")),
                         Not(Exists(N("batch", "has_work_unit"), "pending",
                                     Not(Or(Eq(A("pending", "status"), L("completed")),
                                            Eq(A("pending", "status"), L("failed")),
                                            Eq(A("pending", "status"), L("cancelled")),
                                            Eq(A("pending", "status"), L("denied"))))))),
            "effects": [["set_attr", "batch", "status", "completed"]],
        },
    ]
    return {
        "id": SEED_ID, "version": "1.0.0",
        "depends_on": ["cognitive_areas", "thinking_budget"],
        "self_load_only": True, "area": "memory_consolidation",
        "description": "P15.02: disabled graph-owned portfolio batches, aggregate shared-budget reservation and deterministic native task execution.",
        "microtheory": {"name": SEED_ID,
                        "description": "Fund one bounded portfolio batch before its independent partitions execute in the existing deterministic native task pool."},
        "nodes": [
            {"local_id": 0, "type": "ProcessPortfolioPolicy", "attrs": {
                "name": "process_portfolio_policy", "enabled": 0.0,
                "max_workers": 4.0, "max_partitions": 64.0,
                "max_work_units": 100000.0}},
            {"local_id": 1, "type": "CognitiveArea", "attrs": {
                "name": AREA, "logical_tick": 0, "desired_workers": 4,
                "effort": 1, "status": "active"}},
        ],
        "edges": [
            {"src": {"role": "agent_root"}, "type": "has_process_portfolio_policy",
             "tgt": {"local": 0}, "attrs": {}},
            {"src": {"role": "agent_root"}, "type": "has_cognitive_area",
             "tgt": {"local": 1}, "attrs": {}},
        ],
        "productions": productions, "rules": rules,
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
