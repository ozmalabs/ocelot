#!/usr/bin/env python3
"""Generate the disabled-by-default P25 learned-content budget rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "learning_memory_budget.json"
AREA = "learning_memory_budget"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(node, key): return {"type": "Attr", "node": V(node), "key": key}
def T(value): return {"__term__": value}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def IfThenElse(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}
def And(*items): return {"type": "And", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def Exists(source, name, predicate):
    return {"type": "Exists", "source": source, "var_name": name,
            "predicate": predicate}
def N(node, edge):
    return {"type": "Neighbours", "node": V(node), "edge_type": edge,
            "any_type": False}


def build_seed():
    relations = [
        ("Agent", "has_learning_memory_budget_policy", "LearningMemoryBudgetPolicy"),
        ("Agent", "has_learning_memory_item", "LearningMemoryItem"),
        ("LearningMemoryItem", "has_learning_memory_cache", "LearningMemoryCache"),
        ("LearningMemoryItem", "has_learning_memory_graph_node", "LearningMemoryGraphNode"),
        ("LearningMemoryItem", "has_eviction_receipt", "LearningMemoryEvictionReceipt"),
        ("Agent", "has_durable_learning_read", "DurableLearningRead"),
        ("Agent", "has_learning_memory_read_receipt", "LearningMemoryReadReceipt"),
    ]

    admit_item = {
        "name": "lmb_admit_charged_learning_content",
        "area": AREA, "order": 0, "latency_class": "background", "batch": False,
        "comment": "Charge every incoming dynamic item before making it learner-visible.",
        "match": [["ag", "has_learning_memory_budget_policy", "pol"],
                  ["ag", "has_learning_memory_item", "item"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("item", "availability"), L("pending_admission")),
                      Gt(A("item", "charged_bytes"), L(0.0)),
                      Lte(A("item", "charged_bytes"), A("pol", "capacity_bytes"))),
        "effects": [["set_attr", "item", "availability", "resident"],
                    ["set_attr", "item", "retention_priority",
                     T(IfThenElse(Eq(A("item", "content_class"), L("persistent_summary")),
                                  A("pol", "verified_summary_priority"),
                                  A("item", "admission_epoch")))],
                    ["set_attr", "pol", "resident_bytes",
                     T({"type": "Plus", "items": [A("pol", "resident_bytes"),
                                                        A("item", "charged_bytes")]})]],
    }
    reject_oversize = {
        "name": "lmb_reject_content_larger_than_shared_capacity",
        "area": AREA, "order": 0, "latency_class": "background", "batch": False,
        "comment": "Reject an item that cannot fit by itself; never expose its payload for free.",
        "match": [["ag", "has_learning_memory_budget_policy", "pol"],
                  ["ag", "has_learning_memory_item", "item"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("item", "availability"), L("pending_admission")),
                      Gt(A("item", "charged_bytes"), A("pol", "capacity_bytes"))),
        "effects": [["set_attr", "item", "availability", "rejected_capacity"],
                    ["set_attr", "item", "payload", None]],
    }
    select_victim = {
        "name": "lmb_evict_lowest_priority_resident_content",
        "area": AREA, "order": 1, "latency_class": "background", "batch": False,
        "comment": "Select the lowest-priority resident learned item under shared byte pressure; target/source identity is not an eviction input.",
        "match": [["ag", "has_learning_memory_budget_policy", "pol"],
                  ["ag", "has_learning_memory_item", "item"]],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Gt(A("pol", "resident_bytes"), A("pol", "capacity_bytes")),
            Eq(A("item", "availability"), L("resident")),
            Gt(A("item", "charged_bytes"), L(0.0)),
            Not(Exists(N("ag", "has_learning_memory_item"), "other", And(
                Eq(A("other", "availability"), L("resident")),
                Gt(A("other", "charged_bytes"), L(0.0)),
                Lt(A("other", "retention_priority"), A("item", "retention_priority")),
            ))),
        ),
        "effects": [
            ["set_attr", "item", "availability", "evicted"],
            ["set_attr", "item", "payload", None],
            ["set_attr", "pol", "resident_bytes",
             T({"type": "Minus", "a": A("pol", "resident_bytes"),
                "b": A("item", "charged_bytes")})],
            ["add_node", "receipt", "LearningMemoryEvictionReceipt", {
                "item_id": T(A("item", "item_id")),
                "content_class": T(A("item", "content_class")),
                "charged_bytes": T(A("item", "charged_bytes")),
                "protection_class": T(A("item", "protection_class")),
                "status": "evicted", "answer_payload_retained": False,
            }],
            ["add_edge", "item", "has_eviction_receipt", "receipt", {}],
            ["add_edge", "ag", "has_learning_memory_read_receipt", "receipt", {}],
        ],
    }
    invalidate_cache = {
        "name": "lmb_invalidate_views_of_evicted_content",
        "area": AREA, "order": 2, "latency_class": "background", "batch": False,
        "comment": "Make derived cache views unavailable when their source item is evicted.",
        "match": [["ag", "has_learning_memory_budget_policy", "pol"],
                  ["ag", "has_learning_memory_item", "item"],
                  ["item", "has_learning_memory_cache", "cache"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("item", "availability"), L("evicted")),
                      Eq(A("cache", "availability"), L("resident"))),
        "effects": [["set_attr", "cache", "availability", "stale"],
                    ["set_attr", "cache", "prediction", None],
                    ["set_attr", "cache", "rebuild_from_source", T(L(False))]],
    }
    charge_durable_read = {
        "name": "lmb_charge_durable_rebuild_before_read",
        "area": AREA, "order": 3, "latency_class": "background", "batch": False,
        "comment": "Charge durable reconstruction work before making a record available again.",
        "match": [["ag", "has_learning_memory_budget_policy", "pol"],
                  ["ag", "has_durable_learning_read", "read"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("read", "status"), L("requested")),
                      Gt(A("read", "rebuild_bytes"), L(0.0))),
        "effects": [["set_attr", "pol", "durable_read_bytes",
                     T({"type": "Plus", "items": [A("pol", "durable_read_bytes"),
                                                        A("read", "rebuild_bytes")]})],
                    ["set_attr", "read", "status", "charged"],
                    ["set_attr", "read", "availability", "pending_capacity_admission"],
                    ["add_node", "receipt", "LearningMemoryReadReceipt", {
                        "read_id": T(A("read", "read_id")),
                        "rebuild_bytes": T(A("read", "rebuild_bytes")),
                        "status": "charged", "answer_payload": None,
                    }],
                    ["add_edge", "ag", "has_learning_memory_read_receipt", "receipt", {}]],
    }
    return {
        "id": "learning_memory_budget", "version": "1.0.0",
        "depends_on": [], "self_load_only": True, "area": AREA,
        "description": "Opt-in native admission/eviction accounting for dynamically learned content; storage adapters perform mechanical I/O only.",
        "microtheory": {"name": AREA,
                        "description": "Equal capacity and eviction semantics for all learned content."},
        "nodes": [{"local_id": 0, "type": "LearningMemoryBudgetPolicy", "attrs": {
            "name": "learning_memory_budget_policy", "enabled": 0.0,
            "capacity_bytes": 8192.0, "resident_bytes": 0.0,
            "durable_read_bytes": 0.0, "fixed_runtime_bytes_reported_separately": True,
            "verified_summary_priority": 1000000.0,
            "protection_policy": "uniform_content_no_target_exemption",
        }}],
        "edges": [{"src": {"role": "agent_root"},
                    "type": "has_learning_memory_budget_policy",
                    "tgt": {"local": 0}, "attrs": {}}],
        "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                         "src": {"type": src, "var": "src"}, "edge_type": edge,
                         "tgt": {"type": tgt, "var": "tgt"}}
                        for src, edge, tgt in relations],
        "rules": [admit_item, reject_oversize, select_victim,
                  invalidate_cache, charge_durable_read],
    }


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
